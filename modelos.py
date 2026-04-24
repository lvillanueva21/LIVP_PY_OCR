from dataclasses import dataclass, field
from typing import Any, List


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

    ocr_confianza_promedio: float = 0.0
    ocr_confianza_mediana: float = 0.0
    ocr_cantidad_palabras: int = 0
    ocr_palabras_baja_confianza: int = 0
    ocr_caracteres_totales: int = 0
    ocr_ruido_textual: float = 0.0
    ocr_tiempo_total_ms: int = 0
    ocr_tiempo_ocr_ms: int = 0
    ocr_variante_ganadora: str = ""
    ocr_variante_clave: str = ""
    ocr_numero_intentos: int = 0
    ocr_score_estimado: float = 0.0
    ocr_dificultad: str = ""
    ocr_dificultad_nivel: int = 0
    ocr_dificultad_indice: int = 0
    ocr_requiere_revision: bool = False
    ocr_observaciones: List[str] = field(default_factory=list)


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
    paginas_ocr_forzadas: List[int] = field(default_factory=list)
    acciones_preparacion: List[str] = field(default_factory=list)
    errores_ocr: List[str] = field(default_factory=list)
    alertas_operativas: List[str] = field(default_factory=list)
    resumen_paginas: List[ResultadoPagina] = field(default_factory=list)
    campos_extraidos: List[CampoExtraido] = field(default_factory=list)

    modo_analisis: str = "basico"
    etiqueta_modo: str = "Básico"
    recomendacion_modo: str = ""
    observaciones_modo: List[str] = field(default_factory=list)
    es_provisional: bool = False
    analisis_parcial: bool = False
    motivo_detencion_seguridad: str = ""
    tiempo_total_ms: int = 0

    metricas_documento_modo: Any = None
    metricas_paginas_modo: List[Any] = field(default_factory=list)
    comparacion_modos: Any = None