class ModoAnalisis:
    BASICO = "basico"
    PRO = "pro"
    COMPARAR = "comparar"

    ETIQUETAS = {
        BASICO: "Básico",
        PRO: "Pro",
        COMPARAR: "Comparar ambos",
    }

    ORDEN = [BASICO, PRO, COMPARAR]

    @classmethod
    def etiqueta(cls, modo: str) -> str:
        return cls.ETIQUETAS.get(modo, modo.title())

    @classmethod
    def opciones_combo(cls) -> list[tuple[str, str]]:
        return [(modo, cls.etiqueta(modo)) for modo in cls.ORDEN]