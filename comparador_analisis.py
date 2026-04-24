from __future__ import annotations

from typing import Iterable

from metricas_analisis import (
    MetricaDocumentoModo,
    MetricaPaginaModo,
    ResumenComparacionAnalisis,
)
from modos_analisis import ModoAnalisis


class ComparadorAnalisis:
    TOTAL_CAMPOS_ESPERADOS = 8

    def construir_metricas_paginas(self, resultado) -> list[MetricaPaginaModo]:
        paginas = resultado.resumen_paginas or []
        tiempo_total = getattr(resultado, "tiempo_total_ms", 0)
        tiempo_por_pagina = int(tiempo_total / max(1, len(paginas)))

        metricas = []
        for pagina in paginas:
            observaciones = []

            if pagina.codigo_diagnostico == "ocr_recomendado":
                observaciones.append("Página candidata a OCR.")
            elif pagina.codigo_diagnostico == "mixta":
                observaciones.append("Página mixta o híbrida.")

            if pagina.ocr_error:
                observaciones.append(f"OCR con error: {pagina.ocr_error}")

            fuente_texto = "sin_texto"
            if pagina.tiene_texto and pagina.texto_extraido.strip():
                fuente_texto = "texto_digital"
            elif pagina.ocr_ejecutado and pagina.texto_ocr.strip():
                fuente_texto = "texto_ocr"

            caracteres_digital = len((pagina.texto_extraido or "").strip())
            caracteres_ocr = len((pagina.texto_ocr or "").strip())

            metricas.append(
                MetricaPaginaModo(
                    numero_pagina=pagina.numero_pagina,
                    fuente_texto=fuente_texto,
                    caracteres_texto_digital=caracteres_digital,
                    caracteres_texto_ocr=caracteres_ocr,
                    total_caracteres_utiles=max(caracteres_digital, caracteres_ocr),
                    cantidad_campos_detectados=0,
                    tiempo_estimado_ms=tiempo_por_pagina,
                    observaciones=observaciones,
                )
            )

        return metricas

    def construir_metricas_documento(self, resultado) -> MetricaDocumentoModo:
        paginas = resultado.resumen_paginas or []
        campos_detectados = sum(1 for campo in resultado.campos_extraidos if campo.detectado)

        paginas_con_texto_digital = sum(1 for pagina in paginas if pagina.tiene_texto)
        paginas_con_ocr = sum(1 for pagina in paginas if pagina.ocr_ejecutado and pagina.texto_ocr.strip())

        texto_fuente = (
            (resultado.texto_final_revisado or "").strip()
            or (resultado.texto_completo or "").strip()
            or (resultado.texto_ocr_completo or "").strip()
        )

        score_campos = self._calcular_score_campos(campos_detectados)
        score_legibilidad = self._calcular_score_legibilidad(texto_fuente)
        score_confianza = self._calcular_score_confianza(resultado)
        score_texto_util = self._calcular_score_texto_util(texto_fuente)
        score_estabilidad = self._calcular_score_estabilidad(resultado)
        score_velocidad = self._calcular_score_velocidad(getattr(resultado, "tiempo_total_ms", 0))

        score_total = self._combinar_scores(
            score_campos=score_campos,
            score_legibilidad=score_legibilidad,
            score_confianza=score_confianza,
            score_texto_util=score_texto_util,
            score_estabilidad=score_estabilidad,
            score_velocidad=score_velocidad,
        )

        observaciones = []
        if resultado.codigo_diagnostico_general == "ocr_recomendado":
            observaciones.append("Documento con alta dependencia de OCR.")
        if resultado.codigo_estado_ocr in {"parcial", "error", "no_disponible"}:
            observaciones.append(f"Estado OCR: {resultado.estado_ocr}")
        if getattr(resultado, "observaciones_modo", None):
            observaciones.extend(resultado.observaciones_modo)

        return MetricaDocumentoModo(
            modo=resultado.modo_analisis,
            etiqueta_modo=resultado.etiqueta_modo,
            paginas_totales=resultado.cantidad_paginas,
            paginas_con_texto_digital=paginas_con_texto_digital,
            paginas_con_ocr=paginas_con_ocr,
            total_caracteres_utiles=len(texto_fuente),
            cantidad_campos_detectados=campos_detectados,
            tiempo_total_ms=getattr(resultado, "tiempo_total_ms", 0),
            score_campos=score_campos,
            score_legibilidad=score_legibilidad,
            score_confianza=score_confianza,
            score_texto_util=score_texto_util,
            score_estabilidad=score_estabilidad,
            score_velocidad=score_velocidad,
            score_total=score_total,
            observaciones=self._limpiar_lista(observaciones),
        )

    def recomendar_modo(self, resultado) -> str:
        paginas = resultado.resumen_paginas or []
        paginas_sin_texto = sum(1 for pagina in paginas if not pagina.tiene_texto)
        paginas_mixtas = sum(1 for pagina in paginas if pagina.codigo_diagnostico == "mixta")

        if resultado.codigo_diagnostico_general == "ocr_recomendado":
            return "Se recomienda modo Pro: predominan páginas escaneadas y OCR intensivo."

        if paginas_mixtas > 0 or paginas_sin_texto >= max(2, int(resultado.cantidad_paginas * 0.3)):
            return "Se recomienda modo Pro: hay páginas mixtas o sin texto suficiente."

        return "Modo Básico suficiente para este documento, salvo que quieras comparar."

    def comparar(self, resultado_basico, resultado_pro) -> ResumenComparacionAnalisis:
        metricas_basico = resultado_basico.metricas_documento_modo
        metricas_pro = resultado_pro.metricas_documento_modo

        score_basico = metricas_basico.score_total if metricas_basico else 0.0
        score_pro = metricas_pro.score_total if metricas_pro else 0.0
        diferencia = abs(score_basico - score_pro)

        if diferencia <= 3:
            modo_ganador = "empate"
            etiqueta_ganador = "Empate"
            motivo = "Ambos modos quedaron demasiado cerca en score comparativo."
        elif score_pro > score_basico:
            modo_ganador = ModoAnalisis.PRO
            etiqueta_ganador = "Ganó Pro"
            motivo = "El modo Pro obtuvo mejor score comparativo estimado."
        else:
            modo_ganador = ModoAnalisis.BASICO
            etiqueta_ganador = "Ganó Básico"
            motivo = "El modo Básico obtuvo mejor score comparativo estimado."

        recomendacion = resultado_pro.recomendacion_modo or resultado_basico.recomendacion_modo
        observaciones = []

        if getattr(resultado_pro, "es_provisional", False):
            observaciones.append(
                "El modo Pro aún es provisional en esta fase y reutiliza la base del modo Básico."
            )

        return ResumenComparacionAnalisis(
            modo_ganador=modo_ganador,
            etiqueta_ganador=etiqueta_ganador,
            score_basico=score_basico,
            score_pro=score_pro,
            diferencia_absoluta=diferencia,
            motivo=motivo,
            recomendacion=recomendacion,
            observaciones=observaciones,
        )

    def _calcular_score_campos(self, campos_detectados: int) -> float:
        return round((campos_detectados / self.TOTAL_CAMPOS_ESPERADOS) * 100, 2)

    def _calcular_score_legibilidad(self, texto: str) -> float:
        if not texto:
            return 0.0

        caracteres = len(texto)
        letras_numeros = sum(1 for caracter in texto if caracter.isalnum())
        ratio_util = letras_numeros / max(1, caracteres)

        score = ratio_util * 100
        return round(max(0.0, min(100.0, score)), 2)

    def _calcular_score_confianza(self, resultado) -> float:
        paginas = resultado.resumen_paginas or []
        if not paginas:
            return float(resultado.confianza_diagnostico)

        promedio_paginas = sum(pagina.confianza for pagina in paginas) / len(paginas)
        score = (promedio_paginas + float(resultado.confianza_diagnostico)) / 2
        return round(max(0.0, min(100.0, score)), 2)

    def _calcular_score_texto_util(self, texto: str) -> float:
        longitud = len(texto.strip())
        if longitud <= 0:
            return 0.0

        score = min(100.0, (longitud / 2000) * 100)
        return round(score, 2)

    def _calcular_score_estabilidad(self, resultado) -> float:
        score = 100.0
        score -= len(resultado.errores_ocr or []) * 15

        if resultado.codigo_estado_ocr == "error":
            score -= 25
        elif resultado.codigo_estado_ocr == "parcial":
            score -= 10
        elif resultado.codigo_estado_ocr == "no_disponible":
            score -= 20

        if not (resultado.texto_completo.strip() or resultado.texto_ocr_completo.strip()):
            score -= 20

        return round(max(0.0, min(100.0, score)), 2)

    def _calcular_score_velocidad(self, tiempo_total_ms: int) -> float:
        if tiempo_total_ms <= 0:
            return 75.0
        if tiempo_total_ms <= 2000:
            return 100.0
        if tiempo_total_ms <= 5000:
            return 85.0
        if tiempo_total_ms <= 10000:
            return 70.0
        if tiempo_total_ms <= 20000:
            return 55.0
        return 40.0

    def _combinar_scores(
        self,
        *,
        score_campos: float,
        score_legibilidad: float,
        score_confianza: float,
        score_texto_util: float,
        score_estabilidad: float,
        score_velocidad: float,
    ) -> float:
        pesos = {
            "campos": 6,
            "legibilidad": 5,
            "confianza": 4,
            "texto_util": 3,
            "estabilidad": 2,
            "velocidad": 1,
        }

        total_pesos = sum(pesos.values())
        acumulado = (
            score_campos * pesos["campos"]
            + score_legibilidad * pesos["legibilidad"]
            + score_confianza * pesos["confianza"]
            + score_texto_util * pesos["texto_util"]
            + score_estabilidad * pesos["estabilidad"]
            + score_velocidad * pesos["velocidad"]
        )
        return round(acumulado / total_pesos, 2)

    def _limpiar_lista(self, valores: Iterable[str]) -> list[str]:
        salida = []
        for valor in valores:
            valor = (valor or "").strip()
            if valor and valor not in salida:
                salida.append(valor)
        return salida