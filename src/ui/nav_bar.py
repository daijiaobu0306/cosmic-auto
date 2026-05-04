"""通用底部导航栏组件"""
from PyQt6.QtWidgets import QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt


def create_nav_bar(navigator, page):
    """创建统一的底部导航栏：上一页 | 返回目录 | 下一页

    Args:
        navigator: Navigator 对象，提供 navigate_prev/navigate_next/navigate_to_directory
        page: 当前页面 QWidget，用于获取其在 stacked_widget 中的 index

    Returns:
        QHBoxLayout: 底部导航布局
    """
    nav_layout = QHBoxLayout()
    nav_layout.setSpacing(10)

    btn_style = """
        QPushButton {
            background-color: #ecf0f1;
            color: #2c3e50;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            font-size: 11px;
            padding: 0 12px;
        }
        QPushButton:hover {
            background-color: #d5dbdb;
            border-color: #95a5a6;
        }
    """

    btn_primary_style = """
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 11px;
            padding: 0 12px;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
    """

    # 上一页
    btn_prev = QPushButton("◀ 上一页")
    btn_prev.setMinimumSize(80, 28)
    btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_prev.setStyleSheet(btn_style)
    btn_prev.clicked.connect(lambda: navigator.navigate_prev(_get_page_index(page)))
    nav_layout.addWidget(btn_prev)

    nav_layout.addStretch()

    # 返回目录
    btn_dir = QPushButton("返回目录")
    btn_dir.setMinimumSize(80, 28)
    btn_dir.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_dir.setStyleSheet(btn_primary_style)
    btn_dir.clicked.connect(navigator.navigate_to_directory)
    nav_layout.addWidget(btn_dir)

    nav_layout.addStretch()

    # 下一页
    btn_next = QPushButton("下一页 ▶")
    btn_next.setMinimumSize(80, 28)
    btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
    btn_next.setStyleSheet(btn_style)
    btn_next.clicked.connect(lambda: navigator.navigate_next(_get_page_index(page)))
    nav_layout.addWidget(btn_next)

    return nav_layout


def _get_page_index(page):
    """获取页面在 stacked_widget 中的 index"""
    parent = page.parent()
    if parent and hasattr(parent, 'indexOf'):
        return parent.indexOf(page)
    return -1
