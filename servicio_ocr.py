from modelos import ResultadoAnalisisPDF


class ServicioOCR:
    def __init__(self) -> None:
        self.motor_ocr = "Pendiente de integrar"

    def esta_configurado(self) -> bool:
        return False

    def obtener_estado(self, resultado: ResultadoAnalisisPDF) -> tuple[str, str, str, bool]:
        if resultado.codigo_diagnostico_general == "texto_digital":
            return (
                "no_ejecutado",
                "OCR no ejecutado",
                "El documento ya tiene texto digital suficiente. No hace falta OCR por ahora.",
                False,
            )

        if resultado.codigo_diagnostico_general == "mixta":
            return (
                "apto",
                "Documento apto para OCR",
                "OCR pendiente para siguiente fase. Conviene aplicar OCR solo a páginas mixtas o sin texto suficiente.",
                True,
            )

        if resultado.codigo_diagnostico_general == "ocr_recomendado":
            return (
                "apto",
                "Documento apto para OCR",
                "OCR pendiente para siguiente fase. El documento parece escaneado y es buen candidato para OCR completo.",
                True,
            )

        return (
            "no_ejecutado",
            "OCR no ejecutado",
            "No hay suficientes datos para definir una estrategia OCR.",
            False,
        )

    def ejecutar_ocr(self, *args, **kwargs):
        raise NotImplementedError(
            "La integración OCR aún no está implementada en esta fase del proyecto."
        )