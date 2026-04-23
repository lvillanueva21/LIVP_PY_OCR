from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from analizador_pdf import AnalizadorPDF


class VentanaPrincipal(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.analizador = AnalizadorPDF()
        self.setWindowTitle("Analizador de PDFs")
        self.resize(1100, 720)
        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        contenedor = QWidget()
        self.setCentralWidget(contenedor)

        layout_principal = QVBoxLayout(contenedor)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(14)

        self._crear_encabezado(layout_principal)
        self._crear_panel_seleccion(layout_principal)
        self._crear_panel_resumen(layout_principal)
        self._crear_panel_paginas(layout_principal)
        self._crear_panel_notificacion(layout_principal)

        barra_estado = QStatusBar()
        barra_estado.showMessage("Aplicación lista.")
        self.setStatusBar(barra_estado)

    def _crear_encabezado(self, layout_padre: QVBoxLayout) -> None:
        titulo = QLabel("Analizador inicial de PDF")
        titulo.setObjectName("titulo_principal")

        subtitulo = QLabel("Carga un PDF y revisa si contiene texto digital o si probablemente requiere OCR.")
        subtitulo.setObjectName("subtitulo")
        subtitulo.setWordWrap(True)

        layout_padre.addWidget(titulo)
        layout_padre.addWidget(subtitulo)

    def _crear_panel_seleccion(self, layout_padre: QVBoxLayout) -> None:
        grupo = QGroupBox("Archivo PDF")
        layout = QHBoxLayout(grupo)
        layout.setSpacing(10)

        self.input_ruta = QLineEdit()
        self.input_ruta.setPlaceholderText("Selecciona un archivo PDF...")
        self.input_ruta.setReadOnly(True)

        self.boton_seleccionar = QPushButton("Seleccionar PDF")
        self.boton_seleccionar.clicked.connect(self.seleccionar_pdf)

        layout.addWidget(self.input_ruta, 1)
        layout.addWidget(self.boton_seleccionar)

        layout_padre.addWidget(grupo)

    def _crear_panel_resumen(self, layout_padre: QVBoxLayout) -> None:
        grupo = QGroupBox("Resumen del documento")
        layout = QGridLayout(grupo)
        layout.setHorizontalSpacing(16)
        layout.setVerticalSpacing(10)

        etiqueta_nombre = QLabel("Nombre del archivo:")
        etiqueta_paginas = QLabel("Cantidad de páginas:")
        etiqueta_texto = QLabel("¿Tiene texto digital?:")
        etiqueta_ocr = QLabel("¿Probablemente necesita OCR?:")

        self.valor_nombre = QLabel("-")
        self.valor_paginas = QLabel("-")
        self.valor_texto = QLabel("-")
        self.valor_ocr = QLabel("-")

        layout.addWidget(etiqueta_nombre, 0, 0)
        layout.addWidget(self.valor_nombre, 0, 1)

        layout.addWidget(etiqueta_paginas, 1, 0)
        layout.addWidget(self.valor_paginas, 1, 1)

        layout.addWidget(etiqueta_texto, 2, 0)
        layout.addWidget(self.valor_texto, 2, 1)

        layout.addWidget(etiqueta_ocr, 3, 0)
        layout.addWidget(self.valor_ocr, 3, 1)

        layout_padre.addWidget(grupo)

    def _crear_panel_paginas(self, layout_padre: QVBoxLayout) -> None:
        grupo = QGroupBox("Detalle por página")
        layout = QVBoxLayout(grupo)

        self.tabla_paginas = QTableWidget(0, 3)
        self.tabla_paginas.setHorizontalHeaderLabels(["Página", "Estado", "Caracteres detectados"])
        self.tabla_paginas.verticalHeader().setVisible(False)
        self.tabla_paginas.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_paginas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_paginas.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_paginas.horizontalHeader().setStretchLastSection(True)
        self.tabla_paginas.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout.addWidget(self.tabla_paginas)
        layout_padre.addWidget(grupo, 1)

    def _crear_panel_notificacion(self, layout_padre: QVBoxLayout) -> None:
        panel = QFrame()
        panel.setObjectName("panel_notificacion")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 10, 12, 10)

        titulo = QLabel("Notificación")
        titulo.setStyleSheet("font-weight: 700; color: #243b53;")

        self.label_notificacion = QLabel("Aún no se ha analizado ningún archivo.")
        self.label_notificacion.setWordWrap(True)

        layout.addWidget(titulo)
        layout.addWidget(self.label_notificacion)

        layout_padre.addWidget(panel)

    def seleccionar_pdf(self) -> None:
        ruta_archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo PDF",
            "",
            "Archivos PDF (*.pdf)",
        )

        if not ruta_archivo:
            self._mostrar_notificacion("No se seleccionó ningún archivo.", "alerta")
            self.statusBar().showMessage("Selección cancelada.")
            return

        self.input_ruta.setText(ruta_archivo)
        self.statusBar().showMessage("Analizando PDF...")
        self._mostrar_notificacion("Procesando documento seleccionado...", "alerta")

        try:
            resultado = self.analizador.analizar(ruta_archivo)
            self._mostrar_resultado(resultado)
            self.statusBar().showMessage("Análisis completado correctamente.")
            self._mostrar_notificacion("El documento fue analizado correctamente.", "ok")
        except FileNotFoundError as error:
            self._limpiar_resultados()
            self.statusBar().showMessage("No se pudo localizar el archivo.")
            self._mostrar_notificacion(str(error), "error")
            QMessageBox.warning(self, "Archivo no válido", str(error))
        except ValueError as error:
            self._limpiar_resultados()
            self.statusBar().showMessage("El PDF no pudo analizarse.")
            self._mostrar_notificacion(str(error), "error")
            QMessageBox.critical(self, "Error al analizar PDF", str(error))
        except Exception as error:
            self._limpiar_resultados()
            mensaje = f"Ocurrió un error inesperado: {error}"
            self.statusBar().showMessage("Error inesperado durante el análisis.")
            self._mostrar_notificacion(mensaje, "error")
            QMessageBox.critical(self, "Error inesperado", mensaje)

    def _mostrar_resultado(self, resultado) -> None:
        self.valor_nombre.setText(resultado.nombre_archivo)
        self.valor_paginas.setText(str(resultado.cantidad_paginas))
        self.valor_texto.setText("Sí" if resultado.tiene_texto_digital else "No")
        self.valor_ocr.setText("Sí" if resultado.necesita_ocr else "No")

        self.valor_texto.setObjectName("estado_ok" if resultado.tiene_texto_digital else "estado_alerta")
        self.valor_ocr.setObjectName("estado_alerta" if resultado.necesita_ocr else "estado_ok")
        self.valor_texto.style().unpolish(self.valor_texto)
        self.valor_texto.style().polish(self.valor_texto)
        self.valor_ocr.style().unpolish(self.valor_ocr)
        self.valor_ocr.style().polish(self.valor_ocr)

        self.tabla_paginas.setRowCount(0)

        for pagina in resultado.resumen_paginas:
            fila = self.tabla_paginas.rowCount()
            self.tabla_paginas.insertRow(fila)

            item_pagina = QTableWidgetItem(str(pagina.numero_pagina))
            item_estado = QTableWidgetItem("Con texto" if pagina.tiene_texto else "Sin texto")
            item_caracteres = QTableWidgetItem(str(pagina.cantidad_caracteres))

            self.tabla_paginas.setItem(fila, 0, item_pagina)
            self.tabla_paginas.setItem(fila, 1, item_estado)
            self.tabla_paginas.setItem(fila, 2, item_caracteres)

    def _limpiar_resultados(self) -> None:
        self.valor_nombre.setText("-")
        self.valor_paginas.setText("-")
        self.valor_texto.setText("-")
        self.valor_ocr.setText("-")
        self.valor_texto.setObjectName("")
        self.valor_ocr.setObjectName("")
        self.valor_texto.style().unpolish(self.valor_texto)
        self.valor_texto.style().polish(self.valor_texto)
        self.valor_ocr.style().unpolish(self.valor_ocr)
        self.valor_ocr.style().polish(self.valor_ocr)
        self.tabla_paginas.setRowCount(0)

    def _mostrar_notificacion(self, mensaje: str, tipo: str) -> None:
        self.label_notificacion.setText(mensaje)

        if tipo == "ok":
            self.label_notificacion.setObjectName("estado_ok")
        elif tipo == "alerta":
            self.label_notificacion.setObjectName("estado_alerta")
        else:
            self.label_notificacion.setObjectName("estado_error")

        self.label_notificacion.style().unpolish(self.label_notificacion)
        self.label_notificacion.style().polish(self.label_notificacion)