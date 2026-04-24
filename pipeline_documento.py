from copy import deepcopy
from time import perf_counter

from analizador_pdf import AnalizadorPDF
from comparador_analisis import ComparadorAnalisis
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

    def procesar(self, ruta_archivo: str, callback=None) -> ResultadoAnalisisPDF:
        inicio = perf_counter()

        self._emitir_progreso(callback, 5, "Analizando PDF...")
        resultado = self.analizador.analizar(ruta_archivo)

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

        if not resultado.apto_para_ocr:
            resultado.ocr_disponible = self.servicio_ocr.esta_configurado()
            self._preparar_texto_revision(resultado)
            self._extraer_campos(resultado, callback)
            resultado.tiempo_total_ms = int((perf_counter() - inicio) * 1000)
            self._emitir_progreso(callback, 100, "Análisis completado. OCR no requerido.")
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
            self._preparar_texto_revision(resultado)
            self._extraer_campos(resultado, callback)
            resultado.tiempo_total_ms = int((perf_counter() - inicio) * 1000)
            self._emitir_progreso(callback, 100, "Análisis completado. OCR no disponible.")
            return resultado

        self._emitir_progreso(callback, 28, "Preparando OCR local...")
        resultado = self.servicio_ocr.ejecutar_ocr(
            resultado,
            self.procesador_imagen,
            callback=callback,
        )

        resultado.detalle_ocr = self._construir_detalle_ocr(
            resultado.detalle_ocr,
            acciones_preparacion,
        )

        self._preparar_texto_revision(resultado)
        self._extraer_campos(resultado, callback)
        resultado.tiempo_total_ms = int((perf_counter() - inicio) * 1000)

        mensaje_final = "Procesamiento completado."
        if resultado.codigo_estado_ocr == "ejecutado":
            mensaje_final = "Procesamiento completado con OCR."
        elif resultado.codigo_estado_ocr == "parcial":
            mensaje_final = "Procesamiento completado con OCR y observaciones."
        elif resultado.codigo_estado_ocr in {"error", "no_disponible"}:
            mensaje_final = "Procesamiento completado con incidencias OCR."

        self._emitir_progreso(callback, 100, mensaje_final)
        return resultado

    def procesar_segun_modo(self, ruta_archivo: str, modo: str, callback=None) -> tuple[
        ResultadoAnalisisPDF,
        ResultadoAnalisisPDF | None,
        ResultadoAnalisisPDF | None,
        object | None,
    ]:
        if modo == ModoAnalisis.BASICO:
            resultado_basico = self.procesar(ruta_archivo, callback=callback)
            self._finalizar_modo(resultado_basico, ModoAnalisis.BASICO)
            return resultado_basico, resultado_basico, None, None

        if modo == ModoAnalisis.PRO:
            callback_basico = self._crear_callback_rango(callback, 0, 85, "Base")
            resultado_base = self.procesar(ruta_archivo, callback=callback_basico)
            resultado_pro = self._crear_resultado_provisional(resultado_base)
            self._emitir_progreso(callback, 92, "Preparando modo Pro estructural...")
            self._finalizar_modo(resultado_pro, ModoAnalisis.PRO)
            self._emitir_progreso(callback, 100, "Modo Pro estructural completado.")
            return resultado_pro, None, resultado_pro, None

        callback_basico = self._crear_callback_rango(callback, 0, 72, "Básico")
        resultado_basico = self.procesar(ruta_archivo, callback=callback_basico)
        self._finalizar_modo(resultado_basico, ModoAnalisis.BASICO)

        self._emitir_progreso(callback, 78, "Construyendo resultado Pro estructural...")
        resultado_pro = self._crear_resultado_provisional(resultado_basico)
        self._finalizar_modo(resultado_pro, ModoAnalisis.PRO)

        self._emitir_progreso(callback, 90, "Comparando resultados...")
        comparacion = self.comparador_analisis.comparar(resultado_basico, resultado_pro)

        resultado_basico.comparacion_modos = comparacion
        resultado_pro.comparacion_modos = comparacion

        resultado_mostrado = resultado_basico
        if comparacion.modo_ganador == ModoAnalisis.PRO:
            resultado_mostrado = resultado_pro

        self._emitir_progreso(callback, 100, "Comparación completada.")
        return resultado_mostrado, resultado_basico, resultado_pro, comparacion

    def reextraer_campos(self, resultado: ResultadoAnalisisPDF, callback=None) -> ResultadoAnalisisPDF:
        self._emitir_progreso(callback, 70, "Reextrayendo campos desde texto revisado...")
        resultado = self.extractor_poliza.extraer(resultado)
        self._finalizar_metricas_existentes(resultado)
        self._emitir_progreso(callback, 100, "Campos reextraídos correctamente.")
        return resultado

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

    def _extraer_campos(self, resultado: ResultadoAnalisisPDF, callback=None) -> None:
        self._emitir_progreso(callback, 85, "Extrayendo campos básicos de póliza...")
        self.extractor_poliza.extraer(resultado)

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

    def _crear_callback_rango(self, callback, inicio: int, fin: int, prefijo: str):
        if callback is None:
            return None

        ancho = max(1, fin - inicio)

        def callback_rango(valor: int, mensaje: str) -> None:
            valor_ajustado = inicio + int((max(0, min(100, valor)) / 100) * ancho)
            callback(valor_ajustado, f"{prefijo}: {mensaje}")

        return callback_rango