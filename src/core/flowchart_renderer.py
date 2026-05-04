"""纯 Python 时序图渲染器（基于 Pillow，零外部依赖）

用于替代 mermaid-cli (mmdc)，方便打包成 exe 后开箱即用。
"""
import os
import tempfile
from PIL import Image, ImageDraw, ImageFont


def _get_font(size: int = 14):
    """尝试加载系统中文字体，失败则用默认字体"""
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


def render_sequence_diagram(
    participants: list[str],
    arrows: list[dict],
    output_path: str,
    title: str = "",
) -> bool:
    """
    渲染时序图为 PNG 图片。

    参数：
        participants: 参与者名称列表，如 ["用户", "系统", "数据库"]
        arrows: 箭头列表，每项为：
            {
                "from": 参与者名称,
                "to": 参与者名称,
                "label": "动作描述",
                "dashed": False,  # True=虚线（返回），False=实线（请求）
            }
        output_path: 输出 PNG 路径
        title: 可选标题

    返回：是否成功
    """
    try:
        # === 参数计算 ===
        font = _get_font(14)
        font_small = _get_font(12)
        title_font = _get_font(16)

        box_w = 160       # 参与者矩形宽度
        box_h = 40         # 参与者矩形高度
        h_gap = 80         # 参与者之间的水平间距
        v_gap = 60         # 箭头之间的垂直间距
        margin_x = 40      # 左右留白
        margin_top = 50    # 顶部留白
        label_offset = 8   # 箭头文字偏移

        n_participants = len(participants)
        n_arrows = len(arrows)

        # 计算画布尺寸
        total_width = max(
            margin_x * 2 + n_participants * box_w + (n_participants - 1) * h_gap,
            400,
        )
        # 标题留白
        title_offset = 30 if title else 0
        total_height = (
            margin_top
            + title_offset
            + box_h
            + 20  # lifeline 起始偏移
            + n_arrows * v_gap
            + 60  # 底部留白
        )

        img = Image.new("RGB", (total_width, total_height), "white")
        draw = ImageDraw.Draw(img)

        # === 绘制标题 ===
        y_cursor = margin_top
        if title:
            bbox = draw.textbbox((0, 0), title, font=title_font)
            tw = bbox[2] - bbox[0]
            draw.text(((total_width - tw) // 2, y_cursor), title, fill="#2c3e50", font=title_font)
            y_cursor += title_offset

        # === 计算每个参与者中心 X 坐标 ===
        participant_x = {}
        start_x = (total_width - (n_participants * box_w + (n_participants - 1) * h_gap)) // 2
        for i, name in enumerate(participants):
            cx = start_x + i * (box_w + h_gap) + box_w // 2
            participant_x[name] = cx

            # 绘制矩形框
            x0 = cx - box_w // 2
            y0 = y_cursor
            x1 = cx + box_w // 2
            y1 = y_cursor + box_h
            draw.rounded_rectangle([x0, y0, x1, y1], radius=6, fill="#e8f0fe", outline="#3498db", width=2)

            # 绘制文字（居中）
            text_bbox = draw.textbbox((0, 0), name, font=font)
            tw = text_bbox[2] - text_bbox[0]
            th = text_bbox[3] - text_bbox[1]
            draw.text(
                (cx - tw // 2, y0 + (box_h - th) // 2),
                name,
                fill="#2c3e50",
                font=font,
            )

        # === 绘制生命线（垂直虚线）===
        lifeline_top = y_cursor + box_h
        lifeline_bottom = y_cursor + box_h + 20 + n_arrows * v_gap + 10
        for name in participants:
            cx = participant_x[name]
            _draw_dashed_line(draw, cx, lifeline_top, cx, lifeline_bottom, fill="#bdc3c7", dash_len=6, gap_len=4)

        # === 绘制箭头 ===
        y_arrow = lifeline_top + 20 + v_gap // 2
        for arrow in arrows:
            from_name = arrow.get("from", "")
            to_name = arrow.get("to", "")
            label = arrow.get("label", "")
            dashed = arrow.get("dashed", False)

            if from_name not in participant_x or to_name not in participant_x:
                continue

            x_from = participant_x[from_name]
            x_to = participant_x[to_name]

            # 箭头线
            color = "#7f8c8d" if dashed else "#2c3e50"
            if dashed:
                _draw_dashed_line(draw, x_from, y_arrow, x_to, y_arrow, fill=color, dash_len=8, gap_len=5, width=2)
            else:
                draw.line([(x_from, y_arrow), (x_to, y_arrow)], fill=color, width=2)

            # 箭头头部
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

            # 箭头标签
            mid_x = (x_from + x_to) // 2
            label_y = y_arrow - 18
            text_bbox = draw.textbbox((0, 0), label, font=font_small)
            tw = text_bbox[2] - text_bbox[0]
            draw.text((mid_x - tw // 2, label_y), label, fill="#495057", font=font_small)

            y_arrow += v_gap

        # === 保存 ===
        out_dir = os.path.dirname(output_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        img.save(output_path, "PNG")
        return True

    except Exception as e:
        print(f"[Flowchart] 渲染异常：{e}")
        return False


def _draw_dashed_line(
    draw: ImageDraw.ImageDraw,
    x0: int, y0: int, x1: int, y1: int,
    fill: str = "#000000",
    dash_len: int = 6,
    gap_len: int = 4,
    width: int = 1,
):
    """绘制虚线"""
    import math
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
