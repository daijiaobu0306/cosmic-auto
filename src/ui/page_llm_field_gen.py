"""Page - LLM 数据字段生成页面（模块五）"""
import os
import subprocess
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt

from core.ddl_parser import parse_ddl_folder, build_ddl_context, format_ddl_summary
from workers.llm_field_gen_worker import LLMFieldGenWorker
from .nav_bar import create_nav_bar


class PageLLMFieldGen(QWidget):
    def __init__(self, navigator):
        super().__init__()
        self.navigator = navigator
        self.llm_thread = None
        self._ddl_context = None
        self._setup_ui()

    def set_input_file(self, path):
        self.excel_file_edit.setText(path)

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        title = QLabel("LLM 数据字段生成")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            padding: 3px 0;
        """)
        layout.addWidget(title)

        subtitle = QLabel("根据 L 列数据组名称，调用大模型生成 M 列数据字段（支持 DDL 辅助）")
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

        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("请输入 API_KEY")
        self.api_key_edit.setStyleSheet(input_style)
        key_layout = QHBoxLayout()
        key_label = QLabel("API_KEY:")
        key_label.setStyleSheet(label_style)
        key_layout.addWidget(key_label)
        key_layout.addWidget(self.api_key_edit)
        layout.addLayout(key_layout)

        # Model
        self.model_edit = QLineEdit()
        self.model_edit.setText("qwen3.5-flash")
        self.model_edit.setStyleSheet(input_style)
        model_layout = QHBoxLayout()
        model_label = QLabel("MODEL:")
        model_label.setStyleSheet(label_style)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_edit)
        layout.addLayout(model_layout)

        # URL
        self.url_edit = QLineEdit()
        self.url_edit.setText("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions")
        self.url_edit.setStyleSheet(input_style)
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        url_label.setStyleSheet(label_style)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_edit)
        layout.addLayout(url_layout)

        # Excel File
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

        # DDL 辅助区域
        ddl_group = QGroupBox("建表语句辅助（可选）")
        ddl_group.setCheckable(True)
        ddl_group.setChecked(False)
        ddl_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                color: #495057;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 14px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 2px 6px;
            }
        """)
        ddl_layout = QVBoxLayout()

        ddl_folder_layout = QHBoxLayout()
        ddl_folder_label = QLabel("DDL文件夹:")
        ddl_folder_label.setStyleSheet(label_style)
        ddl_folder_layout.addWidget(ddl_folder_label)
        self.ddl_folder_edit = QLineEdit()
        self.ddl_folder_edit.setPlaceholderText("包含 .sql 文件的文件夹路径")
        self.ddl_folder_edit.setStyleSheet(input_style)
        ddl_folder_layout.addWidget(self.ddl_folder_edit)
        self.btn_ddl_folder = QPushButton("浏览")
        self.btn_ddl_folder.setMinimumSize(60, 28)
        self.btn_ddl_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ddl_folder.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #d5dbdb; }
        """)
        self.btn_ddl_folder.clicked.connect(self._browse_ddl_folder)
        ddl_folder_layout.addWidget(self.btn_ddl_folder)
        ddl_layout.addLayout(ddl_folder_layout)

        self.btn_ddl_load = QPushButton("加载建表语句")
        self.btn_ddl_load.setMinimumSize(100, 28)
        self.btn_ddl_load.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ddl_load.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        self.btn_ddl_load.clicked.connect(self._load_ddl)
        ddl_layout.addWidget(self.btn_ddl_load, 0, Qt.AlignmentFlag.AlignLeft)

        self.ddl_status = QLabel("未加载")
        self.ddl_status.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        ddl_layout.addWidget(self.ddl_status)

        ddl_group.setLayout(ddl_layout)
        layout.addWidget(ddl_group)

        # Start Button
        self.btn_start = QPushButton("开始生成")
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
        self.btn_start.clicked.connect(self._start_gen)
        layout.addWidget(self.btn_start, 0, Qt.AlignmentFlag.AlignCenter)

        # 打开文件按钮（初始隐藏）
        self.btn_open_file = QPushButton("打开生成文件")
        self.btn_open_file.setMinimumSize(120, 30)
        self.btn_open_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_file.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        self.btn_open_file.clicked.connect(self._open_output_file)
        self.btn_open_file.hide()
        layout.addWidget(self.btn_open_file, 0, Qt.AlignmentFlag.AlignCenter)

        # Log Area
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

        # Navigation
        nav = create_nav_bar(self.navigator, self)
        layout.addLayout(nav)

        self.setLayout(layout)

    def _browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 Excel 文件", "", "Excel Files (*.xlsx)")
        if path:
            self.excel_file_edit.setText(path)

    def _browse_ddl_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择 DDL 文件夹")
        if folder:
            self.ddl_folder_edit.setText(folder)

    def _load_ddl(self):
        folder = self.ddl_folder_edit.text().strip()
        if not folder:
            QMessageBox.warning(self, "警告", "请先选择 DDL 文件夹")
            return
        try:
            tables = parse_ddl_folder(folder)
            if tables:
                self._ddl_context = build_ddl_context(tables)
                summary = format_ddl_summary(tables)
                self.ddl_status.setText(summary)
                self.ddl_status.setStyleSheet("font-size: 10px; color: #27ae60;")
            else:
                self._ddl_context = None
                self.ddl_status.setText("未找到有效的 CREATE TABLE 语句")
                self.ddl_status.setStyleSheet("font-size: 10px; color: #e74c3c;")
        except Exception as e:
            self._ddl_context = None
            self.ddl_status.setText(f"解析失败: {str(e)}")
            self.ddl_status.setStyleSheet("font-size: 10px; color: #e74c3c;")

    def _start_gen(self):
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

        output_file = "LLM数据字段生成.xlsx"
        self._output_file = output_file
        self.log_edit.clear()
        self.btn_start.setEnabled(False)
        self.btn_open_file.hide()

        if self._ddl_context:
            self.log_edit.append("📎 已加载 DDL 上下文，将参考数据库表结构生成字段\n")

        self.llm_thread = LLMFieldGenWorker(api_key, model, url, excel_file, output_file, self._ddl_context)
        self.llm_thread.text_written.connect(self._append_log)
        self.llm_thread.finished.connect(self._on_finished)
        self.llm_thread.start()

    def _append_log(self, text):
        self.log_edit.append(text)

    def _on_finished(self):
        self.btn_start.setEnabled(True)
        self.log_edit.append("\n【数据字段生成完成】")
        if hasattr(self, '_output_file') and os.path.exists(self._output_file):
            self.btn_open_file.show()

    def _open_output_file(self):
        """打开生成的文件"""
        if not hasattr(self, '_output_file') or not os.path.exists(self._output_file):
            QMessageBox.warning(self, "警告", "生成文件不存在")
            return

        try:
            if sys.platform == 'win32':
                os.startfile(self._output_file)
            elif sys.platform == 'darwin':
                subprocess.run(['open', self._output_file])
            else:
                subprocess.run(['xdg-open', self._output_file])
        except Exception as e:
            QMessageBox.warning(self, "警告", f"无法打开文件: {str(e)}")
