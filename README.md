# COSMIC-GUI 项目说明文档

## 一、项目概述

**COSMIC-GUI** 是一个基于 PyQt6 的桌面应用程序，用于自动化 COSMIC 方法论相关的 Excel 表格处理工作。

### 核心功能（四个页面流程）

```
Page1 (欢迎页) → Page2 (自动填空) → Page3 (大模型填充) → Page4 (Excel转Word)
```

| 页面 | 文件 | 功能 |
|------|------|------|
| Page1 | page1_welcome.py | 展示欢迎页和准备事项 |
| Page2 | page2_auto_fill.py | 根据 I、K 列自动填写 H、J、L 列 |
| Page3 | page3_llm_fill.py | 调用 LLM API 填写 M 列 |
| Page4 | page4_excel_to_word.py | 将 Excel 转换为 Word 文档 |

---

## 二、文件架构

```
src/
├── gui.py                      # 程序入口，QApplication 初始化
├── main_window.py              # 主窗口，管理 QStackedWidget 和页面切换
├── core/                       # 核心业务逻辑（纯函数，无 UI）
│   ├── auto_fill.py            # 自动填空逻辑（读取/写入 Excel）
│   └── llm_fill.py             # LLM 填充逻辑（调用 API 生成字段）
├── ui/                         # UI 页面
│   ├── main_window.py          # 主窗口
│   ├── page1_welcome.py         # 欢迎页
│   ├── page2_auto_fill.py       # 自动填空页
│   ├── page3_llm_fill.py        # LLM 填充页
│   ├── page4_excel_to_word.py   # Excel 转 Word 页
│   └── styles.py               # 样式配置（预留）
├── workers/                     # 后台工作线程（QThread）
│   ├── auto_fill_worker.py      # 自动填空后台线程
│   ├── llm_fill_worker.py       # LLM 填充后台线程
│   └── excel_to_word_worker.py  # Excel 转 Word 后台线程
└── utils/
    └── resource_path.py         # 资源路径工具（PyInstaller 打包用）
```

---

## 三、页面设计与开发的黄金法则

**每次新增页面或修改页面时，必须同步更新以下内容，否则会出现断层：**

### 3.1 新增页面（以 Page4 为例）

| 步骤 | 必须更新的文件 | 修改内容 |
|------|---------------|---------|
| 1 | ui/page4_xxx.py | 创建新页面类，继承 QWidget |
| 2 | ui/main_window.py | import 页面类，在 __init__ 中创建实例，addWidget 添加到 stacked |
| 3 | **前一页**（page3_llm_fill.py） | 在导航按钮区域添加「下一步」按钮，指向新页面索引 |

### 3.2 新增后台线程（以 excel_to_word_worker.py 为例）

| 步骤 | 必须更新的文件 | 修改内容 |
|------|---------------|---------|
| 1 | workers/xxx_worker.py | 创建 QThread 子类，信号 text_written、finished |
| 2 | ui/对应的page.py | import worker 类，创建实例，连接信号，启动线程 |

### 3.3 删除/修改页面的检查清单

- [ ] ui/main_window.py — 是否移除/修改了 addWidget 和实例化代码
- [ ] **前一页** — 导航按钮是否指向了正确的页面索引
- [ ] workers/ 相关worker — 是否需要一并删除或修改

---

## 四、页面跳转逻辑（页面索引）

QStackedWidget 的页面顺序由 `main_window.py` 中 `addWidget` 的顺序决定：

```python
self.stacked.addWidget(self.page1)   # 索引 0
self.stacked.addWidget(self.page2)   # 索引 1
self.stacked.addWidget(self.page3)   # 索引 2
self.stacked.addWidget(self.page4)   # 索引 3
```

页面内跳转方式：`self.stacked_widget.setCurrentIndex(N)`

---

## 五、各页面的核心逻辑

### Page2 - 自动填空
- **输入**：Excel 文件路径 + Sheet 名称
- **输出**：直接在原文件上修改 H、J、L 列
- **核心函数**：`core/auto_fill.py` 中的 `auto_fill(file_path, sheet_name)`
- **Worker**：`workers/auto_fill_worker.py` → `AutoFillWorker`

### Page3 - 大模型填充
- **输入**：API_KEY、MODEL、URL、Excel 文件路径
- **输出**：`大模型填充后.xlsx`
- **核心函数**：`core/llm_fill.py` 中的 `llm_fill_async(...)`
- **Worker**：`workers/llm_fill_worker.py` → `LLMFillWorker`
- **特殊**：页面有 `set_input_file(path)` 方法，由 Page2 成功回调自动填充路径

### Page4 - Excel转Word
- **输入**：用户手动选择的 Excel 文件
- **输出**：`原文件名_转换后.docx`（自动生成）
- **核心逻辑**：直接封装 `docs/example/excel_to_word-v5.py` 的转换逻辑
- **Worker**：`workers/excel_to_word_worker.py` → `ExcelToWordWorker`

---

## 六、Worker 模式详解

所有耗时操作必须放在 **QThread 后台线程** 中执行，避免阻塞 UI。

### Worker 标准结构

```python
class XxxWorker(QThread):
    text_written = pyqtSignal(str)  # 日志输出信号

    def __init__(self, 参数...):
        super().__init__()
        # 保存参数

    def run(self):
        # 1. 重定向 stdout 到信号
        old_stdout = sys.stdout
        sys.stdout = OutputRedirector(self._emit_output)
        try:
            # 2.执行业务逻辑
            self._do_work()
        finally:
            sys.stdout = old_stdout

    def _emit_output(self, text):
        self.text_written.emit(text)
```

### OutputRedirector 标准实现

```python
class OutputRedirector(QObject):
    text_written = pyqtSignal(str)

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def write(self, text):
        if text.strip():
            self.callback(text)

    def flush(self):
        pass
```

---

## 七、资源路径

所有资源文件（图标、模板等）通过 `utils/resource_path.py` 的 `resource_path()` 函数获取。

**当前资源路径约定：**
- 应用图标：`ui/应用图标.png`
- 模板文件：`模板/cosmic-自动填充-模板.xlsx`

---

## 八、样式规范（Web 风格复刻）

Page1 和 Page4 已使用统一的 Web 风格布局：

- **背景色**：`#f5f5f5`
- **容器宽度**：固定 600px，水平居中
- **字体**：无衬线字体（system-ui 默认）
- **按钮**：
  - 主按钮：背景 `#3b82f6`，白色文字，160×44px，圆角 6px
  - 次按钮：背景 `#f3f4f6`，深色文字，160×44px，圆角 6px

---

## 九、未来功能扩展建议

1. **如果需要新增页面**：参考 Page4 的完整实现
2. **如果需要调用新的 API**：参考 Page3 + llm_fill_worker.py 的 Worker 模式
3. **如果需要新的 Excel 处理逻辑**：参考 core/auto_fill.py 添加到 core/ 目录
4. **如果需要修改 UI 风格**：统一在各 page 的 `_setup_ui()` 中修改样式，或提取到 styles.py

---

## 十、运行方式

```bash
cd d:/cod/AI/cosmic-GUI/src
python gui.py
```

---

*文档创建时间：2026-04-26*
*最后更新：添加 Page4 (Excel转Word) 功能*