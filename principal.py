import sys

from PySide6.QtWidgets import QApplication

from estilos import ESTILOS_APP
from ventana_principal import VentanaPrincipal


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(ESTILOS_APP)

    ventana = VentanaPrincipal()
    ventana.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()