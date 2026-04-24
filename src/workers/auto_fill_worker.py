"""AutoFill 后台工作线程"""
import sys
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from core.auto_fill import auto_fill


class OutputRedirector(QObject):
    """输出重定向"""
    text_written = pyqtSignal(str)

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def write(self, text):
        if text.strip():
            self.callback(text)

    def flush(self):
        pass


class AutoFillWorker(QThread):
    """自动填空工作线程"""
    text_written = pyqtSignal(str)

    def __init__(self, file_path, sheet_name):
        super().__init__()
        self.file_path = file_path
        self.sheet_name = sheet_name

    def run(self):
        old_stdout = sys.stdout
        sys.stdout = OutputRedirector(self._emit_output)
        try:
            auto_fill(self.file_path, self.sheet_name)
        finally:
            sys.stdout = old_stdout

    def _emit_output(self, text):
        self.text_written.emit(text)