"""Page1 - 事前准备页面"""
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from PyQt6.QtCore import Qt

from utils import resource_path


class Page1(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self._setup_ui()

    def _setup_ui(self):
        # 主布局 - 上下填充，横向居中
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(60, 40, 60, 40)
        main_layout.addStretch()

        # 标题区域
        title = QLabel("COSMIC 自动化工具")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        """)
        main_layout.addWidget(title)

        # 副标题
        subtitle = QLabel("事前准备")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
            margin-bottom: 40px;
        """)
        main_layout.addWidget(subtitle)

        # 信息卡片框架（透明无边框）
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                padding: 0px;
            }
        """)
        card_layout = QVBoxLayout()
        card_layout.setSpacing(14)
        card_layout.setContentsMargins(0, 0, 0, 0)

        # 准备事项列表
        items = [
            ("1", "准备好对应 Excel 表格（可参考模板）"),
            ("2", "准备好大模型的 API_KEY和URL地址，"),
            ("3", "检查EXCEL格式：如：单元格合并、层级关系，确保与模板一致"),
        ]

        for num, text in items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(12)

            # 序号圆点
            num_label = QLabel(num)
            num_label.setFixedSize(24, 24)
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_label.setStyleSheet("""
                background-color: #3498db;
                color: white;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            """)
            item_layout.addWidget(num_label)

            # 文字
            text_label = QLabel(text)
            text_label.setStyleSheet("font-size: 14px; color: #495057;")
            text_label.setWordWrap(False)
            item_layout.addWidget(text_label)

            item_layout.addStretch()
            card_layout.addLayout(item_layout)

        card.setLayout(card_layout)
        main_layout.addWidget(card)

        main_layout.addStretch()

        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_open_template = QPushButton("📄 打开模板")
        self.btn_open_template.setFixedSize(120, 36)
        self.btn_open_template.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_template.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: none;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
        """)
        self.btn_open_template.clicked.connect(self._open_template)
        btn_layout.addWidget(self.btn_open_template)

        self.btn_next = QPushButton("下一步 →")
        self.btn_next.setFixedSize(120, 36)
        self.btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_next.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_next.clicked.connect(self._go_next)
        btn_layout.addWidget(self.btn_next)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def _open_template(self):
        template_path = resource_path("D:\cod\AI\cosmic-GUI\/test\模板\cosmic-自动填充-模板.xlsx")
        if os.path.exists(template_path):
            os.startfile(template_path)
        else:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", f"找不到模板文件:\n{template_path}")

    def _go_next(self):
        self.stacked_widget.setCurrentIndex(1)