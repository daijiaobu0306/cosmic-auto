# COSMIC-GUI 开发计划

> **对应 PRD**：[docs/PRD.md](PRD.md)（v2.1）  
> **创建日期**：2026-05-02  
> **用途**：跨对话协作开发指南。每个 Task 可在单次对话中完成，完成后勾选 checkbox 并更新文档。

---

## 开发进度总览

| 阶段 | Task | 名称 | 状态 |
|------|------|------|------|
| Phase 1 | T1 | 人天计算器 | ✅ 已完成 |
| Phase 1 | T2 | AI 识图（核心逻辑 + Worker） | ✅ 已完成 |
| Phase 1 | T3 | TXT 解析 + 生成 Excel（核心逻辑 + Worker） | ✅ 已完成 |
| Phase 1 | T4 | AI 识图 + 生成 Excel（UI 页面） | ✅ 已完成 |
| Phase 1 | T5 | 自动画流程图 | ☐ 待开发 |
| Phase 1 | T6 | DDL 辅助填充 | ☐ 待开发 |
| Phase 2 | T7 | 顶部 Tab 导航重构 | ☐ 待开发 |
| Phase 2 | T8 | 跨页面数据传递 + API 配置共享 | ☐ 待开发 |
| Phase 3 | T9 | 集成测试 + 文档更新 | ☐ 待开发 |

---

## 开发约定

### 代码模式（必须遵循）

每个新功能遵循以下结构：

```
src/core/xxx.py          ← 纯业务逻辑（无 Qt 依赖），函数式
src/workers/xxx_worker.py ← QThread 子类，桥接 core 和 UI
src/ui/page_xxx.py       ← QWidget 子类，UI 界面
```

### Worker 标准模板

```python
class XxxWorker(QThread):
    text_written = pyqtSignal(str)

    def __init__(self, 参数...):
        super().__init__()
        self._params = ...

    def run(self):
        old_stdout = sys.stdout
        sys.stdout = OutputRedirector(self._emit_output)
        try:
            # 调用 core 函数
            result = core_function(self._params)
        finally:
            sys.stdout = old_stdout

    def _emit_output(self, text):
        self.text_written.emit(text)
```

### 页面标准模板

```python
class PageXxx(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self._setup_ui()

    def _setup_ui(self):
        # 构建 UI
        ...

    def _start_task(self):
        # 验证输入 → 禁用按钮 → 创建 Worker → 连接信号 → 启动
        self.worker = XxxWorker(...)
        self.worker.text_written.connect(self._append_log)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _append_log(self, text):
        self.log_area.append(text)

    def _on_finished(self):
        self.start_btn.setEnabled(True)
```

### AI 调用模式（参考现有 llm_fill.py）

- 使用 `aiohttp` 异步 HTTP 调用
- OpenAI 兼容格式（`/v1/chat/completions`）
- 并发控制：`asyncio.Semaphore(10)`
- Worker 内用 `asyncio.run()` 启动事件循环

---

## Phase 1：独立功能开发

---

### T1：人天计算器

> **PRD 对应**：模块一（2.1）  
> **依赖**：无  
> **预计工作量**：0.5 次对话

#### 目标

创建一个简单的计算器页面，输入项目金额、扣减率、人天单价，计算 COSMIC 行数。

#### 文件变更

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `src/ui/page_calculator.py` | 计算器页面 |
| 修改 | `src/ui/main_window.py` | 添加页面到 stacked widget |
| 修改 | `src/ui/page1_welcome.py` | 添加「打开计算器」按钮 |
| 修改 | `src/ui/page2_auto_fill.py` | 更新导航索引 |
| 修改 | `src/ui/page3_llm_fill.py` | 更新导航索引 |
| 修改 | `src/ui/page4_excel_to_word.py` | 更新导航索引 |

#### 核心逻辑

```python
def calculate_workload(project_amount: float, deduction_rate: float, daily_price: float) -> dict:
    """
    project_amount: 项目金额（元）
    deduction_rate: 预计扣减率（%），如 15 表示 15%
    daily_price: 人天单价（元/天）
    返回: {"lines": int, "budget": float}
    """
    actual_budget = project_amount / (1 - deduction_rate / 100)
    lines = math.ceil(actual_budget / daily_price)
    return {"lines": lines, "budget": actual_budget}
```

#### UI 布局

```
┌─────────────────────────────────────┐
│         COSMIC 人天单价计算器          │
├─────────────────────────────────────┤
│  项目金额（元）：[____________]        │
│  预计扣减率（%）：[____________]        │
│  人天单价（元/天）：[____________]      │
│                                     │
│  [    计算    ]                      │
│                                     │
│  ┌─────────────────────────────┐    │
│  │  计算结果                      │    │
│  │  实际预算：¥XXX               │    │
│  │  需编写行数：XXX 行            │    │
│  └─────────────────────────────┘    │
│  [    复制结果    ]                  │
└─────────────────────────────────────┘
```

#### 验收标准

- [x] 输入三个参数后点击计算，正确显示行数和实际预算
- [x] 边界值：扣减率 0%、扣减率接近 100%、金额为 0 时有合理提示
- [x] 复制结果按钮可将结果复制到剪贴板
- [x] 页面可通过 stacked widget 索引正常切换

---

### T2：AI 识图 — 核心逻辑 + Worker

> **PRD 对应**：模块二（2.2）  
> **依赖**：无  
> **预计工作量**：1 次对话

#### 目标

实现 AI 识图的核心逻辑：调用多模态模型识别截图，输出带层级缩进的 TXT 文件。

#### 文件变更

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `src/core/ai_recognize.py` | 识图核心逻辑 |
| 新增 | `src/workers/ai_recognize_worker.py` | Worker 线程 |

#### core/ai_recognize.py 核心函数

```python
async def recognize_images(
    image_folder: str,       # 截图文件夹路径
    system_name: str,        # 系统名称（一级功能）
    system_desc: str,        # 系统描述
    api_key: str,
    api_url: str,
    model_name: str,
) -> str:
    """
    遍历文件夹中的 JPG/PNG，逐张调用多模态模型识别。
    返回：带层级缩进的 TXT 文本内容。
    """
```

#### 提示词结构

```python
SYSTEM_PROMPT = """你是一个软件功能分析专家。用户会给你一个软件系统的截图，你需要识别截图中的功能模块和具体功能点。

系统名称：{system_name}
系统描述：{system_desc}

请按照以下格式输出：
1 二级功能名称
  1.1 三级功能名称
        功能过程1
        功能过程2
  1.2 三级功能名称
        功能过程3

规则：
1. 使用序号+缩进表示层级，不使用树形符号
2. 二级功能：无缩进，序号为 1、2、3...
3. 三级功能：2空格缩进，序号为 1.1、1.2...
4. 功能过程：8空格缩进，无序号，用动词开头（查询/添加/修改/删除/导出/展示）
5. 只输出功能结构，不输出其他解释文字
6. 输出中文"""
```

#### 多模态 API 调用格式

```python
# OpenAI 兼容格式（支持 GPT-4o、Qwen-VL 等）
{
    "model": model_name,
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [
            {"type": "text", "text": "请识别这张截图中的功能："},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]}
    ]
}
```

#### workers/ai_recognize_worker.py

```python
class AIRecognizeWorker(QThread):
    text_written = pyqtSignal(str)

    def __init__(self, image_folder, system_name, system_desc, api_key, api_url, model_name):
        super().__init__()
        # 保存参数

    def run(self):
        # 重定向 stdout
        # 调用 recognize_images()
        # 输出结果到 stdout（通过信号传递给 UI）
```

#### 验收标准

- [x] 能遍历文件夹中的 JPG/PNG 文件
- [x] 能正确将图片编码为 base64 并发送给多模态 API
- [x] API 返回结果能正确拼接为带层级缩进的 TXT
- [x] 并发控制正常（Semaphore 限制）
- [x] 失败重试机制（最多 2 次）
- [x] 输出 TXT 格式符合 PRD 2.2.5 规范
- [x] 多模态 API 兼容阿里云百炼嵌套格式（image_url: {url: ...}）
- [x] Bearer Token 认证方式正确

---

### T3：TXT 解析 + 生成 Excel — 核心逻辑 + Worker

> **PRD 对应**：模块三（2.3）  
> **依赖**：T2（TXT 格式定义，但可并行开发）  
> **预计工作量**：1 次对话

#### 目标

解析模块二产出的 TXT 文件，生成符合 COSMIC 模板格式的 Excel（含合并单元格和 ERWX）。

#### 文件变更

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `src/core/txt_to_excel.py` | TXT 解析 + Excel 生成 |
| 新增 | `src/workers/txt_to_excel_worker.py` | Worker 线程 |

#### core/txt_to_excel.py 核心函数

```python
def parse_txt(txt_content: str) -> list[dict]:
    """
    解析带层级缩进的 TXT，返回结构化数据。

    返回格式：
    [
        {
            "level2": "手机APP监控",
            "level3": "启动分析",
            "process": "查询APP启动次数"
        },
        ...
    ]

    解析规则：
    - 无缩进 + 数字序号 → 二级功能
    - 2空格 + 数字序号 → 三级功能
    - 8空格 + 无序号 → 功能过程
    """


def generate_excel(
    parsed_data: list[dict],
    system_name: str,
    output_path: str
) -> str:
    """
    根据解析数据生成 COSMIC Excel。

    生成规则：
    - B/C 列：= system_name，整列合并
    - D 列：二级功能，同名合并
    - E 列：三级功能，同名合并
    - F/G 列：留空
    - H 列：留空，按 I 列合并对齐
    - I 列：功能过程，每个合并 4 行
    - J 列：留空
    - K 列：每个 I 对应 4 行 E/R/W/X
    - L/M/N 列：留空

    返回：输出文件路径
    """
```

#### 合并单元格实现要点

```python
# 使用 openpyxl 的 merge_cells
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Side

# 合并示例
ws.merge_cells(f'B2:B{total_rows}')     # 需求名称 - 整列合并
ws.merge_cells(f'C2:C{total_rows}')     # 一级功能 - 整列合并
ws.merge_cells(f'D{start}:D{end}')      # 二级功能 - 按范围合并
ws.merge_cells(f'I{start}:I{end}')      # 功能过程 - 每4行合并
ws.merge_cells(f'H{start}:H{end}')      # 触发事件 - 按 I 列对齐
```

#### K 列 ERWX 生成规则

```python
DATA_MOVE_TYPES = ['E', 'R', 'W', 'X']

# 每个功能过程生成 4 行
for process in processes:
    for move_type in DATA_MOVE_TYPES:
        row = {
            'I': process['process'],
            'K': move_type,
        }
```

#### workers/txt_to_excel_worker.py

```python
class TxtToExcelWorker(QThread):
    text_written = pyqtSignal(str)

    def __init__(self, txt_path, system_name, output_path):
        super().__init__()

    def run(self):
        # 1. 读取 TXT 文件
        # 2. 调用 parse_txt()
        # 3. 调用 generate_excel()
        # 4. 输出日志
```

#### 验收标准

- [ ] 能正确解析 TXT 的三级层级结构（二级/三级/功能过程）
- [ ] 生成的 Excel 列结构与模板一致（14 列）
- [ ] B/C 列整列合并，值为系统名称
- [ ] D 列按二级功能合并，E 列按三级功能合并
- [ ] I 列每个功能过程合并 4 行
- [ ] H 列按 I 列合并范围对齐
- [ ] K 列每个功能过程为 E/R/W/X 四行
- [ ] 合并单元格的值正确写入（只在合并区域的第一个单元格写值）
- [ ] 生成的 Excel 可被现有 Page2（自动填充）正常读取

---

### T4：AI 识图 + 生成 Excel — UI 页面

> **PRD 对应**：模块二（2.2.9）+ 模块三（2.3.9）  
> **依赖**：T2、T3  
> **预计工作量**：1 次对话

#### 目标

创建「AI 识图」Tab 页面，整合 T2 和 T3 的功能，提供完整的用户交互界面。

#### 文件变更

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `src/ui/page_ai_recognize.py` | AI 识图页面 |
| 修改 | `src/ui/main_window.py` | 添加页面到 stacked widget |

#### UI 布局

```
┌─────────────────────────────────────────────────┐
│                AI 识图生成功能清单                  │
├─────────────────────────────────────────────────┤
│  系统名称：[________________________]            │
│  系统描述：[________________________]            │
│  截图文件夹：[________________] [选择文件夹]      │
│  API Key：  [________________________]           │
│  API URL：  [________________________]           │
│  模型名称：  [________________________]           │
│                                                 │
│  [    开始识别    ]  进度：3/10                   │
│  ┌─────────────────────────────────────────┐    │
│  │  日志输出区域                              │    │
│  │  > 正在识别第 1 张图片...                   │    │
│  │  > 识别完成，发现 3 个二级功能               │    │
│  └─────────────────────────────────────────┘    │
│                                                 │
│  [打开功能清单TXT] [确认完成，生成Excel]          │
│                                                 │
│  ── 生成 Excel ──                               │
│  TXT文件路径：[________________] [选择文件]       │
│  [    预览    ]  [    导出 Excel    ]            │
│  ┌─────────────────────────────────────────┐    │
│  │  Excel 预览区域（表格）                     │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

#### 页面逻辑流程

```
1. 用户填写表单 → 点击「开始识别」
2. 创建 AIRecognizeWorker → 连接信号 → 启动
3. Worker 完成 → 生成 TXT 文件 → 日志提示
4. 用户点击「打开功能清单」→ 调用系统默认编辑器打开 TXT
5. 用户人工审核修改后 → 点击「确认完成，生成 Excel」
6. 自动填入 TXT 路径 → 用户点击「预览」
7. 创建 TxtToExcelWorker → 在预览区域展示结果
8. 用户确认 → 点击「导出 Excel」→ 选择保存路径
```

#### 打开文件功能

```python
import subprocess
import os

def open_file_with_default_app(file_path: str):
    """用系统默认应用打开文件"""
    if os.name == 'nt':  # Windows
        os.startfile(file_path)
    else:
        subprocess.run(['xdg-open', file_path])
```

#### 验收标准

- [x] 表单输入验证完整（所有必填项非空、文件夹存在）
- [x] 开始识别按钮点击后禁用，完成后恢复
- [x] 日志区域实时显示识别进度
- [x] 识别完成后 TXT 文件路径自动填入下方区域
- [x] 「打开功能清单」按钮可调用系统编辑器打开 TXT
- [x] 预览功能正确展示 Excel 内容（含合并单元格的视觉效果）
- [x] 导出功能可选择保存路径并生成 Excel 文件

---

### T5：自动画流程图

> **PRD 对应**：模块七（2.7）  
> **依赖**：无（独立扩展 Page4）  
> **预计工作量**：1 次对话

#### 目标

在 Excel 转 Word 过程中，自动为每个四级/五级标题生成 Mermaid 时序图，插入 Word 文档。

#### 文件变更

| 操作 | 文件 | 说明 |
|------|------|------|
| 修改 | `src/workers/excel_to_word_worker.py` | 添加流程图生成逻辑 |
| 修改 | `src/ui/page4_excel_to_word.py` | 添加 Checkbox 和 mmdc 检测 |

#### 核心逻辑：Mermaid 代码生成

```python
def generate_mermaid_code(rows: list[dict]) -> str:
    """
    根据一组数据行生成 Mermaid 时序图代码。

    rows: [{"sender": "用户", "receiver": "系统", "action": "查询APP启动次数", "is_return": False}, ...]

    返回：
    sequenceDiagram
        用户->>系统: 查询APP启动次数
        系统-->>用户: 返回查询结果
    """
    code = "sequenceDiagram\n"
    for row in rows:
        arrow = "-->>" if row['is_return'] else "->>"
        code += f"    {row['sender']}{arrow}{row['receiver']}: {row['action']}\n"
    return code
```

#### F 列解析（发起者/接收者）

```python
import re

def parse_sender_receiver(f_value: str) -> tuple[str, str]:
    """
    解析 F 列的发起者/接收者。

    输入示例："发起者：用户\n接收者：系统"
    返回：("用户", "系统")
    """
    sender_match = re.search(r'发起者[：:]\s*(.+)', f_value)
    receiver_match = re.search(r'接收者[：:]\s*(.+)', f_value)
    sender = sender_match.group(1).strip() if sender_match else "未知"
    receiver = receiver_match.group(1).strip() if receiver_match else "未知"
    return sender, receiver
```

#### K 列判断返回动作

```python
def is_return_action(k_value: str) -> bool:
    """
    根据 K 列判断是否为返回动作。
    X（输出/展示）视为返回，E/R/W 视为正向。
    """
    return str(k_value).strip().upper() == 'X'
```

#### Mermaid 渲染

```python
import subprocess
import tempfile
import os

def render_mermaid(mermaid_code: str, output_path: str) -> bool:
    """
    调用 mmdc 将 Mermaid 代码渲染为 PNG。

    需要：Node.js + @mermaid-js/mermaid-cli
    安装命令：npm install -g @mermaid-js/mermaid-cli
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
        f.write(mermaid_code)
        mmd_path = f.name

    try:
        result = subprocess.run(
            ['mmdc', '-i', mmd_path, '-o', output_path, '-t', 'transparent', '-b', 'transparent'],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    finally:
        os.unlink(mmd_path)
```

#### mmdc 安装检测

```python
def check_mmdc_installed() -> bool:
    """检测 mmdc 是否已安装"""
    try:
        result = subprocess.run(['mmdc', '--version'], capture_output=True, timeout=5)
        return result.returncode == 0
    except FileNotFoundError:
        return False
```

#### UI 变更（page4_excel_to_word.py）

在现有页面中添加：

```python
# 流程图选项
self.flowchart_checkbox = QCheckBox("自动生成流程图")
self.flowchart_checkbox.stateChanged.connect(self._on_flowchart_toggle)

# mmdc 状态指示
self.mmdc_status = QLabel()
self._update_mmdc_status()  # 绿色/红色指示灯
```

#### excel_to_word_worker.py 修改

在现有的 `run()` 方法中，标题生成后插入流程图：

```python
# 在每个标题段落 flush 后
if self.generate_flowchart and content_rows:
    mermaid_code = generate_mermaid_code(content_rows)
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        if render_mermaid(mermaid_code, tmp.name):
            doc.add_picture(tmp.name, width=Inches(5.5))
            os.unlink(tmp.name)
```

#### 验收标准

- [ ] Checkbox 勾选后，mmdc 状态指示灯正确显示（绿色/红色）
- [ ] mmdc 未安装时，Checkbox 不可勾选，提示安装命令
- [ ] 能正确从 F 列解析出发起者/接收者
- [ ] 能正确从 K 列判断返回动作（X → 虚线）
- [ ] 生成的 Mermaid 语法正确
- [ ] 渲染的 PNG 图片正确插入 Word 文档（在标题下方）
- [ ] Mermaid 语法错误时跳过该图，日志提示，不中断流程
- [ ] F 列无法解析时跳过该行，日志提示

---

### T6：DDL 辅助填充

> **PRD 对应**：模块五（2.5）  
> **依赖**：无（独立扩展 Page3）  
> **预计工作量**：1 次对话

#### 目标

在 LLM 填充数据属性时，可选用数据库建表语句作为上下文，使生成结果更贴合实际系统。

#### 文件变更

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `src/core/ddl_parser.py` | DDL 解析逻辑 |
| 修改 | `src/core/llm_fill.py` | 添加 DDL 上下文注入 |
| 修改 | `src/workers/llm_fill_worker.py` | 传递 DDL 参数 |
| 修改 | `src/ui/page3_llm_fill.py` | 添加 DDL 区域 |

#### core/ddl_parser.py

```python
import re
from pathlib import Path

def parse_ddl_folder(folder_path: str) -> dict[str, list[dict]]:
    """
    遍历文件夹中的 .sql 文件，解析 CREATE TABLE 语句。

    返回格式：
    {
        "user_info": {
            "table_comment": "用户信息表",  # 如有 COMMENT
            "columns": [
                {"name": "id", "type": "bigint", "comment": "主键ID"},
                {"name": "user_name", "type": "varchar(64)", "comment": "用户名"},
                ...
            ]
        },
        ...
    }
    """
    tables = {}
    for sql_file in Path(folder_path).glob("*.sql"):
        content = sql_file.read_text(encoding='utf-8')
        tables.update(parse_sql_content(content))
    return tables


def parse_sql_content(sql: str) -> dict[str, list[dict]]:
    """解析 SQL 内容中的 CREATE TABLE 语句"""
    # 匹配 CREATE TABLE 语句
    # 提取表名、字段名、字段类型、COMMENT
    # 兼容 MySQL/PostgreSQL/Oracle 常见语法
    ...
```

#### DDL 解析正则

```python
# CREATE TABLE 匹配
TABLE_PATTERN = re.compile(
    r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\']?(\w+)[`"\']?\s*\((.*?)\)',
    re.IGNORECASE | re.DOTALL
)

# 字段匹配（每行一个字段定义）
COLUMN_PATTERN = re.compile(
    r'[`"\']?(\w+)[`"\']?\s+(\w+(?:\([^)]*\))?)\s*(?:.*?COMMENT\s+[\'"]([^\'"]*))?',
    re.IGNORECASE
)

# 表注释匹配
TABLE_COMMENT_PATTERN = re.compile(
    r'COMMENT\s*[=]\s*[\'"]([^\'"]*)[\'"]',
    re.IGNORECASE
)
```

#### LLM 翻译字段名为中文

```python
async def translate_fields_to_chinese(
    tables: dict, api_key: str, api_url: str, model_name: str
) -> dict[str, dict]:
    """
    调用 LLM 将表名和字段名翻译为中文。

    返回格式（与输入结构相同，但增加了 chinese_name 字段）。
    """
    prompt = f"""请将以下数据库表和字段名翻译为中文，保持原有结构。

{format_tables_for_prompt(tables)}

输出格式（JSON）：
{{
    "表英文名": {{
        "table_chinese": "表中文名",
        "columns": {{
            "字段英文名": "字段中文名",
            ...
        }}
    }}
}}"""
    # 调用 LLM API
    ...
```

#### llm_fill.py 修改

```python
def build_ddl_context(tables_chinese: dict) -> str:
    """
    构建 DDL 上下文字符串，注入到 LLM prompt 中。

    格式：
    系统数据库表结构：
    - 用户信息表(user_info): ID, 用户名, 手机号, 邮箱...
    - 订单表(order_info): 订单号, 用户ID, 金额, 创建时间...
    """
    context = "系统数据库表结构：\n"
    for table_name, info in tables_chinese.items():
        columns = ", ".join(info['columns'].values())
        context += f"- {info['table_chinese']}({table_name}): {columns}\n"
    return context
```

#### llm_fill_async 修改

```python
async def llm_fill_async(
    excel_path: str,
    api_key: str,
    model: str,
    url: str,
    ddl_context: str = None,  # 新增参数
) -> str:
    # 在构建 prompt 时注入 DDL 上下文
    system_prompt = SYSTEM_PROMPT
    if ddl_context:
        system_prompt += f"\n\n参考数据库表结构：\n{ddl_context}\n请优先使用上述表中的实际字段名，并适当扩展。"
```

#### UI 变更（page3_llm_fill.py）

```python
# 新增：DDL 辅助区域（可折叠）
self.ddl_group = QGroupBox("建表语句辅助（可选）")
self.ddl_group.setCheckable(True)
self.ddl_group.setChecked(False)

# 文件夹选择
self.ddl_folder_input = QLineEdit()
self.ddl_folder_btn = QPushButton("选择文件夹")

# DDL 解析状态
self.ddl_status = QLabel("未加载")
self.ddl_preview = QTextEdit()  # 显示解析出的表和字段数量
self.ddl_load_btn = QPushButton("加载建表语句")
```

#### 验收标准

- [ ] 能正确解析 MySQL CREATE TABLE 语句（表名、字段名、字段类型）
- [ ] 能解析 COMMENT 注释
- [ ] 一个 .sql 文件中可包含多个 CREATE TABLE
- [ ] LLM 翻译字段名为中文，结果合理
- [ ] DDL 上下文正确注入到 LLM prompt 中
- [ ] 启用 DDL 辅助后，M 列生成的数据属性包含真实字段名
- [ ] 未启用 DDL 辅助时，原有功能不受影响
- [ ] DDL 折叠区域可展开/收起

---

## Phase 2：架构重构

---

### T7：顶部 Tab 导航重构

> **PRD 对应**：模块八（2.8）  
> **依赖**：T1、T4（新增页面已完成）  
> **预计工作量**：1 次对话

#### 目标

将线性 QStackedWidget 导航改为顶部 Tab 标签导航，用户可自由跳转。

#### 文件变更

| 操作 | 文件 | 说明 |
|------|------|------|
| 重写 | `src/ui/main_window.py` | 用 QTabWidget 替代 QStackedWidget + 导航按钮 |
| 修改 | `src/gui.py` | 窗口尺寸调整（如需要） |
| 修改 | 所有 page_xxx.py | 移除页面内的「上一步/下一步」按钮（保留功能按钮） |

#### 新 main_window.py 结构

```python
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PyQt6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("COSMIC-GUI")
        self.setMinimumSize(900, 700)

        # 创建 Tab Widget
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.setCentralWidget(self.tabs)

        # 添加各功能页面
        self.page_calculator = PageCalculator()
        self.tabs.addTab(self.page_calculator, "人天计算器")

        self.page_ai_recognize = PageAIRecognize()
        self.tabs.addTab(self.page_ai_recognize, "AI识图")

        self.page_auto_fill = PageAutoFill()
        self.tabs.addTab(self.page_auto_fill, "自动填充")

        self.page_llm_fill = PageLLMFill()
        self.tabs.addTab(self.page_llm_fill, "LLM填充")

        self.page_excel_to_word = PageExcelToWord()
        self.tabs.addTab(self.page_excel_to_word, "Excel转Word")
```

#### 页面改造要点

- 移除所有页面的 `stacked_widget` 参数（不再需要）
- 移除页面内的「上一步」「下一步」按钮
- 保留页面内的功能按钮（开始、预览、导出等）
- 页面状态在 Tab 切换时保持（QTabWidget 默认行为）

#### 验收标准

- [ ] 顶部显示 5 个 Tab 标签
- [ ] 点击 Tab 可切换到对应页面
- [ ] Tab 切换不丢失已输入的数据
- [ ] 所有原有功能正常工作
- [ ] 窗口可调整大小，布局自适应
- [ ] 无「上一步/下一步」按钮残留

---

### T8：跨页面数据传递 + API 配置共享

> **PRD 对应**：PRD 3.1（统一配置）  
> **依赖**：T7  
> **预计工作量**：0.5 次对话

#### 目标

实现页面间数据传递（如 Module 3 的 Excel 输出传给 Module 4）和 API 配置全局共享。

#### 文件变更

| 操作 | 文件 | 说明 |
|------|------|------|
| 新增 | `src/core/config_store.py` | 全局配置存储（单例） |
| 修改 | `src/ui/main_window.py` | 添加页面间桥接逻辑 |
| 修改 | 各页面 | 添加「传递到下一模块」按钮 |

#### config_store.py

```python
from dataclasses import dataclass, field

@dataclass
class AppConfig:
    """全局应用配置（单例模式）"""
    api_key: str = ""
    api_url: str = ""
    model_name: str = ""

    # 页面间传递的文件路径
    txt_output_path: str = ""      # 模块二输出的 TXT 路径
    excel_output_path: str = ""    # 模块三输出的 Excel 路径
    filled_excel_path: str = ""    # 模块四/五填充后的 Excel 路径

# 全局单例
config = AppConfig()
```

#### 页面间桥接

在 main_window.py 中：

```python
# 页面间数据传递方法
def pass_excel_to_auto_fill(self, excel_path: str):
    """模块三 → 模块四：传递 Excel 路径"""
    config.excel_output_path = excel_path
    self.page_auto_fill.set_input_file(excel_path)
    self.tabs.setCurrentWidget(self.page_auto_fill)

def pass_excel_to_llm_fill(self, excel_path: str):
    """模块四 → 模块五：传递填充后的 Excel 路径"""
    config.filled_excel_path = excel_path
    self.page_llm_fill.set_input_file(excel_path)
    self.tabs.setCurrentWidget(self.page_llm_fill)
```

#### 各页面添加快捷按钮

```python
# 在模块三页面（AI 识图）的导出完成后
self.pass_btn = QPushButton("传递到自动填充 →")
self.pass_btn.clicked.connect(lambda: main_window.pass_excel_to_auto_fill(output_path))

# 在模块四页面（自动填充）完成后
self.pass_btn = QPushButton("传递到 LLM 填充 →")
self.pass_btn.clicked.connect(lambda: main_window.pass_excel_to_llm_fill(output_path))
```

#### 验收标准

- [ ] API 配置在任意页面修改后，其他页面自动同步
- [ ] 模块三导出的 Excel 可一键传递到模块四
- [ ] 模块四填充后的 Excel 可一键传递到模块五
- [ ] 传递后目标页面自动填入文件路径
- [ ] 传递后自动切换到目标 Tab

---

## Phase 3：收尾

---

### T9：集成测试 + 文档更新

> **依赖**：T1-T8 全部完成  
> **预计工作量**：0.5 次对话

#### 测试矩阵

| 测试项 | 测试内容 | 预期结果 |
|--------|----------|----------|
| T1 计算器 | 输入 500000, 15%, 1500 | 行数=393 |
| T2 AI 识图 | 提供测试截图 + API 配置 | 输出正确格式的 TXT |
| T3 生成 Excel | 输入测试 TXT | 生成带合并单元格的 Excel |
| T4 页面集成 | 完整流程：识图→审核→导出 | 端到端可用 |
| T5 流程图 | 用现有测试 Excel 转 Word | Word 中包含时序图 |
| T6 DDL 辅助 | 提供测试 .sql + Excel | M 列包含真实字段名 |
| Tab 导航 | 点击所有 Tab | 页面切换正常，数据不丢失 |
| 数据传递 | 模块三→四→五 | 文件路径正确传递 |
| 回归测试 | 现有 Page2/Page3/Page4 | 功能无退化 |

#### 文档更新清单

| 文件 | 更新内容 |
|------|----------|
| `docs/plan.md` | 所有 Task 标记为已完成 |
| `docs/PRD.md` | 版本号更新为 v2.2，标注已实现功能 |
| `README.md` | 更新文件架构、功能说明、运行方式 |
| 各 page 文件 | 同步更新「黄金法则」检查清单 |

---

## 附录：文件变更总览

```
src/
├── gui.py                          # T7 修改
├── core/
│   ├── auto_fill.py                # 不变
│   ├── llm_fill.py                 # T6 修改
│   ├── ai_recognize.py             # T2 新增
│   ├── txt_to_excel.py             # T3 新增
│   ├── ddl_parser.py               # T6 新增
│   └── config_store.py             # T8 新增
├── ui/
│   ├── main_window.py              # T7 重写，T1/T4/T8 修改
│   ├── page1_welcome.py            # T7 可能移除
│   ├── page2_auto_fill.py          # T7 修改（移除导航按钮）
│   ├── page3_llm_fill.py           # T6 修改，T7 修改
│   ├── page4_excel_to_word.py      # T5 修改，T7 修改
│   ├── page_calculator.py          # T1 新增
│   └── page_ai_recognize.py        # T4 新增
├── workers/
│   ├── auto_fill_worker.py         # 不变
│   ├── llm_fill_worker.py          # T6 修改
│   ├── excel_to_word_worker.py     # T5 修改
│   ├── ai_recognize_worker.py      # T2 新增
│   └── txt_to_excel_worker.py      # T3 新增
└── utils/
    └── resource_path.py            # 不变
```

---

*文档版本：v1.0 | 创建于 2026-05-02*
