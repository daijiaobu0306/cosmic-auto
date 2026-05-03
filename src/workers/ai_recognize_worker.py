"""AI 识图后台工作线程"""
import asyncio
from PyQt6.QtCore import QThread, pyqtSignal

from core.ai_recognize import recognize_images_async, save_txt


class AIRecognizeWorker(QThread):
    """AI 识图工作线程"""
    text_written = pyqtSignal(str)
    finished_with_result = pyqtSignal(str)  # 完成时发送结果文本

    def __init__(self, image_folder, system_name, system_desc,
                 api_key, api_url, model_name, output_path):
        super().__init__()
        self.image_folder = image_folder
        self.system_name = system_name
        self.system_desc = system_desc
        self.api_key = api_key
        self.api_url = api_url
        self.model_name = model_name
        self.output_path = output_path

    def _emit_log(self, text):
        """直接发送日志信号"""
        self.text_written.emit(text)

    def run(self):
        try:
            self._emit_log("正在初始化...")

            result = asyncio.run(recognize_images_async(
                self.image_folder,
                self.system_name,
                self.system_desc,
                self.api_key,
                self.api_url,
                self.model_name,
                self._emit_log
            ))

            # 保存 TXT 文件
            self._emit_log(f"\n正在保存结果到: {self.output_path}")
            save_txt(result, self.output_path)
            self._emit_log(f"✅ 功能清单已保存: {self.output_path}")

            # 发送完成信号
            self.finished_with_result.emit(self.output_path)

        except Exception as e:
            self._emit_log(f"\n❌ 错误: {str(e)}")
