"""脚本1: 自动填空 - 根据 I、K 列自动填写 H、J、L 列"""
import random
import openpyxl


def auto_fill(file_path, sheet_name):
    """
    处理Excel表格，根据I列和K列的内容自动填写H、J、L列
    """
    COL_I = 9
    COL_K = 11
    COL_H = 8
    COL_J = 10
    COL_L = 12

    workbook = openpyxl.load_workbook(file_path)
    if sheet_name not in workbook.sheetnames:
        print(f"错误: 工作表 '{sheet_name}' 不存在。")
        return False

    sheet = workbook[sheet_name]
    print(f"成功加载文件: {file_path}, 工作表: {sheet_name}")

    i_merge_info = {}
    for merge_range in sheet.merged_cells.ranges:
        if merge_range.min_col <= COL_I <= merge_range.max_col:
            start_row = merge_range.min_row
            i_value = sheet.cell(row=start_row, column=COL_I).value
            if i_value and isinstance(i_value, str) and len(i_value) >= 2:
                i_verb = i_value[:2]
                i_content = i_value[2:]
                i_merge_info[start_row] = (i_verb, i_content)

    for row_index in range(2, sheet.max_row + 1):
        i_verb = None
        i_content = None
        start_row = row_index

        for merge_range in sheet.merged_cells.ranges:
            if merge_range.min_col <= COL_I <= merge_range.max_col:
                if merge_range.min_row <= row_index <= merge_range.max_row:
                    start_row = merge_range.min_row
                    if start_row in i_merge_info:
                        i_verb, i_content = i_merge_info[start_row]
                        break

        if not i_verb and not i_content:
            i_value = sheet.cell(row=row_index, column=COL_I).value
            if i_value and isinstance(i_value, str) and len(i_value) >= 2:
                i_verb = i_value[:2]
                i_content = i_value[2:]
            else:
                continue

        k_value = sheet.cell(row=row_index, column=COL_K).value
        k_type = str(k_value).upper().strip() if k_value else ""

        h_cell = sheet.cell(row=row_index, column=COL_H)
        if h_cell.value is None or h_cell.value == "":
            h_col_value = _generate_h_col(i_verb, i_content)
            if row_index == start_row and not isinstance(h_cell, openpyxl.cell.cell.MergedCell):
                sheet.cell(row=row_index, column=COL_H, value=h_col_value)

        j_cell = sheet.cell(row=row_index, column=COL_J)
        if j_cell.value is None or j_cell.value == "":
            j_col_value = _generate_j_col(k_type, i_verb, i_content)
            if not isinstance(j_cell, openpyxl.cell.cell.MergedCell):
                sheet.cell(row=row_index, column=COL_J, value=j_col_value)

        l_cell = sheet.cell(row=row_index, column=COL_L)
        if l_cell.value is None or l_cell.value == "":
            l_col_value = _generate_l_col(k_type, i_verb, i_content)
            if not isinstance(l_cell, openpyxl.cell.cell.MergedCell):
                sheet.cell(row=row_index, column=COL_L, value=l_col_value)

    workbook.save(file_path)
    print("\n处理完成！结果已保存到原文件中。")
    return True


def _generate_h_col(i_verb, i_content):
    verb_end_pair = random.choice([("调用", "接口"), ("发起", "请求")])
    return f"用户{verb_end_pair[0]}{i_content}{i_verb}{verb_end_pair[1]}"


def _generate_j_col(k_type, i_verb, i_content):
    if k_type == 'E':
        end_choice = random.choice(["参数", "条件", "信息"])
        return f"输入{i_content}{i_verb}{end_choice}"
    elif k_type == 'R':
        return f"读取{i_content}{i_verb}信息"
    elif k_type == 'W':
        start_choice = random.choice(["保存", "写入"])
        return f"{start_choice}{i_content}{i_verb}的数据"
    elif k_type == 'X':
        start_choice = random.choice(["展示", "输出"])
        return f"{start_choice}{i_content}{i_verb}结果"
    else:
        return ""


def _generate_l_col(k_type, i_verb, i_content):
    if k_type == 'E':
        return f"{i_content}{i_verb}信息"
    elif k_type == 'R':
        return f"{i_content}{i_verb}数据"
    elif k_type == 'W':
        return f"{i_content}数据"
    elif k_type == 'X':
        return f"{i_content}{i_verb}结果"
    else:
        return ""