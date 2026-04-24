from __future__ import annotations

import threading

from etapas_proceso import ProcesoCanceladoError


class DetencionSeguridadError(Exception):
    pass


class ControladorCancelacion:
    def __init__(self) -> None:
        self._cancelado = threading.Event()
        self._permiso_pausa = threading.Event()
        self._permiso_pausa.set()

        self._lock = threading.Lock()
        self._pausado = False
        self._motivo = ""
        self._tipo = "usuario"

    def solicitar_cancelacion(self, motivo: str = "Procesamiento cancelado por el usuario.") -> None:
        with self._lock:
            self._motivo = motivo
            self._tipo = "usuario"
            self._cancelado.set()
            self._permiso_pausa.set()
            self._pausado = False

    def detener_por_seguridad(self, motivo: str) -> None:
        with self._lock:
            self._motivo = motivo
            self._tipo = "seguridad"
            self._cancelado.set()
            self._permiso_pausa.set()
            self._pausado = False
        raise DetencionSeguridadError(motivo)

    def pausar(self) -> None:
        with self._lock:
            if self._cancelado.is_set():
                return
            self._pausado = True
            self._permiso_pausa.clear()

    def reanudar(self) -> None:
        with self._lock:
            self._pausado = False
            self._permiso_pausa.set()

    def esta_pausado(self) -> bool:
        with self._lock:
            return self._pausado and not self._cancelado.is_set()

    def fue_detencion_seguridad(self) -> bool:
        with self._lock:
            return self._tipo == "seguridad"

    def motivo_actual(self) -> str:
        with self._lock:
            return self._motivo

    def esperar_si_pausado(self, intervalo: float = 0.15) -> None:
        while self.esta_pausado():
            if self._cancelado.wait(intervalo):
                break
        self.verificar_estado()

    def verificar_estado(self) -> None:
        if not self._cancelado.is_set():
            return

        motivo = self._motivo or "Procesamiento detenido."
        if self._tipo == "seguridad":
            raise DetencionSeguridadError(motivo)
        raise ProcesoCanceladoError(motivo)