"""模块三：解析功能清单 TXT → 生成 COSMIC Excel（含合并单元格 + ERWX）"""

import re
import math
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Side, Font
from openpyxl.utils import get_column_letter


# --- TXT 解析 ---

def parse_txt(txt_content: str) -> list[dict]:
    """
    解析带层级缩进的 TXT，返回结构化数据。

    层级规则（PRD 2.3.5）：
    - 无缩进 + 数字序号 → 二级功能
    - 4空格（或1个tab）+ 数字序号 → 三级功能
    - 8空格（或2个tab）+ 无序号 → 功能过程

    支持 tab 和空格混合缩进（tab 视为 4 空格）。

    返回：
    [
        {"level2": "手机APP监控", "level3": "启动分析", "process": "查询APP启动次数"},
        ...
    ]
    """
    lines = txt_content.splitlines()
    result = []
    current_level2 = None
    current_level3 = None

    # 正则匹配（在 tab 被替换为空格后匹配）
    re_level2 = re.compile(r'^(\d+)\s+(.+)$')              # "1 二级功能"
    re_level3 = re.compile(r'^\s{2,6}(\d+\.\d+)\s+(.+)$')  # "    1.1 三级功能" (4空格±2容差)
    re_process = re.compile(r'^\s{6,}(.+)$')               # "        功能过程" (8空格±2容差)

    for raw_line in lines:
        # 将 tab 替换为 4 个空格（统一缩进格式）
        line = raw_line.replace('\t', '    ').rstrip()
        if not line or line.strip() == '':
            continue

        # 跳过注释行
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('//'):
            continue

        # 尝试匹配功能过程（8空格缩进，无序号）
        process_match = re_process.match(line)
        if process_match and not re.match(r'^\s+\d', line):
            process_name = process_match.group(1).strip()
            if current_level2 and current_level3 and process_name:
                result.append({
                    "level2": current_level2,
                    "level3": current_level3,
                    "process": process_name,
                })
            continue

        # 尝试匹配三级功能（4空格 + 数字序号）
        level3_match = re_level3.match(line)
        if level3_match:
            current_level3 = level3_match.group(2).strip()
            continue

        # 尝试匹配二级功能（无缩进 + 数字序号）
        level2_match = re_level2.match(line)
        if level2_match:
            current_level2 = level2_match.group(2).strip()
            current_level3 = None  # 重置三级
            continue

    return result


# --- Excel 生成 ---

# 列定义（14列 A-N）
COLUMNS = [
    ('A', '修订标识'),
    ('B', '需求名称'),
    ('C', '一级功能'),
    ('D', '二级功能'),
    ('E', '三级功能'),
    ('F', '功能用户'),
    ('G', '功能用户需求'),
    ('H', '触发事件'),
    ('I', '功能过程'),
    ('J', '子过程描述'),
    ('K', '数据移动类型'),
    ('L', '数据组'),
    ('M', '数据属性'),
    ('N', 'CFP'),
]

DATA_MOVE_TYPES = ['E', 'R', 'W', 'X']

# 样式
THIN_BORDER = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin'),
)
HEADER_FONT = Font(bold=True, size=11)
CENTER_ALIGN = Alignment(horizontal='center', vertical='center', wrap_text=True)
LEFT_ALIGN = Alignment(horizontal='left', vertical='center', wrap_text=True)


def _build_rows(parsed_data: list[dict], system_name: str) -> list[dict]:
    """
    将解析数据展开为 Excel 行数据（每个功能过程 4 行：E/R/W/X）。
    """
    rows = []
    for item in parsed_data:
        for move_type in DATA_MOVE_TYPES:
            rows.append({
                'B': system_name,       # 需求名称
                'C': system_name,       # 一级功能
                'D': item['level2'],    # 二级功能
                'E': item['level3'],    # 三级功能
                'F': '',                # 功能用户（留空）
                'G': '',                # 功能用户需求（留空）
                'H': '',                # 触发事件（留空）
                'I': item['process'],   # 功能过程
                'J': '',                # 子过程描述（留空）
                'K': move_type,         # 数据移动类型
                'L': '',                # 数据组（留空）
                'M': '',                # 数据属性（留空）
                'N': '',                # CFP（留空）
            })
    return rows


def _apply_styles(ws, total_rows: int):
    """应用统一的单元格样式。"""
    for row in ws.iter_rows(min_row=1, max_row=total_rows, max_col=14):
        for cell in row:
            cell.border = THIN_BORDER
            if cell.row == 1:
                cell.font = HEADER_FONT
                cell.alignment = CENTER_ALIGN
            else:
                cell.alignment = LEFT_ALIGN


def _merge_cells(ws, rows: list[dict], total_rows: int):
    """
    执行合并单元格逻辑。

    合并规则（PRD 2.3.6）：
    - B（需求名称）：整列合并
    - C（一级功能）：整列合并
    - D（二级功能）：同名连续合并
    - E（三级功能）：同名连续合并（在同一二级功能内）
    - F（功能用户）：整列合并（留空）
    - H（触发事件）：按 I 列合并范围对齐
    - I（功能过程）：每个功能过程合并 4 行
    """
    data_start = 2  # 第1行是表头

    if total_rows < data_start:
        return

    # B 列：整列合并
    if total_rows >= data_start:
        ws.merge_cells(f'B{data_start}:B{total_rows}')
        ws[f'B{data_start}'] = rows[0]['B']

    # C 列：整列合并
    if total_rows >= data_start:
        ws.merge_cells(f'C{data_start}:C{total_rows}')
        ws[f'C{data_start}'] = rows[0]['C']

    # F 列：整列合并（留空）
    if total_rows >= data_start:
        ws.merge_cells(f'F{data_start}:F{total_rows}')

    # D 列：同名连续合并
    _merge_consecutive(ws, rows, 'D', data_start, total_rows)

    # E 列：同名连续合并（需要在同一 D 值范围内）
    _merge_e_column(ws, rows, data_start, total_rows)

    # I 列：每个功能过程合并 4 行
    # H 列：按 I 列合并范围对齐
    _merge_i_and_h(ws, rows, data_start, total_rows)


def _merge_consecutive(ws, rows: list[dict], col_letter: str, data_start: int, total_rows: int):
    """合并同列中连续相同值的单元格。"""
    if not rows:
        return

    col_idx = ord(col_letter) - ord('A') + 1
    start = data_start
    current_val = rows[0][col_letter]

    for i in range(1, len(rows)):
        if rows[i][col_letter] != current_val:
            end = data_start + i - 1
            if end > start:
                ws.merge_cells(f'{col_letter}{start}:{col_letter}{end}')
                ws.cell(row=start, column=col_idx, value=current_val)
            elif end == start:
                ws.cell(row=start, column=col_idx, value=current_val)
            start = data_start + i
            current_val = rows[i][col_letter]

    # 处理最后一组
    end = total_rows
    if end > start:
        ws.merge_cells(f'{col_letter}{start}:{col_letter}{end}')
        ws.cell(row=start, column=col_idx, value=current_val)
    elif end == start:
        ws.cell(row=start, column=col_idx, value=current_val)


def _merge_e_column(ws, rows: list[dict], data_start: int, total_rows: int):
    """
    合并 E 列（三级功能），同一三级功能下的行合并，
    但需要在同一二级功能范围内。
    """
    if not rows:
        return

    col_idx = 5  # E 列
    start = data_start
    current_d = rows[0]['D']
    current_e = rows[0]['E']

    for i in range(1, len(rows)):
        if rows[i]['D'] != current_d or rows[i]['E'] != current_e:
            end = data_start + i - 1
            if end > start:
                ws.merge_cells(f'E{start}:E{end}')
                ws.cell(row=start, column=col_idx, value=current_e)
            elif end == start:
                ws.cell(row=start, column=col_idx, value=current_e)
            start = data_start + i
            current_d = rows[i]['D']
            current_e = rows[i]['E']

    # 处理最后一组
    end = total_rows
    if end > start:
        ws.merge_cells(f'E{start}:E{end}')
        ws.cell(row=start, column=col_idx, value=current_e)
    elif end == start:
        ws.cell(row=start, column=col_idx, value=current_e)


def _merge_i_and_h(ws, rows: list[dict], data_start: int, total_rows: int):
    """合并 I 列（每4行）和 H 列（按 I 列对齐）。"""
    i_start = data_start
    i = 0

    while i < len(rows):
        current_process = rows[i]['I']
        # 找到同一个功能过程的所有行（应该是4行 E/R/W/X）
        group_start = i
        while i < len(rows) and rows[i]['I'] == current_process:
            i += 1
        group_end = i  # exclusive

        row_start = data_start + group_start
        row_end = data_start + group_end - 1

        # I 列合并
        if row_end > row_start:
            ws.merge_cells(f'I{row_start}:I{row_end}')
        ws.cell(row=row_start, column=9, value=current_process)

        # H 列合并（与 I 列范围对齐）
        if row_end > row_start:
            ws.merge_cells(f'H{row_start}:H{row_end}')


def generate_excel(
    parsed_data: list[dict],
    system_name: str,
    output_path: str,
) -> str:
    """
    根据解析数据生成 COSMIC Excel。

    参数：
        parsed_data: parse_txt() 返回的结构化数据
        system_name: 系统名称（一级功能 / 需求名称）
        output_path: 输出 Excel 文件路径

    返回：输出文件路径
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "COSMIC"

    # 写表头（第1行）
    for col_idx, (col_letter, col_name) in enumerate(COLUMNS, start=1):
        ws.cell(row=1, column=col_idx, value=col_name)

    # 构建行数据
    rows = _build_rows(parsed_data, system_name)

    if not rows:
        # 没有数据时只保存表头
        _apply_styles(ws, 1)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(output))
        return str(output)

    # 写数据（从第2行开始）
    for row_idx, row_data in enumerate(rows, start=2):
        for col_letter, value in row_data.items():
            col_idx = ord(col_letter) - ord('A') + 1
            ws.cell(row=row_idx, column=col_idx, value=value)

    total_rows = len(rows) + 1  # +1 for header

    # 合并单元格
    _merge_cells(ws, rows, total_rows)

    # 应用样式
    _apply_styles(ws, total_rows)

    # 调整列宽
    col_widths = {
        'A': 10, 'B': 20, 'C': 20, 'D': 18, 'E': 18,
        'F': 12, 'G': 14, 'H': 14, 'I': 25,
        'J': 14, 'K': 10, 'L': 14, 'M': 14, 'N': 8,
    }
    for col, width in col_widths.items():
        ws.column_dimensions[col].width = width

    # 保存
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(output))

    return str(output)


def preview_data(parsed_data: list[dict], system_name: str) -> list[list[str]]:
    """
    生成预览数据（表格形式），供 UI 展示。

    返回：二维列表，第一行为表头，后续为数据行。
    """
    header = [col_name for _, col_name in COLUMNS]
    rows_data = _build_rows(parsed_data, system_name)

    result = [header]
    for row in rows_data:
        result.append([
            '',             # A
            row['B'],       # B
            row['C'],       # C
            row['D'],       # D
            row['E'],       # E
            row['F'],       # F
            row['G'],       # G
            row['H'],       # H
            row['I'],       # I
            row['J'],       # J
            row['K'],       # K
            row['L'],       # L
            row['M'],       # M
            row['N'],       # N
        ])

    return result
