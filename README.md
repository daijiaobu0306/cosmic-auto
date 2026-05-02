# COSMIC-GUI

COSMIC 功能点度量自动化工具，基于 PyQt6 桌面应用。

## 快速启动

```bash
cd d:/cod/AI/cosmic-GUI/src
python gui.py
```

## 文件结构

```
src/
├── gui.py                      # 程序入口
├── core/                       # 纯业务逻辑（无 Qt 依赖）
│   ├── auto_fill.py            # 自动填空（H/J/L 列）
│   ├── llm_fill.py             # LLM 填充（M 列）
│   ├── ai_recognize.py         # AI 识图 → TXT
│   ├── txt_to_excel.py         # TXT → Excel（含合并单元格）
│   ├── ddl_parser.py           # DDL 解析
│   └── config_store.py         # 全局配置单例
├── ui/                         # PyQt6 页面
│   ├── main_window.py          # 主窗口（Tab 导航）
│   ├── page_calculator.py      # 人天计算器
│   ├── page_ai_recognize.py    # AI 识图 + 生成 Excel
│   ├── page2_auto_fill.py      # 自动填充
│   ├── page3_llm_fill.py       # LLM 填充（含 DDL 辅助）
│   └── page4_excel_to_word.py  # Excel 转 Word + 流程图
├── workers/                    # QThread 后台线程
│   ├── auto_fill_worker.py
│   ├── llm_fill_worker.py
│   ├── excel_to_word_worker.py
│   ├── ai_recognize_worker.py
│   └── txt_to_excel_worker.py
└── utils/
    └── resource_path.py        # 资源路径（打包用）
```

## 功能模块

| Tab | 功能 | 说明 |
|-----|------|------|
| 人天计算器 | 项目金额 → COSMIC 行数 | 编写前估算 |
| AI识图 | 截图 → 功能清单 TXT → Excel | 编写前生成框架 |
| 自动填充 | 规则引擎填写 H/J/L 列 | 编写中 |
| LLM填充 | 大模型填写 M 列（可选 DDL 辅助） | 编写中 |
| Excel转Word | Excel → Word 文档 + Mermaid 时序图 | 编写后 |

## 开发文档

- **[PRD.md](docs/PRD.md)** — 产品需求文档（功能规格、输入输出、验收标准）
- **[plan.md](docs/plan.md)** — 开发计划（任务拆分、代码模板、进度追踪、文件变更清单）

开发新功能时，先读 plan.md 了解约定和任务要求，完成后勾选对应 checkbox。

## 依赖

- Python 3.10+
- PyQt6, openpyxl, python-docx, aiohttp
- 可选：Node.js + @mermaid-js/mermaid-cli（流程图渲染）

---

## UI 设计规范

为保证所有页面的 UI 一致性，新开发页面必须遵循以下规范：

### 字体大小标准

| 元素类型 | 字体大小 | 说明 |
|----------|----------|------|
| 页面标题 | 16px | 主标题，加粗 |
| 页面副标题 | 11px | 说明文字，灰色 |
| 表单标签 | 12px | 输入框前的说明文字 |
| 输入框内容 | 12px | 用户输入的文字 |
| 按钮文字 | 12-13px | 功能按钮 |
| 结果数值 | 18px | 重要数值显示（加粗） |
| 结果标签 | 10px | 数值下方的说明文字 |

### 颜色规范

| 用途 | 色值 | 说明 |
|------|------|------|
| 主色调 | #3498db | 按钮、边框、强调色 |
| 主色调悬停 | #2980b9 | 鼠标悬停状态 |
| 主色调按下 | #1f618d | 鼠标按下状态 |
| 标题文字 | #2c3e50 | 主要文字 |
| 正文文字 | #495057 | 表单标签、说明文字 |
| 次要文字 | #7f8c8d | 副标题、提示文字 |
| 背景色 | #f8f9fa | 卡片背景 |
| 边框色 | #e9ecef | 卡片边框 |
| 成功色 | #27ae60 | 成功状态提示 |

### 间距规范

| 间距类型 | 数值 | 说明 |
|----------|------|------|
| 页面边距 | 30px | 页面内容与窗口边缘的距离 |
| 元素间距 | 10-12px | 各组件之间的垂直间距 |
| 卡片内边距 | 15px | 卡片内部的内边距 |
| 按钮尺寸 | 100-120px × 32-36px | 标准按钮大小 |

### 交互规范

- 所有可点击元素必须设置 `cursor: PointingHandCursor`
- 输入框获得焦点时边框变为蓝色（#3498db）
- 按钮悬停时颜色加深
- 成功操作（如复制）显示 1.5 秒成功提示后恢复

---

*最后更新：2026-05-02*
