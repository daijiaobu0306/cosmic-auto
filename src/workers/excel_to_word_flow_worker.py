"""ExcelToWordFlow 后台工作线程（生成 Word 文档并插入流程图）

仅负责 QThread 生命周期管理，业务逻辑已移至 core/excel_to_word_flow.py
流程图使用纯 Python Pillow 渲染，无需 Node.js / mmdc，可直接打包为 exe。
"""
import sys
from PyQt6.QtCore import QThread, pyqtSignal, QObject

from core.excel_to_word_flow import excel_to_word_flow


class OutputRedirector(QObject):
    """重定向 stdout 为信号"""
    text_written = pyqtSignal(str)

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def write(self, text):
        if text.strip():
            self.callback(text)

    def flush(self):
        pass


class ExcelToWordFlowWorker(QThread):
    text_written = pyqtSignal(str)

    def __init__(self, excel_file: str, output_file: str, generate_flowchart: bool = True):
        super().__init__()
        self.excel_file = excel_file
        self.output_file = output_file
        self.generate_flowchart = generate_flowchart

    def run(self):
        old_stdout = sys.stdout
        sys.stdout = OutputRedirector(self._emit_output)
        try:
            excel_to_word_flow(
                self.excel_file,
                self.output_file,
                self.generate_flowchart,
                callback_print=self._emit_output,
            )
        finally:
            sys.stdout = old_stdout

    def _emit_output(self, text):
        self.text_written.emit(text)
