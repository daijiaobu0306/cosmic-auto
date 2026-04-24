"""Page2 - 自动填空页面"""
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import QObject

from workers.auto_fill_worker import AutoFillWorker


class Page2(QWidget):
    def __init__(self, stacked_widget, on_success_callback):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.on_success_callback = on_success_callback
        self.auto_fill_thread = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("选择文件:"))
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("请选择 Excel 文件 (.xlsx)")
        file_layout.addWidget(self.file_edit)
        self.btn_browse = QPushButton("浏览")
        self.btn_browse.clicked.connect(self._browse_file)
        file_layout.addWidget(self.btn_browse)
        layout.addLayout(file_layout)

        sheet_layout = QHBoxLayout()
        sheet_layout.addWidget(QLabel("定位 Sheet 表:"))
        self.sheet_edit = QLineEdit()
        self.sheet_edit.setText("cosmic模块汇总")
        self.sheet_edit.setPlaceholderText("请输入 Sheet 名称")
        sheet_layout.addWidget(self.sheet_edit)
        layout.addLayout(sheet_layout)

        self.btn_start = QPushButton("开始运行")
        self.btn_start.clicked.connect(self._start_auto_fill)
        layout.addWidget(self.btn_start)

        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("日志输出区域...")
        layout.addWidget(self.log_edit)

        nav_layout = QHBoxLayout()
        self.btn_prev = QPushButton("上一步")
        self.btn_prev.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        nav_layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton("下一步")
        self.btn_next.clicked.connect(self._go_next)
        self.btn_next.setEnabled(False)
        nav_layout.addWidget(self.btn_next)

        nav_layout.addStretch()
        layout.addLayout(nav_layout)
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
        self.btn_next.setEnabled(True)
        self.on_success_callback()
        self.log_edit.append("\n【自动填空完成，可进行下一步】")

    def _go_next(self):
        if self.auto_fill_thread and self.auto_fill_thread.isFinished():
            self.stacked_widget.setCurrentIndex(2)
        else:
            QMessageBox.warning(self, "警告", "请先执行步骤1（自动填空）")