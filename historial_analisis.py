from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class HistorialAnalisis:
    def __init__(self, ruta_historial: str | None = None) -> None:
        base_dir = Path(__file__).resolve().parent
        self.ruta_historial = Path(ruta_historial) if ruta_historial else base_dir / "historial_analisis.jsonl"

    def existe_historial(self) -> bool:
        return self.ruta_historial.exists() and self.ruta_historial.stat().st_size > 0

    def leer_registros(self) -> list[dict]:
        if not self.ruta_historial.exists():
            return []

        registros = []
        with self.ruta_historial.open("r", encoding="utf-8") as archivo:
            for linea in archivo:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    registros.append(json.loads(linea))
                except Exception:
                    continue

        return registros

    def guardar_registro(
        self,
        resultado,
        *,
        resultado_basico=None,
        resultado_pro=None,
        comparacion=None,
    ) -> dict:
        registro = self._construir_registro(
            resultado,
            resultado_basico=resultado_basico,
            resultado_pro=resultado_pro,
            comparacion=comparacion,
        )

        self.ruta_historial.parent.mkdir(parents=True, exist_ok=True)
        with self.ruta_historial.open("a", encoding="utf-8") as archivo:
            archivo.write(json.dumps(registro, ensure_ascii=False) + "\n")

        return registro

    def _construir_registro(
        self,
        resultado,
        *,
        resultado_basico=None,
        resultado_pro=None,
        comparacion=None,
    ) -> dict:
        ruta_archivo = Path(resultado.ruta_archivo)
        tamano_archivo_bytes = ruta_archivo.stat().st_size if ruta_archivo.exists() else 0

        score_basico = None
        if resultado_basico is not None and resultado_basico.metricas_documento_modo is not None:
            score_basico = resultado_basico.metricas_documento_modo.score_total

        score_pro = None
        if resultado_pro is not None and resultado_pro.metricas_documento_modo is not None:
            score_pro = resultado_pro.metricas_documento_modo.score_total

        ganador = comparacion.etiqueta_ganador if comparacion is not None else resultado.etiqueta_modo
        revision_manual = comparacion.revision_manual_recomendada if comparacion is not None else False

        observaciones = []
        if resultado.observaciones_modo:
            observaciones.extend(resultado.observaciones_modo)
        if comparacion is not None:
            if comparacion.motivo:
                observaciones.append(comparacion.motivo)
            if comparacion.motivo_revision_manual:
                observaciones.append(comparacion.motivo_revision_manual)
            observaciones.extend(comparacion.observaciones)

        paginas = []
        for pagina in resultado.resumen_paginas:
            paginas.append(
                {
                    "numero_pagina": pagina.numero_pagina,
                    "dificultad": pagina.ocr_dificultad or "-",
                    "indice_dificultad": pagina.ocr_dificultad_indice,
                    "requiere_revision": pagina.ocr_requiere_revision,
                    "confianza_promedio": pagina.ocr_confianza_promedio,
                    "confianza_mediana": pagina.ocr_confianza_mediana,
                    "palabras": pagina.ocr_cantidad_palabras,
                    "palabras_baja_confianza": pagina.ocr_palabras_baja_confianza,
                    "tiempo_total_ms": pagina.ocr_tiempo_total_ms,
                    "intentos": pagina.ocr_numero_intentos,
                    "variante": pagina.ocr_variante_ganadora or "-",
                    "observaciones": list(pagina.ocr_observaciones),
                }
            )

        comparaciones_paginas = []
        if comparacion is not None:
            for item in comparacion.comparaciones_paginas:
                comparaciones_paginas.append(
                    {
                        "numero_pagina": item.numero_pagina,
                        "score_basico": item.score_basico,
                        "score_pro": item.score_pro,
                        "ganador": item.etiqueta_ganador,
                        "revision_manual_recomendada": item.revision_manual_recomendada,
                        "dificultad_basico": item.dificultad_basico,
                        "dificultad_pro": item.dificultad_pro,
                        "observaciones": list(item.observaciones),
                    }
                )

        return {
            "fecha_hora": datetime.now().isoformat(timespec="seconds"),
            "archivo_analizado": resultado.nombre_archivo,
            "ruta_archivo": resultado.ruta_archivo,
            "tamano_archivo_bytes": tamano_archivo_bytes,
            "cantidad_paginas": resultado.cantidad_paginas,
            "modo_usado": resultado.etiqueta_modo,
            "score_basico": score_basico,
            "score_pro": score_pro,
            "ganador": ganador,
            "campos_detectados": sum(1 for campo in resultado.campos_extraidos if campo.detectado),
            "tiempo_total_ms": resultado.tiempo_total_ms,
            "observaciones": self._limpiar_lista(observaciones),
            "revision_manual_recomendada": revision_manual,
            "paginas": paginas,
            "comparaciones_paginas": comparaciones_paginas,
        }

    def _limpiar_lista(self, valores: list[str]) -> list[str]:
        salida = []
        for valor in valores:
            valor = (valor or "").strip()
            if valor and valor not in salida:
                salida.append(valor)
        return salida