# Cosmic-GUI 项目结构

```
cosmic-GUI/
├── .git/                      # Git 版本控制
├── src/                       # 源代码
│   ├── core/                  # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── auto_fill.py       # 自动填充模块
│   │   └── llm_fill.py        # 大模型填充模块
│   ├── ui/                    # 界面模块
│   │   ├── __init__.py
│   │   ├── main_window.py     # 主窗口
│   │   ├── page1_welcome.py   # 欢迎页
│   │   ├── page2_auto_fill.py # 自动填充页
│   │   ├── page3_llm_fill.py  # LLM填充页
│   │   └── styles.py          # 样式配置
│   ├── utils/                 # 工具模块
│   │   ├── __init__.py
│   │   └── resource_path.py   # 资源路径工具
│   ├── workers/               # 后台工作线程
│   │   ├── __init__.py
│   │   ├── auto_fill_worker.py
│   │   └── llm_fill_worker.py
│   ├── gui.py                 # GUI入口
│   └── requirements.txt        # 依赖
├── docs/                      # 文档及测试数据
│   ├── README.txt
│   └── test_data/              # 测试数据（模板/生成文件）
│       ├── 模板/
│       │   ├── cosmic-自动填充-test1.xlsx
│       │   ├── cosmic-自动填充-test2.xlsx
│       │   └── cosmic-自动填充-模板.xlsx
│       └── 大模型填充后.xlsx
└── PROJECT_STRUCTURE.md        # 本文件
```

## 目录说明

| 目录 | 说明 |
|------|------|
| src/ | 所有源代码，包括 core/ui/utils/workers 和入口文件 |
| docs/ | 文档和测试数据（包括Excel模板和生成文件） |
| docs/ | 文档和说明文件 |

## 关键文件速查

- **GUI入口**: [src/gui.py](src/gui.py)
- **自动填充核心**: [src/core/auto_fill.py](src/core/auto_fill.py)
- **LLM填充核心**: [src/core/llm_fill.py](src/core/llm_fill.py)
- **主界面**: [src/ui/main_window.py](src/ui/main_window.py)
- **后台线程**: [src/workers/auto_fill_worker.py](src/workers/auto_fill_worker.py), [src/workers/llm_fill_worker.py](src/workers/llm_fill_worker.py)