import math
import cairo
from engine.primitives import (
    WIDTH, HEIGHT, hex_rgb, hex_rgba, set_ink, rounded_rect_path,
    draw_ink_box, draw_scotch_tape, draw_slanted_stamp_banner,
    draw_speech_bubble, draw_digital_clock, draw_ecg_waveform,
    draw_sound_wave_arcs, draw_fire_plume, clamp, smoothstep
)
from engine.characters import (
    draw_chad, draw_neighbor, draw_water_jug,
    draw_fire_extinguisher_prop, draw_hand_with_pen
)
from engine.overlays import draw_notebook_card, draw_sticky_note_pad, draw_taped_label
from engine.diagrams import draw_calorie_tube_overlay, draw_screw_stud_inset

# ==============================================================================
# CACHED BACKGROUND SURFACES (Rendered once per worker for >300 FPS speed)
# ==============================================================================
_BG_CACHE = {}

def _get_cached_bg(key, builder_fn):
    if key not in _BG_CACHE:
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
        c = cairo.Context(surf)
        builder_fn(c)
        _BG_CACHE[key] = surf
    return _BG_CACHE[key]

# ==============================================================================
# 1. BIRCH STREET BROWNSTONE EXTERIOR (Day, Night, Red Alerts, Raging Fire)
# ==============================================================================
def _build_brownstone_base(ctx, is_night=False):
    # Sky gradient
    pat = cairo.LinearGradient(0, 0, 0, HEIGHT)
    if is_night:
        pat.add_color_stop_rgb(0.0, *hex_rgb("#141923"))
        pat.add_color_stop_rgb(0.7, *hex_rgb("#232936"))
    else:
        pat.add_color_stop_rgb(0.0, *hex_rgb("#A8BCC8"))
        pat.add_color_stop_rgb(0.7, *hex_rgb("#D5DFE5"))
    ctx.set_source(pat)
    ctx.paint()

    mul = 0.42 if is_night else 1.0
    def _col(h):
        r, g, b = hex_rgb(h)
        return (r * mul, g * mul, b * mul)

    # Sidewalk & Asphalt Street at bottom
    ctx.rectangle(0, 815, WIDTH, 145)
    ctx.set_source_rgb(*_col("#C5BEB5"))
    ctx.fill_preserve()
    set_ink(ctx, 3.5)
    ctx.stroke()
    ctx.rectangle(0, 960, WIDTH, 120)
    ctx.set_source_rgb(*_col("#6E7075"))
    ctx.fill()

    # Left Brownstone Building (#A87658) + Rooftop Water Tower
    draw_ink_box(ctx, 185, 175, 365, 650, "#A87658" if not is_night else "#4A3428", stroke_w=4.5)
    draw_ink_box(ctx, 0, 115, 185, 710, "#9E5B48" if not is_night else "#422720", stroke_w=4.5)
    # Water tower on roof
    draw_ink_box(ctx, 425, 55, 86, 85, "#8C6D53" if not is_night else "#3D3025", stroke_w=3.5)
    ctx.move_to(418, 55)
    ctx.line_to(468, 28)
    ctx.line_to(518, 55)
    ctx.close_path()
    ctx.fill_preserve()
    set_ink(ctx, 3.5)
    ctx.stroke()

    # Center 4-Story Red-Brick Apartment Building (#C45B46)
    bx, by, bw, bh = 550, 145, 880, 680
    draw_ink_box(ctx, bx, by, bw, bh, "#C45B46" if not is_night else "#562820", stroke_w=4.5)
    # Top cornice
    draw_ink_box(ctx, bx - 10, by - 16, bw + 20, 22, "#D8CFC4" if not is_night else "#5E5A55", stroke_w=3.5)

    # Right 2-Story Tan House/Shop (#C8B08A) with Striped Awning
    draw_ink_box(ctx, 1430, 185, 420, 640, "#8E493A" if not is_night else "#3E201A", stroke_w=4.5)
    ctx.move_to(1430, 395)
    ctx.line_to(1600, 200)
    ctx.line_to(1775, 395)
    ctx.close_path()
    ctx.set_source_rgb(*_col("#D8C5A2"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()
    draw_ink_box(ctx, 1430, 395, 345, 430, "#C8B08A" if not is_night else "#584D3D", stroke_w=4.0)

    # Center Building Windows (4 floors x 6 columns)
    for fl in range(4):
        wy = 275 + fl * 142
        for col in range(6):
            if fl == 3 and col == 3:
                continue  # Front entrance door slot
            wx = bx + 62 + col * 138
            draw_ink_box(ctx, wx, wy, 58, 92, "#7C8C96" if not is_night else "#222830", stroke_w=3.5)
            draw_ink_box(ctx, wx - 6, wy - 10, 70, 10, "#B89A82" if not is_night else "#4A3E35", stroke_w=2.5)

    # Center Front Stoop & Door
    draw_ink_box(ctx, bx + 385, 585, 105, 185, "#4E382E", stroke_w=4.0)
    for st in range(5):
        draw_ink_box(ctx, bx + 365 - st * 4, 770 + st * 14, 145 + st * 8, 14, "#B8B0A4" if not is_night else "#504C48", stroke_w=2.5)

    # Fire escape balconies & diagonal ladders on right side of center building
    set_ink(ctx, 3.5)
    for fl in range(3):
        fey = 235 + fl * 142
        ctx.rectangle(bx + 645, fey, 225, 48)
        ctx.stroke()
        ctx.move_to(bx + 810, fey + 48)
        ctx.line_to(bx + 735, fey + 142)
        ctx.stroke()

    # Neighbor's fenced tomato garden on left of stoop
    gx, gy, gw, gh = 455, 765, 435, 115
    for tx in range(gx + 35, gx + gw - 25, 52):
        ctx.arc(tx, gy + 15, 32, 0, math.pi * 2)
        ctx.set_source_rgb(*_col("#6B8E4E"))
        ctx.fill_preserve()
        set_ink(ctx, 2.5)
        ctx.stroke()
        ctx.arc(tx - 8, gy + 10, 6, 0, math.pi * 2)
        ctx.arc(tx + 10, gy + 22, 6, 0, math.pi * 2)
        ctx.set_source_rgb(*_col("#D4382C"))
        ctx.fill()
    # Iron fence
    set_ink(ctx, 3.5)
    ctx.rectangle(gx, gy + 15, gw, gh - 15)
    for fx in range(gx, gx + gw, 18):
        ctx.move_to(fx, gy + 10)
        ctx.line_to(fx, gy + gh)
    ctx.stroke()

    # Parked cars along bottom curb
    for cx_car, ccol in [(45, "#5C6B5E"), (285, "#5A6578"), (1025, "#9E8D68"), (1485, "#8C8E92")]:
        ctx.move_to(cx_car, 985)
        ctx.line_to(cx_car + 45, 920)
        ctx.line_to(cx_car + 215, 920)
        ctx.line_to(cx_car + 285, 985)
        ctx.line_to(cx_car + 320, 1080)
        ctx.line_to(cx_car - 20, 1080)
        ctx.close_path()
        ctx.set_source_rgb(*_col(ccol))
        ctx.fill_preserve()
        set_ink(ctx, 4.0)
        ctx.stroke()

def draw_env_brownstone_exterior(ctx, t, mode="day", prog=0.0):
    is_night = mode in ("night_title", "night_target_window", "night_all_red_alerts", "night_fire")
    surf = _get_cached_bg("brownstone_night" if is_night else "brownstone_day",
                          lambda c: _build_brownstone_base(c, is_night=is_night))
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint()

    bx = 550
    if mode == "day_to_night_beacon" and prog > 0.45:
        n_surf = _get_cached_bg("brownstone_night", lambda c: _build_brownstone_base(c, is_night=True))
        ctx.save()
        ctx.set_source_surface(n_surf, 0, 0)
        ctx.paint_with_alpha(clamp((prog - 0.45) / 0.35, 0.0, 1.0))
        ctx.restore()
        # Single brightly lit 3rd floor window
        wx, wy = bx + 62 + 2 * 138, 275 + 1 * 142
        draw_ink_box(ctx, wx, wy, 58, 92, "#FFF3C4", stroke_w=3.5)
        pat = cairo.RadialGradient(wx + 29, wy + 46, 10, wx + 29, wy + 46, 145)
        pat.add_color_stop_rgba(0.0, 1.0, 0.85, 0.45, 0.75)
        pat.add_color_stop_rgba(1.0, 1.0, 0.85, 0.45, 0.0)
        ctx.set_source(pat)
        ctx.paint()

    elif mode == "night_title":
        # Pulsing red 3rd-floor window + FRIDAY / 3:12 AM title
        wx, wy = bx + 62 + 1 * 138, 275 + 1 * 142
        draw_ink_box(ctx, wx, wy, 58, 92, "#B82828", stroke_w=3.0)
        if prog > 0.25:
            ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(145)
            ctx.set_source_rgb(1, 1, 1)
            ext = ctx.text_extents("FRIDAY")
            ctx.move_to((WIDTH - ext.width) * 0.5, 515)
            ctx.show_text("FRIDAY")
        if prog > 0.52:
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(64)
            ctx.set_source_rgb(*hex_rgb("#F7D436"))
            ctx.move_to(835, 615)
            ctx.show_text("3:12 AM")

    elif mode == "floor_numbers":
        # Chad standing at bottom of steps with 2 water jugs + 1, 2, 3 you + NO ELEVATOR
        draw_chad(ctx, bx + 435, 815, scale=0.46, facing="back", pose="idle", prop="jugs_2", t=t)
        floors = [(1, 715, 0.15), (2, 573, 0.35), (3, 431, 0.55)]
        for fnum, fy, t0 in floors:
            if prog > t0:
                fx = bx + 535 if fnum < 3 else bx + 365
                ctx.arc(fx, fy, 36, 0, math.pi * 2)
                ctx.set_source_rgb(*hex_rgb("#F5C838"))
                ctx.fill_preserve()
                set_ink(ctx, 3.5)
                ctx.stroke()
                ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(42)
                ctx.set_source_rgb(*hex_rgb("#C92420"))
                ctx.move_to(fx - 14, fy + 15)
                ctx.show_text(str(fnum))
                if fnum == 3:
                    ctx.move_to(fx + 52, fy + 12)
                    ctx.show_text("you")
                    # Red circle around 3rd-floor left window
                    ctx.arc(bx + 62 + 138 + 29, 275 + 142 + 46, 62, 0, math.pi * 2)
                    ctx.set_line_width(5.5)
                    ctx.stroke()
        if prog > 0.72:
            draw_taped_label(ctx, bx + 685, 835, "NO ELEVATOR", angle_deg=-3.5, scale=0.82)

    elif mode == "night_target_window":
        wx, wy = bx + 62 + 2 * 138, 275 + 1 * 142
        draw_ink_box(ctx, wx, wy, 58, 92, "#F5D468", stroke_w=3.5)
        ctx.save()
        ctx.set_dash([14.0, 12.0])
        for ri in range(3):
            rad = 95 + ri * 85 + (t * 45.0) % 85
            ctx.arc(wx + 29, wy + 46, rad, 0, math.pi * 2)
            ctx.set_source_rgba(0.98, 0.85, 0.45, max(0, 0.65 - rad / 420.0))
            ctx.set_line_width(4.0)
            ctx.stroke()
        ctx.restore()

    elif mode == "night_all_red_alerts":
        pulse = 0.55 + 0.45 * math.sin(t * 14.0)
        for fl in range(4):
            wy = 275 + fl * 142
            for col in range(6):
                if fl == 3 and col == 3:
                    continue
                wx = bx + 62 + col * 138
                draw_ink_box(ctx, wx, wy, 58, 92, "#E52222", stroke_w=3.0, alpha=pulse)

    elif mode == "night_fire":
        # Raging flames & thick dark smoke pouring out of all 6 top-floor windows
        for col in range(6):
            wx = bx + 62 + col * 138
            wy = 275
            draw_ink_box(ctx, wx, wy, 58, 92, "#FF8C24", stroke_w=3.0)
            draw_fire_plume(ctx, wx - 12, wy + 45, 82, 135, t, seed=col * 3)
            # Rising smoke puffs
            for sp in range(4):
                sy = wy - 55 - sp * 55 - ((t * 40.0 + col * 19) % 55)
                sx = wx + 29 + sp * 28 + math.sin(t * 3 + sp) * 14
                ctx.arc(sx, sy, 38 + sp * 14, 0, math.pi * 2)
                ctx.set_source_rgba(0.18, 0.17, 0.19, 0.55 - sp * 0.1)
                ctx.fill()

# ==============================================================================
# 2. APOCALYPSE RUINED BIRCH STREET (Shot 2: Zombie Horde + Burning Skyline)
# ==============================================================================
def draw_env_apocalypse_street(ctx, t, prog=0.0):
    ctx.save()
    # Dark smoky orange-red sky gradient
    pat = cairo.LinearGradient(0, 0, 0, HEIGHT)
    pat.add_color_stop_rgb(0.0, *hex_rgb("#11131A"))
    pat.add_color_stop_rgb(0.48, *hex_rgb("#5E2216"))
    pat.add_color_stop_rgb(1.0, *hex_rgb("#241F21"))
    ctx.set_source(pat)
    ctx.paint()

    # Distant burning skyline silhouettes + fire plumes
    for bx_s, bw_s, bh_s in [(620, 95, 220), (740, 110, 290), (880, 85, 240), (990, 125, 340), (1140, 90, 260)]:
        draw_ink_box(ctx, bx_s, 600 - bh_s, bw_s, bh_s, "#2B1814", stroke_w=3.0)
        draw_fire_plume(ctx, bx_s + 10, 600 - bh_s + 25, bw_s - 20, 95, t, seed=bx_s)

    # Perspective street & flanking rowhouses converging to (960, 560)
    ctx.move_to(120, HEIGHT)
    ctx.line_to(780, 580)
    ctx.line_to(1140, 580)
    ctx.line_to(1800, HEIGHT)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#2C292B"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()

    # Center lane line
    ctx.move_to(960, 580)
    ctx.line_to(960, HEIGHT)
    ctx.set_source_rgba(0.65, 0.62, 0.58, 0.65)
    ctx.set_line_width(8.0)
    ctx.stroke()

    # Left & Right perspective buildings
    for side in (-1, 1):
        bx0 = 0 if side == -1 else WIDTH
        bx1 = 740 if side == -1 else 1180
        ctx.move_to(bx0, 140)
        ctx.line_to(bx1, 430)
        ctx.line_to(bx1, 590)
        ctx.line_to(bx0, 740)
        ctx.close_path()
        ctx.set_source_rgb(*hex_rgb("#3D2822" if side == -1 else "#4A3A32"))
        ctx.fill_preserve()
        set_ink(ctx, 4.0)
        ctx.stroke()

    # Shambling Zombie Horde in street center
    zombies = [
        (865, 620, 0.42, "worker"), (965, 635, 0.45, "nurse"), (1055, 615, 0.40, "gown"),
        (725, 675, 0.56, "nurse"), (1145, 685, 0.58, "gown"), (1275, 670, 0.54, "nurse"),
        (1415, 735, 0.72, "worker"), (465, 815, 0.86, "nurse")
    ]
    for zx, zy, zs, ztype in zombies:
        shamble_y = zy + math.sin(t * 4.5 + zx) * 4.0
        ctx.save()
        ctx.translate(zx, shamble_y)
        ctx.scale(zs, zs)
        # Legs
        set_ink(ctx, 5.0)
        ctx.move_to(-12, 10)
        ctx.line_to(-16, 125)
        ctx.move_to(12, 10)
        ctx.line_to(16, 125)
        ctx.stroke()
        # Torso
        tcol = "#C8B84A" if ztype == "worker" else "#C5BEBA"
        draw_ink_box(ctx, -28, -75, 56, 90, tcol, stroke_w=3.5, r=10)
        # Head (tilted grey-green skull)
        ctx.rotate(0.18 if zx % 2 == 0 else -0.18)
        ctx.arc(0, -115, 38, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#889288"))
        ctx.fill_preserve()
        set_ink(ctx, 3.5)
        ctx.stroke()
        for ex in (-14, 14):
            ctx.arc(ex, -118, 8, 0, math.pi * 2)
            ctx.set_source_rgb(0.95, 0.95, 0.9)
            ctx.fill()
        ctx.restore()

    # Chad in foreground left (turns around in shock, then walks off-screen left)
    mel_x = 670 - clamp((prog - 0.52) / 0.35, 0.0, 1.0) * 850
    mel_face = "back" if prog < 0.22 else "left"
    mel_pose = "walk" if prog > 0.52 else "idle"
    if mel_x > -180:
        draw_chad(ctx, mel_x, 765, scale=1.65, facing=mel_face, pose=mel_pose,
                    expression="grimace_teeth", t=t)

    # Top-left slanted stamp banner: "6 DAYS FROM NOW"
    draw_slanted_stamp_banner(ctx, "6 DAYS FROM NOW", x=110, y=85, angle_deg=-2.2)
    ctx.restore()

# ==============================================================================
# 3. PROTAGONIST'S BEDROOM (Night, Alarm Wakeup, ECG, Sunrise Cardboard)
# ==============================================================================
def _build_bedroom_base(ctx):
    # Dark blue-grey night bedroom walls & floor
    draw_ink_box(ctx, 0, 0, WIDTH, 815, "#1E242E", stroke_w=0)
    draw_ink_box(ctx, 0, 815, WIDTH, 265, "#262322", stroke_w=4.0)

    # Window on top right overlooking dark city buildings
    wx, wy, ww, wh = 965, 0, 745, 485
    draw_ink_box(ctx, wx, wy, ww, wh, "#172030", stroke_w=6.0)
    # Distant dark buildings with tiny yellow lit windows
    for bx_c, bw_c, bh_c in [(1020, 130, 240), (1180, 110, 190), (1380, 150, 280), (1560, 120, 220)]:
        draw_ink_box(ctx, bx_c, wy + wh - bh_c, bw_c, bh_c, "#101622", stroke_w=2.5)
        draw_ink_box(ctx, bx_c + 28, wy + wh - bh_c + 35, 18, 24, "#C8B268", stroke_w=0)
    # Window panes & curtains
    ctx.move_to(wx + ww * 0.5, wy)
    ctx.line_to(wx + ww * 0.5, wy + wh)
    ctx.move_to(wx, wy + wh * 0.5)
    ctx.line_to(wx + ww, wy + wh * 0.5)
    set_ink(ctx, 5.0)
    ctx.stroke()
    draw_ink_box(ctx, wx - 55, 0, 95, wh + 35, "#283242", stroke_w=4.0)
    draw_ink_box(ctx, wx + ww - 40, 0, 95, wh + 35, "#283242", stroke_w=4.0)

    # Wooden Nightstand in center
    nx, ny, nw, nh = 1055, 515, 365, 365
    draw_ink_box(ctx, nx, ny, nw, nh, "#4E3A2A", stroke_w=4.5, shadow=True)
    draw_ink_box(ctx, nx + 35, ny + 45, nw - 70, 115, "#423022", stroke_w=3.5)
    ctx.arc(nx + nw * 0.5, ny + 102, 12, 0, math.pi * 2)
    ctx.stroke()

    # Gooseneck Desk Lamp on nightstand
    ctx.save()
    ctx.translate(nx + 255, ny + 18)
    ctx.scale(1.8, 0.45)
    ctx.arc(0, 0, 38, 0, math.pi * 2)
    ctx.set_source_rgb(*hex_rgb("#5A544C"))
    ctx.fill_preserve()
    set_ink(ctx, 3.5)
    ctx.stroke()
    ctx.restore()
    ctx.move_to(nx + 265, ny + 12)
    ctx.curve_to(nx + 285, ny - 155, nx + 245, ny - 210, nx + 195, ny - 165)
    set_ink(ctx, 9.0)
    ctx.stroke()
    # Lamp shade cone
    ctx.move_to(nx + 195, ny - 165)
    ctx.line_to(nx + 135, ny - 115)
    ctx.line_to(nx + 185, ny - 75)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#686056"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()

    # Wooden Bed on left
    draw_ink_box(ctx, 510, 315, 510, 265, "#4E3A2A", stroke_w=5.0)
    # Pillow
    rounded_rect_path(ctx, 575, 465, 265, 95, 28)
    ctx.set_source_rgb(*hex_rgb("#4A4C54"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()

def draw_env_bedroom(ctx, t, mode="sleep", clock_str="3:00", prog=0.0):
    if mode == "closeup_wake":
        # Medium closeup of nightstand + Chad popping head above blanket (Shot 4)
        draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#321A18", stroke_w=0)
        draw_ink_box(ctx, 0, 195, 835, 420, "#5E3228", stroke_w=5.5)
        # Nightstand & vibrating phone
        nx, ny = 735, 515
        draw_ink_box(ctx, nx, ny, 580, 565, "#683628", stroke_w=5.5)
        draw_ink_box(ctx, nx + 65, ny + 120, 440, 185, "#582C20", stroke_w=4.0)

        # Vibrating phone on nightstand pulsing red light
        vib_x = math.sin(t * 55.0) * 6.0
        vib_y = math.cos(t * 62.0) * 4.0
        ctx.save()
        ctx.translate(nx + 195 + vib_x, ny + 25 + vib_y)
        ctx.rotate(-0.35)
        draw_ink_box(ctx, -65, -35, 130, 70, "#C92420", stroke_w=4.0, r=10, shadow=True)
        ctx.restore()

        # Chad's shocked head peeking over purple blanket in bottom-left
        draw_chad(ctx, 185, 615, scale=2.15, facing="right", pose="sleep_bed",
                    expression="shocked", t=t, red_rim=0.8)
        # Big blue-purple blanket mound covering bottom-left
        ctx.move_to(-50, 620)
        ctx.curve_to(250, 540, 680, 590, 885, 760)
        ctx.line_to(910, HEIGHT)
        ctx.line_to(-50, HEIGHT)
        ctx.close_path()
        ctx.set_source_rgb(*hex_rgb("#5A4668"))
        ctx.fill_preserve()
        set_ink(ctx, 6.5)
        ctx.stroke()
        return

    if mode == "closeup_ecg":
        # Closeup of Chad sitting up with glowing red ECG heartbeat line (Shot 5)
        draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#121014", stroke_w=0)
        pat = cairo.RadialGradient(WIDTH * 0.85, HEIGHT * 0.5, 50, WIDTH * 0.85, HEIGHT * 0.5, 950)
        pat.add_color_stop_rgba(0.0, 0.85, 0.12, 0.10, 0.55)
        pat.add_color_stop_rgba(1.0, 0.85, 0.12, 0.10, 0.0)
        ctx.set_source(pat)
        ctx.paint()

        expr = "shocked" if prog > 0.45 else "neutral"
        draw_chad(ctx, 940, 1020, scale=2.95, facing="front", pose="idle",
                    expression=expr, t=t, red_rim=0.75)
        draw_ecg_waveform(ctx, t, progress=clamp(prog * 1.35, 0.1, 1.0), spike=(prog > 0.45))
        return

    # Standard wide bedroom base
    surf = _get_cached_bg("bedroom_base", _build_bedroom_base)
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint()

    if mode == "sleep":
        # Chad sleeping under blue duvet
        draw_chad(ctx, 780, 635, scale=1.05, facing="front", pose="sleep_bed", expression="asleep", t=t)
        ctx.move_to(0, 740)
        ctx.curve_to(280, 560, 720, 545, 985, 665)
        ctx.line_to(985, 985)
        ctx.line_to(0, 1080)
        ctx.close_path()
        ctx.set_source_rgb(*hex_rgb("#2C3856"))
        ctx.fill_preserve()
        set_ink(ctx, 5.0)
        ctx.stroke()
        # Phone on nightstand lights up red at prog > 0.5
        pcol = "#D42620" if prog > 0.5 else "#181A20"
        draw_ink_box(ctx, 1145, 525, 65, 32, pcol, stroke_w=3.0, r=4)

    elif mode == "blink_gone":
        # Chad sitting on edge of bed holding phone; "🔕 No notifications" pill pops up
        is_red = (prog < 0.22)
        draw_chad(ctx, 825, 645, scale=1.28, facing="front", pose="sit_bed",
                    expression="worried", prop="phone_red" if is_red else "phone", t=t)
        if prog > 0.52:
            rounded_rect_path(ctx, 1135, 535, 465, 86, 22)
            ctx.set_source_rgb(*hex_rgb("#F4F1EA"))
            ctx.fill_preserve()
            set_ink(ctx, 3.5)
            ctx.stroke()
            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(34)
            ctx.set_source_rgb(*hex_rgb("#1B1918"))
            ctx.move_to(1175, 590)
            ctx.show_text("No notifications")

    elif mode in ("clock_wait", "ew04_beam"):
        is_red = (clock_str == "3:00" and prog > 0.22) or (mode == "ew04_beam")
        draw_digital_clock(ctx, 1110, 445, 165, 95, time_str=clock_str, glow=is_red)
        expr = "shocked" if is_red else "worried"
        draw_chad(ctx, 815, 645, scale=1.28, facing="right", pose="sit_bed",
                    expression=expr, prop="phone_red" if is_red else "phone", t=t)
        if mode == "ew04_beam":
            # Red dotted trajectory from "EW04" in night sky window into Chad's phone
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(44)
            ctx.set_source_rgb(*hex_rgb("#E51C1C"))
            ctx.move_to(1515, 235)
            ctx.show_text("EW04")
            ctx.save()
            ctx.set_dash([10.0, 12.0])
            ctx.move_to(1560, 255)
            ctx.curve_to(1510, 460, 1180, 620, 845, 665)
            ctx.set_line_width(6.0)
            ctx.stroke()
            ctx.restore()

    elif mode == "sunrise_cardboard":
        # Window taped with brown cardboard; seams glow blue at 3:01 then orange at 6:47
        wx, wy, ww, wh = 965, 0, 745, 485
        draw_ink_box(ctx, wx + 45, wy + 25, ww - 90, wh - 45, "#8E6D4A", stroke_w=4.0)
        is_sun = (prog > 0.65)
        seam_col = (1.0, 0.62, 0.18, 0.9) if is_sun else (0.35, 0.68, 1.0, 0.85)
        ctx.set_source_rgba(*seam_col)
        ctx.set_line_width(10.0)
        ctx.move_to(wx + ww * 0.5, wy + 25)
        ctx.line_to(wx + ww * 0.5, wy + wh - 20)
        ctx.move_to(wx + 45, wy + wh * 0.5)
        ctx.line_to(wx + ww - 45, wy + wh * 0.5)
        ctx.stroke()
        draw_scotch_tape(ctx, wx + 135, wy + 65, 95, 32, -8)
        draw_scotch_tape(ctx, wx + 595, wy + 295, 95, 32, 5)
        draw_digital_clock(ctx, 1110, 445, 165, 95, time_str="6:47" if is_sun else "3:01", glow=False)
        if prog < 0.45:
            draw_chad(ctx, 1345, 655, scale=1.22, facing="left", pose="idle", expression="worried", t=t)

# ==============================================================================
# 4. WINDOW POV DOWN TO NEIGHBOR'S GARDEN & BIRCH STREET
# ==============================================================================
def _build_window_garden_base(ctx, is_night=False):
    mul = 0.28 if is_night else 1.0
    def _c(h):
        r, g, b = hex_rgb(h)
        return (r * mul, g * mul, b * mul)

    # Diagonal street, sidewalk, lawn & garden bed
    draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#84807A" if not is_night else "#222632", stroke_w=0)

    # Sidewalk & Brick courtyard wall
    ctx.move_to(220, 0)
    ctx.line_to(WIDTH, 390)
    ctx.line_to(WIDTH, HEIGHT)
    ctx.line_to(0, HEIGHT)
    ctx.close_path()
    ctx.set_source_rgb(*_c("#DFD6C5"))
    ctx.fill_preserve()
    set_ink(ctx, 4.5)
    ctx.stroke()

    # Grass patch & raised wooden tomato bed
    ctx.move_to(575, 495)
    ctx.line_to(945, 295)
    ctx.line_to(1465, 545)
    ctx.line_to(1115, 815)
    ctx.close_path()
    ctx.set_source_rgb(*_c("#A6B56E"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()

    # Raised brown soil bed & 5 staked tomato plants
    ctx.move_to(615, 495)
    ctx.line_to(955, 315)
    ctx.line_to(1455, 525)
    ctx.line_to(1315, 645)
    ctx.line_to(945, 475)
    ctx.line_to(735, 585)
    ctx.close_path()
    ctx.set_source_rgb(*_c("#8E6B4E"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()

    for sx, sy in [(705, 515), (845, 445), (965, 385), (1135, 465), (1285, 535)]:
        ctx.move_to(sx, sy + 20)
        ctx.line_to(sx - 6, sy - 245)
        set_ink(ctx, 6.0)
        ctx.stroke()
        for ty_off in (-65, -135, -195):
            ctx.arc(sx - 24, sy + ty_off, 18, 0, math.pi * 2)
            ctx.arc(sx + 24, sy + ty_off + 12, 18, 0, math.pi * 2)
            ctx.set_source_rgb(*_c("#D4382C"))
            ctx.fill_preserve()
            set_ink(ctx, 2.5)
            ctx.stroke()

    # Black wrought-iron fence & gate on right
    set_ink(ctx, 5.5)
    for fi in range(14):
        fx = 995 + fi * 62
        fy = 185 + fi * 28
        ctx.move_to(fx, fy)
        ctx.line_to(fx - 12, fy + 225)
    ctx.stroke()

    # Foreground 3rd-floor window sill in bottom-left
    ctx.move_to(0, 295)
    ctx.line_to(1225, HEIGHT)
    ctx.line_to(0, HEIGHT)
    ctx.close_path()
    ctx.set_source_rgb(*_c("#E5DAC8"))
    ctx.fill_preserve()
    set_ink(ctx, 6.0)
    ctx.stroke()

def draw_env_window_garden(ctx, t, mode="watering", prog=0.0):
    is_night = mode in ("cardboard_gap_bathrobe_man", "hose_abandoned_night")
    surf = _get_cached_bg("garden_night" if is_night else "garden_day",
                          lambda c: _build_window_garden_base(c, is_night=is_night))
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint()

    if mode in ("watering", "cardboard_gap_watering"):
        draw_neighbor(ctx, 1055, 465, scale=1.08, is_zombie=False, watering=True, t=t)
        if mode == "cardboard_gap_watering":
            # Framed between two vertical torn brown cardboard sheets (Shot 81)
            draw_ink_box(ctx, 0, 0, 655, HEIGHT, "#6A543E", stroke_w=6.0)
            draw_ink_box(ctx, 1275, 0, 645, HEIGHT, "#6A543E", stroke_w=6.0)

    elif mode == "chad_cart":
        # Chad outside on sidewalk with shopping cart of 28 water jugs (Shot 23)
        draw_chad(ctx, 1175, 715, scale=1.05, facing="front", pose="idle", t=t)
        # Cart full of jugs next to him
        draw_ink_box(ctx, 935, 675, 175, 135, "#8E949C", stroke_w=4.0, r=6)
        for jr in range(3):
            for jc in range(3):
                draw_water_jug(ctx, 965 + jc * 52, 655 - jr * 42, scale=0.62)

    elif mode == "hose_abandoned_night":
        # Running hose lying in dark puddle next to dropped garden trowel (Shot 99)
        ctx.save()
        ctx.translate(1015, 695)
        ctx.scale(2.4, 0.65)
        ctx.arc(0, 0, 75, 0, math.pi * 2)
        ctx.set_source_rgba(0.12, 0.22, 0.36, 0.85)
        ctx.fill()
        ctx.restore()
        ctx.move_to(595, 385)
        ctx.curve_to(565, 585, 795, 645, 925, 685)
        ctx.set_source_rgb(*hex_rgb("#2E5E36"))
        ctx.set_line_width(14.0)
        ctx.stroke()

    elif mode == "cardboard_gap_bathrobe_man":
        # Shot 93: Parked car headlights illuminating man in bathrobe walking in circles, then sprinting
        # Headlight cone
        pat = cairo.LinearGradient(980, 390, 1480, 620)
        pat.add_color_stop_rgba(0.0, 1.0, 0.96, 0.78, 0.75)
        pat.add_color_stop_rgba(1.0, 1.0, 0.96, 0.78, 0.0)
        ctx.move_to(980, 390)
        ctx.line_to(1520, 520)
        ctx.line_to(1380, 720)
        ctx.close_path()
        ctx.set_source(pat)
        ctx.fill()

        # Man in bathrobe (walks in slow circles until prog > 0.65, then sprints left!)
        if prog < 0.65:
            ang = t * 2.2
            mx = 1235 + math.cos(ang) * 45
            my = 445 + math.sin(ang) * 22
        else:
            sprint_p = (prog - 0.65) / 0.35
            mx = 1235 - sprint_p * 780
            my = 445 - sprint_p * 260
        draw_ink_box(ctx, mx - 18, my - 45, 36, 65, "#DCE2E6", stroke_w=3.0, r=8)
        ctx.arc(mx, my - 65, 22, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#8C948E"))
        ctx.fill_preserve()
        set_ink(ctx, 3.0)
        ctx.stroke()

        # Torn cardboard mask around perimeter with 4 strips of tape
        ctx.save()
        ctx.rectangle(0, 0, WIDTH, HEIGHT)
        ctx.arc(WIDTH * 0.5, HEIGHT * 0.5, 520, 0, math.pi * 2)
        ctx.set_fill_rule(cairo.FILL_RULE_EVEN_ODD)
        ctx.set_source_rgb(*hex_rgb("#5A432E"))
        ctx.fill()
        ctx.restore()
        for tx, ty, ta in [(480, 180, -28), (1440, 180, 28), (480, 880, 28), (1440, 880, -28)]:
            draw_scotch_tape(ctx, tx, ty, 135, 42, ta)
