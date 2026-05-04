"""Page2 - 自动填空页面"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from workers.auto_fill_worker import AutoFillWorker
from .nav_bar import create_nav_bar


class Page2(QWidget):
    def __init__(self, navigator, on_success_callback):
        super().__init__()
        self.navigator = navigator
        self.on_success_callback = on_success_callback
        self.auto_fill_thread = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # 标题
        title = QLabel("自动填充")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            padding: 3px 0;
        """)
        layout.addWidget(title)

        # 副标题
        subtitle = QLabel("规则引擎填写 H/J/L 列")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 10px;
            color: #7f8c8d;
            padding-bottom: 3px;
        """)
        layout.addWidget(subtitle)

        file_layout = QHBoxLayout()
        file_label = QLabel("选择文件:")
        file_label.setStyleSheet("font-size: 11px; color: #495057; min-width: 70px;")
        file_layout.addWidget(file_label)
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("请选择 Excel 文件 (.xlsx)")
        self.file_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 11px;
                color: #2c3e50;
                background-color: white;
            }
            QLineEdit:focus { border-color: #3498db; }
        """)
        file_layout.addWidget(self.file_edit)
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
        self.btn_browse.clicked.connect(self._browse_file)
        file_layout.addWidget(self.btn_browse)
        layout.addLayout(file_layout)

        sheet_layout = QHBoxLayout()
        sheet_label = QLabel("定位 Sheet 表:")
        sheet_label.setStyleSheet("font-size: 11px; color: #495057; min-width: 70px;")
        sheet_layout.addWidget(sheet_label)
        self.sheet_edit = QLineEdit()
        self.sheet_edit.setText("cosmic模块汇总")
        self.sheet_edit.setPlaceholderText("请输入 Sheet 名称")
        self.sheet_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 11px;
                color: #2c3e50;
                background-color: white;
            }
            QLineEdit:focus { border-color: #3498db; }
        """)
        sheet_layout.addWidget(self.sheet_edit)
        layout.addLayout(sheet_layout)

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
        self.btn_start.clicked.connect(self._start_auto_fill)
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

        nav = create_nav_bar(self.navigator, self)
        layout.addLayout(nav)
        self.setLayout(layout)

    def _browse_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择 Excel 文件", "", "Excel Files (*.xlsx)")
        if path:
            self.file_edit.setText(path)

    def _start_auto_fill(self):
        file_path = self.file_edit.text().strip()
        sheet_name = self.sheet_edit.text().strip()

        if not file_path:
            QMessageBox.warning(self, "警告", "请选择 Excel 文件")
            return
        if not sheet_name:
            QMessageBox.warning(self, "警告", "请输入 Sheet 名称")
            return

        self.log_edit.clear()
        self.btn_start.setEnabled(False)

        self.auto_fill_thread = AutoFillWorker(file_path, sheet_name)
        self.auto_fill_thread.text_written.connect(self._append_log)
        self.auto_fill_thread.finished.connect(self._auto_fill_finished)
        self.auto_fill_thread.start()

    def _append_log(self, text):
        self.log_edit.append(text)

    def _auto_fill_finished(self):
        self.btn_start.setEnabled(True)
        self.on_success_callback()
        self.log_edit.append("\n【自动填空完成】")