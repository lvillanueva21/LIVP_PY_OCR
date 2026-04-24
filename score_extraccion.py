import re

from metricas_analisis import MetricaDocumentoModo, MetricaPaginaModo


class ScoreExtraccion:
    PESOS_DOCUMENTO = {
        "campos": 6,
        "legibilidad": 5,
        "confianza": 4,
        "texto_util": 3,
        "estabilidad": 2,
        "velocidad": 1,
    }

    PESOS_PAGINA = {
        "legibilidad": 5,
        "confianza": 4,
        "texto_util": 3,
        "estabilidad": 2,
        "velocidad": 1,
    }

    def calcular_ruido_textual(self, texto: str) -> float:
        texto = (texto or "").strip()
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

    def contar_palabras_utiles(self, texto: str) -> int:
        return len(re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]{2,}", texto or ""))

    def puntuar_pagina(self, metrica: MetricaPaginaModo) -> MetricaPaginaModo:
        score_legibilidad = self._score_legibilidad_pagina(metrica)
        score_confianza = self._score_confianza_pagina(metrica)
        score_texto_util = self._score_texto_util_pagina(metrica)
        score_estabilidad = self._score_estabilidad_pagina(metrica)
        score_velocidad = self._score_velocidad_pagina(metrica)

        score_total = self._combinar_scores(
            {
                "legibilidad": score_legibilidad,
                "confianza": score_confianza,
                "texto_util": score_texto_util,
                "estabilidad": score_estabilidad,
                "velocidad": score_velocidad,
            },
            self.PESOS_PAGINA,
        )

        metrica.score_legibilidad = score_legibilidad
        metrica.score_confianza = score_confianza
        metrica.score_texto_util = score_texto_util
        metrica.score_estabilidad = score_estabilidad
        metrica.score_velocidad = score_velocidad
        metrica.score_total = score_total
        return metrica

    def puntuar_documento(self, metrica: MetricaDocumentoModo) -> MetricaDocumentoModo:
        score_campos = self._score_campos_documento(metrica)
        score_legibilidad = self._score_legibilidad_documento(metrica)
        score_confianza = self._score_confianza_documento(metrica)
        score_texto_util = self._score_texto_util_documento(metrica)
        score_estabilidad = self._score_estabilidad_documento(metrica)
        score_velocidad = self._score_velocidad_documento(metrica)

        score_total = self._combinar_scores(
            {
                "campos": score_campos,
                "legibilidad": score_legibilidad,
                "confianza": score_confianza,
                "texto_util": score_texto_util,
                "estabilidad": score_estabilidad,
                "velocidad": score_velocidad,
            },
            self.PESOS_DOCUMENTO,
        )

        metrica.score_campos = score_campos
        metrica.score_legibilidad = score_legibilidad
        metrica.score_confianza = score_confianza
        metrica.score_texto_util = score_texto_util
        metrica.score_estabilidad = score_estabilidad
        metrica.score_velocidad = score_velocidad
        metrica.score_total = score_total
        return metrica

    def _score_legibilidad_pagina(self, metrica: MetricaPaginaModo) -> float:
        if metrica.total_caracteres_utiles <= 0:
            return 0.0

        base = 100.0 - min(55.0, metrica.ruido_textual * 120.0)

        if metrica.cantidad_palabras < 5 and metrica.total_caracteres_utiles > 0:
            base -= 15.0

        if metrica.fuente_texto == "texto_digital":
            base += 6.0

        return round(max(0.0, min(100.0, base)), 2)

    def _score_confianza_pagina(self, metrica: MetricaPaginaModo) -> float:
        if metrica.fuente_texto == "texto_digital" and metrica.confianza_ocr_promedio <= 0:
            return 88.0

        return round(max(0.0, min(100.0, metrica.confianza_ocr_promedio)), 2)

    def _score_texto_util_pagina(self, metrica: MetricaPaginaModo) -> float:
        if metrica.total_caracteres_utiles <= 0:
            return 0.0

        score_caracteres = min(60.0, metrica.total_caracteres_utiles / 10.0)
        score_palabras = min(40.0, metrica.cantidad_palabras * 2.0)
        return round(min(100.0, score_caracteres + score_palabras), 2)

    def _score_estabilidad_pagina(self, metrica: MetricaPaginaModo) -> float:
        score = 100.0
        score -= min(30.0, metrica.problemas_detectados * 8.0)
        score -= max(0, metrica.numero_intentos - 1) * 4.0

        if metrica.total_caracteres_utiles == 0:
            score -= 25.0

        return round(max(0.0, min(100.0, score)), 2)

    def _score_velocidad_pagina(self, metrica: MetricaPaginaModo) -> float:
        tiempo = metrica.tiempo_total_ms

        if tiempo <= 0:
            return 75.0
        if tiempo <= 500:
            return 100.0
        if tiempo <= 1200:
            return 88.0
        if tiempo <= 2500:
            return 72.0
        if tiempo <= 5000:
            return 58.0
        return 42.0

    def _score_campos_documento(self, metrica: MetricaDocumentoModo) -> float:
        return round((metrica.cantidad_campos_detectados / 8) * 100, 2)

    def _score_legibilidad_documento(self, metrica: MetricaDocumentoModo) -> float:
        base = 100.0 - min(45.0, metrica.ruido_textual_promedio * 100.0)
        base -= min(20.0, metrica.paginas_revision_recomendada * 3.0)
        if metrica.paginas_con_texto_digital > 0:
            base += 4.0
        return round(max(0.0, min(100.0, base)), 2)

    def _score_confianza_documento(self, metrica: MetricaDocumentoModo) -> float:
        if metrica.paginas_con_ocr == 0 and metrica.paginas_con_texto_digital > 0:
            return 88.0
        return round(max(0.0, min(100.0, metrica.confianza_ocr_promedio)), 2)

    def _score_texto_util_documento(self, metrica: MetricaDocumentoModo) -> float:
        if metrica.total_caracteres_utiles <= 0:
            return 0.0

        score_caracteres = min(60.0, metrica.total_caracteres_utiles / 200.0)
        score_palabras = min(40.0, metrica.total_palabras / 10.0)
        return round(min(100.0, score_caracteres + score_palabras), 2)

    def _score_estabilidad_documento(self, metrica: MetricaDocumentoModo) -> float:
        score = 100.0
        score -= min(35.0, metrica.problemas_detectados * 3.5)
        score -= min(20.0, metrica.paginas_revision_recomendada * 2.5)

        if metrica.total_caracteres_utiles == 0:
            score -= 30.0

        return round(max(0.0, min(100.0, score)), 2)

    def _score_velocidad_documento(self, metrica: MetricaDocumentoModo) -> float:
        tiempo = metrica.tiempo_total_ms

        if tiempo <= 0:
            return 75.0
        if tiempo <= 2000:
            return 100.0
        if tiempo <= 5000:
            return 86.0
        if tiempo <= 10000:
            return 72.0
        if tiempo <= 20000:
            return 58.0
        if tiempo <= 40000:
            return 44.0
        return 32.0

    def _combinar_scores(self, scores: dict[str, float], pesos: dict[str, int]) -> float:
        total_pesos = sum(pesos.values())
        acumulado = 0.0

        for clave, peso in pesos.items():
            acumulado += scores.get(clave, 0.0) * peso

        return round(acumulado / total_pesos, 2)