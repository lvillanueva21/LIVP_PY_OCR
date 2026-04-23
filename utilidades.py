from pathlib import Path


def obtener_nombre_archivo(ruta_archivo: str) -> str:
    return Path(ruta_archivo).name


def es_pdf_valido(ruta_archivo: str) -> bool:
    ruta = Path(ruta_archivo)
    return ruta.exists() and ruta.is_file() and ruta.suffix.lower() == ".pdf"


def guardar_texto_en_archivo(ruta_archivo: str, contenido: str) -> None:
    ruta = Path(ruta_archivo)
    ruta.write_text(contenido, encoding="utf-8")