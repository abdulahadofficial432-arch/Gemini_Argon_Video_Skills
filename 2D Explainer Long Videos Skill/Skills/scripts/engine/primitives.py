import math
import random
import cairo

# ==============================================================================
# COLOR PALETTE & CONSTANTS (Matched to "Exact Video.mp4")
# ==============================================================================
WIDTH = 1920
HEIGHT = 1080
FPS = 30

def hex_rgb(h):
    h = h.lstrip('#')
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)

def hex_rgba(h, a=1.0):
    r, g, b = hex_rgb(h)
    return (r, g, b, a)

def clamp(val, lo=0.0, hi=1.0):
    return max(lo, min(hi, val))

def smoothstep(edge0, edge1, x):
    if edge1 <= edge0:
        return 1.0 if x >= edge0 else 0.0
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def ease_out_back(t):
    t = clamp(t, 0.0, 1.0)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * pow(t - 1.0, 3) + c1 * pow(t - 1.0, 2)

def ease_out_cubic(t):
    t = clamp(t, 0.0, 1.0)
    return 1.0 - pow(1.0 - t, 3)

# ==============================================================================
# CAMERA & POST-PROCESSING HELPERS
# ==============================================================================
def apply_camera(ctx, zoom=1.0, pan_x=0.0, pan_y=0.0, shake_amp=0.0, t=0.0):
    """Applies continuous camera zoom, pan, and procedural trauma shake."""
    sx = 0.0
    sy = 0.0
    rot = 0.0
    if shake_amp > 0.0:
        sx = math.sin(t * 47.3) * shake_amp + math.cos(t * 83.1) * (shake_amp * 0.5)
        sy = math.cos(t * 53.7) * shake_amp + math.sin(t * 91.9) * (shake_amp * 0.5)
        rot = math.sin(t * 39.0) * (shake_amp * 0.0004)
    ctx.translate(WIDTH / 2.0 + sx, HEIGHT / 2.0 + sy)
    if rot != 0.0:
        ctx.rotate(rot)
    ctx.scale(zoom, zoom)
    ctx.translate(-WIDTH / 2.0 - pan_x, -HEIGHT / 2.0 - pan_y)

_VIGNETTE_SURFACE = None

def get_vignette_surface():
    global _VIGNETTE_SURFACE
    if _VIGNETTE_SURFACE is not None:
        return _VIGNETTE_SURFACE
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    c = cairo.Context(surf)
    # Radial dark vignette matching the atmospheric borders of Exact Video
    pat = cairo.RadialGradient(WIDTH * 0.5, HEIGHT * 0.5, HEIGHT * 0.32,
                               WIDTH * 0.5, HEIGHT * 0.5, WIDTH * 0.65)
    pat.add_color_stop_rgba(0.0, 0.0, 0.0, 0.0, 0.0)
    pat.add_color_stop_rgba(0.65, 0.02, 0.01, 0.01, 0.14)
    pat.add_color_stop_rgba(1.0, 0.0, 0.0, 0.0, 0.58)
    c.set_source(pat)
    c.paint()
    _VIGNETTE_SURFACE = surf
    return surf

def draw_vignette(ctx, strength=1.0):
    surf = get_vignette_surface()
    ctx.save()
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint_with_alpha(clamp(strength, 0.0, 1.0))
    ctx.restore()

def draw_red_alarm_pulse(ctx, t, freq=2.0, max_alpha=0.38):
    """Pulsing emergency red glow overlay across the frame."""
    pulse = (math.sin(t * freq * math.pi * 2.0) * 0.5 + 0.5) ** 1.4
    alpha = pulse * max_alpha
    if alpha <= 0.01:
        return
    ctx.save()
    pat = cairo.RadialGradient(WIDTH * 0.5, HEIGHT * 0.5, 100, WIDTH * 0.5, HEIGHT * 0.5, 1100)
    pat.add_color_stop_rgba(0.0, 0.85, 0.08, 0.08, alpha * 0.45)
    pat.add_color_stop_rgba(1.0, 0.90, 0.05, 0.05, alpha)
    ctx.set_source(pat)
    ctx.paint()
    ctx.restore()

# ==============================================================================
# HAND-INKED VECTOR DRAWING PRIMITIVES
# ==============================================================================
INK_COLOR = (0.10, 0.08, 0.07)  # Deep warm charcoal-black ink outline

def set_ink(ctx, width=4.0, alpha=1.0):
    ctx.set_source_rgba(INK_COLOR[0], INK_COLOR[1], INK_COLOR[2], alpha)
    ctx.set_line_width(width)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

def rounded_rect_path(ctx, x, y, w, h, r=12.0):
    r = min(r, w * 0.5, h * 0.5)
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r, r, -math.pi * 0.5, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi * 0.5)
    ctx.arc(x + r, y + h - r, r, math.pi * 0.5, math.pi)
    ctx.arc(x + r, y + r, r, math.pi, math.pi * 1.5)
    ctx.close_path()

def draw_ink_box(ctx, x, y, w, h, fill_hex="#F5F0DC", stroke_w=4.0, r=0.0, shadow=False, alpha=1.0):
    ctx.save()
    if shadow:
        if r > 0:
            rounded_rect_path(ctx, x + 8, y + 10, w, h, r)
        else:
            ctx.rectangle(x + 8, y + 10, w, h)
        ctx.set_source_rgba(0, 0, 0, 0.32 * alpha)
        ctx.fill()
    if r > 0:
        rounded_rect_path(ctx, x, y, w, h, r)
    else:
        ctx.rectangle(x, y, w, h)
    if fill_hex:
        ctx.set_source_rgba(*hex_rgba(fill_hex, alpha))
        if stroke_w > 0:
            ctx.fill_preserve()
        else:
            ctx.fill()
    if stroke_w > 0:
        set_ink(ctx, stroke_w, alpha)
        ctx.stroke()
    ctx.restore()

def draw_scotch_tape(ctx, x, y, w=110, h=34, angle_deg=25.0, alpha=0.65):
    """Draws the semi-transparent yellowish scotch tape strip at corners of notes."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(math.radians(angle_deg))
    ctx.rectangle(-w * 0.5, -h * 0.5, w, h)
    ctx.set_source_rgba(0.92, 0.89, 0.74, alpha)
    ctx.fill_preserve()
    ctx.set_source_rgba(0.55, 0.52, 0.42, alpha * 0.6)
    ctx.set_line_width(1.5)
    ctx.stroke()
    ctx.restore()

def draw_slanted_stamp_banner(ctx, text, x=110, y=95, angle_deg=-2.2, scale=1.0):
    """Draws the glowing neon-red bordered stamp banner ('6 DAYS FROM NOW', '10:00 PM')."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(math.radians(angle_deg))
    ctx.scale(scale, scale)

    ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(56)
    ext = ctx.text_extents(text)
    pad_x, pad_y = 38, 22
    bw = ext.width + pad_x * 2
    bh = ext.height + pad_y * 2

    # Outer red glow
    for glow_w, glow_a in [(22, 0.18), (14, 0.32), (8, 0.55)]:
        rounded_rect_path(ctx, 0, 0, bw, bh, 8)
        ctx.set_source_rgba(0.95, 0.18, 0.15, glow_a)
        ctx.set_line_width(glow_w)
        ctx.stroke()

    # Dark semi-transparent backing
    rounded_rect_path(ctx, 0, 0, bw, bh, 8)
    ctx.set_source_rgba(0.16, 0.06, 0.06, 0.82)
    ctx.fill_preserve()

    # Crisp white-hot core border
    ctx.set_source_rgba(1.0, 0.92, 0.90, 0.98)
    ctx.set_line_width(5.0)
    ctx.stroke()

    # Text with subtle red outer glow
    tx = pad_x - ext.x_bearing
    ty = pad_y - ext.y_bearing
    ctx.move_to(tx, ty)
    ctx.set_source_rgba(0.95, 0.2, 0.15, 0.5)
    ctx.text_path(text)
    ctx.set_line_width(8)
    ctx.stroke()

    ctx.move_to(tx, ty)
    ctx.set_source_rgb(1.0, 0.98, 0.97)
    ctx.show_text(text)
    ctx.restore()

def draw_speech_bubble(ctx, x, y, w, h, tail_tx, tail_ty, lines, red_last_line=False, scale=1.0):
    """Draws a hand-inked cream speech bubble with a pointed tail."""
    if scale <= 0.01:
        return
    ctx.save()
    cx, cy = x + w * 0.5, y + h * 0.5
    ctx.translate(cx, cy)
    ctx.scale(scale, scale)
    ctx.translate(-cx, -cy)

    # Shadow
    rounded_rect_path(ctx, x + 6, y + 8, w, h, 18)
    ctx.set_source_rgba(0, 0, 0, 0.35)
    ctx.fill()

    # Main bubble + tail
    rounded_rect_path(ctx, x, y, w, h, 18)
    ctx.set_source_rgb(*hex_rgb("#F7F2E2"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()

    # Tail triangle
    bx = clamp(tail_tx, x + 30, x + w - 30)
    by = y + h if tail_ty > cy else y
    ctx.move_to(bx - 16, by - (3 if tail_ty > cy else -3))
    ctx.line_to(tail_tx, tail_ty)
    ctx.line_to(bx + 16, by - (3 if tail_ty > cy else -3))
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#F7F2E2"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()
    # Cover seam
    ctx.move_to(bx - 15, by)
    ctx.line_to(bx + 15, by)
    ctx.set_source_rgb(*hex_rgb("#F7F2E2"))
    ctx.set_line_width(6.0)
    ctx.stroke()

    # Text lines
    ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    font_sz = 30 if len(lines) <= 3 else 26
    ctx.set_font_size(font_sz)
    total_h = len(lines) * (font_sz + 10)
    start_y = y + (h - total_h) * 0.5 + font_sz
    for idx, line in enumerate(lines):
        ext = ctx.text_extents(line)
        lx = x + (w - ext.width) * 0.5
        ly = start_y + idx * (font_sz + 10)
        if red_last_line and idx == len(lines) - 1:
            ctx.set_source_rgb(*hex_rgb("#C91E1E"))
        else:
            ctx.set_source_rgb(*hex_rgb("#1B1918"))
        ctx.move_to(lx, ly)
        ctx.show_text(line)
    ctx.restore()

def draw_digital_clock(ctx, x, y, w, h, time_str="3:00", glow=False):
    """Draws the nightstand red LED digital alarm clock."""
    ctx.save()
    # Outer dark plastic casing
    draw_ink_box(ctx, x, y, w, h, "#252328", stroke_w=3.5, r=8, shadow=True)
    # Inner dark screen
    draw_ink_box(ctx, x + 10, y + 10, w - 20, h - 20, "#12090B", stroke_w=2.0, r=4)

    if glow:
        pat = cairo.RadialGradient(x + w * 0.5, y + h * 0.5, 10, x + w * 0.5, y + h * 0.5, w * 1.2)
        pat.add_color_stop_rgba(0.0, 0.95, 0.12, 0.12, 0.42)
        pat.add_color_stop_rgba(1.0, 0.95, 0.12, 0.12, 0.0)
        ctx.set_source(pat)
        ctx.arc(x + w * 0.5, y + h * 0.5, w * 1.2, 0, math.pi * 2)
        ctx.fill()

    ctx.select_font_face("Consolas", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(h * 0.54)
    ext = ctx.text_extents(time_str)
    tx = x + (w - ext.width) * 0.5 - ext.x_bearing
    ty = y + (h - ext.height) * 0.5 - ext.y_bearing
    # Red LED glow
    ctx.move_to(tx, ty)
    ctx.set_source_rgba(1.0, 0.1, 0.1, 0.45)
    ctx.text_path(time_str)
    ctx.set_line_width(6.0)
    ctx.stroke()

    ctx.move_to(tx, ty)
    ctx.set_source_rgb(1.0, 0.18, 0.16)
    ctx.show_text(time_str)
    ctx.restore()

def draw_ecg_waveform(ctx, t, progress=1.0, spike=False):
    """Draws the glowing red heartbeat ECG trace across the lower screen (Shot 5)."""
    ctx.save()
    y_base = 925
    max_x = int(WIDTH * clamp(progress, 0.0, 1.0))
    pts = []
    for x in range(0, max_x, 6):
        # Periodic P-Q-R-S-T heartbeat complex every 260px
        phase = (x % 260) / 260.0
        dy = 0.0
        is_big_spike = spike and (x > 1350 and x < 1650)
        amp = 2.4 if is_big_spike else 1.0
        if 0.35 < phase < 0.42:
            dy = -18.0 * math.sin((phase - 0.35) / 0.07 * math.pi)
        elif 0.45 <= phase < 0.48:
            dy = 22.0 * ((phase - 0.45) / 0.03)
        elif 0.48 <= phase < 0.54:
            p2 = (phase - 0.48) / 0.06
            dy = (22.0 * (1.0 - p2) - 85.0 * amp * math.sin(p2 * math.pi))
        elif 0.54 <= phase < 0.58:
            dy = 34.0 * amp * math.sin((phase - 0.54) / 0.04 * math.pi)
        elif 0.65 < phase < 0.78:
            dy = -14.0 * math.sin((phase - 0.65) / 0.13 * math.pi)
        pts.append((x, y_base + dy))

    if len(pts) > 1:
        for lw, alpha in [(18.0, 0.18), (10.0, 0.35), (4.5, 0.95)]:
            ctx.move_to(pts[0][0], pts[0][1])
            for px, py in pts[1:]:
                ctx.line_to(px, py)
            if lw < 6.0:
                ctx.set_source_rgba(1.0, 0.35, 0.30, alpha)
            else:
                ctx.set_source_rgba(0.95, 0.08, 0.08, alpha)
            ctx.set_line_width(lw)
            ctx.stroke()
        # Leading white-hot dot
        lx, ly = pts[-1]
        ctx.arc(lx, ly, 8, 0, math.pi * 2)
        ctx.set_source_rgb(1.0, 0.9, 0.9)
        ctx.fill()
    ctx.restore()

def draw_sound_wave_arcs(ctx, cx, cy, angle_rad, spread_rad, t, count=3, max_r=260, color_hex="#E51C1C"):
    """Draws pulsing red emergency sound-wave arcs radiating from phones/walls."""
    ctx.save()
    r_rgb = hex_rgb(color_hex)
    for i in range(count):
        prog = ((t * 1.8 + i / float(count)) % 1.0)
        rad = 35.0 + prog * max_r
        alpha = (1.0 - prog) * 0.85
        for w, a_mul in [(12.0, 0.25), (4.5, 1.0)]:
            ctx.arc(cx, cy, rad, angle_rad - spread_rad * 0.5, angle_rad + spread_rad * 0.5)
            ctx.set_source_rgba(r_rgb[0], r_rgb[1], r_rgb[2], alpha * a_mul)
            ctx.set_line_width(w)
            ctx.stroke()
    ctx.restore()

def draw_fire_plume(ctx, x, y, w, h, t, seed=0):
    """Draws animated flickering cartoon fire tongues and rising smoke."""
    ctx.save()
    n_tongues = max(3, int(w / 28))
    for i in range(n_tongues):
        fx = x + (i + 0.5) * (w / n_tongues)
        phase = t * 8.0 + i * 1.7 + seed
        fh = h * (0.65 + 0.35 * math.sin(phase))
        sway = math.cos(phase * 0.8) * (w * 0.08)
        # Outer orange-red flame
        ctx.move_to(fx - w / n_tongues * 0.65, y)
        ctx.curve_to(fx - w / n_tongues * 0.4, y - fh * 0.5,
                     fx + sway * 0.5, y - fh * 0.8,
                     fx + sway, y - fh)
        ctx.curve_to(fx + sway * 0.5, y - fh * 0.8,
                     fx + w / n_tongues * 0.4, y - fh * 0.5,
                     fx + w / n_tongues * 0.65, y)
        ctx.close_path()
        ctx.set_source_rgba(0.95, 0.36, 0.08, 0.88)
        ctx.fill_preserve()
        set_ink(ctx, 2.5, 0.7)
        ctx.stroke()

        # Inner yellow core
        ch = fh * 0.6
        ctx.move_to(fx - w / n_tongues * 0.35, y)
        ctx.curve_to(fx - w / n_tongues * 0.2, y - ch * 0.5,
                     fx + sway * 0.4, y - ch * 0.8,
                     fx + sway * 0.6, y - ch)
        ctx.curve_to(fx + sway * 0.4, y - ch * 0.8,
                     fx + w / n_tongues * 0.2, y - ch * 0.5,
                     fx + w / n_tongues * 0.35, y)
        ctx.close_path()
        ctx.set_source_rgba(1.0, 0.82, 0.22, 0.92)
        ctx.fill()
    ctx.restore()
