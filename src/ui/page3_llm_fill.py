"""Page3 - 大模型填充页面"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QMessageBox
)

from workers.llm_fill_worker import LLMFillWorker


class Page3(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.llm_thread = None
        self._setup_ui()

    def set_input_file(self, path):
        self.excel_file_edit.setText(path)

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("请输入 API_KEY")
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("API_KEY:"))
        key_layout.addWidget(self.api_key_edit)
        layout.addLayout(key_layout)

        self.model_edit = QLineEdit()
        self.model_edit.setText("qwen3.5-flash")
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("MODEL:"))
        model_layout.addWidget(self.model_edit)
        layout.addLayout(model_layout)

        self.url_edit = QLineEdit()
        self.url_edit.setText("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)

        self.excel_file_edit = QLineEdit()
        self.excel_file_edit.setPlaceholderText("请选择 Excel 文件")
        excel_layout = QHBoxLayout()
        excel_layout.addWidget(QLabel("EXCEL_FILE:"))
        excel_layout.addWidget(self.excel_file_edit)
        self.btn_browse = QPushButton("浏览")
        self.btn_browse.clicked.connect(self._browse_excel)
        excel_layout.addWidget(self.btn_browse)
        layout.addLayout(excel_layout)

        self.btn_start = QPushButton("开始运行")
        self.btn_start.clicked.connect(self._start_llm_fill)
        layout.addWidget(self.btn_start)

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("日志输出区域...")
        layout.addWidget(self.log_edit)

        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("上一步")
        self.btn_prev.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        nav_layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton("下一步")
        self.btn_next.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        nav_layout.addWidget(self.btn_next)

        nav_layout.addStretch()
        layout.addLayout(nav_layout)

        self.setLayout(layout)

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

        self.llm_thread = LLMFillWorker(api_key, model, url, excel_file, output_file)
        self.llm_thread.text_written.connect(self._append_log)
        self.llm_thread.finished.connect(self._llm_finished)
        self.llm_thread.start()

    def _append_log(self, text):
        self.log_edit.append(text)

    def _llm_finished(self):
        self.btn_start.setEnabled(True)
        self.log_edit.append("\n【大模型填充完成】")