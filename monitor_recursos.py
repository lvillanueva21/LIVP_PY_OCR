from __future__ import annotations

from pathlib import Path

from limites_proceso import LimitesProceso
from modos_analisis import ModoAnalisis


class MonitorRecursos:
    def __init__(self, limites: LimitesProceso | None = None) -> None:
        self.limites = limites or LimitesProceso()

    def evaluar_archivo_previo(self, ruta_archivo: str, modo: str) -> dict:
        ruta = Path(ruta_archivo)
        tamano_bytes = ruta.stat().st_size if ruta.exists() else 0
        tamano_mb = round(tamano_bytes / (1024 * 1024), 2)

        alertas = []
        recomendaciones = []

        if tamano_mb >= self.limites.umbral_archivo_pesado_mb:
            alertas.append(
                f"El documento excede el umbral normal de tamaño ({tamano_mb} MB)."
            )

        es_modo_comparacion = modo not in {ModoAnalisis.BASICO, ModoAnalisis.PRO}
        if es_modo_comparacion and tamano_mb >= self.limites.umbral_archivo_pesado_mb:
            recomendaciones.append(
                "Se recomienda comparar solo páginas candidatas o usar modo rápido."
            )

        return {
            "tamano_bytes": tamano_bytes,
            "tamano_mb": tamano_mb,
            "alertas": alertas,
            "recomendaciones": recomendaciones,
        }

    def evaluar_documento(self, resultado, modo: str) -> dict:
        ruta = Path(resultado.ruta_archivo)
        tamano_bytes = ruta.stat().st_size if ruta.exists() else 0
        tamano_mb = round(tamano_bytes / (1024 * 1024), 2)
        paginas = resultado.cantidad_paginas

        estimacion_consumo_mb = self.estimar_consumo_mb(tamano_mb, paginas, modo)

        alertas = []
        recomendaciones = []
        escenario_pesado = False
        detener_por_seguridad = False
        motivo_detencion = ""

        if tamano_mb >= self.limites.umbral_archivo_pesado_mb:
            escenario_pesado = True
            alertas.append(
                f"El documento excede umbral normal de tamaño ({tamano_mb} MB)."
            )

        if paginas >= self.limites.umbral_paginas_pesado:
            escenario_pesado = True
            alertas.append(
                f"El documento tiene muchas páginas ({paginas})."
            )

        if estimacion_consumo_mb >= self.limites.umbral_consumo_estimado_mb:
            escenario_pesado = True
            alertas.append(
                f"Consumo estimado alto ({estimacion_consumo_mb} MB)."
            )

        es_modo_comparacion = modo not in {ModoAnalisis.BASICO, ModoAnalisis.PRO}

        if escenario_pesado:
            recomendaciones.append("Se recomienda modo rápido para este documento.")
            if es_modo_comparacion:
                recomendaciones.append(
                    "Se recomienda comparar solo páginas candidatas."
                )

        if (
            self.limites.detener_por_seguridad
            and (
                tamano_mb >= self.limites.umbral_archivo_pesado_mb * 4
                or paginas >= self.limites.umbral_paginas_pesado * 3
                or estimacion_consumo_mb >= self.limites.umbral_consumo_estimado_mb * 1.8
            )
        ):
            detener_por_seguridad = True
            motivo_detencion = (
                "El análisis fue detenido por seguridad: el documento excede umbrales críticos de tamaño, "
                "páginas o consumo estimado."
            )

        return {
            "tamano_bytes": tamano_bytes,
            "tamano_mb": tamano_mb,
            "paginas": paginas,
            "estimacion_consumo_mb": round(estimacion_consumo_mb, 2),
            "escenario_pesado": escenario_pesado,
            "alertas": alertas,
            "recomendaciones": recomendaciones,
            "detener_por_seguridad": detener_por_seguridad,
            "motivo_detencion": motivo_detencion,
        }

    def seleccionar_paginas_para_comparacion(self, resultado_basico) -> list[int]:
        prioridades: list[tuple[int, int]] = []
        metricas_map = {
            metrica.numero_pagina: metrica
            for metrica in (resultado_basico.metricas_paginas_modo or [])
        }

        for indice, pagina in enumerate(resultado_basico.resumen_paginas):
            prioridad = 0
            metrica = metricas_map.get(pagina.numero_pagina)

            if pagina.codigo_diagnostico == "ocr_recomendado":
                prioridad += 6
            elif pagina.codigo_diagnostico == "mixta":
                prioridad += 4

            if pagina.ocr_requiere_revision:
                prioridad += 5

            if pagina.ocr_dificultad == "crítica":
                prioridad += 5
            elif pagina.ocr_dificultad == "difícil":
                prioridad += 3

            if metrica is not None and metrica.score_total < 60:
                prioridad += 4

            if not pagina.tiene_texto or pagina.cantidad_caracteres < 40:
                prioridad += 2

            if pagina.cobertura_imagen >= 0.65:
                prioridad += 1

            if prioridad > 0:
                prioridades.append((prioridad, indice))

        prioridades.sort(key=lambda item: (-item[0], item[1]))

        limite = min(
            self.limites.max_paginas_comparacion_total,
            max(1, len(resultado_basico.resumen_paginas)),
        )

        seleccionadas = [indice for _, indice in prioridades[:limite]]

        if not seleccionadas:
            seleccionadas = list(range(min(limite, len(resultado_basico.resumen_paginas))))

        return seleccionadas

    def analizar_resultado_operativo(self, resultado) -> list[str]:
        alertas = []

        paginas_lentas = [
            pagina.numero_pagina
            for pagina in resultado.resumen_paginas
            if pagina.ocr_tiempo_total_ms > self.limites.max_tiempo_pagina_ms
        ]
        if paginas_lentas:
            alertas.append(
                f"Se detectaron páginas con tiempo anormal: {', '.join(map(str, paginas_lentas[:8]))}."
            )

        paginas_muchos_intentos = [
            pagina.numero_pagina
            for pagina in resultado.resumen_paginas
            if pagina.ocr_numero_intentos > self.limites.max_reintentos_por_pagina
        ]
        if paginas_muchos_intentos:
            alertas.append(
                f"Se detectaron páginas con demasiados reintentos: {', '.join(map(str, paginas_muchos_intentos[:8]))}."
            )

        paginas_revision = [
            pagina.numero_pagina
            for pagina in resultado.resumen_paginas
            if pagina.ocr_requiere_revision
        ]
        if paginas_revision:
            alertas.append(
                f"Hay páginas que requieren revisión manual: {', '.join(map(str, paginas_revision[:8]))}."
            )

        salida = []
        for alerta in alertas:
            alerta = (alerta or "").strip()
            if alerta and alerta not in salida:
                salida.append(alerta)

        return salida

    def estimar_consumo_mb(self, tamano_mb: float, paginas: int, modo: str) -> float:
        base = max(tamano_mb * 2.0, paginas * 4.5)

        if modo == ModoAnalisis.BASICO:
            factor = 1.0
        elif modo == ModoAnalisis.PRO:
            factor = 1.65
        else:
            factor = 2.25
            if self.limites.comparar_solo_paginas_problematicas:
                factor = 1.75

        return base * factor