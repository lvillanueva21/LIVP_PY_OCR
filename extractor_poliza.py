import re

from modelos import CampoExtraido, ResultadoAnalisisPDF


class ExtractorPoliza:
    def extraer(self, resultado: ResultadoAnalisisPDF) -> ResultadoAnalisisPDF:
        texto_fuente, nombre_fuente = self._obtener_texto_fuente(resultado)
        resultado.texto_fuente_extraccion = nombre_fuente

        campos = [
            self._crear_campo(
                "numero_poliza",
                "Número de póliza",
                *self._extraer_numero_poliza(texto_fuente),
            ),
            self._crear_campo(
                "fecha_emision",
                "Fecha de emisión",
                *self._extraer_fecha_emision(texto_fuente),
            ),
            self._crear_campo(
                "vigencia_desde",
                "Vigencia desde",
                *self._extraer_vigencia_desde(texto_fuente),
            ),
            self._crear_campo(
                "vigencia_hasta",
                "Vigencia hasta",
                *self._extraer_vigencia_hasta(texto_fuente),
            ),
            self._crear_campo(
                "aseguradora",
                "Aseguradora",
                *self._extraer_aseguradora(texto_fuente),
            ),
            self._crear_campo(
                "contratante",
                "Contratante",
                *self._extraer_contratante(texto_fuente),
            ),
            self._crear_campo(
                "ruc",
                "RUC",
                *self._extraer_ruc(texto_fuente),
            ),
            self._crear_campo(
                "moneda",
                "Moneda",
                *self._extraer_moneda(texto_fuente),
            ),
        ]

        resultado.campos_extraidos = campos
        return resultado

    def _crear_campo(
        self,
        nombre_campo: str,
        etiqueta: str,
        valor: str,
        estrategia: str,
    ) -> CampoExtraido:
        valor_limpio = self._limpiar_valor(valor)
        return CampoExtraido(
            nombre_campo=nombre_campo,
            etiqueta=etiqueta,
            valor=valor_limpio,
            detectado=bool(valor_limpio),
            estrategia=estrategia if valor_limpio else "no_detectado",
        )

    def _obtener_texto_fuente(self, resultado: ResultadoAnalisisPDF) -> tuple[str, str]:
        if resultado.texto_final_revisado.strip():
            return resultado.texto_final_revisado, "texto_final_revisado"
        if resultado.texto_completo.strip():
            return resultado.texto_completo, "texto_digital"
        if resultado.texto_ocr_completo.strip():
            return resultado.texto_ocr_completo, "texto_ocr"
        return "", "sin_texto"

    def _extraer_numero_poliza(self, texto: str) -> tuple[str, str]:
        patrones = [
            r"P[ÓO]LIZA\s*(?:N[°ºO]\.?|NRO\.?|NÚMERO)?\s*[:#]?\s*([A-Z0-9\-\/]+)",
            r"N[ÚU]MERO\s+DE\s+P[ÓO]LIZA\s*[:#]?\s*([A-Z0-9\-\/]+)",
        ]

        for patron in patrones:
            coincidencia = re.search(patron, texto, re.IGNORECASE)
            if coincidencia:
                return coincidencia.group(1), "regex_etiqueta"

        return "", "no_detectado"

    def _extraer_fecha_emision(self, texto: str) -> tuple[str, str]:
        patrones = [
            r"FECHA\s+DE\s+EMISI[ÓO]N\s*[:#]?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})",
            r"EMISI[ÓO]N\s*[:#]?\s*([0-9]{2}/[0-9]{2}/[0-9]{4})",
        ]

        for patron in patrones:
            coincidencia = re.search(patron, texto, re.IGNORECASE)
            if coincidencia:
                return coincidencia.group(1), "regex_etiqueta"

        lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]
        for linea in lineas[:20]:
            linea_mayus = linea.upper()
            if "VIGENCIA" in linea_mayus:
                continue
            coincidencia = re.search(r"\b([0-9]{2}/[0-9]{2}/[0-9]{4})\b", linea)
            if coincidencia:
                return coincidencia.group(1), "heuristica_encabezado"

        return "", "no_detectado"

    def _extraer_vigencia_desde(self, texto: str) -> tuple[str, str]:
        coincidencia = re.search(
            r"VIGENCIA\s+DESDE\s*[:#]?\s*([^\n\r]+)",
            texto,
            re.IGNORECASE,
        )
        if coincidencia:
            return coincidencia.group(1), "regex_etiqueta"

        return "", "no_detectado"

    def _extraer_vigencia_hasta(self, texto: str) -> tuple[str, str]:
        coincidencia = re.search(
            r"VIGENCIA\s+HASTA\s*[:#]?\s*([^\n\r]+)",
            texto,
            re.IGNORECASE,
        )
        if coincidencia:
            return coincidencia.group(1), "regex_etiqueta"

        return "", "no_detectado"

    def _extraer_aseguradora(self, texto: str) -> tuple[str, str]:
        palabras_clave = [
            "SEGUROS",
            "CIA DE SEG",
            "COMPAÑIA DE SEGUROS",
            "SEGUROS Y REASEGUROS",
            "CIA DE SEG Y REAS",
            "ASEGURADORA",
        ]

        lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]

        for linea in lineas[:20]:
            linea_mayus = linea.upper()
            if any(clave in linea_mayus for clave in palabras_clave):
                if "DATOS DEL" in linea_mayus or "CORREDOR" in linea_mayus:
                    continue
                return linea, "heuristica_encabezado"

        return "", "no_detectado"

    def _extraer_contratante(self, texto: str) -> tuple[str, str]:
        bloque = self._extraer_bloque_contratante(texto)

        if bloque:
            coincidencia = re.search(
                r"RAZ[ÓO]N\s+SOCIAL\s+(.+?)(?:\s+RUC\b|$)",
                bloque,
                re.IGNORECASE,
            )
            if coincidencia:
                return coincidencia.group(1), "bloque_contratante_razon_social"

            coincidencia = re.search(
                r"NOMBRE\s+(.+?)(?:\s+RUC\b|$)",
                bloque,
                re.IGNORECASE,
            )
            if coincidencia:
                return coincidencia.group(1), "bloque_contratante_nombre"

        coincidencia = re.search(
            r"CONTRATANTE\s*[:#]?\s*([^\n\r]+)",
            texto,
            re.IGNORECASE,
        )
        if coincidencia:
            return coincidencia.group(1), "regex_etiqueta"

        return "", "no_detectado"

    def _extraer_ruc(self, texto: str) -> tuple[str, str]:
        bloque = self._extraer_bloque_contratante(texto)

        if bloque:
            coincidencia = re.search(r"\bRUC\s*[:#]?\s*(\d{11})\b", bloque, re.IGNORECASE)
            if coincidencia:
                return coincidencia.group(1), "bloque_contratante_ruc"

        coincidencia = re.search(r"\bRUC\s*[:#]?\s*(\d{11})\b", texto, re.IGNORECASE)
        if coincidencia:
            return coincidencia.group(1), "regex_etiqueta"

        return "", "no_detectado"

    def _extraer_moneda(self, texto: str) -> tuple[str, str]:
        coincidencia = re.search(
            r"\bMONEDA\b\s*[:#]?\s*(US\$|USD|DOLARES|DÓLARES|SOLES|S\/|PEN)",
            texto,
            re.IGNORECASE,
        )
        if coincidencia:
            return coincidencia.group(1), "regex_etiqueta"

        coincidencia = re.search(
            r"\bMONEDA\b[^\n\r]*\b(US\$|USD|DOLARES|DÓLARES|SOLES|S\/|PEN)\b",
            texto,
            re.IGNORECASE,
        )
        if coincidencia:
            return coincidencia.group(1), "regex_contexto"

        return "", "no_detectado"

    def _extraer_bloque_contratante(self, texto: str) -> str:
        lineas = [linea.strip() for linea in texto.splitlines() if linea.strip()]

        inicio = -1
        for indice, linea in enumerate(lineas):
            if "DATOS DEL CONTRATANTE" in linea.upper():
                inicio = indice + 1
                break

        if inicio == -1:
            return ""

        lineas_bloque = []
        encabezados_corte = (
            "DATOS DEL ASEGURADO",
            "DATOS DEL VEHICULO",
            "DATOS DEL VEHÍCULO",
            "DATOS DEL CORREDOR",
            "DATOS DEL RIESGO",
            "COBERTURAS",
            "PRIMAS",
            "CONDICIONES",
            "SERVICIOS",
            "RESUMEN",
        )

        for linea in lineas[inicio:]:
            linea_mayus = linea.upper()
            if any(linea_mayus.startswith(encabezado) for encabezado in encabezados_corte):
                break
            lineas_bloque.append(linea)

        return "\n".join(lineas_bloque)

    def _limpiar_valor(self, valor: str) -> str:
        valor = valor.strip()
        valor = re.sub(r"\s+", " ", valor)
        valor = valor.strip(" :-")
        return valor