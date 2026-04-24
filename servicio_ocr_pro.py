from time import perf_counter

import fitz
import pytesseract
from pytesseract import Output, TesseractNotFoundError

from controlador_cancelacion import DetencionSeguridadError
from etapas_proceso import ProcesoCanceladoError
from evaluador_pagina import EvaluadorPagina
from limites_proceso import LimitesProceso
from modelos import ResultadoAnalisisPDF
from preprocesador_pro import PreprocesadorPro
from servicio_ocr import ServicioOCR
from variantes_ocr import construir_variantes_para_pagina


class ServicioOCRPro(ServicioOCR):
    def __init__(
        self,
        preprocesador: PreprocesadorPro | None = None,
        evaluador: EvaluadorPagina | None = None,
    ) -> None:
        super().__init__(evaluador_pagina=evaluador)
        self.preprocesador = preprocesador or PreprocesadorPro()

    def ejecutar_ocr_pro(
        self,
        resultado: ResultadoAnalisisPDF,
        callback=None,
        cancelador=None,
        controlador=None,
        limites: LimitesProceso | None = None,
        callback_alerta=None,
    ) -> ResultadoAnalisisPDF:
        if not self.esta_configurado():
            resultado.codigo_estado_ocr = "no_disponible"
            resultado.estado_ocr = "OCR no disponible"
            resultado.detalle_ocr = (
                "Tesseract no está instalado o no está accesible desde el sistema."
            )
            resultado.motor_ocr = "Tesseract OCR Pro (no disponible)"
            resultado.ocr_disponible = False
            return resultado

        limites = limites or LimitesProceso()
        self.idioma_ocr = self._obtener_idioma_ocr()
        self.motor_ocr = f"Tesseract OCR Pro ({self.idioma_ocr})"
        resultado.motor_ocr = self.motor_ocr
        resultado.ocr_disponible = True

        paginas_objetivo = self._obtener_paginas_objetivo(resultado)
        resultado.paginas_ocr_objetivo = len(paginas_objetivo)

        if not paginas_objetivo:
            resultado.codigo_estado_ocr = "no_ejecutado"
            resultado.estado_ocr = "OCR no ejecutado"
            resultado.detalle_ocr = "No se encontraron páginas candidatas para OCR Pro."
            return resultado

        textos_ocr = []
        errores = []
        procesadas = 0
        resumen_variantes = []

        try:
            documento = fitz.open(resultado.ruta_archivo)
        except Exception as error:
            resultado.codigo_estado_ocr = "error"
            resultado.estado_ocr = "OCR Pro fallido"
            resultado.detalle_ocr = f"No se pudo abrir el PDF para OCR Pro. Detalle: {error}"
            resultado.errores_ocr.append(str(error))
            return resultado

        try:
            total = len(paginas_objetivo)

            for posicion, indice_pagina in enumerate(paginas_objetivo, start=1):
                if controlador is not None:
                    controlador.esperar_si_pausado()
                    controlador.verificar_estado()

                if cancelador and cancelador():
                    raise ProcesoCanceladoError("Procesamiento cancelado por el usuario.")

                pagina_resultado = resultado.resumen_paginas[indice_pagina]
                numero_visible = indice_pagina + 1
                tiempo_inicio_pagina = perf_counter()

                if callback:
                    progreso = 30 + int((posicion - 1) / max(1, total) * 58)
                    callback(
                        progreso,
                        f"Modo Pro: probando variantes en página {numero_visible} de {resultado.cantidad_paginas}...",
                    )

                try:
                    pagina_pdf = documento.load_page(indice_pagina)
                    imagen_base = self.preprocesador.renderizar_pagina(pagina_pdf, zoom=2.0)

                    analisis_imagen = self.evaluador_pagina.analizar_condicion_pagina(
                        pagina_resultado,
                        imagen_base,
                    )
                    variantes = construir_variantes_para_pagina(analisis_imagen)

                    mejor_resultado = None
                    tiempo_ocr_acumulado = 0
                    intentos_realizados = 0

                    for variante in variantes:
                        if controlador is not None:
                            controlador.esperar_si_pausado()
                            controlador.verificar_estado()

                        if cancelador and cancelador():
                            raise ProcesoCanceladoError("Procesamiento cancelado por el usuario.")

                        if intentos_realizados >= limites.max_reintentos_por_pagina:
                            if callback_alerta:
                                callback_alerta(
                                    f"Se alcanzó el máximo de reintentos configurado en la página {numero_visible}."
                                )
                            break

                        tiempo_transcurrido_ms = int((perf_counter() - tiempo_inicio_pagina) * 1000)
                        if tiempo_transcurrido_ms > limites.max_tiempo_pagina_ms:
                            if callback_alerta:
                                callback_alerta(
                                    f"La página {numero_visible} superó el límite de tiempo configurado."
                                )
                            if (
                                limites.detener_por_seguridad
                                and tiempo_transcurrido_ms > int(limites.max_tiempo_pagina_ms * 1.8)
                                and controlador is not None
                            ):
                                controlador.detener_por_seguridad(
                                    f"El análisis fue detenido por seguridad: la página {numero_visible} excedió el límite crítico de tiempo."
                                )
                            break

                        tiempo_inicio_intento = perf_counter()
                        imagen_tratada, _ = self.preprocesador.aplicar_variante(
                            imagen_base,
                            variante,
                            idioma_osd="osd",
                        )

                        tiempo_inicio_ocr = perf_counter()
                        datos_ocr = pytesseract.image_to_data(
                            imagen_tratada,
                            lang=self.idioma_ocr,
                            config=f"--oem 3 --psm {variante.psm}",
                            output_type=Output.DICT,
                        )
                        texto_ocr = pytesseract.image_to_string(
                            imagen_tratada,
                            lang=self.idioma_ocr,
                            config=f"--oem 3 --psm {variante.psm}",
                        ).strip()
                        tiempo_ocr_ms = int((perf_counter() - tiempo_inicio_ocr) * 1000)
                        tiempo_total_intento_ms = int((perf_counter() - tiempo_inicio_intento) * 1000)

                        tiempo_ocr_acumulado += tiempo_ocr_ms
                        intentos_realizados += 1

                        evaluacion = self.evaluador_pagina.evaluar_intento(
                            texto_ocr,
                            datos_ocr,
                            tiempo_total_ms=tiempo_total_intento_ms,
                            tiempo_ocr_ms=tiempo_ocr_ms,
                            analisis_imagen=analisis_imagen,
                            numero_intentos=intentos_realizados,
                        )
                        evaluacion["variante"] = variante

                        if mejor_resultado is None or evaluacion["score"] > mejor_resultado["score"]:
                            mejor_resultado = evaluacion

                        if (
                            not analisis_imagen["es_problematica"]
                            and mejor_resultado["score"] >= 72
                        ):
                            break

                    tiempo_total_pagina_ms = int((perf_counter() - tiempo_inicio_pagina) * 1000)

                    if mejor_resultado and mejor_resultado["texto"]:
                        observaciones = list(mejor_resultado["observaciones"])

                        if intentos_realizados >= limites.max_reintentos_por_pagina:
                            observaciones.append("Se alcanzó el límite configurado de reintentos por página.")

                        if tiempo_total_pagina_ms > limites.max_tiempo_pagina_ms:
                            observaciones.append("Se alcanzó el límite configurado de tiempo por página.")

                        pagina_resultado.texto_ocr = mejor_resultado["texto"]
                        pagina_resultado.ocr_ejecutado = True
                        pagina_resultado.ocr_error = ""
                        pagina_resultado.ocr_confianza_promedio = mejor_resultado["confianza_promedio"]
                        pagina_resultado.ocr_confianza_mediana = mejor_resultado["confianza_mediana"]
                        pagina_resultado.ocr_cantidad_palabras = mejor_resultado["cantidad_palabras"]
                        pagina_resultado.ocr_palabras_baja_confianza = mejor_resultado["palabras_baja_confianza"]
                        pagina_resultado.ocr_caracteres_totales = mejor_resultado["caracteres_totales"]
                        pagina_resultado.ocr_ruido_textual = mejor_resultado["ruido_textual"]
                        pagina_resultado.ocr_tiempo_total_ms = tiempo_total_pagina_ms
                        pagina_resultado.ocr_tiempo_ocr_ms = tiempo_ocr_acumulado
                        pagina_resultado.ocr_variante_ganadora = mejor_resultado["variante"].nombre
                        pagina_resultado.ocr_variante_clave = mejor_resultado["variante"].clave
                        pagina_resultado.ocr_numero_intentos = intentos_realizados
                        pagina_resultado.ocr_score_estimado = mejor_resultado["score"]
                        pagina_resultado.ocr_dificultad = mejor_resultado["dificultad"]
                        pagina_resultado.ocr_dificultad_nivel = mejor_resultado["dificultad_nivel"]
                        pagina_resultado.ocr_dificultad_indice = mejor_resultado["dificultad_indice"]
                        pagina_resultado.ocr_requiere_revision = mejor_resultado["requiere_revision"]
                        pagina_resultado.ocr_observaciones = self._limpiar_observaciones(observaciones)

                        procesadas += 1
                        textos_ocr.append(
                            f"===== PÁGINA {numero_visible} | VARIANTE: {mejor_resultado['variante'].nombre} =====\n{mejor_resultado['texto']}"
                        )
                        resumen_variantes.append(
                            f"P{numero_visible}: {mejor_resultado['variante'].clave}"
                        )
                    else:
                        pagina_resultado.ocr_ejecutado = False
                        pagina_resultado.ocr_error = "No se obtuvo texto OCR utilizable."
                        pagina_resultado.ocr_tiempo_total_ms = tiempo_total_pagina_ms
                        pagina_resultado.ocr_tiempo_ocr_ms = tiempo_ocr_acumulado
                        pagina_resultado.ocr_numero_intentos = intentos_realizados
                        pagina_resultado.ocr_dificultad = "crítica"
                        pagina_resultado.ocr_dificultad_nivel = 4
                        pagina_resultado.ocr_dificultad_indice = 100
                        pagina_resultado.ocr_requiere_revision = True
                        pagina_resultado.ocr_observaciones = [
                            "OCR vacío.",
                            "Revisión manual recomendada.",
                        ]
                        errores.append(f"Página {numero_visible}: no se obtuvo texto OCR utilizable.")

                except ProcesoCanceladoError:
                    raise
                except DetencionSeguridadError:
                    raise
                except TesseractNotFoundError:
                    resultado.codigo_estado_ocr = "no_disponible"
                    resultado.estado_ocr = "OCR Pro no disponible"
                    resultado.detalle_ocr = (
                        "Tesseract no está instalado o no está accesible desde el sistema."
                    )
                    resultado.motor_ocr = "Tesseract OCR Pro (no disponible)"
                    resultado.ocr_disponible = False
                    return resultado
                except Exception as error:
                    pagina_resultado.ocr_ejecutado = False
                    pagina_resultado.ocr_error = str(error)
                    pagina_resultado.ocr_dificultad = "crítica"
                    pagina_resultado.ocr_dificultad_nivel = 4
                    pagina_resultado.ocr_dificultad_indice = 100
                    pagina_resultado.ocr_requiere_revision = True
                    pagina_resultado.ocr_observaciones = [
                        "Error durante OCR Pro.",
                        "Revisión manual recomendada.",
                    ]
                    errores.append(f"Página {numero_visible}: {error}")

            resultado.texto_ocr_completo = "\n\n".join(textos_ocr).strip()
            resultado.paginas_ocr_procesadas = procesadas
            resultado.errores_ocr = errores

            if procesadas > 0 and not errores:
                resultado.codigo_estado_ocr = "ejecutado"
                resultado.estado_ocr = "OCR Pro ejecutado"
                detalle = f"Se procesaron {procesadas} página(s) con OCR Pro."
            elif procesadas > 0 and errores:
                resultado.codigo_estado_ocr = "parcial"
                resultado.estado_ocr = "OCR Pro ejecutado con observaciones"
                detalle = (
                    f"Se procesaron {procesadas} página(s) con OCR Pro, pero hubo incidencias en {len(errores)}."
                )
            else:
                resultado.codigo_estado_ocr = "error"
                resultado.estado_ocr = "OCR Pro fallido"
                detalle = "No se pudo obtener texto OCR útil con las variantes PRO."

            if resumen_variantes:
                detalle += f" Variantes ganadoras: {' | '.join(resumen_variantes[:8])}."
            resultado.detalle_ocr = detalle

            return resultado
        finally:
            documento.close()