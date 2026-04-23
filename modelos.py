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
    texto_ocr: str = ""
    ocr_ejecutado: bool = False
    ocr_error: str = ""


@dataclass
class CampoExtraido:
    nombre_campo: str
    etiqueta: str
    valor: str = ""
    detectado: bool = False
    estrategia: str = "no_detectado"


@dataclass
class ResultadoAnalisisPDF:
    ruta_archivo: str
    nombre_archivo: str
    cantidad_paginas: int
    tiene_texto_digital: bool
    necesita_ocr: bool
    texto_completo: str = ""
    texto_ocr_completo: str = ""
    texto_final_revisado: str = ""
    texto_fuente_extraccion: str = ""
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
    ocr_disponible: bool = False
    requiere_preprocesamiento: bool = False
    paginas_ocr_objetivo: int = 0
    paginas_ocr_procesadas: int = 0
    acciones_preparacion: List[str] = field(default_factory=list)
    errores_ocr: List[str] = field(default_factory=list)
    resumen_paginas: List[ResultadoPagina] = field(default_factory=list)
    campos_extraidos: List[CampoExtraido] = field(default_factory=list)