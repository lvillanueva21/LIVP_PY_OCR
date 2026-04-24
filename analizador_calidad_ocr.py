import re
import statistics


class AnalizadorCalidadOCR:
    UMBRAL_BAJA_CONFIANZA = 55.0

    def analizar(
        self,
        texto: str,
        datos_ocr: dict,
        *,
        tiempo_total_ms: int,
        tiempo_ocr_ms: int,
    ) -> dict:
        texto_limpio = (texto or "").strip()
        caracteres_totales = len(texto_limpio)
        caracteres_utiles = sum(1 for caracter in texto_limpio if caracter.isalnum())

        palabras_detectadas = self._extraer_palabras_ocr(datos_ocr)
        cantidad_palabras = len(palabras_detectadas)

        confidencias = self._extraer_confianzas_validas(datos_ocr)
        confianza_promedio = round(sum(confidencias) / len(confidencias), 2) if confidencias else 0.0
        confianza_mediana = round(statistics.median(confidencias), 2) if confidencias else 0.0

        palabras_baja_confianza = sum(
            1 for palabra in palabras_detectadas if palabra["confianza"] < self.UMBRAL_BAJA_CONFIANZA
        )

        ruido_textual = self._calcular_ruido_textual(texto_limpio)
        ratio_util = round(caracteres_utiles / max(1, caracteres_totales), 4)

        score_calidad = self._calcular_score_calidad(
            caracteres_utiles=caracteres_utiles,
            cantidad_palabras=cantidad_palabras,
            confianza_promedio=confianza_promedio,
            ratio_util=ratio_util,
            ruido_textual=ruido_textual,
            palabras_baja_confianza=palabras_baja_confianza,
        )

        return {
            "texto": texto_limpio,
            "caracteres_totales": caracteres_totales,
            "caracteres_utiles": caracteres_utiles,
            "cantidad_palabras": cantidad_palabras,
            "confianza_promedio": confianza_promedio,
            "confianza_mediana": confianza_mediana,
            "palabras_baja_confianza": palabras_baja_confianza,
            "ruido_textual": ruido_textual,
            "ratio_util": ratio_util,
            "tiempo_total_ms": tiempo_total_ms,
            "tiempo_ocr_ms": tiempo_ocr_ms,
            "score_calidad": score_calidad,
        }

    def _extraer_palabras_ocr(self, datos_ocr: dict) -> list[dict]:
        textos = datos_ocr.get("text", []) or []
        confianzas = datos_ocr.get("conf", []) or []

        salida = []
        for texto, confianza in zip(textos, confianzas):
            palabra = (texto or "").strip()
            if not palabra:
                continue

            try:
                valor_confianza = float(confianza)
            except Exception:
                valor_confianza = -1.0

            if valor_confianza < 0:
                continue

            if not re.search(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]", palabra):
                continue

            salida.append(
                {
                    "texto": palabra,
                    "confianza": valor_confianza,
                }
            )

        return salida

    def _extraer_confianzas_validas(self, datos_ocr: dict) -> list[float]:
        palabras = self._extraer_palabras_ocr(datos_ocr)
        return [palabra["confianza"] for palabra in palabras if palabra["confianza"] >= 0]

    def _calcular_ruido_textual(self, texto: str) -> float:
        if not texto:
            return 1.0

        caracteres_totales = len(texto)
        caracteres_ruidosos = sum(
            1
            for caracter in texto
            if not (
                caracter.isalnum()
                or caracter.isspace()
                or caracter in ".,:;/()-_%$#°*+[]{}"
            )
        )
        return round(caracteres_ruidosos / max(1, caracteres_totales), 4)

    def _calcular_score_calidad(
        self,
        *,
        caracteres_utiles: int,
        cantidad_palabras: int,
        confianza_promedio: float,
        ratio_util: float,
        ruido_textual: float,
        palabras_baja_confianza: int,
    ) -> float:
        score = 0.0
        score += min(28.0, caracteres_utiles / 25.0)
        score += min(22.0, cantidad_palabras * 1.0)
        score += min(30.0, confianza_promedio * 0.35)
        score += min(20.0, ratio_util * 20.0)

        score -= min(18.0, ruido_textual * 90.0)
        score -= min(12.0, palabras_baja_confianza * 0.8)

        return round(max(0.0, min(100.0, score)), 2)