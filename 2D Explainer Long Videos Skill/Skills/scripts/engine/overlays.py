import math
import cairo
from engine.primitives import (
    WIDTH, HEIGHT, hex_rgb, hex_rgba, set_ink, rounded_rect_path,
    draw_ink_box, draw_scotch_tape, draw_speech_bubble, clamp, smoothstep, ease_out_back
)
from engine.characters import draw_hand_with_pen, draw_water_jug

# ==============================================================================
# MINI ICONS FOR NOTEBOOKS & DIAGRAMS
# ==============================================================================
def draw_mini_icon(ctx, icon_type, x, y, size=28):
    ctx.save()
    ctx.translate(x, y)
    s = size / 32.0
    ctx.scale(s, s)
    if icon_type == "water":
        ctx.move_to(0, -16)
        ctx.curve_to(10, -2, 13, 6, 13, 11)
        ctx.arc(0, 11, 13, 0, math.pi)
        ctx.curve_to(-13, 6, -10, -2, 0, -16)
        ctx.close_path()
        ctx.set_source_rgb(*hex_rgb("#3B8EEA"))
        ctx.fill_preserve()
        set_ink(ctx, 2.8)
        ctx.stroke()
    elif icon_type == "food":
        rounded_rect_path(ctx, -11, -12, 22, 26, 4)
        ctx.set_source_rgb(*hex_rgb("#E8922D"))
        ctx.fill_preserve()
        set_ink(ctx, 2.8)
        ctx.stroke()
        ctx.move_to(-11, -5)
        ctx.line_to(11, -5)
        ctx.stroke()
    elif icon_type == "cash":
        draw_ink_box(ctx, -15, -9, 30, 18, "#58B86C", stroke_w=2.8, r=2)
        ctx.arc(0, 0, 5, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#2E6E3A"))
        ctx.fill()
    elif icon_type == "door":
        draw_ink_box(ctx, -10, -16, 20, 32, "#8C5832", stroke_w=2.8, r=1)
        ctx.arc(5, 0, 2.5, 0, math.pi * 2)
        ctx.set_source_rgb(0.95, 0.85, 0.3)
        ctx.fill()
    elif icon_type == "battery":
        draw_ink_box(ctx, -10, -12, 20, 26, "#7A4CE0", stroke_w=2.8, r=2)
        draw_ink_box(ctx, -5, -16, 10, 4, "#7A4CE0", stroke_w=2.5)
    elif icon_type == "siren":
        ctx.arc(0, 4, 12, math.pi, 0)
        ctx.line_to(12, 12)
        ctx.line_to(-12, 12)
        ctx.close_path()
        ctx.set_source_rgb(*hex_rgb("#D92525"))
        ctx.fill_preserve()
        set_ink(ctx, 2.8)
        ctx.stroke()
    ctx.restore()

# ==============================================================================
# SPIRAL LINED NOTEBOOK POPUP (With Live Moving Pen Hand & Hatched Progress Bars)
# ==============================================================================
def draw_notebook_card(ctx, x, y, w, h, title="", sub_title="", items=None,
                       progress=1.0, angle_deg=-1.6, spiral=True, tape=True, show_pen=True):
    """
    Draws the signature lined spiral notebook popup and animates items sequentially
    according to `progress` in [0, 1], placing the cartoon hand+pen at the active tip.
    """
    if items is None:
        items = []
    ctx.save()
    cx, cy = x + w * 0.5, y + h * 0.5
    pop_s = ease_out_back(clamp(progress * 6.0, 0.0, 1.0))
    ctx.translate(cx, cy)
    ctx.rotate(math.radians(angle_deg))
    ctx.scale(pop_s, pop_s)
    ctx.translate(-cx, -cy)

    # Drop shadow & cream paper base (#F5F0DC)
    draw_ink_box(ctx, x, y, w, h, "#F5F0DC", stroke_w=3.5, r=4, shadow=True)

    # Horizontal light-blue ruled lines
    line_spacing = 46
    for ly in range(int(y + 72), int(y + h - 16), line_spacing):
        ctx.move_to(x + 4, ly)
        ctx.line_to(x + w - 4, ly)
        ctx.set_source_rgba(0.68, 0.78, 0.88, 0.65)
        ctx.set_line_width(2.0)
        ctx.stroke()

    # Vertical red margin line
    margin_x = x + 68 if spiral else x + 48
    ctx.move_to(margin_x, y + 4)
    ctx.line_to(margin_x, y + h - 4)
    ctx.set_source_rgba(0.86, 0.32, 0.30, 0.78)
    ctx.set_line_width(2.5)
    ctx.stroke()

    # Punched holes & silver wire spiral rings on left edge
    if spiral:
        for hy in (y + h * 0.22, y + h * 0.50, y + h * 0.78):
            ctx.arc(x + 36, hy, 10, 0, math.pi * 2)
            ctx.set_source_rgba(0.32, 0.28, 0.24, 0.65)
            ctx.fill_preserve()
            set_ink(ctx, 2.0, 0.5)
            ctx.stroke()
        for sy in range(int(y + 24), int(y + h - 18), 38):
            rounded_rect_path(ctx, x - 14, sy, 28, 12, 5)
            ctx.set_source_rgb(0.75, 0.77, 0.80)
            ctx.fill_preserve()
            set_ink(ctx, 2.2)
            ctx.stroke()

    # Scotch tape at top right
    if tape:
        draw_scotch_tape(ctx, x + w - 35, y + 12, w=115, h=36, angle_deg=28.0)

    # Header Title (with yellow highlighter strip)
    cur_y = y + 64
    if title:
        ctx.save()
        ctx.rectangle(margin_x + 14, cur_y - 38, w - (margin_x - x) - 36, 46)
        ctx.set_source_rgba(0.97, 0.89, 0.42, 0.72)
        ctx.fill()
        ctx.restore()

        ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(40)
        ctx.set_source_rgb(*hex_rgb("#162955"))
        ctx.move_to(margin_x + 20, cur_y)
        ctx.show_text(title)
        if sub_title:
            ext = ctx.text_extents(title)
            ctx.set_font_size(22)
            ctx.move_to(margin_x + 32 + ext.width, cur_y - 2)
            ctx.show_text(sub_title)
        cur_y += 62

    # Progressive items & active pen position tracking
    n_items = max(1, len(items))
    pen_tx, pen_ty = None, None
    pen_col = "#162955"

    for idx, item in enumerate(items):
        t0 = 0.08 + (idx / float(n_items)) * 0.82
        t1 = 0.08 + ((idx + 1) / float(n_items)) * 0.82
        iprog = clamp((progress - t0) / max(0.01, (t1 - t0)), 0.0, 1.0)
        if iprog <= 0.0:
            break

        itype = item.get("type", "text")
        ix = margin_x + 22

        if itype == "bar_row":
            icon = item.get("icon", "water")
            label = item.get("label", "WATER")
            val_text = item.get("val", "2 gal")
            new_val = item.get("new_val", None)
            bar_frac = item.get("frac", 0.1)
            bar_col = item.get("color", "#3B8EEA")

            draw_mini_icon(ctx, icon, ix + 16, cur_y - 12, size=30)
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(34)
            ctx.set_source_rgb(*hex_rgb("#162955"))

            full_str = f"{label} {val_text}"
            vis_chars = max(1, int(len(full_str) * clamp(iprog * 1.6, 0.0, 1.0)))
            sub_str = full_str[:vis_chars]
            ctx.move_to(ix + 44, cur_y)
            ctx.show_text(sub_str)
            ext = ctx.text_extents(sub_str)

            if new_val and iprog > 0.55:
                # Red strikethrough over old val + red new_val beside it
                lbl_ext = ctx.text_extents(label + " ")
                val_ext = ctx.text_extents(val_text)
                sx0 = ix + 44 + lbl_ext.width
                ctx.move_to(sx0 - 4, cur_y - 12)
                ctx.line_to(sx0 + val_ext.width + 6, cur_y - 16)
                ctx.set_source_rgb(*hex_rgb("#D42620"))
                ctx.set_line_width(4.5)
                ctx.stroke()

                nv_prog = clamp((iprog - 0.55) / 0.45, 0.0, 1.0)
                nv_chars = max(1, int(len(new_val) * nv_prog))
                nv_sub = new_val[:nv_chars]
                ctx.move_to(sx0 + val_ext.width + 18, cur_y)
                ctx.show_text(nv_sub)
                nv_ext = ctx.text_extents(nv_sub)
                pen_tx = sx0 + val_ext.width + 22 + nv_ext.width
                pen_ty = cur_y - 6
                pen_col = "#D42620"
            elif iprog < 0.98:
                pen_tx = ix + 48 + ext.width
                pen_ty = cur_y - 6
                pen_col = "#162955"

            # Progress Bar with hatched fill
            bx, by = ix + 44, cur_y + 16
            bw = w - (margin_x - x) - 95
            bh = 24
            draw_ink_box(ctx, bx, by, bw, bh, "#F5F0DC", stroke_w=2.8)
            fill_w = bw * bar_frac * clamp((iprog - 0.25) / 0.75, 0.0, 1.0)
            if fill_w > 2:
                ctx.save()
                ctx.rectangle(bx + 2, by + 2, fill_w - 2, bh - 4)
                ctx.clip()
                ctx.set_source_rgba(*hex_rgba(bar_col, 0.35))
                ctx.paint()
                # Diagonal hatch lines
                ctx.set_source_rgb(*hex_rgb(bar_col))
                ctx.set_line_width(2.5)
                for hx in range(int(bx - bh), int(bx + fill_w + bh), 8):
                    ctx.move_to(hx, by + bh)
                    ctx.line_to(hx + bh, by)
                ctx.stroke()
                ctx.restore()
            cur_y += 92

        elif itype == "tally":
            max_count = item.get("max_count", 28)
            cur_count = max(1, int(round(max_count * iprog)))
            denom = item.get("denom", "")

            # Draw big counter number in header right
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(58)
            is_done = (cur_count >= max_count)
            ctx.set_source_rgb(*hex_rgb("#D42620" if is_done else "#162955"))
            num_str = f"{cur_count}"
            ctx.move_to(x + w * 0.52, y + 66)
            ctx.show_text(num_str)
            if is_done:
                Rounded = draw_ink_box(ctx, x + w * 0.49, y + 14, 92, 64, None, stroke_w=3.5)
            if denom:
                ctx.set_font_size(34)
                ctx.set_source_rgb(*hex_rgb("#162955"))
                ctx.move_to(x + w * 0.72, y + 66)
                ctx.show_text(denom)

            # Draw tally groups of 5
            tx_start = margin_x + 24
            ty_row = cur_y + 12
            for g in range((cur_count + 4) // 5):
                gx = tx_start + (g % 3) * 105
                gy = ty_row + (g // 3) * 62
                n_in_group = min(5, cur_count - g * 5)
                n_vert = min(4, n_in_group)
                for v in range(n_vert):
                    vx = gx + v * 14
                    ctx.move_to(vx, gy - 26)
                    ctx.line_to(vx + 2, gy + 16)
                    ctx.set_source_rgb(*hex_rgb("#162955"))
                    ctx.set_line_width(4.0)
                    ctx.stroke()
                    pen_tx, pen_ty = vx + 2, gy
                if n_in_group == 5:
                    ctx.move_to(gx - 8, gy + 10)
                    ctx.line_to(gx + 52, gy - 18)
                    ctx.set_source_rgb(*hex_rgb("#D42620"))
                    ctx.set_line_width(4.2)
                    ctx.stroke()
                    pen_tx, pen_ty = gx + 52, gy - 18
                    pen_col = "#D42620"

        elif itype == "text":
            txt = item.get("text", "")
            col = item.get("color", "#162955")
            sz = item.get("size", 34)
            highlight = item.get("highlight", None)
            circle = item.get("circle", False)

            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(sz)
            vis_n = max(1, int(len(txt) * iprog))
            sub_t = txt[:vis_n]
            ext = ctx.text_extents(sub_t)

            if highlight and iprog > 0.3:
                ctx.save()
                ctx.rectangle(ix - 4, cur_y - sz + 4, ext.width + 12, sz + 6)
                ctx.set_source_rgba(*hex_rgba(highlight, 0.55))
                ctx.fill()
                ctx.restore()

            ctx.set_source_rgb(*hex_rgb(col))
            ctx.move_to(ix, cur_y)
            ctx.show_text(sub_t)

            if circle and iprog > 0.75:
                ctx.save()
                ctx.translate(ix + ext.width * 0.5, cur_y - sz * 0.35)
                ctx.scale(1.0, 0.52)
                ctx.arc(0, 0, ext.width * 0.62, 0, math.pi * 2 * clamp((iprog - 0.75) * 4.0, 0, 1))
                ctx.set_source_rgb(*hex_rgb("#D42620"))
                ctx.set_line_width(4.0)
                ctx.stroke()
                ctx.restore()

            if iprog < 0.98:
                pen_tx = ix + ext.width + 6
                pen_ty = cur_y - 4
                pen_col = col
            cur_y += sz + 22

        elif itype == "pass_row":
            letter = item.get("letter", "P")
            rest = item.get("rest", "ull the pin")
            lcol = item.get("color", "#D4A017")
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(58)
            ctx.set_source_rgb(*hex_rgb(lcol))
            ctx.move_to(ix, cur_y + 8)
            ctx.show_text(letter)

            ctx.set_font_size(30)
            ctx.set_source_rgb(*hex_rgb("#162955"))
            vis_n = max(1, int(len(rest) * iprog))
            sub_r = rest[:vis_n]
            ctx.move_to(ix + 46, cur_y + 6)
            ctx.show_text(sub_r)
            ext = ctx.text_extents(sub_r)
            if iprog < 0.98:
                pen_tx = ix + 48 + ext.width
                pen_ty = cur_y
                pen_col = "#162955"
            cur_y += 92

        elif itype == "month_droplets":
            # 6x5 grid of 30 blue water droplets
            gx0 = margin_x + 28
            gy0 = cur_y - 18
            cw, ch = (w - (margin_x - x) - 65) / 6.0, 52
            n_drops = int(round(30 * iprog))
            for r in range(5):
                for c in range(6):
                    d_idx = r * 6 + c + 1
                    cx_cell = gx0 + c * cw
                    cy_cell = gy0 + r * ch
                    draw_ink_box(ctx, cx_cell, cy_cell, cw, ch, None, stroke_w=2.0)
                    if d_idx <= n_drops:
                        draw_mini_icon(ctx, "water", cx_cell + cw * 0.55, cy_cell + ch * 0.55, size=24)
                        pen_tx, pen_ty = cx_cell + cw * 0.6, cy_cell + ch * 0.6
                        pen_col = "#3B8EEA"

    if show_pen and pen_tx is not None and pen_ty is not None:
        draw_hand_with_pen(ctx, pen_tx, pen_ty, pen_color=pen_col, angle_deg=35.0, scale=0.88)

    ctx.restore()

# ==============================================================================
# STICKY NOTE & TAPED INDEX LABELS
# ==============================================================================
def draw_sticky_note_pad(ctx, x, y, w, h, lines, progress=1.0, circle_word=None, show_pen=True):
    """Draws the yellow post-it sticky note pad ('3 MIN AIR / 3 DAYS WATER / 3 WEEKS FOOD')."""
    ctx.save()
    # Stacked yellow sheets behind
    draw_ink_box(ctx, x + 6, y + 6, w, h, "#D8BA38", stroke_w=3.5, shadow=True)
    draw_ink_box(ctx, x, y, w, h, "#F2D44E", stroke_w=4.0)

    # Curled bottom-right corner
    ctx.move_to(x + w - 42, y + h)
    ctx.line_to(x + w, y + h - 38)
    ctx.line_to(x + w - 36, y + h - 32)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#D8BA38"))
    ctx.fill_preserve()
    set_ink(ctx, 3.0)
    ctx.stroke()

    ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(40)
    n_lines = max(1, len(lines))
    pen_tx, pen_ty = None, None
    for i, line in enumerate(lines):
        t0 = (i / float(n_lines)) * 0.85
        t1 = ((i + 1) / float(n_lines)) * 0.85
        lprog = clamp((progress - t0) / max(0.01, t1 - t0), 0.0, 1.0)
        if lprog <= 0:
            break
        vis_n = max(1, int(len(line) * lprog))
        sub = line[:vis_n]
        ly = y + 95 + i * 90
        ctx.set_source_rgb(*hex_rgb("#1B1918"))
        ctx.move_to(x + 36, ly)
        ctx.show_text(sub)
        ext = ctx.text_extents(sub)
        if lprog < 0.98:
            pen_tx, pen_ty = x + 42 + ext.width, ly - 8

        if circle_word and circle_word in line and progress > 0.85:
            cprog = clamp((progress - 0.85) / 0.15, 0.0, 1.0)
            ctx.save()
            ctx.translate(x + 36 + ext.width * 0.72, ly - 14)
            ctx.scale(1.0, 0.48)
            ctx.arc(0, 0, 75, 0, math.pi * 2 * cprog)
            ctx.set_source_rgb(*hex_rgb("#D42620"))
            ctx.set_line_width(4.5)
            ctx.stroke()
            ctx.restore()
            pen_tx, pen_ty = x + 36 + ext.width * 0.72 + 75, ly - 14

    if show_pen and pen_tx is not None:
        draw_hand_with_pen(ctx, pen_tx, pen_ty, pen_color="#D42620", angle_deg=32.0, scale=0.92)
    ctx.restore()

def draw_taped_label(ctx, x, y, text, sub_text=None, color="#162955", angle_deg=-2.5, scale=1.0):
    """Draws a white/cream lined paper strip taped to the screen."""
    if scale <= 0.01:
        return
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(math.radians(angle_deg))
    ctx.scale(scale, scale)

    ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(34)
    ext = ctx.text_extents(text)
    w = max(210, ext.width + 64)
    h = 74 if not sub_text else 118

    draw_ink_box(ctx, -w * 0.5, -h * 0.5, w, h, "#F5F0DC", stroke_w=3.2, shadow=True)
    draw_scotch_tape(ctx, 0, -h * 0.5 - 4, w=72, h=26, angle_deg=3.0)

    ctx.set_source_rgb(*hex_rgb(color))
    ctx.move_to(-ext.width * 0.5, 10 if not sub_text else -8)
    ctx.show_text(text)

    if sub_text:
        ctx.set_font_size(28)
        ctx.set_source_rgb(*hex_rgb("#162955"))
        ext2 = ctx.text_extents(sub_text)
        ctx.move_to(-ext2.width * 0.5, 34)
        ctx.show_text(sub_text)
    ctx.restore()

# ==============================================================================
# OCTOBER WALL CALENDAR TRANSITION SCENE
# ==============================================================================
def draw_october_calendar(ctx, t, crossed_days, active_day, bottom_title,
                          bottom_sub="", show_cardboard=False, red_siren=False, prog=1.0):
    """
    Renders the iconic October wall calendar scene where a red marker crosses out
    each day (17..23) and writes the countdown at the bottom.
    """
    ctx.save()
    # Warm brown wall background (tinted crimson during 1 DAY LEFT / HOUR ZERO)
    if red_siren:
        pulse = 0.5 + 0.5 * math.sin(t * 10.0)
        ctx.set_source_rgb(0.45 + 0.18 * pulse, 0.18, 0.14)
    else:
        ctx.set_source_rgb(*hex_rgb("#7A5E42"))
    ctx.paint()

    cal_x = 380 if show_cardboard else 510
    cal_y = 35
    cal_w = 840
    cal_h = 980

    # Slight perspective tilt when cardboard appears
    ctx.save()
    if show_cardboard:
        ctx.translate(cal_x + cal_w * 0.5, cal_y + cal_h * 0.5)
        ctx.rotate(math.radians(-1.2))
        ctx.translate(-(cal_x + cal_w * 0.5), -(cal_y + cal_h * 0.5))

    draw_ink_box(ctx, cal_x, cal_y, cal_w, cal_h, "#F4F1EA", stroke_w=4.5, shadow=True)

    # Red pushpin at top center
    ctx.arc(cal_x + cal_w * 0.5, cal_y + 26, 13, 0, math.pi * 2)
    ctx.set_source_rgb(*hex_rgb("#C92420"))
    ctx.fill_preserve()
    set_ink(ctx, 3.5)
    ctx.stroke()

    # "OCTOBER" header
    ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(72)
    ctx.set_source_rgb(*hex_rgb("#181615"))
    oct_ext = ctx.text_extents("OCTOBER")
    ctx.move_to(cal_x + (cal_w - oct_ext.width) * 0.5, cal_y + 125)
    ctx.show_text("OCTOBER")

    # Days of week header: S M T W T F S
    gx0 = cal_x + 55
    gy0 = cal_y + 185
    gw = cal_w - 110
    gh = 530
    cw = gw / 7.0
    ch = gh / 5.0

    days_hdr = ["S", "M", "T", "W", "T", "F", "S"]
    ctx.set_font_size(28)
    for c, dh in enumerate(days_hdr):
        ctx.move_to(gx0 + c * cw + cw * 0.42, gy0 - 14)
        ctx.show_text(dh)

    # 5x7 Grid (Oct 1 starts on Wednesday col=3)
    pen_tx, pen_ty = None, None
    for r in range(5):
        for c in range(7):
            cx_cell = gx0 + c * cw
            cy_cell = gy0 + r * ch
            draw_ink_box(ctx, cx_cell, cy_cell, cw, ch, None, stroke_w=3.0)
            day_num = r * 7 + c - 2
            if 1 <= day_num <= 31:
                ctx.set_font_size(24)
                ctx.set_source_rgb(*hex_rgb("#181615"))
                ctx.move_to(cx_cell + 10, cy_cell + 28)
                ctx.show_text(str(day_num))

                # Thursday 23 circled in red with "9 PM"
                if day_num == 23:
                    ctx.save()
                    ctx.arc(cx_cell + cw * 0.5, cy_cell + ch * 0.52, cw * 0.54, 0, math.pi * 2)
                    ctx.set_source_rgb(*hex_rgb("#C92420"))
                    ctx.set_line_width(7.0)
                    ctx.stroke()
                    ctx.set_font_size(22)
                    ctx.move_to(cx_cell + 24, cy_cell + ch - 16)
                    ctx.show_text("9 PM")
                    ctx.restore()

                # Previously crossed out days
                if day_num in crossed_days:
                    ctx.move_to(cx_cell + 16, cy_cell + 16)
                    ctx.line_to(cx_cell + cw - 16, cy_cell + ch - 16)
                    ctx.move_to(cx_cell + cw - 16, cy_cell + 16)
                    ctx.line_to(cx_cell + 16, cy_cell + ch - 16)
                    ctx.set_source_rgb(*hex_rgb("#C92420"))
                    ctx.set_line_width(8.0)
                    ctx.stroke()

                # Active day being crossed out right now
                if day_num == active_day:
                    xprog = clamp(prog * 2.2, 0.0, 1.0)
                    if xprog > 0:
                        p1 = clamp(xprog * 2.0, 0.0, 1.0)
                        ctx.move_to(cx_cell + 16, cy_cell + 16)
                        ctx.line_to(cx_cell + 16 + (cw - 32) * p1, cy_cell + 16 + (ch - 32) * p1)
                        ctx.set_source_rgb(*hex_rgb("#C92420"))
                        ctx.set_line_width(8.5)
                        ctx.stroke()
                        pen_tx = cx_cell + 16 + (cw - 32) * p1
                        pen_ty = cy_cell + 16 + (ch - 32) * p1
                    if xprog > 0.5:
                        p2 = clamp((xprog - 0.5) * 2.0, 0.0, 1.0)
                        ctx.move_to(cx_cell + cw - 16, cy_cell + 16)
                        ctx.line_to(cx_cell + cw - 16 - (cw - 32) * p2, cy_cell + 16 + (ch - 32) * p2)
                        ctx.set_source_rgb(*hex_rgb("#C92420"))
                        ctx.set_line_width(8.5)
                        ctx.stroke()
                        pen_tx = cx_cell + cw - 16 - (cw - 32) * p2
                        pen_ty = cy_cell + 16 + (ch - 32) * p2

    # Bottom Red Countdown Text ("6 DAYS LEFT", etc.)
    tprog = clamp((prog - 0.35) / 0.55, 0.0, 1.0)
    if tprog > 0 and bottom_title:
        ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(68)
        ctx.set_source_rgb(*hex_rgb("#C92420"))
        vis_n = max(1, int(len(bottom_title) * tprog))
        sub_bt = bottom_title[:vis_n]
        ext_bt = ctx.text_extents(sub_bt)
        btx = cal_x + 95
        bty = cal_y + 835
        ctx.move_to(btx, bty)
        ctx.show_text(sub_bt)
        if tprog < 0.98:
            pen_tx, pen_ty = btx + ext_bt.width + 8, bty - 12

        if bottom_sub and tprog > 0.75:
            ctx.set_font_size(30)
            ctx.set_source_rgb(*hex_rgb("#221E1D"))
            ctx.move_to(cal_x + 360, cal_y + 895)
            ctx.show_text(bottom_sub)

    ctx.restore()  # end calendar transform

    # Taped cardboard on right ("THIS SIDE UP ↑") from Day 4 onward
    if show_cardboard:
        cb_x, cb_y, cb_w, cb_h = 1320, 115, 470, 680
        draw_ink_box(ctx, cb_x, cb_y, cb_w, cb_h, "#9E7B56", stroke_w=4.0, shadow=True)
        draw_scotch_tape(ctx, cb_x + 20, cb_y + 20, 95, 34, -35)
        draw_scotch_tape(ctx, cb_x + cb_w - 20, cb_y + 20, 95, 34, 35)
        draw_scotch_tape(ctx, cb_x + 20, cb_y + cb_h - 20, 95, 34, 35)
        draw_scotch_tape(ctx, cb_x + cb_w - 20, cb_y + cb_h - 20, 95, 34, -35)

        ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(32)
        ctx.set_source_rgba(0.28, 0.18, 0.12, 0.85)
        ctx.move_to(cb_x + 85, cb_y + 275)
        ctx.show_text("THIS SIDE UP ↑")

    if pen_tx is not None and pen_ty is not None:
        draw_hand_with_pen(ctx, pen_tx, pen_ty, pen_color="#C92420", angle_deg=42.0, scale=1.0)
    ctx.restore()

# ==============================================================================
# SMARTPHONE UI & EMERGENCY ALERT SCREENS
# ==============================================================================
def draw_smartphone_alert(ctx, t, clock_str="3:12", header_tag="COUNTY ALERT · now",
                          big_title="EMERGENCY\nALERT", body_lines=None,
                          highlight_phrase=None, footer_code=None,
                          two_hands=False, screenshot_flash=0.0, progress=1.0):
    """
    Renders the closeup smartphone held in Chad's hand(s) with glowing red
    EMERGENCY ALERT screen and progressive text reveal.
    """
    if body_lines is None:
        body_lines = []
    ctx.save()

    # Phone bezel dimensions
    px, py, pw, ph = 640, 55, 620, 980
    ctx.translate(px + pw * 0.5, py + ph * 0.5)
    ctx.rotate(math.radians(-1.8))
    ctx.translate(-(px + pw * 0.5), -(py + ph * 0.5))

    # Red ambient backlight behind phone
    pat = cairo.RadialGradient(px + pw * 0.5, py + ph * 0.45, 80, px + pw * 0.5, py + ph * 0.45, 620)
    pat.add_color_stop_rgba(0.0, 0.95, 0.12, 0.12, 0.52)
    pat.add_color_stop_rgba(1.0, 0.95, 0.12, 0.12, 0.0)
    ctx.set_source(pat)
    ctx.paint()

    # Outer dark phone body (#1D1E22)
    draw_ink_box(ctx, px, py, pw, ph, "#1D1E22", stroke_w=5.0, r=42, shadow=True)
    # Inner screen (#0E0F12)
    sx, sy, sw, sh = px + 24, py + 28, pw - 48, ph - 56
    draw_ink_box(ctx, sx, sy, sw, sh, "#0E0F12", stroke_w=2.0, r=28)

    # Top status bar
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.set_source_rgba(0.95, 0.95, 0.95, 0.9)
    ctx.move_to(sx + 32, sy + 42)
    ctx.show_text(clock_str)
    # Status icons on right
    for bi in range(3):
        ctx.rectangle(sx + sw - 110 + bi * 22, sy + 22, 14, 20)
        ctx.fill()

    # Red Alert Card inside screen
    ax, ay, aw = sx + 18, sy + 64, sw - 36
    ah = clamp(progress * 1.35, 0.18, 1.0) * (sh - 120)
    draw_ink_box(ctx, ax, ay, aw, ah, "#BF1515", stroke_w=0, r=22)

    # Warning triangle + header_tag
    ctx.move_to(ax + 36, ay + 24)
    ctx.line_to(ax + 22, ay + 50)
    ctx.line_to(ax + 50, ay + 50)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#F7D436"))
    ctx.fill_preserve()
    set_ink(ctx, 2.5)
    ctx.stroke()

    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.set_source_rgb(1.0, 0.96, 0.96)
    ctx.move_to(ax + 64, ay + 47)
    ctx.show_text(header_tag)

    # Big Title
    cur_y = ay + 115
    if progress > 0.12:
        ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(52)
        for tline in big_title.split("\n"):
            ctx.move_to(ax + 28, cur_y)
            ctx.show_text(tline)
            cur_y += 60
        cur_y += 16

    # Progressive body lines
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(38)
    n_b = max(1, len(body_lines))
    for i, bline in enumerate(body_lines):
        t0 = 0.22 + (i / float(n_b)) * 0.65
        if progress < t0:
            break
        if highlight_phrase and highlight_phrase in bline and progress > t0 + 0.12:
            # Yellow highlighter behind phrase
            pre = bline.split(highlight_phrase)[0]
            pre_ext = ctx.text_extents(pre)
            hp_ext = ctx.text_extents(highlight_phrase)
            rounded_rect_path(ctx, ax + 26 + pre_ext.width, cur_y - 38, hp_ext.width + 16, 48, 8)
            ctx.set_source_rgba(0.98, 0.78, 0.18, 0.65)
            ctx.fill()

        ctx.set_source_rgb(1.0, 0.97, 0.97)
        ctx.move_to(ax + 28, cur_y)
        ctx.show_text(bline)
        cur_y += 50

    # Operator footer (EW04)
    if footer_code:
        ctx.select_font_face("Consolas", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(20)
        ctx.set_source_rgba(1.0, 0.85, 0.85, 0.75)
        ctx.move_to(ax + 28, ay + ah - 75)
        ctx.show_text("Sender: Ashford County · Operator:")
        ctx.set_font_size(46)
        ctx.set_source_rgb(1.0, 0.25, 0.22)
        ctx.move_to(ax + 150, ay + ah - 22)
        ctx.show_text(footer_code)

    # Screenshot flash & corner thumbnail preview (Shot 30)
    if screenshot_flash > 0.0:
        if screenshot_flash < 0.35:
            ctx.rectangle(sx, sy, sw, sh)
            ctx.set_source_rgba(1, 1, 1, (0.35 - screenshot_flash) * 2.5)
            ctx.fill()
        else:
            # Mini screenshot thumbnail in top-right of phone screen
            draw_ink_box(ctx, sx + sw - 165, sy + 95, 135, 235, "#BF1515", stroke_w=3.5, r=8, shadow=True)

    # Cartoon hands gripping the phone bezel
    if two_hands:
        for side in (-1, 1):
            hx = px if side == -1 else px + pw
            hy = py + ph * 0.68
            rounded_rect_path(ctx, hx - 75, hy - 45, 150, 95, 42)
            ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
            ctx.fill_preserve()
            set_ink(ctx, 4.5)
            ctx.stroke()
    else:
        # Left thumb overlapping bottom-left bezel
        ctx.move_to(px - 140, py + ph)
        ctx.curve_to(px - 90, py + ph - 180, px + 30, py + ph - 210, px + 75, py + ph - 165)
        ctx.curve_to(px + 95, py + ph - 135, px + 40, py + ph - 40, px - 20, py + ph)
        ctx.close_path()
        ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
        ctx.fill_preserve()
        set_ink(ctx, 5.0)
        ctx.stroke()

        # Right 3 fingers wrapping right bezel edge
        for fi in range(3):
            fy = py + ph * 0.66 + fi * 82
            rounded_rect_path(ctx, px + pw - 24, fy, 74, 64, 30)
            ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
            ctx.fill_preserve()
            set_ink(ctx, 5.0)
            ctx.stroke()

    ctx.restore()
