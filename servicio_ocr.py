import fitz
import pytesseract
from pytesseract import TesseractNotFoundError

from modelos import ResultadoAnalisisPDF
from procesador_imagen import ProcesadorImagen


class ServicioOCR:
    def __init__(self) -> None:
        self.motor_ocr = "Tesseract OCR local"
        self.idioma_ocr = "spa+eng"
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    def esta_configurado(self) -> bool:
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def obtener_estado(self, resultado: ResultadoAnalisisPDF) -> tuple[str, str, str, bool]:
        if resultado.codigo_diagnostico_general == "texto_digital":
            return (
                "no_ejecutado",
                "OCR no ejecutado",
                "El documento ya tiene texto digital suficiente. No hace falta OCR por ahora.",
                False,
            )

        if resultado.codigo_diagnostico_general in {"mixta", "ocr_recomendado"}:
            return (
                "apto",
                "Documento apto para OCR",
                "OCR pendiente para siguiente fase o ejecución automática cuando el motor esté disponible.",
                True,
            )

        return (
            "no_ejecutado",
            "OCR no ejecutado",
            "No hay suficientes datos para definir una estrategia OCR.",
            False,
        )

    def ejecutar_ocr(
        self,
        resultado: ResultadoAnalisisPDF,
        procesador_imagen: ProcesadorImagen,
        callback=None,
    ) -> ResultadoAnalisisPDF:
        if not self.esta_configurado():
            resultado.codigo_estado_ocr = "no_disponible"
            resultado.estado_ocr = "OCR no disponible"
            resultado.detalle_ocr = (
                "Tesseract no está instalado o no está accesible desde el sistema."
            )
            resultado.motor_ocr = "Tesseract OCR local (no disponible)"
            resultado.ocr_disponible = False
            return resultado

        self.idioma_ocr = self._obtener_idioma_ocr()
        self.motor_ocr = f"Tesseract OCR local ({self.idioma_ocr})"
        resultado.motor_ocr = self.motor_ocr
        resultado.ocr_disponible = True

        paginas_objetivo = self._obtener_paginas_objetivo(resultado)
        resultado.paginas_ocr_objetivo = len(paginas_objetivo)

        if not paginas_objetivo:
            resultado.codigo_estado_ocr = "no_ejecutado"
            resultado.estado_ocr = "OCR no ejecutado"
            resultado.detalle_ocr = (
                "No se encontraron páginas candidatas para OCR en esta fase."
            )
            return resultado

        textos_ocr = []
        errores = []
        procesadas = 0

        try:
            documento = fitz.open(resultado.ruta_archivo)
        except Exception as error:
            resultado.codigo_estado_ocr = "error"
            resultado.estado_ocr = "OCR fallido"
            resultado.detalle_ocr = f"No se pudo abrir el PDF para OCR. Detalle: {error}"
            resultado.errores_ocr.append(str(error))
            return resultado

        try:
            total = len(paginas_objetivo)

            for posicion, indice_pagina in enumerate(paginas_objetivo, start=1):
                numero_visible = indice_pagina + 1
                pagina_resultado = resultado.resumen_paginas[indice_pagina]

                if callback:
                    progreso = 30 + int((posicion - 1) / max(1, total) * 60)
                    callback(
                        progreso,
                        f"Aplicando OCR en página {numero_visible} de {resultado.cantidad_paginas}...",
                    )

                try:
                    pagina_pdf = documento.load_page(indice_pagina)
                    imagen = procesador_imagen.preparar_imagen_pagina(pagina_pdf)
                    texto_ocr = pytesseract.image_to_string(
                        imagen,
                        lang=self.idioma_ocr,
                        config="--psm 6",
                    ).strip()

                    pagina_resultado.texto_ocr = texto_ocr
                    pagina_resultado.ocr_ejecutado = True
                    pagina_resultado.ocr_error = ""
                    procesadas += 1

                    if texto_ocr:
                        textos_ocr.append(f"===== PÁGINA {numero_visible} =====\n{texto_ocr}")

                except TesseractNotFoundError:
                    resultado.codigo_estado_ocr = "no_disponible"
                    resultado.estado_ocr = "OCR no disponible"
                    resultado.detalle_ocr = (
                        "Tesseract no está instalado o no está en el PATH del sistema."
                    )
                    resultado.motor_ocr = "Tesseract OCR local (no disponible)"
                    resultado.ocr_disponible = False
                    return resultado
                except Exception as error:
                    mensaje_error = f"Página {numero_visible}: {error}"
                    pagina_resultado.ocr_ejecutado = False
                    pagina_resultado.ocr_error = str(error)
                    errores.append(mensaje_error)

            resultado.texto_ocr_completo = "\n\n".join(textos_ocr).strip()
            resultado.paginas_ocr_procesadas = procesadas
            resultado.errores_ocr = errores

            if procesadas > 0 and not errores:
                resultado.codigo_estado_ocr = "ejecutado"
                resultado.estado_ocr = "OCR ejecutado"
                resultado.detalle_ocr = (
                    f"Se procesaron {procesadas} página(s) con OCR local correctamente."
                )
            elif procesadas > 0 and errores:
                resultado.codigo_estado_ocr = "parcial"
                resultado.estado_ocr = "OCR ejecutado con observaciones"
                resultado.detalle_ocr = (
                    f"Se procesaron {procesadas} página(s), pero hubo incidencias en "
                    f"{len(errores)} página(s)."
                )
            else:
                resultado.codigo_estado_ocr = "error"
                resultado.estado_ocr = "OCR fallido"
                resultado.detalle_ocr = (
                    "No se pudo obtener texto OCR utilizable en las páginas candidatas."
                )

            return resultado
        finally:
            documento.close()

    def _obtener_paginas_objetivo(self, resultado: ResultadoAnalisisPDF) -> list[int]:
        if resultado.codigo_diagnostico_general == "ocr_recomendado":
            return list(range(len(resultado.resumen_paginas)))

        if resultado.codigo_diagnostico_general == "mixta":
            indices = []
            for indice, pagina in enumerate(resultado.resumen_paginas):
                if pagina.codigo_diagnostico in {"mixta", "ocr_recomendado"}:
                    indices.append(indice)
            return indices

        return []

    def _obtener_idioma_ocr(self) -> str:
        try:
            idiomas_disponibles = set(pytesseract.get_languages(config=""))
        except Exception:
            return "eng"

        if "spa" in idiomas_disponibles and "eng" in idiomas_disponibles:
            return "spa+eng"
        if "spa" in idiomas_disponibles:
            return "spa"
        if "eng" in idiomas_disponibles:
            return "eng"

        if idiomas_disponibles:
            return sorted(idiomas_disponibles)[0]

        return "eng"