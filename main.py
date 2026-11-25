import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    fenster = MainWindow()
    fenster.show()
    sys.exit(app.exec())