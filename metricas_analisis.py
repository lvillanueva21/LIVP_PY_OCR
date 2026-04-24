from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class MetricaPaginaModo:
    numero_pagina: int
    fuente_texto: str = "sin_texto"
    caracteres_texto_digital: int = 0
    caracteres_texto_ocr: int = 0
    total_caracteres_utiles: int = 0
    cantidad_campos_detectados: int = 0
    tiempo_estimado_ms: int = 0
    observaciones: List[str] = field(default_factory=list)


@dataclass
class MetricaDocumentoModo:
    modo: str
    etiqueta_modo: str
    paginas_totales: int = 0
    paginas_con_texto_digital: int = 0
    paginas_con_ocr: int = 0
    total_caracteres_utiles: int = 0
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
class ResumenComparacionAnalisis:
    modo_ganador: str = ""
    etiqueta_ganador: str = ""
    score_basico: float = 0.0
    score_pro: float = 0.0
    diferencia_absoluta: float = 0.0
    motivo: str = ""
    recomendacion: str = ""
    observaciones: List[str] = field(default_factory=list)