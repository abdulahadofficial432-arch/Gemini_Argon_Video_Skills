import math
import cairo
from engine.primitives import (
    WIDTH, HEIGHT, hex_rgb, hex_rgba, set_ink, rounded_rect_path,
    draw_ink_box, draw_scotch_tape, draw_speech_bubble, clamp, smoothstep
)
from engine.characters import draw_hand_with_pen, draw_water_jug
from engine.overlays import draw_mini_icon, draw_notebook_card, draw_taped_label

# ==============================================================================
# 1. COUNTY WEBSITE & PHONE CALL / DELETED VIDEO SCREENS
# ==============================================================================
def draw_county_website_phone(ctx, t, prog):
    """Shot 13: ashfordcounty-oem.gov/alerts showing 'No alerts issued this week'."""
    ctx.save()
    px, py, pw, ph = 640, 45, 640, 990
    draw_ink_box(ctx, px, py, pw, ph, "#1D1E22", stroke_w=5.0, r=42, shadow=True)
    sx, sy, sw, sh = px + 24, py + 28, pw - 48, ph - 56
    draw_ink_box(ctx, sx, sy, sw, sh, "#F4F2EC", stroke_w=2.0, r=26)

    scroll_y = -prog * 110.0
    ctx.save()
    rounded_rect_path(ctx, sx, sy + 90, sw, sh - 90, 20)
    ctx.clip()
    ctx.translate(0, scroll_y)

    # Navy Header Banner
    draw_ink_box(ctx, sx, sy + 90, sw, 115, "#1E3A5F", stroke_w=0)
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(30)
    ctx.set_source_rgb(1, 1, 1)
    ctx.move_to(sx + 95, sy + 142)
    ctx.show_text("ASHFORD COUNTY")
    ctx.set_font_size(20)
    ctx.set_source_rgba(0.85, 0.9, 1.0, 0.9)
    ctx.move_to(sx + 95, sy + 172)
    ctx.show_text("Emergency Management")

    # Green status card: "No alerts issued this week"
    gx, gy, gw, gh = sx + 34, sy + 275, sw - 68, 165
    draw_ink_box(ctx, gx, gy, gw, gh, "#D4EDDA", stroke_w=3.0, r=14)
    ctx.arc(gx + 52, gy + gh * 0.5, 24, 0, math.pi * 2)
    ctx.set_source_rgb(*hex_rgb("#28A745"))
    ctx.fill_preserve()
    set_ink(ctx, 2.5)
    ctx.stroke()

    ctx.set_font_size(34)
    ctx.set_source_rgb(*hex_rgb("#15251B"))
    ctx.move_to(gx + 96, gy + 68)
    ctx.show_text("No alerts issued")
    ctx.move_to(gx + 96, gy + 108)
    ctx.show_text("this week")
    ctx.set_font_size(18)
    ctx.move_to(gx + 96, gy + 140)
    ctx.show_text("Last updated: Fri 8:00 AM")

    # Skeleton placeholder rows under "Recent alerts"
    ctx.set_font_size(24)
    ctx.move_to(gx, gy + 215)
    ctx.show_text("Recent alerts")
    for r in range(4):
        draw_ink_box(ctx, gx, gy + 235 + r * 78, gw, 60, "#EAE6DC", stroke_w=1.5, r=8)
    ctx.restore()

    # URL bar at top
    draw_ink_box(ctx, sx + 22, sy + 36, sw - 44, 44, "#E2DFD7", stroke_w=2.0, r=12)
    ctx.set_font_size(19)
    ctx.set_source_rgb(0.2, 0.2, 0.2)
    ctx.move_to(sx + 55, sy + 64)
    ctx.show_text("ashfordcounty-oem.gov/alerts")

    # Cartoon hand scrolling at bottom right
    hx = px + pw - 90
    hy = py + ph - 180 - math.sin(prog * math.pi) * 90
    rounded_rect_path(ctx, hx - 35, hy - 20, 95, 55, 25)
    ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()
    ctx.restore()

def draw_phone_call_hangup(ctx, t, prog):
    """Shot 80: Dark phone call UI with 'Your name?' speech bubble and finger pressing end-call."""
    ctx.save()
    ctx.set_source_rgb(0.03, 0.03, 0.04)
    ctx.paint()

    px, py, pw, ph = 680, 180, 520, 820
    ctx.save()
    ctx.translate(px + pw * 0.5, py + ph * 0.5)
    ctx.rotate(math.radians(8.0))
    ctx.translate(-(px + pw * 0.5), -(py + ph * 0.5))

    draw_ink_box(ctx, px, py, pw, ph, "#1A1D24", stroke_w=5.0, r=38, shadow=True)
    # Avatar circle
    ctx.arc(px + pw * 0.5, py + 230, 68, 0, math.pi * 2)
    ctx.set_source_rgb(0.32, 0.35, 0.42)
    ctx.fill()

    # Red hang-up button at bottom center
    bx, by = px + pw * 0.5, py + ph - 140
    ctx.arc(bx, by, 44, 0, math.pi * 2)
    ctx.set_source_rgb(*hex_rgb("#D92525"))
    ctx.fill_preserve()
    set_ink(ctx, 3.0)
    ctx.stroke()
    ctx.restore()

    # Speech bubble at top
    b_txt = ["Your name?"] if prog > 0.25 else ["..."]
    draw_speech_bubble(ctx, 480, 95, 620, 175, 920, 340, b_txt, scale=clamp(prog * 4.0, 0.0, 1.0))

    # Cartoon hand pressing red button
    tap_x = 925 - (1.0 - clamp(prog * 1.4, 0.0, 1.0)) * 180
    tap_y = 845 + (1.0 - clamp(prog * 1.4, 0.0, 1.0)) * 120
    ctx.move_to(0, 680)
    ctx.line_to(tap_x - 35, tap_y)
    set_ink(ctx, 18.0)
    ctx.stroke()
    ctx.arc(tap_x, tap_y, 34, 0, math.pi * 2)
    ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()
    ctx.restore()

def draw_deleted_videos_grid(ctx, t, prog):
    """Shot 60: 3x3 grid of viral hospital zombie videos turning 'Video unavailable'."""
    ctx.save()
    px, py, pw, ph = 640, 55, 640, 960
    draw_ink_box(ctx, px, py, pw, ph, "#1D1E22", stroke_w=5.0, r=40, shadow=True)
    sx, sy, sw, sh = px + 24, py + 28, pw - 48, ph - 56
    draw_ink_box(ctx, sx, sy, sw, sh, "#121316", stroke_w=2.0, r=26)

    # Search bar
    draw_ink_box(ctx, sx + 28, sy + 55, sw - 56, 46, "#EAE6DC", stroke_w=2.0, r=12)
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(22)
    ctx.set_source_rgb(0.15, 0.15, 0.15)
    ctx.move_to(sx + 48, sy + 86)
    ctx.show_text("ashford hospital attack")

    # 3x3 grid of video thumbnails
    gx0, gy0 = sx + 26, sy + 125
    cw = (sw - 68) / 3.0
    ch = (sh - 175) / 3.0
    del_order = [0, 4, 2, 6, 8, 1, 3, 7, 5]
    n_deleted = int(prog * 10.5)

    for idx in range(9):
        r, c = idx // 3, idx % 3
        tx = gx0 + c * (cw + 8)
        ty = gy0 + r * (ch + 8)
        is_del = (del_order.index(idx) < n_deleted)
        if is_del:
            draw_ink_box(ctx, tx, ty, cw, ch, "#2A2B2E", stroke_w=2.0, r=6)
            ctx.arc(tx + cw * 0.5, ty + ch * 0.38, 18, 0, math.pi * 2)
            ctx.set_source_rgba(0.75, 0.75, 0.78, 0.8)
            ctx.set_line_width(3.0)
            ctx.stroke()
            ctx.set_font_size(17)
            ctx.move_to(tx + 22, ty + ch * 0.68)
            ctx.show_text("Video")
            ctx.move_to(tx + 12, ty + ch * 0.82)
            ctx.show_text("unavailable")
        else:
            # Greenish hospital zombie thumbnail + play icon
            draw_ink_box(ctx, tx, ty, cw, ch, "#5E7268", stroke_w=2.0, r=6)
            ctx.arc(tx + cw * 0.5, ty + ch * 0.42, 26, 0, math.pi * 2)
            ctx.set_source_rgb(*hex_rgb("#8C948E"))
            ctx.fill_preserve()
            set_ink(ctx, 2.0)
            ctx.stroke()
            ctx.arc(tx + cw * 0.5, ty + ch * 0.5, 18, 0, math.pi * 2)
            ctx.set_source_rgba(0, 0, 0, 0.55)
            ctx.fill()

    # Two cartoon hands holding phone
    for side in (-1, 1):
        hx = px if side == -1 else px + pw
        rounded_rect_path(ctx, hx - 70, py + ph * 0.65, 140, 88, 38)
        ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
        ctx.fill_preserve()
        set_ink(ctx, 4.5)
        ctx.stroke()
    ctx.restore()

# ==============================================================================
# 2. MACRO PIXEL-GRID "EW04" & INVESTIGATION BOARD
# ==============================================================================
def draw_pixel_macro_ew04(ctx, t, prog):
    """Shot 32: Extreme macro zoom on red LED pixel grid 'Sender: Ashford County · Operator: EW04'."""
    ctx.save()
    ctx.set_source_rgb(0.58, 0.08, 0.08)
    ctx.paint()

    # Pixel grid lines
    ctx.set_source_rgba(0.25, 0.02, 0.02, 0.45)
    ctx.set_line_width(2.0)
    for gx in range(0, WIDTH, 16):
        ctx.move_to(gx, 0)
        ctx.line_to(gx, HEIGHT)
    for gy in range(0, HEIGHT, 16):
        ctx.move_to(0, gy)
        ctx.line_to(WIDTH, gy)
    ctx.stroke()

    # Pan left so "Operator: EW04" moves into center
    pan_x = (1.0 - smoothstep(0.0, 0.55, prog)) * 950.0 - 420.0
    ctx.select_font_face("Consolas", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(145)
    txt = "Sender: Ashford County · Operator: EW04"
    ctx.set_source_rgba(1.0, 0.88, 0.86, 0.92)
    ctx.move_to(pan_x, 565)
    ctx.show_text(txt)

    # Circle "EW04" in glowing red ink when pan settles
    if prog > 0.52:
        cprog = clamp((prog - 0.52) / 0.38, 0.0, 1.0)
        cx, cy = 1020, 515
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(1.8, 0.95)
        ctx.arc(0, 0, 185, 0, math.pi * 2 * cprog)
        ctx.set_source_rgb(1.0, 0.22, 0.18)
        ctx.set_line_width(14.0)
        ctx.stroke()
        ctx.restore()
        ang = math.pi * 2 * cprog
        tip_x = cx + math.cos(ang) * 185 * 1.8
        tip_y = cy + math.sin(ang) * 185 * 0.95
        draw_hand_with_pen(ctx, tip_x, tip_y, pen_color="#E51C1C", angle_deg=55.0, scale=1.05)

    ctx.restore()

def draw_email_printout(ctx, t, prog):
    """Shot 45: Full-screen email from Ashford County OEM + Library Volunteer card."""
    ctx.save()
    ctx.set_source_rgb(0.08, 0.08, 0.10)
    ctx.paint()

    cx, cy, cw, ch = 260, 55, 1400, 970
    draw_ink_box(ctx, cx, cy, cw, ch, "#F6F3EB", stroke_w=4.5, shadow=True)

    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(38)
    ctx.set_source_rgb(*hex_rgb("#1B1918"))

    headers = [
        ("From: Ashford County OEM", "#1B1918"),
        ("To: Chad", "#1B1918"),
        ("Date: April 12, last spring", "#1B1918"),
        ("Subject: Welcome to the  ", "#1B1918"),
    ]
    for i, (htxt, hcol) in enumerate(headers):
        if prog > i * 0.08:
            ctx.move_to(cx + 65, cy + 95 + i * 56)
            ctx.show_text(htxt)

    if prog > 0.28:
        ctx.set_source_rgb(*hex_rgb("#D42620"))
        ctx.move_to(cx + 530, cy + 95 + 3 * 56)
        ctx.show_text("Emergency Alert Test Group")
        ctx.move_to(cx + 530, cy + 108 + 3 * 56)
        ctx.line_to(cx + 1060, cy + 108 + 3 * 56)
        ctx.set_line_width(6.0)
        ctx.stroke()

    ctx.move_to(cx + 45, cy + 305)
    ctx.line_to(cx + cw - 45, cy + 305)
    ctx.set_source_rgb(0.55, 0.54, 0.52)
    ctx.set_line_width(2.5)
    ctx.stroke()

    # Taped Library Volunteer sign-up card on right
    if prog > 0.18:
        lx, ly, lw, lh = cx + 810, cy + 345, 510, 325
        draw_ink_box(ctx, lx, ly, lw, lh, "#EAE0C8", stroke_w=3.8, shadow=True)
        draw_scotch_tape(ctx, lx + lw * 0.5, ly - 4, 85, 28, 2.0)
        ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(28)
        ctx.set_source_rgb(*hex_rgb("#2B2622"))
        ctx.move_to(lx + 32, ly + 52)
        ctx.show_text("LIBRARY · VOLUNTEERS")
        ctx.set_font_size(18)
        ctx.set_source_rgb(0.38, 0.34, 0.30)
        ctx.move_to(lx + 32, ly + 82)
        ctx.show_text("Spring sign-up")
        for r in range(4):
            ry = ly + 118 + r * 52
            ctx.move_to(lx + 32, ry)
            ctx.line_to(lx + lw - 32, ry)
            ctx.set_source_rgb(0.55, 0.50, 0.44)
            ctx.set_line_width(2.0)
            ctx.stroke()
            if r in (0, 1, 3):
                # Wavy squiggle signatures for other volunteers
                ctx.move_to(lx + 38, ry - 12)
                for wx in range(0, 140 if r < 2 else 95, 28):
                    ctx.rel_curve_to(10, -12, 18, 12, 28, 0)
                ctx.set_source_rgb(0.38, 0.34, 0.30)
                ctx.set_line_width(2.5)
                ctx.stroke()
        if prog > 0.25:
            sprog = clamp((prog - 0.25) / 0.20, 0.0, 1.0)
            sig = "Chad H."[:max(1, int(7 * sprog))]
            ctx.set_font_size(38)
            ctx.set_source_rgb(*hex_rgb("#162955"))
            ctx.move_to(lx + 42, ly + 216)
            ctx.show_text(sig)
            if sprog < 0.98:
                ext = ctx.text_extents(sig)
                draw_hand_with_pen(ctx, lx + 46 + ext.width, ly + 210, pen_color="#162955", scale=0.85)

    # Bottom body text + yellow highlighter
    if prog > 0.55:
        body_lines = [
            "Thank you for joining,",
            "Zone Four volunteer.",
            "Your phone is our",
            "only civilian test device."
        ]
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(46)
        for bi, bl in enumerate(body_lines):
            if prog > 0.55 + bi * 0.09:
                by = cy + 685 + bi * 66
                if bi == 3 and prog > 0.86:
                    hprog = clamp((prog - 0.86) / 0.12, 0.0, 1.0)
                    ctx.rectangle(cx + 60, by - 44, 590 * hprog, 56)
                    ctx.set_source_rgba(0.98, 0.90, 0.28, 0.72)
                    ctx.fill()
                ctx.set_source_rgb(*hex_rgb("#181615"))
                ctx.move_to(cx + 65, by)
                ctx.show_text(bl)
    ctx.restore()

def draw_ellen_ward_board(ctx, t, prog):
    """Shot 46: Ellen Ward business card + Polaroid EW04 + Zone 1..4 map."""
    ctx.save()
    ctx.set_source_rgb(0.06, 0.06, 0.08)
    ctx.paint()

    # Left Card: Ellen Ward
    draw_ink_box(ctx, 145, 165, 680, 350, "#F5F2EA", stroke_w=4.0, shadow=True)
    ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(28)
    ctx.set_source_rgb(0.35, 0.35, 0.35)
    ctx.move_to(185, 220)
    ctx.show_text("Signed,")
    ctx.set_font_size(74)
    ctx.set_source_rgb(*hex_rgb("#162955"))
    ctx.move_to(195, 325)
    ctx.show_text("Ellen Ward")
    ctx.set_font_size(32)
    ctx.move_to(195, 425)
    ctx.show_text("Emergency Coordinator")
    ctx.move_to(195, 470)
    ctx.show_text("Ashford County OEM")

    # Right Polaroid: ALERT TEST / EW04
    draw_ink_box(ctx, 1060, 115, 680, 520, "#F5F2EA", stroke_w=4.0, shadow=True)
    draw_scotch_tape(ctx, 1400, 115, 90, 32, 0.0)
    draw_ink_box(ctx, 1110, 145, 580, 390, "#1A1C22", stroke_w=3.0)
    draw_ink_box(ctx, 1235, 185, 330, 325, "#3A1212", stroke_w=3.0)
    draw_ink_box(ctx, 1235, 185, 330, 55, "#C92420", stroke_w=0)
    ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(26)
    ctx.set_source_rgb(1, 1, 1)
    ctx.move_to(1255, 224)
    ctx.show_text("ALERT TEST")
    ctx.set_font_size(24)
    ctx.move_to(1255, 295)
    ctx.show_text("Zone 4 · Civilian")
    ctx.move_to(1255, 335)
    ctx.show_text("Operator:")
    ctx.set_font_size(48)
    ew_str = "EW04" if prog > 0.35 else "  04"
    ctx.move_to(1250, 405)
    ctx.show_text(ew_str)

    ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(28)
    ctx.set_source_rgb(*hex_rgb("#162955"))
    ctx.move_to(1140, 590)
    ctx.show_text("my phone, alert #3")

    # Red dashed connector curve ("same person")
    if prog > 0.35:
        cprog = clamp((prog - 0.35) / 0.25, 0.0, 1.0)
        ctx.save()
        ctx.set_dash([18.0, 14.0])
        ctx.move_to(360, 355)
        ctx.curve_to(650, 490, 980, 490, 360 + (1295 - 360) * cprog, 355 + (425 - 355) * cprog)
        ctx.set_source_rgb(*hex_rgb("#E51C1C"))
        ctx.set_line_width(6.0)
        ctx.stroke()
        ctx.restore()
        ctx.set_font_size(36)
        ctx.set_source_rgb(0.95, 0.93, 0.88)
        ctx.move_to(640, 565)
        ctx.show_text("same person")

    # Bottom Zone 1..4 Map Card
    if prog > 0.58:
        zx, zy, zw, zh = 510, 610, 540, 350
        draw_ink_box(ctx, zx, zy, zw, zh, "#F4EFE2", stroke_w=4.0, shadow=True)
        ctx.move_to(zx + zw * 0.5, zy + 20)
        ctx.line_to(zx + zw * 0.5, zy + zh - 20)
        ctx.move_to(zx + 20, zy + zh * 0.5)
        ctx.line_to(zx + zw - 20, zy + zh * 0.5)
        set_ink(ctx, 3.5)
        ctx.stroke()

        ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(38)
        ctx.set_source_rgb(*hex_rgb("#3A3836"))
        ctx.move_to(zx + 55, zy + 105)
        ctx.show_text("Zone 1")
        ctx.move_to(zx + 330, zy + 105)
        ctx.show_text("Zone 2")
        ctx.move_to(zx + 55, zy + 275)
        ctx.show_text("Zone 3")
        ctx.set_source_rgb(*hex_rgb("#D42620"))
        ctx.move_to(zx + 330, zy + 275)
        ctx.show_text("Zone 4")

        if prog > 0.78:
            ctx.save()
            ctx.translate(zx + 405, zy + 262)
            ctx.scale(1.6, 0.75)
            ctx.arc(0, 0, 62, 0, math.pi * 2)
            ctx.set_source_rgb(*hex_rgb("#D42620"))
            ctx.set_line_width(5.0)
            ctx.stroke()
            ctx.restore()
            ctx.set_font_size(34)
            ctx.move_to(1380, 695)
            ctx.show_text("YOUR ZONE!")
    ctx.restore()

# ==============================================================================
# 3. ARCHITECTURAL & SURVIVAL TECHNICAL DIAGRAMS
# ==============================================================================
def draw_door_cross_section(ctx, t, prog):
    """Shot 49: 'Your front door, from above' cross-section with frame splintering."""
    ctx.save()
    ctx.set_source_rgb(0.18, 0.16, 0.14)
    ctx.paint()

    cx, cy, cw, ch = 135, 110, 1650, 860
    draw_ink_box(ctx, cx, cy, cw, ch, "#F5F2EA", stroke_w=5.0, shadow=True)

    ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(44)
    ctx.set_source_rgb(*hex_rgb("#162955"))
    ctx.move_to(cx + 55, cy + 80)
    ctx.show_text("Your front door, from above")

    ctx.set_font_size(36)
    ctx.set_source_rgb(0.42, 0.42, 0.42)
    ctx.move_to(cx + 65, cy + 185)
    ctx.show_text("OUTSIDE")
    ctx.move_to(cx + 65, cy + 760)
    ctx.show_text("INSIDE")

    # Left wall stud, center wooden door slab, right frame + wall stud
    y_mid = cy + 430
    draw_ink_box(ctx, cx + 50, y_mid - 45, 235, 95, "#D9D2C2", stroke_w=4.5)

    # Door slab (tilts down slightly on kick impact)
    kick_p = smoothstep(0.35, 0.65, prog)
    ctx.save()
    ctx.translate(cx + 315, y_mid)
    ctx.rotate(math.radians(kick_p * 3.2))
    draw_ink_box(ctx, 0, -35, 730, 70, "#B88655", stroke_w=4.5)
    # Latch bolt
    draw_ink_box(ctx, 710, -12, 55, 24, "#8C9298", stroke_w=3.5)
    ctx.restore()

    # Right door frame + wall stud
    draw_ink_box(ctx, cx + 1055, y_mid - 48, 95, 96, "#D8B384", stroke_w=4.5)
    draw_ink_box(ctx, cx + 1165, y_mid - 55, 180, 110, "#C99E67", stroke_w=4.5)
    draw_ink_box(ctx, cx + 1360, y_mid - 45, 240, 95, "#D9D2C2", stroke_w=4.5)

    # Labels
    ctx.set_font_size(30)
    ctx.set_source_rgb(*hex_rgb("#162955"))
    ctx.move_to(cx + 390, y_mid + 85)
    ctx.show_text("door")
    ctx.move_to(cx + 860, y_mid + 85)
    ctx.show_text("lock")
    ctx.move_to(cx + 1015, y_mid - 82)
    ctx.show_text("frame")
    ctx.move_to(cx + 1205, y_mid + 125)
    ctx.show_text("wall stud")

    # Red kick arrow above door
    if prog > 0.20:
        ax, ay = cx + 680, y_mid - 165 + kick_p * 25
        ctx.move_to(ax, ay)
        ctx.line_to(ax, ay + 95)
        ctx.move_to(ax - 24, ay + 68)
        ctx.line_to(ax, ay + 98)
        ctx.line_to(ax + 24, ay + 68)
        ctx.set_source_rgb(*hex_rgb("#D42620"))
        ctx.set_line_width(14.0)
        ctx.stroke()

    # Frame splintering & big red X at lock frame
    if prog > 0.55:
        fx, fy = cx + 1085, y_mid + 20
        set_ink(ctx, 4.0)
        for ang, d in [(-0.4, 65), (0.1, 80), (0.6, 70), (1.1, 55)]:
            ctx.move_to(fx, fy)
            ctx.line_to(fx + math.cos(ang) * d, fy + math.sin(ang) * d)
        ctx.stroke()

        # Big Red X over broken frame
        ctx.move_to(fx - 75, fy - 75)
        ctx.line_to(fx + 75, fy + 75)
        ctx.move_to(fx + 75, fy - 75)
        ctx.line_to(fx - 75, fy + 75)
        ctx.set_source_rgb(*hex_rgb("#D42620"))
        ctx.set_line_width(14.0)
        ctx.stroke()
    ctx.restore()

def draw_strike_plate_ruler(ctx, t, prog):
    """Shot 50: Metal strike plate + tiny 1-inch screw measured by yellow ruler."""
    ctx.save()
    ctx.set_source_rgb(0.18, 0.16, 0.14)
    ctx.paint()
    cx, cy, cw, ch = 220, 105, 1480, 870
    draw_ink_box(ctx, cx, cy, cw, ch, "#F5F2EA", stroke_w=5.0, shadow=True)

    # Metal strike plate on left
    spx, spy, spw, sph = cx + 210, cy + 145, 290, 580
    draw_ink_box(ctx, spx, spy, spw, sph, "#B4B8BC", stroke_w=5.0, r=18, shadow=True)
    draw_ink_box(ctx, spx + 48, spy + 145, 140, 290, "#6E7276", stroke_w=4.5, r=6)
    for hy in (spy + 65, spy + sph - 65):
        ctx.arc(spx + 118, hy, 22, 0, math.pi * 2)
        ctx.set_source_rgb(0.88, 0.88, 0.88)
        ctx.fill_preserve()
        set_ink(ctx, 4.0)
        ctx.stroke()

    # Blue circle around strike plate
    if prog > 0.15:
        cprog = clamp((prog - 0.15) / 0.30, 0.0, 1.0)
        ctx.save()
        ctx.translate(spx + spw * 0.5, spy + sph * 0.5)
        ctx.arc(0, 0, 310, 0, math.pi * 2 * cprog)
        ctx.set_source_rgb(*hex_rgb("#223B78"))
        ctx.set_line_width(4.5)
        ctx.stroke()
        ctx.restore()
        ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(28)
        ctx.move_to(spx - 35, spy - 28)
        ctx.show_text("strike plate")

    # 1-inch screw on right
    sc_x, sc_y = cx + 865, cy + 495
    draw_ink_box(ctx, sc_x, sc_y - 22, 14, 44, "#D4C6A8", stroke_w=3.5)
    ctx.move_to(sc_x + 14, sc_y - 11)
    ctx.line_to(sc_x + 175, sc_y - 7)
    ctx.line_to(sc_x + 205, sc_y)
    ctx.line_to(sc_x + 175, sc_y + 7)
    ctx.line_to(sc_x + 14, sc_y + 11)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#D4C6A8"))
    ctx.fill_preserve()
    set_ink(ctx, 3.5)
    ctx.stroke()

    # Yellow ruler below screw
    if prog > 0.42:
        rx, ry, rw, rh = sc_x, sc_y + 85, 420, 75
        draw_ink_box(ctx, rx, ry, rw, rh, "#EDD868", stroke_w=3.5)
        for tick in range(17):
            tx = rx + tick * (rw / 16.0)
            th = 28 if tick % 8 == 0 else (18 if tick % 4 == 0 else 10)
            ctx.move_to(tx, ry)
            ctx.line_to(tx, ry + th)
            set_ink(ctx, 2.5)
            ctx.stroke()
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(24)
        ctx.move_to(rx + 8, ry + 58)
        ctx.show_text("0")
        ctx.move_to(rx + rw * 0.5 - 8, ry + 58)
        ctx.show_text("1")
        ctx.move_to(rx + rw - 22, ry + 58)
        ctx.show_text("2")

    # Red "1 IN  that's it?" bracket above screw
    if prog > 0.65:
        ctx.move_to(sc_x, sc_y - 45)
        ctx.line_to(sc_x, sc_y - 62)
        ctx.line_to(sc_x + 205, sc_y - 62)
        ctx.line_to(sc_x + 205, sc_y - 45)
        ctx.set_source_rgb(*hex_rgb("#D42620"))
        ctx.set_line_width(4.0)
        ctx.stroke()
        ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(52)
        ctx.move_to(sc_x + 48, sc_y - 82)
        ctx.show_text("1 IN")
        ctx.set_font_size(28)
        ctx.move_to(sc_x + 225, sc_y - 78)
        ctx.show_text("that's it?")
    ctx.restore()

def draw_screw_stud_inset(ctx, x, y, w, h, prog):
    """Inset card showing 3-inch screw biting deep through plate + frame into wood stud."""
    ctx.save()
    draw_ink_box(ctx, x, y, w, h, "#F6F3EB", stroke_w=4.0, shadow=True)

    px = x + 85
    py = y + 85
    ph = h - 135
    # Strike plate, frame, and wood stud blocks
    draw_ink_box(ctx, px, py, 16, ph, "#9EA4AA", stroke_w=3.5)
    draw_ink_box(ctx, px + 16, py, 145, ph, "#DEC09A", stroke_w=3.5)
    draw_ink_box(ctx, px + 165, py, 290, ph, "#C9A06C", stroke_w=3.5)

    ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.set_source_rgb(*hex_rgb("#162955"))
    ctx.move_to(px - 28, py - 18)
    ctx.show_text("plate")
    ctx.move_to(px + 55, py - 18)
    ctx.show_text("frame")
    ctx.set_source_rgb(*hex_rgb("#D42620"))
    ctx.move_to(px + 255, py - 18)
    ctx.show_text("wood stud")

    # Dashed ghost of old 1-inch screw at top
    ctx.save()
    ctx.set_dash([6.0, 5.0])
    ctx.rectangle(px - 10, py + 55, 95, 14)
    ctx.set_source_rgba(0.35, 0.35, 0.38, 0.7)
    ctx.set_line_width(2.5)
    ctx.stroke()
    ctx.restore()

    # Long 3-inch brass screw driving deep into stud
    sc_len = 335 * clamp(prog * 1.4, 0.2, 1.0)
    sy = py + ph * 0.65
    draw_ink_box(ctx, px - 14, sy - 20, 14, 40, "#D4AF37", stroke_w=3.0)
    ctx.move_to(px, sy - 9)
    ctx.line_to(px + sc_len - 22, sy - 7)
    ctx.line_to(px + sc_len, sy)
    ctx.line_to(px + sc_len - 22, sy + 7)
    ctx.line_to(px, sy + 9)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#D4AF37"))
    ctx.fill_preserve()
    set_ink(ctx, 3.0)
    ctx.stroke()
    # Thread hashes
    for tx in range(int(px + 12), int(px + sc_len - 24), 14):
        ctx.move_to(tx, sy - 8)
        ctx.line_to(tx + 5, sy + 8)
    ctx.stroke()

    if prog > 0.6:
        ctx.set_source_rgb(*hex_rgb("#D42620"))
        ctx.set_font_size(34)
        ctx.move_to(px + 140, py + ph + 38)
        ctx.show_text("3 IN")
    ctx.restore()

# ==============================================================================
# 4. CALORIE TUBE, RECEIPT, WATER CHARTS, FRIDGE & BACKPACK X-RAY
# ==============================================================================
def draw_calorie_tube_overlay(ctx, x, y, kcal_val, pouring_pb=False, prog=1.0):
    """Shots 34 & 35: Glass test-tube calorie meter & pouring peanut butter stream."""
    ctx.save()
    tx, ty, tw, th = x, y, 145, 340

    # Pouring peanut butter arc from jar on table (Shot 35)
    if pouring_pb:
        jx, jy = 860, 560
        # Jar of Peanut Butter on table
        draw_ink_box(ctx, jx - 65, jy - 65, 130, 140, "#C68642", stroke_w=4.0, r=14)
        draw_ink_box(ctx, jx - 60, jy - 30, 120, 68, "#F5F0DC", stroke_w=2.5)
        ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(18)
        ctx.set_source_rgb(*hex_rgb("#B52420"))
        ctx.move_to(jx - 44, jy - 4)
        ctx.show_text("PEANUT")
        ctx.set_source_rgb(0.1, 0.1, 0.1)
        ctx.move_to(jx - 42, jy + 18)
        ctx.show_text("BUTTER")
        # Red lid beside jar
        draw_ink_box(ctx, jx + 68, jy + 48, 115, 26, "#C92420", stroke_w=3.5, r=4)

        # Curved thick peanut-butter tube arcing from jar into calorie tube
        ctx.move_to(jx, jy - 55)
        ctx.curve_to(jx + 140, jy - 480, tx - 80, ty - 280, tx + tw * 0.5, ty + 20)
        ctx.set_source_rgb(*hex_rgb("#C68642"))
        ctx.set_line_width(58.0)
        ctx.stroke_preserve()
        set_ink(ctx, 5.5)
        ctx.stroke()

    # Glass test tube body (rounded U-bottom curving downward from 0 to pi)
    def _tube_path():
        ctx.new_path()
        ctx.move_to(tx, ty)
        ctx.line_to(tx + tw, ty)
        ctx.line_to(tx + tw, ty + th - tw * 0.5)
        ctx.arc(tx + tw * 0.5, ty + th - tw * 0.5, tw * 0.5, 0, math.pi)
        ctx.close_path()

    _tube_path()
    ctx.set_source_rgba(0.18, 0.20, 0.22, 0.72)
    ctx.fill()

    # Liquid fill inside tube (rising from bottom up)
    fill_frac = clamp(kcal_val / 2300.0, 0.0, 1.05)
    fill_h = th * fill_frac
    ctx.save()
    _tube_path()
    ctx.clip()
    ctx.rectangle(tx, ty + th - fill_h, tw, fill_h)
    ctx.set_source_rgb(*hex_rgb("#C68642"))
    ctx.fill()
    ctx.restore()

    _tube_path()
    set_ink(ctx, 5.5)
    ctx.stroke()

    # Top rim lip
    draw_ink_box(ctx, tx - 16, ty - 8, tw + 32, 14, "#2A2C30", stroke_w=4.0, r=4)

    # "1 DAY" marker line
    day_y = ty + th * 0.24
    ctx.move_to(tx - 24, day_y)
    ctx.line_to(tx + tw + 24, day_y)
    ctx.set_source_rgb(*hex_rgb("#1E3A78"))
    ctx.set_line_width(5.0)
    ctx.stroke()
    if pouring_pb:
        draw_taped_label(ctx, tx + tw + 75, day_y, "1 DAY", scale=0.72)

    # Glass cracks & overflow puddle when > 2400 kcal
    if kcal_val >= 2400:
        set_ink(ctx, 3.5)
        ctx.move_to(tx + 40, ty + 80)
        ctx.line_to(tx + 75, ty + 135)
        ctx.line_to(tx + 55, ty + 185)
        ctx.stroke()
        # Overflow puddle below tube
        ctx.save()
        ctx.translate(tx + tw * 0.5, ty + th + 35)
        ctx.scale(1.8, 0.32)
        ctx.arc(0, 0, 68, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#C68642"))
        ctx.fill_preserve()
        set_ink(ctx, 3.0)
        ctx.stroke()
        ctx.restore()

    # Labels
    ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(28)
    ctx.set_source_rgb(1, 1, 1)
    ctx.move_to(tx - 10, ty + th + 62)
    ctx.show_text("CALORIES")
    ctx.set_font_size(34)
    ctx.move_to(tx + 18, ty - 28)
    ctx.show_text(f"{int(kcal_val):,}")
    ctx.restore()

def draw_pantry_receipt(ctx, t, prog):
    """Shot 37: Thermal printer printing 'PANTRY MART' non-perishable food receipt."""
    ctx.save()
    rx, ry, rw = 590, 60, 740
    rh = 180 + 680 * clamp(prog * 1.25, 0.1, 1.0)

    # Thermal printer slot at top
    draw_ink_box(ctx, rx - 45, ry - 25, rw + 90, 68, "#2C3038", stroke_w=4.5, r=8, shadow=True)

    # White receipt paper with jagged bottom edge
    ctx.move_to(rx, ry + 20)
    ctx.line_to(rx + rw, ry + 20)
    ctx.line_to(rx + rw, ry + rh)
    for jx in range(int(rx + rw), int(rx), -28):
        ctx.line_to(jx - 14, ry + rh - 14)
        ctx.line_to(jx - 28, ry + rh)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#F7F5F0"))
    ctx.fill_preserve()
    set_ink(ctx, 3.5)
    ctx.stroke()

    ctx.select_font_face("Consolas", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(42)
    ctx.set_source_rgb(0.12, 0.12, 0.12)
    ctx.move_to(rx + 215, ry + 105)
    ctx.show_text("PANTRY MART")
    ctx.set_font_size(22)
    ctx.move_to(rx + 280, ry + 142)
    ctx.show_text("SAT 10:42 AM")

    rows = [
        ("PEANUT BUTTER x4", "11.96"),
        ("RICE 10 LB", "8.49"),
        ("BEANS x6", "5.94"),
        ("CANNED CHICKEN", "9.90"),
        ("OATS", "4.29"),
    ]
    ctx.set_font_size(32)
    for i, (item_lbl, price) in enumerate(rows):
        if prog > 0.12 + i * 0.13:
            iy = ry + 235 + i * 86
            ctx.set_source_rgb(0.12, 0.12, 0.12)
            ctx.move_to(rx + 55, iy)
            ctx.show_text(item_lbl)
            ctx.move_to(rx + rw - 155, iy)
            ctx.show_text(price)
            # Checkbox + red checkmark
            draw_ink_box(ctx, rx + rw - 215, iy - 28, 30, 30, None, stroke_w=2.5)
            ctx.move_to(rx + rw - 210, iy - 12)
            ctx.line_to(rx + rw - 198, iy - 2)
            ctx.line_to(rx + rw - 178, iy - 32)
            ctx.set_source_rgb(*hex_rgb("#D42620"))
            ctx.set_line_width(4.5)
            ctx.stroke()

    if prog > 0.80:
        ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(46)
        ctx.set_source_rgb(*hex_rgb("#D42620"))
        ctx.move_to(rx + 185, ry + rh - 55)
        ctx.show_text("No fridge needed!")
    ctx.restore()

def draw_water_stack_120_diagram(ctx, t, prog):
    """Shot 73: 30 jugs + 40 tub + 50 heater stacking into 120 gallons column."""
    ctx.save()
    draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#EAE3CE", stroke_w=0)
    for ly in range(60, HEIGHT, 52):
        ctx.move_to(0, ly)
        ctx.line_to(WIDTH, ly)
        ctx.set_source_rgba(0.65, 0.72, 0.78, 0.45)
        ctx.set_line_width(2.0)
        ctx.stroke()
    ctx.move_to(215, 0)
    ctx.line_to(215, HEIGHT)
    ctx.set_source_rgba(0.85, 0.35, 0.35, 0.55)
    ctx.stroke()

    base_y = 890
    ctx.move_to(280, base_y)
    ctx.line_to(1640, base_y)
    set_ink(ctx, 5.5)
    ctx.stroke()

    if prog < 0.55:
        # Three separate containers side-by-side: 30 jugs, 40 tub, 50 heater
        boxes = [
            (380, 190, "30", "jugs", 0.05),
            (810, 250, "40", "tub", 0.18),
            (1240, 315, "50", "heater", 0.32),
        ]
        for bx, bh, num, lbl, t0 in boxes:
            if prog > t0:
                bprog = clamp((prog - t0) / 0.16, 0.0, 1.0)
                cur_h = bh * bprog
                draw_ink_box(ctx, bx, base_y - bh, 270, bh, "#F5F0DC", stroke_w=4.5)
                draw_ink_box(ctx, bx + 6, base_y - cur_h, 258, cur_h, "#488EE0", stroke_w=0)
                ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(56)
                ctx.set_source_rgb(1, 1, 1)
                ctx.move_to(bx + 95, base_y - bh * 0.4)
                ctx.show_text(num)
                ctx.set_font_size(38)
                ctx.set_source_rgb(*hex_rgb("#162955"))
                ctx.move_to(bx + 95, base_y + 55)
                ctx.show_text(lbl)
    else:
        # Stacked single column: 30 + 40 + 50 = 120 gallons
        sprog = clamp((prog - 0.55) / 0.42, 0.0, 1.0)
        sx, sw = 790, 340
        draw_ink_box(ctx, sx, base_y - 680, sw, 680, "#F5F0DC", stroke_w=5.5)
        tiers = [(0, 180, "30", "#73B0F0"), (180, 230, "40", "#5598E6"), (410, 260, "50", "#3B7FD4")]
        for y_off, th, num, col in tiers:
            draw_ink_box(ctx, sx + 8, base_y - y_off - th, sw - 16, th, col, stroke_w=2.5)
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(58)
            ctx.set_source_rgb(1, 1, 1)
            ctx.move_to(sx + 130, base_y - y_off - th * 0.38)
            ctx.show_text(num)

        # Red curly brace on right + "120 gallons"
        if sprog > 0.25:
            bx = sx + sw + 42
            ctx.move_to(bx, base_y - 670)
            ctx.curve_to(bx + 45, base_y - 670, bx + 25, base_y - 340, bx + 68, base_y - 340)
            ctx.curve_to(bx + 25, base_y - 340, bx + 45, base_y - 10, bx, base_y - 10)
            ctx.set_source_rgb(*hex_rgb("#D42620"))
            ctx.set_line_width(7.0)
            ctx.stroke()

            ctx.set_font_size(110)
            txt = "120"[:max(1, int(3 * clamp((sprog - 0.3) * 2.2, 0, 1)))]
            ctx.move_to(bx + 98, base_y - 310)
            ctx.show_text(txt)
            ext = ctx.text_extents(txt)
            if sprog > 0.75:
                ctx.set_font_size(46)
                ctx.move_to(bx + 115, base_y - 235)
                ctx.show_text("gallons")
            else:
                draw_hand_with_pen(ctx, bx + 104 + ext.width, base_y - 315, pen_color="#D42620")
    ctx.restore()

def draw_backpack_xray(ctx, t, prog):
    """Shot 75: Top-down X-ray cutaway inside bug-out bag on wooden floor."""
    ctx.save()
    # Warm wood plank floor background
    draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#7C5836", stroke_w=0)
    for px in range(0, WIDTH, 240):
        ctx.move_to(px, 0)
        ctx.line_to(px, HEIGHT)
        set_ink(ctx, 3.0, 0.45)
        ctx.stroke()

    # Open green/black backpack outline
    bx, by, bw, bh = 440, 210, 1040, 680
    rounded_rect_path(ctx, bx, by, bw, bh, 85)
    ctx.set_source_rgb(*hex_rgb("#354839"))
    ctx.fill_preserve()
    set_ink(ctx, 6.0)
    ctx.stroke()

    rounded_rect_path(ctx, bx + 55, by + 65, bw - 110, bh - 130, 45)
    ctx.set_source_rgb(*hex_rgb("#111314"))
    ctx.fill_preserve()
    ctx.set_dash([14.0, 10.0])
    ctx.set_source_rgb(*hex_rgb("#D4BE5C"))
    ctx.set_line_width(5.0)
    ctx.stroke()
    ctx.set_dash([])

    # Items popping inside backpack
    if prog > 0.10:
        draw_water_jug(ctx, bx + 260, by + 280, scale=2.2)
        draw_water_jug(ctx, bx + 450, by + 295, scale=2.2)
        draw_taped_label(ctx, bx + 425, by - 12, "2 gal water", angle_deg=1.0, scale=0.88)
    if prog > 0.35:
        draw_ink_box(ctx, bx + 690, by + 150, 185, 115, "#EAE8E2", stroke_w=3.5, r=6)
        ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(28)
        ctx.set_source_rgb(*hex_rgb("#224B8A"))
        ctx.move_to(bx + 738, by + 218)
        ctx.show_text("RICE")
        draw_ink_box(ctx, bx + 895, by + 350, 120, 85, "#D8C292", stroke_w=3.5, r=14)
        draw_taped_label(ctx, bx + 865, by - 5, "3 days", angle_deg=-3.0, scale=0.85)
        draw_taped_label(ctx, bx + bw + 95, by + 275, "food", angle_deg=1.5, scale=0.85)
    if prog > 0.60:
        # Hand-crank orange radio
        draw_ink_box(ctx, bx + 215, by + 485, 165, 110, "#D97224", stroke_w=4.0, r=12)
        draw_taped_label(ctx, bx - 75, by + 595, "radio", angle_deg=-4.0, scale=0.85)
    if prog > 0.78:
        # Red first-aid kit
        draw_ink_box(ctx, bx + 620, by + 465, 175, 125, "#C92420", stroke_w=4.0, r=14)
        ctx.rectangle(bx + 695, by + 495, 24, 65)
        ctx.rectangle(bx + 675, by + 515, 64, 24)
        ctx.set_source_rgb(1, 1, 1)
        ctx.fill()
        draw_taped_label(ctx, bx + bw + 85, by + 595, "first aid", angle_deg=2.0, scale=0.85)
    ctx.restore()

def draw_calendar_6_summary(ctx, t, prog):
    """Shot 110: Tear-off calendar flipping 6..1 then lining up all 6 pages with red checkmarks."""
    ctx.save()
    ctx.set_source_rgb(0.08, 0.09, 0.14)
    ctx.paint()

    pages = [
        ("6", "DAYS LEFT", "water"),
        ("5", "DAYS LEFT", "food"),
        ("4", "DAYS LEFT", "door"),
        ("3", "DAYS LEFT", "cash"),
        ("2", "DAYS LEFT", "battery"),
        ("1", "DAY LEFT", "siren"),
    ]

    def _draw_mini_cal(cx, cy, s, num, sub, icon, checked=False):
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(s, s)
        w, h = 440, 560
        draw_ink_box(ctx, -w * 0.5, -h * 0.5, w, h, "#F5F0DC", stroke_w=4.5, r=8, shadow=True)
        draw_ink_box(ctx, -w * 0.5, -h * 0.5, w, 92, "#C92A24", stroke_w=4.5, r=4)
        for hx in (-120, 0, 120):
            ctx.arc(hx, -h * 0.5 + 46, 10, 0, math.pi * 2)
            ctx.set_source_rgb(0.15, 0.1, 0.1)
            ctx.fill()
        ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(165)
        ctx.set_source_rgb(*hex_rgb("#162955"))
        ext = ctx.text_extents(num)
        ctx.move_to(-ext.width * 0.5, 45)
        ctx.show_text(num)
        ctx.set_font_size(36)
        ext2 = ctx.text_extents(sub)
        ctx.move_to(-ext2.width * 0.5, 130)
        ctx.show_text(sub)
        draw_mini_icon(ctx, icon, 0, 205, size=56)

        if checked:
            ctx.move_to(-145, -35)
            ctx.line_to(-25, 95)
            ctx.line_to(175, -165)
            ctx.set_source_rgb(*hex_rgb("#D42620"))
            ctx.set_line_width(26.0)
            ctx.stroke()
        ctx.restore()

    if prog < 0.65:
        idx = min(5, int((prog / 0.65) * 6))
        num, sub, icon = pages[idx]
        _draw_mini_cal(WIDTH * 0.5, HEIGHT * 0.5, 1.08, num, sub, icon, checked=False)
    else:
        sprog = clamp((prog - 0.65) / 0.35, 0.0, 1.0)
        n_checked = int(sprog * 7)
        for i, (num, sub, icon) in enumerate(pages):
            px = 230 + i * 292
            py = HEIGHT * 0.52
            _draw_mini_cal(px, py, 0.56, num, sub, icon, checked=(i < n_checked))
    ctx.restore()

# ==============================================================================
# 5. ADDITIONAL CUTAWAYS & DIAGRAMS (Card Terminal, Cart, Fridge, Heater, Note, Hospital)
# ==============================================================================
def draw_card_terminal_split(ctx, t, prog):
    """Shot 21: Left payment terminal ('APPROVED ✅') + Right notebook ('28 + 2 = 30')."""
    ctx.save()
    ctx.set_source_rgb(0.28, 0.29, 0.27)
    ctx.paint()

    # Left: Card Payment Terminal + Blue CHAD Credit Card
    tx, ty, tw, th = 220, 290, 420, 620
    card_insert = smoothstep(0.0, 0.35, prog) * 75.0
    draw_ink_box(ctx, tx + 95, ty - 185 + card_insert, 230, 210, "#2458A6", stroke_w=4.0, r=14, shadow=True)
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(24)
    ctx.set_source_rgb(1, 1, 1)
    ctx.move_to(tx + 120, ty - 135 + card_insert)
    ctx.show_text("CHAD")
    ctx.set_font_size(16)
    ctx.move_to(tx + 120, ty - 95 + card_insert)
    ctx.show_text("•••• 2930")
    draw_ink_box(ctx, tx + 245, ty - 115 + card_insert, 48, 36, "#D4AF37", stroke_w=2.0, r=4)

    # Terminal body
    draw_ink_box(ctx, tx, ty, tw, th, "#3E424B", stroke_w=5.0, r=28, shadow=True)
    is_app = (prog > 0.35)
    scr_col = "#A8E6B4" if is_app else "#8EA892"
    draw_ink_box(ctx, tx + 42, ty + 48, tw - 84, 185, scr_col, stroke_w=3.5, r=12)
    ctx.set_source_rgb(*hex_rgb("#163820"))
    ctx.set_font_size(20)
    ctx.move_to(tx + 68, ty + 88)
    ctx.show_text("WATER 1 GAL x28")
    ctx.set_font_size(34)
    ctx.move_to(tx + 82, ty + 148)
    ctx.show_text("APPROVED" if is_app else "INSERT CARD")

    # PIN keypad 4x3
    keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "X", "<", "O"]
    for idx, k in enumerate(keys):
        r, c = idx // 3, idx % 3
        kx = tx + 52 + c * 110
        ky = ty + 275 + r * 78
        kcol = "#D93832" if k == "X" else ("#E8B828" if k == "<" else ("#38A852" if k == "O" else "#EAECEF"))
        draw_ink_box(ctx, kx, ky, 92, 60, kcol, stroke_w=3.0, r=8)

    # Right: Lined Notebook ("28 jugs + 2 at home = 30")
    draw_notebook_card(
        ctx, 920, 140, 860, 760,
        title="",
        items=[
            {"type": "text", "text": "  28 jugs", "size": 68, "color": "#162955"},
            {"type": "text", "text": "+  2 at home", "size": 68, "color": "#162955"},
            {"type": "text", "text": "------------", "size": 48, "color": "#162955"},
            {"type": "text", "text": "  30 gallons", "size": 72, "color": "#D42620"},
        ],
        progress=prog,
        angle_deg=2.2
    )
    ctx.restore()

def draw_cart_topdown(ctx, t, prog):
    """Shot 38: Top-down shopping cart basket with RICE, BEANS, OATS, CHICKEN + can opener."""
    ctx.save()
    draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#D6CEBE", stroke_w=0)

    bx, by, bw, bh = 510, 210, 900, 620
    draw_ink_box(ctx, bx, by, bw, bh, "#787E85", stroke_w=7.0, r=12, shadow=True)
    # Wire mesh grid
    for gx in range(bx + 45, bx + bw, 45):
        ctx.move_to(gx, by)
        ctx.line_to(gx, by + bh)
    for gy in range(by + 45, by + bh, 45):
        ctx.move_to(bx, gy)
        ctx.line_to(bx + bw, gy)
    ctx.set_source_rgba(0.25, 0.27, 0.30, 0.55)
    ctx.set_line_width(2.5)
    ctx.stroke()

    # Red cart handle bar at bottom
    draw_ink_box(ctx, bx + 40, by + bh + 32, bw - 80, 32, "#C92A24", stroke_w=4.0, r=10)

    # Food items inside cart
    draw_ink_box(ctx, bx + 55, by + 55, 340, 240, "#EAE8E2", stroke_w=4.0, r=8)
    ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(52)
    ctx.set_source_rgb(*hex_rgb("#224B8A"))
    ctx.move_to(bx + 145, by + 185)
    ctx.show_text("RICE")

    draw_ink_box(ctx, bx + 430, by + 55, 210, 145, "#8C5832", stroke_w=4.0, r=6)
    draw_ink_box(ctx, bx + 660, by + 75, 210, 145, "#8C5832", stroke_w=4.0, r=6)
    draw_ink_box(ctx, bx + 520, by + 355, 250, 165, "#C9B082", stroke_w=4.0, r=6)
    ctx.set_font_size(38)
    ctx.set_source_rgb(0.15, 0.12, 0.10)
    ctx.move_to(bx + 585, by + 450)
    ctx.show_text("OATS")

    # 4 Red peanut butter jar lids
    for jx, jy in [(bx + 125, by + 385), (bx + 245, by + 345), (bx + 135, by + 505), (bx + 255, by + 485)]:
        ctx.arc(jx, jy, 54, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#C92A24"))
        ctx.fill_preserve()
        set_ink(ctx, 4.0)
        ctx.stroke()

    # Manual Can Opener dropped on top by cartoon hand
    if prog > 0.25:
        drop_y = (1.0 - smoothstep(0.25, 0.55, prog)) * -180.0
        ctx.save()
        ctx.translate(bx + 390, by + 370 + drop_y)
        ctx.rotate(-0.2)
        draw_ink_box(ctx, -95, -18, 190, 36, "#C4C8CC", stroke_w=4.0, r=12, shadow=True)
        draw_ink_box(ctx, -10, -12, 120, 14, "#C92A24", stroke_w=3.0, r=6)
        ctx.restore()
    ctx.restore()

def draw_power_out_atms(ctx, t, prog):
    """Shot 39: Card reader + ASHFORD ATM losing power ('Power out? Cards & ATMs die.')."""
    ctx.save()
    ctx.set_source_rgb(0.08, 0.08, 0.10)
    ctx.paint()

    dead = (prog > 0.48)
    # Left Card Terminal
    draw_ink_box(ctx, 210, 360, 330, 520, "#3E424B", stroke_w=4.5, r=18)
    draw_ink_box(ctx, 238, 395, 274, 155, "#151618" if dead else "#72B87E", stroke_w=3.0, r=8)
    if dead:
        ctx.arc(375, 472, 42, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#D42620"))
        ctx.set_line_width(4.5)
        ctx.stroke()

    # Center ASHFORD ATM
    draw_ink_box(ctx, 635, 175, 465, 720, "#5C6068", stroke_w=5.0, r=8)
    draw_ink_box(ctx, 660, 200, 415, 75, "#264B36", stroke_w=3.5)
    ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(32)
    ctx.set_source_rgb(*hex_rgb("#E5D068"))
    ctx.move_to(765, 250)
    ctx.show_text("ASHFORD")
    draw_ink_box(ctx, 695, 305, 345, 205, "#151618" if dead else "#3A7BD5", stroke_w=3.5, r=6)
    if not dead:
        ctx.set_source_rgb(1, 1, 1)
        ctx.move_to(740, 420)
        ctx.show_text("WELCOME")
    else:
        ctx.arc(867, 407, 48, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#D42620"))
        ctx.set_line_width(5.0)
        ctx.stroke()

    # Right Notebook
    draw_notebook_card(
        ctx, 1280, 465, 575, 415,
        title="",
        items=[
            {"type": "text", "text": "Power out?", "size": 42, "color": "#D42620"},
            {"type": "text", "text": "Cards & ATMs", "size": 40, "color": "#162955"},
            {"type": "text", "text": "die.", "size": 40, "color": "#162955", "circle": True},
            {"type": "text", "text": "Keep small bills.", "size": 32, "color": "#162955"},
        ],
        progress=prog,
        angle_deg=3.0
    )
    ctx.restore()

def draw_fridge_4h_diagram(ctx, t, prog):
    """Shots 63 & 64: Unplugged refrigerator with 4-hour safe food pie-chart timer."""
    ctx.save()
    ctx.set_source_rgb(0.07, 0.08, 0.11)
    ctx.paint()

    fx, fy, fw, fh = 695, 195, 385, 685
    draw_ink_box(ctx, fx, fy, fw, 225, "#788594", stroke_w=5.0, r=14, shadow=True)
    draw_ink_box(ctx, fx, fy + 232, fw, 448, "#788594", stroke_w=5.0, r=14, shadow=True)
    # Handles
    draw_ink_box(ctx, fx + fw - 34, fy + 45, 14, 135, "#B0B8C2", stroke_w=3.0, r=6)
    draw_ink_box(ctx, fx + fw - 34, fy + 265, 14, 175, "#B0B8C2", stroke_w=3.0, r=6)

    # Wall outlet & unplugged cord with Red X
    draw_ink_box(ctx, fx + fw + 145, fy + fh - 155, 62, 95, "#DFDDD6", stroke_w=3.5, r=4)
    ctx.move_to(fx + fw + 15, fy + fh - 40)
    ctx.line_to(fx + fw + 85, fy + fh - 15)
    ctx.set_source_rgb(*hex_rgb("#D42620"))
    ctx.set_line_width(8.0)
    ctx.stroke()

    # Circular 4h pie-chart clock on lower fridge door
    cx, cy, rad = fx + fw * 0.5, fy + 465, 135
    ctx.arc(cx, cy, rad, 0, math.pi * 2)
    ctx.set_source_rgb(*hex_rgb("#DFD9C8"))
    ctx.fill_preserve()
    set_ink(ctx, 5.0)
    ctx.stroke()

    # Blue 4h wedge
    ctx.move_to(cx, cy)
    ctx.arc(cx, cy, rad - 8, -math.pi * 0.5, -math.pi * 0.5 + math.pi * 0.65 * clamp(prog * 1.4, 0.2, 1.0))
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#3B82C8"))
    ctx.fill_preserve()
    set_ink(ctx, 3.5)
    ctx.stroke()

    if prog > 0.45:
        ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(58)
        ctx.set_source_rgb(*hex_rgb("#181615"))
        ctx.move_to(cx - 58, cy + 32)
        ctx.show_text("4h")
    ctx.restore()

def draw_water_heater_50gal_diagram(ctx, t, prog):
    """Shot 69: Lined paper diagram of 50 GAL water heater tank ('sealed + clean')."""
    ctx.save()
    draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#EAE3CE", stroke_w=0)
    for ly in range(60, HEIGHT, 52):
        ctx.move_to(0, ly)
        ctx.line_to(WIDTH, ly)
        ctx.set_source_rgba(0.65, 0.72, 0.78, 0.45)
        ctx.set_line_width(2.0)
        ctx.stroke()

    tx, ty, tw, th = 760, 175, 360, 680
    # Top cold & hot pipes
    draw_ink_box(ctx, tx + 65, 0, 26, ty + 10, "#4B86C8", stroke_w=4.0)
    draw_ink_box(ctx, tx + tw - 95, 0, 26, ty + 10, "#C95B5B", stroke_w=4.0)

    # Tank cylinder
    draw_ink_box(ctx, tx, ty, tw, th, "#F5F2EA", stroke_w=5.5, r=28, shadow=True)
    fill_h = (th - 45) * clamp(prog * 1.35, 0.35, 1.0)
    draw_ink_box(ctx, tx + 8, ty + th - fill_h - 8, tw - 16, fill_h, "#488EE0", stroke_w=0, r=18)

    # Red shutoff valve X on top-left cold pipe
    ctx.arc(tx + 78, ty - 42, 26, 0, math.pi * 2)
    ctx.set_source_rgb(1, 1, 1)
    ctx.fill_preserve()
    ctx.set_source_rgb(*hex_rgb("#D42620"))
    ctx.set_line_width(5.0)
    ctx.stroke()
    ctx.move_to(tx + 62, ty - 58)
    ctx.line_to(tx + 94, ty - 26)
    ctx.move_to(tx + 94, ty - 58)
    ctx.line_to(tx + 62, ty - 26)
    ctx.stroke()

    # Left label: "50 GAL"
    ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(64)
    ctx.set_source_rgb(*hex_rgb("#2258A8"))
    ctx.move_to(380, 535)
    ctx.show_text("50 GAL")

    # Right padlock: "sealed + clean"
    if prog > 0.45:
        lx, ly = 1320, 480
        ctx.arc(lx + 55, ly, 36, math.pi, 0)
        set_ink(ctx, 8.0)
        ctx.stroke()
        draw_ink_box(ctx, lx, ly, 110, 95, "#E8B828", stroke_w=4.5, r=12, shadow=True)
        ctx.arc(lx + 55, ly + 42, 10, 0, math.pi * 2)
        ctx.set_source_rgb(0.15, 0.12, 0.10)
        ctx.fill()
        ctx.set_font_size(34)
        ctx.set_source_rgb(*hex_rgb("#162955"))
        ctx.move_to(lx - 10, ly + 150)
        ctx.show_text("sealed")
        ctx.move_to(lx - 15, ly + 195)
        ctx.show_text("+ clean")
    ctx.restore()

def draw_folded_note_doormat(ctx, t, prog):
    """Shot 83: Unfolded lined notebook warning note to the neighbor on the brown doormat."""
    ctx.save()
    draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#6A4E35", stroke_w=0)
    draw_ink_box(ctx, 110, 65, WIDTH - 220, HEIGHT - 130, "#8C745A", stroke_w=12.0, r=18)

    nx, ny, nw, nh = 590, 48, 740, 975
    draw_ink_box(ctx, nx, ny, nw, nh, "#F4F1EA", stroke_w=5.5, shadow=True)
    # Fold creases (crosshair)
    ctx.move_to(nx + nw * 0.5, ny + 25)
    ctx.line_to(nx + nw * 0.5, ny + nh - 25)
    ctx.move_to(nx + 25, ny + nh * 0.48)
    ctx.line_to(nx + nw - 25, ny + nh * 0.48)
    ctx.set_source_rgba(0.25, 0.23, 0.22, 0.55)
    ctx.set_line_width(4.0)
    ctx.stroke()

    lines = [
        "STAY INSIDE",
        "THURSDAY NIGHT.",
        "LOCK YOUR DOOR.",
        "DON'T OPEN IT",
        "FOR ANYONE."
    ]
    ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(52)
    for i, ln in enumerate(lines):
        if prog > i * 0.16:
            ly = ny + 245 + i * 95
            ctx.set_source_rgb(*hex_rgb("#162955"))
            ctx.move_to(nx + 105, ly)
            ctx.show_text(ln)
            if i == 1:
                ctx.move_to(nx + 105, ly + 14)
                ctx.line_to(nx + 585, ly + 8)
                ctx.set_source_rgb(*hex_rgb("#D42620"))
                ctx.set_line_width(6.0)
                ctx.stroke()
    ctx.restore()

def draw_hospital_phone_video(ctx, t, prog, show_hands=False):
    """Shot 59: Shaky vertical phone footage of the hospital hallway zombie patient."""
    ctx.save()
    ctx.set_source_rgb(0.18, 0.19, 0.18)
    ctx.paint()

    # Vertical 9:16 video frame in center
    vx, vy, vw, vh = 655, 0, 610, 1080
    if show_hands:
        vx, vy, vw, vh = 665, 55, 590, 960
        draw_ink_box(ctx, vx - 22, vy - 24, vw + 44, vh + 48, "#1D1E22", stroke_w=5.0, r=38, shadow=True)

    ctx.save()
    ctx.rectangle(vx, vy, vw, vh)
    ctx.clip()

    # Sickly green-grey hospital corridor perspective
    draw_ink_box(ctx, vx, vy, vw, vh, "#76847A", stroke_w=0)
    # Ceiling & floor perspective lines
    ctx.move_to(vx, vy)
    ctx.line_to(vx + vw * 0.35, vy + vh * 0.25)
    ctx.line_to(vx + vw * 0.65, vy + vh * 0.25)
    ctx.line_to(vx + vw, vy)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#5A685E"))
    ctx.fill_preserve()
    set_ink(ctx, 3.0)
    ctx.stroke()

    # Fluorescent ceiling light panels
    for li in range(3):
        lw = 240 - li * 48
        lh = 32 - li * 6
        draw_ink_box(ctx, vx + (vw - lw) * 0.5, vy + 38 + li * 68, lw, lh, "#E4EFE8", stroke_w=2.0)

    if prog < 0.52:
        # Wide corridor: patient in paper gown standing still in distance
        px, py = vx + vw * 0.5, vy + vh * 0.54
        draw_ink_box(ctx, px - 36, py - 85, 72, 145, "#DCE2DE", stroke_w=3.0, r=8)
        ctx.arc(px, py - 110, 24, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#8C948E"))
        ctx.fill_preserve()
        set_ink(ctx, 3.0)
        ctx.stroke()
    elif prog < 0.78:
        # Nurse touches patient's shoulder; he turns his head showing glowing white eye
        px, py = vx + vw * 0.55, vy + vh * 0.58
        draw_ink_box(ctx, px - 85, py - 180, 170, 420, "#DCE2DE", stroke_w=4.0, r=16)
        ctx.arc(px, py - 240, 62, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#8C948E"))
        ctx.fill_preserve()
        set_ink(ctx, 4.0)
        ctx.stroke()
        if prog > 0.65:
            # Glowing white zombie eye & snarling mouth
            ctx.arc(px + 28, py - 248, 12, 0, math.pi * 2)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill()
        # Nurse in blue scrubs on left reaching out
        draw_ink_box(ctx, vx, py - 160, 165, 420, "#4B869E", stroke_w=4.0)
        ctx.move_to(vx + 145, py - 120)
        ctx.line_to(px - 45, py - 165)
        ctx.set_source_rgb(*hex_rgb("#D8B094"))
        ctx.set_line_width(28.0)
        ctx.stroke()
    else:
        # Lunge & bite closeup (like frame_285.jpg!)
        px, py = vx + vw * 0.48, vy + vh * 0.46
        draw_ink_box(ctx, vx + 30, py + 40, vw - 60, 520, "#DCE2DE", stroke_w=4.0, r=24)
        # Zombie head lunging forward with wide gaping mouth & glowing eyes
        ctx.arc(px, py - 55, 118, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#969E98"))
        ctx.fill_preserve()
        set_ink(ctx, 4.5)
        ctx.stroke()
        for ex in (px - 38, px + 38):
            ctx.arc(ex, py - 75, 18, 0, math.pi * 2)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill()
        rounded_rect_path(ctx, px - 42, py - 18, 84, 78, 16)
        ctx.set_source_rgb(*hex_rgb("#421414"))
        ctx.fill_preserve()
        set_ink(ctx, 3.5)
        ctx.stroke()
        # Nurse's forearm grabbed across frame
        ctx.move_to(vx + 80, vy + vh)
        ctx.line_to(vx + vw - 95, py - 65)
        ctx.set_source_rgb(*hex_rgb("#E2B89A"))
        ctx.set_line_width(78.0)
        ctx.stroke_preserve()
        set_ink(ctx, 4.0)
        ctx.stroke()

    # Social video UI overlay (right side icons + bottom red scrub bar)
    for ii in range(3):
        ctx.arc(vx + vw - 48, vy + vh - 380 + ii * 82, 26, 0, math.pi * 2)
        ctx.set_source_rgba(0, 0, 0, 0.45)
        ctx.fill_preserve()
        ctx.set_source_rgb(1, 1, 1)
        ctx.set_line_width(2.5)
        ctx.stroke()
    ctx.rectangle(vx, vy + vh - 12, vw * prog, 8)
    ctx.set_source_rgb(*hex_rgb("#E51C1C"))
    ctx.fill()
    ctx.restore()

    if show_hands:
        for side in (-1, 1):
            hx = vx if side == -1 else vx + vw
            rounded_rect_path(ctx, hx - 70, vy + vh * 0.65, 140, 88, 38)
            ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
            ctx.fill_preserve()
            set_ink(ctx, 4.5)
            ctx.stroke()
    ctx.restore()
