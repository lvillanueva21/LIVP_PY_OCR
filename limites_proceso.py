from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class LimitesProceso:
    max_reintentos_por_pagina: int = 4
    max_tiempo_pagina_segundos: int = 12
    max_paginas_comparacion_total: int = 20
    comparar_solo_paginas_problematicas: bool = True

    umbral_archivo_pesado_mb: int = 20
    umbral_paginas_pesado: int = 60
    umbral_consumo_estimado_mb: int = 512

    detener_por_seguridad: bool = True

    @property
    def max_tiempo_pagina_ms(self) -> int:
        return self.max_tiempo_pagina_segundos * 1000

    def to_dict(self) -> dict:
        return asdict(self)

    def resumen_textual(self) -> str:
        return (
            f"Reintentos máx: {self.max_reintentos_por_pagina} | "
            f"Tiempo/página: {self.max_tiempo_pagina_segundos}s | "
            f"Páginas comp.: {self.max_paginas_comparacion_total} | "
            f"Solo problemáticas: {'Sí' if self.comparar_solo_paginas_problematicas else 'No'}"
        )