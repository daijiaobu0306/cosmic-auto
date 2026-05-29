# COSMIC-GUI

COSMIC 功能点度量自动化工具，基于 PyQt6 桌面应用。

> **⚠️ 开发铁律：本项目最终会打包成 exe 分发给所有用户。**
> 每次开发时必须格外注意以下问题：
> - **文件路径**：禁止使用相对路径或硬编码项目目录路径。所有用户可写数据（配置、提示词、缓存等）必须存放在用户级目录（Windows: `%APPDATA%/COSMIC-GUI/`，其他: `~/.cosmic-gui/`），确保 exe 在任意电脑上都能正常读写。
> - **资源文件**：打包后 `__file__` 指向 exe 内部路径，不能用 `os.path.dirname(__file__)` 定位打包外的文件。需要随 exe 分发的资源文件应通过 PyInstaller 的 `--add-data` 打包进 exe。
> - **依赖库**：所有 `import` 的第三方库都必须能被 PyInstaller 正确识别和打包，避免使用隐式导入。
> - **路径拼接**：统一使用 `os.path.join()` 拼接路径，不要用字符串拼接或硬编码 `/` 或 `\`。

## 快速启动

```bash
cd d:/cod/AI/cosmic-GUI/src
python gui.py
```

## 文件结构

```
src/
├── gui.py                          # 程序入口
├── core/                           # 纯业务逻辑（无 Qt 依赖）
│   ├── auto_fill.py                # 自动填空（H/J/L 列）
│   ├── llm_fill.py                 # LLM 填充（M 列）
│   ├── llm_field_gen.py            # LLM 数据字段生成（M 列 + DDL 辅助）
│   ├── ai_recognize.py             # AI 识图 → TXT
│   ├── txt_to_excel.py             # TXT → Excel（含合并单元格）
│   ├── excel_to_word.py            # Excel → Word（纯转换逻辑）
│   ├── excel_to_word_flow.py       # Excel → Word + 流程图（纯转换逻辑）
│   ├── ddl_parser.py               # DDL 解析
│   ├── flowchart_renderer.py       # 纯 Python 时序图渲染（Pillow）
│   └── config_store.py             # 全局配置单例
├── ui/                             # PyQt6 页面
│   ├── main_window.py              # 主窗口（导航中枢 + Navigator）
│   ├── welcome_page.py             # 欢迎页（第一屏）
│   ├── directory_page.py           # 功能目录页（分类展示所有功能）
│   ├── nav_bar.py                  # 通用底部导航栏组件
│   ├── page_calculator.py          # 人天计算器
│   ├── page_ai_recognize.py        # AI 识图 + 生成 Excel
│   ├── page_txt_to_excel.py        # TXT 生成 Excel
│   ├── page2_auto_fill.py          # 自动填充
│   ├── page3_llm_fill.py           # LLM 填充
│   ├── page4_excel_to_word.py      # Excel 转 Word
│   ├── page_excel_to_word_flow.py  # Excel 转 Word（含流程图）
│   └── page_llm_field_gen.py       # LLM 数据字段生成
├── workers/                        # QThread 后台线程
│   ├── auto_fill_worker.py
│   ├── llm_fill_worker.py
│   ├── llm_field_gen_worker.py
│   ├── excel_to_word_worker.py
│   ├── excel_to_word_flow_worker.py
│   ├── ai_recognize_worker.py
│   └── txt_to_excel_worker.py
└── utils/
    └── resource_path.py            # 资源路径（打包用）
```

## 页面导航结构

程序采用三层导航：**欢迎页 → 功能目录 → 功能页面**

```
欢迎页 (index 0)
  └─ [Let's Go] → 功能目录 (index 1)
       ├─ 编写前
       │   ├─ 人天计算器 (index 2)
       │   ├─ AI 识图 (index 3)
       │   └─ TXT 生成 Excel (index 4)
       ├─ 编写中
       │   ├─ 自动填充 (index 5)
       │   └─ LLM 字段生成 (index 6)
       └─ 编写后
           ├─ Excel 转 Word (index 7)
           └─ Excel 转 Word（含流程图） (index 8)
```

> **变更记录 (2026-05-29)**：已移除"LLM 填充"功能（原 index 6），保留"LLM 字段生成"功能。两个功能存在重复，"LLM 字段生成"支持 DDL 辅助，功能更完善。
> 
> **回滚方法**：如需恢复"LLM 填充"功能，参考 `docs/CHANGELOG_LLM_FILL_REMOVAL.md`。

**导航规则：**
- 欢迎页：只有 Let's Go 按钮，进入功能目录
- 功能目录：展示所有功能卡片（按编写前/中/后分类），点击跳转对应功能页；底部 Let's Go 从第一个功能开始
- 功能页面：底部统一「上一页 | 返回目录 | 下一页」导航栏，按目录顺序跳转

## 功能模块

| 分类 | 功能 | 说明 | 对应页面 |
|------|------|------|----------|
| 编写前 | 人天计算器 | 项目金额 → COSMIC 行数 | page_calculator.py | 模块1
| 编写前 | AI 识图 | 截图 → 功能清单 TXT | page_ai_recognize.py | 模块2
| 编写前 | TXT 生成 Excel | 功能清单 TXT → COSMIC Excel | page_txt_to_excel.py | 模块3
| 编写中 | 自动填充 | 规则引擎填写 H/J/L 列 | page2_auto_fill.py | 模块4
| 编写中 | LLM 字段生成 | 大模型填写 M 列（支持 DDL 辅助） | page_llm_field_gen.py | 模块5
| 编写后 | Excel 转 Word | COSMIC Excel → Word 文档 | page4_excel_to_word.py | 模块6
| 编写后 | Excel 转 Word（含流程图） | COSMIC Excel → Word + Mermaid 流程图 |   page_excel_to_word_flow.py | 模块7

## 添加新功能指南

新增功能模块时，按以下步骤操作，确保自动注册到目录和导航系统：

### 1. 创建 core 和 worker（如需要）

```
src/core/your_feature.py          ← 纯业务逻辑（无 Qt 依赖）
src/workers/your_feature_worker.py ← QThread 子类
```

### 2. 创建 UI 页面

新建 `src/ui/page_your_feature.py`，遵循以下模板：

```python
from .nav_bar import create_nav_bar

class PageYourFeature(QWidget):
    def __init__(self, navigator):
        super().__init__()
        self.navigator = navigator
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # 标题、副标题、输入表单、按钮、日志区域...
        # （参考现有页面实现）

        # 底部导航栏（必须）
        nav = create_nav_bar(self.navigator, self)
        layout.addLayout(nav)

        self.setLayout(layout)
```

**关键约定：**
- 构造函数接收 `navigator` 对象（不是 `stacked_widget`）
- 底部必须使用 `create_nav_bar(self.navigator, self)` 创建导航栏
- 按钮使用 `setMinimumSize()` 而非 `setFixedSize()`
- 日志区域使用 `addWidget(widget, 1)` 添加 stretch 因子

### 3. 注册到目录页

编辑 `src/ui/directory_page.py`，在 `CATEGORIES` 列表中添加条目：

```python
CATEGORIES = [
    ("编写前", [
        # ... 现有功能 ...
        ("你的功能名", "功能描述", 9),  # index 9 = 新页面在 stacked_widget 中的位置
    ]),
    # ...
]
```

### 4. 注册到主窗口

编辑 `src/ui/main_window.py`：

```python
# 1. 导入新页面
from .page_your_feature import PageYourFeature

# 2. 在 FEATURE_ORDER 中添加新 index（保持目录顺序）
FEATURE_ORDER = [2, 3, 4, 5, 6, 7, 8, 9]  # 追加 9

# 3. 在 __init__ 中添加页面
self.page_your_feature = PageYourFeature(self.navigator)
self.stacked.addWidget(self.page_your_feature)
```

**注意：** `FEATURE_ORDER` 中的顺序必须与 `CATEGORIES` 中的顺序一致。

## Worker 模式

所有耗时操作必须在 QThread 中执行，遵循以下模式：

```python
class YourWorker(QThread):
    text_written = pyqtSignal(str)           # 日志输出信号
    finished_with_result = pyqtSignal(str)   # 可选：完成后传递结果路径

    def __init__(self, params...):
        super().__init__()
        self._params = params

    def run(self):
        # 调用 core 函数，通过 callback 或 stdout 重定向输出日志
        result = core_function(self._params, callback_print=self._emit_log)
        self.finished_with_result.emit(result)

    def _emit_log(self, text):
        self.text_written.emit(text)
```

## UI 设计规范

### 窗口与布局

| 项目 | 规范 |
|------|------|
| 主窗口默认大小 | 900×700 px |
| 最小窗口大小 | 900×700 px |
| 页面边距 | 20px (水平), 15px (垂直) |
| 元素间距 | 8-10px |
| 卡片内边距 | 10px |
| 卡片圆角 | 6px |

### 字体大小

| 元素类型 | 字体大小 |
|----------|----------|
| 页面标题 | 14px，加粗 |
| 页面副标题 | 10px，灰色 |
| 表单标签 | 11px |
| 输入框内容 | 11px |
| 按钮文字 | 11-12px |
| 结果数值 | 16px，加粗 |
| 结果标签 | 9px |
| 日志区域 | 10px，等宽字体 |

### 按钮尺寸（使用 setMinimumSize，允许拉伸）

| 按钮类型 | 最小尺寸 |
|----------|----------|
| 主操作按钮 | 100×30 px |
| 导航按钮 | 80×28 px |
| 功能按钮 | 70×28 px |

### 颜色规范

| 用途 | 色值 |
|------|------|
| 主色调 | #3498db |
| 主色调悬停 | #2980b9 |
| 主色调按下 | #1f618d |
| 标题文字 | #2c3e50 |
| 正文文字 | #495057 |
| 次要文字 | #7f8c8d |
| 背景色 | #f8f9fa |
| 边框色 | #e9ecef |
| 成功色 | #27ae60 |

### 交互规范

- 所有可点击元素设置 `cursor: PointingHandCursor`
- 输入框聚焦时边框变为蓝色（#3498db）
- 按钮悬停时颜色加深
- 成功操作显示 1.5 秒提示后恢复

### 全屏与窗口化

- 所有页面支持窗口最大化显示
- 使用 `setMinimumSize()` 代替 `setFixedSize()`
- 日志区域和输入框使用 `stretch` 因子自适应
- 窗口缩小时内容不堆叠、不遮挡

## 踩坑记录

### 1. 标题居中 + 右上角按钮：不能用 Layout 方案

**场景**：页面标题需要在整个窗口宽度内居中，同时右上角有一个操作按钮（如"自定义提示词"）。

**错误尝试**（均失败）：
- `[stretch] [title] [btn] [stretch]` — 标题和按钮一起被挤到中间，标题偏左
- `[title] [stretch] [btn]` — title 是小 label，stretch 把它推到左边
- 嵌套 `QHBoxLayout`（stretch + title + stretch）放在外层 layout 里 — **嵌套的 QLayout 不会自动扩展填满空间**（不像 QWidget），标题依然偏左
- 用 `QWidget` 包裹嵌套 layout — QWidget 会扩展，但标题居中区域是「窗口宽度 - 按钮宽度」，不是整个窗口宽度，标题仍然偏左

**根因**：只要标题和按钮在同一个 `QHBoxLayout` 里，按钮占据的右侧空间就会让标题的可用宽度变窄，标题永远无法在整个窗口宽度内居中。

**正确方案**：绝对定位 + `resizeEvent`

```python
# 标题和按钮作为页面的直接子控件，不放入 layout
self._title = QLabel("页面标题", self)
self._subtitle = QLabel("副标题", self)
self.prompt_btn = QPushButton("操作按钮", self)

# layout 顶部预留空间
layout.addSpacing(55)

def resizeEvent(self, event):
    super().resizeEvent(event)
    w = self.width()
    # 标题基于整个窗口宽度居中
    title_w = self._title.sizeHint().width()
    self._title.setGeometry((w - title_w) // 2, 15, title_w, 24)
    # 副标题居中对齐
    sub_w = self._subtitle.sizeHint().width()
    self._subtitle.setGeometry((w - sub_w) // 2, 38, sub_w, 16)
    # 按钮贴右上角
    btn_w = self.prompt_btn.sizeHint().width()
    self.prompt_btn.move(w - btn_w - 10, 12)
```

**适用场景**：任何需要标题在整个窗口内居中、同时同行有固定宽度控件（按钮等）的情况。

### 2. Worker 与 Core 职责混淆：业务逻辑不能写在 Worker 里

**场景**：AI 辅助开发时，容易将业务逻辑（数据处理、文件转换、格式生成）直接写在 Worker 文件中，导致 Core 层空洞、Worker 层臃肿。

**错误示例**（重构前）：
```
workers/excel_to_word_worker.py    # 300+ 行，包含完整的 Excel→Word 转换逻辑
workers/excel_to_word_flow_worker.py # 300+ 行，包含流程图生成 + Word 转换逻辑
core/excel_to_word.py              # 不存在
core/excel_to_word_flow.py         # 不存在
```

**根因**：AI 生成代码时，倾向于把所有逻辑放在一个文件里，没有严格遵循分层架构。如果 README 没有明确约束，后续维护者（包括 AI）会继续在 Worker 里堆积逻辑。

**正确架构**：
```
core/excel_to_word.py             # 纯业务逻辑：读取 Excel → 解析 → 生成 Word
core/excel_to_word_flow.py        # 纯业务逻辑：读取 Excel → 解析 → 生成流程图 → 生成 Word
workers/excel_to_word_worker.py   # 仅 QThread 壳子：调用 core 函数，转发日志信号
workers/excel_to_word_flow_worker.py # 仅 QThread 壳子：调用 core 函数，转发日志信号
```

**Worker 标准写法**：
```python
class YourWorker(QThread):
    text_written = pyqtSignal(str)

    def run(self):
        # 重定向 stdout 以捕获日志
        old_stdout = sys.stdout
        sys.stdout = OutputRedirector(self._emit_output)
        try:
            # 调用 core 函数，业务逻辑零耦合
            your_business_logic(
                self.param1, self.param2,
                callback_print=self._emit_output,
            )
        finally:
            sys.stdout = old_stdout

    def _emit_output(self, text):
        self.text_written.emit(text)
```

**踩坑教训**：
1. **Worker 只做两件事**：管理 QThread 生命周期 + 调用 core 函数
2. **业务逻辑必须在 Core**：确保可独立测试、可复用、无 Qt 依赖
3. **AI 生成代码后必须审查分层**：检查 Worker 文件是否超过 50 行（超过说明可能混入了业务逻辑）
4. **README 必须明确约束**：在"添加新功能指南"中强调分层规则

## 依赖

- Python 3.10+
- PyQt6, openpyxl, python-docx, aiohttp, Pillow

## 开发文档

- **[PRD.md](docs/PRD.md)** — 产品需求文档

---

*最后更新：2026-05-14*
