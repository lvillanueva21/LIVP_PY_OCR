from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FuenteBusqueda:
    fuente_id: str
    etiqueta: str
    texto: str
    prioridad: int
    confianza_base: float
    requiere_revision: bool = False
    pagina: int | None = None
    tipo: str = "documento"


class SelectorFuenteExtraccion:
    def construir_fuentes(self, resultado) -> list[FuenteBusqueda]:
        fuentes: list[FuenteBusqueda] = []

        if resultado.texto_final_revisado.strip():
            fuentes.append(
                FuenteBusqueda(
                    fuente_id="texto_revisado",
                    etiqueta="Texto revisado",
                    texto=resultado.texto_final_revisado,
                    prioridad=0,
                    confianza_base=98.0,
                    requiere_revision=False,
                    tipo="documento",
                )
            )

        if resultado.texto_completo.strip():
            fuentes.append(
                FuenteBusqueda(
                    fuente_id="texto_digital",
                    etiqueta="Texto digital",
                    texto=resultado.texto_completo,
                    prioridad=1,
                    confianza_base=92.0,
                    requiere_revision=False,
                    tipo="documento",
                )
            )

        fuentes.extend(self._construir_fuentes_ocr_documento(resultado))
        fuentes.extend(self._construir_fuentes_por_pagina(resultado))

        fuentes = [fuente for fuente in fuentes if (fuente.texto or "").strip()]
        fuentes.sort(
            key=lambda fuente: (
                fuente.prioridad,
                -fuente.confianza_base,
                fuente.pagina if fuente.pagina is not None else 0,
            )
        )
        return fuentes

    def fuente_principal(self, resultado) -> str:
        fuentes = self.construir_fuentes(resultado)
        if not fuentes:
            return "sin_texto"
        return fuentes[0].fuente_id

    def _construir_fuentes_ocr_documento(self, resultado) -> list[FuenteBusqueda]:
        fuentes: list[FuenteBusqueda] = []

        paginas_pro = []
        paginas_basico = []

        for pagina in resultado.resumen_paginas:
            texto_ocr = (pagina.texto_ocr or "").strip()
            if not texto_ocr:
                continue

            tipo_ocr = self._tipo_ocr_pagina(pagina)
            if tipo_ocr == "ocr_pro":
                paginas_pro.append(pagina)
            else:
                paginas_basico.append(pagina)

        if paginas_pro:
            texto = "\n\n".join(
                f"===== PÁGINA {pagina.numero_pagina} =====\n{pagina.texto_ocr.strip()}"
                for pagina in paginas_pro
                if pagina.texto_ocr.strip()
            ).strip()

            confianza = self._promedio_confianza_paginas(paginas_pro, default=74.0)
            requiere_revision = any(pagina.ocr_requiere_revision for pagina in paginas_pro)

            fuentes.append(
                FuenteBusqueda(
                    fuente_id="texto_ocr_pro",
                    etiqueta="Texto OCR Pro",
                    texto=texto,
                    prioridad=2,
                    confianza_base=confianza,
                    requiere_revision=requiere_revision,
                    tipo="documento",
                )
            )

        if paginas_basico:
            texto = "\n\n".join(
                f"===== PÁGINA {pagina.numero_pagina} =====\n{pagina.texto_ocr.strip()}"
                for pagina in paginas_basico
                if pagina.texto_ocr.strip()
            ).strip()

            confianza = self._promedio_confianza_paginas(paginas_basico, default=64.0)
            requiere_revision = any(pagina.ocr_requiere_revision for pagina in paginas_basico)

            fuentes.append(
                FuenteBusqueda(
                    fuente_id="texto_ocr_basico",
                    etiqueta="Texto OCR básico",
                    texto=texto,
                    prioridad=3,
                    confianza_base=confianza,
                    requiere_revision=requiere_revision,
                    tipo="documento",
                )
            )

        return fuentes

    def _construir_fuentes_por_pagina(self, resultado) -> list[FuenteBusqueda]:
        fuentes: list[FuenteBusqueda] = []

        for pagina in resultado.resumen_paginas:
            texto_digital = (pagina.texto_extraido or "").strip()
            if texto_digital:
                fuentes.append(
                    FuenteBusqueda(
                        fuente_id=f"pagina_{pagina.numero_pagina}_texto_digital",
                        etiqueta=f"Página {pagina.numero_pagina} texto digital",
                        texto=texto_digital,
                        prioridad=4,
                        confianza_base=90.0,
                        requiere_revision=False,
                        pagina=pagina.numero_pagina,
                        tipo="pagina",
                    )
                )

            texto_ocr = (pagina.texto_ocr or "").strip()
            if texto_ocr:
                tipo_ocr = self._tipo_ocr_pagina(pagina)
                confianza = max(38.0, min(95.0, pagina.ocr_confianza_promedio or 60.0))
                if pagina.ocr_requiere_revision:
                    confianza -= 8.0

                fuentes.append(
                    FuenteBusqueda(
                        fuente_id=f"pagina_{pagina.numero_pagina}_{tipo_ocr}",
                        etiqueta=f"Página {pagina.numero_pagina} {'OCR Pro' if tipo_ocr == 'ocr_pro' else 'OCR básico'}",
                        texto=texto_ocr,
                        prioridad=5 if tipo_ocr == "ocr_pro" else 6,
                        confianza_base=confianza,
                        requiere_revision=pagina.ocr_requiere_revision,
                        pagina=pagina.numero_pagina,
                        tipo="pagina",
                    )
                )

        return fuentes

    def _tipo_ocr_pagina(self, pagina) -> str:
        clave = (pagina.ocr_variante_clave or "").strip().lower()
        if clave and clave != "basico_estandar":
            return "ocr_pro"
        return "ocr_basico"

    def _promedio_confianza_paginas(self, paginas: list, default: float) -> float:
        valores = [pagina.ocr_confianza_promedio for pagina in paginas if pagina.ocr_confianza_promedio > 0]
        if not valores:
            return default
        return round(sum(valores) / len(valores), 2)