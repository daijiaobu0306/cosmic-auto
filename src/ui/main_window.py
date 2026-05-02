"""主窗口"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtGui import QIcon

from utils import resource_path
from .page_calculator import PageCalculator
from .page1_welcome import Page1
from .page2_auto_fill import Page2
from .page3_llm_fill import Page3
from .page4_excel_to_word import Page4


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("COSMIC 自动化工具")
        self.setWindowIcon(QIcon(resource_path("ui/应用图标.png")))
        self.resize(700, 550)

        self.stacked = QStackedWidget()

        # 页面0：欢迎页
        self.page1 = Page1(self.stacked)
        # 页面1：人天计算器
        self.page_calculator = PageCalculator(self.stacked)
        # 页面2：自动填充
        self.page2 = Page2(self.stacked, self._on_auto_fill_success)
        # 页面3：LLM填充
        self.page3 = Page3(self.stacked)
        # 页面4：Excel转Word
        self.page4 = Page4(self.stacked)

        self.stacked.addWidget(self.page1)
        self.stacked.addWidget(self.page_calculator)
        self.stacked.addWidget(self.page2)
        self.stacked.addWidget(self.page3)
        self.stacked.addWidget(self.page4)

        layout = QVBoxLayout()
        layout.addWidget(self.stacked)
        self.setLayout(layout)

    def _on_auto_fill_success(self):
        file_path = self.page2.file_edit.text().strip()
        self.page3.set_input_file(file_path)