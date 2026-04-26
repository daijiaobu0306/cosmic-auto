"""LLMFill 后台工作线程"""
import asyncio
import threading
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from core.llm_fill import llm_fill_async


class ThrottledPrinter(QObject):
    """带节流功能的日志输出，避免信号淹没GUI"""
    text_written = pyqtSignal(str)

    def __init__(self, interval=0.1):
        super().__init__()
        self.interval = interval
        self.buffer = []
        self.lock = threading.Lock()
        self._timer = None

    def print(self, text):
        with self.lock:
            self.buffer.append(text)
            if self._timer is None:
                self._timer = threading.Timer(self.interval, self._flush)
                self._timer.start()

    def _flush(self):
        with self.lock:
            output = '\n'.join(self.buffer) if self.buffer else ''
            self.buffer.clear()
            self._timer = None
        if output:
            self.text_written.emit(output)


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
        self._throttled_printer = ThrottledPrinter(interval=0.1)
        self._throttled_printer.text_written.connect(self.text_written.emit)
        try:
            asyncio.run(llm_fill_async(
                self.api_key, self.model, self.url,
                self.excel_file, self.output_file,
                lambda text: self._throttled_printer.print(text)
            ))
        finally:
            if self._throttled_printer._timer:
                self._throttled_printer._timer.cancel()