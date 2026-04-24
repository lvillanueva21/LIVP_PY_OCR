from copy import deepcopy
from time import perf_counter

from analizador_pdf import AnalizadorPDF
from comparador_analisis import ComparadorAnalisis
from etapas_proceso import (
    ESTADO_ADVERTENCIA,
    ESTADO_COMPLETADA,
    ESTADO_EN_CURSO,
    ESTADO_OMITIDA,
    ETAPA_COMPARACION_RESULTADOS,
    ETAPA_CONSOLIDACION_TEXTO,
    ETAPA_EVALUACION_OCR,
    ETAPA_EXTRACCION_CAMPOS,
    ETAPA_FINALIZACION,
    ETAPA_INSPECCION_INICIAL,
    ETAPA_LECTURA_TEXTO_DIGITAL,
    ETAPA_OCR,
    ProcesoCanceladoError,
)
from extractor_poliza import ExtractorPoliza
from modos_analisis import ModoAnalisis
from modelos import ResultadoAnalisisPDF
from procesador_imagen import ProcesadorImagen
from servicio_ocr import ServicioOCR


class PipelineDocumento:
    def __init__(
        self,
        analizador: AnalizadorPDF | None = None,
        procesador_imagen: ProcesadorImagen | None = None,
        servicio_ocr: ServicioOCR | None = None,
        extractor_poliza: ExtractorPoliza | None = None,
        comparador_analisis: ComparadorAnalisis | None = None,
    ) -> None:
        self.analizador = analizador or AnalizadorPDF()
        self.procesador_imagen = procesador_imagen or ProcesadorImagen()
        self.servicio_ocr = servicio_ocr or ServicioOCR()
        self.extractor_poliza = extractor_poliza or ExtractorPoliza()
        self.comparador_analisis = comparador_analisis or ComparadorAnalisis()

    def procesar(
        self,
        ruta_archivo: str,
        callback=None,
        callback_etapa=None,
        cancelador=None,
        modo_etiqueta: str = "Básico",
    ) -> ResultadoAnalisisPDF:
        inicio = perf_counter()

        self._verificar_cancelacion(cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_INSPECCION_INICIAL,
            ESTADO_EN_CURSO,
            f"Abriendo PDF y preparando análisis en modo {modo_etiqueta}.",
        )
        self._emitir_progreso(callback, 5, "Analizando PDF...")
        resultado = self.analizador.analizar(ruta_archivo)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_INSPECCION_INICIAL,
            ESTADO_COMPLETADA,
            f"Documento inspeccionado correctamente. Páginas detectadas: {resultado.cantidad_paginas}.",
        )

        self._verificar_cancelacion(cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_LECTURA_TEXTO_DIGITAL,
            ESTADO_EN_CURSO,
            "Revisando texto digital disponible y diagnóstico inicial.",
        )
        if resultado.tiene_texto_digital:
            detalle_texto = "Se encontró texto digital suficiente en el documento."
        else:
            detalle_texto = "No se encontró texto digital suficiente; se evaluará OCR."
        self._emitir_etapa(
            callback_etapa,
            ETAPA_LECTURA_TEXTO_DIGITAL,
            ESTADO_COMPLETADA,
            detalle_texto,
        )

        self._verificar_cancelacion(cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_EVALUACION_OCR,
            ESTADO_EN_CURSO,
            "Evaluando necesidad de OCR y preparación de imagen.",
        )
        self._emitir_progreso(callback, 20, "Evaluando estrategia de OCR...")
        requiere_preprocesamiento, acciones_preparacion = self.procesador_imagen.evaluar_preparacion(
            resultado
        )

        resultado.requiere_preprocesamiento = requiere_preprocesamiento
        resultado.acciones_preparacion = acciones_preparacion

        codigo_estado_base, estado_base, detalle_base, apto_para_ocr = self.servicio_ocr.obtener_estado(
            resultado
        )

        resultado.codigo_estado_ocr = codigo_estado_base
        resultado.estado_ocr = estado_base
        resultado.detalle_ocr = detalle_base
        resultado.apto_para_ocr = apto_para_ocr
        resultado.motor_ocr = self.servicio_ocr.motor_ocr

        detalle_evaluacion = detalle_base
        if acciones_preparacion:
            detalle_evaluacion += f" Preparación sugerida: {' | '.join(acciones_preparacion)}."
        self._emitir_etapa(
            callback_etapa,
            ETAPA_EVALUACION_OCR,
            ESTADO_COMPLETADA,
            detalle_evaluacion,
        )

        self._verificar_cancelacion(cancelador)

        if not resultado.apto_para_ocr:
            resultado.ocr_disponible = self.servicio_ocr.esta_configurado()
            self._emitir_etapa(
                callback_etapa,
                ETAPA_OCR,
                ESTADO_OMITIDA,
                "OCR omitido: el documento ya tiene texto digital suficiente o no lo requiere.",
            )
            self._consolidar_y_extraer(
                resultado,
                callback=callback,
                callback_etapa=callback_etapa,
                cancelador=cancelador,
            )
            resultado.tiempo_total_ms = int((perf_counter() - inicio) * 1000)
            return resultado

        if not self.servicio_ocr.esta_configurado():
            resultado.codigo_estado_ocr = "no_disponible"
            resultado.estado_ocr = "OCR no disponible"
            resultado.detalle_ocr = self._construir_detalle_ocr(
                "Tesseract no está instalado o no está accesible desde el sistema.",
                acciones_preparacion,
            )
            resultado.motor_ocr = self.servicio_ocr.motor_ocr
            resultado.ocr_disponible = False

            self._emitir_etapa(
                callback_etapa,
                ETAPA_OCR,
                ESTADO_ADVERTENCIA,
                "OCR omitido: Tesseract no está disponible en el sistema.",
            )
            self._consolidar_y_extraer(
                resultado,
                callback=callback,
                callback_etapa=callback_etapa,
                cancelador=cancelador,
            )
            resultado.tiempo_total_ms = int((perf_counter() - inicio) * 1000)
            return resultado

        self._emitir_etapa(
            callback_etapa,
            ETAPA_OCR,
            ESTADO_EN_CURSO,
            f"Ejecutando OCR en modo {modo_etiqueta}.",
        )
        self._emitir_progreso(callback, 28, "Preparando OCR local...")
        resultado = self.servicio_ocr.ejecutar_ocr(
            resultado,
            self.procesador_imagen,
            callback=callback,
            cancelador=cancelador,
        )

        resultado.detalle_ocr = self._construir_detalle_ocr(
            resultado.detalle_ocr,
            acciones_preparacion,
        )

        estado_ocr_etapa = ESTADO_COMPLETADA
        if resultado.codigo_estado_ocr in {"parcial", "no_disponible"}:
            estado_ocr_etapa = ESTADO_ADVERTENCIA
        elif resultado.codigo_estado_ocr == "error":
            estado_ocr_etapa = ESTADO_ADVERTENCIA

        self._emitir_etapa(
            callback_etapa,
            ETAPA_OCR,
            estado_ocr_etapa,
            resultado.detalle_ocr,
        )

        self._consolidar_y_extraer(
            resultado,
            callback=callback,
            callback_etapa=callback_etapa,
            cancelador=cancelador,
        )
        resultado.tiempo_total_ms = int((perf_counter() - inicio) * 1000)
        return resultado

    def procesar_segun_modo(
        self,
        ruta_archivo: str,
        modo: str,
        callback=None,
        callback_etapa=None,
        cancelador=None,
    ) -> tuple[ResultadoAnalisisPDF, ResultadoAnalisisPDF | None, ResultadoAnalisisPDF | None, object | None]:
        self._emitir_etapa(
            callback_etapa,
            ETAPA_COMPARACION_RESULTADOS,
            ESTADO_OMITIDA,
            "Comparación aún no ejecutada.",
        )
        self._emitir_etapa(
            callback_etapa,
            ETAPA_FINALIZACION,
            ESTADO_OMITIDA,
            "Finalización pendiente.",
        )

        if modo == ModoAnalisis.BASICO:
            resultado_basico = self.procesar(
                ruta_archivo,
                callback=callback,
                callback_etapa=callback_etapa,
                cancelador=cancelador,
                modo_etiqueta="Básico",
            )
            self._finalizar_modo(resultado_basico, ModoAnalisis.BASICO)

            self._emitir_etapa(
                callback_etapa,
                ETAPA_COMPARACION_RESULTADOS,
                ESTADO_OMITIDA,
                "Comparación omitida: solo se ejecutó el modo Básico.",
            )
            self._emitir_etapa(
                callback_etapa,
                ETAPA_FINALIZACION,
                ESTADO_COMPLETADA,
                "Procesamiento en modo Básico completado.",
            )
            self._emitir_progreso(callback, 100, "Procesamiento completado.")
            return resultado_basico, resultado_basico, None, None

        if modo == ModoAnalisis.PRO:
            resultado_base = self.procesar(
                ruta_archivo,
                callback=callback,
                callback_etapa=callback_etapa,
                cancelador=cancelador,
                modo_etiqueta="Pro",
            )
            self._verificar_cancelacion(cancelador)

            resultado_pro = self._crear_resultado_provisional(resultado_base)
            self._finalizar_modo(resultado_pro, ModoAnalisis.PRO)

            self._emitir_etapa(
                callback_etapa,
                ETAPA_COMPARACION_RESULTADOS,
                ESTADO_OMITIDA,
                "Comparación omitida: solo se ejecutó el modo Pro.",
            )
            self._emitir_etapa(
                callback_etapa,
                ETAPA_FINALIZACION,
                ESTADO_COMPLETADA,
                "Procesamiento en modo Pro estructural completado.",
            )
            self._emitir_progreso(callback, 100, "Procesamiento completado.")
            return resultado_pro, None, resultado_pro, None

        callback_basico = self._crear_callback_rango(callback, 0, 78, "Básico")
        resultado_basico = self.procesar(
            ruta_archivo,
            callback=callback_basico,
            callback_etapa=callback_etapa,
            cancelador=cancelador,
            modo_etiqueta="Básico",
        )
        self._finalizar_modo(resultado_basico, ModoAnalisis.BASICO)

        self._verificar_cancelacion(cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_COMPARACION_RESULTADOS,
            ESTADO_EN_CURSO,
            "Construyendo resultado Pro provisional y calculando comparación.",
        )
        self._emitir_progreso(callback, 86, "Preparando comparación de resultados...")

        resultado_pro = self._crear_resultado_provisional(resultado_basico)
        self._finalizar_modo(resultado_pro, ModoAnalisis.PRO)

        comparacion = self.comparador_analisis.comparar(resultado_basico, resultado_pro)
        resultado_basico.comparacion_modos = comparacion
        resultado_pro.comparacion_modos = comparacion

        detalle_comparacion = comparacion.motivo or "Comparación completada."
        if comparacion.observaciones:
            detalle_comparacion += f" {' | '.join(comparacion.observaciones)}"

        self._emitir_etapa(
            callback_etapa,
            ETAPA_COMPARACION_RESULTADOS,
            ESTADO_COMPLETADA,
            detalle_comparacion,
        )
        self._emitir_etapa(
            callback_etapa,
            ETAPA_FINALIZACION,
            ESTADO_COMPLETADA,
            "Comparación de modos completada.",
        )
        self._emitir_progreso(callback, 100, "Procesamiento completado.")

        resultado_mostrado = resultado_basico
        if comparacion.modo_ganador == ModoAnalisis.PRO:
            resultado_mostrado = resultado_pro

        return resultado_mostrado, resultado_basico, resultado_pro, comparacion

    def reextraer_campos(self, resultado: ResultadoAnalisisPDF, callback=None) -> ResultadoAnalisisPDF:
        self._emitir_progreso(callback, 70, "Reextrayendo campos desde texto revisado...")
        resultado = self.extractor_poliza.extraer(resultado)
        self._finalizar_metricas_existentes(resultado)
        self._emitir_progreso(callback, 100, "Campos reextraídos correctamente.")
        return resultado

    def _consolidar_y_extraer(
        self,
        resultado: ResultadoAnalisisPDF,
        *,
        callback=None,
        callback_etapa=None,
        cancelador=None,
    ) -> None:
        self._verificar_cancelacion(cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_CONSOLIDACION_TEXTO,
            ESTADO_EN_CURSO,
            "Consolidando texto base para revisión manual.",
        )
        self._preparar_texto_revision(resultado)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_CONSOLIDACION_TEXTO,
            ESTADO_COMPLETADA,
            "Texto consolidado correctamente.",
        )

        self._verificar_cancelacion(cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_EXTRACCION_CAMPOS,
            ESTADO_EN_CURSO,
            "Extrayendo campos básicos de póliza.",
        )
        self._emitir_progreso(callback, 85, "Extrayendo campos básicos de póliza...")
        self.extractor_poliza.extraer(resultado)

        campos_detectados = sum(1 for campo in resultado.campos_extraidos if campo.detectado)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_EXTRACCION_CAMPOS,
            ESTADO_COMPLETADA,
            f"Extracción completada. Campos detectados: {campos_detectados}.",
        )

    def _finalizar_modo(self, resultado: ResultadoAnalisisPDF, modo: str) -> None:
        resultado.modo_analisis = modo
        resultado.etiqueta_modo = ModoAnalisis.etiqueta(modo)
        resultado.recomendacion_modo = self.comparador_analisis.recomendar_modo(resultado)
        resultado.metricas_paginas_modo = self.comparador_analisis.construir_metricas_paginas(resultado)
        resultado.metricas_documento_modo = self.comparador_analisis.construir_metricas_documento(resultado)

    def _finalizar_metricas_existentes(self, resultado: ResultadoAnalisisPDF) -> None:
        resultado.metricas_paginas_modo = self.comparador_analisis.construir_metricas_paginas(resultado)
        resultado.metricas_documento_modo = self.comparador_analisis.construir_metricas_documento(resultado)

    def _crear_resultado_provisional(self, resultado_base: ResultadoAnalisisPDF) -> ResultadoAnalisisPDF:
        resultado_pro = deepcopy(resultado_base)
        resultado_pro.es_provisional = True
        resultado_pro.observaciones_modo.append(
            "Modo Pro provisional: en esta fase aún reutiliza el flujo del modo Básico."
        )
        return resultado_pro

    def _preparar_texto_revision(self, resultado: ResultadoAnalisisPDF) -> None:
        if resultado.texto_final_revisado.strip():
            return

        texto_base = resultado.texto_completo.strip()
        if not texto_base:
            texto_base = resultado.texto_ocr_completo.strip()

        resultado.texto_final_revisado = texto_base

    def _construir_detalle_ocr(
        self,
        detalle_base: str,
        acciones_preparacion: list[str],
    ) -> str:
        if not acciones_preparacion:
            return detalle_base

        acciones_texto = " | ".join(acciones_preparacion)
        return f"{detalle_base} Preparación sugerida: {acciones_texto}."

    def _emitir_progreso(self, callback, valor: int, mensaje: str) -> None:
        if callback:
            callback(valor, mensaje)

    def _emitir_etapa(self, callback_etapa, etapa_id: str, estado: str, detalle: str) -> None:
        if callback_etapa:
            callback_etapa(etapa_id, estado, detalle)

    def _crear_callback_rango(self, callback, inicio: int, fin: int, prefijo: str):
        if callback is None:
            return None

        ancho = max(1, fin - inicio)

        def callback_rango(valor: int, mensaje: str) -> None:
            valor_ajustado = inicio + int((max(0, min(100, valor)) / 100) * ancho)
            callback(valor_ajustado, f"{prefijo}: {mensaje}")

        return callback_rango

    def _verificar_cancelacion(self, cancelador) -> None:
        if cancelador and cancelador():
            raise ProcesoCanceladoError("Procesamiento cancelado por el usuario.")