from dataclasses import dataclass, field
from typing import List


@dataclass
class ResultadoPagina:
    numero_pagina: int
    tiene_texto: bool
    cantidad_caracteres: int
    texto_extraido: str = ""
    cantidad_imagenes: int = 0
    cobertura_imagen: float = 0.0
    codigo_diagnostico: str = "sin_analisis"
    diagnostico: str = "Sin análisis"
    confianza: int = 0


@dataclass
class ResultadoAnalisisPDF:
    ruta_archivo: str
    nombre_archivo: str
    cantidad_paginas: int
    tiene_texto_digital: bool
    necesita_ocr: bool
    texto_completo: str = ""
    diagnostico_general: str = "Sin análisis"
    codigo_diagnostico_general: str = "sin_analisis"
    detalle_diagnostico: str = ""
    confianza_diagnostico: int = 0
    tipo_ocr_sugerido: str = "-"
    estado_ocr: str = "OCR no ejecutado"
    codigo_estado_ocr: str = "no_ejecutado"
    detalle_ocr: str = ""
    motor_ocr: str = "Pendiente de integrar"
    apto_para_ocr: bool = False
    requiere_preprocesamiento: bool = False
    acciones_preparacion: List[str] = field(default_factory=list)
    resumen_paginas: List[ResultadoPagina] = field(default_factory=list)