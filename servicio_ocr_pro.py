from time import perf_counter

import fitz
import pytesseract
from pytesseract import Output, TesseractNotFoundError

from etapas_proceso import ProcesoCanceladoError
from evaluador_pagina import EvaluadorPagina
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
        super().__init__()
        self.preprocesador = preprocesador or PreprocesadorPro()
        self.evaluador = evaluador or EvaluadorPagina()

    def ejecutar_ocr_pro(
        self,
        resultado: ResultadoAnalisisPDF,
        callback=None,
        cancelador=None,
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

                    analisis_pagina = self.evaluador.analizar_condicion_pagina(
                        pagina_resultado,
                        imagen_base,
                    )
                    variantes = construir_variantes_para_pagina(analisis_pagina)

                    mejor_resultado = None
                    tiempo_ocr_acumulado = 0
                    intentos_realizados = 0

                    for variante in variantes:
                        if cancelador and cancelador():
                            raise ProcesoCanceladoError("Procesamiento cancelado por el usuario.")

                        tiempo_inicio_intento = perf_counter()
                        imagen_tratada, observaciones_pre = self.preprocesador.aplicar_variante(
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

                        evaluacion = self.evaluador.evaluar_intento(
                            texto_ocr,
                            datos_ocr,
                            tiempo_total_ms=tiempo_total_intento_ms,
                            tiempo_ocr_ms=tiempo_ocr_ms,
                            observaciones=analisis_pagina["observaciones"] + observaciones_pre,
                        )

                        evaluacion["variante"] = variante
                        evaluacion["numero_intentos"] = intentos_realizados

                        if mejor_resultado is None or evaluacion["score"] > mejor_resultado["score"]:
                            mejor_resultado = evaluacion

                        # Si la página no parecía difícil y ya logramos buen score, no seguimos probando todo.
                        if (
                            not analisis_pagina["es_problematica"]
                            and mejor_resultado["score"] >= 72
                        ):
                            break

                    tiempo_total_pagina_ms = int((perf_counter() - tiempo_inicio_pagina) * 1000)

                    if mejor_resultado and mejor_resultado["texto"]:
                        pagina_resultado.texto_ocr = mejor_resultado["texto"]
                        pagina_resultado.ocr_ejecutado = True
                        pagina_resultado.ocr_error = ""
                        pagina_resultado.ocr_confianza_promedio = mejor_resultado["confianza_promedio"]
                        pagina_resultado.ocr_confianza_mediana = mejor_resultado["confianza_mediana"]
                        pagina_resultado.ocr_cantidad_palabras = mejor_resultado["cantidad_palabras"]
                        pagina_resultado.ocr_tiempo_total_ms = tiempo_total_pagina_ms
                        pagina_resultado.ocr_tiempo_ocr_ms = tiempo_ocr_acumulado
                        pagina_resultado.ocr_variante_ganadora = mejor_resultado["variante"].nombre
                        pagina_resultado.ocr_numero_intentos = mejor_resultado["numero_intentos"]
                        pagina_resultado.ocr_score_estimado = mejor_resultado["score"]
                        pagina_resultado.ocr_observaciones = mejor_resultado["observaciones"]

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
                        pagina_resultado.ocr_observaciones = analisis_pagina["observaciones"]
                        errores.append(f"Página {numero_visible}: no se obtuvo texto OCR utilizable.")

                except ProcesoCanceladoError:
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
                    pagina_resultado.ocr_observaciones.append("Error durante OCR Pro.")
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