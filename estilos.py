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
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 12px;
    background-color: #ffffff;
    font-weight: 600;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px 0 6px;
    color: #334e68;
}

QPushButton {
    background-color: #243b53;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #334e68;
}

QPushButton:pressed {
    background-color: #102a43;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    border: 1px solid #bcccdc;
    border-radius: 8px;
    padding: 8px;
    selection-background-color: #486581;
}

QTableWidget {
    background-color: #ffffff;
    border: 1px solid #bcccdc;
    border-radius: 8px;
    gridline-color: #d9e2ec;
    selection-background-color: #d9e2ec;
    selection-color: #102a43;
}

QHeaderView::section {
    background-color: #e9eff5;
    color: #243b53;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #bcccdc;
    font-weight: 600;
}

QLabel#titulo_principal {
    font-size: 20px;
    font-weight: 700;
    color: #102a43;
}

QLabel#subtitulo {
    font-size: 12px;
    color: #486581;
}

QLabel#estado_ok {
    color: #127a5b;
    font-weight: 600;
}

QLabel#estado_alerta {
    color: #b7791f;
    font-weight: 600;
}

QLabel#estado_error {
    color: #c53030;
    font-weight: 600;
}

QFrame#panel_notificacion {
    background-color: #ffffff;
    border: 1px solid #d9e2ec;
    border-radius: 10px;
}

QStatusBar {
    background-color: #e9eff5;
    color: #243b53;
}
"""