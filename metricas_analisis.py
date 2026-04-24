from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class MetricaPaginaModo:
    numero_pagina: int
    fuente_texto: str = "sin_texto"
    caracteres_texto_digital: int = 0
    caracteres_texto_ocr: int = 0
    caracteres_totales: int = 0
    total_caracteres_utiles: int = 0
    cantidad_palabras: int = 0
    palabras_baja_confianza: int = 0
    confianza_ocr_promedio: float = 0.0
    confianza_ocr_mediana: float = 0.0
    tiempo_total_ms: int = 0
    tiempo_ocr_ms: int = 0
    variante_ganadora: str = ""
    numero_intentos: int = 0
    ruido_textual: float = 0.0
    problemas_detectados: int = 0
    dificultad: str = ""
    dificultad_nivel: int = 0
    dificultad_indice: int = 0
    requiere_revision: bool = False
    cantidad_campos_detectados: int = 0
    observaciones: List[str] = field(default_factory=list)

    score_legibilidad: float = 0.0
    score_confianza: float = 0.0
    score_texto_util: float = 0.0
    score_estabilidad: float = 0.0
    score_velocidad: float = 0.0
    score_total: float = 0.0


@dataclass
class MetricaDocumentoModo:
    modo: str
    etiqueta_modo: str
    paginas_totales: int = 0
    paginas_con_texto_digital: int = 0
    paginas_con_ocr: int = 0
    total_caracteres_utiles: int = 0
    total_caracteres: int = 0
    total_palabras: int = 0
    palabras_baja_confianza_totales: int = 0
    confianza_ocr_promedio: float = 0.0
    confianza_ocr_mediana: float = 0.0
    numero_total_intentos: int = 0
    ruido_textual_promedio: float = 0.0
    problemas_detectados: int = 0
    paginas_revision_recomendada: int = 0
    paginas_faciles: int = 0
    paginas_medias: int = 0
    paginas_dificiles: int = 0
    paginas_criticas: int = 0
    cantidad_campos_detectados: int = 0
    tiempo_total_ms: int = 0

    score_campos: float = 0.0
    score_legibilidad: float = 0.0
    score_confianza: float = 0.0
    score_texto_util: float = 0.0
    score_estabilidad: float = 0.0
    score_velocidad: float = 0.0
    score_total: float = 0.0

    observaciones: List[str] = field(default_factory=list)


@dataclass
class ComparacionPaginaAnalisis:
    numero_pagina: int
    score_basico: float = 0.0
    score_pro: float = 0.0
    diferencia_absoluta: float = 0.0
    modo_ganador: str = ""
    etiqueta_ganador: str = ""
    motivo: str = ""
    revision_manual_recomendada: bool = False
    fuente_basico: str = "-"
    fuente_pro: str = "-"
    dificultad_basico: str = "-"
    dificultad_pro: str = "-"
    observaciones: List[str] = field(default_factory=list)


@dataclass
class ResumenComparacionAnalisis:
    modo_ganador: str = ""
    etiqueta_ganador: str = ""
    score_basico: float = 0.0
    score_pro: float = 0.0
    diferencia_absoluta: float = 0.0
    motivo: str = ""
    recomendacion: str = ""
    observaciones: List[str] = field(default_factory=list)
    comparaciones_paginas: List[ComparacionPaginaAnalisis] = field(default_factory=list)
    revision_manual_recomendada: bool = False
    motivo_revision_manual: str = ""