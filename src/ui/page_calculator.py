"""Page0 - COSMIC 人天单价计算器"""
import math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QFormLayout
)
from PyQt6.QtCore import Qt


class PageCalculator(QWidget):
    def __init__(self, stacked_widget=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self._setup_ui()

    def _setup_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(8)

        # ===== 标题区域 =====
        title = QLabel("COSMIC 人天单价计算器")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            padding: 3px 0;
        """)
        main_layout.addWidget(title)

        # 副标题
        subtitle = QLabel("根据项目金额和单价，快速估算所需编写的 COSMIC 功能点行数")
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

        # ===== 计算按钮 =====
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.calc_btn = QPushButton("计  算")
        self.calc_btn.setFixedSize(100, 30)
        self.calc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.calc_btn.setStyleSheet("""
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
        self.calc_btn.clicked.connect(self._calculate)
        btn_layout.addWidget(self.calc_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # ===== 结果显示区域 =====
        result_card = self._create_result_card()
        main_layout.addWidget(result_card)

        # ===== 复制按钮 =====
        copy_layout = QHBoxLayout()
        copy_layout.addStretch()

        self.copy_btn = QPushButton("复制结果")
        self.copy_btn.setFixedSize(80, 28)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.setEnabled(False)
        self.copy_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #bdc3c7;
                border-color: #e0e0e0;
            }
        """)
        self.copy_btn.clicked.connect(self._copy_result)
        copy_layout.addWidget(self.copy_btn)

        copy_layout.addStretch()
        main_layout.addLayout(copy_layout)

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

        # 存储计算结果
        self._result_text = ""

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
            min-width: 90px;
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
                min-width: 150px;
            }
            QLineEdit:focus {
                border-color: #3498db;
                background-color: #f8fbff;
            }
            QLineEdit:hover {
                border-color: #adb5bd;
            }
        """

        # 项目金额
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("例如：500000")
        self.amount_input.setStyleSheet(input_style)
        self.amount_input.setToolTip("项目的合同总金额（单位：元）")

        amount_label = QLabel("项目金额（元）：")
        amount_label.setStyleSheet(label_style)
        amount_label.setMinimumWidth(100)
        form_layout.addRow(amount_label, self.amount_input)

        # 预计扣减率
        self.deduction_input = QLineEdit()
        self.deduction_input.setPlaceholderText("例如：15")
        self.deduction_input.setStyleSheet(input_style)
        self.deduction_input.setToolTip("预计的成本扣减比例（%），如 15 表示 15%")

        deduction_label = QLabel("预计扣减率（%）：")
        deduction_label.setStyleSheet(label_style)
        deduction_label.setMinimumWidth(100)
        form_layout.addRow(deduction_label, self.deduction_input)

        # 人天单价
        self.price_input = QLineEdit()
        self.price_input.setPlaceholderText("例如：1500")
        self.price_input.setStyleSheet(input_style)
        self.price_input.setToolTip("每人天的单价（单位：元/天）")

        price_label = QLabel("人天单价（元/天）：")
        price_label.setStyleSheet(label_style)
        price_label.setMinimumWidth(100)
        form_layout.addRow(price_label, self.price_input)

        card.setLayout(form_layout)
        return card

    def _create_result_card(self):
        """创建结果显示卡片"""
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

        result_layout = QVBoxLayout()
        result_layout.setSpacing(6)

        # 结果标题
        result_title = QLabel("计算结果")
        result_title.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #2c3e50;
            padding-bottom: 4px;
            border-bottom: 1px solid #bdd7ee;
        """)
        result_layout.addWidget(result_title)

        # 结果内容
        result_content_layout = QHBoxLayout()
        result_content_layout.setSpacing(20)

        # 实际预算
        budget_layout = QVBoxLayout()
        budget_layout.setSpacing(3)

        budget_label = QLabel("实际预算")
        budget_label.setStyleSheet("""
            font-size: 9px;
            color: #7f8c8d;
        """)
        budget_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        budget_layout.addWidget(budget_label)

        self.budget_value = QLabel("¥ 0")
        self.budget_value.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        """)
        self.budget_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        budget_layout.addWidget(self.budget_value)

        result_content_layout.addLayout(budget_layout)

        # 分隔线
        separator = QLabel()
        separator.setFixedWidth(2)
        separator.setFixedHeight(30)
        separator.setStyleSheet("""
            background-color: #bdd7ee;
            border: none;
        """)
        result_content_layout.addWidget(separator)

        # 需编写行数
        lines_layout = QVBoxLayout()
        lines_layout.setSpacing(3)

        lines_label = QLabel("需编写行数")
        lines_label.setStyleSheet("""
            font-size: 9px;
            color: #7f8c8d;
        """)
        lines_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lines_layout.addWidget(lines_label)

        self.lines_value = QLabel("0 行")
        self.lines_value.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #3498db;
        """)
        self.lines_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lines_layout.addWidget(self.lines_value)

        result_content_layout.addLayout(lines_layout)

        result_content_layout.addStretch()
        result_layout.addLayout(result_content_layout)

        card.setLayout(result_layout)
        return card

    def _validate_inputs(self) -> tuple[bool, float, float, float]:
        """验证输入并返回数值"""
        try:
            amount = self.amount_input.text().strip()
            deduction = self.deduction_input.text().strip()
            price = self.price_input.text().strip()

            if not amount or not deduction or not price:
                QMessageBox.warning(self, "输入错误", "请填写所有输入字段")
                return False, 0, 0, 0

            amount = float(amount)
            deduction = float(deduction)
            price = float(price)

            if amount < 0:
                QMessageBox.warning(self, "输入错误", "项目金额不能为负数")
                return False, 0, 0, 0

            if deduction < 0 or deduction >= 100:
                QMessageBox.warning(self, "输入错误", "扣减率必须在 0-100% 之间")
                return False, 0, 0, 0

            if price <= 0:
                QMessageBox.warning(self, "输入错误", "人天单价必须大于 0")
                return False, 0, 0, 0

            return True, amount, deduction, price

        except ValueError:
            QMessageBox.warning(self, "输入错误", "请输入有效的数值")
            return False, 0, 0, 0

    def _calculate(self):
        """执行计算"""
        valid, amount, deduction, price = self._validate_inputs()
        if not valid:
            return

        # 计算实际预算（扣除扣减率后的金额）
        actual_budget = amount / (1 - deduction / 100)

        # 计算需要编写的行数（向上取整）
        lines = math.ceil(actual_budget / price)

        # 更新显示
        self.budget_value.setText(f"¥ {actual_budget:,.2f}")
        self.lines_value.setText(f"{lines:,} 行")

        # 启用复制按钮
        self.copy_btn.setEnabled(True)

        # 保存结果文本
        self._result_text = (
            f"项目金额：¥ {amount:,.2f}\n"
            f"扣减率：{deduction}%\n"
            f"人天单价：¥ {price:,.2f}\n"
            f"─────────────────────\n"
            f"实际预算：¥ {actual_budget:,.2f}\n"
            f"需编写行数：{lines:,} 行"
        )

    def _copy_result(self):
        """复制结果到剪贴板"""
        if not self._result_text:
            return

        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._result_text)

        # 显示复制成功提示
        original_text = self.copy_btn.text()
        self.copy_btn.setText("已复制!")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
        """)

        # 1.5秒后恢复
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self._restore_copy_button(original_text))

    def _restore_copy_button(self, original_text: str):
        """恢复复制按钮状态"""
        self.copy_btn.setText(original_text)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
                border-color: #95a5a6;
            }
        """)

    def _go_back(self):
        """返回欢迎页"""
        if self.stacked_widget:
            self.stacked_widget.setCurrentIndex(0)


# 独立运行测试
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = PageCalculator()
    window.setWindowTitle("COSMIC 人天单价计算器")
    window.resize(600, 500)
    window.show()

    sys.exit(app.exec())
