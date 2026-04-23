from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pipeline_documento import PipelineDocumento


class VentanaPrincipal(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.pipeline = PipelineDocumento()
        self.resultado_actual = None
        self.setWindowTitle("Analizador de PDFs")
        self.resize(1220, 880)
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
        self._crear_panel_central(layout_principal)
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
        layout_principal = QVBoxLayout(grupo)
        layout_principal.setSpacing(10)

        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(10)

        self.input_ruta = QLineEdit()
        self.input_ruta.setPlaceholderText("Selecciona un archivo PDF...")
        self.input_ruta.setReadOnly(True)

        self.boton_seleccionar = QPushButton("Seleccionar PDF")
        self.boton_seleccionar.clicked.connect(self.seleccionar_pdf)

        fila_superior.addWidget(self.input_ruta, 1)
        fila_superior.addWidget(self.boton_seleccionar)

        fila_progreso = QHBoxLayout()
        fila_progreso.setSpacing(10)

        self.label_progreso = QLabel("Esperando archivo...")
        self.label_progreso.setObjectName("diagnostico_secundario")

        self.barra_progreso = QProgressBar()
        self.barra_progreso.setRange(0, 100)
        self.barra_progreso.setValue(0)
        self.barra_progreso.setTextVisible(True)

        fila_progreso.addWidget(self.label_progreso, 1)
        fila_progreso.addWidget(self.barra_progreso, 2)

        layout_principal.addLayout(fila_superior)
        layout_principal.addLayout(fila_progreso)

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
        etiqueta_ocr = QLabel("OCR sugerido")
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

        self.valor_detalle_diagnostico = QLabel("Aún no se ha procesado ningún documento.")
        self.valor_detalle_diagnostico.setWordWrap(True)

        self.valor_confianza_diagnostico = QLabel("Confianza estimada: -")
        self.valor_confianza_diagnostico.setObjectName("diagnostico_secundario")
        self.valor_confianza_diagnostico.setWordWrap(True)

        etiqueta_estado_ocr = QLabel("Estado OCR")
        etiqueta_estado_ocr.setObjectName("etiqueta_seccion")

        self.valor_estado_ocr = QLabel("OCR no ejecutado")
        self.valor_estado_ocr.setObjectName("valor_principal")
        self.valor_estado_ocr.setWordWrap(True)

        etiqueta_detalle_ocr = QLabel("Detalle OCR")
        etiqueta_detalle_ocr.setObjectName("etiqueta_seccion")

        self.valor_detalle_ocr = QLabel("Sin preparación pendiente.")
        self.valor_detalle_ocr.setWordWrap(True)

        layout.addWidget(etiqueta_titulo)
        layout.addWidget(self.valor_diagnostico)
        layout.addSpacing(8)
        layout.addWidget(etiqueta_detalle)
        layout.addWidget(self.valor_detalle_diagnostico)
        layout.addSpacing(8)
        layout.addWidget(self.valor_confianza_diagnostico)
        layout.addSpacing(10)
        layout.addWidget(etiqueta_estado_ocr)
        layout.addWidget(self.valor_estado_ocr)
        layout.addSpacing(8)
        layout.addWidget(etiqueta_detalle_ocr)
        layout.addWidget(self.valor_detalle_ocr)
        layout.addStretch()

        return grupo

    def _crear_panel_central(self, layout_padre: QVBoxLayout) -> None:
        self.pestanas_centrales = QTabWidget()

        tab_detalle = self._crear_tab_detalle_paginas()
        tab_texto = self._crear_tab_texto()

        self.pestanas_centrales.addTab(tab_detalle, "Detalle por página")
        self.pestanas_centrales.addTab(tab_texto, "Texto extraído")

        layout_padre.addWidget(self.pestanas_centrales, 1)

    def _crear_tab_detalle_paginas(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(8, 8, 8, 8)

        self.tabla_paginas = QTableWidget(0, 6)
        self.tabla_paginas.setHorizontalHeaderLabels(
            [
                "Página",
                "Texto",
                "Caracteres",
                "Imágenes",
                "Cobertura imagen",
                "Diagnóstico",
            ]
        )
        self.tabla_paginas.verticalHeader().setVisible(False)
        self.tabla_paginas.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_paginas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_paginas.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_paginas.setAlternatingRowColors(True)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tabla_paginas.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout.addWidget(self.tabla_paginas)
        return contenedor

    def _crear_tab_texto(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(8, 8, 8, 8)

        self.pestanas_texto = QTabWidget()

        pestaña_texto_digital = QWidget()
        layout_digital = QVBoxLayout(pestaña_texto_digital)
        layout_digital.setContentsMargins(8, 8, 8, 8)

        self.texto_completo = QPlainTextEdit()
        self.texto_completo.setReadOnly(True)
        self.texto_completo.setPlaceholderText("Aquí se mostrará el texto digital extraído del documento.")
        layout_digital.addWidget(self.texto_completo)

        pestaña_texto_ocr = QWidget()
        layout_ocr = QVBoxLayout(pestaña_texto_ocr)
        layout_ocr.setContentsMargins(8, 8, 8, 8)

        self.texto_ocr_completo = QPlainTextEdit()
        self.texto_ocr_completo.setReadOnly(True)
        self.texto_ocr_completo.setPlaceholderText("Aquí se mostrará el texto OCR obtenido del documento.")
        layout_ocr.addWidget(self.texto_ocr_completo)

        pestaña_texto_por_pagina = QWidget()
        layout_por_pagina = QVBoxLayout(pestaña_texto_por_pagina)
        layout_por_pagina.setContentsMargins(8, 8, 8, 8)
        layout_por_pagina.setSpacing(8)

        fila_selector = QHBoxLayout()
        etiqueta_selector = QLabel("Página:")
        etiqueta_selector.setObjectName("etiqueta_seccion")

        self.selector_pagina = QComboBox()
        self.selector_pagina.currentIndexChanged.connect(self._mostrar_texto_pagina_seleccionada)

        fila_selector.addWidget(etiqueta_selector)
        fila_selector.addWidget(self.selector_pagina)
        fila_selector.addStretch()

        splitter = QSplitter(Qt.Vertical)

        panel_digital = QWidget()
        layout_panel_digital = QVBoxLayout(panel_digital)
        layout_panel_digital.setContentsMargins(0, 0, 0, 0)
        layout_panel_digital.setSpacing(6)

        label_digital = QLabel("Texto digital de la página")
        label_digital.setObjectName("etiqueta_seccion")

        self.texto_pagina_digital = QPlainTextEdit()
        self.texto_pagina_digital.setReadOnly(True)

        layout_panel_digital.addWidget(label_digital)
        layout_panel_digital.addWidget(self.texto_pagina_digital)

        panel_ocr = QWidget()
        layout_panel_ocr = QVBoxLayout(panel_ocr)
        layout_panel_ocr.setContentsMargins(0, 0, 0, 0)
        layout_panel_ocr.setSpacing(6)

        label_ocr = QLabel("Texto OCR de la página")
        label_ocr.setObjectName("etiqueta_seccion")

        self.texto_pagina_ocr = QPlainTextEdit()
        self.texto_pagina_ocr.setReadOnly(True)

        layout_panel_ocr.addWidget(label_ocr)
        layout_panel_ocr.addWidget(self.texto_pagina_ocr)

        splitter.addWidget(panel_digital)
        splitter.addWidget(panel_ocr)
        splitter.setSizes([300, 300])

        layout_por_pagina.addLayout(fila_selector)
        layout_por_pagina.addWidget(splitter)

        self.pestanas_texto.addTab(pestaña_texto_digital, "Texto digital")
        self.pestanas_texto.addTab(pestaña_texto_ocr, "Texto OCR")
        self.pestanas_texto.addTab(pestaña_texto_por_pagina, "Texto por página")

        layout.addWidget(self.pestanas_texto)
        return contenedor

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
        self._actualizar_progreso(0, "Iniciando procesamiento...")
        self._mostrar_notificacion("Procesando documento seleccionado...", "alerta")
        self.boton_seleccionar.setEnabled(False)

        try:
            resultado = self.pipeline.procesar(
                ruta_archivo,
                callback=self._actualizar_progreso,
            )
            self.resultado_actual = resultado
            self._mostrar_resultado(resultado)
            self._actualizar_progreso(100, "Procesamiento completado.")
            self._mostrar_notificacion("El documento fue analizado correctamente.", "ok")
        except FileNotFoundError as error:
            self.resultado_actual = None
            self._limpiar_resultados()
            self._actualizar_progreso(0, "No se pudo localizar el archivo.")
            self._mostrar_notificacion(str(error), "error")
            QMessageBox.warning(self, "Archivo no válido", str(error))
        except ValueError as error:
            self.resultado_actual = None
            self._limpiar_resultados()
            self._actualizar_progreso(0, "El PDF no pudo analizarse.")
            self._mostrar_notificacion(str(error), "error")
            QMessageBox.critical(self, "Error al analizar PDF", str(error))
        except Exception as error:
            self.resultado_actual = None
            self._limpiar_resultados()
            mensaje = f"Ocurrió un error inesperado: {error}"
            self._actualizar_progreso(0, "Error inesperado durante el análisis.")
            self._mostrar_notificacion(mensaje, "error")
            QMessageBox.critical(self, "Error inesperado", mensaje)
        finally:
            self.boton_seleccionar.setEnabled(True)

    def _actualizar_progreso(self, valor: int, mensaje: str) -> None:
        self.barra_progreso.setValue(max(0, min(100, valor)))
        self.label_progreso.setText(mensaje)
        self.statusBar().showMessage(mensaje)
        QApplication.processEvents()

    def _mostrar_resultado(self, resultado) -> None:
        self.valor_nombre.setText(resultado.nombre_archivo)
        self.valor_paginas.setText(str(resultado.cantidad_paginas))
        self.valor_texto.setText("Sí" if resultado.tiene_texto_digital else "No")
        self.valor_ocr.setText(resultado.tipo_ocr_sugerido)

        self.valor_diagnostico.setText(resultado.diagnostico_general)
        self.valor_detalle_diagnostico.setText(resultado.detalle_diagnostico)
        self.valor_confianza_diagnostico.setText(
            f"Confianza estimada: {resultado.confianza_diagnostico}%"
        )

        self.valor_estado_ocr.setText(resultado.estado_ocr)
        detalle_ocr = resultado.detalle_ocr
        if resultado.paginas_ocr_objetivo > 0:
            detalle_ocr += (
                f"\nPáginas objetivo: {resultado.paginas_ocr_objetivo} | "
                f"Procesadas: {resultado.paginas_ocr_procesadas}"
            )
        detalle_ocr += f"\nMotor OCR: {resultado.motor_ocr}"
        self.valor_detalle_ocr.setText(detalle_ocr)

        self.valor_texto.setObjectName("estado_ok" if resultado.tiene_texto_digital else "estado_alerta")
        self.valor_ocr.setObjectName("estado_ok" if resultado.tipo_ocr_sugerido == "No" else "estado_alerta")

        if resultado.codigo_diagnostico_general == "texto_digital":
            self.valor_diagnostico.setObjectName("estado_ok")
        else:
            self.valor_diagnostico.setObjectName("estado_alerta")

        if resultado.codigo_estado_ocr in {"ejecutado"}:
            self.valor_estado_ocr.setObjectName("estado_ok")
        elif resultado.codigo_estado_ocr in {"parcial", "apto", "no_ejecutado"}:
            self.valor_estado_ocr.setObjectName("estado_alerta")
        else:
            self.valor_estado_ocr.setObjectName("estado_error")

        self.valor_texto.style().unpolish(self.valor_texto)
        self.valor_texto.style().polish(self.valor_texto)

        self.valor_ocr.style().unpolish(self.valor_ocr)
        self.valor_ocr.style().polish(self.valor_ocr)

        self.valor_diagnostico.style().unpolish(self.valor_diagnostico)
        self.valor_diagnostico.style().polish(self.valor_diagnostico)

        self.valor_estado_ocr.style().unpolish(self.valor_estado_ocr)
        self.valor_estado_ocr.style().polish(self.valor_estado_ocr)

        self.tabla_paginas.setRowCount(0)

        for pagina in resultado.resumen_paginas:
            fila = self.tabla_paginas.rowCount()
            self.tabla_paginas.insertRow(fila)

            item_pagina = QTableWidgetItem(str(pagina.numero_pagina))
            item_texto = QTableWidgetItem("Sí" if pagina.tiene_texto else "No")
            item_caracteres = QTableWidgetItem(str(pagina.cantidad_caracteres))
            item_imagenes = QTableWidgetItem(str(pagina.cantidad_imagenes))
            item_cobertura = QTableWidgetItem(f"{pagina.cobertura_imagen * 100:.0f}%")
            item_diagnostico = QTableWidgetItem(f"{pagina.diagnostico} ({pagina.confianza}%)")

            item_pagina.setTextAlignment(Qt.AlignCenter)
            item_texto.setTextAlignment(Qt.AlignCenter)
            item_caracteres.setTextAlignment(Qt.AlignCenter)
            item_imagenes.setTextAlignment(Qt.AlignCenter)
            item_cobertura.setTextAlignment(Qt.AlignCenter)

            self.tabla_paginas.setItem(fila, 0, item_pagina)
            self.tabla_paginas.setItem(fila, 1, item_texto)
            self.tabla_paginas.setItem(fila, 2, item_caracteres)
            self.tabla_paginas.setItem(fila, 3, item_imagenes)
            self.tabla_paginas.setItem(fila, 4, item_cobertura)
            self.tabla_paginas.setItem(fila, 5, item_diagnostico)

        self._cargar_texto_extraido(resultado)

    def _cargar_texto_extraido(self, resultado) -> None:
        self.selector_pagina.blockSignals(True)
        self.selector_pagina.clear()

        if resultado.tiene_texto_digital and resultado.texto_completo.strip():
            self.texto_completo.setPlainText(resultado.texto_completo)
        else:
            self.texto_completo.setPlainText(
                "Este documento no contiene texto digital suficiente para una lectura completa."
            )

        if resultado.texto_ocr_completo.strip():
            self.texto_ocr_completo.setPlainText(resultado.texto_ocr_completo)
        else:
            self.texto_ocr_completo.setPlainText(
                f"{resultado.estado_ocr}\n\n{resultado.detalle_ocr}"
            )

        for pagina in resultado.resumen_paginas:
            self.selector_pagina.addItem(f"Página {pagina.numero_pagina}")

        self.selector_pagina.blockSignals(False)

        if resultado.resumen_paginas:
            self.selector_pagina.setCurrentIndex(0)
            self._mostrar_texto_pagina(0)
        else:
            self.texto_pagina_digital.setPlainText("No hay páginas disponibles para mostrar.")
            self.texto_pagina_ocr.setPlainText("No hay páginas disponibles para mostrar.")

    def _mostrar_texto_pagina_seleccionada(self, indice: int) -> None:
        self._mostrar_texto_pagina(indice)

    def _mostrar_texto_pagina(self, indice: int) -> None:
        if self.resultado_actual is None:
            self.texto_pagina_digital.setPlainText("")
            self.texto_pagina_ocr.setPlainText("")
            return

        if indice < 0 or indice >= len(self.resultado_actual.resumen_paginas):
            self.texto_pagina_digital.setPlainText("")
            self.texto_pagina_ocr.setPlainText("")
            return

        pagina = self.resultado_actual.resumen_paginas[indice]

        if pagina.tiene_texto and pagina.texto_extraido.strip():
            self.texto_pagina_digital.setPlainText(pagina.texto_extraido)
        else:
            self.texto_pagina_digital.setPlainText(
                "Esta página no contiene texto digital suficiente."
            )

        if pagina.ocr_error:
            self.texto_pagina_ocr.setPlainText(
                f"OCR con error en esta página:\n\n{pagina.ocr_error}"
            )
        elif pagina.ocr_ejecutado and pagina.texto_ocr.strip():
            self.texto_pagina_ocr.setPlainText(pagina.texto_ocr)
        elif pagina.ocr_ejecutado and not pagina.texto_ocr.strip():
            self.texto_pagina_ocr.setPlainText(
                "OCR ejecutado, pero no devolvió texto legible en esta página."
            )
        else:
            if self.resultado_actual.codigo_estado_ocr == "no_disponible":
                self.texto_pagina_ocr.setPlainText(
                    "OCR no disponible. Instala Tesseract y vuelve a intentar."
                )
            elif self.resultado_actual.codigo_estado_ocr == "no_ejecutado":
                self.texto_pagina_ocr.setPlainText(
                    "OCR no fue necesario para esta página."
                )
            else:
                self.texto_pagina_ocr.setPlainText(
                    "OCR no se aplicó a esta página en esta ejecución."
                )

    def _limpiar_resultados(self) -> None:
        self.valor_nombre.setText("-")
        self.valor_paginas.setText("-")
        self.valor_texto.setText("-")
        self.valor_ocr.setText("-")
        self.valor_diagnostico.setText("Sin análisis")
        self.valor_detalle_diagnostico.setText("No se pudo obtener información del documento.")
        self.valor_confianza_diagnostico.setText("Confianza estimada: -")
        self.valor_estado_ocr.setText("OCR no ejecutado")
        self.valor_detalle_ocr.setText("Sin preparación pendiente.")
        self.texto_completo.setPlainText("")
        self.texto_ocr_completo.setPlainText("")
        self.texto_pagina_digital.setPlainText("")
        self.texto_pagina_ocr.setPlainText("")

        self.valor_texto.setObjectName("valor_principal")
        self.valor_ocr.setObjectName("valor_principal")
        self.valor_diagnostico.setObjectName("diagnostico_texto")
        self.valor_estado_ocr.setObjectName("valor_principal")

        self.valor_texto.style().unpolish(self.valor_texto)
        self.valor_texto.style().polish(self.valor_texto)

        self.valor_ocr.style().unpolish(self.valor_ocr)
        self.valor_ocr.style().polish(self.valor_ocr)

        self.valor_diagnostico.style().unpolish(self.valor_diagnostico)
        self.valor_diagnostico.style().polish(self.valor_diagnostico)

        self.valor_estado_ocr.style().unpolish(self.valor_estado_ocr)
        self.valor_estado_ocr.style().polish(self.valor_estado_ocr)

        self.tabla_paginas.setRowCount(0)
        self.selector_pagina.clear()

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