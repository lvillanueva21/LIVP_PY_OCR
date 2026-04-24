from dataclasses import dataclass, field

from metricas_analisis import MetricaDocumentoModo
from modos_analisis import ModoAnalisis


@dataclass
class RecomendacionModo:
    modo_recomendado: str
    mensaje: str
    razones: list[str] = field(default_factory=list)
    requiere_revision_manual: bool = False
    motivo_revision_manual: str = ""


class RecomendadorModo:
    def recomendar(self, resultado, metrica: MetricaDocumentoModo) -> RecomendacionModo:
        razones = []

        if resultado.codigo_diagnostico_general == "ocr_recomendado":
            razones.append("El documento fue clasificado como escaneado o altamente dependiente de OCR.")

        if resultado.codigo_diagnostico_general == "mixta":
            razones.append("El documento es mixto o híbrido.")

        if metrica.paginas_revision_recomendada > 0:
            razones.append(
                f"Hay {metrica.paginas_revision_recomendada} página(s) con baja calidad estimada o revisión sugerida."
            )

        if metrica.problemas_detectados > 0:
            razones.append(
                f"Se detectaron {metrica.problemas_detectados} incidencia(s) en OCR o legibilidad."
            )

        if metrica.cantidad_campos_detectados <= 3 and resultado.cantidad_paginas > 0:
            razones.append("Se detectaron pocos campos clave; conviene intentar un modo más fuerte o revisar manualmente.")

        if resultado.modo_analisis == ModoAnalisis.PRO:
            if metrica.paginas_revision_recomendada > 0:
                return RecomendacionModo(
                    modo_recomendado=ModoAnalisis.PRO,
                    mensaje="Modo Pro ejecutado. Aun así se recomienda revisión manual en páginas problemáticas.",
                    razones=razones,
                    requiere_revision_manual=True,
                    motivo_revision_manual="Persisten páginas con baja calidad o bajo score comparativo.",
                )

            return RecomendacionModo(
                modo_recomendado=ModoAnalisis.PRO,
                mensaje="Modo Pro ejecutado correctamente. No se observan alertas fuertes.",
                razones=razones or ["El documento quedó dentro de parámetros aceptables en modo Pro."],
                requiere_revision_manual=False,
                motivo_revision_manual="",
            )

        if resultado.codigo_diagnostico_general in {"mixta", "ocr_recomendado"}:
            return RecomendacionModo(
                modo_recomendado=ModoAnalisis.PRO,
                mensaje="Se recomienda modo Pro por la calidad o estructura del documento.",
                razones=razones,
                requiere_revision_manual=False,
                motivo_revision_manual="",
            )

        if metrica.confianza_ocr_promedio > 0 and metrica.confianza_ocr_promedio < 60:
            razones.append("La confianza OCR promedio es baja.")
            return RecomendacionModo(
                modo_recomendado=ModoAnalisis.PRO,
                mensaje="Se recomienda modo Pro por baja confianza OCR en el análisis base.",
                razones=razones,
                requiere_revision_manual=False,
                motivo_revision_manual="",
            )

        if metrica.ruido_textual_promedio > 0.18:
            razones.append("La proporción de ruido textual es alta.")
            return RecomendacionModo(
                modo_recomendado=ModoAnalisis.PRO,
                mensaje="Se recomienda modo Pro por ruido textual alto en el resultado.",
                razones=razones,
                requiere_revision_manual=False,
                motivo_revision_manual="",
            )

        return RecomendacionModo(
            modo_recomendado=ModoAnalisis.BASICO,
            mensaje="Modo Básico suficiente para este documento, salvo que quieras comparar resultados.",
            razones=razones or ["El documento parece legible y con estructura suficientemente estable."],
            requiere_revision_manual=False,
            motivo_revision_manual="",
        )