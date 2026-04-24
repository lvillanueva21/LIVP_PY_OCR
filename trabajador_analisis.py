from PySide6.QtCore import QObject, Signal, Slot

from controlador_cancelacion import ControladorCancelacion, DetencionSeguridadError
from limites_proceso import LimitesProceso
from monitor_recursos import MonitorRecursos
from pipeline_documento import PipelineDocumento
from etapas_proceso import ProcesoCanceladoError


class TrabajadorAnalisis(QObject):
    progreso = Signal(int, str)
    etapa = Signal(str, str, str)
    alerta = Signal(str)
    finalizado = Signal(object, object, object, object)
    error = Signal(str)
    cancelado = Signal(str)
    detenido_seguridad = Signal(str)

    def __init__(self, ruta_archivo: str, modo: str, limites: LimitesProceso | None = None) -> None:
        super().__init__()
        self.ruta_archivo = ruta_archivo
        self.modo = modo
        self.limites = limites or LimitesProceso()
        self.controlador = ControladorCancelacion()
        self.monitor = MonitorRecursos(self.limites)

    @Slot()
    def ejecutar(self) -> None:
        pipeline = PipelineDocumento(
            limites_proceso=self.limites,
            monitor_recursos=self.monitor,
        )

        try:
            resultado_mostrado, resultado_basico, resultado_pro, comparacion = pipeline.procesar_segun_modo(
                self.ruta_archivo,
                self.modo,
                callback=self._emitir_progreso,
                callback_etapa=self._emitir_etapa,
                callback_alerta=self._emitir_alerta,
                controlador=self.controlador,
            )

            for mensaje in self.monitor.analizar_resultado_operativo(resultado_mostrado):
                self._emitir_alerta(mensaje)

            self.finalizado.emit(resultado_mostrado, resultado_basico, resultado_pro, comparacion)

        except DetencionSeguridadError as error:
            self.detenido_seguridad.emit(str(error) or "El análisis fue detenido por seguridad.")
        except ProcesoCanceladoError as error:
            self.cancelado.emit(str(error) or "Procesamiento cancelado por el usuario.")
        except Exception as error:
            self.error.emit(str(error))

    @Slot()
    def cancelar(self) -> None:
        self.controlador.solicitar_cancelacion(
            "Procesamiento cancelado por el usuario."
        )
        self.progreso.emit(0, "Cancelación solicitada. Esperando cierre seguro...")

    @Slot()
    def pausar(self) -> None:
        self.controlador.pausar()
        self.progreso.emit(self.progreso_value_aproximado(), "Procesamiento en pausa...")

    @Slot()
    def reanudar(self) -> None:
        self.controlador.reanudar()
        self.progreso.emit(self.progreso_value_aproximado(), "Procesamiento reanudado.")

    def progreso_value_aproximado(self) -> int:
        return 0

    def _emitir_progreso(self, valor: int, mensaje: str) -> None:
        self.progreso.emit(valor, mensaje)

    def _emitir_etapa(self, etapa_id: str, estado: str, detalle: str) -> None:
        self.etapa.emit(etapa_id, estado, detalle)

    def _emitir_alerta(self, mensaje: str) -> None:
        self.alerta.emit(mensaje)