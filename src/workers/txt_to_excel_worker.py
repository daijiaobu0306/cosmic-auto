"""模块三 Worker：TXT → Excel（后台线程）"""

import sys
from PyQt6.QtCore import QThread, pyqtSignal
from core.txt_to_excel import parse_txt, generate_excel


class TxtToExcelWorker(QThread):
    """在后台线程中执行 TXT 解析 + Excel 生成。"""

    text_written = pyqtSignal(str)
    finished_with_result = pyqtSignal(str)

    def __init__(self, txt_path: str, system_name: str, output_path: str):
        super().__init__()
        self._txt_path = txt_path
        self._system_name = system_name
        self._output_path = output_path

    def run(self):
        old_stdout = sys.stdout
        sys.stdout = self._create_redirector()
        try:
            print(f"开始读取 TXT 文件: {self._txt_path}")
            with open(self._txt_path, 'r', encoding='utf-8') as f:
                txt_content = f.read()

            print("正在解析功能清单...")
            parsed_data = parse_txt(txt_content)

            if not parsed_data:
                print("[错误] 未能从 TXT 中解析出任何功能过程。请检查文件格式。")
                return

            level2_count = len(set(item['level2'] for item in parsed_data))
            level3_count = len(set((item['level2'], item['level3']) for item in parsed_data))
            process_count = len(parsed_data)
            print(f"解析完成: {level2_count} 个二级功能, {level3_count} 个三级功能, {process_count} 个功能过程")

            total_rows = process_count * 4  # 每个功能过程 4 行 (E/R/W/X)
            print(f"将生成 {total_rows} 行数据（每个功能过程 4 行: E/R/W/X）")

            print("正在生成 Excel...")
            result_path = generate_excel(parsed_data, self._system_name, self._output_path)

            print(f"Excel 生成完成: {result_path}")
            self.finished_with_result.emit(result_path)

        except FileNotFoundError:
            print(f"[错误] 找不到 TXT 文件: {self._txt_path}")
        except Exception as e:
            print(f"[错误] 生成 Excel 失败: {e}")
        finally:
            sys.stdout = old_stdout

    def _emit_output(self, text: str):
        if text and text.strip():
            self.text_written.emit(text)

    def _create_redirector(self):
        redirector = _OutputRedirector()
        redirector.callback = self._emit_output
        return redirector


class _OutputRedirector:
    """重定向 stdout 到信号。"""

    def __init__(self):
        self.callback = None

    def write(self, text: str):
        if text and text.strip() and self.callback:
            self.callback(text)

    def flush(self):
        pass
