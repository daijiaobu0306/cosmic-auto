"""Page7 - Excel 转 Word（含流程图）页面"""
import os
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QFileDialog, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt

from workers.excel_to_word_flow_worker import ExcelToWordFlowWorker
from .nav_bar import create_nav_bar


class PageExcelToWordFlow(QWidget):
    def __init__(self, navigator):
        super().__init__()
        self.navigator = navigator
        self.worker = None
        self.output_file = ""
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(10)

        # 标题
        title = QLabel("Excel 转 Word（含流程图）")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            padding: 3px 0;
        """)
        main_layout.addWidget(title)

        # 副标题
        subtitle = QLabel("将 COSMIC 表格转换为 Word 文档，并自动生成时序流程图")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 10px;
            color: #7f8c8d;
            padding-bottom: 3px;
        """)
        main_layout.addWidget(subtitle)

        # 文件选择
        file_layout = QHBoxLayout()
        file_label = QLabel("Excel 文件:")
        file_label.setStyleSheet("font-size: 11px; color: #495057; min-width: 70px;")
        file_layout.addWidget(file_label)

        self.excel_file_edit = QLineEdit()
        self.excel_file_edit.setPlaceholderText("请选择已填充完成的 Excel 文件（.xlsx）")
        self.excel_file_edit.setStyleSheet("""
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
        file_layout.addWidget(self.excel_file_edit)

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
        file_layout.addWidget(self.btn_browse)
        main_layout.addLayout(file_layout)

        # 选项区域
        option_layout = QHBoxLayout()
        option_layout.setSpacing(12)

        self.flowchart_checkbox = QCheckBox("自动生成流程图（基于 Pillow，无需额外依赖）")
        self.flowchart_checkbox.setChecked(True)
        self.flowchart_checkbox.setStyleSheet("font-size: 11px; color: #495057;")
        option_layout.addWidget(self.flowchart_checkbox)

        option_layout.addStretch()
        main_layout.addLayout(option_layout)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_convert = QPushButton("开始转换")
        self.btn_convert.setMinimumSize(120, 30)
        self.btn_convert.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_convert.setStyleSheet("""
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
        self.btn_convert.clicked.connect(self._start_convert)
        btn_layout.addWidget(self.btn_convert)

        self.btn_open_doc = QPushButton("打开生成文档")
        self.btn_open_doc.setMinimumSize(110, 28)
        self.btn_open_doc.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_doc.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #229954; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """)
        self.btn_open_doc.clicked.connect(self._open_output_file)
        self.btn_open_doc.setEnabled(False)
        btn_layout.addWidget(self.btn_open_doc)

        self.btn_open_folder = QPushButton("打开所在目录")
        self.btn_open_folder.setMinimumSize(100, 28)
        self.btn_open_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #d5dbdb; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """)
        self.btn_open_folder.clicked.connect(self._open_output_folder)
        self.btn_open_folder.setEnabled(False)
        btn_layout.addWidget(self.btn_open_folder)

        main_layout.addLayout(btn_layout)

        # 日志区域
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setPlaceholderText("日志输出区域（包含流程图渲染与文档生成过程）...")
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
        main_layout.addWidget(self.log_edit, 1)

        # 底部导航
        nav = create_nav_bar(self.navigator, self)
        main_layout.addLayout(nav)

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

        if not os.path.exists(excel_file):
            QMessageBox.warning(self, "警告", f"文件不存在：{excel_file}")
            return

        base_name = os.path.splitext(os.path.basename(excel_file))[0]
        output_dir = os.path.dirname(excel_file) or "."
        self.output_file = os.path.join(output_dir, f"{base_name}_转换后_含流程图.docx")

        self.log_edit.clear()
        self.btn_convert.setEnabled(False)
        self.btn_open_doc.setEnabled(False)
        self.btn_open_folder.setEnabled(False)

        self.log_edit.append(f"开始转换...\n输入文件: {excel_file}\n输出文件: {self.output_file}\n")

        self.worker = ExcelToWordFlowWorker(
            excel_file=excel_file,
            output_file=self.output_file,
            generate_flowchart=self.flowchart_checkbox.isChecked(),
        )
        self.worker.text_written.connect(self._append_log)
        self.worker.finished.connect(self._convert_finished)
        self.worker.start()

    def _append_log(self, text):
        self.log_edit.append(text)

    def _convert_finished(self):
        self.btn_convert.setEnabled(True)
        self.btn_open_doc.setEnabled(True)
        self.btn_open_folder.setEnabled(True)
        self.log_edit.append("\n【任务结束】")

    def _open_output_file(self):
        if not self.output_file or not os.path.exists(self.output_file):
            QMessageBox.warning(self, "提示", "生成文件不存在，请先完成转换")
            return
        if os.name == 'nt':
            os.startfile(self.output_file)
        else:
            subprocess.run(['xdg-open', self.output_file])

    def _open_output_folder(self):
        if not self.output_file or not os.path.exists(self.output_file):
            QMessageBox.warning(self, "提示", "生成文件不存在，请先完成转换")
            return
        subprocess.run(['explorer', '/select,', self.output_file])
