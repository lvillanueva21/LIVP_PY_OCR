from __future__ import annotations

from pathlib import Path

import fitz
from PIL import Image

from preprocesador_pro import PreprocesadorPro
from variantes_ocr import obtener_variante_por_clave


class GuardadorPDFPro:
    def __init__(self, preprocesador: PreprocesadorPro | None = None) -> None:
        self.preprocesador = preprocesador or PreprocesadorPro()

    def guardar_pdf_optimizado(self, resultado_pro, ruta_destino: str) -> str:
        if resultado_pro is None:
            raise ValueError("No hay resultado PRO para guardar.")

        if not resultado_pro.ruta_archivo:
            raise ValueError("El resultado PRO no tiene ruta de archivo original.")

        ruta_salida = Path(ruta_destino)
        ruta_salida.parent.mkdir(parents=True, exist_ok=True)

        documento = fitz.open(resultado_pro.ruta_archivo)
        imagenes_pdf = []

        try:
            for indice, pagina_resultado in enumerate(resultado_pro.resumen_paginas):
                pagina_pdf = documento.load_page(indice)
                imagen_base = self.preprocesador.renderizar_pagina(pagina_pdf, zoom=2.0)

                imagen_final = imagen_base.convert("RGB")

                clave_variante = pagina_resultado.ocr_variante_clave or ""
                if clave_variante:
                    variante = obtener_variante_por_clave(clave_variante)
                    if variante is not None:
                        imagen_tratada, _ = self.preprocesador.aplicar_variante(
                            imagen_base,
                            variante,
                            idioma_osd="osd",
                        )
                        imagen_final = imagen_tratada.convert("RGB")

                imagenes_pdf.append(imagen_final)

            if not imagenes_pdf:
                raise ValueError("No se pudieron generar páginas para el PDF optimizado.")

            primera = imagenes_pdf[0]
            restantes = imagenes_pdf[1:]

            primera.save(
                ruta_salida,
                "PDF",
                resolution=150.0,
                save_all=True,
                append_images=restantes,
            )

            return str(ruta_salida)
        finally:
            documento.close()
            for imagen in imagenes_pdf:
                try:
                    imagen.close()
                except Exception:
                    pass