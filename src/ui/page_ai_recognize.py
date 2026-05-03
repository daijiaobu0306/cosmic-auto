"""Page - AI 识图生成功能清单"""
import os
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QFormLayout, QFileDialog, QTextEdit, QGroupBox,
)
from PyQt6.QtCore import Qt

from workers.ai_recognize_worker import AIRecognizeWorker


class PageAIRecognize(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.worker = None
        self._output_path = ""
        self._setup_ui()

    def _setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(8)

        # ===== 标题区域 =====
        title = QLabel("AI 识图生成功能清单")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            padding: 3px 0;
        """)
        main_layout.addWidget(title)

        # 副标题
        subtitle = QLabel("上传软件截图，AI 自动识别功能模块并生成功能清单")
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

        self.start_btn = QPushButton("开始识别")
        self.start_btn.setFixedSize(100, 30)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.start_btn.clicked.connect(self._start_recognize)
        btn_layout.addWidget(self.start_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # ===== 日志输出区域 =====
        log_group = QGroupBox("识别日志")
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
        self.log_area.setMinimumHeight(100)
        self.log_area.setMaximumHeight(150)
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

        # ===== 结果操作区域 =====
        result_card = self._create_result_card()
        main_layout.addWidget(result_card)

        # ===== 底部导航 =====
        nav_layout = QHBoxLayout()

        self.btn_back = QPushButton("返回欢迎页")
        self.btn_back.setFixedSize(80, 28)
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
                border-color: #95a5a6;
            }
        """)
        self.btn_back.clicked.connect(self._go_back)
        nav_layout.addWidget(self.btn_back)

        nav_layout.addStretch()
        main_layout.addLayout(nav_layout)

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

        # 标签样式
        label_style = """
            font-size: 11px;
            color: #495057;
            padding-right: 6px;
            min-width: 70px;
        """

        # 输入框样式
        input_style = """
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                font-size: 11px;
                color: #2c3e50;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f8fbff;
            }
            QLineEdit:hover {
                border-color: #adb5bd;
            }
        """

        # 系统名称
        self.system_name_input = QLineEdit()
        self.system_name_input.setPlaceholderText("例如：客户端用户感知分析能力")
        self.system_name_input.setStyleSheet(input_style)
        self.system_name_input.setToolTip("整个系统的名称，将作为一级功能名称")

        name_label = QLabel("系统名称：")
        name_label.setStyleSheet(label_style)
        form_layout.addRow(name_label, self.system_name_input)

        # 系统描述
        self.system_desc_input = QLineEdit()
        self.system_desc_input.setPlaceholderText("例如：面向运营商的客户端用户体验质量分析平台")
        self.system_desc_input.setStyleSheet(input_style)
        self.system_desc_input.setToolTip("一句话说清楚系统是什么")

        desc_label = QLabel("系统描述：")
        desc_label.setStyleSheet(label_style)
        form_layout.addRow(desc_label, self.system_desc_input)

        # 截图文件夹
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("选择包含截图的文件夹")
        self.folder_input.setStyleSheet(input_style)
        self.folder_input.setToolTip("包含 JPG/PNG 截图的文件夹路径")

        self.folder_btn = QPushButton("选择文件夹")
        self.folder_btn.setFixedSize(80, 28)
        self.folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
                border-color: #95a5a6;
            }
        """)
        self.folder_btn.clicked.connect(self._select_folder)
        folder_layout.addWidget(self.folder_input)
        folder_layout.addWidget(self.folder_btn)

        folder_label = QLabel("截图文件夹：")
        folder_label.setStyleSheet(label_style)
        form_layout.addRow(folder_label, folder_layout)

        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("sk-xxx")
        self.api_key_input.setStyleSheet(input_style)
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setToolTip("多模态模型的 API 密钥")

        key_label = QLabel("API Key：")
        key_label.setStyleSheet(label_style)
        form_layout.addRow(key_label, self.api_key_input)

        # API URL
        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://api.openai.com/v1")
        self.api_url_input.setStyleSheet(input_style)
        self.api_url_input.setToolTip("模型接口地址（OpenAI 兼容格式）")

        url_label = QLabel("API URL：")
        url_label.setStyleSheet(label_style)
        form_layout.addRow(url_label, self.api_url_input)

        # 模型名称
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("gpt-4o / qwen-vl-max")
        self.model_input.setStyleSheet(input_style)
        self.model_input.setToolTip("使用的模型标识")

        model_label = QLabel("模型名称：")
        model_label.setStyleSheet(label_style)
        form_layout.addRow(model_label, self.model_input)

        card.setLayout(form_layout)
        return card

    def _create_result_card(self):
        """创建结果操作卡片"""
        card = QFrame()
        card.setObjectName("resultCard")
        card.setStyleSheet("""
            QFrame#resultCard {
                background-color: #f0f7ff;
                border: 2px solid #3498db;
                border-radius: 6px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(6)

        # 结果标题
        result_title = QLabel("识别结果")
        result_title.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #2c3e50;
            padding-bottom: 4px;
            border-bottom: 1px solid #bdd7ee;
        """)
        layout.addWidget(result_title)

        # 文件路径显示
        self.result_path_label = QLabel("功能清单文件：未生成")
        self.result_path_label.setStyleSheet("""
            font-size: 11px;
            color: #495057;
            padding: 3px 0;
        """)
        self.result_path_label.setWordWrap(True)
        layout.addWidget(self.result_path_label)

        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.open_btn = QPushButton("打开功能清单")
        self.open_btn.setFixedSize(100, 28)
        self.open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_btn.setEnabled(False)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.open_btn.clicked.connect(self._open_txt_file)
        btn_layout.addWidget(self.open_btn)

        self.confirm_btn = QPushButton("确认完成，生成 Excel")
        self.confirm_btn.setFixedSize(130, 28)
        self.confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_btn.setEnabled(False)
        self.confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.confirm_btn.clicked.connect(self._confirm_and_generate)
        btn_layout.addWidget(self.confirm_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        card.setLayout(layout)
        return card

    def _confirm_and_generate(self):
        """从识别结果区域跳转到 TXT 生成 Excel 页面"""
        if self.stacked_widget and self._output_path:
            # 获取系统名称
            system_name = self.system_name_input.text().strip()
            # 获取目标页面并设置数据
            target_page = self.stacked_widget.widget(3)
            if target_page and hasattr(target_page, 'set_txt_path'):
                target_page.set_txt_path(self._output_path, system_name)
            # 跳转到 TXT 生成 Excel 页面
            self.stacked_widget.setCurrentIndex(3)

    def _select_folder(self):
        """选择截图文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择截图文件夹", "",
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.folder_input.setText(folder)

    def _validate_inputs(self) -> bool:
        """验证输入"""
        if not self.system_name_input.text().strip():
            QMessageBox.warning(self, "输入错误", "请填写系统名称")
            return False

        if not self.system_desc_input.text().strip():
            QMessageBox.warning(self, "输入错误", "请填写系统描述")
            return False

        if not self.folder_input.text().strip():
            QMessageBox.warning(self, "输入错误", "请选择截图文件夹")
            return False

        if not self.api_key_input.text().strip():
            QMessageBox.warning(self, "输入错误", "请填写 API Key")
            return False

        if not self.api_url_input.text().strip():
            QMessageBox.warning(self, "输入错误", "请填写 API URL")
            return False

        if not self.model_input.text().strip():
            QMessageBox.warning(self, "输入错误", "请填写模型名称")
            return False

        # 检查文件夹是否存在
        folder = self.folder_input.text().strip()
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "输入错误", f"文件夹不存在: {folder}")
            return False

        return True

    def _start_recognize(self):
        """开始识别"""
        if not self._validate_inputs():
            return

        # 禁用按钮
        self.start_btn.setEnabled(False)
        self.start_btn.setText("识别中...")
        self.log_area.clear()

        # 生成输出路径
        folder = self.folder_input.text().strip()
        system_name = self.system_name_input.text().strip()
        output_path = os.path.join(folder, f"{system_name}_功能清单.txt")
        self._output_path = output_path

        # 创建 Worker
        self.worker = AIRecognizeWorker(
            image_folder=folder,
            system_name=system_name,
            system_desc=self.system_desc_input.text().strip(),
            api_key=self.api_key_input.text().strip(),
            api_url=self.api_url_input.text().strip(),
            model_name=self.model_input.text().strip(),
            output_path=output_path,
        )

        # 连接信号
        self.worker.text_written.connect(self._append_log)
        self.worker.finished_with_result.connect(self._on_finished)
        self.worker.finished.connect(self._on_thread_finished)

        # 启动
        self.worker.start()

    def _append_log(self, text):
        """追加日志"""
        self.log_area.append(text)
        # 滚动到底部
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_finished(self, output_path):
        """识别完成"""
        self._output_path = output_path
        self.result_path_label.setText(f"功能清单文件：{output_path}")
        self.open_btn.setEnabled(True)
        self.confirm_btn.setEnabled(True)

    def _on_thread_finished(self):
        """线程结束"""
        self.start_btn.setEnabled(True)
        self.start_btn.setText("开始识别")

    def _open_txt_file(self):
        """用系统默认编辑器打开 TXT 文件"""
        if not self._output_path or not os.path.exists(self._output_path):
            QMessageBox.warning(self, "错误", "功能清单文件不存在")
            return

        try:
            if os.name == 'nt':  # Windows
                os.startfile(self._output_path)
            else:  # Linux/Mac
                subprocess.run(['xdg-open', self._output_path])
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法打开文件: {str(e)}")

    def _go_back(self):
        """返回欢迎页"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)


# 独立运行测试
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = PageAIRecognize()
    window.setWindowTitle("AI 识图生成功能清单")
    window.resize(700, 600)
    window.show()

    sys.exit(app.exec())
