import cv2
import numpy as np

from analizador_calidad_ocr import AnalizadorCalidadOCR
from dificultad_pagina import DificultadPagina
from observaciones_pagina import ObservacionesPagina


class EvaluadorPagina:
    def __init__(
        self,
        analizador_calidad: AnalizadorCalidadOCR | None = None,
        clasificador_dificultad: DificultadPagina | None = None,
        generador_observaciones: ObservacionesPagina | None = None,
    ) -> None:
        self.analizador_calidad = analizador_calidad or AnalizadorCalidadOCR()
        self.clasificador_dificultad = clasificador_dificultad or DificultadPagina()
        self.generador_observaciones = generador_observaciones or ObservacionesPagina()

    def analizar_condicion_pagina(self, pagina_resultado, imagen_pil) -> dict:
        gris = np.array(imagen_pil.convert("L"))
        brillo_promedio = float(np.mean(gris))
        contraste = float(np.std(gris))
        varianza_laplaciana = float(cv2.Laplacian(gris, cv2.CV_64F).var())

        es_oscura = brillo_promedio < 85
        es_muy_clara = brillo_promedio > 220
        bajo_contraste = contraste < 35
        probable_borroso = varianza_laplaciana < 70
        sospecha_orientacion = imagen_pil.width > imagen_pil.height * 1.35

        observaciones = []
        if es_oscura:
            observaciones.append("Imagen oscura.")
        if es_muy_clara:
            observaciones.append("Imagen muy clara.")
        if bajo_contraste:
            observaciones.append("Bajo contraste.")
        if probable_borroso:
            observaciones.append("Posible desenfoque o baja nitidez.")
        if sospecha_orientacion:
            observaciones.append("Posible orientación incorrecta.")

        es_problematica = (
            not pagina_resultado.tiene_texto
            or pagina_resultado.cantidad_caracteres < 40
            or pagina_resultado.cobertura_imagen >= 0.70
            or es_oscura
            or es_muy_clara
            or bajo_contraste
            or probable_borroso
        )

        es_muy_problematica = (
            pagina_resultado.cantidad_caracteres == 0
            and pagina_resultado.cobertura_imagen >= 0.85
        ) or (sum([es_oscura, es_muy_clara, bajo_contraste, probable_borroso]) >= 2)

        return {
            "es_problematica": es_problematica,
            "es_muy_problematica": es_muy_problematica,
            "sospecha_orientacion": sospecha_orientacion,
            "brillo_promedio": round(brillo_promedio, 2),
            "contraste": round(contraste, 2),
            "nitidez": round(varianza_laplaciana, 2),
            "es_oscura": es_oscura,
            "es_muy_clara": es_muy_clara,
            "bajo_contraste": bajo_contraste,
            "probable_borroso": probable_borroso,
            "observaciones": observaciones,
        }

    def evaluar_intento(
        self,
        texto: str,
        datos_ocr: dict,
        *,
        tiempo_total_ms: int,
        tiempo_ocr_ms: int,
        analisis_imagen: dict,
        numero_intentos: int,
    ) -> dict:
        analisis_ocr = self.analizador_calidad.analizar(
            texto,
            datos_ocr,
            tiempo_total_ms=tiempo_total_ms,
            tiempo_ocr_ms=tiempo_ocr_ms,
        )

        dificultad = self.clasificador_dificultad.clasificar(
            analisis_imagen,
            analisis_ocr,
            numero_intentos=numero_intentos,
        )

        observaciones = self.generador_observaciones.construir(
            analisis_imagen,
            analisis_ocr,
            numero_intentos=numero_intentos,
            dificultad=dificultad["dificultad"],
            requiere_revision=dificultad["requiere_revision"],
        )

        return {
            "texto": analisis_ocr["texto"],
            "caracteres_totales": analisis_ocr["caracteres_totales"],
            "caracteres_utiles": analisis_ocr["caracteres_utiles"],
            "cantidad_palabras": analisis_ocr["cantidad_palabras"],
            "confianza_promedio": analisis_ocr["confianza_promedio"],
            "confianza_mediana": analisis_ocr["confianza_mediana"],
            "palabras_baja_confianza": analisis_ocr["palabras_baja_confianza"],
            "ruido_textual": analisis_ocr["ruido_textual"],
            "score": analisis_ocr["score_calidad"],
            "tiempo_total_ms": analisis_ocr["tiempo_total_ms"],
            "tiempo_ocr_ms": analisis_ocr["tiempo_ocr_ms"],
            "dificultad": dificultad["dificultad"],
            "dificultad_nivel": dificultad["nivel"],
            "dificultad_indice": dificultad["indice"],
            "requiere_revision": dificultad["requiere_revision"],
            "observaciones": observaciones,
        }