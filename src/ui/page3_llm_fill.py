"""Page3 - 大模型填充页面"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize

from workers.llm_fill_worker import LLMFillWorker
from core.prompt_manager import load_prompts
from .prompt_edit_dialog import PromptEditDialog
from .nav_bar import create_nav_bar

# 右上角按钮通用样式
_PROMPT_BTN_STYLE = """
    QPushButton {
        background-color: white;
        color: #495057;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        font-size: 11px;
        padding: 4px 12px;
    }
    QPushButton:hover {
        background-color: #f8f9fa;
        border-color: #adb5bd;
    }
    QPushButton:pressed {
        background-color: #e9ecef;
    }
"""


class Page3(QWidget):
    def __init__(self, navigator):
        super().__init__()
        self.navigator = navigator
        self.llm_thread = None
        self._setup_ui()

    def set_input_file(self, path):
        self.excel_file_edit.setText(path)

    def resizeEvent(self, event):
        """窗口大小变化时，重新定位标题、副标题和按钮"""
        super().resizeEvent(event)
        w = self.width()
        btn_w = self.prompt_btn.sizeHint().width()
        # 标题居中（相对于整个窗口宽度）
        title_w = self._title.sizeHint().width()
        self._title.setGeometry((w - title_w) // 2, 15, title_w, 24)
        # 副标题居中（和标题对齐）
        sub_w = self._subtitle.sizeHint().width()
        self._subtitle.setGeometry((w - sub_w) // 2, 38, sub_w, 16)
        # 按钮贴右上角
        self.prompt_btn.move(w - btn_w - 10, 12)

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # 标题（绝对定位，保证在整个窗口宽度内居中）
        self._title = QLabel("LLM 填充", self)
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            background: transparent;
        """)

        # 副标题（绝对定位，和标题一起居中）
        self._subtitle = QLabel("大模型填写 M 列（可选 DDL 辅助）", self)
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._subtitle.setStyleSheet("""
            font-size: 10px;
            color: #7f8c8d;
            background: transparent;
        """)

        # 右上角按钮（绝对定位）
        self.prompt_btn = QPushButton("自定义提示词", self)
        self.prompt_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prompt_btn.setStyleSheet(_PROMPT_BTN_STYLE)
        self.prompt_btn.clicked.connect(self._open_prompt_dialog)

        # 顶部留出空间给标题和副标题
        layout.addSpacing(55)

        input_style = """
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 11px;
                color: #2c3e50;
                background-color: white;
            }
            QLineEdit:focus { border-color: #3498db; }
        """

        label_style = "font-size: 11px; color: #495057; min-width: 80px;"

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("请输入 API_KEY")
        self.api_key_edit.setStyleSheet(input_style)
        key_layout = QHBoxLayout()
        key_label = QLabel("API_KEY:")
        key_label.setStyleSheet(label_style)
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.api_key_edit)
        layout.addLayout(key_layout)

        self.model_edit = QLineEdit()
        self.model_edit.setText("qwen3.5-flash")
        self.model_edit.setStyleSheet(input_style)
        model_layout = QHBoxLayout()
        model_label = QLabel("MODEL:")
        model_label.setStyleSheet(label_style)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_edit)
        layout.addLayout(model_layout)

        self.url_edit = QLineEdit()
        self.url_edit.setText("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
        self.url_edit.setStyleSheet(input_style)
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        url_label.setStyleSheet(label_style)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)

        self.excel_file_edit = QLineEdit()
        self.excel_file_edit.setPlaceholderText("请选择 Excel 文件")
        self.excel_file_edit.setStyleSheet(input_style)
        excel_layout = QHBoxLayout()
        excel_label = QLabel("EXCEL_FILE:")
        excel_label.setStyleSheet(label_style)
        excel_layout.addWidget(excel_label)
        excel_layout.addWidget(self.excel_file_edit)
        self.btn_browse = QPushButton("浏览")
        self.btn_browse.setMinimumSize(60, 28)
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #d5dbdb; }
        """)
        self.btn_browse.clicked.connect(self._browse_excel)
        excel_layout.addWidget(self.btn_browse)
        layout.addLayout(excel_layout)

        self.btn_start = QPushButton("开始运行")
        self.btn_start.setMinimumSize(100, 30)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """)
        self.btn_start.clicked.connect(self._start_llm_fill)
        layout.addWidget(self.btn_start, 0, Qt.AlignmentFlag.AlignCenter)

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("日志输出区域...")
        self.log_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 10px;
                color: #495057;
                padding: 6px;
            }
        """)
        layout.addWidget(self.log_edit, 1)

        nav = create_nav_bar(self.navigator, self)
        layout.addLayout(nav)

        self.setLayout(layout)

    def _open_prompt_dialog(self):
        """打开自定义提示词编辑对话框"""
        dialog = PromptEditDialog("llm_fill", self)
        dialog.exec()

    def _browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 Excel 文件", "", "Excel Files (*.xlsx)")
        if path:
            self.excel_file_edit.setText(path)

    def _start_llm_fill(self):
        api_key = self.api_key_edit.text().strip()
        model = self.model_edit.text().strip()
        url = self.url_edit.text().strip()
        excel_file = self.excel_file_edit.text().strip()

        if not api_key:
            QMessageBox.warning(self, "警告", "请输入 API_KEY")
            return
        if not excel_file:
            QMessageBox.warning(self, "警告", "请选择 Excel 文件")
            return

        output_file = "大模型填充后.xlsx"
        self.log_edit.clear()
        self.btn_start.setEnabled(False)

        # 读取自定义提示词
        prompts = load_prompts()
        custom_sys = prompts.get("llm_fill", {}).get("system_prompt")

        self.llm_thread = LLMFillWorker(api_key, model, url, excel_file, output_file,
                                         custom_system_prompt=custom_sys)
        self.llm_thread.text_written.connect(self._append_log)
        self.llm_thread.finished.connect(self._llm_finished)
        self.llm_thread.start()

    def _append_log(self, text):
        self.log_edit.append(text)

    def _llm_finished(self):
        self.btn_start.setEnabled(True)
        self.log_edit.append("\n【大模型填充完成】")