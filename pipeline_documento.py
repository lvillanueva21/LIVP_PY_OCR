from time import perf_counter

from analizador_pdf import AnalizadorPDF
from comparador_resultados import ComparadorResultados
from controlador_cancelacion import DetencionSeguridadError
from etapas_proceso import (
    ESTADO_ADVERTENCIA,
    ESTADO_COMPLETADA,
    ESTADO_EN_CURSO,
    ESTADO_OMITIDA,
    ETAPA_COMPARACION_RESULTADOS,
    ETAPA_CONSOLIDACION_TEXTO,
    ETAPA_EVALUACION_OCR,
    ETAPA_EXTRACCION_CAMPOS,
    ETAPA_FINALIZACION,
    ETAPA_INSPECCION_INICIAL,
    ETAPA_LECTURA_TEXTO_DIGITAL,
    ETAPA_OCR,
    ProcesoCanceladoError,
)
from extractor_poliza import ExtractorPoliza
from limites_proceso import LimitesProceso
from modos_analisis import ModoAnalisis
from modelos import ResultadoAnalisisPDF
from monitor_recursos import MonitorRecursos
from procesador_imagen import ProcesadorImagen
from servicio_ocr import ServicioOCR
from servicio_ocr_pro import ServicioOCRPro


class PipelineDocumento:
    def __init__(
        self,
        analizador: AnalizadorPDF | None = None,
        procesador_imagen: ProcesadorImagen | None = None,
        servicio_ocr: ServicioOCR | None = None,
        servicio_ocr_pro: ServicioOCRPro | None = None,
        extractor_poliza: ExtractorPoliza | None = None,
        comparador_resultados: ComparadorResultados | None = None,
        limites_proceso: LimitesProceso | None = None,
        monitor_recursos: MonitorRecursos | None = None,
    ) -> None:
        self.limites = limites_proceso or LimitesProceso()
        self.monitor_recursos = monitor_recursos or MonitorRecursos(self.limites)

        self.analizador = analizador or AnalizadorPDF()
        self.procesador_imagen = procesador_imagen or ProcesadorImagen()
        self.servicio_ocr = servicio_ocr or ServicioOCR()
        self.servicio_ocr_pro = servicio_ocr_pro or ServicioOCRPro()
        self.extractor_poliza = extractor_poliza or ExtractorPoliza()
        self.comparador_resultados = comparador_resultados or ComparadorResultados()

    def procesar(
        self,
        ruta_archivo: str,
        callback=None,
        callback_etapa=None,
        callback_alerta=None,
        cancelador=None,
        controlador=None,
        modo_etiqueta: str = "Básico",
        paginas_forzadas: list[int] | None = None,
    ) -> ResultadoAnalisisPDF:
        return self._procesar_interno(
            ruta_archivo,
            modo=ModoAnalisis.BASICO,
            callback=callback,
            callback_etapa=callback_etapa,
            callback_alerta=callback_alerta,
            cancelador=cancelador,
            controlador=controlador,
            modo_etiqueta=modo_etiqueta,
            paginas_forzadas=paginas_forzadas,
        )

    def procesar_pro(
        self,
        ruta_archivo: str,
        callback=None,
        callback_etapa=None,
        callback_alerta=None,
        cancelador=None,
        controlador=None,
        modo_etiqueta: str = "Pro",
        paginas_forzadas: list[int] | None = None,
    ) -> ResultadoAnalisisPDF:
        return self._procesar_interno(
            ruta_archivo,
            modo=ModoAnalisis.PRO,
            callback=callback,
            callback_etapa=callback_etapa,
            callback_alerta=callback_alerta,
            cancelador=cancelador,
            controlador=controlador,
            modo_etiqueta=modo_etiqueta,
            paginas_forzadas=paginas_forzadas,
        )

    def _procesar_interno(
        self,
        ruta_archivo: str,
        *,
        modo: str,
        callback=None,
        callback_etapa=None,
        callback_alerta=None,
        cancelador=None,
        controlador=None,
        modo_etiqueta: str = "Básico",
        paginas_forzadas: list[int] | None = None,
    ) -> ResultadoAnalisisPDF:
        inicio = perf_counter()
        es_modo_pro = modo == ModoAnalisis.PRO

        self._controlar(controlador, cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_INSPECCION_INICIAL,
            ESTADO_EN_CURSO,
            f"Abriendo PDF y preparando análisis en modo {modo_etiqueta}.",
        )
        self._emitir_progreso(callback, 5, "Analizando PDF...")
        resultado = self.analizador.analizar(ruta_archivo)

        evaluacion_operativa = self.monitor_recursos.evaluar_documento(resultado, modo)

        resultado.alertas_operativas = self._limpiar_lista(
            evaluacion_operativa["alertas"] + evaluacion_operativa["recomendaciones"]
        )

        for mensaje in resultado.alertas_operativas:
            self._emitir_alerta(callback_alerta, mensaje)

        if evaluacion_operativa["detener_por_seguridad"]:
            mensaje = evaluacion_operativa["motivo_detencion"]
            if controlador is not None:
                controlador.detener_por_seguridad(mensaje)
            raise DetencionSeguridadError(mensaje)

        self._emitir_etapa(
            callback_etapa,
            ETAPA_INSPECCION_INICIAL,
            ESTADO_COMPLETADA,
            f"Documento inspeccionado correctamente. Páginas detectadas: {resultado.cantidad_paginas}.",
        )

        self._controlar(controlador, cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_LECTURA_TEXTO_DIGITAL,
            ESTADO_EN_CURSO,
            "Revisando texto digital disponible y diagnóstico inicial.",
        )
        if resultado.tiene_texto_digital:
            detalle_texto = "Se encontró texto digital suficiente en el documento."
        else:
            detalle_texto = "No se encontró texto digital suficiente; se evaluará OCR."
        self._emitir_etapa(
            callback_etapa,
            ETAPA_LECTURA_TEXTO_DIGITAL,
            ESTADO_COMPLETADA,
            detalle_texto,
        )

        self._controlar(controlador, cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_EVALUACION_OCR,
            ESTADO_EN_CURSO,
            "Evaluando necesidad de OCR y preparación de imagen.",
        )
        self._emitir_progreso(callback, 20, "Evaluando estrategia de OCR...")
        requiere_preprocesamiento, acciones_preparacion = self.procesador_imagen.evaluar_preparacion(
            resultado
        )

        resultado.requiere_preprocesamiento = requiere_preprocesamiento
        resultado.acciones_preparacion = acciones_preparacion
        resultado.paginas_ocr_forzadas = list(paginas_forzadas or [])

        if resultado.paginas_ocr_forzadas and len(resultado.paginas_ocr_forzadas) < resultado.cantidad_paginas:
            resultado.analisis_parcial = True
            resultado.observaciones_modo.append(
                f"Análisis parcial: OCR limitado a {len(resultado.paginas_ocr_forzadas)} página(s) candidatas."
            )
            self._emitir_alerta(
                callback_alerta,
                f"Comparación limitada a {len(resultado.paginas_ocr_forzadas)} página(s) candidatas por seguridad."
            )

        servicio_activo = self.servicio_ocr_pro if es_modo_pro else self.servicio_ocr
        codigo_estado_base, estado_base, detalle_base, apto_para_ocr = servicio_activo.obtener_estado(
            resultado
        )

        resultado.codigo_estado_ocr = codigo_estado_base
        resultado.estado_ocr = estado_base
        resultado.detalle_ocr = detalle_base
        resultado.apto_para_ocr = apto_para_ocr
        resultado.motor_ocr = servicio_activo.motor_ocr

        detalle_evaluacion = detalle_base
        if es_modo_pro and apto_para_ocr:
            detalle_evaluacion += " Se probarán variantes adaptativas por página según dificultad."
        if acciones_preparacion:
            detalle_evaluacion += f" Preparación sugerida: {' | '.join(acciones_preparacion)}."
        if resultado.paginas_ocr_forzadas:
            detalle_evaluacion += (
                f" OCR restringido a {len(resultado.paginas_ocr_forzadas)} página(s) por seguridad operativa."
            )

        self._emitir_etapa(
            callback_etapa,
            ETAPA_EVALUACION_OCR,
            ESTADO_COMPLETADA,
            detalle_evaluacion,
        )

        self._controlar(controlador, cancelador)

        if not resultado.apto_para_ocr:
            resultado.ocr_disponible = servicio_activo.esta_configurado()
            self._emitir_etapa(
                callback_etapa,
                ETAPA_OCR,
                ESTADO_OMITIDA,
                "OCR omitido: el documento ya tiene texto digital suficiente o no lo requiere.",
            )
            self._consolidar_y_extraer(
                resultado,
                callback=callback,
                callback_etapa=callback_etapa,
                cancelador=cancelador,
                controlador=controlador,
            )
            resultado.tiempo_total_ms = int((perf_counter() - inicio) * 1000)
            return resultado

        if not servicio_activo.esta_configurado():
            resultado.codigo_estado_ocr = "no_disponible"
            resultado.estado_ocr = "OCR no disponible"
            resultado.detalle_ocr = self._construir_detalle_ocr(
                "Tesseract no está instalado o no está accesible desde el sistema.",
                acciones_preparacion,
            )
            resultado.motor_ocr = servicio_activo.motor_ocr
            resultado.ocr_disponible = False

            self._emitir_etapa(
                callback_etapa,
                ETAPA_OCR,
                ESTADO_ADVERTENCIA,
                "OCR omitido: Tesseract no está disponible en el sistema.",
            )
            self._consolidar_y_extraer(
                resultado,
                callback=callback,
                callback_etapa=callback_etapa,
                cancelador=cancelador,
                controlador=controlador,
            )
            resultado.tiempo_total_ms = int((perf_counter() - inicio) * 1000)
            return resultado

        self._emitir_etapa(
            callback_etapa,
            ETAPA_OCR,
            ESTADO_EN_CURSO,
            f"Ejecutando OCR en modo {modo_etiqueta}.",
        )
        self._emitir_progreso(callback, 28, "Preparando OCR...")

        if es_modo_pro:
            resultado = self.servicio_ocr_pro.ejecutar_ocr_pro(
                resultado,
                callback=callback,
                cancelador=cancelador,
                controlador=controlador,
                limites=self.limites,
                callback_alerta=callback_alerta,
            )
        else:
            resultado = self.servicio_ocr.ejecutar_ocr(
                resultado,
                self.procesador_imagen,
                callback=callback,
                cancelador=cancelador,
                controlador=controlador,
                limites=self.limites,
                callback_alerta=callback_alerta,
            )

        resultado.detalle_ocr = self._construir_detalle_ocr(
            resultado.detalle_ocr,
            acciones_preparacion,
        )

        estado_ocr_etapa = ESTADO_COMPLETADA
        if resultado.codigo_estado_ocr in {"parcial", "no_disponible", "error"}:
            estado_ocr_etapa = ESTADO_ADVERTENCIA

        self._emitir_etapa(
            callback_etapa,
            ETAPA_OCR,
            estado_ocr_etapa,
            resultado.detalle_ocr,
        )

        self._consolidar_y_extraer(
            resultado,
            callback=callback,
            callback_etapa=callback_etapa,
            cancelador=cancelador,
            controlador=controlador,
        )
        resultado.tiempo_total_ms = int((perf_counter() - inicio) * 1000)

        if es_modo_pro:
            resultado.observaciones_modo.append(
                "Modo Pro ejecutó filtros adaptativos sobre páginas candidatas."
            )

        return resultado

    def procesar_segun_modo(
        self,
        ruta_archivo: str,
        modo: str,
        callback=None,
        callback_etapa=None,
        callback_alerta=None,
        cancelador=None,
        controlador=None,
    ) -> tuple[ResultadoAnalisisPDF, ResultadoAnalisisPDF | None, ResultadoAnalisisPDF | None, object | None]:
        self._emitir_etapa(
            callback_etapa,
            ETAPA_COMPARACION_RESULTADOS,
            ESTADO_OMITIDA,
            "Comparación aún no ejecutada.",
        )
        self._emitir_etapa(
            callback_etapa,
            ETAPA_FINALIZACION,
            ESTADO_OMITIDA,
            "Finalización pendiente.",
        )

        if modo == ModoAnalisis.BASICO:
            resultado_basico = self.procesar(
                ruta_archivo,
                callback=callback,
                callback_etapa=callback_etapa,
                callback_alerta=callback_alerta,
                cancelador=cancelador,
                controlador=controlador,
                modo_etiqueta="Básico",
            )
            self._finalizar_modo(resultado_basico, ModoAnalisis.BASICO)

            self._emitir_etapa(
                callback_etapa,
                ETAPA_COMPARACION_RESULTADOS,
                ESTADO_OMITIDA,
                "Comparación omitida: solo se ejecutó el modo Básico.",
            )
            self._emitir_etapa(
                callback_etapa,
                ETAPA_FINALIZACION,
                ESTADO_COMPLETADA,
                "Procesamiento en modo Básico completado.",
            )
            self._emitir_progreso(callback, 100, "Procesamiento completado.")
            return resultado_basico, resultado_basico, None, None

        if modo == ModoAnalisis.PRO:
            resultado_pro = self.procesar_pro(
                ruta_archivo,
                callback=callback,
                callback_etapa=callback_etapa,
                callback_alerta=callback_alerta,
                cancelador=cancelador,
                controlador=controlador,
                modo_etiqueta="Pro",
            )
            self._finalizar_modo(resultado_pro, ModoAnalisis.PRO)

            self._emitir_etapa(
                callback_etapa,
                ETAPA_COMPARACION_RESULTADOS,
                ESTADO_OMITIDA,
                "Comparación omitida: solo se ejecutó el modo Pro.",
            )
            self._emitir_etapa(
                callback_etapa,
                ETAPA_FINALIZACION,
                ESTADO_COMPLETADA,
                "Procesamiento en modo Pro completado.",
            )
            self._emitir_progreso(callback, 100, "Procesamiento completado.")
            return resultado_pro, None, resultado_pro, None

        callback_basico = self._crear_callback_rango(callback, 0, 48, "Básico")
        resultado_basico = self.procesar(
            ruta_archivo,
            callback=callback_basico,
            callback_etapa=callback_etapa,
            callback_alerta=callback_alerta,
            cancelador=cancelador,
            controlador=controlador,
            modo_etiqueta="Básico",
        )
        self._finalizar_modo(resultado_basico, ModoAnalisis.BASICO)

        self._controlar(controlador, cancelador)

        paginas_para_pro, mensaje_limitacion = self._resolver_paginas_para_comparacion(resultado_basico)
        if mensaje_limitacion:
            self._emitir_alerta(callback_alerta, mensaje_limitacion)

        callback_pro = self._crear_callback_rango(callback, 48, 90, "Pro")
        resultado_pro = self.procesar_pro(
            ruta_archivo,
            callback=callback_pro,
            callback_etapa=callback_etapa,
            callback_alerta=callback_alerta,
            cancelador=cancelador,
            controlador=controlador,
            modo_etiqueta="Pro",
            paginas_forzadas=paginas_para_pro,
        )
        if mensaje_limitacion:
            resultado_pro.observaciones_modo.append(mensaje_limitacion)

        self._finalizar_modo(resultado_pro, ModoAnalisis.PRO)

        self._controlar(controlador, cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_COMPARACION_RESULTADOS,
            ESTADO_EN_CURSO,
            "Calculando comparación entre modo Básico y modo Pro.",
        )
        self._emitir_progreso(callback, 94, "Comparando resultados...")

        comparacion = self.comparador_resultados.comparar(resultado_basico, resultado_pro)
        resultado_basico.comparacion_modos = comparacion
        resultado_pro.comparacion_modos = comparacion

        detalle_comparacion = comparacion.motivo or "Comparación completada."
        if comparacion.revision_manual_recomendada and comparacion.motivo_revision_manual:
            detalle_comparacion += f" {comparacion.motivo_revision_manual}"
        if comparacion.observaciones:
            detalle_comparacion += f" {' | '.join(comparacion.observaciones)}"

        self._emitir_etapa(
            callback_etapa,
            ETAPA_COMPARACION_RESULTADOS,
            ESTADO_COMPLETADA,
            detalle_comparacion,
        )
        self._emitir_etapa(
            callback_etapa,
            ETAPA_FINALIZACION,
            ESTADO_COMPLETADA,
            "Comparación de modos completada.",
        )
        self._emitir_progreso(callback, 100, "Procesamiento completado.")

        resultado_mostrado = resultado_basico
        if comparacion.modo_ganador == ModoAnalisis.PRO:
            resultado_mostrado = resultado_pro

        return resultado_mostrado, resultado_basico, resultado_pro, comparacion

    def reextraer_campos(self, resultado: ResultadoAnalisisPDF, callback=None) -> ResultadoAnalisisPDF:
        self._emitir_progreso(callback, 70, "Reextrayendo campos desde texto revisado...")
        resultado = self.extractor_poliza.extraer(resultado)
        self._finalizar_metricas_existentes(resultado)
        self._emitir_progreso(callback, 100, "Campos reextraídos correctamente.")
        return resultado

    def _consolidar_y_extraer(
        self,
        resultado: ResultadoAnalisisPDF,
        *,
        callback=None,
        callback_etapa=None,
        cancelador=None,
        controlador=None,
    ) -> None:
        self._controlar(controlador, cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_CONSOLIDACION_TEXTO,
            ESTADO_EN_CURSO,
            "Consolidando texto base para revisión manual.",
        )
        self._preparar_texto_revision(resultado)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_CONSOLIDACION_TEXTO,
            ESTADO_COMPLETADA,
            "Texto consolidado correctamente.",
        )

        self._controlar(controlador, cancelador)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_EXTRACCION_CAMPOS,
            ESTADO_EN_CURSO,
            "Extrayendo campos básicos de póliza.",
        )
        self._emitir_progreso(callback, 85, "Extrayendo campos básicos de póliza...")
        self.extractor_poliza.extraer(resultado)

        campos_detectados = sum(1 for campo in resultado.campos_extraidos if campo.detectado)
        self._emitir_etapa(
            callback_etapa,
            ETAPA_EXTRACCION_CAMPOS,
            ESTADO_COMPLETADA,
            f"Extracción completada. Campos detectados: {campos_detectados}.",
        )

    def _finalizar_modo(self, resultado: ResultadoAnalisisPDF, modo: str) -> None:
        resultado.modo_analisis = modo
        resultado.etiqueta_modo = ModoAnalisis.etiqueta(modo)
        resultado.metricas_paginas_modo = self.comparador_resultados.construir_metricas_paginas(resultado)
        resultado.metricas_documento_modo = self.comparador_resultados.construir_metricas_documento(resultado)

        recomendacion = self.comparador_resultados.recomendar_modo(resultado)
        resultado.recomendacion_modo = recomendacion.mensaje
        resultado.observaciones_modo = self._combinar_observaciones_modo(
            resultado.observaciones_modo,
            resultado.alertas_operativas,
            recomendacion.razones,
            [recomendacion.motivo_revision_manual] if recomendacion.motivo_revision_manual else [],
        )
        resultado.es_provisional = False

    def _finalizar_metricas_existentes(self, resultado: ResultadoAnalisisPDF) -> None:
        resultado.metricas_paginas_modo = self.comparador_resultados.construir_metricas_paginas(resultado)
        resultado.metricas_documento_modo = self.comparador_resultados.construir_metricas_documento(resultado)

    def _resolver_paginas_para_comparacion(self, resultado_basico) -> tuple[list[int], str]:
        total_paginas = resultado_basico.cantidad_paginas

        if (
            total_paginas <= self.limites.max_paginas_comparacion_total
            and not self.limites.comparar_solo_paginas_problematicas
        ):
            return [], ""

        paginas = self.monitor_recursos.seleccionar_paginas_para_comparacion(resultado_basico)
        paginas = paginas[: self.limites.max_paginas_comparacion_total]

        if not paginas:
            return [], ""

        mensaje = (
            f"Se recomienda comparar solo páginas candidatas. "
            f"Modo Pro limitado a {len(paginas)} página(s) prioritarias."
        )

        if not self.limites.comparar_solo_paginas_problematicas and total_paginas > self.limites.max_paginas_comparacion_total:
            mensaje = (
                f"El documento excede el umbral normal. "
                f"La comparación total fue recortada a {len(paginas)} página(s) por seguridad."
            )

        return paginas, mensaje

    def _preparar_texto_revision(self, resultado: ResultadoAnalisisPDF) -> None:
        if resultado.texto_final_revisado.strip():
            return

        texto_base = resultado.texto_completo.strip()
        if not texto_base:
            texto_base = resultado.texto_ocr_completo.strip()

        resultado.texto_final_revisado = texto_base

    def _construir_detalle_ocr(
        self,
        detalle_base: str,
        acciones_preparacion: list[str],
    ) -> str:
        if not acciones_preparacion:
            return detalle_base

        acciones_texto = " | ".join(acciones_preparacion)
        return f"{detalle_base} Preparación sugerida: {acciones_texto}."

    def _combinar_observaciones_modo(self, *grupos: list[str]) -> list[str]:
        salida = []
        for grupo in grupos:
            for valor in grupo:
                valor = (valor or "").strip()
                if valor and valor not in salida:
                    salida.append(valor)
        return salida

    def _controlar(self, controlador, cancelador) -> None:
        if controlador is not None:
            controlador.esperar_si_pausado()
            controlador.verificar_estado()

        if cancelador and cancelador():
            raise ProcesoCanceladoError("Procesamiento cancelado por el usuario.")

    def _emitir_progreso(self, callback, valor: int, mensaje: str) -> None:
        if callback:
            callback(valor, mensaje)

    def _emitir_etapa(self, callback_etapa, etapa_id: str, estado: str, detalle: str) -> None:
        if callback_etapa:
            callback_etapa(etapa_id, estado, detalle)

    def _emitir_alerta(self, callback_alerta, mensaje: str) -> None:
        if callback_alerta:
            callback_alerta(mensaje)

    def _crear_callback_rango(self, callback, inicio: int, fin: int, prefijo: str):
        if callback is None:
            return None

        ancho = max(1, fin - inicio)

        def callback_rango(valor: int, mensaje: str) -> None:
            valor_ajustado = inicio + int((max(0, min(100, valor)) / 100) * ancho)
            callback(valor_ajustado, f"{prefijo}: {mensaje}")

        return callback_rango

    def _limpiar_lista(self, valores: list[str]) -> list[str]:
        salida = []
        for valor in valores:
            valor = (valor or "").strip()
            if valor and valor not in salida:
                salida.append(valor)
        return salida