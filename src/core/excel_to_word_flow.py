"""Excel → Word 转换业务逻辑（含流程图）

负责：读取 COSMIC Excel → 解析层级结构 → 生成流程图 → 生成 Word 文档
流程图使用纯 Python Pillow 渲染，无需 Node.js / mmdc，可直接打包为 exe。
"""
import time
import tempfile
import os
import re
import openpyxl
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt, Inches
from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH

from core.flowchart_renderer import render_sequence_diagram


def parse_sender_receiver(f_value: str):
    """解析发起者和接收者字符串"""
    if not f_value:
        return "", ""
    match = re.search(r"发起者[:：]\s*(.*?)\s*接收者[:：]\s*(.*)", str(f_value), re.S)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return "", ""


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


def add_centered_picture(doc: Document, image_path: str, width_inches: float = 5.5):
    """添加居中图片"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(image_path, width=Inches(width_inches))
    return p


def excel_to_word_flow(excel_file: str, output_file: str, generate_flowchart: bool = True,
                       callback_print=None) -> dict:
    """将 COSMIC Excel 转换为 Word 文档（可选生成流程图）

    Args:
        excel_file: 输入的 Excel 文件路径
        output_file: 输出的 Word 文件路径
        generate_flowchart: 是否生成流程图
        callback_print: 日志回调函数（可选）

    Returns:
        dict: 包含耗时、行数、流程图数量等统计信息
    """
    if callback_print is None:
        callback_print = lambda x: None

    start_time = time.time()
    callback_print("[Flow] 开始执行 Excel → Word 转换（含流程图选项）")
    callback_print(f"[Flow] 输入文件：{excel_file}")
    callback_print(f"[Flow] 输出文件：{output_file}")
    callback_print(f"[Flow] 流程图开关：{'开启' if generate_flowchart else '关闭'}")
    if generate_flowchart:
        callback_print("[Flow] 流程图渲染引擎：Pillow（纯 Python，无需 Node.js）")
        callback_print("[Flow] 流程图模板：三实体（发起者→接收者→数据库）+ 四箭头固定句式")

    if not os.path.exists(excel_file):
        callback_print(f"[Flow] 错误：输入文件不存在 → {excel_file}")
        return {"output_file": None, "elapsed": 0, "row_count": 0, "flowchart_count": 0}

    wb = openpyxl.load_workbook(excel_file, data_only=True)
    sheet = wb.active

    doc = Document()
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
        f_col = row[5]   # F列（发起者+接收者）
        i_col = row[8]   # I列（五级模块/功能过程名）
        j_col = row[9]   # J列（子过程描述）
        k_col = row[10] if len(row) > 10 else None  # K列（数据移动类型）
        m_col = row[12] if len(row) > 12 else None  # M列（数据属性）
        data.append((c_col, d_col, e_col, f_col, i_col, j_col, k_col, m_col))

    callback_print(f"[Flow] 读取到 {len(data)} 行数据（从第 2 行开始）")

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

    # 当前段落的发起者/接收者
    current_sender = ""
    current_receiver = ""
    # 当前功能过程名（I列）
    current_process_name = ""
    # 正文缓存
    content_buffer = []

    flowchart_count = 0
    skipped_rows = 0
    current_heading_title = ""

    def flush_section():
        """输出当前段落的流程图 + 正文（图片在前，文字在后）"""
        nonlocal flowchart_count, skipped_rows

        has_text = bool(content_buffer)
        has_flowchart = bool(
            generate_flowchart
            and current_sender
            and current_receiver
            and current_process_name
        )

        if not has_text and not has_flowchart:
            return

        callback_print(f"[Flow] 输出段落：流程图={'是' if has_flowchart else '否'}，正文={len(content_buffer)} 条")

        # === 1. 先输出流程图图片 ===
        if has_flowchart:
            flowchart_count += 1
            process = current_process_name
            sender = current_sender
            receiver = current_receiver

            callback_print(f"[Flow] --- 第 {flowchart_count} 张流程图 ---")
            callback_print(f"[Flow] 发起者：{sender}")
            callback_print(f"[Flow] 接收者：{receiver}")
            callback_print(f"[Flow] 功能过程：{process}")

            # 四箭头固定模板
            arrows = [
                {"from": sender, "to": receiver,
                 "label": f"发起{process}请求", "dashed": False},
                {"from": receiver, "to": "数据库",
                 "label": f"调用{process}接口", "dashed": False},
                {"from": "数据库", "to": receiver,
                 "label": f"返回{process}数据", "dashed": True},
                {"from": receiver, "to": sender,
                 "label": f"展示{process}结果", "dashed": True},
            ]

            for a in arrows:
                arrow_type = "虚线(返回)" if a['dashed'] else "实线(请求)"
                callback_print(f"[Flow]   {a['from']} --[{arrow_type}]--> {a['to']}: {a['label']}")

            participants = [sender, receiver, "数据库"]

            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name

            ok = render_sequence_diagram(
                participants=participants,
                arrows=arrows,
                output_path=tmp_path,
                title="",  # 不在图片中生成标题，避免重复
            )

            if ok:
                callback_print(f"[Flow] 流程图渲染成功：{tmp_path}")
                add_centered_picture(doc, tmp_path, width_inches=5.5)
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            else:
                callback_print("[Flow] 流程图渲染失败，跳过图片插入")

        # === 2. 再输出正文段落（和模块六完全一致）===
        if has_text:
            callback_print(f"[Flow] 输出正文段落：共 {len(content_buffer)} 条")
            for i, (jv, mv) in enumerate(content_buffer, start=1):
                if i == 1:
                    text = f"({i}){current_sender}{jv}，字段包括{mv}。"
                elif i == len(content_buffer):
                    text = f"({i}){current_receiver}向{current_sender}{jv}，字段包括{mv}。"
                else:
                    text = f"({i}){current_receiver}{jv}，字段包括{mv}。"
                add_paragraph(doc, text)
            content_buffer.clear()

    # ========== 主循环 ==========
    for idx, (c_col, d_col, e_col, f_col, i_col, j_col, k_col, m_col) in enumerate(data):
        # 当层级变化时先输出缓存
        if content_buffer or current_process_name:
            if (c_col and c_col != last_c) or (d_col and d_col != last_d) or (e_col and e_col != last_e):
                flush_section()

        # 二级标题 (C列)
        if c_col and c_col != last_c:
            flush_section()
            level2_num += 1
            level3_num = 0
            level4_num = 0
            level5_num = 0
            current_heading_title = f"{level1_num}.{level2_num} {c_col}"
            add_heading(doc, current_heading_title, 'Heading 2')
            last_c = c_col

        # 三级标题 (D列)
        if d_col and d_col != last_d:
            flush_section()
            level3_num += 1
            level4_num = 0
            level5_num = 0
            current_heading_title = f"{level1_num}.{level2_num}.{level3_num} {d_col}"
            add_heading(doc, current_heading_title, 'Heading 3')
            last_d = d_col

        # 四级标题 (E列)
        if e_col and e_col != last_e:
            flush_section()
            level4_num += 1
            level5_num = 0
            current_heading_title = f"{level1_num}.{level2_num}.{level3_num}.{level4_num} {e_col}"
            add_heading(doc, current_heading_title, 'Heading 4')
            last_e = e_col

        # 五级标题 (I列) — 每个功能过程是一个独立段落
        if i_col and i_col != last_i:
            flush_section()
            level5_num += 1
            current_heading_title = f"{level1_num}.{level2_num}.{level3_num}.{level4_num}.{level5_num} {i_col}"
            add_heading(doc, current_heading_title, 'Heading 5')
            current_process_name = str(i_col).strip()
            last_i = i_col

        # 解析发起者/接收者（F列）
        if f_col:
            sender, receiver = parse_sender_receiver(f_col)
            if sender and receiver:
                current_sender = sender
                current_receiver = receiver
            else:
                skipped_rows += 1
                callback_print(f"[Flow] 跳过 F 列解析失败的行（行号约 {idx + 2}），F={f_col}")

        # 收集正文数据（J列为主，M列可选）
        if j_col:
            content_buffer.append((j_col, m_col or ""))

        # 末行刷出
        if idx == len(data) - 1:
            flush_section()

    # ========== 保存文档 ==========
    out_dir = os.path.dirname(output_file)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    if os.path.exists(output_file):
        os.remove(output_file)

    doc.save(output_file)
    elapsed = time.time() - start_time
    callback_print(f"[Flow] 转换完成，输出文件：{output_file}，总用时 {elapsed:.1f} 秒")
    callback_print(f"[Flow] 流程图数量：{flowchart_count}，跳过行数：{skipped_rows}")

    return {
        "output_file": output_file,
        "elapsed": elapsed,
        "row_count": len(data),
        "flowchart_count": flowchart_count,
    }
