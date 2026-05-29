"""LLMFieldGenWorker 后台工作线程"""
import asyncio
import threading
from PyQt6.QtCore import QThread, QTimer, pyqtSignal, QObject

from core.llm_field_gen import llm_field_gen_async


class ThrottledPrinter(QObject):
    """带节流功能的日志输出，避免信号淹没GUI

    工作线程调用 print() → emit message_received（跨线程信号）
    主线程收到后启动 QTimer → 触发 _flush() → emit text_written
    保证 QTimer 只在主线程启停。
    """
    text_written = pyqtSignal(str)
    message_received = pyqtSignal()

    def __init__(self, interval_ms=100):
        super().__init__()
        self._buffer = []
        self._lock = threading.Lock()
        self._flush_requested = False

        self._timer = QTimer(self)
        self._timer.setInterval(interval_ms)
        self._timer.timeout.connect(self._flush)

        self.message_received.connect(self._schedule_flush)

    def print(self, text):
        with self._lock:
            self._buffer.append(text)
        self.message_received.emit()

    def _schedule_flush(self):
        """仅在主线程运行，安全启停 QTimer"""
        if not self._timer.isActive():
            self._timer.start()

    def _flush(self):
        with self._lock:
            output = '\n'.join(self._buffer) if self._buffer else ''
            self._buffer.clear()
            if not self._buffer:
                self._timer.stop()
        if output:
            self.text_written.emit(output)


class LLMFieldGenWorker(QThread):
    """LLM 数据字段生成工作线程"""
    text_written = pyqtSignal(str)

    def __init__(self, api_key, model, url, excel_file, output_file, ddl_context=None,
                 custom_system_prompt=None):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.url = url
        self.excel_file = excel_file
        self.output_file = output_file
        self.ddl_context = ddl_context
        self.custom_system_prompt = custom_system_prompt

        self._throttled_printer = ThrottledPrinter(interval_ms=100)
        self._throttled_printer.text_written.connect(self.text_written)

    def run(self):
        try:
            asyncio.run(llm_field_gen_async(
                self.api_key, self.model, self.url,
                self.excel_file, self.output_file,
                lambda text: self._throttled_printer.print(text),
                self.ddl_context,
                custom_system_prompt=self.custom_system_prompt,
            ))
        except Exception as e:
            # 捕获所有异常，输出到GUI而不是崩溃
            self._throttled_printer.print(f"\n❌ 程序异常: {str(e)}")
            self._throttled_printer.print("💡 请检查:")
            self._throttled_printer.print("  1) 输出文件是否被其他程序打开（如Excel）")
            self._throttled_printer.print("  2) 输入文件格式是否正确")
            self._throttled_printer.print("  3) API配置是否正确")
        finally:
            self._throttled_printer._timer.stop()
