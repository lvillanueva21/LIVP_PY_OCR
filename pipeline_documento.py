from analizador_pdf import AnalizadorPDF
from modelos import ResultadoAnalisisPDF
from procesador_imagen import ProcesadorImagen
from servicio_ocr import ServicioOCR


class PipelineDocumento:
    def __init__(
        self,
        analizador: AnalizadorPDF | None = None,
        procesador_imagen: ProcesadorImagen | None = None,
        servicio_ocr: ServicioOCR | None = None,
    ) -> None:
        self.analizador = analizador or AnalizadorPDF()
        self.procesador_imagen = procesador_imagen or ProcesadorImagen()
        self.servicio_ocr = servicio_ocr or ServicioOCR()

    def procesar(self, ruta_archivo: str, callback=None) -> ResultadoAnalisisPDF:
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
            self._emitir_progreso(callback, 100, "Análisis completado. OCR no requerido.")
            return resultado

        if not self.servicio_ocr.esta_configurado():
            resultado.codigo_estado_ocr = "no_disponible"
            resultado.estado_ocr = "OCR no disponible"
            resultado.detalle_ocr = self._construir_detalle_ocr(
                "Tesseract no está instalado o no está en el PATH del sistema.",
                acciones_preparacion,
            )
            resultado.motor_ocr = "Tesseract OCR local (no disponible)"
            resultado.ocr_disponible = False
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

        mensaje_final = "Procesamiento completado."
        if resultado.codigo_estado_ocr == "ejecutado":
            mensaje_final = "Procesamiento completado con OCR."
        elif resultado.codigo_estado_ocr == "parcial":
            mensaje_final = "Procesamiento completado con OCR y observaciones."
        elif resultado.codigo_estado_ocr in {"error", "no_disponible"}:
            mensaje_final = "Procesamiento completado con incidencias OCR."

        self._emitir_progreso(callback, 100, mensaje_final)
        return resultado

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