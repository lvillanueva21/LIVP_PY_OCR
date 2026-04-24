class DificultadPagina:
    def clasificar(
        self,
        analisis_imagen: dict,
        analisis_ocr: dict,
        *,
        numero_intentos: int,
    ) -> dict:
        puntos = 0

        if analisis_ocr.get("caracteres_totales", 0) == 0:
            puntos += 5
        elif analisis_ocr.get("cantidad_palabras", 0) < 8:
            puntos += 2

        confianza_promedio = analisis_ocr.get("confianza_promedio", 0.0)
        if confianza_promedio < 40:
            puntos += 4
        elif confianza_promedio < 60:
            puntos += 2

        palabras_baja_confianza = analisis_ocr.get("palabras_baja_confianza", 0)
        if palabras_baja_confianza >= 12:
            puntos += 3
        elif palabras_baja_confianza >= 5:
            puntos += 1

        ruido_textual = analisis_ocr.get("ruido_textual", 0.0)
        if ruido_textual >= 0.22:
            puntos += 3
        elif ruido_textual >= 0.12:
            puntos += 1

        if analisis_imagen.get("es_oscura"):
            puntos += 1
        if analisis_imagen.get("es_muy_clara"):
            puntos += 1
        if analisis_imagen.get("bajo_contraste"):
            puntos += 1
        if analisis_imagen.get("probable_borroso"):
            puntos += 1
        if analisis_imagen.get("sospecha_orientacion"):
            puntos += 1

        if numero_intentos >= 4:
            puntos += 2
        elif numero_intentos >= 2:
            puntos += 1

        tiempo_total_ms = analisis_ocr.get("tiempo_total_ms", 0)
        if tiempo_total_ms > 4000:
            puntos += 1

        if puntos <= 2:
            return {
                "dificultad": "fácil",
                "nivel": 1,
                "indice": min(100, puntos * 12),
                "requiere_revision": False,
            }

        if puntos <= 5:
            return {
                "dificultad": "media",
                "nivel": 2,
                "indice": min(100, puntos * 12),
                "requiere_revision": False,
            }

        if puntos <= 8:
            return {
                "dificultad": "difícil",
                "nivel": 3,
                "indice": min(100, puntos * 12),
                "requiere_revision": True,
            }

        return {
            "dificultad": "crítica",
            "nivel": 4,
            "indice": min(100, puntos * 12),
            "requiere_revision": True,
        }