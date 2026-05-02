"""Page4 - Excel转Word页面"""
import os
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt

from workers.excel_to_word_worker import ExcelToWordWorker


class Page4(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.excel_to_word_thread = None
        self._setup_ui()

    def _setup_ui(self):
        # 设置整体背景
        self.setStyleSheet("background-color: #f5f5f5;")

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 容器框架 - 固定宽度600px，水平居中
        container = QFrame()
        container.setFixedWidth(600)
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # 主标题
        title = QLabel("Excel 转 Word")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 24px;
        """)
        container_layout.addWidget(title)

        # 副标题
        subtitle = QLabel("将 COSMIC 表格转换为 Word 文档")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 18px;
            font-weight: 400;
            color: #6b7280;
            margin-bottom: 48px;
        """)
        container_layout.addWidget(subtitle)

        # 文件选择区域
        file_section = QFrame()
        file_layout = QVBoxLayout()
        file_layout.setSpacing(24)

        # Excel 文件选择行
        excel_row = QHBoxLayout()
        excel_row.setSpacing(16)

        self.excel_file_edit = QLineEdit()
        self.excel_file_edit.setPlaceholderText("请选择 Excel 文件")
        self.excel_file_edit.setFixedHeight(44)
        self.excel_file_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 16px;
                padding: 0 12px;
                background-color: white;
            }
        """)
        excel_row.addWidget(self.excel_file_edit)

        self.btn_browse = QPushButton("浏览")
        self.btn_browse.setFixedSize(80, 44)
        self.btn_browse.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        self.btn_browse.clicked.connect(self._browse_excel)
        excel_row.addWidget(self.btn_browse)

        file_layout.addLayout(excel_row)

        # 文件选择标签
        file_hint = QLabel("请选择已完成填充的 Excel 文件（.xlsx）")
        file_hint.setStyleSheet("font-size: 14px; color: #9ca3af;")
        file_layout.addWidget(file_hint)

        file_section.setLayout(file_layout)
        container_layout.addWidget(file_section)

        # 与按钮的间距
        container_layout.addSpacing(48)

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(16)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_convert = QPushButton("开始转换")
        self.btn_convert.setFixedSize(160, 44)
        self.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convert.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:disabled {
                background-color: #93c5fd;
            }
        """)
        self.btn_convert.clicked.connect(self._start_convert)
        btn_layout.addWidget(self.btn_convert)

        container_layout.addLayout(btn_layout)

        # 与日志的间距
        container_layout.addSpacing(32)

        # 日志区域
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("日志输出区域...")
        self.log_edit.setFixedHeight(160)
        self.log_edit.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                font-size: 14px;
                padding: 12px;
                background-color: white;
                line-height: 24px;
            }
        """)
        container_layout.addWidget(self.log_edit)

        # 与底部导航的间距
        container_layout.addSpacing(32)

        # 底部导航按钮
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(16)

        self.btn_prev = QPushButton("← 上一步")
        self.btn_prev.setFixedSize(160, 44)
        self.btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_prev.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                color: #374151;
                border: none;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)
        self.btn_prev.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        nav_layout.addWidget(self.btn_prev)

        nav_layout.addStretch()

        self.btn_open_folder = QPushButton("📂 打开所在目录")
        self.btn_open_folder.setFixedSize(160, 44)
        self.btn_open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:disabled {
                background-color: #6ee7b7;
            }
        """)
        self.btn_open_folder.clicked.connect(self._open_output_folder)
        self.btn_open_folder.setEnabled(False)
        nav_layout.addWidget(self.btn_open_folder)

        container_layout.addLayout(nav_layout)

        container.setLayout(container_layout)
        main_layout.addWidget(container)

        self.setLayout(main_layout)

    def _browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 Excel 文件", "", "Excel Files (*.xlsx)"
        )
        if path:
            self.excel_file_edit.setText(path)

    def _start_convert(self):
        excel_file = self.excel_file_edit.text().strip()

        if not excel_file:
            QMessageBox.warning(self, "警告", "请选择 Excel 文件")
            return

        # 自动生成输出文件名：原文件名_转换后.docx
        base_name = os.path.splitext(os.path.basename(excel_file))[0]
        output_dir = os.path.dirname(excel_file)
        if not output_dir:
            output_dir = "."
        self.output_file = os.path.join(output_dir, f"{base_name}_转换后.docx")

        self.log_edit.clear()
        self.btn_convert.setEnabled(False)
        self.btn_open_folder.setEnabled(False)
        self.log_edit.append(f"开始转换...\n输入文件: {excel_file}\n输出文件: {self.output_file}\n")

        self.excel_to_word_thread = ExcelToWordWorker(excel_file, self.output_file)
        self.excel_to_word_thread.text_written.connect(self._append_log)
        self.excel_to_word_thread.finished.connect(self._convert_finished)
        self.excel_to_word_thread.start()

    def _append_log(self, text):
        self.log_edit.append(text)

    def _convert_finished(self):
        self.btn_convert.setEnabled(True)
        self.btn_open_folder.setEnabled(True)
        self.log_edit.append("\n【转换完成】")

    def _open_output_folder(self):
        if hasattr(self, 'output_file') and os.path.exists(self.output_file):
            subprocess.run(['explorer', '/select,', self.output_file])