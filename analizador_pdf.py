import fitz

from modelos import ResultadoAnalisisPDF, ResultadoPagina
from utilidades import obtener_nombre_archivo, es_pdf_valido


class AnalizadorPDF:
    UMBRAL_TEXTO_SOLIDO = 80
    UMBRAL_TEXTO_MINIMO = 15
    UMBRAL_COBERTURA_IMAGEN_RELEVANTE = 0.35
    UMBRAL_COBERTURA_IMAGEN_ALTA = 0.70

    def analizar(self, ruta_archivo: str) -> ResultadoAnalisisPDF:
        if not es_pdf_valido(ruta_archivo):
            raise FileNotFoundError("El archivo no existe, no es accesible o no es un PDF válido.")

        try:
            documento = fitz.open(ruta_archivo)
        except Exception as error:
            raise ValueError(f"No se pudo abrir el PDF. Detalle: {error}") from error

        try:
            cantidad_paginas = documento.page_count
            resumen_paginas = []
            tiene_texto_digital = False
            textos_documento = []

            for indice in range(cantidad_paginas):
                pagina = documento.load_page(indice)
                texto = pagina.get_text("text").strip()
                cantidad_caracteres = len(texto)
                pagina_tiene_texto = cantidad_caracteres > 0

                if pagina_tiene_texto:
                    tiene_texto_digital = True
                    textos_documento.append(f"===== PÁGINA {indice + 1} =====\n{texto}")

                cantidad_imagenes, cobertura_imagen = self._obtener_estadisticas_imagen(pagina)
                codigo_diagnostico, diagnostico, confianza = self._diagnosticar_pagina(
                    cantidad_caracteres=cantidad_caracteres,
                    cantidad_imagenes=cantidad_imagenes,
                    cobertura_imagen=cobertura_imagen,
                )

                resumen_paginas.append(
                    ResultadoPagina(
                        numero_pagina=indice + 1,
                        tiene_texto=pagina_tiene_texto,
                        cantidad_caracteres=cantidad_caracteres,
                        texto_extraido=texto,
                        cantidad_imagenes=cantidad_imagenes,
                        cobertura_imagen=cobertura_imagen,
                        codigo_diagnostico=codigo_diagnostico,
                        diagnostico=diagnostico,
                        confianza=confianza,
                    )
                )

            (
                codigo_diagnostico_general,
                diagnostico_general,
                detalle_diagnostico,
                confianza_diagnostico,
                necesita_ocr,
                tipo_ocr_sugerido,
            ) = self._diagnosticar_documento(resumen_paginas)

            texto_completo = "\n\n".join(textos_documento).strip()

            return ResultadoAnalisisPDF(
                ruta_archivo=ruta_archivo,
                nombre_archivo=obtener_nombre_archivo(ruta_archivo),
                cantidad_paginas=cantidad_paginas,
                tiene_texto_digital=tiene_texto_digital,
                necesita_ocr=necesita_ocr,
                texto_completo=texto_completo,
                diagnostico_general=diagnostico_general,
                codigo_diagnostico_general=codigo_diagnostico_general,
                detalle_diagnostico=detalle_diagnostico,
                confianza_diagnostico=confianza_diagnostico,
                tipo_ocr_sugerido=tipo_ocr_sugerido,
                resumen_paginas=resumen_paginas,
            )
        finally:
            documento.close()

    def _obtener_estadisticas_imagen(self, pagina: fitz.Page) -> tuple[int, float]:
        cantidad_imagenes_bloque = 0
        area_total_imagenes = 0.0

        try:
            contenido = pagina.get_text("dict")
            bloques = contenido.get("blocks", [])
            area_pagina = max(1.0, pagina.rect.width * pagina.rect.height)

            for bloque in bloques:
                if bloque.get("type") == 1:
                    cantidad_imagenes_bloque += 1
                    bbox = bloque.get("bbox")

                    if bbox and len(bbox) == 4:
                        x0, y0, x1, y1 = bbox
                        ancho = max(0.0, x1 - x0)
                        alto = max(0.0, y1 - y0)
                        area_total_imagenes += ancho * alto

            cobertura_imagen = min(area_total_imagenes / area_pagina, 1.0)
        except Exception:
            cobertura_imagen = 0.0

        try:
            cantidad_imagenes_pdf = len(pagina.get_images(full=True))
        except Exception:
            cantidad_imagenes_pdf = 0

        cantidad_imagenes = max(cantidad_imagenes_bloque, cantidad_imagenes_pdf)
        return cantidad_imagenes, cobertura_imagen

    def _diagnosticar_pagina(
        self,
        cantidad_caracteres: int,
        cantidad_imagenes: int,
        cobertura_imagen: float,
    ) -> tuple[str, str, int]:
        # Regla principal: mucho texto y poca imagen suele indicar PDF digital.
        if cantidad_caracteres >= self.UMBRAL_TEXTO_SOLIDO and cobertura_imagen < self.UMBRAL_COBERTURA_IMAGEN_RELEVANTE:
            return "texto_digital", "Texto digital detectado", 96

        # Texto presente junto con imagen relevante: documento mixto o página híbrida.
        if cantidad_caracteres > 0 and cobertura_imagen >= self.UMBRAL_COBERTURA_IMAGEN_RELEVANTE:
            if cantidad_caracteres >= self.UMBRAL_TEXTO_MINIMO:
                return "mixta", "Mixta o híbrida", 86
            return "mixta", "Texto escaso con imagen relevante", 78

        # Texto corto pero existente, sin fuerte presencia de imagen.
        if cantidad_caracteres >= self.UMBRAL_TEXTO_MINIMO:
            return "texto_digital", "Texto digital detectado", 82

        if 0 < cantidad_caracteres < self.UMBRAL_TEXTO_MINIMO:
            return "texto_digital", "Texto digital breve", 72

        # Sin texto y con imagen dominante: alta probabilidad de escaneo.
        if cantidad_caracteres == 0 and (
            cobertura_imagen >= self.UMBRAL_COBERTURA_IMAGEN_RELEVANTE or cantidad_imagenes > 0
        ):
            if cobertura_imagen >= self.UMBRAL_COBERTURA_IMAGEN_ALTA:
                return "ocr_recomendado", "Sin texto; OCR recomendado", 97
            return "ocr_recomendado", "Sin texto; probable escaneada", 90

        # Sin texto ni imagen clara: puede ser una página en blanco o irregular.
        return "mixta", "Sin texto digital; revisar página", 65

    def _diagnosticar_documento(
        self,
        resumen_paginas: list[ResultadoPagina],
    ) -> tuple[str, str, str, int, bool, str]:
        total_paginas = len(resumen_paginas)

        if total_paginas == 0:
            return (
                "sin_analisis",
                "Sin análisis",
                "El documento no contiene páginas utilizables.",
                0,
                False,
                "-",
            )

        paginas_texto = sum(1 for pagina in resumen_paginas if pagina.codigo_diagnostico == "texto_digital")
        paginas_mixtas = sum(1 for pagina in resumen_paginas if pagina.codigo_diagnostico == "mixta")
        paginas_ocr = sum(1 for pagina in resumen_paginas if pagina.codigo_diagnostico == "ocr_recomendado")

        promedio_confianza = round(
            sum(pagina.confianza for pagina in resumen_paginas) / total_paginas
        )

        if paginas_texto == total_paginas:
            return (
                "texto_digital",
                "PDF con texto digital",
                "Todas las páginas muestran texto digital utilizable. No parece requerir OCR.",
                max(80, promedio_confianza),
                False,
                "No",
            )

        if paginas_ocr == total_paginas:
            return (
                "ocr_recomendado",
                "PDF escaneado / OCR recomendado",
                "No se detectó texto digital suficiente y predominan páginas con indicios fuertes de escaneo.",
                max(85, promedio_confianza),
                True,
                "Sí",
            )

        detalle = (
            f"Se detectaron {paginas_texto} páginas con texto digital, "
            f"{paginas_mixtas} páginas mixtas o irregulares y "
            f"{paginas_ocr} páginas con recomendación clara de OCR."
        )

        tipo_ocr_sugerido = "Parcial" if paginas_texto > 0 else "Sí"
        confianza_documento = max(70, round(promedio_confianza * 0.9))

        return (
            "mixta",
            "PDF mixto o híbrido",
            detalle,
            confianza_documento,
            True,
            tipo_ocr_sugerido,
        )