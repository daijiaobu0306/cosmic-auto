"""Excel → Word 转换业务逻辑（纯函数，无 Qt 依赖）

负责：读取 COSMIC Excel → 解析层级结构 → 生成 Word 文档
"""
import time
import re
import openpyxl
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.enum.text import WD_LINE_SPACING


def parse_sender_receiver(text: str):
    """解析发起者和接收者字符串"""
    sender = receiver = ""
    if text:
        match = re.search(r"发起者[:：]\s*(.*?)\s*接收者[:：]\s*(.*)", text, re.S)
        if match:
            sender = match.group(1).strip()
            receiver = match.group(2).strip()
    return sender, receiver


def add_heading(doc: Document, text: str, style_name: str):
    """添加标题段落"""
    p = doc.add_paragraph(text)
    p.style = style_name
    run = p.runs[0]
    run.font.name = '黑体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    run.italic = False
    return p


def add_paragraph(doc: Document, text: str):
    """添加正文段落（首行缩进 21pt）"""
    p = doc.add_paragraph(text)
    p.style = 'Normal'
    p.paragraph_format.first_line_indent = Pt(21)
    return p


def excel_to_word(excel_file: str, output_file: str, callback_print=None) -> dict:
    """将 COSMIC Excel 转换为 Word 文档

    Args:
        excel_file: 输入的 Excel 文件路径
        output_file: 输出的 Word 文件路径
        callback_print: 日志回调函数（可选）

    Returns:
        dict: 包含耗时、行数等统计信息
    """
    if callback_print is None:
        callback_print = lambda x: None

    start_time = time.time()
    callback_print("正在转换，请稍后...")

    # 读取 Excel
    wb = openpyxl.load_workbook(excel_file)
    sheet = wb.active

    # 创建 Word 文档
    doc = Document()

    # 设置全文 1.5 倍行距、宋体、五号（10.5pt）
    style = doc.styles['Normal']
    style.font.name = '宋体'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    style.font.size = Pt(10.5)
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE

    # 读取数据
    data = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        c_col = row[2]   # C列（二级模块）
        d_col = row[3]   # D列（三级模块）
        e_col = row[4]   # E列（四级模块）
        f_col = row[5]   # F列（发起者+接受者字符串）
        i_col = row[8]   # I列（五级模块）
        j_col = row[9]   # J列
        m_col = row[12]  # M列
        data.append((c_col, d_col, e_col, f_col, i_col, j_col, m_col))

    # 编号计数器
    level1_num = 1
    level2_num = 0
    level3_num = 0
    level4_num = 0
    level5_num = 0

    last_c = None
    last_d = None
    last_e = None
    last_i = None

    # 输出正文函数
    content_buffer = []
    current_sender = ""
    current_receiver = ""

    def flush_content_buffer():
        nonlocal current_sender, current_receiver
        if content_buffer:
            for i, (jv, mv) in enumerate(content_buffer, start=1):
                if i == 1:
                    text = f"({i}){current_sender}{jv}，字段包括{mv}。"
                elif i == len(content_buffer):
                    text = f"({i}){current_receiver}向{current_sender}{jv}，字段包括{mv}。"
                else:
                    text = f"({i}){current_receiver}{jv}，字段包括{mv}。"
                add_paragraph(doc, text)
            content_buffer.clear()

    # 主循环
    for idx, (c_col, d_col, e_col, f_col, i_col, j_col, m_col) in enumerate(data):
        if content_buffer:
            if (c_col and c_col != last_c) or (d_col and d_col != last_d) or (e_col and e_col != last_e):
                flush_content_buffer()

        # 二级标题 (C列)
        if c_col and c_col != last_c:
            flush_content_buffer()
            level2_num += 1
            level3_num = 0
            level4_num = 0
            level5_num = 0
            add_heading(doc, f"{level1_num}.{level2_num} {c_col}", 'Heading 2')
            last_c = c_col

        # 三级标题 (D列)
        if d_col and d_col != last_d:
            flush_content_buffer()
            level3_num += 1
            level4_num = 0
            level5_num = 0
            add_heading(doc, f"{level1_num}.{level2_num}.{level3_num} {d_col}", 'Heading 3')
            last_d = d_col

        # 四级标题 (E列)
        if e_col and e_col != last_e:
            flush_content_buffer()
            level4_num += 1
            level5_num = 0
            add_heading(doc, f"{level1_num}.{level2_num}.{level3_num}.{level4_num} {e_col}", 'Heading 4')
            last_e = e_col

        # 五级标题 (I列)
        if i_col and i_col != last_i:
            flush_content_buffer()
            level5_num += 1
            add_heading(doc, f"{level1_num}.{level2_num}.{level3_num}.{level4_num}.{level5_num} {i_col}", 'Heading 5')
            last_i = i_col

        # 解析发起者 / 接收者
        if f_col:
            current_sender, current_receiver = parse_sender_receiver(f_col)

        # 收集正文数据
        if j_col and m_col:
            content_buffer.append((j_col, m_col))

        # 如果是最后一行，输出缓存
        if idx == len(data) - 1:
            flush_content_buffer()

    # 保存文档
    import os
    if os.path.exists(output_file):
        os.remove(output_file)

    doc.save(output_file)

    elapsed = time.time() - start_time
    callback_print(f"\n生成完成：{output_file} 用时 {elapsed:.1f} 秒")

    return {
        "output_file": output_file,
        "elapsed": elapsed,
        "row_count": len(data),
    }
