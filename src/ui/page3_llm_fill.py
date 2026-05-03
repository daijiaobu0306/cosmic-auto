"""Page3 - 大模型填充页面"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

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
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # 标题
        title = QLabel("LLM 填充")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            padding: 3px 0;
        """)
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel("大模型填写 M 列（可选 DDL 辅助）")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 10px;
            color: #7f8c8d;
            padding-bottom: 3px;
        """)
        layout.addWidget(subtitle)

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
        self.btn_browse.setFixedSize(60, 28)
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
        self.btn_start.setFixedSize(100, 30)
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
        layout.addWidget(self.log_edit)

        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("上一步")
        self.btn_prev.setFixedSize(80, 28)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #d5dbdb; }
        """)
        self.btn_prev.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(4))
        nav_layout.addWidget(self.btn_prev)

        nav_layout.addStretch()

        self.btn_next = QPushButton("下一步")
        self.btn_next.setFixedSize(80, 28)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.btn_next.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(6))
        nav_layout.addWidget(self.btn_next)

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