"""COSMIC 自动化工具 - 主入口"""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

from ui.main_window import MainWindow
from utils.resource_path import resource_path


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("ui/应用图标.png")))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())