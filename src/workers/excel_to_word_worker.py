"""ExcelToWord 后台工作线程

仅负责 QThread 生命周期管理，业务逻辑已移至 core/excel_to_word.py
"""
import sys
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from core.excel_to_word import excel_to_word


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


class ExcelToWordWorker(QThread):
    """Excel转Word工作线程"""
    text_written = pyqtSignal(str)

    def __init__(self, excel_file, output_file):
        super().__init__()
        self.excel_file = excel_file
        self.output_file = output_file

    def run(self):
        old_stdout = sys.stdout
        sys.stdout = OutputRedirector(self._emit_output)
        try:
            excel_to_word(
                self.excel_file,
                self.output_file,
                callback_print=self._emit_output,
            )
        finally:
            sys.stdout = old_stdout

    def _emit_output(self, text):
        self.text_written.emit(text)
