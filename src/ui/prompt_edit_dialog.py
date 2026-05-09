"""提示词编辑对话框 - 用于自定义各模块的 LLM 提示词"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QScrollArea, QWidget,
    QFrame,
)
from PyQt6.QtCore import Qt

from core.prompt_manager import load_prompts, save_prompts, get_default_prompts


# 对话框样式
_DIALOG_STYLE = """
QDialog {
    background-color: #f8f9fa;
}
QLabel#dialogTitle {
    font-size: 15px;
    font-weight: bold;
    color: #2c3e50;
    padding: 8px 0;
}
QLabel#sectionLabel {
    font-size: 12px;
    font-weight: bold;
    color: #2c3e50;
    padding: 4px 0 2px 0;
}
QLabel#hintLabel {
    font-size: 10px;
    color: #7f8c8d;
    padding-bottom: 4px;
}
QTextEdit {
    background-color: white;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    font-family: Consolas, "Microsoft YaHei", monospace;
    font-size: 11px;
    color: #2c3e50;
    padding: 6px;
}
QTextEdit:focus {
    border-color: #3498db;
}
QFrame#separator {
    background-color: #e9ecef;
    max-height: 1px;
}
QPushButton#resetBtn {
    background-color: #ecf0f1;
    color: #495057;
    border: 1px solid #bdc3c7;
    border-radius: 4px;
    font-size: 11px;
    padding: 6px 14px;
}
QPushButton#resetBtn:hover {
    background-color: #d5dbdb;
    border-color: #95a5a6;
}
QPushButton#saveBtn {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 11px;
    font-weight: bold;
    padding: 6px 20px;
}
QPushButton#saveBtn:hover {
    background-color: #2980b9;
}
QPushButton#cancelBtn {
    background-color: white;
    color: #495057;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    font-size: 11px;
    padding: 6px 14px;
}
QPushButton#cancelBtn:hover {
    background-color: #f8f9fa;
    border-color: #adb5bd;
}
"""


# 各模块提示词的显示标签
_MODULE_LABELS = {
    "ai_recognize": "AI 识图",
    "llm_fill": "LLM 填充",
    "llm_field_gen": "LLM 数据字段生成",
}

# 各字段的显示名称
_FIELD_LABELS = {
    "system_prompt": "系统提示词",
    "user_prompt": "用户提示词",
    "system_prompt_retry": "重试提示词",
}

# 各字段的说明
_FIELD_HINTS = {
    "system_prompt": "定义 AI 的角色和任务规则，支持 {system_name} 和 {system_desc} 占位符",
    "user_prompt": "随截图一起发送给模型的指令文本",
    "system_prompt_retry": "首次结果重复时使用的更严格提示词",
}


class PromptEditDialog(QDialog):
    """提示词编辑对话框"""

    def __init__(self, module_key, parent=None):
        """
        Args:
            module_key: 模块标识，如 "ai_recognize" / "llm_fill" / "llm_field_gen"
            parent: 父窗口
        """
        super().__init__(parent)
        self.module_key = module_key
        self.prompts = load_prompts()
        self.module_prompts = self.prompts.get(module_key, {})
        self._editors = {}  # field_key -> QTextEdit

        self.setWindowTitle(f"自定义提示词 - {_MODULE_LABELS.get(module_key, module_key)}")
        self.setMinimumSize(700, 500)
        self.resize(700, 500)
        self.setStyleSheet(_DIALOG_STYLE)
        self.setModal(True)

        self._setup_ui()

        # 居中显示
        if parent:
            parent_rect = parent.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

    def _setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(10)

        # 标题
        title = QLabel(f"自定义提示词 - {_MODULE_LABELS.get(self.module_key, self.module_key)}")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        # 分隔线
        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(sep)

        # 可滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(12)

        # 为每个提示词字段创建编辑区
        for field_key, value in self.module_prompts.items():
            section = self._create_field_section(field_key, value)
            scroll_layout.addWidget(section)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll, 1)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        reset_btn = QPushButton("恢复默认")
        reset_btn.setObjectName("resetBtn")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_to_default)
        btn_layout.addWidget(reset_btn)

        btn_layout.addStretch()

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("cancelBtn")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("保存")
        save_btn.setObjectName("saveBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_and_close)
        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

    def _create_field_section(self, field_key, value):
        """创建单个提示词字段的编辑区域"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e9ecef;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # 字段标题
        label = QLabel(_FIELD_LABELS.get(field_key, field_key))
        label.setObjectName("sectionLabel")
        layout.addWidget(label)

        # 字段说明
        hint = _FIELD_HINTS.get(field_key, "")
        if hint:
            hint_label = QLabel(hint)
            hint_label.setObjectName("hintLabel")
            hint_label.setWordWrap(True)
            layout.addWidget(hint_label)

        # 文本编辑器
        editor = QTextEdit()
        editor.setPlainText(value)
        editor.setMinimumHeight(100)
        editor.setMaximumHeight(200)
        layout.addWidget(editor)

        self._editors[field_key] = editor

        frame.setLayout(layout)
        return frame

    def _reset_to_default(self):
        """恢复为默认提示词"""
        defaults = get_default_prompts()
        default_module = defaults.get(self.module_key, {})
        for field_key, editor in self._editors.items():
            if field_key in default_module:
                editor.setPlainText(default_module[field_key])

    def _save_and_close(self):
        """保存并关闭"""
        for field_key, editor in self._editors.items():
            self.module_prompts[field_key] = editor.toPlainText()

        self.prompts[self.module_key] = self.module_prompts
        save_prompts(self.prompts)
        self.accept()
