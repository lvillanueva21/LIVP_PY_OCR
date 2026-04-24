import re

import cv2
import fitz
import numpy as np
import pytesseract
from PIL import Image, ImageOps

from variantes_ocr import VarianteOCR


class PreprocesadorPro:
    def renderizar_pagina(self, pagina_pdf: fitz.Page, zoom: float = 2.0) -> Image.Image:
        matriz = fitz.Matrix(zoom, zoom)
        pixmap = pagina_pdf.get_pixmap(matrix=matriz, alpha=False)
        imagen = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        return imagen

    def aplicar_variante(
        self,
        imagen_original: Image.Image,
        variante: VarianteOCR,
        idioma_osd: str = "osd",
    ) -> tuple[Image.Image, list[str]]:
        observaciones = []
        imagen = imagen_original.convert("RGB")

        if variante.usar_orientacion_osd:
            imagen, rotacion, obs = self._corregir_orientacion_osd(imagen, idioma_osd)
            observaciones.extend(obs)
            if rotacion:
                observaciones.append(f"Orientación corregida: {rotacion}°.")

        if variante.escala and variante.escala != 1.0:
            imagen = self._reescalar(imagen, variante.escala)
            observaciones.append(f"Reescalado x{variante.escala:.1f}.")

        imagen = ImageOps.grayscale(imagen)

        if variante.usar_autocontraste:
            imagen = ImageOps.autocontrast(imagen, cutoff=1)
            observaciones.append("Autocontraste aplicado.")

        arreglo = np.array(imagen)

        if variante.usar_denoise:
            arreglo = cv2.fastNlMeansDenoising(arreglo, None, 10, 7, 21)
            observaciones.append("Reducción de ruido aplicada.")

        if variante.usar_deskew:
            arreglo, angulo = self._deskew(arreglo)
            if abs(angulo) > 0.2:
                observaciones.append(f"Deskew aplicado ({angulo:.2f}°).")

        if variante.usar_binarizacion_adaptativa:
            arreglo = cv2.adaptiveThreshold(
                arreglo,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                31,
                15,
            )
            observaciones.append("Binarización adaptativa aplicada.")
        elif variante.usar_binarizacion_simple:
            _, arreglo = cv2.threshold(
                arreglo,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU,
            )
            observaciones.append("Binarización simple aplicada.")

        if variante.usar_sharpen:
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            arreglo = cv2.filter2D(arreglo, -1, kernel)
            observaciones.append("Realce moderado de nitidez aplicado.")

        imagen_salida = Image.fromarray(arreglo)
        return imagen_salida, observaciones

    def _reescalar(self, imagen: Image.Image, factor: float) -> Image.Image:
        ancho = max(1, int(imagen.width * factor))
        alto = max(1, int(imagen.height * factor))
        return imagen.resize((ancho, alto), Image.Resampling.LANCZOS)

    def _corregir_orientacion_osd(
        self,
        imagen: Image.Image,
        idioma_osd: str,
    ) -> tuple[Image.Image, int, list[str]]:
        observaciones = []

        try:
            texto_osd = pytesseract.image_to_osd(imagen, lang=idioma_osd)
            coincidencia = re.search(r"Rotate:\s+(\d+)", texto_osd)
            if not coincidencia:
                return imagen, 0, observaciones

            rotacion = int(coincidencia.group(1))
            if rotacion not in {90, 180, 270}:
                return imagen, 0, observaciones

            imagen_corregida = imagen.rotate(360 - rotacion, expand=True)
            return imagen_corregida, rotacion, observaciones
        except Exception:
            observaciones.append("No se pudo determinar orientación por OSD.")
            return imagen, 0, observaciones

    def _deskew(self, arreglo_gris: np.ndarray) -> tuple[np.ndarray, float]:
        try:
            invertida = cv2.bitwise_not(arreglo_gris)
            _, umbral = cv2.threshold(
                invertida,
                0,
                255,
                cv2.THRESH_BINARY + cv2.THRESH_OTSU,
            )
            coordenadas = np.column_stack(np.where(umbral > 0))

            if coordenadas.size == 0:
                return arreglo_gris, 0.0

            angulo = cv2.minAreaRect(coordenadas)[-1]

            if angulo < -45:
                angulo_correccion = -(90 + angulo)
            else:
                angulo_correccion = -angulo

            if abs(angulo_correccion) < 0.2:
                return arreglo_gris, 0.0

            centro = (arreglo_gris.shape[1] // 2, arreglo_gris.shape[0] // 2)
            matriz = cv2.getRotationMatrix2D(centro, angulo_correccion, 1.0)
            corregida = cv2.warpAffine(
                arreglo_gris,
                matriz,
                (arreglo_gris.shape[1], arreglo_gris.shape[0]),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
            return corregida, angulo_correccion
        except Exception:
            return arreglo_gris, 0.0