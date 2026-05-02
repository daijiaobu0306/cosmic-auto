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

*最后更新：2026-05-02*
