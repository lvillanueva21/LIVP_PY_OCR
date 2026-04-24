from dataclasses import dataclass


@dataclass(frozen=True)
class VarianteOCR:
    clave: str
    nombre: str
    psm: int = 6
    escala: float = 1.0
    usar_autocontraste: bool = True
    usar_binarizacion_simple: bool = False
    usar_binarizacion_adaptativa: bool = False
    usar_denoise: bool = False
    usar_deskew: bool = False
    usar_orientacion_osd: bool = False
    usar_sharpen: bool = False


VARIANTES_REGISTRADAS = [
    VarianteOCR(
        clave="gris_autocontraste",
        nombre="Gris + autocontraste",
        psm=6,
        escala=1.4,
        usar_autocontraste=True,
    ),
    VarianteOCR(
        clave="gris_autocontraste_sharpen",
        nombre="Gris + autocontraste + sharpen",
        psm=6,
        escala=1.6,
        usar_autocontraste=True,
        usar_sharpen=True,
    ),
    VarianteOCR(
        clave="adaptativa_denoise",
        nombre="Binarización adaptativa + denoise",
        psm=6,
        escala=1.8,
        usar_autocontraste=True,
        usar_binarizacion_adaptativa=True,
        usar_denoise=True,
    ),
    VarianteOCR(
        clave="simple_deskew",
        nombre="Binarización simple + deskew",
        psm=6,
        escala=1.8,
        usar_autocontraste=True,
        usar_binarizacion_simple=True,
        usar_deskew=True,
    ),
    VarianteOCR(
        clave="orientacion_adaptativa",
        nombre="Corrección orientación + adaptativa",
        psm=11,
        escala=2.0,
        usar_autocontraste=True,
        usar_binarizacion_adaptativa=True,
        usar_denoise=True,
        usar_deskew=True,
        usar_orientacion_osd=True,
        usar_sharpen=True,
    ),
]

MAPA_VARIANTES = {variante.clave: variante for variante in VARIANTES_REGISTRADAS}


def obtener_variante_por_clave(clave: str) -> VarianteOCR | None:
    return MAPA_VARIANTES.get((clave or "").strip())


def construir_variantes_para_pagina(analisis_pagina: dict) -> list[VarianteOCR]:
    es_problematica = analisis_pagina.get("es_problematica", False)
    es_muy_problematica = analisis_pagina.get("es_muy_problematica", False)
    sospecha_orientacion = analisis_pagina.get("sospecha_orientacion", False)

    variantes = [
        MAPA_VARIANTES["gris_autocontraste"],
        MAPA_VARIANTES["gris_autocontraste_sharpen"],
    ]

    if es_problematica:
        variantes.extend(
            [
                MAPA_VARIANTES["adaptativa_denoise"],
                MAPA_VARIANTES["simple_deskew"],
            ]
        )

    if es_muy_problematica or sospecha_orientacion:
        variantes.append(MAPA_VARIANTES["orientacion_adaptativa"])

    salida = []
    claves = set()
    for variante in variantes:
        if variante.clave not in claves:
            claves.add(variante.clave)
            salida.append(variante)

    return salida