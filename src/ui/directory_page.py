"""功能目录页 - 展示所有功能模块，支持点击跳转"""
import os
import requests
from urllib.parse import quote
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from utils import resource_path

FEEDBACK_URL = "http://120.55.98.247:5000/feedback"


# 功能定义：(分类, 名称, 描述, stacked_widget_index)
CATEGORIES = [
    ("编写前", [
        ("人天计算器", "根据金额估算 COSMIC 行数", 2),
        ("AI 识图", "截图 → AI 识别 → 功能清单 TXT", 3),
        ("TXT 生成 Excel", "功能清单 TXT → COSMIC Excel", 4),
    ]),
    ("编写中", [
        ("自动填充", "规则引擎填写 H/J/L 列", 5),
        ("LLM 填充", "大模型填写 M 列", 6),
        ("LLM 字段生成", "大模型填写 M 列（支持 DDL 辅助）", 7),
    ]),
    ("编写后", [
        ("Excel 转 Word", "COSMIC Excel → Word 文档", 8),
        ("Excel 转 Word（含流程图）", "COSMIC Excel → Word 文档 + 自动流程图", 9),
    ]),
]

# 分类颜色
CATEGORY_COLORS = {
    "编写前": "#3498db",
    "编写中": "#27ae60",
    "编写后": "#8e44ad",
}


class DirectoryPage(QWidget):
    def __init__(self, navigate_to):
        super().__init__()
        self._navigate_to = navigate_to
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(12)

        # 反馈按钮（独立一行）
        feedback_row = QHBoxLayout()
        feedback_btn = QPushButton("问题反馈")
        feedback_btn.setMinimumSize(80, 28)
        feedback_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        feedback_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                padding: 0 10px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        feedback_btn.clicked.connect(self._show_feedback_dialog)
        feedback_row.addWidget(feedback_btn)
        feedback_row.addStretch()
        main_layout.addLayout(feedback_row)

        # 标题
        title = QLabel("COSMIC 功能目录")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 4px 0;
        """)
        main_layout.addWidget(title)

        subtitle = QLabel("选择功能开始使用，或点击 Let's Go 从头开始全流程")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            font-size: 10px;
            color: #7f8c8d;
            padding-bottom: 6px;
        """)
        main_layout.addWidget(subtitle)

        # 功能分类区域（使用弹性布局居中）
        categories_container = QVBoxLayout()
        categories_container.setSpacing(16)

        for category_name, features in CATEGORIES:
            color = CATEGORY_COLORS.get(category_name, "#3498db")
            section = self._create_category_section(category_name, features, color)
            categories_container.addWidget(section)

        main_layout.addLayout(categories_container)

        main_layout.addStretch()

        # 打开模板按钮
        template_layout = QHBoxLayout()
        template_layout.addStretch()
        template_btn = QPushButton("打开 COSMIC 模板文件")
        template_btn.setMinimumSize(180, 30)
        template_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        template_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                font-size: 11px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
        """)
        template_btn.clicked.connect(self._open_template)
        template_layout.addWidget(template_btn)
        template_layout.addStretch()
        main_layout.addLayout(template_layout)

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
        lets_go_btn.clicked.connect(lambda: self._navigate_to(2))
        btn_layout.addWidget(lets_go_btn)
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def _create_category_section(self, name, features, color):
        """创建一个分类区域"""
        section = QFrame()
        section.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 0px;
            }
        """)
        section_layout = QVBoxLayout()
        section_layout.setContentsMargins(12, 10, 12, 12)
        section_layout.setSpacing(8)

        # 分类标题栏
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        color_bar = QLabel()
        color_bar.setFixedSize(4, 16)
        color_bar.setStyleSheet(f"background-color: {color}; border-radius: 2px;")
        header_layout.addWidget(color_bar)

        cat_label = QLabel(name)
        cat_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {color};
        """)
        header_layout.addWidget(cat_label)
        header_layout.addStretch()

        section_layout.addLayout(header_layout)

        # 功能卡片网格
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(10)

        for feat_name, feat_desc, page_index in features:
            card = self._create_feature_card(feat_name, feat_desc, page_index, color)
            cards_layout.addWidget(card)

        cards_layout.addStretch()
        section_layout.addLayout(cards_layout)

        section.setLayout(section_layout)
        return section

    def _create_feature_card(self, name, desc, page_index, color):
        """创建单个功能卡片"""
        card = QFrame()
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setMinimumWidth(160)
        card.setMaximumWidth(220)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 0px;
            }
            QFrame:hover {
                border-color: #3498db;
                background-color: #f0f7ff;
            }
        """)
        # 让整个卡片可点击：使用 QPushButton 模拟
        card_layout = QVBoxLayout()
        card_layout.setContentsMargins(12, 10, 12, 10)
        card_layout.setSpacing(4)

        name_label = QLabel(name)
        name_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: #2c3e50;
        """)
        card_layout.addWidget(name_label)

        desc_label = QLabel(desc)
        desc_label.setStyleSheet("""
            font-size: 10px;
            color: #7f8c8d;
        """)
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)

        card.setLayout(card_layout)

        # 使用事件过滤器实现卡片点击
        card.mousePressEvent = lambda event, idx=page_index: self._navigate_to(idx)

        return card

    def _open_template(self):
        template_path = resource_path("../docs/test_data/模板/cosmic-自动填充-模板.xlsx")
        if os.path.exists(template_path):
            os.startfile(template_path)
        else:
            QMessageBox.warning(self, "警告", f"找不到模板文件:\n{template_path}")

    def _show_feedback_dialog(self):
        msg, ok = QInputDialog.getMultiLineText(
            self, "问题反馈", "请输入您在使用中遇到的问题或bug：", ""
        )
        if ok and msg.strip():
            try:
                url = f"{FEEDBACK_URL}?msg={quote(msg.strip())}"
                resp = requests.get(url, timeout=10)
                if resp.status_code == 200:
                    QMessageBox.information(self, "感谢反馈", "您的反馈已提交，我们会尽快处理！")
                else:
                    QMessageBox.warning(self, "提交失败", f"服务器返回错误：{resp.status_code}")
            except Exception as e:
                QMessageBox.warning(self, "提交失败", f"网络错误：{str(e)}")
