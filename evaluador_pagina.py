import re
import statistics

import cv2
import numpy as np


class EvaluadorPagina:
    def analizar_condicion_pagina(self, pagina_resultado, imagen_pil) -> dict:
        gris = np.array(imagen_pil.convert("L"))
        brillo_promedio = float(np.mean(gris))
        contraste = float(np.std(gris))
        varianza_laplaciana = float(cv2.Laplacian(gris, cv2.CV_64F).var())

        observaciones = []

        es_oscura = brillo_promedio < 85
        es_muy_clara = brillo_promedio > 220
        bajo_contraste = contraste < 35
        probable_borroso = varianza_laplaciana < 70
        sospecha_orientacion = imagen_pil.width > imagen_pil.height * 1.35

        if es_oscura:
            observaciones.append("Imagen oscura.")
        if es_muy_clara:
            observaciones.append("Imagen muy clara.")
        if bajo_contraste:
            observaciones.append("Bajo contraste.")
        if probable_borroso:
            observaciones.append("Posible desenfoque o baja nitidez.")
        if sospecha_orientacion:
            observaciones.append("Posible orientación incorrecta.")

        es_problematica = (
            not pagina_resultado.tiene_texto
            or pagina_resultado.cantidad_caracteres < 40
            or pagina_resultado.cobertura_imagen >= 0.70
            or es_oscura
            or es_muy_clara
            or bajo_contraste
            or probable_borroso
        )

        es_muy_problematica = (
            pagina_resultado.cantidad_caracteres == 0
            and pagina_resultado.cobertura_imagen >= 0.85
        ) or (sum([es_oscura, es_muy_clara, bajo_contraste, probable_borroso]) >= 2)

        return {
            "es_problematica": es_problematica,
            "es_muy_problematica": es_muy_problematica,
            "sospecha_orientacion": sospecha_orientacion,
            "brillo_promedio": round(brillo_promedio, 2),
            "contraste": round(contraste, 2),
            "nitidez": round(varianza_laplaciana, 2),
            "observaciones": observaciones,
        }

    def evaluar_intento(
        self,
        texto: str,
        datos_ocr: dict,
        *,
        tiempo_total_ms: int,
        tiempo_ocr_ms: int,
        observaciones: list[str],
    ) -> dict:
        texto_limpio = (texto or "").strip()
        caracteres_totales = len(texto_limpio)
        caracteres_utiles = sum(1 for caracter in texto_limpio if caracter.isalnum())
        palabras = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]{2,}", texto_limpio)
        cantidad_palabras = len(palabras)

        confidencias = self._extraer_confianzas_validas(datos_ocr)
        confianza_promedio = round(sum(confidencias) / len(confidencias), 2) if confidencias else 0.0
        confianza_mediana = round(statistics.median(confidencias), 2) if confidencias else 0.0

        ratio_util = 0.0
        if caracteres_totales > 0:
            ratio_util = caracteres_utiles / caracteres_totales

        simbolos_raros = sum(1 for caracter in texto_limpio if not (caracter.isalnum() or caracter.isspace() or caracter in ".,:;/()-_%$#°"))
        penalizacion_ruido = min(25.0, simbolos_raros * 0.4)

        score = (
            min(30.0, cantidad_palabras * 1.2)
            + min(25.0, caracteres_utiles / 20.0)
            + min(30.0, confianza_promedio * 0.35)
            + min(15.0, ratio_util * 15.0)
            - penalizacion_ruido
        )
        score = round(max(0.0, min(100.0, score)), 2)

        observaciones_intento = list(observaciones)
        if cantidad_palabras == 0:
            observaciones_intento.append("OCR devolvió pocas o ninguna palabra útil.")
        if confianza_promedio < 45 and cantidad_palabras > 0:
            observaciones_intento.append("Confianza OCR baja.")
        if simbolos_raros > max(10, caracteres_totales * 0.1):
            observaciones_intento.append("Texto con alto ruido simbólico.")

        return {
            "texto": texto_limpio,
            "caracteres_totales": caracteres_totales,
            "caracteres_utiles": caracteres_utiles,
            "cantidad_palabras": cantidad_palabras,
            "confianza_promedio": confianza_promedio,
            "confianza_mediana": confianza_mediana,
            "ratio_util": round(ratio_util, 4),
            "score": score,
            "tiempo_total_ms": tiempo_total_ms,
            "tiempo_ocr_ms": tiempo_ocr_ms,
            "observaciones": self._limpiar_observaciones(observaciones_intento),
        }

    def _extraer_confianzas_validas(self, datos_ocr: dict) -> list[float]:
        salida = []
        for valor in datos_ocr.get("conf", []):
            try:
                numero = float(valor)
                if numero >= 0:
                    salida.append(numero)
            except Exception:
                continue
        return salida

    def _limpiar_observaciones(self, observaciones: list[str]) -> list[str]:
        salida = []
        for observacion in observaciones:
            observacion = (observacion or "").strip()
            if observacion and observacion not in salida:
                salida.append(observacion)
        return salida