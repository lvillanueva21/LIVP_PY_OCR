class ObservacionesPagina:
    def construir(
        self,
        analisis_imagen: dict,
        analisis_ocr: dict,
        *,
        numero_intentos: int,
        dificultad: str,
        requiere_revision: bool,
    ) -> list[str]:
        observaciones = list(analisis_imagen.get("observaciones", []))

        if analisis_imagen.get("es_oscura"):
            observaciones.append("Baja iluminación.")
        if analisis_imagen.get("es_muy_clara"):
            observaciones.append("Exceso de luz o sobreexposición.")
        if analisis_imagen.get("bajo_contraste"):
            observaciones.append("Contraste pobre.")
        if analisis_imagen.get("probable_borroso"):
            observaciones.append("Posible desenfoque.")
        if analisis_imagen.get("sospecha_orientacion"):
            observaciones.append("Imagen posiblemente torcida o mal orientada.")

        if analisis_ocr.get("caracteres_totales", 0) == 0:
            observaciones.append("OCR vacío.")
        if analisis_ocr.get("confianza_promedio", 0.0) < 45 and analisis_ocr.get("cantidad_palabras", 0) > 0:
            observaciones.append("Confianza OCR baja.")
        if analisis_ocr.get("palabras_baja_confianza", 0) >= 8:
            observaciones.append("Muchas palabras con baja confianza.")
        if analisis_ocr.get("ruido_textual", 0.0) >= 0.18:
            observaciones.append("Demasiados símbolos raros o ruido textual.")
        if numero_intentos >= 2:
            observaciones.append("Se necesitaron reintentos.")
        if analisis_ocr.get("tiempo_total_ms", 0) > 3500:
            observaciones.append("Página costosa de procesar.")

        observaciones.append(f"Dificultad estimada: {dificultad}.")

        if requiere_revision:
            observaciones.append("Revisión manual recomendada.")

        salida = []
        for observacion in observaciones:
            observacion = (observacion or "").strip()
            if observacion and observacion not in salida:
                salida.append(observacion)
        return salida