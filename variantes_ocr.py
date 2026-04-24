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


def construir_variantes_para_pagina(analisis_pagina: dict) -> list[VarianteOCR]:
    es_problematica = analisis_pagina.get("es_problematica", False)
    es_muy_problematica = analisis_pagina.get("es_muy_problematica", False)
    sospecha_orientacion = analisis_pagina.get("sospecha_orientacion", False)

    variantes = [
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
    ]

    if es_problematica:
        variantes.extend(
            [
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
            ]
        )

    if es_muy_problematica or sospecha_orientacion:
        variantes.append(
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
            )
        )

    # Evita duplicados por clave manteniendo el orden.
    salida = []
    claves = set()
    for variante in variantes:
        if variante.clave not in claves:
            claves.add(variante.clave)
            salida.append(variante)

    return salida