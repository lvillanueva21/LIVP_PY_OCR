import json
from pathlib import Path

from modelos import ResultadoAnalisisPDF


class ExportadorResultados:
    def exportar_json(self, resultado: ResultadoAnalisisPDF, ruta_destino: str) -> None:
        if resultado is None:
            raise ValueError("No hay resultados para exportar.")

        ruta = Path(ruta_destino)
        datos = self._construir_diccionario(resultado)

        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=4)

    def exportar_txt(self, resultado: ResultadoAnalisisPDF, ruta_destino: str) -> None:
        if resultado is None:
            raise ValueError("No hay resultados para exportar.")

        ruta = Path(ruta_destino)
        contenido = self._construir_texto_plano(resultado)

        with ruta.open("w", encoding="utf-8") as archivo:
            archivo.write(contenido)

    def _construir_diccionario(self, resultado: ResultadoAnalisisPDF) -> dict:
        return {
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
                }
                for pagina in resultado.resumen_paginas
            ],
            "textos": {
                "texto_digital_completo": resultado.texto_completo,
                "texto_ocr_completo": resultado.texto_ocr_completo,
                "texto_final_revisado": resultado.texto_final_revisado,
            },
        }

    def _construir_texto_plano(self, resultado: ResultadoAnalisisPDF) -> str:
        lineas = []

        lineas.append("RESULTADO DE ANÁLISIS DE PDF")
        lineas.append("=" * 80)
        lineas.append("")

        lineas.append("RESUMEN DEL DOCUMENTO")
        lineas.append("-" * 80)
        lineas.append(f"Ruta del archivo: {resultado.ruta_archivo}")
        lineas.append(f"Nombre del archivo: {resultado.nombre_archivo}")
        lineas.append(f"Cantidad de páginas: {resultado.cantidad_paginas}")
        lineas.append(f"Tiene texto digital: {'Sí' if resultado.tiene_texto_digital else 'No'}")
        lineas.append(f"Necesita OCR: {'Sí' if resultado.necesita_ocr else 'No'}")
        lineas.append("")

        lineas.append("DIAGNÓSTICO")
        lineas.append("-" * 80)
        lineas.append(f"Diagnóstico general: {resultado.diagnostico_general}")
        lineas.append(f"Código diagnóstico: {resultado.codigo_diagnostico_general}")
        lineas.append(f"Detalle: {resultado.detalle_diagnostico}")
        lineas.append(f"Confianza: {resultado.confianza_diagnostico}%")
        lineas.append("")

        lineas.append("ESTADO OCR")
        lineas.append("-" * 80)
        lineas.append(f"Tipo OCR sugerido: {resultado.tipo_ocr_sugerido}")
        lineas.append(f"Estado OCR: {resultado.estado_ocr}")
        lineas.append(f"Código estado OCR: {resultado.codigo_estado_ocr}")
        lineas.append(f"Detalle OCR: {resultado.detalle_ocr}")
        lineas.append(f"Motor OCR: {resultado.motor_ocr}")
        lineas.append(f"Apto para OCR: {'Sí' if resultado.apto_para_ocr else 'No'}")
        lineas.append(f"OCR disponible: {'Sí' if resultado.ocr_disponible else 'No'}")
        lineas.append(
            f"Requiere preprocesamiento: {'Sí' if resultado.requiere_preprocesamiento else 'No'}"
        )
        lineas.append(f"Páginas objetivo OCR: {resultado.paginas_ocr_objetivo}")
        lineas.append(f"Páginas procesadas OCR: {resultado.paginas_ocr_procesadas}")

        if resultado.acciones_preparacion:
            lineas.append("Acciones de preparación:")
            for accion in resultado.acciones_preparacion:
                lineas.append(f"- {accion}")

        if resultado.errores_ocr:
            lineas.append("Errores OCR:")
            for error in resultado.errores_ocr:
                lineas.append(f"- {error}")

        lineas.append("")
        lineas.append("CAMPOS EXTRAÍDOS")
        lineas.append("-" * 80)
        lineas.append(f"Fuente de extracción: {resultado.texto_fuente_extraccion or '-'}")
        for campo in resultado.campos_extraidos:
            lineas.append(f"{campo.etiqueta}: {campo.valor if campo.valor else 'No detectado'}")
            lineas.append(f"  Estado: {'Detectado' if campo.detectado else 'No detectado'}")
            lineas.append(f"  Estrategia: {campo.estrategia}")
        lineas.append("")

        lineas.append("DETALLE POR PÁGINA")
        lineas.append("-" * 80)
        for pagina in resultado.resumen_paginas:
            lineas.append(f"Página {pagina.numero_pagina}")
            lineas.append(f"  Tiene texto digital: {'Sí' if pagina.tiene_texto else 'No'}")
            lineas.append(f"  Cantidad de caracteres: {pagina.cantidad_caracteres}")
            lineas.append(f"  Cantidad de imágenes: {pagina.cantidad_imagenes}")
            lineas.append(f"  Cobertura imagen: {pagina.cobertura_imagen * 100:.0f}%")
            lineas.append(f"  Diagnóstico: {pagina.diagnostico}")
            lineas.append(f"  Código diagnóstico: {pagina.codigo_diagnostico}")
            lineas.append(f"  Confianza: {pagina.confianza}%")
            lineas.append(f"  OCR ejecutado: {'Sí' if pagina.ocr_ejecutado else 'No'}")
            lineas.append(f"  Error OCR: {pagina.ocr_error if pagina.ocr_error else '-'}")
            lineas.append("")

        lineas.append("TEXTO DIGITAL EXTRAÍDO")
        lineas.append("-" * 80)
        lineas.append(resultado.texto_completo if resultado.texto_completo.strip() else "No hay texto digital extraído.")
        lineas.append("")

        lineas.append("TEXTO OCR")
        lineas.append("-" * 80)
        lineas.append(resultado.texto_ocr_completo if resultado.texto_ocr_completo.strip() else "No hay texto OCR extraído.")
        lineas.append("")

        lineas.append("TEXTO FINAL REVISADO")
        lineas.append("-" * 80)
        lineas.append(resultado.texto_final_revisado if resultado.texto_final_revisado.strip() else "No hay texto final revisado.")
        lineas.append("")

        return "\n".join(lineas)