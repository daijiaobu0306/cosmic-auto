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
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 2px;
        """)
        main_layout.addWidget(title)

        # 副标题
        subtitle = QLabel("COSMIC 功能点度量全流程自动化")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 11px;
            color: #7f8c8d;
            margin-bottom: 10px;
        """)
        main_layout.addWidget(subtitle)

        # 使用需知标题
        tips_title = QLabel("使用需知")
        tips_title.setStyleSheet("""
            font-size: 13px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 10px;
            margin-bottom: 6px;
        """)
        main_layout.addWidget(tips_title)

        # 使用需知内容卡片
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        card_layout = QVBoxLayout()
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(12, 12, 12, 12)

        # 表格标题行
        header_layout = QHBoxLayout()
        header_layout.setSpacing(0)

        header_style = """
            font-size: 10px;
            font-weight: bold;
            color: #495057;
            padding: 4px 8px;
            background-color: #e9ecef;
            border-radius: 3px;
        """

        func_header = QLabel("功能")
        func_header.setStyleSheet(header_style + "min-width: 120px;")
        header_layout.addWidget(func_header)

        material_header = QLabel("需要准备什么")
        material_header.setStyleSheet(header_style + "min-width: 180px;")
        header_layout.addWidget(material_header)

        note_header = QLabel("注意事项")
        note_header.setStyleSheet(header_style + "min-width: 150px;")
        header_layout.addWidget(note_header)

        card_layout.addLayout(header_layout)

        # 表格数据行
        table_data = [
            ("人天计算器", "项目金额、扣减率、单价", "无"),
            ("AI 识图", "系统截图文件夹 + API 配置", "截图要清晰完整"),
            ("TXT 生成 Excel", "功能清单 TXT", "⚠️ 缩进格式要求严格"),
            ("自动填充 / LLM 填充", "COSMIC Excel 模板", "格式需与模板一致"),
            ("Excel 转 Word", "填写完成的 Excel", "H/J/L/M 列需先填好"),
        ]

        row_style = """
            font-size: 10px;
            color: #495057;
            padding: 5px 8px;
            border-bottom: 1px solid #e9ecef;
        """

        highlight_style = """
            font-size: 10px;
            color: #e67e22;
            padding: 5px 8px;
            border-bottom: 1px solid #e9ecef;
            font-weight: bold;
        """

        for func, material, note in table_data:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(0)

            func_label = QLabel(func)
            func_label.setStyleSheet(row_style + "min-width: 120px; font-weight: bold;")
            row_layout.addWidget(func_label)

            material_label = QLabel(material)
            material_label.setStyleSheet(row_style + "min-width: 180px;")
            row_layout.addWidget(material_label)

            note_label = QLabel(note)
            note_label.setStyleSheet(highlight_style if "⚠️" in note else row_style + "min-width: 150px;")
            row_layout.addWidget(note_label)

            card_layout.addLayout(row_layout)

        # TXT 缩进规则说明
        txt_rule_layout = QVBoxLayout()
        txt_rule_layout.setSpacing(4)

        txt_rule_title = QLabel("⚠️ TXT 缩进规则（TXT 生成 Excel 必看）")
        txt_rule_title.setStyleSheet("""
            font-size: 10px;
            font-weight: bold;
            color: #e67e22;
            margin-top: 6px;
        """)
        txt_rule_layout.addWidget(txt_rule_title)

        rules = [
            "• 二级功能：无缩进 + 数字序号      例：1 手机APP监控",
            "• 三级功能：4空格 + 数字序号        例：    1.1 启动分析",
            "• 功能过程：8空格 + 无序号          例：        查询APP启动次数",
        ]

        for rule in rules:
            rule_label = QLabel(rule)
            rule_label.setStyleSheet("""
                font-size: 10px;
                color: #495057;
                padding-left: 12px;
                font-family: Consolas, "Courier New", monospace;
            """)
            txt_rule_layout.addWidget(rule_label)

        card_layout.addLayout(txt_rule_layout)

        # AI 接口说明
        ai_tip = QLabel("💡 本工具所有 AI 功能均使用 OpenAI 兼容接口格式，支持 GPT-4o、通义千问、DeepSeek 等")
        ai_tip.setStyleSheet("""
            font-size: 10px;
            color: #7f8c8d;
            margin-top: 6px;
            padding: 6px 8px;
            background-color: #eaf2f8;
            border-radius: 4px;
        """)
        ai_tip.setWordWrap(True)
        card_layout.addWidget(ai_tip)

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
