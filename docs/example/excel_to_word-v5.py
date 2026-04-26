import openpyxl
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt
from docx.enum.text import WD_LINE_SPACING
import re
import os
import time

# ========== 初始化 ==========
start_time = time.time()
print("正在转换，请稍后...", end="", flush=True)

# 读取 Excel
excel_file = "222.xlsx"
wb = openpyxl.load_workbook(excel_file)
sheet = wb.active

# 创建 Word 文档
doc = Document()

# 设置全文 1.5 倍行距、宋体、五号（10.5pt）
style = doc.styles['Normal']
style.font.name = '宋体'
style._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
style.font.size = Pt(10.5)  # 五号
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

# 添加标题函数
def add_heading(doc, text, style_name):
    """添加标题（中文黑体）"""
    p = doc.add_paragraph(text)
    p.style = style_name
    run = p.runs[0]
    run.font.name = '黑体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    run.italic = False
    return p

# 添加正文函数
def add_paragraph(doc, text):
    """添加正文（继承 Normal 样式，首行缩进2个字符）"""
    p = doc.add_paragraph(text)
    p.style = 'Normal'
    p.paragraph_format.first_line_indent = Pt(21)
    return p

# 解析发起者和接受者
def parse_sender_receiver(text):
    """从 F 列字符串提取 发起者 和 接受者"""
    sender = receiver = ""
    if text:
        match = re.search(r"发起者[:：]\s*(.*?)\s*接收者[:：]\s*(.*)", text, re.S)
        if match:
            sender = match.group(1).strip()
            receiver = match.group(2).strip()
    return sender, receiver

# 输出正文函数
def flush_content_buffer():
    """输出并清空正文缓存"""
    global content_buffer, current_sender, current_receiver
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

# 缓存正文
content_buffer = []
current_sender = ""
current_receiver = ""

# ========== 主循环 ==========
for idx, (c_col, d_col, e_col, f_col, i_col, j_col, m_col) in enumerate(data):

    # === 修复点：层级回退时输出缓存 ===
    # 当从更深层标题（五级/四级）回退到更浅层（三级/二级）时，应立即输出缓存的正文
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
        sender, receiver = parse_sender_receiver(f_col)
        current_sender = sender
        current_receiver = receiver

    # 收集正文数据
    if j_col and m_col:
        content_buffer.append((j_col, m_col))

    # 如果是最后一行，输出缓存
    if idx == len(data) - 1:
        flush_content_buffer()

# ========== 保存文档 ==========
output_file = "转换后文档.docx"
if os.path.exists(output_file):
    os.remove(output_file)

doc.save(output_file)

elapsed = time.time() - start_time
print(f"\n生成完成：{output_file} ✅ 用时 {elapsed:.1f} 秒")
