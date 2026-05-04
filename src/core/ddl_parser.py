"""DDL 解析 - 从 SQL 文件中提取建表语句"""
import re
from pathlib import Path


def parse_ddl_folder(folder_path: str) -> dict:
    """遍历文件夹中的 .sql 文件，解析 CREATE TABLE 语句"""
    tables = {}
    for sql_file in Path(folder_path).glob("*.sql"):
        content = sql_file.read_text(encoding='utf-8', errors='ignore')
        tables.update(parse_sql_content(content))
    return tables


def parse_sql_content(sql: str) -> dict:
    """解析 SQL 内容中的 CREATE TABLE 语句"""
    tables = {}
    # 先去掉 SQL 单行注释，避免注释中的括号干扰匹配
    cleaned = re.sub(r'--[^\n]*', '', sql)
    # 找到所有 CREATE TABLE 的位置
    create_pattern = re.compile(
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\']?(\w+)[`"\']?\s*\(',
        re.IGNORECASE
    )
    for match in create_pattern.finditer(cleaned):
        table_name = match.group(1)
        # 从左括号开始，用括号计数找到匹配的右括号
        start = match.end()  # 指向 '(' 之后的位置
        depth = 1
        pos = start
        while pos < len(cleaned) and depth > 0:
            if cleaned[pos] == '(':
                depth += 1
            elif cleaned[pos] == ')':
                depth -= 1
            pos += 1
        body = cleaned[start:pos - 1]
        columns = _parse_columns(body)
        # 从右括号之后提取表注释
        after = cleaned[pos:pos + 200]
        table_comment = _extract_table_comment(after)
        tables[table_name] = {
            "table_comment": table_comment,
            "columns": columns
        }
    return tables


def _parse_columns(body: str) -> list:
    columns = []
    for line in body.split('\n'):
        line = line.strip().rstrip(',')
        if not line or line.upper().startswith(('PRIMARY', 'UNIQUE', 'KEY', 'INDEX', 'CONSTRAINT', 'CHECK')):
            continue
        col_match = re.match(
            r'[`"\']?(\w+)[`"\']?\s+(\w+(?:\([^)]*\))?)\s*(.*)',
            line, re.IGNORECASE
        )
        if col_match:
            col_name = col_match.group(1)
            col_type = col_match.group(2)
            rest = col_match.group(3)
            comment = ""
            comment_match = re.search(r"COMMENT\s+['\"]([^'\"]*)['\"]", rest, re.IGNORECASE)
            if comment_match:
                comment = comment_match.group(1)
            columns.append({"name": col_name, "type": col_type, "comment": comment})
    return columns


def _extract_table_comment(body: str) -> str:
    match = re.search(r"COMMENT\s*=\s*['\"]([^'\"]*)['\"]", body, re.IGNORECASE)
    return match.group(1) if match else ""


def build_ddl_context(tables: dict) -> str:
    """构建 DDL 上下文字符串"""
    if not tables:
        return ""
    context = "系统数据库表结构：\n"
    for table_name, info in tables.items():
        display_name = info.get("table_comment") or table_name
        cols = []
        for c in info["columns"]:
            name = c["comment"] if c["comment"] else c["name"]
            cols.append(name)
        context += f"- {display_name}({table_name}): {', '.join(cols)}\n"
    return context


def format_ddl_summary(tables: dict) -> str:
    """格式化 DDL 解析摘要，用于 UI 显示"""
    if not tables:
        return "未解析到任何表"
    lines = [f"共解析到 {len(tables)} 张表："]
    for table_name, info in tables.items():
        display_name = info.get("table_comment") or table_name
        col_count = len(info["columns"])
        lines.append(f"  - {display_name}({table_name}): {col_count} 个字段")
    return "\n".join(lines)
