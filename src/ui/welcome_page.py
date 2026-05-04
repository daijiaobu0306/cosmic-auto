"""欢迎页 - 程序入口第一屏"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt


class WelcomePage(QWidget):
    def __init__(self, navigate_to):
        super().__init__()
        self._navigate_to = navigate_to
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.addStretch()

        # 标题
        title = QLabel("COSMIC 自动化工具")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 6px;
        """)
        main_layout.addWidget(title)

        # 副标题
        subtitle = QLabel("COSMIC 功能点度量全流程自动化")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 12px;
            color: #7f8c8d;
            margin-bottom: 30px;
        """)
        main_layout.addWidget(subtitle)

        # 准备事项卡片
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

        items = [
            ("1", "准备好对应 Excel 表格（可参考模板）"),
            ("2", "准备好大模型的 API_KEY 和 URL 地址"),
            ("3", "检查 Excel 格式：如单元格合并、层级关系，确保与模板一致"),
        ]

        for num, text in items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(10)

            num_label = QLabel(num)
            num_label.setFixedSize(20, 20)
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_label.setStyleSheet("""
                background-color: #3498db;
                color: white;
                border-radius: 10px;
                font-size: 11px;
                font-weight: bold;
            """)
            item_layout.addWidget(num_label)

            text_label = QLabel(text)
            text_label.setStyleSheet("font-size: 12px; color: #495057;")
            item_layout.addWidget(text_label)

            item_layout.addStretch()
            card_layout.addLayout(item_layout)

        card.setLayout(card_layout)
        main_layout.addWidget(card)

        main_layout.addStretch()

        # Let's Go 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        lets_go_btn = QPushButton("Let's Go  →")
        lets_go_btn.setMinimumSize(140, 36)
        lets_go_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        lets_go_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1f618d;
            }
        """)
        lets_go_btn.clicked.connect(lambda: self._navigate_to(1))
        btn_layout.addWidget(lets_go_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
