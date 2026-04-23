from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
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
    QPlainTextEdit,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from analizador_pdf import AnalizadorPDF


class VentanaPrincipal(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.analizador = AnalizadorPDF()
        self.resultado_actual = None
        self.setWindowTitle("Analizador de PDFs")
        self.resize(1160, 820)
        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        contenedor = QWidget()
        self.setCentralWidget(contenedor)

        layout_principal = QVBoxLayout(contenedor)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(16)

        self._crear_encabezado(layout_principal)
        self._crear_panel_seleccion(layout_principal)
        self._crear_panel_superior(layout_principal)
        self._crear_panel_paginas(layout_principal)
        self._crear_panel_texto(layout_principal)
        self._crear_panel_notificacion(layout_principal)

        barra_estado = QStatusBar()
        barra_estado.showMessage("Aplicación lista.")
        self.setStatusBar(barra_estado)

    def _crear_encabezado(self, layout_padre: QVBoxLayout) -> None:
        titulo = QLabel("Analizador inicial de PDF")
        titulo.setObjectName("titulo_principal")

        subtitulo = QLabel(
            "Carga un PDF y revisa si contiene texto digital, si es mixto o si probablemente requerirá OCR."
        )
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

    def _crear_panel_superior(self, layout_padre: QVBoxLayout) -> None:
        layout_superior = QHBoxLayout()
        layout_superior.setSpacing(16)

        grupo_resumen = self._crear_panel_resumen()
        grupo_diagnostico = self._crear_panel_diagnostico()

        layout_superior.addWidget(grupo_resumen, 2)
        layout_superior.addWidget(grupo_diagnostico, 1)

        layout_padre.addLayout(layout_superior)

    def _crear_panel_resumen(self) -> QGroupBox:
        grupo = QGroupBox("Resumen del documento")
        layout = QGridLayout(grupo)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(12)

        etiqueta_nombre = QLabel("Nombre del archivo")
        etiqueta_nombre.setObjectName("etiqueta_seccion")
        etiqueta_paginas = QLabel("Cantidad de páginas")
        etiqueta_paginas.setObjectName("etiqueta_seccion")
        etiqueta_texto = QLabel("Texto digital detectado")
        etiqueta_texto.setObjectName("etiqueta_seccion")
        etiqueta_ocr = QLabel("Necesidad probable de OCR")
        etiqueta_ocr.setObjectName("etiqueta_seccion")

        self.valor_nombre = QLabel("-")
        self.valor_nombre.setObjectName("valor_principal")
        self.valor_nombre.setWordWrap(True)

        self.valor_paginas = QLabel("-")
        self.valor_paginas.setObjectName("valor_principal")

        self.valor_texto = QLabel("-")
        self.valor_texto.setObjectName("valor_principal")

        self.valor_ocr = QLabel("-")
        self.valor_ocr.setObjectName("valor_principal")

        tarjeta_1 = self._crear_tarjeta_resumen(etiqueta_nombre, self.valor_nombre)
        tarjeta_2 = self._crear_tarjeta_resumen(etiqueta_paginas, self.valor_paginas)
        tarjeta_3 = self._crear_tarjeta_resumen(etiqueta_texto, self.valor_texto)
        tarjeta_4 = self._crear_tarjeta_resumen(etiqueta_ocr, self.valor_ocr)

        layout.addWidget(tarjeta_1, 0, 0, 1, 2)
        layout.addWidget(tarjeta_2, 1, 0)
        layout.addWidget(tarjeta_3, 1, 1)
        layout.addWidget(tarjeta_4, 2, 0, 1, 2)

        return grupo

    def _crear_tarjeta_resumen(self, etiqueta: QLabel, valor: QLabel) -> QFrame:
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta_resumen")

        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        layout.addWidget(etiqueta)
        layout.addWidget(valor)

        return tarjeta

    def _crear_panel_diagnostico(self) -> QGroupBox:
        grupo = QGroupBox("Diagnóstico")
        layout = QVBoxLayout(grupo)
        layout.setSpacing(10)

        etiqueta_titulo = QLabel("Estado detectado")
        etiqueta_titulo.setObjectName("etiqueta_seccion")

        self.valor_diagnostico = QLabel("Sin análisis")
        self.valor_diagnostico.setObjectName("diagnostico_texto")
        self.valor_diagnostico.setWordWrap(True)

        etiqueta_detalle = QLabel("Interpretación")
        etiqueta_detalle.setObjectName("etiqueta_seccion")

        self.valor_detalle_diagnostico = QLabel(
            "Aún no se ha procesado ningún documento."
        )
        self.valor_detalle_diagnostico.setWordWrap(True)

        layout.addWidget(etiqueta_titulo)
        layout.addWidget(self.valor_diagnostico)
        layout.addSpacing(8)
        layout.addWidget(etiqueta_detalle)
        layout.addWidget(self.valor_detalle_diagnostico)
        layout.addStretch()

        return grupo

    def _crear_panel_paginas(self, layout_padre: QVBoxLayout) -> None:
        grupo = QGroupBox("Detalle por página")
        layout = QVBoxLayout(grupo)

        self.tabla_paginas = QTableWidget(0, 3)
        self.tabla_paginas.setHorizontalHeaderLabels(["Página", "Estado", "Caracteres detectados"])
        self.tabla_paginas.verticalHeader().setVisible(False)
        self.tabla_paginas.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_paginas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_paginas.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_paginas.setAlternatingRowColors(True)
        self.tabla_paginas.horizontalHeader().setStretchLastSection(False)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_paginas.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout.addWidget(self.tabla_paginas)
        layout_padre.addWidget(grupo, 1)

    def _crear_panel_texto(self, layout_padre: QVBoxLayout) -> None:
        grupo = QGroupBox("Texto extraído")
        layout = QVBoxLayout(grupo)

        self.pestanas_texto = QTabWidget()

        pestaña_texto_completo = QWidget()
        layout_texto_completo = QVBoxLayout(pestaña_texto_completo)
        layout_texto_completo.setContentsMargins(8, 8, 8, 8)

        self.texto_completo = QPlainTextEdit()
        self.texto_completo.setReadOnly(True)
        self.texto_completo.setPlaceholderText("Aquí se mostrará el texto completo extraído del documento.")
        layout_texto_completo.addWidget(self.texto_completo)

        pestaña_texto_por_pagina = QWidget()
        layout_texto_por_pagina = QVBoxLayout(pestaña_texto_por_pagina)
        layout_texto_por_pagina.setContentsMargins(8, 8, 8, 8)
        layout_texto_por_pagina.setSpacing(8)

        fila_selector = QHBoxLayout()
        etiqueta_selector = QLabel("Página:")
        etiqueta_selector.setObjectName("etiqueta_seccion")

        self.selector_pagina = QComboBox()
        self.selector_pagina.currentIndexChanged.connect(self._mostrar_texto_pagina_seleccionada)

        fila_selector.addWidget(etiqueta_selector)
        fila_selector.addWidget(self.selector_pagina)
        fila_selector.addStretch()

        self.texto_pagina = QPlainTextEdit()
        self.texto_pagina.setReadOnly(True)
        self.texto_pagina.setPlaceholderText("Aquí se mostrará el texto de la página seleccionada.")

        layout_texto_por_pagina.addLayout(fila_selector)
        layout_texto_por_pagina.addWidget(self.texto_pagina)

        self.pestanas_texto.addTab(pestaña_texto_completo, "Texto completo")
        self.pestanas_texto.addTab(pestaña_texto_por_pagina, "Texto por página")

        layout.addWidget(self.pestanas_texto)
        layout_padre.addWidget(grupo, 1)

    def _crear_panel_notificacion(self, layout_padre: QVBoxLayout) -> None:
        panel = QFrame()
        panel.setObjectName("panel_notificacion")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

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
            self.resultado_actual = resultado
            self._mostrar_resultado(resultado)
            self.statusBar().showMessage("Análisis completado correctamente.")
            self._mostrar_notificacion("El documento fue analizado correctamente.", "ok")
        except FileNotFoundError as error:
            self.resultado_actual = None
            self._limpiar_resultados()
            self.statusBar().showMessage("No se pudo localizar el archivo.")
            self._mostrar_notificacion(str(error), "error")
            QMessageBox.warning(self, "Archivo no válido", str(error))
        except ValueError as error:
            self.resultado_actual = None
            self._limpiar_resultados()
            self.statusBar().showMessage("El PDF no pudo analizarse.")
            self._mostrar_notificacion(str(error), "error")
            QMessageBox.critical(self, "Error al analizar PDF", str(error))
        except Exception as error:
            self.resultado_actual = None
            self._limpiar_resultados()
            mensaje = f"Ocurrió un error inesperado: {error}"
            self.statusBar().showMessage("Error inesperado durante el análisis.")
            self._mostrar_notificacion(mensaje, "error")
            QMessageBox.critical(self, "Error inesperado", mensaje)

    def _mostrar_resultado(self, resultado) -> None:
        self.valor_nombre.setText(resultado.nombre_archivo)
        self.valor_paginas.setText(str(resultado.cantidad_paginas))

        total_paginas = len(resultado.resumen_paginas)
        paginas_con_texto = sum(1 for pagina in resultado.resumen_paginas if pagina.tiene_texto)
        paginas_sin_texto = total_paginas - paginas_con_texto

        self.valor_texto.setText("Sí" if resultado.tiene_texto_digital else "No")
        self.valor_ocr.setText("Sí" if resultado.necesita_ocr else "No")

        if paginas_con_texto == total_paginas and total_paginas > 0:
            diagnostico = "PDF con texto digital"
            detalle = "Todas las páginas tienen texto extraíble. No parece requerir OCR."
            tipo_diagnostico = "ok"
        elif paginas_con_texto > 0 and paginas_sin_texto > 0:
            diagnostico = "PDF mixto o híbrido"
            detalle = (
                f"Se detectaron {paginas_con_texto} páginas con texto y "
                f"{paginas_sin_texto} páginas sin texto. Puede requerir OCR parcial."
            )
            tipo_diagnostico = "alerta"
        else:
            diagnostico = "PDF escaneado / OCR recomendado"
            detalle = "No se detectó texto digital extraíble. Probablemente requerirá OCR."
            tipo_diagnostico = "alerta"

        self.valor_diagnostico.setText(diagnostico)
        self.valor_detalle_diagnostico.setText(detalle)

        self.valor_texto.setObjectName("estado_ok" if resultado.tiene_texto_digital else "estado_alerta")
        self.valor_ocr.setObjectName("estado_alerta" if resultado.necesita_ocr else "estado_ok")
        self.valor_diagnostico.setObjectName("estado_ok" if tipo_diagnostico == "ok" else "estado_alerta")

        self.valor_texto.style().unpolish(self.valor_texto)
        self.valor_texto.style().polish(self.valor_texto)

        self.valor_ocr.style().unpolish(self.valor_ocr)
        self.valor_ocr.style().polish(self.valor_ocr)

        self.valor_diagnostico.style().unpolish(self.valor_diagnostico)
        self.valor_diagnostico.style().polish(self.valor_diagnostico)

        self.tabla_paginas.setRowCount(0)

        for pagina in resultado.resumen_paginas:
            fila = self.tabla_paginas.rowCount()
            self.tabla_paginas.insertRow(fila)

            item_pagina = QTableWidgetItem(str(pagina.numero_pagina))
            item_estado = QTableWidgetItem("Con texto" if pagina.tiene_texto else "Sin texto")
            item_caracteres = QTableWidgetItem(str(pagina.cantidad_caracteres))

            item_pagina.setTextAlignment(Qt.AlignCenter)
            item_caracteres.setTextAlignment(Qt.AlignCenter)

            self.tabla_paginas.setItem(fila, 0, item_pagina)
            self.tabla_paginas.setItem(fila, 1, item_estado)
            self.tabla_paginas.setItem(fila, 2, item_caracteres)

        self._cargar_texto_extraido(resultado)

    def _cargar_texto_extraido(self, resultado) -> None:
        self.selector_pagina.blockSignals(True)
        self.selector_pagina.clear()

        if resultado.tiene_texto_digital:
            if resultado.texto_completo.strip():
                self.texto_completo.setPlainText(resultado.texto_completo)
            else:
                self.texto_completo.setPlainText(
                    "Se detectó texto digital, pero no se pudo construir un bloque de texto completo."
                )

            for pagina in resultado.resumen_paginas:
                self.selector_pagina.addItem(f"Página {pagina.numero_pagina}")

            if resultado.resumen_paginas:
                self.selector_pagina.setCurrentIndex(0)
                self._mostrar_texto_pagina(0)
            else:
                self.texto_pagina.setPlainText("No hay páginas disponibles para mostrar.")
        else:
            mensaje = (
                "Este documento no contiene texto digital extraíble.\n\n"
                "En una fase posterior se integrará OCR para intentar leer este tipo de archivos."
            )
            self.texto_completo.setPlainText(mensaje)
            self.texto_pagina.setPlainText(mensaje)

        self.selector_pagina.blockSignals(False)

    def _mostrar_texto_pagina_seleccionada(self, indice: int) -> None:
        self._mostrar_texto_pagina(indice)

    def _mostrar_texto_pagina(self, indice: int) -> None:
        if self.resultado_actual is None:
            self.texto_pagina.setPlainText("")
            return

        if indice < 0 or indice >= len(self.resultado_actual.resumen_paginas):
            self.texto_pagina.setPlainText("")
            return

        pagina = self.resultado_actual.resumen_paginas[indice]

        if pagina.tiene_texto and pagina.texto_extraido.strip():
            self.texto_pagina.setPlainText(pagina.texto_extraido)
        else:
            self.texto_pagina.setPlainText(
                "Esta página no contiene texto digital extraíble.\n\n"
                "Quedará pendiente para OCR en una fase posterior."
            )

    def _limpiar_resultados(self) -> None:
        self.valor_nombre.setText("-")
        self.valor_paginas.setText("-")
        self.valor_texto.setText("-")
        self.valor_ocr.setText("-")
        self.valor_diagnostico.setText("Sin análisis")
        self.valor_detalle_diagnostico.setText("No se pudo obtener información del documento.")

        self.valor_texto.setObjectName("valor_principal")
        self.valor_ocr.setObjectName("valor_principal")
        self.valor_diagnostico.setObjectName("diagnostico_texto")

        self.valor_texto.style().unpolish(self.valor_texto)
        self.valor_texto.style().polish(self.valor_texto)

        self.valor_ocr.style().unpolish(self.valor_ocr)
        self.valor_ocr.style().polish(self.valor_ocr)

        self.valor_diagnostico.style().unpolish(self.valor_diagnostico)
        self.valor_diagnostico.style().polish(self.valor_diagnostico)

        self.tabla_paginas.setRowCount(0)
        self.selector_pagina.clear()
        self.texto_completo.setPlainText("")
        self.texto_pagina.setPlainText("")

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