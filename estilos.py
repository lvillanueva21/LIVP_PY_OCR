ESTILOS_APP = """
QWidget {
    background-color: #f4f6f8;
    color: #1f2933;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #f4f6f8;
}

QGroupBox {
    border: 1px solid #d9e2ec;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 14px;
    background-color: #ffffff;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px 0 8px;
    color: #243b53;
}

QPushButton {
    background-color: #243b53;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 600;
    min-width: 140px;
}

QPushButton:hover {
    background-color: #334e68;
}

QPushButton:pressed {
    background-color: #102a43;
}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
    background-color: #ffffff;
    border: 1px solid #bcccdc;
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #486581;
}

QComboBox {
    padding-right: 24px;
}

QTableWidget {
    background-color: #ffffff;
    border: 1px solid #bcccdc;
    border-radius: 8px;
    gridline-color: #e3ecf3;
    selection-background-color: #d9e2ec;
    selection-color: #102a43;
    alternate-background-color: #f8fbfd;
}

QHeaderView::section {
    background-color: #e9eff5;
    color: #243b53;
    padding: 10px 8px;
    border: none;
    border-bottom: 1px solid #bcccdc;
    font-weight: 700;
}

QTabWidget::pane {
    border: 1px solid #d9e2ec;
    background-color: #ffffff;
    border-radius: 10px;
    top: -1px;
}

QTabBar::tab {
    background-color: #e9eff5;
    color: #334e68;
    padding: 10px 16px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    min-width: 140px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #102a43;
}

QProgressBar {
    border: 1px solid #bcccdc;
    border-radius: 7px;
    background-color: #ffffff;
    text-align: center;
    min-height: 18px;
}

QProgressBar::chunk {
    background-color: #243b53;
    border-radius: 6px;
}

QLabel#titulo_principal {
    font-size: 22px;
    font-weight: 700;
    color: #102a43;
}

QLabel#subtitulo {
    font-size: 12px;
    color: #486581;
}

QLabel#etiqueta_seccion {
    font-size: 12px;
    color: #486581;
    font-weight: 600;
}

QLabel#valor_principal {
    font-size: 14px;
    color: #102a43;
    font-weight: 600;
}

QLabel#estado_ok {
    color: #127a5b;
    font-weight: 700;
}

QLabel#estado_alerta {
    color: #b7791f;
    font-weight: 700;
}

QLabel#estado_error {
    color: #c53030;
    font-weight: 700;
}

QLabel#diagnostico_texto {
    font-size: 16px;
    font-weight: 700;
    color: #102a43;
}

QLabel#diagnostico_secundario {
    font-size: 12px;
    color: #486581;
    font-weight: 600;
}

QFrame#panel_notificacion {
    background-color: #ffffff;
    border: 1px solid #d9e2ec;
    border-radius: 12px;
}

QFrame#tarjeta_resumen {
    background-color: #f8fbfd;
    border: 1px solid #e3ecf3;
    border-radius: 10px;
}

QStatusBar {
    background-color: #e9eff5;
    color: #243b53;
}
"""