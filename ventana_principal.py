from pathlib import Path

import fitz
from PySide6.QtCore import Qt, QThread
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QCheckBox,
    QComboBox,
    QDialog,
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
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from dialogo_progreso import DialogoProgreso
from exportador_resultados import ExportadorResultados
from modos_analisis import ModoAnalisis
from trabajador_analisis import TrabajadorAnalisis


class VentanaPrincipal(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.exportador = ExportadorResultados()

        from exportador_excel import ExportadorExcel
        from guardador_pdf_pro import GuardadorPDFPro
        from historial_analisis import HistorialAnalisis

        self.exportador_excel = ExportadorExcel()
        self.guardador_pdf_pro = GuardadorPDFPro()
        self.historial_analisis = HistorialAnalisis()

        self.resultado_actual = None
        self.resultado_basico_actual = None
        self.resultado_pro_actual = None
        self.comparacion_actual = None
        self.pixmap_preview_original = None

        self.hilo_analisis: QThread | None = None
        self.trabajador_analisis: TrabajadorAnalisis | None = None
        self.dialogo_progreso: DialogoProgreso | None = None

        self.setWindowTitle("Analizador de PDFs")
        self.resize(1260, 960)
        self.setAcceptDrops(True)
        self._construir_interfaz()

    def _construir_interfaz(self) -> None:
        contenedor = QWidget()
        self.setCentralWidget(contenedor)

        layout_principal = QVBoxLayout(contenedor)
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(16)

        self._crear_encabezado(layout_principal)
        self._crear_panel_archivo(layout_principal)
        self._crear_tabs_principales(layout_principal)
        self._crear_panel_notificacion(layout_principal)

        barra_estado = QStatusBar()
        barra_estado.showMessage("Aplicación lista.")
        self.setStatusBar(barra_estado)

    def _crear_encabezado(self, layout_padre: QVBoxLayout) -> None:
        titulo = QLabel("Analizador inicial de PDF")
        titulo.setObjectName("titulo_principal")

        subtitulo = QLabel(
            "Carga un PDF, arrástralo a la ventana o suéltalo aquí. Ahora puedes ejecutar análisis en modo Básico, Pro estructural o Comparar ambos."
        )
        subtitulo.setObjectName("subtitulo")
        subtitulo.setWordWrap(True)

        layout_padre.addWidget(titulo)
        layout_padre.addWidget(subtitulo)

    def _crear_panel_archivo(self, layout_padre: QVBoxLayout) -> None:
        grupo = QGroupBox("Archivo PDF")
        layout_principal = QVBoxLayout(grupo)
        layout_principal.setSpacing(10)

        fila_superior = QHBoxLayout()
        fila_superior.setSpacing(10)

        self.input_ruta = QLineEdit()
        self.input_ruta.setPlaceholderText("Selecciona o arrastra un archivo PDF...")
        self.input_ruta.setReadOnly(True)

        self.selector_modo = QComboBox()
        for modo, etiqueta in ModoAnalisis.opciones_combo():
            self.selector_modo.addItem(etiqueta, modo)

        self.boton_seleccionar = QPushButton("Seleccionar PDF")
        self.boton_seleccionar.clicked.connect(self.seleccionar_pdf)

        fila_superior.addWidget(self.input_ruta, 1)
        fila_superior.addWidget(self.selector_modo)
        fila_superior.addWidget(self.boton_seleccionar)

        fila_exportaciones = QHBoxLayout()
        fila_exportaciones.setSpacing(10)

        self.boton_exportar_json = QPushButton("Exportar JSON")
        self.boton_exportar_json.clicked.connect(self.exportar_json)
        self.boton_exportar_json.setEnabled(False)

        self.boton_exportar_txt = QPushButton("Exportar TXT")
        self.boton_exportar_txt.clicked.connect(self.exportar_txt)
        self.boton_exportar_txt.setEnabled(False)

        self.boton_exportar_excel_actual = QPushButton("Exportar Excel actual")
        self.boton_exportar_excel_actual.clicked.connect(self.exportar_excel_actual)
        self.boton_exportar_excel_actual.setEnabled(False)

        self.boton_exportar_excel_historial = QPushButton("Exportar Excel historial")
        self.boton_exportar_excel_historial.clicked.connect(self.exportar_excel_historial)
        self.boton_exportar_excel_historial.setEnabled(self.historial_analisis.existe_historial())

        self.boton_guardar_pdf_optimizado = QPushButton("Guardar PDF optimizado")
        self.boton_guardar_pdf_optimizado.clicked.connect(self.guardar_pdf_optimizado)
        self.boton_guardar_pdf_optimizado.setEnabled(False)

        fila_exportaciones.addWidget(self.boton_exportar_json)
        fila_exportaciones.addWidget(self.boton_exportar_txt)
        fila_exportaciones.addWidget(self.boton_exportar_excel_actual)
        fila_exportaciones.addWidget(self.boton_exportar_excel_historial)
        fila_exportaciones.addWidget(self.boton_guardar_pdf_optimizado)
        fila_exportaciones.addStretch()

        fila_limites = QHBoxLayout()
        fila_limites.setSpacing(10)

        etiqueta_reintentos = QLabel("Reintentos máx/página")
        self.spin_limite_reintentos = QSpinBox()
        self.spin_limite_reintentos.setRange(1, 10)
        self.spin_limite_reintentos.setValue(4)

        etiqueta_tiempo = QLabel("Tiempo máx/página")
        self.spin_limite_tiempo = QSpinBox()
        self.spin_limite_tiempo.setRange(3, 120)
        self.spin_limite_tiempo.setValue(12)
        self.spin_limite_tiempo.setSuffix(" s")

        etiqueta_paginas = QLabel("Máx. páginas comparación")
        self.spin_limite_paginas = QSpinBox()
        self.spin_limite_paginas.setRange(3, 300)
        self.spin_limite_paginas.setValue(20)

        self.check_solo_problematicas = QCheckBox("Comparar solo páginas problemáticas")
        self.check_solo_problematicas.setChecked(True)

        fila_limites.addWidget(etiqueta_reintentos)
        fila_limites.addWidget(self.spin_limite_reintentos)
        fila_limites.addWidget(etiqueta_tiempo)
        fila_limites.addWidget(self.spin_limite_tiempo)
        fila_limites.addWidget(etiqueta_paginas)
        fila_limites.addWidget(self.spin_limite_paginas)
        fila_limites.addWidget(self.check_solo_problematicas)
        fila_limites.addStretch()

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

        self.label_alerta_operativa = QLabel("Sin alertas operativas.")
        self.label_alerta_operativa.setObjectName("diagnostico_secundario")
        self.label_alerta_operativa.setWordWrap(True)

        etiqueta_drop = QLabel("También puedes arrastrar y soltar un PDF sobre la ventana.")
        etiqueta_drop.setObjectName("diagnostico_secundario")

        layout_principal.addLayout(fila_superior)
        layout_principal.addLayout(fila_exportaciones)
        layout_principal.addLayout(fila_limites)
        layout_principal.addLayout(fila_progreso)
        layout_principal.addWidget(self.label_alerta_operativa)
        layout_principal.addWidget(etiqueta_drop)

        layout_padre.addWidget(grupo)

    def _obtener_limites_desde_ui(self):
        from limites_proceso import LimitesProceso

        return LimitesProceso(
            max_reintentos_por_pagina=self.spin_limite_reintentos.value(),
            max_tiempo_pagina_segundos=self.spin_limite_tiempo.value(),
            max_paginas_comparacion_total=self.spin_limite_paginas.value(),
            comparar_solo_paginas_problematicas=self.check_solo_problematicas.isChecked(),
        )

    def _habilitar_controles_operativos(self, habilitar: bool) -> None:
        self.boton_seleccionar.setEnabled(habilitar)
        self.selector_modo.setEnabled(habilitar)
        self.spin_limite_reintentos.setEnabled(habilitar)
        self.spin_limite_tiempo.setEnabled(habilitar)
        self.spin_limite_paginas.setEnabled(habilitar)
        self.check_solo_problematicas.setEnabled(habilitar)

    def _manejar_alerta_operativa(self, mensaje: str) -> None:
        self.label_alerta_operativa.setText(mensaje)
        self.label_alerta_operativa.setObjectName("estado_alerta")
        self.label_alerta_operativa.style().unpolish(self.label_alerta_operativa)
        self.label_alerta_operativa.style().polish(self.label_alerta_operativa)
        self._mostrar_notificacion(mensaje, "alerta")

    def _manejar_detencion_seguridad(self, mensaje: str) -> None:
        self._actualizar_progreso(0, "Análisis detenido por seguridad.")
        self._manejar_alerta_operativa(mensaje)

        if self.dialogo_progreso is not None:
            self.dialogo_progreso.finalizar(False)

        self._habilitar_controles_operativos(True)

        QMessageBox.warning(self, "Detención por seguridad", mensaje)

    def _crear_tabs_principales(self, layout_padre: QVBoxLayout) -> None:
        self.tabs_principales = QTabWidget()

        self.tab_inicio = self._crear_tab_inicio()
        self.tab_documento = self._crear_tab_documento()
        self.tab_texto_digital = self._crear_tab_texto_digital()
        self.tab_texto_ocr = self._crear_tab_texto_ocr()
        self.tab_texto_por_pagina = self._crear_tab_texto_por_pagina()

        self.tabs_principales.addTab(self.tab_inicio, "Inicio")
        self.tabs_principales.addTab(self.tab_documento, "Documento")
        self.tabs_principales.addTab(self.tab_texto_digital, "Texto digital")
        self.tabs_principales.addTab(self.tab_texto_ocr, "Texto OCR")
        self.tabs_principales.addTab(self.tab_texto_por_pagina, "Texto por página")

        layout_padre.addWidget(self.tabs_principales, 1)

    def _crear_tab_inicio(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(16)

        layout_superior = QHBoxLayout()
        layout_superior.setSpacing(16)

        grupo_resumen = self._crear_panel_resumen()
        grupo_diagnostico = self._crear_panel_diagnostico()

        layout_superior.addWidget(grupo_resumen, 2)
        layout_superior.addWidget(grupo_diagnostico, 1)

        layout.addLayout(layout_superior)

        layout_inferior = QHBoxLayout()
        layout_inferior.setSpacing(16)

        panel_preview = self._crear_panel_preview_pdf()
        panel_modo = self._crear_panel_modo_comparacion()

        layout_inferior.addWidget(panel_preview, 2)
        layout_inferior.addWidget(panel_modo, 1)

        layout.addLayout(layout_inferior, 1)

        return contenedor

    def _crear_tab_documento(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(16)

        splitter_horizontal = QSplitter(Qt.Horizontal)

        grupo_paginas = QGroupBox("Detalle por página")
        layout_paginas = QVBoxLayout(grupo_paginas)

        self.tabla_paginas = QTableWidget(0, 10)
        self.tabla_paginas.setHorizontalHeaderLabels(
            [
                "Página",
                "Texto",
                "Caracteres",
                "Imágenes",
                "Cobertura imagen",
                "Diagnóstico",
                "Dificultad",
                "Score Básico",
                "Score Pro",
                "Ganador",
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
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.tabla_paginas.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeToContents)
        self.tabla_paginas.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout_paginas.addWidget(self.tabla_paginas)

        grupo_campos = QGroupBox("Campos básicos extraídos")
        layout_campos = QVBoxLayout(grupo_campos)
        layout_campos.setSpacing(8)

        fila_campos = QHBoxLayout()
        fila_campos.setSpacing(10)

        self.label_fuente_extraccion = QLabel("Fuente de extracción: -")
        self.label_fuente_extraccion.setObjectName("diagnostico_secundario")

        self.boton_reextraer_campos = QPushButton("Reextraer desde texto revisado")
        self.boton_reextraer_campos.clicked.connect(self.reextraer_campos_desde_texto_revisado)
        self.boton_reextraer_campos.setEnabled(False)

        fila_campos.addWidget(self.label_fuente_extraccion, 1)
        fila_campos.addWidget(self.boton_reextraer_campos)

        self.tabla_campos = QTableWidget(0, 4)
        self.tabla_campos.setHorizontalHeaderLabels(
            [
                "Campo",
                "Valor",
                "Estado",
                "Estrategia",
            ]
        )
        self.tabla_campos.verticalHeader().setVisible(False)
        self.tabla_campos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_campos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_campos.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_campos.setAlternatingRowColors(True)
        self.tabla_campos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla_campos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_campos.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla_campos.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla_campos.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout_campos.addLayout(fila_campos)
        layout_campos.addWidget(self.tabla_campos)

        splitter_horizontal.addWidget(grupo_paginas)
        splitter_horizontal.addWidget(grupo_campos)
        splitter_horizontal.setStretchFactor(0, 3)
        splitter_horizontal.setStretchFactor(1, 2)
        splitter_horizontal.setSizes([940, 420])

        layout.addWidget(splitter_horizontal, 1)
        return contenedor

    def _crear_panel_preview_pdf(self) -> QGroupBox:
        grupo = QGroupBox("Vista previa del PDF")
        layout = QVBoxLayout(grupo)
        layout.setSpacing(8)

        descripcion = QLabel("Se muestra la primera página del PDF como miniatura de referencia.")
        descripcion.setObjectName("diagnostico_secundario")
        descripcion.setWordWrap(True)

        contenedor_preview = QFrame()
        contenedor_preview.setObjectName("preview_pdf_panel")
        layout_preview = QVBoxLayout(contenedor_preview)
        layout_preview.setContentsMargins(12, 12, 12, 12)

        self.label_preview_pdf = QLabel("Aún no hay vista previa disponible.")
        self.label_preview_pdf.setObjectName("preview_pdf_label")
        self.label_preview_pdf.setAlignment(Qt.AlignCenter)
        self.label_preview_pdf.setMinimumHeight(260)
        self.label_preview_pdf.setWordWrap(True)

        layout_preview.addWidget(self.label_preview_pdf)

        layout.addWidget(descripcion)
        layout.addWidget(contenedor_preview, 1)
        return grupo

    def _crear_panel_modo_comparacion(self) -> QGroupBox:
        grupo = QGroupBox("Modo y comparación")
        layout = QGridLayout(grupo)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(10)

        etiquetas = [
            ("Modo solicitado", "label_modo_solicitado"),
            ("Modo ejecutado", "label_modo_ejecutado"),
            ("Recomendación", "label_recomendacion_modo"),
            ("Ganador", "label_ganador_modo"),
            ("Score Básico", "label_score_basico"),
            ("Score Pro", "label_score_pro"),
        ]

        self.label_modo_solicitado = QLabel("-")
        self.label_modo_ejecutado = QLabel("-")
        self.label_recomendacion_modo = QLabel("-")
        self.label_recomendacion_modo.setWordWrap(True)
        self.label_ganador_modo = QLabel("-")
        self.label_score_basico = QLabel("-")
        self.label_score_pro = QLabel("-")

        widgets = {
            "label_modo_solicitado": self.label_modo_solicitado,
            "label_modo_ejecutado": self.label_modo_ejecutado,
            "label_recomendacion_modo": self.label_recomendacion_modo,
            "label_ganador_modo": self.label_ganador_modo,
            "label_score_basico": self.label_score_basico,
            "label_score_pro": self.label_score_pro,
        }

        fila = 0
        for texto, nombre in etiquetas:
            etiqueta = QLabel(texto)
            etiqueta.setObjectName("etiqueta_seccion")
            layout.addWidget(etiqueta, fila, 0)
            layout.addWidget(widgets[nombre], fila, 1)
            fila += 1

        detalle = QLabel("Detalle")
        detalle.setObjectName("etiqueta_seccion")
        self.label_detalle_comparacion = QLabel("-")
        self.label_detalle_comparacion.setWordWrap(True)

        layout.addWidget(detalle, fila, 0)
        layout.addWidget(self.label_detalle_comparacion, fila, 1)

        return grupo

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

    def _crear_tab_texto_digital(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(10)

        self.boton_copiar_digital = QPushButton("Copiar texto digital")
        self.boton_copiar_digital.clicked.connect(self.copiar_texto_digital)

        self.boton_usar_digital = QPushButton("Usar digital como base")
        self.boton_usar_digital.clicked.connect(self.usar_texto_digital_como_base)

        self.boton_copiar_revisado = QPushButton("Copiar texto revisado")
        self.boton_copiar_revisado.clicked.connect(self.copiar_texto_revisado)

        self.boton_guardar_revisado = QPushButton("Guardar texto revisado")
        self.boton_guardar_revisado.clicked.connect(self.guardar_texto_revisado)

        fila_botones.addWidget(self.boton_copiar_digital)
        fila_botones.addWidget(self.boton_usar_digital)
        fila_botones.addWidget(self.boton_copiar_revisado)
        fila_botones.addWidget(self.boton_guardar_revisado)
        fila_botones.addStretch()

        splitter = QSplitter(Qt.Horizontal)

        panel_digital = QWidget()
        layout_digital = QVBoxLayout(panel_digital)
        layout_digital.setContentsMargins(0, 0, 0, 0)
        layout_digital.setSpacing(6)

        label_digital = QLabel("Texto digital extraído")
        label_digital.setObjectName("etiqueta_seccion")

        self.texto_completo = QPlainTextEdit()
        self.texto_completo.setReadOnly(True)
        self.texto_completo.setPlaceholderText("Aquí se mostrará el texto digital extraído del documento.")

        layout_digital.addWidget(label_digital)
        layout_digital.addWidget(self.texto_completo)

        panel_revisado = QWidget()
        layout_revisado = QVBoxLayout(panel_revisado)
        layout_revisado.setContentsMargins(0, 0, 0, 0)
        layout_revisado.setSpacing(6)

        label_revisado = QLabel("Texto final revisado")
        label_revisado.setObjectName("etiqueta_seccion")

        descripcion_revisado = QLabel(
            "Edita aquí la versión final que usarás más adelante para extracción de campos."
        )
        descripcion_revisado.setObjectName("diagnostico_secundario")
        descripcion_revisado.setWordWrap(True)

        self.texto_revisado = QPlainTextEdit()
        self.texto_revisado.setPlaceholderText("Aquí podrás corregir y consolidar el texto final revisado.")
        self.texto_revisado.textChanged.connect(self._sincronizar_texto_revisado)

        layout_revisado.addWidget(label_revisado)
        layout_revisado.addWidget(descripcion_revisado)
        layout_revisado.addWidget(self.texto_revisado)

        splitter.addWidget(panel_digital)
        splitter.addWidget(panel_revisado)
        splitter.setSizes([520, 520])

        layout.addLayout(fila_botones)
        layout.addWidget(splitter, 1)

        return contenedor

    def _crear_tab_texto_ocr(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(10)

        self.boton_copiar_ocr = QPushButton("Copiar texto OCR")
        self.boton_copiar_ocr.clicked.connect(self.copiar_texto_ocr)

        self.boton_usar_ocr = QPushButton("Usar OCR como base")
        self.boton_usar_ocr.clicked.connect(self.usar_texto_ocr_como_base)

        fila_botones.addWidget(self.boton_copiar_ocr)
        fila_botones.addWidget(self.boton_usar_ocr)
        fila_botones.addStretch()

        label_ocr = QLabel("Texto OCR extraído")
        label_ocr.setObjectName("etiqueta_seccion")

        self.texto_ocr_completo = QPlainTextEdit()
        self.texto_ocr_completo.setReadOnly(True)
        self.texto_ocr_completo.setPlaceholderText("Aquí se mostrará el texto OCR obtenido del documento.")

        layout.addLayout(fila_botones)
        layout.addWidget(label_ocr)
        layout.addWidget(self.texto_ocr_completo, 1)

        return contenedor

    def _crear_tab_texto_por_pagina(self) -> QWidget:
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        fila_selector = QHBoxLayout()
        etiqueta_selector = QLabel("Página:")
        etiqueta_selector.setObjectName("etiqueta_seccion")

        self.selector_pagina = QComboBox()
        self.selector_pagina.currentIndexChanged.connect(self._mostrar_texto_pagina_seleccionada)

        fila_selector.addWidget(etiqueta_selector)
        fila_selector.addWidget(self.selector_pagina)
        fila_selector.addStretch()

        splitter = QSplitter(Qt.Horizontal)

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
        splitter.setSizes([520, 520])

        layout.addLayout(fila_selector)
        layout.addWidget(splitter, 1)

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

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile() and url.toLocalFile().lower().endswith(".pdf"):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    ruta_archivo = url.toLocalFile()
                    if ruta_archivo.lower().endswith(".pdf"):
                        self._procesar_pdf(ruta_archivo)
                        event.acceptProposedAction()
                        return

        self._mostrar_notificacion("El archivo soltado no es un PDF válido.", "error")
        event.ignore()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._actualizar_preview_escalado()

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

        self._procesar_pdf(ruta_archivo)

    def _procesar_pdf(self, ruta_archivo: str) -> None:
        if self.hilo_analisis is not None and self.hilo_analisis.isRunning():
            QMessageBox.information(
                self,
                "Procesamiento en curso",
                "Ya existe un procesamiento activo. Espera a que termine o cancélalo.",
            )
            return

        from monitor_recursos import MonitorRecursos

        limites = self._obtener_limites_desde_ui()
        modo = self.selector_modo.currentData()
        monitor = MonitorRecursos(limites)

        evaluacion_previa = monitor.evaluar_archivo_previo(ruta_archivo, modo)
        if evaluacion_previa["alertas"]:
            partes = evaluacion_previa["alertas"] + evaluacion_previa["recomendaciones"]
            mensaje = "\n".join(partes)

            respuesta = QMessageBox.warning(
                self,
                "Documento potencialmente pesado",
                f"{mensaje}\n\n¿Continuar con los límites actuales?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if respuesta != QMessageBox.Yes:
                self._mostrar_notificacion("Procesamiento cancelado antes de iniciar.", "alerta")
                return

            self._manejar_alerta_operativa(mensaje)

        self.input_ruta.setText(ruta_archivo)
        self._actualizar_progreso(0, "Preparando procesamiento...")
        self._mostrar_notificacion("Procesando documento seleccionado...", "alerta")

        self._habilitar_controles_operativos(False)

        self.dialogo_progreso = DialogoProgreso(ModoAnalisis.etiqueta(modo), self)

        self.hilo_analisis = QThread(self)
        self.trabajador_analisis = TrabajadorAnalisis(ruta_archivo, modo, limites)
        self.trabajador_analisis.moveToThread(self.hilo_analisis)

        self.hilo_analisis.started.connect(self.trabajador_analisis.ejecutar)
        self.trabajador_analisis.progreso.connect(self._actualizar_progreso)
        self.trabajador_analisis.progreso.connect(self.dialogo_progreso.actualizar_progreso)
        self.trabajador_analisis.etapa.connect(self.dialogo_progreso.actualizar_etapa)
        self.trabajador_analisis.alerta.connect(self._manejar_alerta_operativa)
        self.trabajador_analisis.alerta.connect(self.dialogo_progreso.mostrar_alerta_operativa)

        self.dialogo_progreso.solicitud_cancelar.connect(self.trabajador_analisis.cancelar)
        self.dialogo_progreso.solicitud_pausar.connect(self.trabajador_analisis.pausar)
        self.dialogo_progreso.solicitud_reanudar.connect(self.trabajador_analisis.reanudar)

        self.trabajador_analisis.finalizado.connect(self._manejar_resultado_analisis)
        self.trabajador_analisis.finalizado.connect(self.hilo_analisis.quit)

        self.trabajador_analisis.error.connect(self._manejar_error_analisis)
        self.trabajador_analisis.error.connect(self.hilo_analisis.quit)

        self.trabajador_analisis.cancelado.connect(self._manejar_cancelacion_analisis)
        self.trabajador_analisis.cancelado.connect(self.hilo_analisis.quit)

        self.trabajador_analisis.detenido_seguridad.connect(self._manejar_detencion_seguridad)
        self.trabajador_analisis.detenido_seguridad.connect(self.hilo_analisis.quit)

        self.hilo_analisis.finished.connect(self._limpiar_trabajo_activo)

        self.hilo_analisis.start()
        self.dialogo_progreso.exec()

    def _manejar_resultado_analisis(self, resultado_mostrado, resultado_basico, resultado_pro, comparacion) -> None:
        self.resultado_actual = resultado_mostrado
        self.resultado_basico_actual = resultado_basico
        self.resultado_pro_actual = resultado_pro
        self.comparacion_actual = comparacion

        self._mostrar_resultado(resultado_mostrado)
        self._actualizar_preview_pdf(resultado_mostrado.ruta_archivo)
        self._actualizar_estado_exportacion(True)
        self.boton_reextraer_campos.setEnabled(True)
        self._actualizar_progreso(100, "Procesamiento completado.")
        self._mostrar_notificacion("El documento fue analizado correctamente.", "ok")

        if resultado_mostrado.alertas_operativas:
            self._manejar_alerta_operativa(resultado_mostrado.alertas_operativas[-1])

        try:
            self.historial_analisis.guardar_registro(
                resultado_mostrado,
                resultado_basico=resultado_basico,
                resultado_pro=resultado_pro,
                comparacion=comparacion,
            )
            self.boton_exportar_excel_historial.setEnabled(True)
        except Exception as error:
            self._mostrar_notificacion(
                f"El análisis terminó, pero no se pudo guardar en historial. Detalle: {error}",
                "alerta",
            )

        if self.dialogo_progreso is not None:
            self.dialogo_progreso.finalizar(True)

        self._habilitar_controles_operativos(True)

    def _manejar_error_analisis(self, mensaje: str) -> None:
        self._actualizar_progreso(0, "Error durante el análisis.")
        self._mostrar_notificacion(mensaje, "error")

        if self.dialogo_progreso is not None:
            self.dialogo_progreso.finalizar(False)

        self._habilitar_controles_operativos(True)

        QMessageBox.critical(self, "Error inesperado", mensaje)

    def _manejar_cancelacion_analisis(self, mensaje: str) -> None:
        self._actualizar_progreso(0, "Procesamiento cancelado.")
        self._mostrar_notificacion(mensaje, "alerta")

        if self.dialogo_progreso is not None:
            self.dialogo_progreso.finalizar(False)

        self._habilitar_controles_operativos(True)

    def _limpiar_trabajo_activo(self) -> None:
        if self.trabajador_analisis is not None:
            self.trabajador_analisis.deleteLater()
            self.trabajador_analisis = None

        if self.hilo_analisis is not None:
            self.hilo_analisis.deleteLater()
            self.hilo_analisis = None

        self.dialogo_progreso = None

    def _actualizar_preview_pdf(self, ruta_archivo: str) -> None:
        self.pixmap_preview_original = None
        documento = None

        try:
            documento = fitz.open(ruta_archivo)
            if documento.page_count == 0:
                self.label_preview_pdf.setText("El PDF no contiene páginas.")
                return

            pagina = documento.load_page(0)
            matriz = fitz.Matrix(0.55, 0.55)
            pixmap = pagina.get_pixmap(matrix=matriz, alpha=False)

            formato = QImage.Format_RGB888
            if pixmap.n == 4:
                formato = QImage.Format_RGBA8888

            imagen = QImage(
                pixmap.samples,
                pixmap.width,
                pixmap.height,
                pixmap.stride,
                formato,
            ).copy()

            self.pixmap_preview_original = QPixmap.fromImage(imagen)
            self._actualizar_preview_escalado()
        except Exception as error:
            self.label_preview_pdf.setPixmap(QPixmap())
            self.label_preview_pdf.setText(f"No se pudo generar la vista previa.\n\n{error}")
        finally:
            if documento is not None:
                try:
                    documento.close()
                except Exception:
                    pass

    def _actualizar_preview_escalado(self) -> None:
        if not self.pixmap_preview_original:
            return

        ancho = max(220, self.label_preview_pdf.width() - 12)
        alto = max(260, self.label_preview_pdf.height() - 12)

        pixmap_escalado = self.pixmap_preview_original.scaled(
            ancho,
            alto,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.label_preview_pdf.setText("")
        self.label_preview_pdf.setPixmap(pixmap_escalado)

    def reextraer_campos_desde_texto_revisado(self) -> None:
        if self.resultado_actual is None:
            QMessageBox.information(self, "Sin resultados", "Primero debes analizar un documento.")
            return

        self._sincronizar_texto_revisado()

        try:
            from pipeline_documento import PipelineDocumento

            pipeline = PipelineDocumento()
            pipeline.reextraer_campos(self.resultado_actual, callback=self._actualizar_progreso)
            self._cargar_campos_extraidos(self.resultado_actual)
            self._actualizar_panel_modo_comparacion()
            self._mostrar_notificacion("Campos reextraídos desde el texto revisado.", "ok")
            self.statusBar().showMessage("Campos reextraídos correctamente.")
        except Exception as error:
            mensaje = f"No se pudo reextraer los campos. Detalle: {error}"
            self._mostrar_notificacion(mensaje, "error")
            QMessageBox.critical(self, "Error al reextraer campos", mensaje)

    def exportar_json(self) -> None:
        if self.resultado_actual is None:
            QMessageBox.information(self, "Sin resultados", "Primero debes analizar un documento.")
            return

        self._sincronizar_texto_revisado()
        ruta = self._solicitar_ruta_exportacion("json")
        if not ruta:
            return

        try:
            self.exportador.exportar_json(
                self.resultado_actual,
                ruta,
                resultado_basico=self.resultado_basico_actual,
                resultado_pro=self.resultado_pro_actual,
                comparacion=self.comparacion_actual,
            )
            self._mostrar_notificacion("Exportación JSON completada correctamente.", "ok")
            self.statusBar().showMessage(f"Archivo JSON guardado en: {ruta}")
        except Exception as error:
            mensaje = f"No se pudo exportar el archivo JSON. Detalle: {error}"
            self._mostrar_notificacion(mensaje, "error")
            QMessageBox.critical(self, "Error al exportar JSON", mensaje)

    def exportar_txt(self) -> None:
        if self.resultado_actual is None:
            QMessageBox.information(self, "Sin resultados", "Primero debes analizar un documento.")
            return

        self._sincronizar_texto_revisado()
        ruta = self._solicitar_ruta_exportacion("txt")
        if not ruta:
            return

        try:
            self.exportador.exportar_txt(
                self.resultado_actual,
                ruta,
                resultado_basico=self.resultado_basico_actual,
                resultado_pro=self.resultado_pro_actual,
                comparacion=self.comparacion_actual,
            )
            self._mostrar_notificacion("Exportación TXT completada correctamente.", "ok")
            self.statusBar().showMessage(f"Archivo TXT guardado en: {ruta}")
        except Exception as error:
            mensaje = f"No se pudo exportar el archivo TXT. Detalle: {error}"
            self._mostrar_notificacion(mensaje, "error")
            QMessageBox.critical(self, "Error al exportar TXT", mensaje)

    def exportar_excel_actual(self) -> None:
        if self.resultado_actual is None:
            QMessageBox.information(self, "Sin resultados", "Primero debes analizar un documento.")
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar análisis como Excel",
            f"analisis_{Path(self.resultado_actual.nombre_archivo).stem}.xlsx",
            "Archivos Excel (*.xlsx)",
        )

        if not ruta:
            return

        ruta_path = Path(ruta)
        if ruta_path.suffix.lower() != ".xlsx":
            ruta_path = ruta_path.with_suffix(".xlsx")

        try:
            self.exportador_excel.exportar_documento(
                self.resultado_actual,
                str(ruta_path),
                resultado_basico=self.resultado_basico_actual,
                resultado_pro=self.resultado_pro_actual,
                comparacion=self.comparacion_actual,
            )
            self._mostrar_notificacion("Exportación Excel del documento completada.", "ok")
            self.statusBar().showMessage(f"Archivo Excel guardado en: {ruta_path}")
        except Exception as error:
            mensaje = f"No se pudo exportar el Excel del documento. Detalle: {error}"
            self._mostrar_notificacion(mensaje, "error")
            QMessageBox.critical(self, "Error al exportar Excel", mensaje)

    def exportar_excel_historial(self) -> None:
        registros = self.historial_analisis.leer_registros()
        if not registros:
            QMessageBox.information(self, "Sin historial", "Aún no hay historial de análisis para exportar.")
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar historial como Excel",
            "historial_analisis.xlsx",
            "Archivos Excel (*.xlsx)",
        )

        if not ruta:
            return

        ruta_path = Path(ruta)
        if ruta_path.suffix.lower() != ".xlsx":
            ruta_path = ruta_path.with_suffix(".xlsx")

        try:
            self.exportador_excel.exportar_historial(registros, str(ruta_path))
            self._mostrar_notificacion("Exportación Excel del historial completada.", "ok")
            self.statusBar().showMessage(f"Historial Excel guardado en: {ruta_path}")
        except Exception as error:
            mensaje = f"No se pudo exportar el historial Excel. Detalle: {error}"
            self._mostrar_notificacion(mensaje, "error")
            QMessageBox.critical(self, "Error al exportar historial Excel", mensaje)

    def guardar_pdf_optimizado(self) -> None:
        resultado_pro = self.resultado_pro_actual
        if resultado_pro is None and self.resultado_actual is not None and self.resultado_actual.modo_analisis == ModoAnalisis.PRO:
            resultado_pro = self.resultado_actual

        if resultado_pro is None:
            QMessageBox.information(
                self,
                "Sin resultado PRO",
                "Necesitas ejecutar el modo Pro o Comparar ambos para guardar un PDF optimizado.",
            )
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar PDF optimizado",
            f"optimizado_{Path(resultado_pro.nombre_archivo).stem}.pdf",
            "Archivos PDF (*.pdf)",
        )

        if not ruta:
            return

        ruta_path = Path(ruta)
        if ruta_path.suffix.lower() != ".pdf":
            ruta_path = ruta_path.with_suffix(".pdf")

        try:
            self.guardador_pdf_pro.guardar_pdf_optimizado(resultado_pro, str(ruta_path))
            self._mostrar_notificacion("PDF optimizado guardado correctamente.", "ok")
            self.statusBar().showMessage(f"PDF optimizado guardado en: {ruta_path}")
        except Exception as error:
            mensaje = f"No se pudo guardar el PDF optimizado. Detalle: {error}"
            self._mostrar_notificacion(mensaje, "error")
            QMessageBox.critical(self, "Error al guardar PDF optimizado", mensaje)

    def _solicitar_ruta_exportacion(self, formato: str) -> str:
        if self.resultado_actual is None:
            return ""

        nombre_base = Path(self.resultado_actual.nombre_archivo).stem
        nombre_sugerido = f"analisis_{nombre_base}.{formato}"

        if formato == "json":
            filtro = "Archivos JSON (*.json)"
            titulo = "Guardar análisis como JSON"
        else:
            filtro = "Archivos de texto (*.txt)"
            titulo = "Guardar análisis como TXT"

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            titulo,
            nombre_sugerido,
            filtro,
        )

        if not ruta:
            return ""

        ruta_path = Path(ruta)
        if ruta_path.suffix.lower() != f".{formato}":
            ruta_path = ruta_path.with_suffix(f".{formato}")

        return str(ruta_path)

    def copiar_texto_digital(self) -> None:
        self._copiar_al_portapapeles(self.texto_completo.toPlainText(), "texto digital")

    def copiar_texto_ocr(self) -> None:
        self._copiar_al_portapapeles(self.texto_ocr_completo.toPlainText(), "texto OCR")

    def copiar_texto_revisado(self) -> None:
        self._copiar_al_portapapeles(self.texto_revisado.toPlainText(), "texto revisado")

    def usar_texto_digital_como_base(self) -> None:
        texto = self.texto_completo.toPlainText().strip()
        if not texto:
            QMessageBox.information(self, "Sin texto digital", "No hay texto digital disponible para usar como base.")
            return

        self.texto_revisado.blockSignals(True)
        self.texto_revisado.setPlainText(texto)
        self.texto_revisado.blockSignals(False)
        self._sincronizar_texto_revisado()
        self._mostrar_notificacion("Se cargó el texto digital como base del texto revisado.", "ok")

    def usar_texto_ocr_como_base(self) -> None:
        texto = self.texto_ocr_completo.toPlainText().strip()
        if not texto:
            QMessageBox.information(self, "Sin texto OCR", "No hay texto OCR disponible para usar como base.")
            return

        self.texto_revisado.blockSignals(True)
        self.texto_revisado.setPlainText(texto)
        self.texto_revisado.blockSignals(False)
        self._sincronizar_texto_revisado()
        self._mostrar_notificacion("Se cargó el texto OCR como base del texto revisado.", "ok")

    def guardar_texto_revisado(self) -> None:
        if self.resultado_actual is None:
            QMessageBox.information(self, "Sin resultados", "Primero debes analizar un documento.")
            return

        texto = self.texto_revisado.toPlainText().strip()
        if not texto:
            QMessageBox.information(self, "Sin texto revisado", "No hay texto revisado para guardar.")
            return

        nombre_base = Path(self.resultado_actual.nombre_archivo).stem
        nombre_sugerido = f"texto_revisado_{nombre_base}.txt"

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar texto revisado",
            nombre_sugerido,
            "Archivos de texto (*.txt)",
        )

        if not ruta:
            return

        ruta_path = Path(ruta)
        if ruta_path.suffix.lower() != ".txt":
            ruta_path = ruta_path.with_suffix(".txt")

        try:
            ruta_path.write_text(texto, encoding="utf-8")
            self._mostrar_notificacion("Texto revisado guardado correctamente.", "ok")
            self.statusBar().showMessage(f"Texto revisado guardado en: {ruta_path}")
        except Exception as error:
            mensaje = f"No se pudo guardar el texto revisado. Detalle: {error}"
            self._mostrar_notificacion(mensaje, "error")
            QMessageBox.critical(self, "Error al guardar texto revisado", mensaje)

    def _copiar_al_portapapeles(self, texto: str, descripcion: str) -> None:
        if not texto.strip():
            QMessageBox.information(self, "Sin contenido", f"No hay {descripcion} para copiar.")
            return

        QApplication.clipboard().setText(texto)
        self._mostrar_notificacion(f"Se copió el {descripcion} al portapapeles.", "ok")

    def _sincronizar_texto_revisado(self) -> None:
        if self.resultado_actual is not None:
            self.resultado_actual.texto_final_revisado = self.texto_revisado.toPlainText()

    def _actualizar_progreso(self, valor: int, mensaje: str) -> None:
        self.barra_progreso.setValue(max(0, min(100, valor)))
        self.label_progreso.setText(mensaje)
        self.statusBar().showMessage(mensaje)
        QApplication.processEvents()

    def _actualizar_estado_exportacion(self, habilitado: bool) -> None:
        self.boton_exportar_json.setEnabled(habilitado)
        self.boton_exportar_txt.setEnabled(habilitado)
        self.boton_exportar_excel_actual.setEnabled(habilitado)

        tiene_resultado_pro = False
        if self.resultado_pro_actual is not None:
            tiene_resultado_pro = True
        elif self.resultado_actual is not None and self.resultado_actual.modo_analisis == ModoAnalisis.PRO:
            tiene_resultado_pro = True

        self.boton_guardar_pdf_optimizado.setEnabled(habilitado and tiene_resultado_pro)
        self.boton_exportar_excel_historial.setEnabled(self.historial_analisis.existe_historial())

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

        if resultado.codigo_estado_ocr == "ejecutado":
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

        mapa_comparacion_paginas = {}
        if self.comparacion_actual is not None:
            for comparacion_pagina in self.comparacion_actual.comparaciones_paginas:
                mapa_comparacion_paginas[comparacion_pagina.numero_pagina] = comparacion_pagina

        self.tabla_paginas.setRowCount(0)

        for pagina in resultado.resumen_paginas:
            fila = self.tabla_paginas.rowCount()
            self.tabla_paginas.insertRow(fila)

            comparacion_pagina = mapa_comparacion_paginas.get(pagina.numero_pagina)

            score_basico = "-"
            score_pro = "-"
            ganador_pagina = "-"

            if comparacion_pagina is not None:
                score_basico = f"{comparacion_pagina.score_basico:.2f}"
                score_pro = f"{comparacion_pagina.score_pro:.2f}"
                ganador_pagina = comparacion_pagina.etiqueta_ganador or "-"

            dificultad = pagina.ocr_dificultad or "-"

            item_pagina = QTableWidgetItem(str(pagina.numero_pagina))
            item_texto = QTableWidgetItem("Sí" if pagina.tiene_texto else "No")
            item_caracteres = QTableWidgetItem(str(pagina.cantidad_caracteres))
            item_imagenes = QTableWidgetItem(str(pagina.cantidad_imagenes))
            item_cobertura = QTableWidgetItem(f"{pagina.cobertura_imagen * 100:.0f}%")
            item_diagnostico = QTableWidgetItem(f"{pagina.diagnostico} ({pagina.confianza}%)")
            item_dificultad = QTableWidgetItem(dificultad)
            item_score_basico = QTableWidgetItem(score_basico)
            item_score_pro = QTableWidgetItem(score_pro)
            item_ganador = QTableWidgetItem(ganador_pagina)

            tooltip_metricas = (
                f"Confianza OCR promedio: {pagina.ocr_confianza_promedio:.2f}\n"
                f"Confianza OCR mediana: {pagina.ocr_confianza_mediana:.2f}\n"
                f"Palabras detectadas: {pagina.ocr_cantidad_palabras}\n"
                f"Palabras baja confianza: {pagina.ocr_palabras_baja_confianza}\n"
                f"Caracteres OCR: {pagina.ocr_caracteres_totales}\n"
                f"Tiempo página: {pagina.ocr_tiempo_total_ms} ms\n"
                f"Intentos: {pagina.ocr_numero_intentos}\n"
                f"Variante: {pagina.ocr_variante_ganadora or '-'}\n"
                f"Dificultad: {pagina.ocr_dificultad or '-'}\n"
                f"Índice dificultad: {pagina.ocr_dificultad_indice}"
            )

            if pagina.ocr_observaciones:
                tooltip_metricas += "\nObservaciones:\n- " + "\n- ".join(pagina.ocr_observaciones)

            item_diagnostico.setToolTip(tooltip_metricas)
            item_dificultad.setToolTip(tooltip_metricas)

            if comparacion_pagina is not None:
                tooltip_comparacion = comparacion_pagina.motivo
                if comparacion_pagina.revision_manual_recomendada:
                    tooltip_comparacion += "\nRevisión manual recomendada."
                if comparacion_pagina.observaciones:
                    tooltip_comparacion += "\n" + "\n".join(comparacion_pagina.observaciones)

                item_ganador.setToolTip(tooltip_comparacion)

            item_pagina.setTextAlignment(Qt.AlignCenter)
            item_texto.setTextAlignment(Qt.AlignCenter)
            item_caracteres.setTextAlignment(Qt.AlignCenter)
            item_imagenes.setTextAlignment(Qt.AlignCenter)
            item_cobertura.setTextAlignment(Qt.AlignCenter)
            item_dificultad.setTextAlignment(Qt.AlignCenter)
            item_score_basico.setTextAlignment(Qt.AlignCenter)
            item_score_pro.setTextAlignment(Qt.AlignCenter)
            item_ganador.setTextAlignment(Qt.AlignCenter)

            self.tabla_paginas.setItem(fila, 0, item_pagina)
            self.tabla_paginas.setItem(fila, 1, item_texto)
            self.tabla_paginas.setItem(fila, 2, item_caracteres)
            self.tabla_paginas.setItem(fila, 3, item_imagenes)
            self.tabla_paginas.setItem(fila, 4, item_cobertura)
            self.tabla_paginas.setItem(fila, 5, item_diagnostico)
            self.tabla_paginas.setItem(fila, 6, item_dificultad)
            self.tabla_paginas.setItem(fila, 7, item_score_basico)
            self.tabla_paginas.setItem(fila, 8, item_score_pro)
            self.tabla_paginas.setItem(fila, 9, item_ganador)

        self._cargar_textos(resultado)
        self._cargar_campos_extraidos(resultado)
        self._actualizar_panel_modo_comparacion()

    def _cargar_textos(self, resultado) -> None:
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

        if not resultado.texto_final_revisado.strip():
            base_inicial = resultado.texto_completo.strip() or resultado.texto_ocr_completo.strip()
            resultado.texto_final_revisado = base_inicial

        self.texto_revisado.blockSignals(True)
        self.texto_revisado.setPlainText(resultado.texto_final_revisado)
        self.texto_revisado.blockSignals(False)

        for pagina in resultado.resumen_paginas:
            self.selector_pagina.addItem(f"Página {pagina.numero_pagina}")

        self.selector_pagina.blockSignals(False)

        if resultado.resumen_paginas:
            self.selector_pagina.setCurrentIndex(0)
            self._mostrar_texto_pagina(0)
        else:
            self.texto_pagina_digital.setPlainText("No hay páginas disponibles para mostrar.")
            self.texto_pagina_ocr.setPlainText("No hay páginas disponibles para mostrar.")

    def _cargar_campos_extraidos(self, resultado) -> None:
        self.label_fuente_extraccion.setText(
            f"Fuente de extracción: {resultado.texto_fuente_extraccion or '-'}"
        )

        self.tabla_campos.setRowCount(0)

        for campo in resultado.campos_extraidos:
            fila = self.tabla_campos.rowCount()
            self.tabla_campos.insertRow(fila)

            item_campo = QTableWidgetItem(campo.etiqueta)
            item_valor = QTableWidgetItem(campo.valor if campo.valor else "No detectado")
            item_estado = QTableWidgetItem("Detectado" if campo.detectado else "No detectado")
            item_estrategia = QTableWidgetItem(campo.estrategia)

            self.tabla_campos.setItem(fila, 0, item_campo)
            self.tabla_campos.setItem(fila, 1, item_valor)
            self.tabla_campos.setItem(fila, 2, item_estado)
            self.tabla_campos.setItem(fila, 3, item_estrategia)

    def _actualizar_panel_modo_comparacion(self) -> None:
        modo_solicitado = self.selector_modo.currentData()
        self.label_modo_solicitado.setText(ModoAnalisis.etiqueta(modo_solicitado))

        if self.resultado_actual is None:
            self.label_modo_ejecutado.setText("-")
            self.label_recomendacion_modo.setText("-")
            self.label_ganador_modo.setText("-")
            self.label_score_basico.setText("-")
            self.label_score_pro.setText("-")
            self.label_detalle_comparacion.setText("-")
            return

        self.label_modo_ejecutado.setText(self.resultado_actual.etiqueta_modo)
        self.label_recomendacion_modo.setText(self.resultado_actual.recomendacion_modo or "-")

        score_basico = "-"
        if self.resultado_basico_actual and self.resultado_basico_actual.metricas_documento_modo:
            score_basico = f"{self.resultado_basico_actual.metricas_documento_modo.score_total:.2f}"

        score_pro = "-"
        if self.resultado_pro_actual and self.resultado_pro_actual.metricas_documento_modo:
            score_pro = f"{self.resultado_pro_actual.metricas_documento_modo.score_total:.2f}"

        self.label_score_basico.setText(score_basico)
        self.label_score_pro.setText(score_pro)

        if self.comparacion_actual is not None:
            self.label_ganador_modo.setText(self.comparacion_actual.etiqueta_ganador or "-")

            detalle = self.comparacion_actual.motivo or "-"
            if self.comparacion_actual.revision_manual_recomendada and self.comparacion_actual.motivo_revision_manual:
                detalle += f"\n{self.comparacion_actual.motivo_revision_manual}"

            if self.comparacion_actual.observaciones:
                detalle += "\n" + "\n".join(self.comparacion_actual.observaciones)

            self.label_detalle_comparacion.setText(detalle)
        else:
            self.label_ganador_modo.setText("Sin comparación")
            metrica = self.resultado_actual.metricas_documento_modo
            if metrica is not None:
                detalle = (
                    f"Score total estimado: {metrica.score_total:.2f}\n"
                    f"Campos detectados: {metrica.cantidad_campos_detectados}\n"
                    f"Confianza OCR promedio: {metrica.confianza_ocr_promedio:.2f}\n"
                    f"Tiempo total: {metrica.tiempo_total_ms} ms"
                )
                if metrica.observaciones:
                    detalle += "\n" + "\n".join(metrica.observaciones)
                self.label_detalle_comparacion.setText(detalle)
            else:
                self.label_detalle_comparacion.setText("-")

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
                self.texto_pagina_ocr.setPlainText("OCR no fue necesario para esta página.")
            else:
                self.texto_pagina_ocr.setPlainText(
                    "OCR no se aplicó a esta página en esta ejecución."
                )

    def _limpiar_resultados(self) -> None:
        self.resultado_actual = None
        self.resultado_basico_actual = None
        self.resultado_pro_actual = None
        self.comparacion_actual = None

        self.valor_nombre.setText("-")
        self.valor_paginas.setText("-")
        self.valor_texto.setText("-")
        self.valor_ocr.setText("-")
        self.valor_diagnostico.setText("Sin análisis")
        self.valor_detalle_diagnostico.setText("No se pudo obtener información del documento.")
        self.valor_confianza_diagnostico.setText("Confianza estimada: -")
        self.valor_estado_ocr.setText("OCR no ejecutado")
        self.valor_detalle_ocr.setText("Sin preparación pendiente.")

        self.label_fuente_extraccion.setText("Fuente de extracción: -")
        self.label_modo_solicitado.setText("-")
        self.label_modo_ejecutado.setText("-")
        self.label_recomendacion_modo.setText("-")
        self.label_ganador_modo.setText("-")
        self.label_score_basico.setText("-")
        self.label_score_pro.setText("-")
        self.label_detalle_comparacion.setText("-")
        self.label_alerta_operativa.setText("Sin alertas operativas.")
        self.label_alerta_operativa.setObjectName("diagnostico_secundario")
        self.label_alerta_operativa.style().unpolish(self.label_alerta_operativa)
        self.label_alerta_operativa.style().polish(self.label_alerta_operativa)

        self.label_preview_pdf.setPixmap(QPixmap())
        self.label_preview_pdf.setText("Aún no hay vista previa disponible.")
        self.pixmap_preview_original = None

        self.texto_completo.setPlainText("")
        self.texto_ocr_completo.setPlainText("")
        self.texto_revisado.setPlainText("")
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
        self.tabla_campos.setRowCount(0)
        self.selector_pagina.clear()
        self._actualizar_estado_exportacion(False)
        self.boton_reextraer_campos.setEnabled(False)

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