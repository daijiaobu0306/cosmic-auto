"""Page - TXT 生成 COSMIC Excel"""
import os
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QFormLayout, QFileDialog, QTextEdit, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from workers.txt_to_excel_worker import TxtToExcelWorker
from .nav_bar import create_nav_bar


class PageTxtToExcel(QWidget):
    def __init__(self, navigator):
        super().__init__()
        self.navigator = navigator
        self._excel_output_path = ""
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(8)

        # ===== 标题区域 =====
        title = QLabel("功能清单生成 COSMIC Excel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            padding: 3px 0;
        """)
        main_layout.addWidget(title)

        subtitle = QLabel("将功能清单 TXT 转换为符合 COSMIC 模板格式的 Excel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 10px;
            color: #7f8c8d;
            padding-bottom: 3px;
        """)
        main_layout.addWidget(subtitle)

        # ===== 输入表单区域 =====
        input_card = self._create_input_card()
        main_layout.addWidget(input_card)

        # ===== 操作按钮区域 =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.preview_btn = QPushButton("预览")
        self.preview_btn.setMinimumSize(70, 28)
        self.preview_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #d5dbdb; }
        """)
        self.preview_btn.clicked.connect(self._preview_excel)
        btn_layout.addWidget(self.preview_btn)

        self.export_btn = QPushButton("导出 Excel")
        self.export_btn.setMinimumSize(90, 28)
        self.export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        self.export_btn.clicked.connect(self._export_excel)
        btn_layout.addWidget(self.export_btn)

        self.open_excel_btn = QPushButton("打开文件")
        self.open_excel_btn.setMinimumSize(70, 28)
        self.open_excel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_excel_btn.setEnabled(False)
        self.open_excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #d5dbdb; }
            QPushButton:disabled { background-color: #f5f5f5; color: #bdc3c7; }
        """)
        self.open_excel_btn.clicked.connect(self._open_excel_file)
        btn_layout.addWidget(self.open_excel_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # ===== 预览表格 =====
        preview_group = QGroupBox("Excel 预览")
        preview_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                color: #2c3e50;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(8, 12, 8, 8)

        self.preview_table = QTableWidget()
        self.preview_table.setMinimumHeight(180)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                font-size: 10px;
                gridline-color: #dee2e6;
            }
            QHeaderView::section {
                background-color: #f1f3f5;
                border: 1px solid #dee2e6;
                font-weight: bold;
                font-size: 10px;
                padding: 3px;
            }
        """)
        preview_layout.addWidget(self.preview_table)
        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)

        # ===== 日志区域 =====
        log_group = QGroupBox("操作日志")
        log_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                color: #2c3e50;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
        """)
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(8, 12, 8, 8)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMinimumHeight(80)
        self.log_area.setMaximumHeight(120)
        self.log_area.setStyleSheet("""
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
        log_layout.addWidget(self.log_area)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # ===== 状态标签 =====
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        main_layout.addWidget(self.status_label)

        # ===== 底部导航 =====
        nav = create_nav_bar(self.navigator, self)
        main_layout.addLayout(nav)

        self.setLayout(main_layout)

    def _create_input_card(self):
        """创建输入表单卡片"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 10px;
            }
        """)

        form_layout = QFormLayout()
        form_layout.setSpacing(6)
        form_layout.setContentsMargins(10, 10, 10, 10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        label_style = """
            font-size: 11px;
            color: #495057;
            padding-right: 6px;
            min-width: 70px;
        """

        input_style = """
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 11px;
                color: #2c3e50;
                background-color: white;
            }
            QLineEdit:focus { border-color: #3498db; background-color: #f8fbff; }
            QLineEdit:hover { border-color: #adb5bd; }
        """

        # TXT 文件路径
        txt_layout = QHBoxLayout()
        self.txt_path_input = QLineEdit()
        self.txt_path_input.setPlaceholderText("选择功能清单 TXT 文件")
        self.txt_path_input.setStyleSheet(input_style)

        txt_browse_btn = QPushButton("选择文件")
        txt_browse_btn.setMinimumSize(70, 28)
        txt_browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        txt_browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #d5dbdb; }
        """)
        txt_browse_btn.clicked.connect(self._select_txt_file)

        txt_label = QLabel("TXT 文件：")
        txt_label.setStyleSheet(label_style)
        txt_layout.addWidget(self.txt_path_input)
        txt_layout.addWidget(txt_browse_btn)
        form_layout.addRow(txt_label, txt_layout)

        # 系统名称
        self.system_name_input = QLineEdit()
        self.system_name_input.setPlaceholderText("例如：客户端用户感知分析能力")
        self.system_name_input.setStyleSheet(input_style)
        self.system_name_input.setToolTip("整个系统的名称，将作为一级功能名称")

        name_label = QLabel("系统名称：")
        name_label.setStyleSheet(label_style)
        form_layout.addRow(name_label, self.system_name_input)

        card.setLayout(form_layout)
        return card

    def _select_txt_file(self):
        """选择 TXT 文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择功能清单 TXT 文件", "",
            "文本文件 (*.txt);;所有文件 (*)"
        )
        if file_path:
            self.txt_path_input.setText(file_path)

    def _validate_inputs(self) -> tuple:
        """验证输入，返回 (txt_path, system_name) 或 None"""
        txt_path = self.txt_path_input.text().strip()
        if not txt_path:
            QMessageBox.warning(self, "输入错误", "请选择功能清单 TXT 文件")
            return None
        if not os.path.isfile(txt_path):
            QMessageBox.warning(self, "输入错误", f"TXT 文件不存在: {txt_path}")
            return None

        system_name = self.system_name_input.text().strip()
        if not system_name:
            QMessageBox.warning(self, "输入错误", "请填写系统名称")
            return None

        return txt_path, system_name

    def set_txt_path(self, path: str, system_name: str = ""):
        """外部设置 TXT 路径（用于从 AI 识图页面跳转过来时自动填充）"""
        self.txt_path_input.setText(path)
        if system_name:
            self.system_name_input.setText(system_name)

    def _preview_excel(self):
        """预览 Excel（解析 TXT 并在表格中展示）"""
        validated = self._validate_inputs()
        if not validated:
            return
        txt_path, system_name = validated

        try:
            from core.txt_to_excel import parse_txt, preview_data

            with open(txt_path, 'r', encoding='utf-8') as f:
                txt_content = f.read()

            parsed_data = parse_txt(txt_content)
            if not parsed_data:
                QMessageBox.warning(self, "解析失败", "未能从 TXT 中解析出任何功能过程，请检查文件格式。")
                return

            preview = preview_data(parsed_data, system_name)
            self._display_preview(preview)

            process_count = len(parsed_data)
            self.status_label.setText(
                f"预览: {process_count} 个功能过程, 将生成 {process_count * 4} 行数据"
            )
            self._append_log(f"预览成功: 共 {process_count} 个功能过程")

        except Exception as e:
            QMessageBox.warning(self, "预览失败", f"解析 TXT 时出错: {str(e)}")

    def _display_preview(self, data: list[list[str]]):
        """在表格中展示预览数据"""
        if not data:
            return

        header = data[0]
        rows = data[1:]

        self.preview_table.setColumnCount(len(header))
        self.preview_table.setRowCount(len(rows))
        self.preview_table.setHorizontalHeaderLabels(header)
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        merge_cols = {1, 2, 3, 4, 8}

        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

                if col_idx in merge_cols and row_idx > 0:
                    if row_data[col_idx] == rows[row_idx - 1][col_idx]:
                        item.setBackground(QColor("#f5f5f5"))
                        item.setText("")

                self.preview_table.setItem(row_idx, col_idx, item)

        self.preview_table.resizeColumnsToContents()

    def _export_excel(self):
        """导出 Excel 文件"""
        validated = self._validate_inputs()
        if not validated:
            return
        txt_path, system_name = validated

        default_name = f"{system_name}_COSMIC.xlsx"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "导出 Excel", default_name,
            "Excel 文件 (*.xlsx);;所有文件 (*)"
        )
        if not save_path:
            return

        self.export_btn.setEnabled(False)
        self.export_btn.setText("生成中...")
        self.status_label.setText("正在生成 Excel...")
        self._append_log(f"开始生成 Excel: {save_path}")

        self._excel_worker = TxtToExcelWorker(txt_path, system_name, save_path)
        self._excel_worker.text_written.connect(self._append_log)
        self._excel_worker.finished_with_result.connect(self._on_excel_generated)
        self._excel_worker.finished.connect(self._on_excel_thread_finished)
        self._excel_worker.start()

    def _on_excel_generated(self, output_path: str):
        """Excel 生成完成"""
        self._excel_output_path = output_path
        self.status_label.setText(f"导出完成: {output_path}")
        self.open_excel_btn.setEnabled(True)
        self._append_log("Excel 导出完成")

    def _on_excel_thread_finished(self):
        """Excel Worker 线程结束"""
        self.export_btn.setEnabled(True)
        self.export_btn.setText("导出 Excel")

    def _open_excel_file(self):
        """打开生成的 Excel 文件"""
        if not self._excel_output_path:
            QMessageBox.warning(self, "错误", "没有可打开的 Excel 文件")
            return
        if not os.path.exists(self._excel_output_path):
            QMessageBox.warning(self, "错误", f"文件不存在: {self._excel_output_path}")
            return
        try:
            if os.name == 'nt':
                os.startfile(self._excel_output_path)
            else:
                subprocess.run(['xdg-open', self._excel_output_path])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开文件: {str(e)}")

    def _append_log(self, text):
        """追加日志"""
        self.log_area.append(text)
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())



# 独立运行测试
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    class _DummyNav:
        def navigate_prev(self, idx): pass
        def navigate_next(self, idx): pass
        def navigate_to_directory(self): pass

    window = PageTxtToExcel(_DummyNav())
    window.setWindowTitle("TXT 生成 COSMIC Excel")
    window.resize(700, 600)
    window.show()

    sys.exit(app.exec())
