"""COSMIC 自动化工具 - 主入口"""
import sys
import requests
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer

from ui.main_window import MainWindow
from utils.resource_path import resource_path

TRACK_URL = "http://120.55.98.247:5000/track"


def track_visit():
    try:
        requests.get(TRACK_URL, timeout=2)
    except Exception:
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("ui/应用图标.png")))
    window = MainWindow()
    window.show()
    QTimer.singleShot(1000, track_visit)
    sys.exit(app.exec())