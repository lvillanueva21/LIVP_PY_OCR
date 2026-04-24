from __future__ import annotations

from typing import Iterable

from metricas_analisis import (
    ComparacionPaginaAnalisis,
    MetricaDocumentoModo,
    MetricaPaginaModo,
    ResumenComparacionAnalisis,
)
from modos_analisis import ModoAnalisis
from recomendador_modo import RecomendacionModo, RecomendadorModo
from score_extraccion import ScoreExtraccion


class ComparadorResultados:
    def __init__(
        self,
        score_extraccion: ScoreExtraccion | None = None,
        recomendador: RecomendadorModo | None = None,
    ) -> None:
        self.score_extraccion = score_extraccion or ScoreExtraccion()
        self.recomendador = recomendador or RecomendadorModo()

    def construir_metricas_paginas(self, resultado) -> list[MetricaPaginaModo]:
        metricas = []

        for pagina in resultado.resumen_paginas or []:
            texto_fuente, fuente_texto = self._seleccionar_texto_pagina(pagina)
            total_caracteres_utiles = len(texto_fuente.strip())

            observaciones = []
            if pagina.codigo_diagnostico == "ocr_recomendado":
                observaciones.append("Página candidata a OCR.")
            elif pagina.codigo_diagnostico == "mixta":
                observaciones.append("Página mixta o híbrida.")

            if pagina.ocr_error:
                observaciones.append(f"OCR con error: {pagina.ocr_error}")

            if pagina.ocr_observaciones:
                observaciones.extend(pagina.ocr_observaciones)

            observaciones = self._limpiar_lista(observaciones)

            metrica = MetricaPaginaModo(
                numero_pagina=pagina.numero_pagina,
                fuente_texto=fuente_texto,
                caracteres_texto_digital=len((pagina.texto_extraido or "").strip()),
                caracteres_texto_ocr=len((pagina.texto_ocr or "").strip()),
                caracteres_totales=pagina.ocr_caracteres_totales or total_caracteres_utiles,
                total_caracteres_utiles=total_caracteres_utiles,
                cantidad_palabras=pagina.ocr_cantidad_palabras,
                palabras_baja_confianza=pagina.ocr_palabras_baja_confianza,
                confianza_ocr_promedio=pagina.ocr_confianza_promedio,
                confianza_ocr_mediana=pagina.ocr_confianza_mediana,
                tiempo_total_ms=pagina.ocr_tiempo_total_ms,
                tiempo_ocr_ms=pagina.ocr_tiempo_ocr_ms,
                variante_ganadora=pagina.ocr_variante_ganadora,
                numero_intentos=pagina.ocr_numero_intentos,
                ruido_textual=pagina.ocr_ruido_textual,
                problemas_detectados=len(observaciones),
                dificultad=pagina.ocr_dificultad or "",
                dificultad_nivel=pagina.ocr_dificultad_nivel,
                dificultad_indice=pagina.ocr_dificultad_indice,
                requiere_revision=pagina.ocr_requiere_revision,
                observaciones=observaciones,
            )

            metricas.append(self.score_extraccion.puntuar_pagina(metrica))

        return metricas

    def construir_metricas_documento(self, resultado) -> MetricaDocumentoModo:
        metricas_paginas = self.construir_metricas_paginas(resultado)
        campos_detectados = sum(1 for campo in resultado.campos_extraidos if campo.detectado)

        paginas_con_texto_digital = sum(
            1 for metrica in metricas_paginas if metrica.fuente_texto == "texto_digital"
        )
        paginas_con_ocr = sum(
            1 for metrica in metricas_paginas if metrica.fuente_texto == "texto_ocr"
        )

        texto_fuente = (
            (resultado.texto_final_revisado or "").strip()
            or (resultado.texto_completo or "").strip()
            or (resultado.texto_ocr_completo or "").strip()
        )

        total_caracteres = sum(metrica.caracteres_totales for metrica in metricas_paginas)
        total_palabras = sum(metrica.cantidad_palabras for metrica in metricas_paginas)
        palabras_baja_confianza_totales = sum(metrica.palabras_baja_confianza for metrica in metricas_paginas)

        confianza_promedio_positiva = [
            metrica.confianza_ocr_promedio
            for metrica in metricas_paginas
            if metrica.confianza_ocr_promedio > 0
        ]
        confianza_mediana_positiva = [
            metrica.confianza_ocr_mediana
            for metrica in metricas_paginas
            if metrica.confianza_ocr_mediana > 0
        ]

        confianza_ocr_promedio = (
            round(sum(confianza_promedio_positiva) / len(confianza_promedio_positiva), 2)
            if confianza_promedio_positiva
            else 0.0
        )
        confianza_ocr_mediana = (
            round(sum(confianza_mediana_positiva) / len(confianza_mediana_positiva), 2)
            if confianza_mediana_positiva
            else 0.0
        )

        ruido_textual_promedio = (
            round(sum(metrica.ruido_textual for metrica in metricas_paginas) / len(metricas_paginas), 4)
            if metricas_paginas
            else 1.0
        )

        numero_total_intentos = sum(metrica.numero_intentos for metrica in metricas_paginas)
        problemas_detectados = sum(metrica.problemas_detectados for metrica in metricas_paginas)
        paginas_revision_recomendada = sum(1 for metrica in metricas_paginas if metrica.requiere_revision)

        paginas_faciles = sum(1 for metrica in metricas_paginas if metrica.dificultad == "fácil")
        paginas_medias = sum(1 for metrica in metricas_paginas if metrica.dificultad == "media")
        paginas_dificiles = sum(1 for metrica in metricas_paginas if metrica.dificultad == "difícil")
        paginas_criticas = sum(1 for metrica in metricas_paginas if metrica.dificultad == "crítica")

        observaciones = []
        if resultado.codigo_estado_ocr in {"parcial", "error", "no_disponible"}:
            observaciones.append(f"Estado OCR: {resultado.estado_ocr}")
        if resultado.observaciones_modo:
            observaciones.extend(resultado.observaciones_modo)

        metrica = MetricaDocumentoModo(
            modo=resultado.modo_analisis,
            etiqueta_modo=resultado.etiqueta_modo,
            paginas_totales=resultado.cantidad_paginas,
            paginas_con_texto_digital=paginas_con_texto_digital,
            paginas_con_ocr=paginas_con_ocr,
            total_caracteres_utiles=len(texto_fuente),
            total_caracteres=total_caracteres,
            total_palabras=total_palabras,
            palabras_baja_confianza_totales=palabras_baja_confianza_totales,
            confianza_ocr_promedio=confianza_ocr_promedio,
            confianza_ocr_mediana=confianza_ocr_mediana,
            numero_total_intentos=numero_total_intentos,
            ruido_textual_promedio=ruido_textual_promedio,
            problemas_detectados=problemas_detectados,
            paginas_revision_recomendada=paginas_revision_recomendada,
            paginas_faciles=paginas_faciles,
            paginas_medias=paginas_medias,
            paginas_dificiles=paginas_dificiles,
            paginas_criticas=paginas_criticas,
            cantidad_campos_detectados=campos_detectados,
            tiempo_total_ms=getattr(resultado, "tiempo_total_ms", 0),
            observaciones=self._limpiar_lista(observaciones),
        )

        return self.score_extraccion.puntuar_documento(metrica)

    def recomendar_modo(self, resultado) -> RecomendacionModo:
        metrica = self.construir_metricas_documento(resultado)
        return self.recomendador.recomendar(resultado, metrica)

    def comparar(self, resultado_basico, resultado_pro) -> ResumenComparacionAnalisis:
        metricas_basico = resultado_basico.metricas_documento_modo or self.construir_metricas_documento(resultado_basico)
        metricas_pro = resultado_pro.metricas_documento_modo or self.construir_metricas_documento(resultado_pro)

        paginas_basico = resultado_basico.metricas_paginas_modo or self.construir_metricas_paginas(resultado_basico)
        paginas_pro = resultado_pro.metricas_paginas_modo or self.construir_metricas_paginas(resultado_pro)

        comparaciones_paginas = self._comparar_paginas(paginas_basico, paginas_pro)

        score_basico = metricas_basico.score_total if metricas_basico else 0.0
        score_pro = metricas_pro.score_total if metricas_pro else 0.0
        diferencia = round(abs(score_basico - score_pro), 2)

        revision_manual_recomendada = self._debe_recomendar_revision_manual(
            metricas_basico,
            metricas_pro,
            comparaciones_paginas,
        )
        motivo_revision = self._motivo_revision_manual(
            metricas_basico,
            metricas_pro,
            comparaciones_paginas,
        )

        if revision_manual_recomendada and diferencia <= 2.5:
            modo_ganador = "revision_manual_recomendada"
            etiqueta_ganador = "Revisión manual recomendada"
            motivo = motivo_revision
        elif diferencia <= 2.5:
            modo_ganador = "empate"
            etiqueta_ganador = "Empate"
            motivo = "Ambos modos quedaron demasiado cerca en score comparativo."
        elif score_pro > score_basico:
            modo_ganador = ModoAnalisis.PRO
            etiqueta_ganador = "Ganó Pro"
            motivo = self._motivo_ganador_documento(metricas_basico, metricas_pro, "pro")
        else:
            modo_ganador = ModoAnalisis.BASICO
            etiqueta_ganador = "Ganó Básico"
            motivo = self._motivo_ganador_documento(metricas_basico, metricas_pro, "basico")

        observaciones = []
        if resultado_basico.codigo_estado_ocr == "no_ejecutado":
            observaciones.append("Modo Básico omitió OCR porque no lo necesitó o no encontró páginas candidatas.")
        if resultado_pro.codigo_estado_ocr == "no_ejecutado":
            observaciones.append("Modo Pro no aplicó OCR porque no encontró páginas candidatas.")
        if metricas_pro.numero_total_intentos > 0:
            observaciones.append(
                f"Modo Pro realizó {metricas_pro.numero_total_intentos} intento(s) OCR."
            )

        recomendacion = resultado_pro.recomendacion_modo or resultado_basico.recomendacion_modo

        return ResumenComparacionAnalisis(
            modo_ganador=modo_ganador,
            etiqueta_ganador=etiqueta_ganador,
            score_basico=score_basico,
            score_pro=score_pro,
            diferencia_absoluta=diferencia,
            motivo=motivo,
            recomendacion=recomendacion,
            observaciones=self._limpiar_lista(observaciones),
            comparaciones_paginas=comparaciones_paginas,
            revision_manual_recomendada=revision_manual_recomendada,
            motivo_revision_manual=motivo_revision,
        )

    def _comparar_paginas(
        self,
        paginas_basico: list[MetricaPaginaModo],
        paginas_pro: list[MetricaPaginaModo],
    ) -> list[ComparacionPaginaAnalisis]:
        mapa_basico = {metrica.numero_pagina: metrica for metrica in paginas_basico}
        mapa_pro = {metrica.numero_pagina: metrica for metrica in paginas_pro}

        comparaciones = []
        numeros_paginas = sorted(set(mapa_basico.keys()) | set(mapa_pro.keys()))

        for numero_pagina in numeros_paginas:
            metrica_basico = mapa_basico.get(numero_pagina)
            metrica_pro = mapa_pro.get(numero_pagina)

            score_basico = metrica_basico.score_total if metrica_basico else 0.0
            score_pro = metrica_pro.score_total if metrica_pro else 0.0
            diferencia = round(abs(score_basico - score_pro), 2)

            if diferencia <= 2.0:
                modo_ganador = "empate"
                etiqueta_ganador = "Empate"
                motivo = "Ambos modos quedaron muy cerca en esta página."
            elif score_pro > score_basico:
                modo_ganador = ModoAnalisis.PRO
                etiqueta_ganador = "Pro"
                motivo = self._motivo_ganador_pagina(metrica_basico, metrica_pro, "pro")
            else:
                modo_ganador = ModoAnalisis.BASICO
                etiqueta_ganador = "Básico"
                motivo = self._motivo_ganador_pagina(metrica_basico, metrica_pro, "basico")

            revision_manual = (
                (metrica_basico and metrica_basico.requiere_revision)
                and (metrica_pro and metrica_pro.requiere_revision)
            )

            comparaciones.append(
                ComparacionPaginaAnalisis(
                    numero_pagina=numero_pagina,
                    score_basico=score_basico,
                    score_pro=score_pro,
                    diferencia_absoluta=diferencia,
                    modo_ganador=modo_ganador,
                    etiqueta_ganador=etiqueta_ganador,
                    motivo=motivo,
                    revision_manual_recomendada=revision_manual,
                    fuente_basico=metrica_basico.fuente_texto if metrica_basico else "-",
                    fuente_pro=metrica_pro.fuente_texto if metrica_pro else "-",
                    dificultad_basico=metrica_basico.dificultad if metrica_basico else "-",
                    dificultad_pro=metrica_pro.dificultad if metrica_pro else "-",
                    observaciones=self._construir_observaciones_pagina(metrica_basico, metrica_pro),
                )
            )

        return comparaciones

    def _motivo_ganador_documento(
        self,
        basico: MetricaDocumentoModo,
        pro: MetricaDocumentoModo,
        ganador: str,
    ) -> str:
        if ganador == "pro":
            if pro.cantidad_campos_detectados > basico.cantidad_campos_detectados:
                return "El modo Pro detectó más campos clave en el documento."
            if pro.score_legibilidad > basico.score_legibilidad:
                return "El modo Pro produjo un texto más legible."
            if pro.score_confianza > basico.score_confianza:
                return "El modo Pro obtuvo mejor confianza OCR estimada."
            if pro.paginas_criticas < basico.paginas_criticas:
                return "El modo Pro redujo la cantidad de páginas críticas."
            return "El modo Pro logró mejor score comparativo global."
        else:
            if basico.cantidad_campos_detectados > pro.cantidad_campos_detectados:
                return "El modo Básico detectó más campos clave en el documento."
            if basico.score_velocidad > pro.score_velocidad:
                return "El modo Básico mantuvo una mejor relación entre resultado y tiempo."
            if basico.score_estabilidad > pro.score_estabilidad:
                return "El modo Básico mostró un procesamiento más estable."
            return "El modo Básico logró mejor score comparativo global."

    def _motivo_ganador_pagina(
        self,
        basico: MetricaPaginaModo | None,
        pro: MetricaPaginaModo | None,
        ganador: str,
    ) -> str:
        if basico is None or pro is None:
            return "No se pudo comparar completamente esta página."

        if ganador == "pro":
            if pro.score_legibilidad > basico.score_legibilidad + 2:
                return "El modo Pro produjo mejor legibilidad en esta página."
            if pro.score_confianza > basico.score_confianza + 2:
                return "El modo Pro obtuvo mejor confianza OCR en esta página."
            if pro.score_texto_util > basico.score_texto_util + 2:
                return "El modo Pro extrajo más texto útil en esta página."
            if pro.dificultad_nivel < basico.dificultad_nivel:
                return "El modo Pro redujo la dificultad estimada de esta página."
            return "El modo Pro logró mejor score total en esta página."

        if basico.score_velocidad > pro.score_velocidad + 8:
            return "El modo Básico fue claramente más rápido en esta página."
        if basico.score_estabilidad > pro.score_estabilidad + 2:
            return "El modo Básico fue más estable en esta página."
        if basico.score_legibilidad > pro.score_legibilidad + 2:
            return "El modo Básico produjo un texto más legible en esta página."
        return "El modo Básico logró mejor score total en esta página."

    def _debe_recomendar_revision_manual(
        self,
        basico: MetricaDocumentoModo,
        pro: MetricaDocumentoModo,
        comparaciones_paginas: list[ComparacionPaginaAnalisis],
    ) -> bool:
        paginas_revision = sum(1 for pagina in comparaciones_paginas if pagina.revision_manual_recomendada)
        if paginas_revision > 0:
            return True

        if basico.cantidad_campos_detectados <= 2 and pro.cantidad_campos_detectados <= 2:
            return True

        if basico.score_total < 50 and pro.score_total < 55:
            return True

        if basico.paginas_criticas > 0 and pro.paginas_criticas > 0:
            return True

        return False

    def _motivo_revision_manual(
        self,
        basico: MetricaDocumentoModo,
        pro: MetricaDocumentoModo,
        comparaciones_paginas: list[ComparacionPaginaAnalisis],
    ) -> str:
        paginas_revision = [pagina.numero_pagina for pagina in comparaciones_paginas if pagina.revision_manual_recomendada]
        if paginas_revision:
            return f"Se recomienda revisión manual: páginas problemáticas detectadas ({', '.join(map(str, paginas_revision))})."

        if basico.cantidad_campos_detectados <= 2 and pro.cantidad_campos_detectados <= 2:
            return "Se recomienda revisión manual: ambos modos detectaron muy pocos campos clave."

        if basico.paginas_criticas > 0 and pro.paginas_criticas > 0:
            return "Se recomienda revisión manual: ambos modos mantienen páginas críticas."

        return "Se recomienda revisión manual: ambos modos quedaron con score bajo o demasiado cercano."

    def _construir_observaciones_pagina(
        self,
        basico: MetricaPaginaModo | None,
        pro: MetricaPaginaModo | None,
    ) -> list[str]:
        observaciones = []
        if basico:
            observaciones.extend([f"Básico: {obs}" for obs in basico.observaciones[:2]])
        if pro:
            observaciones.extend([f"Pro: {obs}" for obs in pro.observaciones[:2]])
        return self._limpiar_lista(observaciones)

    def _seleccionar_texto_pagina(self, pagina) -> tuple[str, str]:
        texto_digital = (pagina.texto_extraido or "").strip()
        texto_ocr = (pagina.texto_ocr or "").strip()

        if texto_ocr and len(texto_ocr) > len(texto_digital):
            return texto_ocr, "texto_ocr"
        if texto_digital:
            return texto_digital, "texto_digital"
        if texto_ocr:
            return texto_ocr, "texto_ocr"
        return "", "sin_texto"

    def _limpiar_lista(self, valores: Iterable[str]) -> list[str]:
        salida = []
        for valor in valores:
            valor = (valor or "").strip()
            if valor and valor not in salida:
                salida.append(valor)
        return salida