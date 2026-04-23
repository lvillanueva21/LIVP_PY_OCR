from modelos import ResultadoAnalisisPDF


class ProcesadorImagen:
    def evaluar_preparacion(self, resultado: ResultadoAnalisisPDF) -> tuple[bool, list[str]]:
        paginas_candidatas = [
            pagina
            for pagina in resultado.resumen_paginas
            if pagina.codigo_diagnostico in {"mixta", "ocr_recomendado"}
        ]

        if not paginas_candidatas:
            return False, []

        acciones = []

        if resultado.codigo_diagnostico_general == "mixta":
            acciones.append(
                f"Procesar OCR solo en {len(paginas_candidatas)} página(s) candidata(s)"
            )
        else:
            acciones.append("Procesar OCR en todas las páginas del documento")

        if any(pagina.cobertura_imagen >= 0.35 for pagina in paginas_candidatas):
            acciones.append("Corregir inclinación o rotación antes de OCR")
            acciones.append("Mejorar contraste de las páginas candidatas")

        if any(0 < pagina.cantidad_caracteres < 15 for pagina in paginas_candidatas):
            acciones.append("Conservar el texto digital útil y complementar solo donde falte")

        acciones_limpias = self._eliminar_duplicados(acciones)
        return True, acciones_limpias

    def _eliminar_duplicados(self, acciones: list[str]) -> list[str]:
        acciones_unicas = []
        for accion in acciones:
            if accion not in acciones_unicas:
                acciones_unicas.append(accion)
        return acciones_unicas