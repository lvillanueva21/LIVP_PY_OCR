from dataclasses import dataclass


ESTADO_PENDIENTE = "pendiente"
ESTADO_EN_CURSO = "en_curso"
ESTADO_COMPLETADA = "completada"
ESTADO_OMITIDA = "omitida"
ESTADO_ADVERTENCIA = "advertencia"
ESTADO_ERROR = "error"

ETAPA_INSPECCION_INICIAL = "inspeccion_inicial"
ETAPA_LECTURA_TEXTO_DIGITAL = "lectura_texto_digital"
ETAPA_EVALUACION_OCR = "evaluacion_ocr"
ETAPA_OCR = "ocr"
ETAPA_CONSOLIDACION_TEXTO = "consolidacion_texto"
ETAPA_EXTRACCION_CAMPOS = "extraccion_campos"
ETAPA_COMPARACION_RESULTADOS = "comparacion_resultados"
ETAPA_FINALIZACION = "finalizacion"


@dataclass(frozen=True)
class DefinicionEtapa:
    id_etapa: str
    etiqueta: str


ETAPAS_LINEA_TIEMPO = [
    DefinicionEtapa(ETAPA_INSPECCION_INICIAL, "Inspección inicial"),
    DefinicionEtapa(ETAPA_LECTURA_TEXTO_DIGITAL, "Lectura de texto digital"),
    DefinicionEtapa(ETAPA_EVALUACION_OCR, "Evaluación OCR"),
    DefinicionEtapa(ETAPA_OCR, "OCR básico o pro"),
    DefinicionEtapa(ETAPA_CONSOLIDACION_TEXTO, "Consolidación de texto"),
    DefinicionEtapa(ETAPA_EXTRACCION_CAMPOS, "Extracción de campos"),
    DefinicionEtapa(ETAPA_COMPARACION_RESULTADOS, "Comparación de resultados"),
    DefinicionEtapa(ETAPA_FINALIZACION, "Finalización"),
]

ETIQUETAS_ESTADO = {
    ESTADO_PENDIENTE: "Pendiente",
    ESTADO_EN_CURSO: "En curso",
    ESTADO_COMPLETADA: "Completada",
    ESTADO_OMITIDA: "Omitida",
    ESTADO_ADVERTENCIA: "Advertencia",
    ESTADO_ERROR: "Error",
}


class ProcesoCanceladoError(Exception):
    pass


def etiqueta_estado(estado: str) -> str:
    return ETIQUETAS_ESTADO.get(estado, estado.replace("_", " ").title())


def etiqueta_etapa(id_etapa: str) -> str:
    for etapa in ETAPAS_LINEA_TIEMPO:
        if etapa.id_etapa == id_etapa:
            return etapa.etiqueta
    return id_etapa.replace("_", " ").title()