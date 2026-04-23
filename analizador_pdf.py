import fitz

from modelos import ResultadoAnalisisPDF, ResultadoPagina
from utilidades import obtener_nombre_archivo, es_pdf_valido


class AnalizadorPDF:
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

            for indice in range(cantidad_paginas):
                pagina = documento.load_page(indice)
                texto = pagina.get_text("text").strip()
                cantidad_caracteres = len(texto)
                pagina_tiene_texto = cantidad_caracteres > 0

                if pagina_tiene_texto:
                    tiene_texto_digital = True

                resumen_paginas.append(
                    ResultadoPagina(
                        numero_pagina=indice + 1,
                        tiene_texto=pagina_tiene_texto,
                        cantidad_caracteres=cantidad_caracteres,
                    )
                )

            necesita_ocr = not tiene_texto_digital

            return ResultadoAnalisisPDF(
                ruta_archivo=ruta_archivo,
                nombre_archivo=obtener_nombre_archivo(ruta_archivo),
                cantidad_paginas=cantidad_paginas,
                tiene_texto_digital=tiene_texto_digital,
                necesita_ocr=necesita_ocr,
                resumen_paginas=resumen_paginas,
            )
        finally:
            documento.close()