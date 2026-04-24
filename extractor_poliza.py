from __future__ import annotations

import re
from dataclasses import dataclass

from modelos import CampoExtraido, ResultadoAnalisisPDF
from selector_fuente_extraccion import FuenteBusqueda, SelectorFuenteExtraccion


@dataclass
class CandidatoCampo:
    valor: str
    estrategia: str
    fuente_exacta: str
    confianza_estimada: float
    requiere_revision_manual: bool
    observacion: str
    prioridad_fuente: int

    @property
    def score(self) -> tuple[float, int]:
        return (self.confianza_estimada, -self.prioridad_fuente)


class ExtractorPoliza:
    ENCABEZADOS_CORTE = (
        "DATOS DEL ASEGURADO",
        "DATOS DEL VEHICULO",
        "DATOS DEL VEHÍCULO",
        "DATOS DEL CORREDOR",
        "DATOS DEL RIESGO",
        "DATOS DEL BENEFICIARIO",
        "COBERTURAS",
        "PRIMAS",
        "CONDICIONES",
        "SERVICIOS",
        "RESUMEN",
        "CLAUSULAS",
        "CLÁUSULAS",
        "OBSERVACIONES",
    )

    def __init__(self, selector_fuentes: SelectorFuenteExtraccion | None = None) -> None:
        self.selector_fuentes = selector_fuentes or SelectorFuenteExtraccion()

    def extraer(self, resultado: ResultadoAnalisisPDF) -> ResultadoAnalisisPDF:
        fuentes = self.selector_fuentes.construir_fuentes(resultado)

        campos = [
            self._resolver_campo("numero_poliza", "Número de póliza", fuentes, self._extraer_numero_poliza),
            self._resolver_campo("fecha_emision", "Fecha de emisión", fuentes, self._extraer_fecha_emision),
            self._resolver_campo("vigencia_desde", "Vigencia desde", fuentes, self._extraer_vigencia_desde),
            self._resolver_campo("vigencia_hasta", "Vigencia hasta", fuentes, self._extraer_vigencia_hasta),
            self._resolver_campo("aseguradora", "Aseguradora", fuentes, self._extraer_aseguradora),
            self._resolver_campo("contratante", "Contratante", fuentes, self._extraer_contratante),
            self._resolver_campo("ruc", "RUC", fuentes, self._extraer_ruc),
            self._resolver_campo("moneda", "Moneda", fuentes, self._extraer_moneda),
        ]

        resultado.campos_extraidos = campos
        resultado.texto_fuente_extraccion = self._resumir_fuentes_campos(campos, resultado)
        return resultado

    def _resolver_campo(
        self,
        nombre_campo: str,
        etiqueta: str,
        fuentes: list[FuenteBusqueda],
        extractor,
    ) -> CampoExtraido:
        mejor: CandidatoCampo | None = None

        for fuente in fuentes:
            candidato = extractor(fuente)
            if candidato is None or not candidato.valor:
                continue

            if mejor is None or candidato.score > mejor.score:
                mejor = candidato

        if mejor is None:
            return CampoExtraido(
                nombre_campo=nombre_campo,
                etiqueta=etiqueta,
                valor="",
                detectado=False,
                estrategia="no_detectado",
                fuente_exacta="",
                confianza_estimada=0.0,
                requiere_revision_manual=False,
                observacion="No detectado.",
            )

        return CampoExtraido(
            nombre_campo=nombre_campo,
            etiqueta=etiqueta,
            valor=self._limpiar_valor(mejor.valor),
            detectado=bool(self._limpiar_valor(mejor.valor)),
            estrategia=mejor.estrategia,
            fuente_exacta=mejor.fuente_exacta,
            confianza_estimada=round(mejor.confianza_estimada, 2),
            requiere_revision_manual=mejor.requiere_revision_manual,
            observacion=mejor.observacion,
        )

    def _extraer_numero_poliza(self, fuente: FuenteBusqueda) -> CandidatoCampo | None:
        patrones = [
            (
                r"(?:N[ÚU]MERO\s+DE\s+P[ÓO]LIZA|P[ÓO]LIZA\s*(?:N[°ºO]|NRO|NÚMERO)?)\s*[:#]?\s*(?P<valor>[A-Z0-9][A-Z0-9\-/\.]{3,40})",
                "regex_etiqueta_precisa",
                18,
            ),
            (
                r"(?:P[ÓO]LIZA|CERTIFICADO)\s*[:#]?\s*(?P<valor>[A-Z0-9][A-Z0-9\-/\.]{4,40})",
                "regex_etiqueta",
                12,
            ),
        ]

        candidato = self._buscar_por_patrones(
            fuente,
            patrones,
            normalizador=self._normalizar_numero_poliza,
        )
        if candidato:
            return candidato

        return self._buscar_por_proximidad(
            fuente,
            aliases=[
                "NÚMERO DE PÓLIZA",
                "NUMERO DE POLIZA",
                "PÓLIZA",
                "POLIZA",
                "NRO. PÓLIZA",
                "NRO. POLIZA",
            ],
            extractor=self._normalizar_numero_poliza,
            estrategia="proximidad_textual",
            bonus=8,
        )

    def _extraer_fecha_emision(self, fuente: FuenteBusqueda) -> CandidatoCampo | None:
        patrones = [
            (
                r"(?:FECHA\s+DE\s+EMISI[ÓO]N|FEC\.\s*EMISI[ÓO]N|EMISI[ÓO]N)\s*[:#]?\s*(?P<valor>\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})",
                "regex_etiqueta_precisa",
                18,
            ),
            (
                r"(?:EMITIDO\s+EL|FECHA\s+EMITIDA)\s*[:#]?\s*(?P<valor>\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})",
                "regex_etiqueta",
                12,
            ),
        ]

        candidato = self._buscar_por_patrones(
            fuente,
            patrones,
            normalizador=self._normalizar_fecha,
        )
        if candidato:
            return candidato

        lineas = self._lineas_limpias(fuente.texto)
        for linea in lineas[:25]:
            linea_mayus = linea.upper()
            if "VIGENCIA" in linea_mayus:
                continue
            if "EMISI" in linea_mayus or "FECHA" in linea_mayus:
                fecha = self._primer_fecha(linea)
                if fecha:
                    return self._crear_candidato(
                        valor=fecha,
                        estrategia="heuristica_linea_emision",
                        fuente=fuente,
                        bonus=7,
                        requiere_revision=fuente.requiere_revision,
                        observacion=self._observacion_base(fuente, False),
                    )
        return None

    def _extraer_vigencia_desde(self, fuente: FuenteBusqueda) -> CandidatoCampo | None:
        patrones = [
            (
                r"(?:VIGENCIA\s+DESDE|INICIO\s+DE\s+VIGENCIA|DESDE)\s*[:#]?\s*(?P<valor>\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}(?:\s+\d{1,2}:\d{2})?)",
                "regex_etiqueta_precisa",
                18,
            ),
            (
                r"VIGENCIA[^\n\r]{0,50}DEL\s*(?P<valor>\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}(?:\s+\d{1,2}:\d{2})?)\s+AL\s+\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}",
                "regex_rango_vigencia",
                14,
            ),
        ]

        candidato = self._buscar_por_patrones(
            fuente,
            patrones,
            normalizador=self._normalizar_fecha_hora,
        )
        if candidato:
            return candidato

        rango = self._extraer_rango_vigencia(fuente.texto)
        if rango and rango[0]:
            return self._crear_candidato(
                valor=rango[0],
                estrategia="bloque_contextual_vigencia",
                fuente=fuente,
                bonus=10,
                requiere_revision=fuente.requiere_revision,
                observacion=self._observacion_base(fuente, False),
            )
        return None

    def _extraer_vigencia_hasta(self, fuente: FuenteBusqueda) -> CandidatoCampo | None:
        patrones = [
            (
                r"(?:VIGENCIA\s+HASTA|FIN\s+DE\s+VIGENCIA|HASTA)\s*[:#]?\s*(?P<valor>\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}(?:\s+\d{1,2}:\d{2})?)",
                "regex_etiqueta_precisa",
                18,
            ),
            (
                r"VIGENCIA[^\n\r]{0,50}DEL\s*\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}(?:\s+\d{1,2}:\d{2})?\s+AL\s+(?P<valor>\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}(?:\s+\d{1,2}:\d{2})?)",
                "regex_rango_vigencia",
                14,
            ),
        ]

        candidato = self._buscar_por_patrones(
            fuente,
            patrones,
            normalizador=self._normalizar_fecha_hora,
        )
        if candidato:
            return candidato

        rango = self._extraer_rango_vigencia(fuente.texto)
        if rango and rango[1]:
            return self._crear_candidato(
                valor=rango[1],
                estrategia="bloque_contextual_vigencia",
                fuente=fuente,
                bonus=10,
                requiere_revision=fuente.requiere_revision,
                observacion=self._observacion_base(fuente, False),
            )
        return None

    def _extraer_aseguradora(self, fuente: FuenteBusqueda) -> CandidatoCampo | None:
        patrones = [
            (
                r"(?:ASEGURADORA|COMPAÑ[IÍ]A\s+DE\s+SEGUROS|COMPAÑIA\s+DE\s+SEGUROS|CIA\.\s*DE\s+SEGUROS)\s*[:#]?\s*(?P<valor>[^\n\r]{4,120})",
                "regex_etiqueta_precisa",
                18,
            ),
        ]

        candidato = self._buscar_por_patrones(
            fuente,
            patrones,
            normalizador=self._normalizar_nombre_entidad,
        )
        if candidato:
            return candidato

        palabras_clave = (
            "SEGUROS",
            "ASEGURADORA",
            "SEGUROS Y REASEGUROS",
            "CIA DE SEG",
            "COMPAÑIA DE SEGUROS",
            "COMPANIA DE SEGUROS",
        )

        for linea in self._lineas_limpias(fuente.texto)[:35]:
            linea_mayus = linea.upper()
            if any(clave in linea_mayus for clave in palabras_clave):
                if any(bloque in linea_mayus for bloque in ("CONTRATANTE", "PROVEEDOR", "CORREDOR", "DATOS DEL")):
                    continue
                valor = self._normalizar_nombre_entidad(linea)
                if valor:
                    return self._crear_candidato(
                        valor=valor,
                        estrategia="heuristica_encabezado_aseguradora",
                        fuente=fuente,
                        bonus=8,
                        requiere_revision=fuente.requiere_revision,
                        observacion=self._observacion_base(fuente, False),
                    )
        return None

    def _extraer_contratante(self, fuente: FuenteBusqueda) -> CandidatoCampo | None:
        bloque = self._extraer_bloque_contextual(
            fuente.texto,
            encabezados_inicio=(
                "DATOS DEL CONTRATANTE",
                "DATOS DEL TOMADOR",
                "DATOS DEL ASEGURADO",
                "DATOS DEL PROVEEDOR",
                "1. DATOS DEL PROVEEDOR",
            ),
        )

        if bloque:
            for patron, estrategia, bonus in [
                (
                    r"(?:RAZ[ÓO]N\s+SOCIAL|RAZON\s+SOCIAL)\s*[:#]?\s*(?P<valor>[^\n\r]{4,120})",
                    "bloque_contextual_razon_social",
                    18,
                ),
                (
                    r"(?:CONTRATANTE|TOMADOR|ASEGURADO|SEÑOR\(ES\)|SEÑOR\(ES\)\s*:?|NOMBRE)\s*[:#]?\s*(?P<valor>[^\n\r]{4,120})",
                    "bloque_contextual_nombre",
                    12,
                ),
            ]:
                coincidencia = re.search(patron, bloque, re.IGNORECASE)
                if coincidencia:
                    valor = self._normalizar_nombre_persona_o_empresa(coincidencia.group("valor"))
                    if valor:
                        return self._crear_candidato(
                            valor=valor,
                            estrategia=estrategia,
                            fuente=fuente,
                            bonus=bonus,
                            requiere_revision=fuente.requiere_revision,
                            observacion=self._observacion_base(fuente, False),
                        )

        patrones = [
            (
                r"(?:CONTRATANTE|TOMADOR|ASEGURADO|SEÑOR\(ES\)|SEÑOR\(ES\)|NOMBRE)\s*[:#]?\s*(?P<valor>[^\n\r]{4,120})",
                "regex_etiqueta",
                12,
            ),
        ]
        return self._buscar_por_patrones(
            fuente,
            patrones,
            normalizador=self._normalizar_nombre_persona_o_empresa,
        )

    def _extraer_ruc(self, fuente: FuenteBusqueda) -> CandidatoCampo | None:
        bloque = self._extraer_bloque_contextual(
            fuente.texto,
            encabezados_inicio=(
                "DATOS DEL CONTRATANTE",
                "DATOS DEL TOMADOR",
                "DATOS DEL ASEGURADO",
                "DATOS DEL PROVEEDOR",
                "1. DATOS DEL PROVEEDOR",
            ),
        )

        if bloque:
            coincidencia = re.search(r"\bRUC\s*[:#]?\s*(?P<valor>\d{11})\b", bloque, re.IGNORECASE)
            if coincidencia:
                return self._crear_candidato(
                    valor=coincidencia.group("valor"),
                    estrategia="bloque_contextual_ruc",
                    fuente=fuente,
                    bonus=18,
                    requiere_revision=fuente.requiere_revision,
                    observacion=self._observacion_base(fuente, False),
                )

        coincidencia = re.search(r"\bRUC\s*[:#]?\s*(?P<valor>\d{11})\b", fuente.texto, re.IGNORECASE)
        if coincidencia:
            return self._crear_candidato(
                valor=coincidencia.group("valor"),
                estrategia="regex_etiqueta_precisa",
                fuente=fuente,
                bonus=14,
                requiere_revision=fuente.requiere_revision,
                observacion=self._observacion_base(fuente, False),
            )

        lineas = self._lineas_limpias(fuente.texto)
        for linea in lineas[:60]:
            if any(alias in linea.upper() for alias in ("CONTRATANTE", "TOMADOR", "PROVEEDOR", "ASEGURADO")):
                coincidencia = re.search(r"\b(\d{11})\b", linea)
                if coincidencia:
                    return self._crear_candidato(
                        valor=coincidencia.group(1),
                        estrategia="proximidad_textual_ruc",
                        fuente=fuente,
                        bonus=9,
                        requiere_revision=fuente.requiere_revision,
                        observacion=self._observacion_base(fuente, True),
                    )
        return None

    def _extraer_moneda(self, fuente: FuenteBusqueda) -> CandidatoCampo | None:
        patrones = [
            (
                r"\bMONEDA\b\s*[:#]?\s*(?P<valor>US\$|USD|DOLARES|DÓLARES|SOLES|S\/|PEN)",
                "regex_etiqueta_precisa",
                18,
            ),
            (
                r"\b(?:PRIMA|TOTAL|IMPORTE|MONTO)[^\n\r]{0,60}(?P<valor>US\$|USD|DOLARES|DÓLARES|SOLES|S\/|PEN)\b",
                "regex_contexto",
                10,
            ),
        ]

        candidato = self._buscar_por_patrones(
            fuente,
            patrones,
            normalizador=self._normalizar_moneda,
        )
        if candidato:
            return candidato

        return self._buscar_por_proximidad(
            fuente,
            aliases=["MONEDA", "T/C", "TIPO DE MONEDA"],
            extractor=self._normalizar_moneda,
            estrategia="proximidad_textual",
            bonus=8,
        )

    def _buscar_por_patrones(
        self,
        fuente: FuenteBusqueda,
        patrones: list[tuple[str, str, int]],
        *,
        normalizador=None,
    ) -> CandidatoCampo | None:
        for patron, estrategia, bonus in patrones:
            coincidencia = re.search(patron, fuente.texto, re.IGNORECASE)
            if not coincidencia:
                continue

            valor = coincidencia.group("valor") if "valor" in coincidencia.groupdict() else coincidencia.group(1)
            if normalizador is not None:
                valor = normalizador(valor)
            valor = self._limpiar_valor(valor)

            if not valor:
                continue

            requiere_revision = fuente.requiere_revision
            observacion = self._observacion_base(fuente, requiere_revision)

            return self._crear_candidato(
                valor=valor,
                estrategia=estrategia,
                fuente=fuente,
                bonus=bonus,
                requiere_revision=requiere_revision,
                observacion=observacion,
            )
        return None

    def _buscar_por_proximidad(
        self,
        fuente: FuenteBusqueda,
        *,
        aliases: list[str],
        extractor=None,
        estrategia: str,
        bonus: int,
    ) -> CandidatoCampo | None:
        lineas = self._lineas_limpias(fuente.texto)

        for indice, linea in enumerate(lineas):
            linea_mayus = linea.upper()
            if not any(alias in linea_mayus for alias in aliases):
                continue

            candidatos = [linea]
            if indice + 1 < len(lineas):
                candidatos.append(lineas[indice + 1])
            if indice + 2 < len(lineas):
                candidatos.append(lineas[indice + 2])

            for linea_candidata in candidatos:
                valor = linea_candidata
                valor = re.sub(r"^[A-ZÁÉÍÓÚÑ0-9\s\.\-\/()]+[:#]?\s*", "", valor).strip()

                if extractor is not None:
                    valor = extractor(valor)

                valor = self._limpiar_valor(valor)
                if not valor:
                    continue

                return self._crear_candidato(
                    valor=valor,
                    estrategia=estrategia,
                    fuente=fuente,
                    bonus=bonus,
                    requiere_revision=True if fuente.requiere_revision else False,
                    observacion=self._observacion_base(fuente, True),
                )
        return None

    def _crear_candidato(
        self,
        *,
        valor: str,
        estrategia: str,
        fuente: FuenteBusqueda,
        bonus: int,
        requiere_revision: bool,
        observacion: str,
    ) -> CandidatoCampo:
        confianza = fuente.confianza_base + bonus

        if requiere_revision:
            confianza -= 10

        if len(valor) > 80:
            confianza -= 8
        elif len(valor) > 50:
            confianza -= 4

        if self._proporcion_simbolos_raros(valor) > 0.18:
            confianza -= 10
            requiere_revision = True
            observacion = self._combinar_observaciones(
                observacion,
                "Valor con ruido textual alto.",
            )

        confianza = max(5.0, min(99.0, confianza))

        return CandidatoCampo(
            valor=valor,
            estrategia=estrategia,
            fuente_exacta=fuente.fuente_id,
            confianza_estimada=confianza,
            requiere_revision_manual=requiere_revision,
            observacion=observacion,
            prioridad_fuente=fuente.prioridad,
        )

    def _extraer_bloque_contextual(
        self,
        texto: str,
        *,
        encabezados_inicio: tuple[str, ...],
        max_lineas: int = 14,
    ) -> str:
        lineas = self._lineas_limpias(texto)
        inicio = -1

        for indice, linea in enumerate(lineas):
            linea_mayus = linea.upper()
            if any(encabezado in linea_mayus for encabezado in encabezados_inicio):
                inicio = indice + 1
                break

        if inicio == -1:
            return ""

        lineas_bloque = []
        for linea in lineas[inicio:]:
            linea_mayus = linea.upper()
            if any(linea_mayus.startswith(encabezado) for encabezado in self.ENCABEZADOS_CORTE):
                break
            lineas_bloque.append(linea)
            if len(lineas_bloque) >= max_lineas:
                break

        return "\n".join(lineas_bloque)

    def _extraer_rango_vigencia(self, texto: str) -> tuple[str, str] | None:
        patrones = [
            r"VIGENCIA[^\n\r]{0,50}DEL\s*(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}(?:\s+\d{1,2}:\d{2})?)\s+AL\s+(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}(?:\s+\d{1,2}:\d{2})?)",
            r"DESDE\s*(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}(?:\s+\d{1,2}:\d{2})?)\s+HASTA\s+(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}(?:\s+\d{1,2}:\d{2})?)",
        ]

        for patron in patrones:
            coincidencia = re.search(patron, texto, re.IGNORECASE)
            if coincidencia:
                return (
                    self._normalizar_fecha_hora(coincidencia.group(1)),
                    self._normalizar_fecha_hora(coincidencia.group(2)),
                )
        return None

    def _resumir_fuentes_campos(self, campos: list[CampoExtraido], resultado: ResultadoAnalisisPDF) -> str:
        fuentes = [campo.fuente_exacta for campo in campos if campo.detectado and campo.fuente_exacta]
        fuentes_unicas = []
        for fuente in fuentes:
            if fuente not in fuentes_unicas:
                fuentes_unicas.append(fuente)

        if not fuentes_unicas:
            return self.selector_fuentes.fuente_principal(resultado)

        if len(fuentes_unicas) == 1:
            return fuentes_unicas[0]

        return "mixto_por_campo: " + " | ".join(fuentes_unicas)

    def _observacion_base(self, fuente: FuenteBusqueda, requiere_revision: bool) -> str:
        observaciones = []
        if fuente.requiere_revision:
            observaciones.append("Fuente marcada con revisión manual recomendada.")
        if fuente.tipo == "pagina" and fuente.pagina is not None:
            observaciones.append(f"Origen localizado en página {fuente.pagina}.")
        if requiere_revision:
            observaciones.append("Conviene validar el campo manualmente.")

        return self._combinar_observaciones(*observaciones)

    def _combinar_observaciones(self, *observaciones: str) -> str:
        salida = []
        for observacion in observaciones:
            observacion = (observacion or "").strip()
            if observacion and observacion not in salida:
                salida.append(observacion)
        return " ".join(salida)

    def _lineas_limpias(self, texto: str) -> list[str]:
        return [linea.strip() for linea in texto.splitlines() if linea.strip()]

    def _primer_fecha(self, texto: str) -> str:
        coincidencia = re.search(r"\b(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})\b", texto)
        if not coincidencia:
            return ""
        return self._normalizar_fecha(coincidencia.group(1))

    def _normalizar_numero_poliza(self, valor: str) -> str:
        valor = (valor or "").strip().upper()
        valor = re.sub(r"[^A-Z0-9\-/\.]", "", valor)
        if len(valor) < 4:
            return ""
        if re.fullmatch(r"\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}", valor):
            return ""
        return valor

    def _normalizar_fecha(self, valor: str) -> str:
        valor = (valor or "").strip()
        coincidencia = re.search(r"(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4})", valor)
        if not coincidencia:
            return ""
        fecha = coincidencia.group(1)
        return fecha.replace("-", "/").replace(".", "/")

    def _normalizar_fecha_hora(self, valor: str) -> str:
        valor = (valor or "").strip()
        coincidencia = re.search(
            r"(\d{1,2}[\/\-.]\d{1,2}[\/\-.]\d{2,4}(?:\s+\d{1,2}:\d{2})?)",
            valor,
        )
        if not coincidencia:
            return ""
        dato = coincidencia.group(1)
        return dato.replace("-", "/").replace(".", "/")

    def _normalizar_nombre_entidad(self, valor: str) -> str:
        valor = self._limpiar_valor(valor)
        valor = re.sub(r"\s+RUC\b.*$", "", valor, flags=re.IGNORECASE)
        valor = re.sub(r"\s+MONEDA\b.*$", "", valor, flags=re.IGNORECASE)
        valor = re.sub(r"\s{2,}", " ", valor).strip(" :-")
        if len(valor) < 4:
            return ""
        return valor

    def _normalizar_nombre_persona_o_empresa(self, valor: str) -> str:
        valor = self._limpiar_valor(valor)
        valor = re.sub(r"\bRUC\b.*$", "", valor, flags=re.IGNORECASE)
        valor = re.sub(r"\bDNI\b.*$", "", valor, flags=re.IGNORECASE)
        valor = re.sub(r"\bTEL[ÉE]FONO\b.*$", "", valor, flags=re.IGNORECASE)
        valor = re.sub(r"\bCCI\b.*$", "", valor, flags=re.IGNORECASE)
        valor = valor.strip(" :-")
        if len(valor) < 4:
            return ""
        return valor

    def _normalizar_moneda(self, valor: str) -> str:
        valor_mayus = (valor or "").strip().upper()
        if valor_mayus in {"US$", "USD", "DOLARES", "DÓLARES"}:
            return "USD"
        if valor_mayus in {"SOLES", "S/", "PEN"}:
            return "PEN"
        return ""

    def _limpiar_valor(self, valor: str) -> str:
        valor = (valor or "").strip()
        valor = re.sub(r"\s+", " ", valor)
        return valor.strip(" :-")

    def _proporcion_simbolos_raros(self, valor: str) -> float:
        valor = valor or ""
        if not valor:
            return 1.0
        raros = sum(
            1
            for caracter in valor
            if not (caracter.isalnum() or caracter.isspace() or caracter in ".,:;/()-_%$#°")
        )
        return raros / max(1, len(valor))