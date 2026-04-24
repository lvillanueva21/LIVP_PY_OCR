import json
from pathlib import Path

from modelos import ResultadoAnalisisPDF


class ExportadorResultados:
    def exportar_json(
        self,
        resultado: ResultadoAnalisisPDF,
        ruta_destino: str,
        *,
        resultado_basico: ResultadoAnalisisPDF | None = None,
        resultado_pro: ResultadoAnalisisPDF | None = None,
        comparacion=None,
    ) -> None:
        if resultado is None:
            raise ValueError("No hay resultados para exportar.")

        ruta = Path(ruta_destino)
        datos = self._construir_diccionario(
            resultado,
            resultado_basico=resultado_basico,
            resultado_pro=resultado_pro,
            comparacion=comparacion,
        )

        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=4)

    def exportar_txt(
        self,
        resultado: ResultadoAnalisisPDF,
        ruta_destino: str,
        *,
        resultado_basico: ResultadoAnalisisPDF | None = None,
        resultado_pro: ResultadoAnalisisPDF | None = None,
        comparacion=None,
    ) -> None:
        if resultado is None:
            raise ValueError("No hay resultados para exportar.")

        ruta = Path(ruta_destino)
        contenido = self._construir_texto_plano(
            resultado,
            resultado_basico=resultado_basico,
            resultado_pro=resultado_pro,
            comparacion=comparacion,
        )

        with ruta.open("w", encoding="utf-8") as archivo:
            archivo.write(contenido)

    def _construir_diccionario(
        self,
        resultado: ResultadoAnalisisPDF,
        *,
        resultado_basico: ResultadoAnalisisPDF | None = None,
        resultado_pro: ResultadoAnalisisPDF | None = None,
        comparacion=None,
    ) -> dict:
        datos = {
            "modo": {
                "modo_analisis": resultado.modo_analisis,
                "etiqueta_modo": resultado.etiqueta_modo,
                "recomendacion_modo": resultado.recomendacion_modo,
                "observaciones_modo": resultado.observaciones_modo,
                "es_provisional": resultado.es_provisional,
                "tiempo_total_ms": resultado.tiempo_total_ms,
            },
            "documento": {
                "ruta_archivo": resultado.ruta_archivo,
                "nombre_archivo": resultado.nombre_archivo,
                "cantidad_paginas": resultado.cantidad_paginas,
                "tiene_texto_digital": resultado.tiene_texto_digital,
                "necesita_ocr": resultado.necesita_ocr,
            },
            "diagnostico": {
                "diagnostico_general": resultado.diagnostico_general,
                "codigo_diagnostico_general": resultado.codigo_diagnostico_general,
                "detalle_diagnostico": resultado.detalle_diagnostico,
                "confianza_diagnostico": resultado.confianza_diagnostico,
            },
            "ocr": {
                "tipo_ocr_sugerido": resultado.tipo_ocr_sugerido,
                "estado_ocr": resultado.estado_ocr,
                "codigo_estado_ocr": resultado.codigo_estado_ocr,
                "detalle_ocr": resultado.detalle_ocr,
                "motor_ocr": resultado.motor_ocr,
                "apto_para_ocr": resultado.apto_para_ocr,
                "ocr_disponible": resultado.ocr_disponible,
                "requiere_preprocesamiento": resultado.requiere_preprocesamiento,
                "paginas_ocr_objetivo": resultado.paginas_ocr_objetivo,
                "paginas_ocr_procesadas": resultado.paginas_ocr_procesadas,
                "acciones_preparacion": resultado.acciones_preparacion,
                "errores_ocr": resultado.errores_ocr,
            },
            "extraccion": {
                "fuente_texto": resultado.texto_fuente_extraccion,
                "campos": [
                    {
                        "nombre_campo": campo.nombre_campo,
                        "etiqueta": campo.etiqueta,
                        "valor": campo.valor,
                        "detectado": campo.detectado,
                        "estrategia": campo.estrategia,
                    }
                    for campo in resultado.campos_extraidos
                ],
            },
            "metricas": {
                "documento": self._serializar_metrica_documento(resultado.metricas_documento_modo),
                "paginas": [self._serializar_metrica_pagina(metrica) for metrica in resultado.metricas_paginas_modo],
            },
            "paginas": [
                {
                    "numero_pagina": pagina.numero_pagina,
                    "tiene_texto": pagina.tiene_texto,
                    "cantidad_caracteres": pagina.cantidad_caracteres,
                    "cantidad_imagenes": pagina.cantidad_imagenes,
                    "cobertura_imagen": pagina.cobertura_imagen,
                    "codigo_diagnostico": pagina.codigo_diagnostico,
                    "diagnostico": pagina.diagnostico,
                    "confianza": pagina.confianza,
                    "ocr_ejecutado": pagina.ocr_ejecutado,
                    "ocr_error": pagina.ocr_error,
                    "texto_extraido": pagina.texto_extraido,
                    "texto_ocr": pagina.texto_ocr,
                    "ocr_confianza_promedio": pagina.ocr_confianza_promedio,
                    "ocr_confianza_mediana": pagina.ocr_confianza_mediana,
                    "ocr_cantidad_palabras": pagina.ocr_cantidad_palabras,
                    "ocr_palabras_baja_confianza": pagina.ocr_palabras_baja_confianza,
                    "ocr_caracteres_totales": pagina.ocr_caracteres_totales,
                    "ocr_ruido_textual": pagina.ocr_ruido_textual,
                    "ocr_tiempo_total_ms": pagina.ocr_tiempo_total_ms,
                    "ocr_tiempo_ocr_ms": pagina.ocr_tiempo_ocr_ms,
                    "ocr_variante_ganadora": pagina.ocr_variante_ganadora,
                    "ocr_numero_intentos": pagina.ocr_numero_intentos,
                    "ocr_score_estimado": pagina.ocr_score_estimado,
                    "ocr_dificultad": pagina.ocr_dificultad,
                    "ocr_dificultad_nivel": pagina.ocr_dificultad_nivel,
                    "ocr_dificultad_indice": pagina.ocr_dificultad_indice,
                    "ocr_requiere_revision": pagina.ocr_requiere_revision,
                    "ocr_observaciones": pagina.ocr_observaciones,
                }
                for pagina in resultado.resumen_paginas
            ],
            "textos": {
                "texto_digital_completo": resultado.texto_completo,
                "texto_ocr_completo": resultado.texto_ocr_completo,
                "texto_final_revisado": resultado.texto_final_revisado,
            },
        }

        if resultado_basico is not None:
            datos["resultado_basico"] = {
                "modo": resultado_basico.etiqueta_modo,
                "metricas_documento": self._serializar_metrica_documento(resultado_basico.metricas_documento_modo),
            }

        if resultado_pro is not None:
            datos["resultado_pro"] = {
                "modo": resultado_pro.etiqueta_modo,
                "metricas_documento": self._serializar_metrica_documento(resultado_pro.metricas_documento_modo),
            }

        if comparacion is not None:
            datos["comparacion"] = self._serializar_comparacion(comparacion)

        return datos

    def _construir_texto_plano(
        self,
        resultado: ResultadoAnalisisPDF,
        *,
        resultado_basico: ResultadoAnalisisPDF | None = None,
        resultado_pro: ResultadoAnalisisPDF | None = None,
        comparacion=None,
    ) -> str:
        lineas = []

        lineas.append("RESULTADO DE ANÁLISIS DE PDF")
        lineas.append("=" * 80)
        lineas.append("")
        lineas.append("MODO DE ANÁLISIS")
        lineas.append("-" * 80)
        lineas.append(f"Modo ejecutado: {resultado.etiqueta_modo}")
        lineas.append(f"Recomendación automática: {resultado.recomendacion_modo or '-'}")
        lineas.append(f"Tiempo total: {resultado.tiempo_total_ms} ms")
        if resultado.observaciones_modo:
            lineas.append("Razones / observaciones:")
            for observacion in resultado.observaciones_modo:
                lineas.append(f"- {observacion}")
        lineas.append("")

        if comparacion is not None:
            lineas.append("COMPARACIÓN DE MODOS")
            lineas.append("-" * 80)
            lineas.append(f"Ganador: {comparacion.etiqueta_ganador or '-'}")
            lineas.append(f"Score Básico: {comparacion.score_basico}")
            lineas.append(f"Score Pro: {comparacion.score_pro}")
            lineas.append(f"Diferencia: {comparacion.diferencia_absoluta}")
            lineas.append(f"Motivo: {comparacion.motivo or '-'}")
            lineas.append(f"Recomendación: {comparacion.recomendacion or '-'}")
            lineas.append(
                f"Revisión manual recomendada: {'Sí' if comparacion.revision_manual_recomendada else 'No'}"
            )
            if comparacion.motivo_revision_manual:
                lineas.append(f"Motivo revisión manual: {comparacion.motivo_revision_manual}")
            if comparacion.observaciones:
                lineas.append("Observaciones:")
                for observacion in comparacion.observaciones:
                    lineas.append(f"- {observacion}")
            lineas.append("")

        if resultado.metricas_documento_modo is not None:
            metrica = resultado.metricas_documento_modo
            lineas.append("MÉTRICAS DEL MODO MOSTRADO")
            lineas.append("-" * 80)
            lineas.append(f"Score total: {metrica.score_total}")
            lineas.append(f"Score campos: {metrica.score_campos}")
            lineas.append(f"Score legibilidad: {metrica.score_legibilidad}")
            lineas.append(f"Score confianza: {metrica.score_confianza}")
            lineas.append(f"Score texto útil: {metrica.score_texto_util}")
            lineas.append(f"Score estabilidad: {metrica.score_estabilidad}")
            lineas.append(f"Score velocidad: {metrica.score_velocidad}")
            lineas.append(f"Confianza OCR promedio: {metrica.confianza_ocr_promedio}")
            lineas.append(f"Confianza OCR mediana: {metrica.confianza_ocr_mediana}")
            lineas.append(f"Palabras con baja confianza: {metrica.palabras_baja_confianza_totales}")
            lineas.append(f"Ruido textual promedio: {metrica.ruido_textual_promedio}")
            lineas.append(f"Páginas fáciles: {metrica.paginas_faciles}")
            lineas.append(f"Páginas medias: {metrica.paginas_medias}")
            lineas.append(f"Páginas difíciles: {metrica.paginas_dificiles}")
            lineas.append(f"Páginas críticas: {metrica.paginas_criticas}")
            lineas.append(f"Páginas con revisión sugerida: {metrica.paginas_revision_recomendada}")
            lineas.append("")

        return "\n".join(lineas)

    def _serializar_metrica_documento(self, metrica) -> dict | None:
        if metrica is None:
            return None

        return {
            "modo": metrica.modo,
            "etiqueta_modo": metrica.etiqueta_modo,
            "paginas_totales": metrica.paginas_totales,
            "paginas_con_texto_digital": metrica.paginas_con_texto_digital,
            "paginas_con_ocr": metrica.paginas_con_ocr,
            "total_caracteres_utiles": metrica.total_caracteres_utiles,
            "total_caracteres": metrica.total_caracteres,
            "total_palabras": metrica.total_palabras,
            "palabras_baja_confianza_totales": metrica.palabras_baja_confianza_totales,
            "confianza_ocr_promedio": metrica.confianza_ocr_promedio,
            "confianza_ocr_mediana": metrica.confianza_ocr_mediana,
            "numero_total_intentos": metrica.numero_total_intentos,
            "ruido_textual_promedio": metrica.ruido_textual_promedio,
            "problemas_detectados": metrica.problemas_detectados,
            "paginas_revision_recomendada": metrica.paginas_revision_recomendada,
            "paginas_faciles": metrica.paginas_faciles,
            "paginas_medias": metrica.paginas_medias,
            "paginas_dificiles": metrica.paginas_dificiles,
            "paginas_criticas": metrica.paginas_criticas,
            "cantidad_campos_detectados": metrica.cantidad_campos_detectados,
            "tiempo_total_ms": metrica.tiempo_total_ms,
            "score_campos": metrica.score_campos,
            "score_legibilidad": metrica.score_legibilidad,
            "score_confianza": metrica.score_confianza,
            "score_texto_util": metrica.score_texto_util,
            "score_estabilidad": metrica.score_estabilidad,
            "score_velocidad": metrica.score_velocidad,
            "score_total": metrica.score_total,
            "observaciones": metrica.observaciones,
        }

    def _serializar_metrica_pagina(self, metrica) -> dict | None:
        if metrica is None:
            return None

        return {
            "numero_pagina": metrica.numero_pagina,
            "fuente_texto": metrica.fuente_texto,
            "caracteres_texto_digital": metrica.caracteres_texto_digital,
            "caracteres_texto_ocr": metrica.caracteres_texto_ocr,
            "caracteres_totales": metrica.caracteres_totales,
            "total_caracteres_utiles": metrica.total_caracteres_utiles,
            "cantidad_palabras": metrica.cantidad_palabras,
            "palabras_baja_confianza": metrica.palabras_baja_confianza,
            "confianza_ocr_promedio": metrica.confianza_ocr_promedio,
            "confianza_ocr_mediana": metrica.confianza_ocr_mediana,
            "tiempo_total_ms": metrica.tiempo_total_ms,
            "tiempo_ocr_ms": metrica.tiempo_ocr_ms,
            "variante_ganadora": metrica.variante_ganadora,
            "numero_intentos": metrica.numero_intentos,
            "ruido_textual": metrica.ruido_textual,
            "problemas_detectados": metrica.problemas_detectados,
            "dificultad": metrica.dificultad,
            "dificultad_nivel": metrica.dificultad_nivel,
            "dificultad_indice": metrica.dificultad_indice,
            "requiere_revision": metrica.requiere_revision,
            "score_legibilidad": metrica.score_legibilidad,
            "score_confianza": metrica.score_confianza,
            "score_texto_util": metrica.score_texto_util,
            "score_estabilidad": metrica.score_estabilidad,
            "score_velocidad": metrica.score_velocidad,
            "score_total": metrica.score_total,
            "observaciones": metrica.observaciones,
        }

    def _serializar_comparacion(self, comparacion) -> dict | None:
        if comparacion is None:
            return None

        return {
            "modo_ganador": comparacion.modo_ganador,
            "etiqueta_ganador": comparacion.etiqueta_ganador,
            "score_basico": comparacion.score_basico,
            "score_pro": comparacion.score_pro,
            "diferencia_absoluta": comparacion.diferencia_absoluta,
            "motivo": comparacion.motivo,
            "recomendacion": comparacion.recomendacion,
            "observaciones": comparacion.observaciones,
            "revision_manual_recomendada": comparacion.revision_manual_recomendada,
            "motivo_revision_manual": comparacion.motivo_revision_manual,
            "comparaciones_paginas": [
                {
                    "numero_pagina": pagina.numero_pagina,
                    "score_basico": pagina.score_basico,
                    "score_pro": pagina.score_pro,
                    "diferencia_absoluta": pagina.diferencia_absoluta,
                    "modo_ganador": pagina.modo_ganador,
                    "etiqueta_ganador": pagina.etiqueta_ganador,
                    "motivo": pagina.motivo,
                    "revision_manual_recomendada": pagina.revision_manual_recomendada,
                    "fuente_basico": pagina.fuente_basico,
                    "fuente_pro": pagina.fuente_pro,
                    "dificultad_basico": pagina.dificultad_basico,
                    "dificultad_pro": pagina.dificultad_pro,
                    "observaciones": pagina.observaciones,
                }
                for pagina in comparacion.comparaciones_paginas
            ],
        }