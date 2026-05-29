# LLM 填充功能移除记录

## 变更日期
2026-05-29

## 变更原因
"LLM 填充"和"LLM 字段生成"两个功能存在重复，均用于调用大模型填写 Excel 的 M 列。其中"LLM 字段生成"支持 DDL 辅助功能，功能更完善，因此保留"LLM 字段生成"，移除"LLM 填充"。

## 变更内容

### 1. 从目录页移除
文件：`src/ui/directory_page.py`
- 从 `CATEGORIES` 列表的"编写中"分类中移除了"LLM 填充"条目

### 2. 从主窗口移除
文件：`src/ui/main_window.py`
- 移除了 `Page3` 的导入
- 移除了 `page_llm_fill` 页面的创建和添加
- 更新了 `FEATURE_ORDER` 列表，移除了原 index 6
- 更新了 `_on_auto_fill_success` 方法，改为调用 `page_llm_field_gen.set_input_file()`

### 3. 页面索引变更
| 功能 | 原索引 | 新索引 |
|------|--------|--------|
| 人天计算器 | 2 | 2 |
| AI 识图 | 3 | 3 |
| TXT 生成 Excel | 4 | 4 |
| 自动填充 | 5 | 5 |
| ~~LLM 填充~~ | 6 | ~~已移除~~ |
| LLM 字段生成 | 7 | 6 |
| Excel 转 Word | 8 | 7 |
| Excel 转 Word（含流程图） | 9 | 8 |

## 保留的底层代码
以下文件保留，未删除：
- `src/core/llm_fill.py` - LLM 填充核心逻辑
- `src/workers/llm_fill_worker.py` - LLM 填充 Worker 线程
- `src/ui/page3_llm_fill.py` - LLM 填充 UI 页面

## 回滚方法

### 步骤 1：恢复目录页
在 `src/ui/directory_page.py` 的 `CATEGORIES` 列表中，在"编写中"分类里添加回 LLM 填充条目：

```python
("编写中", [
    ("自动填充", "规则引擎填写 H/J/L 列", 5),
    ("LLM 填充", "大模型填写 M 列", 6),  # 添加这一行
    ("LLM 字段生成", "大模型填写 M 列（支持 DDL 辅助）", 7),  # 索引改为7
]),
```

### 步骤 2：恢复主窗口
在 `src/ui/main_window.py` 中：

1. 添加回导入：
```python
from .page3_llm_fill import Page3
```

2. 更新 FEATURE_ORDER：
```python
FEATURE_ORDER = [2, 3, 4, 5, 6, 7, 8, 9]
```

3. 添加回页面创建（在页面5之后）：
```python
# 页面 6：LLM 填充
self.page_llm_fill = Page3(self.navigator)
self.stacked.addWidget(self.page_llm_fill)

# 页面 7：LLM 数据字段生成
self.page_llm_field_gen = PageLLMFieldGen(self.navigator)
self.stacked.addWidget(self.page_llm_field_gen)
```

4. 恢复 `_on_auto_fill_success` 方法：
```python
def _on_auto_fill_success(self):
    file_path = self.page_auto_fill.file_edit.text().strip()
    self.page_llm_fill.set_input_file(file_path)
```

## 错误诊断增强
在此次变更中，同时增强了 LLM 调用的错误诊断功能：

### 新增错误提示
当 LLM 调用失败时，会输出详细的诊断信息：
- **404 错误**：提示 API 端点 URL 不正确或模型名称不存在
- **401 错误**：提示 API 密钥无效或已过期
- **403 错误**：提示没有权限访问该模型或端点

### 保留底层代码
`src/core/llm_fill.py` 和 `src/core/llm_field_gen.py` 均已更新，增加了错误响应体的读取和显示，方便用户诊断问题。
