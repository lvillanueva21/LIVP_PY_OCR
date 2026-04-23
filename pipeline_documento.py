from analizador_pdf import AnalizadorPDF
from procesador_imagen import ProcesadorImagen
from servicio_ocr import ServicioOCR
from modelos import ResultadoAnalisisPDF


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

    def procesar(self, ruta_archivo: str) -> ResultadoAnalisisPDF:
        resultado = self.analizador.analizar(ruta_archivo)

        requiere_preprocesamiento, acciones_preparacion = self.procesador_imagen.evaluar_preparacion(
            resultado
        )

        codigo_estado_ocr, estado_ocr, detalle_ocr_base, apto_para_ocr = self.servicio_ocr.obtener_estado(
            resultado
        )

        resultado.requiere_preprocesamiento = requiere_preprocesamiento
        resultado.acciones_preparacion = acciones_preparacion
        resultado.codigo_estado_ocr = codigo_estado_ocr
        resultado.estado_ocr = estado_ocr
        resultado.detalle_ocr = self._construir_detalle_ocr(
            detalle_ocr_base,
            acciones_preparacion,
        )
        resultado.motor_ocr = self.servicio_ocr.motor_ocr
        resultado.apto_para_ocr = apto_para_ocr

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