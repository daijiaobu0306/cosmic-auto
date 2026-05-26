"""NESMA 评估 Excel → Word 转换脚本（核心逻辑）

层级结构：
  2. 业务功能需求                    -- 一级标题（代码写死）
  2.1. {C列值}                       -- 二级标题
  2.1.1. {D列值}                     -- 三级标题
  2.1.1.1. {F列值}                   -- 四级标题
  2.1.1.1.1. 功能描述                -- 五级标题（代码写死）
      {I列值，首行缩进2字符}
  2.1.1.1.2. 流程图                  -- 五级标题（代码写死）
      业务流程图：
      【时序图，居中】                -- K/L/M列作为3个参与者
      业务功能：
      1、{K}向{L}提交{F}请求。
      2、{L}调用{M}中的{F}接口。
      3、{F}接口返回数据给{L}。
      4、{L}将{F}结果返回至{K}。

用法：
  python nesma_to_word.py
  （修改下方 EXCEL_PATH / OUTPUT_PATH 后直接运行）
"""
import os
import math
import tempfile
import openpyxl
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt, Inches
from docx.enum.text import WD_LINE_SPACING, WD_ALIGN_PARAGRAPH
from PIL import Image, ImageDraw, ImageFont


# ==================== 配置 ====================
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "投资类项目-新一代全景观测平台-NESMA评估材料0521.xlsx")
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "NESMA评估输出_新-v3.docx")


# ==================== 时序图渲染器（来自 flowchart_renderer.py）====================

def _get_font(size: int = 14):
    """尝试加载系统中文字体"""
    font_candidates = [
        "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",   # 黑体
        "C:/Windows/Fonts/simsun.ttc",   # 宋体
        "C:/Windows/Fonts/simfang.ttf",  # 仿宋
    ]
    for fp in font_candidates:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_dashed_line(draw, x0, y0, x1, y1, fill="#000000", dash_len=6, gap_len=4, width=1):
    """绘制虚线"""
    dx = x1 - x0
    dy = y1 - y0
    length = math.sqrt(dx * dx + dy * dy)
    if length == 0:
        return
    ux, uy = dx / length, dy / length
    pos = 0
    while pos < length:
        sx = x0 + ux * pos
        sy = y0 + uy * pos
        end = min(pos + dash_len, length)
        ex = x0 + ux * end
        ey = y0 + uy * end
        draw.line([(sx, sy), (ex, ey)], fill=fill, width=width)
        pos += dash_len + gap_len


def _wrap_text(text, max_chars=19):
    """将长文本按最大字符数换行，返回行列表"""
    if len(text) <= max_chars:
        return [text]
    lines = []
    while text:
        lines.append(text[:max_chars])
        text = text[max_chars:]
    return lines


def _draw_multiline_text_centered(draw, cx, cy, text, font, fill="#2c3e50", line_spacing=4):
    """在 cx, cy 位置居中绘制多行文字，返回总高度"""
    lines = _wrap_text(text)
    total_h = 0
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])
        total_h += bbox[3] - bbox[1]
    total_h += line_spacing * (len(lines) - 1)

    y = cy - total_h // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        draw.text((cx - tw // 2, y), line, fill=fill, font=font)
        y += line_heights[i] + line_spacing
    return total_h


def render_sequence_diagram(participants, arrows, output_path):
    """渲染时序图为 PNG 图片（无标题），返回是否成功"""
    try:
        font = _get_font(14)
        font_small = _get_font(12)

        box_w = 160
        base_box_h = 40       # 单行文字的矩形高度
        line_height = 20      # 每增加一行文字的额外高度
        h_gap = 80
        v_gap = 60
        margin_x = 40
        margin_top = 50
        max_chars = 19        # 超过此字符数自动换行

        n_participants = len(participants)
        n_arrows = len(arrows)

        # 预计算每个参与者的文字行数和矩形高度
        participant_lines = {}
        max_lines = 1
        for name in participants:
            lines = _wrap_text(name, max_chars)
            participant_lines[name] = lines
            max_lines = max(max_lines, len(lines))

        box_h = base_box_h + (max_lines - 1) * line_height

        total_width = max(
            margin_x * 2 + n_participants * box_w + (n_participants - 1) * h_gap,
            400,
        )

        # 预计算每个箭头标签的行数，用于动态调整 v_gap
        arrow_line_counts = []
        for arrow in arrows:
            label = arrow.get("label", "")
            arrow_line_counts.append(len(_wrap_text(label, max_chars)))

        # 如果箭头标签有多行，增加 v_gap
        effective_v_gap = v_gap
        for lc in arrow_line_counts:
            if lc > 1:
                effective_v_gap = max(effective_v_gap, v_gap + (lc - 1) * 16)

        total_height = (
            margin_top + box_h + 20 + n_arrows * effective_v_gap + 60
        )

        img = Image.new("RGB", (total_width, total_height), "white")
        draw = ImageDraw.Draw(img)

        y_cursor = margin_top

        # 参与者矩形（支持多行文字）
        participant_x = {}
        start_x = (total_width - (n_participants * box_w + (n_participants - 1) * h_gap)) // 2
        for i, name in enumerate(participants):
            cx = start_x + i * (box_w + h_gap) + box_w // 2
            participant_x[name] = cx
            x0 = cx - box_w // 2
            y0 = y_cursor
            x1 = cx + box_w // 2
            y1 = y_cursor + box_h
            draw.rounded_rectangle([x0, y0, x1, y1], radius=6, fill="#e8f0fe", outline="#3498db", width=2)
            _draw_multiline_text_centered(draw, cx, y0 + box_h // 2, name, font)

        # 生命线
        lifeline_top = y_cursor + box_h
        lifeline_bottom = y_cursor + box_h + 20 + n_arrows * effective_v_gap + 10
        for name in participants:
            cx = participant_x[name]
            _draw_dashed_line(draw, cx, lifeline_top, cx, lifeline_bottom, fill="#bdc3c7", dash_len=6, gap_len=4)

        # 箭头
        y_arrow = lifeline_top + 20 + effective_v_gap // 2
        for arrow in arrows:
            from_name = arrow.get("from", "")
            to_name = arrow.get("to", "")
            label = arrow.get("label", "")
            dashed = arrow.get("dashed", False)

            if from_name not in participant_x or to_name not in participant_x:
                continue

            x_from = participant_x[from_name]
            x_to = participant_x[to_name]
            color = "#7f8c8d" if dashed else "#2c3e50"

            if dashed:
                _draw_dashed_line(draw, x_from, y_arrow, x_to, y_arrow, fill=color, dash_len=8, gap_len=5, width=2)
            else:
                draw.line([(x_from, y_arrow), (x_to, y_arrow)], fill=color, width=2)

            arrow_size = 10
            if x_to > x_from:
                draw.polygon([
                    (x_to, y_arrow),
                    (x_to - arrow_size, y_arrow - arrow_size // 2),
                    (x_to - arrow_size, y_arrow + arrow_size // 2),
                ], fill=color)
            elif x_to < x_from:
                draw.polygon([
                    (x_to, y_arrow),
                    (x_to + arrow_size, y_arrow - arrow_size // 2),
                    (x_to + arrow_size, y_arrow + arrow_size // 2),
                ], fill=color)

            # 箭头标签（支持多行，居中绘制）
            mid_x = (x_from + x_to) // 2
            label_lines = _wrap_text(label, max_chars)
            label_total_h = len(label_lines) * 16
            label_y = y_arrow - 8 - label_total_h
            for li, line in enumerate(label_lines):
                text_bbox = draw.textbbox((0, 0), line, font=font_small)
                tw = text_bbox[2] - text_bbox[0]
                draw.text((mid_x - tw // 2, label_y + li * 16), line, fill="#495057", font=font_small)

            y_arrow += effective_v_gap

        out_dir = os.path.dirname(output_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        img.save(output_path, "PNG")
        return True
    except Exception as e:
        print(f"[渲染异常] {e}")
        return False


# ==================== Word 辅助函数 ====================

def add_heading(doc, text, style_name):
    """添加标题段落，设置黑体"""
    p = doc.add_paragraph(text)
    p.style = style_name
    run = p.runs[0]
    run.font.name = '黑体'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    run.italic = False
    return p


def add_normal_paragraph(doc, text, first_line_indent=True):
    """添加正文段落，宋体 10.5pt，首行缩进"""
    p = doc.add_paragraph(text)
    p.style = 'Normal'
    if first_line_indent:
        p.paragraph_format.first_line_indent = Pt(21)  # 2字符缩进
    return p


def add_centered_picture(doc, image_path, width_inches=5.5):
    """插入居中图片"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    run.add_picture(image_path, width=Inches(width_inches))
    return p


# ==================== 合并单元格处理 ====================

def read_excel_with_merged_cells(excel_path):
    """读取 Excel，处理合并单元格，返回行数据列表

    每行格式: (C值, D值, F值, I值, K值, L值, M值)
    合并单元格的空值会沿用上一行的非空值。
    固定从第 2 行开始读取（第 1 行为表头）。
    """
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    sheet = wb.active

    # 建立合并单元格查找表：对于每个合并区域，非左上角单元格的值 = 左上角单元格的值
    merge_map = {}  # (row, col) -> value
    for merged_range in sheet.merged_cells.ranges:
        top_left_value = sheet.cell(merged_range.min_row, merged_range.min_col).value
        for row in range(merged_range.min_row, merged_range.max_row + 1):
            for col in range(merged_range.min_col, merged_range.max_col + 1):
                if row != merged_range.min_row or col != merged_range.min_col:
                    merge_map[(row, col)] = top_left_value

    data = []
    for row_idx, row in enumerate(sheet.iter_rows(min_row=2), start=2):
        def get_cell(col_idx):
            """获取单元格值，优先从合并映射中取"""
            val = row[col_idx - 1].value  # openpyxl 行是0-based
            if val is None and (row_idx, col_idx) in merge_map:
                val = merge_map[(row_idx, col_idx)]
            return val

        c_val = get_cell(3)   # C列 = 二级标题
        d_val = get_cell(4)   # D列 = 三级标题
        f_val = get_cell(6)   # F列 = 四级标题
        i_val = get_cell(9)   # I列 = 功能描述
        k_val = get_cell(11)  # K列 = 参与者1（时序1）
        l_val = get_cell(12)  # L列 = 参与者2（时序2）
        m_val = get_cell(13)  # M列 = 参与者3（时序3）

        # 跳过完全空行
        if not any([c_val, d_val, f_val, i_val]):
            continue

        data.append((c_val, d_val, f_val, i_val, k_val, l_val, m_val))

    wb.close()
    return data


# ==================== 主转换逻辑 ====================

def convert(excel_path, output_path):
    """执行 NESMA Excel → Word 转换"""
    print(f"[转换] 输入：{excel_path}")
    print(f"[转换] 输出：{output_path}")

    if not os.path.exists(excel_path):
        print(f"[错误] 文件不存在：{excel_path}")
        return

    # --- 1. 读取 Excel ---
    data = read_excel_with_merged_cells(excel_path)
    print(f"[转换] 读取到 {len(data)} 行有效数据")

    # --- 2. 初始化 Word ---
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = '宋体'
    style._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    style.font.size = Pt(10.5)
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE

    # --- 3. 写一级标题（代码写死）---
    add_heading(doc, "2. 业务功能需求", 'Heading 1')

    # --- 4. 编号计数器 ---
    level2_num = 0
    level3_num = 0
    level4_num = 0

    last_c = None
    last_d = None
    last_f = None

    # --- 5. 逐行处理 ---
    for c_val, d_val, f_val, i_val, k_val, l_val, m_val in data:
        process_name = str(f_val).strip() if f_val else ""

        # === 二级标题（C列变化）===
        if c_val and c_val != last_c:
            level2_num += 1
            level3_num = 0
            level4_num = 0
            heading_text = f"2.{level2_num}. {c_val}"
            add_heading(doc, heading_text, 'Heading 2')
            last_c = c_val
            last_d = None  # C变化时重置D
            last_f = None

        # === 三级标题（D列变化）===
        if d_val and d_val != last_d:
            level3_num += 1
            level4_num = 0
            heading_text = f"2.{level2_num}.{level3_num}. {d_val}"
            add_heading(doc, heading_text, 'Heading 3')
            last_d = d_val
            last_f = None  # D变化时重置F

        # === 四级标题（F列 = 每行数据）===
        if f_val and f_val != last_f:
            level4_num += 1
            heading_text = f"2.{level2_num}.{level3_num}.{level4_num}. {process_name}"
            add_heading(doc, heading_text, 'Heading 4')
            last_f = f_val

            # --- 五级标题①：功能描述 ---
            add_heading(doc, f"2.{level2_num}.{level3_num}.{level4_num}.1. 功能描述", 'Heading 5')
            if i_val:
                add_normal_paragraph(doc, str(i_val).strip())

            # --- 五级标题②：流程图 ---
            add_heading(doc, f"2.{level2_num}.{level3_num}.{level4_num}.2. 流程图", 'Heading 5')

            # "业务流程图：" 固定描述
            add_normal_paragraph(doc, "业务流程图：", first_line_indent=False)

            # 生成时序图（K/L/M 列作为三个参与者）
            p1 = str(k_val).strip() if k_val else "参与者1"
            p2 = str(l_val).strip() if l_val else "参与者2"
            p3 = str(m_val).strip() if m_val else "参与者3"
            participants = [p1, p2, p3]

            arrows = [
                {"from": p1, "to": p2, "label": f"发起{process_name}请求", "dashed": False},
                {"from": p2, "to": p3, "label": f"调用{process_name}接口", "dashed": False},
                {"from": p3, "to": p2, "label": f"返回{process_name}数据", "dashed": True},
                {"from": p2, "to": p1, "label": f"展示{process_name}结果", "dashed": True},
            ]

            # 渲染并插入图片
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name

            ok = render_sequence_diagram(
                participants=participants,
                arrows=arrows,
                output_path=tmp_path,
            )
            if ok:
                add_centered_picture(doc, tmp_path, width_inches=5.5)
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
            else:
                print(f"[警告] 时序图渲染失败：{process_name}")

            # "业务功能：" 固定描述 + 四句话模板
            add_normal_paragraph(doc, "业务功能：", first_line_indent=False)
            sentences = [
                f"1、{p1}向{p2}提交{process_name}请求。",
                f"2、{p2}调用{p3}中的{process_name}接口。",
                f"3、{process_name}接口返回对应的数据给{p2}。",
                f"4、{p2}将{process_name}结果返回至{p1}。",
            ]
            for s in sentences:
                add_normal_paragraph(doc, s)

    # --- 6. 保存 ---
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    if os.path.exists(output_path):
        os.remove(output_path)

    doc.save(output_path)
    print(f"[转换] 完成！输出文件：{output_path}")


# ==================== 入口 ====================
if __name__ == "__main__":
    convert(EXCEL_PATH, OUTPUT_PATH)
