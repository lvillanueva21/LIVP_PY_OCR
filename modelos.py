from dataclasses import dataclass, field
from typing import List


@dataclass
class ResultadoPagina:
    numero_pagina: int
    tiene_texto: bool
    cantidad_caracteres: int
    texto_extraido: str = ""


@dataclass
class ResultadoAnalisisPDF:
    ruta_archivo: str
    nombre_archivo: str
    cantidad_paginas: int
    tiene_texto_digital: bool
    necesita_ocr: bool
    texto_completo: str = ""
    resumen_paginas: List[ResultadoPagina] = field(default_factory=list)