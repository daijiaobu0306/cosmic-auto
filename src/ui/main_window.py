"""主窗口 - 导航中枢"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from PyQt6.QtGui import QIcon

from utils import resource_path
from .welcome_page import WelcomePage
from .directory_page import DirectoryPage
from .page_calculator import PageCalculator
from .page_ai_recognize import PageAIRecognize
from .page_txt_to_excel import PageTxtToExcel
from .page2_auto_fill import Page2
from .page3_llm_fill import Page3
from .page4_excel_to_word import Page4
from .page_llm_field_gen import PageLLMFieldGen
from .page_excel_to_word_flow import PageExcelToWordFlow


# 功能页面在 stacked_widget 中的 index，按目录顺序排列
FEATURE_ORDER = [2, 3, 4, 5, 6, 7, 8, 9]


class Navigator:
    """统一导航控制器，传递给所有功能页面"""

    def __init__(self, stacked_widget):
        self._stacked = stacked_widget

    def navigate_to(self, index):
        self._stacked.setCurrentIndex(index)

    def navigate_next(self, current_index):
        if current_index in FEATURE_ORDER:
            pos = FEATURE_ORDER.index(current_index)
            if pos < len(FEATURE_ORDER) - 1:
                self._stacked.setCurrentIndex(FEATURE_ORDER[pos + 1])
            else:
                self._stacked.setCurrentIndex(1)  # 最后一个 → 目录
        else:
            self._stacked.setCurrentIndex(1)

    def navigate_prev(self, current_index):
        if current_index in FEATURE_ORDER:
            pos = FEATURE_ORDER.index(current_index)
            if pos > 0:
                self._stacked.setCurrentIndex(FEATURE_ORDER[pos - 1])
            else:
                self._stacked.setCurrentIndex(1)  # 第一个 → 目录
        else:
            self._stacked.setCurrentIndex(1)

    def navigate_to_directory(self):
        self._stacked.setCurrentIndex(1)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("COSMIC 自动化工具")
        self.setWindowIcon(QIcon(resource_path("ui/应用图标.png")))
        self.resize(900, 700)
        self.setMinimumSize(900, 700)

        self.stacked = QStackedWidget()
        self.navigator = Navigator(self.stacked)

        # 页面 0：欢迎页
        self.page_welcome = WelcomePage(self.navigator.navigate_to)
        self.stacked.addWidget(self.page_welcome)

        # 页面 1：功能目录
        self.page_directory = DirectoryPage(self.navigator.navigate_to)
        self.stacked.addWidget(self.page_directory)

        # 页面 2：人天计算器
        self.page_calculator = PageCalculator(self.navigator)
        self.stacked.addWidget(self.page_calculator)

        # 页面 3：AI 识图
        self.page_ai_recognize = PageAIRecognize(self.navigator)
        self.stacked.addWidget(self.page_ai_recognize)

        # 页面 4：TXT 生成 Excel
        self.page_txt_to_excel = PageTxtToExcel(self.navigator)
        self.stacked.addWidget(self.page_txt_to_excel)

        # 页面 5：自动填充
        self.page_auto_fill = Page2(self.navigator, self._on_auto_fill_success)
        self.stacked.addWidget(self.page_auto_fill)

        # 页面 6：LLM 填充
        self.page_llm_fill = Page3(self.navigator)
        self.stacked.addWidget(self.page_llm_fill)

        # 页面 7：LLM 数据字段生成
        self.page_llm_field_gen = PageLLMFieldGen(self.navigator)
        self.stacked.addWidget(self.page_llm_field_gen)

        # 页面 8：Excel 转 Word
        self.page_excel_to_word = Page4(self.navigator)
        self.stacked.addWidget(self.page_excel_to_word)

        # 页面 9：Excel 转 Word（含流程图）
        self.page_excel_to_word_flow = PageExcelToWordFlow(self.navigator)
        self.stacked.addWidget(self.page_excel_to_word_flow)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked)
        self.setLayout(layout)

    def _on_auto_fill_success(self):
        file_path = self.page_auto_fill.file_edit.text().strip()
        self.page_llm_fill.set_input_file(file_path)
