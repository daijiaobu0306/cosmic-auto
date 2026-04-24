"""LLMFill 后台工作线程"""
import sys
import asyncio
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from core.llm_fill import llm_fill_async


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


class LLMFillWorker(QThread):
    """大模型填充工作线程"""
    text_written = pyqtSignal(str)

    def __init__(self, api_key, model, url, excel_file, output_file):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.url = url
        self.excel_file = excel_file
        self.output_file = output_file

    def run(self):
        old_stdout = sys.stdout
        sys.stdout = OutputRedirector(self._emit_output)
        try:
            asyncio.run(llm_fill_async(
                self.api_key, self.model, self.url,
                self.excel_file, self.output_file,
                lambda text: self.text_written.emit(text)
            ))
        finally:
            sys.stdout = old_stdout

    def _emit_output(self, text):
        self.text_written.emit(text)