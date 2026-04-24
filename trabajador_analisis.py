from PySide6.QtCore import QObject, Signal, Slot

from etapas_proceso import (
    ESTADO_ADVERTENCIA,
    ETAPA_FINALIZACION,
    ProcesoCanceladoError,
)
from pipeline_documento import PipelineDocumento


class TrabajadorAnalisis(QObject):
    progreso = Signal(int, str)
    etapa = Signal(str, str, str)
    finalizado = Signal(object, object, object, object)
    error = Signal(str)
    cancelado = Signal(str)

    def __init__(self, ruta_archivo: str, modo: str) -> None:
        super().__init__()
        self.ruta_archivo = ruta_archivo
        self.modo = modo
        self._cancelado = False

    @Slot()
    def ejecutar(self) -> None:
        pipeline = PipelineDocumento()

        try:
            resultado_mostrado, resultado_basico, resultado_pro, comparacion = pipeline.procesar_segun_modo(
                self.ruta_archivo,
                self.modo,
                callback=self._emitir_progreso,
                callback_etapa=self._emitir_etapa,
                cancelador=self._esta_cancelado,
            )
            self.finalizado.emit(resultado_mostrado, resultado_basico, resultado_pro, comparacion)

        except ProcesoCanceladoError as error:
            self._emitir_etapa(
                ETAPA_FINALIZACION,
                ESTADO_ADVERTENCIA,
                str(error) or "Procesamiento cancelado por el usuario.",
            )
            self.cancelado.emit(str(error) or "Procesamiento cancelado por el usuario.")

        except Exception as error:
            self.error.emit(str(error))

    @Slot()
    def cancelar(self) -> None:
        self._cancelado = True
        self.progreso.emit(0, "Cancelación solicitada. Esperando cierre seguro...")

    def _esta_cancelado(self) -> bool:
        return self._cancelado

    def _emitir_progreso(self, valor: int, mensaje: str) -> None:
        self.progreso.emit(valor, mensaje)

    def _emitir_etapa(self, etapa_id: str, estado: str, detalle: str) -> None:
        self.etapa.emit(etapa_id, estado, detalle)