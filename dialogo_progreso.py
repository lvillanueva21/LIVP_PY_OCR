from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from etapas_proceso import (
    ESTADO_ADVERTENCIA,
    ESTADO_COMPLETADA,
    ESTADO_EN_CURSO,
    ESTADO_ERROR,
    ESTADO_OMITIDA,
    ESTADO_PENDIENTE,
    ETAPAS_LINEA_TIEMPO,
    etiqueta_estado,
)


class DialogoProgreso(QDialog):
    solicitud_cancelar = Signal()
    solicitud_pausar = Signal()
    solicitud_reanudar = Signal()

    def __init__(self, modo_etiqueta: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Procesando documento")
        self.setModal(True)
        self.resize(920, 600)

        self._finalizado = False
        self._cancelacion_solicitada = False
        self._pausado = False
        self._ultimo_mensaje = "Preparando procesamiento..."
        self._filas_etapas: dict[str, int] = {}

        self._construir_interfaz()
        self.actualizar_modo(modo_etiqueta)
        self._cargar_etapas()

    def _construir_interfaz(self) -> None:
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(14)

        grupo_resumen = QGroupBox("Estado del procesamiento")
        layout_resumen = QGridLayout(grupo_resumen)
        layout_resumen.setHorizontalSpacing(14)
        layout_resumen.setVerticalSpacing(10)

        etiqueta_modo = QLabel("Modo")
        etiqueta_modo.setObjectName("etiqueta_seccion")
        self.valor_modo = QLabel("-")
        self.valor_modo.setObjectName("valor_principal")

        etiqueta_etapa_actual = QLabel("Etapa actual")
        etiqueta_etapa_actual.setObjectName("etiqueta_seccion")
        self.valor_etapa_actual = QLabel("Esperando inicio...")
        self.valor_etapa_actual.setObjectName("valor_principal")
        self.valor_etapa_actual.setWordWrap(True)

        etiqueta_mensaje = QLabel("Mensaje")
        etiqueta_mensaje.setObjectName("etiqueta_seccion")
        self.valor_mensaje = QLabel("Preparando procesamiento...")
        self.valor_mensaje.setWordWrap(True)

        etiqueta_alerta = QLabel("Alerta operativa")
        etiqueta_alerta.setObjectName("etiqueta_seccion")
        self.valor_alerta_operativa = QLabel("Sin alertas.")
        self.valor_alerta_operativa.setObjectName("diagnostico_secundario")
        self.valor_alerta_operativa.setWordWrap(True)

        layout_resumen.addWidget(etiqueta_modo, 0, 0)
        layout_resumen.addWidget(self.valor_modo, 0, 1)
        layout_resumen.addWidget(etiqueta_etapa_actual, 1, 0)
        layout_resumen.addWidget(self.valor_etapa_actual, 1, 1)
        layout_resumen.addWidget(etiqueta_mensaje, 2, 0)
        layout_resumen.addWidget(self.valor_mensaje, 2, 1)
        layout_resumen.addWidget(etiqueta_alerta, 3, 0)
        layout_resumen.addWidget(self.valor_alerta_operativa, 3, 1)

        self.barra_progreso = QProgressBar()
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.barra_progreso.setTextVisible(True)

        grupo_timeline = QGroupBox("Línea de tiempo")
        layout_timeline = QVBoxLayout(grupo_timeline)

        self.tabla_etapas = QTableWidget(0, 3)
        self.tabla_etapas.setHorizontalHeaderLabels(["Etapa", "Estado", "Detalle"])
        self.tabla_etapas.verticalHeader().setVisible(False)
        self.tabla_etapas.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_etapas.setSelectionMode(QTableWidget.NoSelection)
        self.tabla_etapas.setAlternatingRowColors(True)
        self.tabla_etapas.horizontalHeader().setStretchLastSection(True)
        self.tabla_etapas.setColumnWidth(0, 220)
        self.tabla_etapas.setColumnWidth(1, 120)

        layout_timeline.addWidget(self.tabla_etapas)

        fila_botones = QHBoxLayout()
        fila_botones.addStretch()

        self.boton_pausar = QPushButton("Pausar")
        self.boton_pausar.clicked.connect(self._alternar_pausa)

        self.boton_cancelar = QPushButton("Cancelar")
        self.boton_cancelar.clicked.connect(self._solicitar_cancelacion)

        fila_botones.addWidget(self.boton_pausar)
        fila_botones.addWidget(self.boton_cancelar)

        layout_principal.addWidget(grupo_resumen)
        layout_principal.addWidget(self.barra_progreso)
        layout_principal.addWidget(grupo_timeline, 1)
        layout_principal.addLayout(fila_botones)

    def _cargar_etapas(self) -> None:
        self.tabla_etapas.setRowCount(0)
        self._filas_etapas.clear()

        for fila, etapa in enumerate(ETAPAS_LINEA_TIEMPO):
            self.tabla_etapas.insertRow(fila)
            self._filas_etapas[etapa.id_etapa] = fila

            item_etapa = QTableWidgetItem(etapa.etiqueta)
            item_estado = QTableWidgetItem(etiqueta_estado(ESTADO_PENDIENTE))
            item_detalle = QTableWidgetItem("Pendiente de ejecución.")

            self._aplicar_color_estado(item_estado, ESTADO_PENDIENTE)

            self.tabla_etapas.setItem(fila, 0, item_etapa)
            self.tabla_etapas.setItem(fila, 1, item_estado)
            self.tabla_etapas.setItem(fila, 2, item_detalle)
            self.tabla_etapas.setRowHeight(fila, 42)

    def actualizar_modo(self, modo_etiqueta: str) -> None:
        self.valor_modo.setText(modo_etiqueta)

    def actualizar_progreso(self, valor: int, mensaje: str) -> None:
        self.barra_progreso.setValue(max(0, min(100, valor)))
        self._ultimo_mensaje = mensaje
        if not self._pausado:
            self.valor_mensaje.setText(mensaje)

    def mostrar_alerta_operativa(self, mensaje: str) -> None:
        self.valor_alerta_operativa.setText(mensaje)

    def actualizar_etapa(self, id_etapa: str, estado: str, detalle: str) -> None:
        fila = self._filas_etapas.get(id_etapa)
        if fila is None:
            return

        item_estado = self.tabla_etapas.item(fila, 1)
        item_detalle = self.tabla_etapas.item(fila, 2)

        if item_estado is None or item_detalle is None:
            return

        item_estado.setText(etiqueta_estado(estado))
        self._aplicar_color_estado(item_estado, estado)
        item_detalle.setText(detalle)

        if estado == ESTADO_EN_CURSO:
            item_etapa = self.tabla_etapas.item(fila, 0)
            if item_etapa is not None:
                self.valor_etapa_actual.setText(item_etapa.text())
            self.tabla_etapas.scrollToItem(item_estado)

    def marcar_cancelando(self) -> None:
        if self._cancelacion_solicitada:
            return
        self._cancelacion_solicitada = True
        self.valor_mensaje.setText("Cancelación solicitada. Esperando cierre seguro de la etapa actual...")
        self.boton_cancelar.setEnabled(False)
        self.boton_pausar.setEnabled(False)

    def finalizar(self, aceptado: bool = True) -> None:
        self._finalizado = True
        self.boton_cancelar.setEnabled(False)
        self.boton_pausar.setEnabled(False)

        if aceptado:
            self.accept()
        else:
            self.reject()

    def _alternar_pausa(self) -> None:
        if self._finalizado or self._cancelacion_solicitada:
            return

        if self._pausado:
            self._pausado = False
            self.boton_pausar.setText("Pausar")
            self.valor_mensaje.setText(self._ultimo_mensaje)
            self.solicitud_reanudar.emit()
            return

        self._pausado = True
        self.boton_pausar.setText("Reanudar")
        self.valor_mensaje.setText("Procesamiento en pausa. Puedes reanudar o cancelar.")
        self.solicitud_pausar.emit()

    def _solicitar_cancelacion(self) -> None:
        if self._cancelacion_solicitada:
            return
        self.marcar_cancelando()
        self.solicitud_cancelar.emit()

    def closeEvent(self, event) -> None:
        if self._finalizado:
            super().closeEvent(event)
            return

        self._solicitar_cancelacion()
        event.ignore()

    def _aplicar_color_estado(self, item: QTableWidgetItem, estado: str) -> None:
        color = QColor("#486581")

        if estado == ESTADO_COMPLETADA:
            color = QColor("#127a5b")
        elif estado == ESTADO_EN_CURSO:
            color = QColor("#1f5f8b")
        elif estado == ESTADO_OMITIDA:
            color = QColor("#7b8794")
        elif estado == ESTADO_ADVERTENCIA:
            color = QColor("#b7791f")
        elif estado == ESTADO_ERROR:
            color = QColor("#c53030")

        item.setForeground(QBrush(color))