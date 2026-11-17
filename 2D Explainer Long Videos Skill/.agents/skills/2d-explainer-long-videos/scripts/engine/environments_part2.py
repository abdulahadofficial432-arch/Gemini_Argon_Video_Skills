import math
import cairo
from engine.primitives import (
    WIDTH, HEIGHT, hex_rgb, hex_rgba, set_ink, rounded_rect_path,
    draw_ink_box, draw_scotch_tape, draw_slanted_stamp_banner,
    draw_speech_bubble, draw_sound_wave_arcs, draw_fire_plume, clamp, smoothstep
)
from engine.characters import (
    draw_chad, draw_neighbor, draw_water_jug,
    draw_fire_extinguisher_prop, draw_hand_with_pen
)
from engine.overlays import draw_notebook_card, draw_sticky_note_pad, draw_taped_label
from engine.diagrams import draw_calorie_tube_overlay, draw_screw_stud_inset
from engine.environments import _get_cached_bg

# ==============================================================================
# 5. LIVING ROOM / KITCHEN (Day, Cardboard-Taped Windows, Dark Night, Props)
# ==============================================================================
def _build_living_room_base(ctx, is_dark=False):
    mul = 0.34 if is_dark else 1.0
    def _c(h):
        r, g, b = hex_rgb(h)
        return (r * mul, g * mul, b * mul)

    # Walls, ceiling, wood-plank floor & beige area rug
    draw_ink_box(ctx, 0, 0, WIDTH, 695, "#D8BD98" if not is_dark else "#3D332A", stroke_w=0)
    draw_ink_box(ctx, 0, 0, WIDTH, 55, "#E4D0B4" if not is_dark else "#483E35", stroke_w=3.5)
    draw_ink_box(ctx, 0, 695, WIDTH, 385, "#B88B58" if not is_dark else "#35281C", stroke_w=4.0)
    # Rug
    ctx.move_to(295, 765)
    ctx.line_to(1465, 765)
    ctx.line_to(1715, HEIGHT)
    ctx.line_to(85, HEIGHT)
    ctx.close_path()
    ctx.set_source_rgb(*_c("#C8BA9E"))
    ctx.fill_preserve()
    set_ink(ctx, 3.5)
    ctx.stroke()

    # Left Kitchen: White Fridge, Stove/Oven, Sink & Wood Cabinets
    draw_ink_box(ctx, 0, 175, 165, 745, "#DFDDD6" if not is_dark else "#4A4A48", stroke_w=4.5)
    draw_ink_box(ctx, 85, 38, 295, 325, "#A87B50" if not is_dark else "#3B2B1E", stroke_w=4.0)
    draw_ink_box(ctx, 165, 535, 295, 315, "#DFDDD6" if not is_dark else "#4A4A48", stroke_w=4.0)
    draw_ink_box(ctx, 315, 515, 155, 275, "#A87B50" if not is_dark else "#3B2B1E", stroke_w=4.0)

    # Hallway / Closet Door on left wall
    draw_ink_box(ctx, 485, 85, 115, 635, "#C2986B" if not is_dark else "#423426", stroke_w=4.0)

    # Center Triple Window overlooking suburban houses & trees
    wx, wy, ww, wh = 665, 195, 655, 325
    draw_ink_box(ctx, wx - 16, wy - 16, ww + 32, wh + 32, "#E5D5BE" if not is_dark else "#4A423A", stroke_w=4.0)
    draw_ink_box(ctx, wx, wy, ww, wh, "#C5D8C8" if not is_dark else "#1C2430", stroke_w=3.5)
    if not is_dark:
        for hx_h, hcol in [(720, "#B88A72"), (880, "#9E7B66"), (1060, "#7C8894")]:
            ctx.move_to(hx_h, wy + wh)
            ctx.line_to(hx_h + 65, wy + 135)
            ctx.line_to(hx_h + 135, wy + wh)
            ctx.close_path()
            ctx.set_source_rgb(*_c(hcol))
            ctx.fill_preserve()
            set_ink(ctx, 2.5)
            ctx.stroke()
    ctx.move_to(wx + ww * 0.25, wy)
    ctx.line_to(wx + ww * 0.25, wy + wh)
    ctx.move_to(wx + ww * 0.75, wy)
    ctx.line_to(wx + ww * 0.75, wy + wh)
    set_ink(ctx, 4.0)
    ctx.stroke()

    # Dining Table & 2 Wooden Chairs under window
    draw_ink_box(ctx, 625, 565, 385, 22, "#A87B50" if not is_dark else "#3B2B1E", stroke_w=3.5)
    draw_ink_box(ctx, 645, 587, 18, 195, "#946A42" if not is_dark else "#322418", stroke_w=3.0)
    draw_ink_box(ctx, 965, 587, 18, 195, "#946A42" if not is_dark else "#322418", stroke_w=3.0)
    draw_ink_box(ctx, 665, 485, 115, 295, "#AD8055" if not is_dark else "#3D2D1E", stroke_w=3.5)

    # CRT TV on stand & Olive-Green Armchair (#7B7D54) on right
    draw_ink_box(ctx, 1365, 445, 195, 145, "#6E6A64" if not is_dark else "#2B2A28", stroke_w=4.0, r=8)
    draw_ink_box(ctx, 1380, 460, 135, 115, "#4E5254" if not is_dark else "#1E2022", stroke_w=3.0, r=12)
    draw_ink_box(ctx, 1215, 555, 365, 325, "#84865C" if not is_dark else "#323424", stroke_w=4.5, r=24, shadow=True)

    # Front Door on right wall
    draw_ink_box(ctx, 1685, 65, 235, 865, "#AD845A" if not is_dark else "#3B2D1E", stroke_w=4.5)

def draw_env_living_room(ctx, t, mode="day1_check", cardboard=False, dark_mode=False, props_level=0, prog=0.0):
    surf = _get_cached_bg("living_dark" if dark_mode else "living_day",
                          lambda c: _build_living_room_base(c, is_dark=dark_mode))
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint()

    # Taped brown cardboard over window (with torn gap at top-right corner)
    if cardboard:
        wx, wy, ww, wh = 665, 195, 655, 325
        cprog = clamp(prog * 1.4, 0.25, 1.0) if mode == "tape_cardboard" else 1.0
        draw_ink_box(ctx, wx, wy, ww * cprog, wh, "#7C5E42" if not dark_mode else "#382A1E", stroke_w=4.0)
        # Small torn gap at top-right corner showing dark night sky
        draw_ink_box(ctx, wx + ww - 135, wy + 12, 115, 68, "#162238", stroke_w=3.0)
        for tx_t in range(wx + 45, int(wx + ww * cprog - 20), 145):
            draw_scotch_tape(ctx, tx_t, wy, 48, 22, 0)
            draw_scotch_tape(ctx, tx_t, wy + wh, 48, 22, 0)

    # Dynamic stockpiled props
    if props_level == 0:
        draw_water_jug(ctx, 835, 525, scale=0.68)
        draw_water_jug(ctx, 905, 525, scale=0.68)
    elif props_level >= 1:
        draw_water_jug(ctx, 505, 735, scale=0.72)
        draw_water_jug(ctx, 565, 735, scale=0.72)
        draw_ink_box(ctx, 565, 625, 115, 85, "#B8925A", stroke_w=3.5)
        draw_ink_box(ctx, 565, 710, 115, 85, "#B8925A", stroke_w=3.5)
        # Yellow CRUNCH O's cereal box on table
        draw_ink_box(ctx, 835, 485, 52, 72, "#E8BA28", stroke_w=3.0)
    if props_level >= 2:
        # 30 water jugs + open box of cans + fire extinguisher + first-aid kit + bug-out bag
        for jr in range(2):
            for jc in range(4):
                draw_water_jug(ctx, 85 + jc * 58, 915 - jr * 55, scale=0.75)
        draw_fire_extinguisher_prop(ctx, 435, 455, scale=0.58)
        draw_ink_box(ctx, 885, 515, 75, 52, "#C92420", stroke_w=3.0, r=6)
        draw_ink_box(ctx, 1745, 845, 85, 105, "#243248", stroke_w=3.5, r=18)

    # Mode-specific character actions & overlays
    if mode == "day1_turn":
        f_dir = "back" if prog < 0.55 else "front"
        draw_chad(ctx, 1015, 625, scale=1.22, facing=f_dir, pose="idle", expression="worried", t=t)

    elif mode == "day1_check":
        draw_chad(ctx, 1035, 625, scale=1.22, facing="left", pose="idle", expression="worried", prop="cash", t=t)
        draw_notebook_card(
            ctx, 68, 125, 665, 605,
            title="6 DAYS LEFT", sub_title="FRI 8AM",
            items=[
                {"type": "bar_row", "icon": "water", "label": "WATER", "val": "2 gal", "frac": 0.08, "color": "#3B8EEA"},
                {"type": "bar_row", "icon": "food", "label": "FOOD", "val": "3 days", "frac": 0.12, "color": "#E8922D"},
                {"type": "bar_row", "icon": "cash", "label": "CASH", "val": "$40", "frac": 0.06, "color": "#58B86C"},
            ],
            progress=prog
        )

    elif mode == "call_friend":
        pose = "phone_ear" if prog < 0.65 else "phone_look"
        draw_chad(ctx, 935, 585, scale=1.18, facing="left", pose=pose, expression="worried", prop="phone", t=t)

    elif mode == "broken_or_purpose":
        # Blurred living room closeup of Chad holding cracked phone + 2 taped labels
        draw_chad(ctx, 945, 920, scale=2.75, facing="front", pose="phone_look",
                    expression="shocked" if prog > 0.45 else "neutral", prop="phone", t=t)
        if prog > 0.18:
            draw_taped_label(ctx, 365, 365, "BROKEN?", angle_deg=-5.0, scale=clamp((prog - 0.18) * 5, 0, 1))
        if prog > 0.48:
            draw_taped_label(ctx, 1545, 345, "ON PURPOSE?", color="#D42620", angle_deg=4.5, scale=clamp((prog - 0.48) * 5, 0, 1))

    elif mode == "cereal_hide_cash":
        draw_chad(ctx, 1085, 595, scale=1.25, facing="left", pose="idle", expression="worried", prop="cash", t=t)

    elif mode == "day2_check":
        draw_chad(ctx, 695, 635, scale=1.22, facing="right", pose="idle", expression="worried", t=t)
        draw_notebook_card(
            ctx, 1185, 130, 665, 465,
            title="5 DAYS LEFT", sub_title="SAT",
            items=[
                {"type": "bar_row", "icon": "food", "label": "FOOD", "val": "3", "new_val": "24 days", "frac": 0.92, "color": "#E8922D"},
                {"type": "bar_row", "icon": "cash", "label": "CASH", "val": "$40", "new_val": "$640", "frac": 0.80, "color": "#58B86C"},
            ],
            progress=prog,
            angle_deg=1.8
        )

    elif mode == "test_channel_you":
        if prog < 0.48:
            draw_chad(ctx, 985, 595, scale=1.18, facing="back", pose="idle", t=t)
        else:
            draw_chad(ctx, 925, 780, scale=1.85, facing="front", pose="phone_look", expression="worried", prop="phone", t=t)
            # Little antenna + "TEST CHANNEL" pennant + red arrow "YOU"
            ctx.move_to(945, 685)
            ctx.line_to(1255, 395)
            set_ink(ctx, 5.0)
            ctx.stroke()
            ctx.move_to(1225, 425)
            ctx.line_to(1515, 565)
            ctx.line_to(1465, 645)
            ctx.line_to(1165, 485)
            ctx.close_path()
            ctx.set_source_rgb(*hex_rgb("#F4EFE2"))
            ctx.fill_preserve()
            set_ink(ctx, 3.5)
            ctx.stroke()
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(34)
            ctx.set_source_rgb(*hex_rgb("#D42620"))
            ctx.move_to(1225, 545)
            ctx.show_text("TEST CHANNEL")
            if prog > 0.76:
                ctx.move_to(1265, 365)
                ctx.show_text("YOU")

    elif mode == "tape_cardboard":
        draw_chad(ctx, 1185, 485, scale=1.18, facing="back", pose="idle", t=t)

    elif mode in ("chair_3days_alert", "chair_1hour_later"):
        is_alert = (mode == "chair_3days_alert" and prog > 0.25)
        draw_chad(ctx, 945, 685, scale=1.45, facing="front", pose="sit_chair",
                    expression="shocked" if is_alert else "worried",
                    prop="phone_red" if is_alert else "phone", t=t)
        if is_alert:
            draw_speech_bubble(ctx, 325, 295, 455, 165, 925, 635,
                               ["3 DAYS.", "TELL NO ONE."], red_last_line=True,
                               scale=clamp((prog - 0.25) * 4.0, 0, 1))
        if mode == "chair_1hour_later":
            draw_taped_label(ctx, 265, 165, "1 HOUR LATER", angle_deg=-3.5)

    elif mode == "place_gear_and_eat_fridge":
        if prog < 0.48:
            draw_chad(ctx, 845, 615, scale=1.22, facing="left", pose="idle", expression="worried", prop="extinguisher", t=t)
        else:
            # Open white fridge on left as Chad eats all perishable containers
            draw_ink_box(ctx, 165, 385, 255, 535, "#E8EAE6", stroke_w=4.5)
            n_left = int((1.0 - (prog - 0.48) / 0.52) * 8)
            for fi in range(n_left):
                draw_ink_box(ctx, 195 + (fi % 2) * 85, 425 + (fi // 2) * 95, 55, 65, "#E5A838", stroke_w=2.5)
            draw_chad(ctx, 645, 615, scale=1.35, facing="left", pose="idle", expression="grimace_teeth", t=t)

    elif mode == "bleach_water":
        # Bleach bottle & water jug on dining table + UNSCENTED / 6% / 8 drops / 30:00 clock
        draw_ink_box(ctx, 835, 445, 95, 155, "#EAECEE", stroke_w=4.0, r=12)
        draw_ink_box(ctx, 838, 495, 89, 55, "#2858A8", stroke_w=2.0)
        draw_water_jug(ctx, 985, 535, scale=1.05)
        if prog < 0.38:
            draw_taped_label(ctx, 655, 365, "UNSCENTED", angle_deg=-5.5)
            if prog > 0.18:
                draw_taped_label(ctx, 1185, 385, "6%", color="#D42620", angle_deg=3.5)
        else:
            expr = "wince" if prog > 0.82 else "neutral"
            draw_chad(ctx, 1085, 565, scale=1.28, facing="left", pose="idle", expression=expr, t=t)
            if prog > 0.58:
                # 30:00 countdown wall clock on left
                ctx.arc(285, 315, 78, 0, math.pi * 2)
                ctx.set_source_rgb(*hex_rgb("#F5F0DC"))
                ctx.fill_preserve()
                set_ink(ctx, 4.5)
                ctx.stroke()
                draw_ink_box(ctx, 215, 405, 140, 48, "#F5F0DC", stroke_w=3.0)
                ctx.select_font_face("Consolas", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(32)
                ctx.move_to(242, 440)
                ctx.show_text("0:00" if prog > 0.78 else "30:00")

    elif mode == "pack_bag_timer":
        draw_chad(ctx, 1085, 625, scale=1.22, facing="right", pose="idle", expression="worried", t=t)
        # Yellow dashed escape path to backpack and door handle
        ctx.save()
        ctx.set_dash([14.0, 10.0])
        ctx.move_to(1085, 855)
        ctx.line_to(1765, 895)
        ctx.line_to(1695, 545)
        ctx.set_source_rgb(*hex_rgb("#F5D438"))
        ctx.set_line_width(6.0)
        ctx.stroke()
        ctx.restore()

    elif mode == "call_ellen_ward":
        draw_chad(ctx, 1015, 615, scale=1.28, facing="left", pose="phone_ear", expression="worried", prop="phone", t=t)
        if prog > 0.45:
            draw_speech_bubble(ctx, 325, 165, 585, 195, 965, 485,
                               ["Ellen Ward doesn't", "work there anymore."],
                               scale=clamp((prog - 0.45) * 4.0, 0, 1))

    elif mode in ("thursday_9pm_all_scream", "alarms_cut_short", "power_out_940", "woman_screams_downstairs", "smoke_alarm_11pm"):
        draw_chad(ctx, 960, 625, scale=1.28, facing="front", pose="idle", expression="shocked", t=t)
        if mode == "thursday_9pm_all_scream" and prog > 0.25:
            draw_sound_wave_arcs(ctx, 960, 45, math.pi * 0.5, 1.2, t)
            draw_sound_wave_arcs(ctx, 960, 985, -math.pi * 0.5, 1.2, t)
            draw_sound_wave_arcs(ctx, 185, 540, 0.0, 1.2, t)
            draw_sound_wave_arcs(ctx, 1735, 540, math.pi, 1.2, t)
        elif mode == "alarms_cut_short" and prog < 0.55:
            draw_sound_wave_arcs(ctx, 85, 540, 0.0, 1.2, t)
        elif mode == "power_out_940":
            draw_taped_label(ctx, 215, 145, "9:40 PM", angle_deg=-4.0)
        elif mode == "woman_screams_downstairs":
            if prog < 0.62:
                draw_sound_wave_arcs(ctx, 960, 985, -math.pi * 0.5, 1.2, t)
            else:
                # Stark black silhouette with purple rim light when scream stops
                draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#040406", stroke_w=0)
                draw_chad(ctx, 960, 980, scale=2.85, facing="left", pose="idle",
                            expression="shocked", t=t, red_rim=0.85)
        elif mode == "smoke_alarm_11pm":
            draw_taped_label(ctx, 1615, 145, "11:00 PM", angle_deg=2.5)
            # Ceiling smoke detector flashing red
            ctx.arc(1125, 175, 42, 0, math.pi * 2)
            ctx.set_source_rgb(*hex_rgb("#D8D4CC"))
            ctx.fill_preserve()
            set_ink(ctx, 3.5)
            ctx.stroke()
            if prog > 0.35:
                pat = cairo.RadialGradient(1125, 175, 8, 1125, 175, 195)
                pat.add_color_stop_rgba(0.0, 0.95, 0.12, 0.12, 0.78)
                pat.add_color_stop_rgba(1.0, 0.95, 0.12, 0.12, 0.0)
                ctx.set_source(pat)
                ctx.paint()

# ==============================================================================
# 6. FRONT DOOR INTERIOR ENTRYWAY
# ==============================================================================
def _build_front_door_base(ctx, is_dark=False):
    mul = 0.32 if is_dark else 1.0
    def _c(h):
        r, g, b = hex_rgb(h)
        return (r * mul, g * mul, b * mul)

    draw_ink_box(ctx, 0, 0, WIDTH, 915, "#C9AE8C" if not is_dark else "#383028", stroke_w=0)
    draw_ink_box(ctx, 0, 915, WIDTH, 165, "#9C744A" if not is_dark else "#2B2016", stroke_w=4.0)

    # Center Wooden Front Door (#A87C4F)
    dx, dy, dw, dh = 620, 15, 540, 900
    draw_ink_box(ctx, dx - 24, dy, dw + 48, dh, "#8E643B" if not is_dark else "#2E2014", stroke_w=5.0)
    draw_ink_box(ctx, dx, dy + 18, dw, dh - 18, "#AD8255" if not is_dark else "#3D2E1E", stroke_w=4.5)

    # Peephole, chain lock, deadbolt & handle on right of door
    ctx.arc(dx + dw * 0.5, dy + 245, 18, 0, math.pi * 2)
    ctx.set_source_rgb(*_c("#D4B258"))
    ctx.fill_preserve()
    set_ink(ctx, 3.5)
    ctx.stroke()
    draw_ink_box(ctx, dx + dw - 65, dy + 425, 42, 125, "#C8A850" if not is_dark else "#584A24", stroke_w=3.5, r=6)
    ctx.arc(dx + dw - 44, dy + 462, 16, 0, math.pi * 2)
    ctx.fill_preserve()
    ctx.stroke()

    # Doormat
    ctx.move_to(655, 935)
    ctx.line_to(1125, 935)
    ctx.line_to(1165, HEIGHT)
    ctx.line_to(615, HEIGHT)
    ctx.close_path()
    ctx.set_source_rgb(*_c("#9E8D74"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()

    # Hanging Dark Coat on hook on right wall
    ctx.move_to(1255, 195)
    ctx.line_to(1185, 345)
    ctx.line_to(1195, 655)
    ctx.line_to(1355, 695)
    ctx.line_to(1365, 325)
    ctx.close_path()
    ctx.set_source_rgb(*_c("#4E433A"))
    ctx.fill_preserve()
    set_ink(ctx, 4.5)
    ctx.stroke()

def draw_env_front_door(ctx, t, mode="price_tags", prog=0.0):
    is_dark = mode in ("knocks", "brace_3in", "smoke_fire_escape", "pass_notebook", "aim_extinguisher")
    surf = _get_cached_bg("door_dark" if is_dark else "door_day",
                          lambda c: _build_front_door_base(c, is_dark=is_dark))
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint()

    if mode == "price_tags":
        f_dir = "back" if prog > 0.78 else "front"
        draw_chad(ctx, 1145, 595, scale=1.85, facing=f_dir, pose="idle", expression="worried", t=t)
        if prog > 0.18 and prog < 0.58:
            # $300 yellow price tag hanging on left
            ctx.save()
            ctx.translate(725, 255)
            ctx.rotate(-0.18)
            draw_ink_box(ctx, -110, -45, 240, 95, "#EDD878", stroke_w=4.0, r=8, shadow=True)
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(52)
            ctx.set_source_rgb(*hex_rgb("#181615"))
            ctx.move_to(-65, 18)
            ctx.show_text("$300")
            ctx.restore()
        elif prog >= 0.58:
            # Knocked $300 tag on floor + Giant Red "EVERYTHING" tag slammed on door
            ctx.save()
            ctx.translate(535, 925)
            ctx.rotate(0.15)
            draw_ink_box(ctx, -85, -28, 175, 56, "#C8B868", stroke_w=3.0, r=6)
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(32)
            ctx.move_to(-45, 10)
            ctx.show_text("$300")
            ctx.restore()

            ctx.save()
            ctx.translate(485, 365)
            ctx.rotate(0.06)
            draw_ink_box(ctx, -295, -85, 590, 175, "#C92420", stroke_w=5.5, r=14, shadow=True)
            ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(64)
            ctx.set_source_rgb(1, 1, 1)
            ctx.move_to(-215, 24)
            ctx.show_text("EVERYTHING")
            ctx.restore()

    elif mode == "sticky_water":
        draw_chad(ctx, 525, 765, scale=2.15, facing="back", pose="point_right", t=t)
        draw_sticky_note_pad(ctx, 985, 435, 235, 225,
                             ["3 MIN AIR", "3 DAYS WATER", "3 WEEKS FOOD"],
                             progress=1.0, circle_word="WATER" if prog > 0.45 else None, show_pen=(prog > 0.45))

    elif mode == "todo_calories":
        draw_chad(ctx, 645, 605, scale=1.85, facing="right", pose="point_right", expression="worried", t=t)
        draw_sticky_note_pad(ctx, 835, 225, 265, 255,
                             ["TO DO", "WATER [OK]", "FOOD"],
                             progress=1.0, circle_word="FOOD", show_pen=False)
        if prog > 0.35:
            kcal = 2000.0 * clamp((prog - 0.35) / 0.55, 0.0, 1.0)
            draw_calorie_tube_overlay(ctx, 185, 395, kcal_val=kcal, pouring_pb=False, prog=prog)

    elif mode == "boot_kick":
        draw_chad(ctx, 445, 645, scale=1.85, facing="right", pose="idle", expression="shocked", t=t)
        if prog > 0.48:
            # Concentric kick shockwave rings on center of door + giant cartoon boot from right
            cx_k, cy_k = 890, 485
            for ri in range(3):
                ctx.arc(cx_k, cy_k, 65 + ri * 55, 0, math.pi * 2)
                ctx.set_source_rgba(0.95, 0.25, 0.20, 0.75 - ri * 0.2)
                ctx.set_line_width(5.0)
                ctx.stroke()
            draw_ink_box(ctx, 1020, 435, 890, 95, "#2C303A", stroke_w=5.0)
            draw_ink_box(ctx, 965, 415, 115, 125, "#3E3228", stroke_w=5.0, r=18)

    elif mode == "screw_reinforce":
        draw_chad(ctx, 815, 595, scale=1.85, facing="right", pose="point_right", expression="worried", t=t)
        draw_screw_stud_inset(ctx, 95, 65, 640, 405, prog=prog)
        draw_notebook_card(
            ctx, 85, 515, 585, 415,
            title="",
            items=[
                {"type": "text", "text": "SURVIVAL TIP #", "size": 42, "color": "#D42620"},
                {"type": "text", "text": "Strike plate:", "size": 36, "color": "#162955"},
                {"type": "text", "text": "3-inch screws", "size": 36, "color": "#162955", "highlight": "#E54848"},
                {"type": "text", "text": "into the stud.", "size": 36, "color": "#162955"},
            ],
            progress=prog,
            angle_deg=-1.5
        )

    elif mode == "pack_bag":
        draw_chad(ctx, 735, 595, scale=1.75, facing="right", pose="idle", expression="worried", t=t)
        draw_ink_box(ctx, 965, 805, 115, 135, "#283852", stroke_w=4.0, r=22, shadow=True)

    elif mode in ("knocks", "brace_3in"):
        if mode == "brace_3in":
            draw_chad(ctx, 435, 625, scale=1.75, facing="right", pose="idle", expression="shocked", t=t)
            if prog > 0.45:
                draw_screw_stud_inset(ctx, 1320, 65, 560, 365, prog=1.0)
        for kx_i in range(3):
            if prog > 0.15 + kx_i * 0.25:
                ctx.arc(885 + (kx_i - 1) * 45, 285, 28, 0, math.pi * 2)
                ctx.set_source_rgba(0.95, 0.92, 0.85, 0.55)
                ctx.set_line_width(3.0)
                ctx.stroke()

    elif mode in ("smoke_fire_escape", "pass_notebook", "aim_extinguisher"):
        # Flames and thick grey smoke curling in under bottom of door
        draw_fire_plume(ctx, 645, 920, 490, 95, t, seed=7)
        for sp in range(6):
            ctx.arc(680 + sp * 78, 865 - (sp % 2) * 35, 65, 0, math.pi * 2)
            ctx.set_source_rgba(0.35, 0.34, 0.33, 0.48)
            ctx.fill()

        if mode == "smoke_fire_escape":
            draw_fire_extinguisher_prop(ctx, 555, 865, scale=0.88)
            pose = "crouch" if prog < 0.65 else "idle"
            prop = "backpack_extinguisher" if prog >= 0.65 else None
            draw_chad(ctx, 745, 645, scale=1.75, facing="right", pose=pose,
                        expression="grimace_teeth", prop=prop, t=t)
        elif mode == "pass_notebook":
            draw_chad(ctx, 845, 635, scale=1.75, facing="left", pose="idle",
                        expression="grimace_teeth", prop="backpack_extinguisher", t=t)
            draw_notebook_card(
                ctx, 985, 55, 845, 945,
                title="",
                items=[
                    {"type": "text", "text": "HOW TO FIGHT A FIRE", "size": 46, "color": "#162955"},
                    {"type": "pass_row", "letter": "P", "rest": "ull the pin", "color": "#D4A017"},
                    {"type": "pass_row", "letter": "A", "rest": "im at the BASE", "color": "#D42620"},
                    {"type": "pass_row", "letter": "S", "rest": "queeze", "color": "#2874C8"},
                    {"type": "pass_row", "letter": "S", "rest": "weep side to side", "color": "#389848"},
                ],
                progress=prog,
                angle_deg=1.5,
                spiral=False
            )
        elif mode == "aim_extinguisher":
            draw_chad(ctx, 695, 635, scale=1.75, facing="right", pose="aim_extinguisher",
                        expression="angry", prop="backpack_extinguisher", t=t)

# ==============================================================================
# 7. SUPERMARKET WATER & SURVIVAL AISLES + BANK ATMs + TV NEWS + BATHROOM
# ==============================================================================
def _build_supermarket_base(ctx):
    # Perspective supermarket aisle with metal shelving packed with water jugs
    draw_ink_box(ctx, 0, 0, WIDTH, 260, "#E4DFCE", stroke_w=0)
    draw_ink_box(ctx, 0, 260, WIDTH, 820, "#DFD9CA", stroke_w=0)

    # Ceiling fluorescent lights
    for lx in (560, 920, 1280):
        draw_ink_box(ctx, lx - 45, 25, 90, 145, "#FFFDF5", stroke_w=3.0)

    # Left & Right perspective shelving units
    for side in (-1, 1):
        for tier in range(4):
            y0 = 180 + tier * 185
            x_out = 0 if side == -1 else WIDTH
            x_in = 680 if side == -1 else 1240
            ctx.move_to(x_out, y0)
            ctx.line_to(x_in, 340 + tier * 95)
            set_ink(ctx, 6.0)
            ctx.stroke()
            # Water jugs along shelf
            for ji in range(6):
                jf = (ji + 0.5) / 6.0
                jx = x_out + (x_in - x_out) * jf
                jy = y0 + (340 + tier * 95 - y0) * jf - 28
                js = 0.85 * (1.0 - jf * 0.55)
                draw_water_jug(ctx, jx, jy, scale=js)

def draw_env_supermarket(ctx, t, mode="aisle_walk", prog=0.0):
    if mode in ("aisle_walk", "aisle_notes", "pb_drop_4"):
        surf = _get_cached_bg("supermarket_aisle", _build_supermarket_base)
        ctx.set_source_surface(surf, 0, 0)
        ctx.paint()

        if mode == "aisle_walk":
            s = 0.72 + prog * 0.45
            draw_chad(ctx, 960, 615 + prog * 75, scale=s, facing="front", pose="walk", expression="worried", t=t)
            draw_ink_box(ctx, 960 - 95 * s, 685 + prog * 75, 190 * s, 145 * s, "#8E949C", stroke_w=4.0, r=6)

        elif mode == "aisle_notes":
            draw_chad(ctx, 1025, 655, scale=0.95, facing="right", pose="walk", t=t)
            draw_ink_box(ctx, 1110, 695, 145, 135, "#8E949C", stroke_w=4.0, r=6)
            for jr in range(3):
                for jc in range(3):
                    draw_water_jug(ctx, 1135 + jc * 42, 665 - jr * 42, scale=0.58)
            # Left note: "NOTE TO SELF: 1 gallon per person, per day"
            draw_notebook_card(
                ctx, 65, 55, 910, 225,
                title="",
                items=[
                    {"type": "text", "text": "NOTE TO SELF:", "size": 36, "color": "#D42620"},
                    {"type": "text", "text": "1 gallon per person, per day", "size": 42, "color": "#162955", "circle": True},
                ],
                progress=clamp(prog * 2.0, 0.2, 1.0),
                angle_deg=-1.2,
                show_pen=False
            )
            # Right note: "1 💧 = 1 DAY (drink, cook, wash)"
            if prog > 0.28:
                draw_notebook_card(
                    ctx, 1125, 45, 735, 315,
                    title="",
                    items=[
                        {"type": "text", "text": "1 GAL = 1 DAY", "size": 58, "color": "#D42620"},
                        {"type": "text", "text": "drink · cook · wash", "size": 34, "color": "#162955"},
                    ],
                    progress=clamp((prog - 0.28) / 0.72, 0.0, 1.0),
                    angle_deg=1.8
                )

        elif mode == "pb_drop_4":
            draw_ink_box(ctx, 680, 560, 560, 420, "#7C828A", stroke_w=6.0, r=10)
            n_pb = min(4, int(prog * 5.0) + 1)
            for pi in range(n_pb):
                jx = 815 + pi * 95
                draw_ink_box(ctx, jx, 485, 82, 95, "#C68642", stroke_w=3.5, r=8)
                draw_ink_box(ctx, jx - 4, 472, 90, 18, "#C92420", stroke_w=3.0, r=4)

    elif mode == "cart_stack_28":
        # Shot 20: Shopping cart stacking 28 jugs + JUGS tally card + squeaking wheel
        surf = _get_cached_bg("supermarket_aisle", _build_supermarket_base)
        ctx.set_source_surface(surf, 0, 0)
        ctx.paint()
        ctx.rectangle(0, 0, WIDTH, HEIGHT)
        ctx.set_source_rgba(0.85, 0.82, 0.76, 0.55)
        ctx.fill()

        if prog < 0.80:
            sprog = prog / 0.80
            n_jugs = min(28, max(3, int(3 + sprog * 25)))
            cx_c, cy_c = 1020, 415
            # Cart basket & wheels
            for jr in range(min(4, (n_jugs + 3) // 4)):
                for jc in range(4):
                    if jr * 4 + jc < n_jugs:
                        draw_water_jug(ctx, cx_c + 95 + jc * 135, cy_c + 240 - jr * 105, scale=1.35)
            draw_ink_box(ctx, cx_c, cy_c, 680, 325, None, stroke_w=8.0, r=8)
            for wx_w in (cx_c + 85, cx_c + 595):
                ctx.arc(wx_w, cy_c + 525, 58, 0, math.pi * 2)
                ctx.set_source_rgb(0.18, 0.19, 0.20)
                ctx.fill_preserve()
                set_ink(ctx, 4.5)
                ctx.stroke()

            # JUGS tally notebook on top-left
            draw_notebook_card(
                ctx, 75, 65, 535, 325,
                title="JUGS",
                items=[{"type": "tally", "max_count": 28}],
                progress=sprog,
                show_pen=False
            )
        else:
            # Closeup of cart wheel squeaking with vibration arcs & sparks!
            draw_ink_box(ctx, 680, 0, 1240, 460, "#7C828A", stroke_w=8.0)
            wx_s, wy_s = 785, 795
            ctx.arc(wx_s, wy_s, 95, 0, math.pi * 2)
            ctx.set_source_rgb(0.18, 0.19, 0.20)
            ctx.fill_preserve()
            set_ink(ctx, 5.5)
            ctx.stroke()
            draw_sound_wave_arcs(ctx, wx_s - 65, wy_s, math.pi, 0.9, t, count=3, max_r=140, color_hex="#222222")
            draw_sound_wave_arcs(ctx, wx_s + 65, wy_s, 0.0, 0.9, t, count=3, max_r=140, color_hex="#222222")
            draw_notebook_card(ctx, 75, 65, 535, 325, title="JUGS",
                               items=[{"type": "tally", "max_count": 28}], progress=1.0, show_pen=False)

    elif mode == "survival_aisle_radio":
        # Shot 61: Side-scrolling survival shelf with orange hand-crank radios & first-aid kits
        draw_ink_box(ctx, 0, 0, WIDTH, 815, "#DFD9CA", stroke_w=0)
        draw_ink_box(ctx, 0, 815, WIDTH, 265, "#C5BEB2", stroke_w=4.0)
        for sy in (195, 385, 565, 745):
            draw_ink_box(ctx, 0, sy, WIDTH, 22, "#9E9A90", stroke_w=3.5)
        # Orange hand-crank radios on 2nd shelf
        for rx in range(60, WIDTH, 240):
            if rx == 60 + 2 * 240 and prog > 0.55:
                continue  # Chad picks this one up
            draw_ink_box(ctx, rx, 275, 165, 105, "#D97224", stroke_w=4.0, r=10)
        # Red first-aid kits on 3rd shelf left
        for fx in (55, 295):
            draw_ink_box(ctx, fx, 445, 175, 115, "#C92420", stroke_w=4.0, r=12)
            ctx.rectangle(fx + 75, 475, 24, 55)
            ctx.rectangle(fx + 60, 490, 54, 24)
            ctx.set_source_rgb(1, 1, 1)
            ctx.fill()
        # Water jugs on bottom shelf
        for jx in range(85, WIDTH, 145):
            draw_water_jug(ctx, jx, 685, scale=0.95)

        mel_x = 1350 - prog * 320
        draw_chad(ctx, mel_x, 645, scale=1.55, facing="left", pose="walk" if prog < 0.5 else "idle",
                    expression="worried", t=t)
        draw_ink_box(ctx, mel_x - 420, 625, 360, 235, "#787E85", stroke_w=5.0, r=8)

def draw_env_bank_atms(ctx, t, mode="wide", prog=0.0):
    """Shots 40 & 41: ASHFORD SAVINGS exterior with two ATMs and $600 cash withdrawal."""
    ctx.save()
    draw_ink_box(ctx, 0, 0, WIDTH, 865, "#7C8084", stroke_w=0)
    draw_ink_box(ctx, 0, 865, WIDTH, 215, "#686B6E", stroke_w=4.0)

    # Brick lines
    ctx.set_source_rgba(0.25, 0.26, 0.28, 0.45)
    ctx.set_line_width(2.0)
    for by in range(180, 860, 48):
        ctx.move_to(0, by)
        ctx.line_to(WIDTH, by)
    ctx.stroke()

    pan_x = 0.0
    if mode == "pan_withdraw":
        pan_x = -smoothstep(0.25, 0.58, prog) * 580.0 + 280.0
    ctx.translate(pan_x, 0)

    # Top "ASHFORD SAVINGS" sign
    draw_ink_box(ctx, 185, 65, 1380, 115, "#3E4246", stroke_w=5.0)
    ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(58)
    ctx.set_source_rgb(*hex_rgb("#D8DCE0"))
    ctx.move_to(510, 142)
    ctx.show_text("ASHFORD SAVINGS")

    # Left ATM (OUT OF SERVICE)
    for idx, (ax, status) in enumerate([(225, "OUT OF\nSERVICE"), (1095, "WELCOME")]):
        draw_ink_box(ctx, ax, 235, 425, 630, "#4E5256", stroke_w=5.5)
        draw_ink_box(ctx, ax + 55, 325, 315, 215, "#1E2226" if idx == 0 else "#4A5664", stroke_w=4.0)
        ctx.set_font_size(34)
        if idx == 0 and prog > 0.12:
            ctx.set_source_rgb(*hex_rgb("#C93832"))
            ctx.move_to(ax + 85, 420)
            ctx.show_text("OUT OF")
            ctx.move_to(ax + 75, 465)
            ctx.show_text("SERVICE")
        elif idx == 1:
            ctx.set_source_rgb(1, 1, 1)
            if mode == "pan_withdraw" and prog > 0.62:
                ctx.set_font_size(56)
                ctx.move_to(ax + 125, 425)
                ctx.show_text("$600")
                ctx.set_font_size(22)
                ctx.move_to(ax + 95, 470)
                ctx.show_text("TAKE YOUR CASH")
            else:
                ctx.move_to(ax + 95, 445)
                ctx.show_text("WELCOME")

    # Center CLOSED glass door
    draw_ink_box(ctx, 735, 325, 265, 540, "#5E6266", stroke_w=4.5)
    draw_taped_label(ctx, 867, 465, "CLOSED", angle_deg=-6.5, scale=0.78)

    # Hand holding fan of $20 bills at end of Shot 41
    if mode == "pan_withdraw" and prog > 0.72:
        hx, hy = 1310, 920
        for ang in (-0.25, 0.0, 0.25):
            ctx.save()
            ctx.translate(hx, hy)
            ctx.rotate(ang)
            draw_ink_box(ctx, -145, -185, 290, 145, "#72B87E", stroke_w=4.0, r=6, shadow=True)
            ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(34)
            ctx.set_source_rgb(*hex_rgb("#1E4226"))
            ctx.move_to(-125, -135)
            ctx.show_text("20")
            ctx.restore()
        ctx.arc(hx, hy + 25, 68, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
        ctx.fill_preserve()
        set_ink(ctx, 5.0)
        ctx.stroke()
    ctx.restore()

def draw_env_tv_news(ctx, t, mode="anchor", prog=0.0):
    """Shots 56 & 57: CRT TV screen showing Evening News, Weather bumper, and Ashford General Hospital."""
    ctx.save()
    draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#242220", stroke_w=45.0, r=65)
    sx, sy, sw, sh = 75, 65, WIDTH - 150, HEIGHT - 130

    if mode == "anchor":
        if prog < 0.76:
            draw_ink_box(ctx, sx, sy, sw, sh, "#1C3258", stroke_w=6.0, r=42)
            # News Anchor behind desk
            draw_ink_box(ctx, 640, 625, 640, 165, "#C8B288", stroke_w=4.5)
            draw_ink_box(ctx, 880, 465, 160, 185, "#283B66", stroke_w=4.5, r=24)
            ctx.arc(960, 385, 72, 0, math.pi * 2)
            ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
            ctx.fill_preserve()
            set_ink(ctx, 4.5)
            ctx.stroke()
            # Lower third banner
            draw_ink_box(ctx, 195, 765, 1530, 115, "#1E3A68", stroke_w=4.0)
            draw_ink_box(ctx, 195, 725, 115, 42, "#D4A017", stroke_w=3.0)
            ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(42)
            ctx.set_source_rgb(1, 1, 1)
            ctx.move_to(225, 830)
            ctx.show_text("EVENING NEWS")
            if prog > 0.35:
                draw_ink_box(ctx, 1280, 235, 420, 265, "#DCE4EC", stroke_w=4.5)
                draw_ink_box(ctx, 1340, 275, 300, 185, "#9EA8B2", stroke_w=3.5)
        else:
            # Sunny "WEATHER NEXT" bumper
            draw_ink_box(ctx, sx, sy, sw, sh, "#D49B4B", stroke_w=6.0, r=42)
            ctx.arc(735, 485, 115, 0, math.pi * 2)
            ctx.set_source_rgb(*hex_rgb("#F7D436"))
            ctx.fill_preserve()
            set_ink(ctx, 4.5)
            ctx.stroke()
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(68)
            ctx.set_source_rgb(*hex_rgb("#181615"))
            ctx.move_to(985, 485)
            ctx.show_text("WEATHER")
            ctx.move_to(985, 575)
            ctx.show_text("NEXT")

    elif mode == "hospital":
        draw_ink_box(ctx, sx, sy, sw, sh, "#4E5868", stroke_w=6.0, r=42)
        # ASHFORD GENERAL hospital building
        hx, hy, hw, hh = 295, 135, 1330, 695
        draw_ink_box(ctx, hx, hy, hw, hh, "#C8C2B4", stroke_w=5.0)
        for r in range(3):
            for c in range(8):
                wcol = "#E8D078" if (r + c) % 3 == 0 else "#68829E"
                draw_ink_box(ctx, hx + 65 + c * 155, hy + 55 + r * 115, 85, 68, wcol, stroke_w=3.0)
        draw_ink_box(ctx, hx + 345, hy + 415, 640, 75, "#ECEAE4", stroke_w=4.0)
        ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(38)
        ctx.set_source_rgb(*hex_rgb("#1B1918"))
        ctx.move_to(hx + 435, hy + 468)
        ctx.show_text("+ ASHFORD GENERAL")

        # Glass entrance + rolling metal shutter doors closing
        shutter_h = 265 * clamp(prog * 2.2, 0.2, 1.0)
        draw_ink_box(ctx, hx + 355, hy + 545, 620, 285, "#687E8E", stroke_w=4.0)
        draw_ink_box(ctx, hx + 355, hy + 545, 620, shutter_h, "#8E949A", stroke_w=4.0)

        # Police car on left with flashing blue/red roof light
        draw_ink_box(ctx, 215, 735, 295, 95, "#DFDDD6", stroke_w=4.0, r=12)
        draw_ink_box(ctx, 295, 705, 65, 28, "#2858D8" if int(t * 8) % 2 == 0 else "#D82828", stroke_w=3.0)

        # Reporter in foreground left when prog > 0.58
        if prog > 0.58:
            draw_ink_box(ctx, 455, 765, 265, 250, "#6E3838", stroke_w=4.5, r=28)
            ctx.arc(587, 635, 88, 0, math.pi * 2)
            ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
            ctx.fill_preserve()
            set_ink(ctx, 4.5)
            ctx.stroke()

        # Breaking news lower third banner
        if prog > 0.25:
            draw_ink_box(ctx, 135, 755, 1650, 75, "#DFDDD6", stroke_w=4.0)
            draw_ink_box(ctx, 135, 710, 225, 45, "#C92420", stroke_w=3.5)
            ctx.set_font_size(34)
            ctx.set_source_rgb(*hex_rgb("#8C1D1A"))
            msg = "ISOLATED INCIDENT" if prog > 0.58 else "HOSPITAL CLOSES AFTER PATIENTS ATTACK STAFF"
            ctx.move_to(165, 805)
            ctx.show_text(msg)
    ctx.restore()

def draw_env_bathroom_and_heater(ctx, t, mode="tub_fill", prog=0.0):
    """Shots 67, 68, 70, 71: Bathtub filling (+40 GAL, treat it first!) & Water Heater Closet."""
    ctx.save()
    if mode in ("tub_fill", "tub_treat"):
        # Tiled bathroom with pedestal sink, night window, and white bathtub filling with blue water
        draw_ink_box(ctx, 0, 0, WIDTH, 785, "#D6CFB4", stroke_w=0)
        draw_ink_box(ctx, 0, 785, WIDTH, 295, "#C8C2B0", stroke_w=4.0)
        for gx in range(0, WIDTH, 145):
            ctx.move_to(gx, 0)
            ctx.line_to(gx, 785)
        for gy in range(0, 785, 115):
            ctx.move_to(0, gy)
            ctx.line_to(WIDTH, gy)
        ctx.set_source_rgba(0.35, 0.33, 0.28, 0.35)
        ctx.set_line_width(2.0)
        ctx.stroke()

        # Night window & Pedestal Sink on left
        draw_ink_box(ctx, 510, 125, 225, 365, "#1E2B48", stroke_w=5.0)
        draw_ink_box(ctx, 65, 515, 425, 135, "#EAE8E2", stroke_w=4.5, r=12)
        draw_ink_box(ctx, 165, 650, 145, 430, "#DFDDD6", stroke_w=4.5)

        # Bathtub on right with dashed blue water volume cross-section
        tx, ty, tw, th = 825, 475, 920, 385
        draw_ink_box(ctx, tx, ty, tw, th, "#EAE8E2", stroke_w=5.0, r=12)
        w_h = (th - 65) * (clamp(prog * 1.35, 0.25, 1.0) if mode == "tub_fill" else 0.92)
        draw_ink_box(ctx, tx + 24, ty + th - w_h - 24, tw - 48, w_h, "#6BA8E5", stroke_w=0, r=8)
        ctx.save()
        ctx.set_dash([12.0, 10.0])
        draw_ink_box(ctx, tx + 24, ty + th - w_h - 24, tw - 48, w_h, None, stroke_w=3.5)
        ctx.restore()

        if mode == "tub_fill":
            # Running water stream from faucet + "+40 GAL" taped banner
            ctx.move_to(tx + 55, ty - 25)
            ctx.line_to(tx + 75, ty + th - w_h)
            ctx.set_source_rgba(0.82, 0.94, 1.0, 0.85)
            ctx.set_line_width(18.0)
            ctx.stroke()
            if prog > 0.55:
                draw_taped_label(ctx, 1435, 425, "+40 GAL", color="#2258A8", angle_deg=-5.0, scale=1.15)
        else:
            if prog > 0.35:
                draw_taped_label(ctx, 1285, 445, "treat it first!", color="#D42620", angle_deg=-4.5, scale=1.25)

    elif mode in ("heater_closet", "heater_drain"):
        # Hallway utility closet with white 50 GAL cylindrical water heater
        draw_ink_box(ctx, 0, 0, WIDTH, 815, "#C8AD88", stroke_w=0)
        draw_ink_box(ctx, 0, 815, WIDTH, 265, "#A67C52", stroke_w=4.0)
        draw_ink_box(ctx, 560, 45, 580, 775, "#8E7254", stroke_w=5.5)

        # Cylindrical white water heater tank
        hx, hy, hw, hh = 645, 225, 295, 565
        draw_ink_box(ctx, hx, hy, hw, hh, "#DFDDD6", stroke_w=5.0, r=28, shadow=True)
        # Open closet door on right
        ctx.move_to(1140, 45)
        ctx.line_to(1465, 15)
        ctx.line_to(1465, 925)
        ctx.line_to(1140, 815)
        ctx.close_path()
        ctx.set_source_rgb(*hex_rgb("#AD8255"))
        ctx.fill_preserve()
        set_ink(ctx, 5.0)
        ctx.stroke()

        if mode == "heater_closet":
            if prog > 0.25 and prog < 0.65:
                draw_taped_label(ctx, 845, 365, "OFF", sub_text="power or gas", color="#D42620", angle_deg=-3.5)
            elif prog >= 0.65:
                draw_taped_label(ctx, 685, 295, "COLD: shut", color="#D42620", angle_deg=-4.5)
        else:
            # Drain hose into grey bucket at bottom + "hot tap open"
            draw_ink_box(ctx, hx + 275, 655, 135, 145, "#B4B2AC", stroke_w=4.0, r=8)
            draw_taped_label(ctx, 1025, 445, "hot tap open", color="#D42620", angle_deg=-3.5)
    ctx.restore()

# ==============================================================================
# 8. 3RD / 4TH FLOOR HALLWAY, STAIRWELL & PEEPHOLE SEQUENCE
# ==============================================================================
def _build_hallway_base(ctx, is_dark=False):
    mul = 0.28 if is_dark else 1.0
    def _c(h):
        r, g, b = hex_rgb(h)
        return (r * mul, g * mul, b * mul)

    # Perspective hallway walls, ceiling, wainscoting, runner rug & stairs
    draw_ink_box(ctx, 0, 0, WIDTH, 680, "#DFD3BD" if not is_dark else "#2B2825", stroke_w=0)
    draw_ink_box(ctx, 0, 680, WIDTH, 400, "#9E7852" if not is_dark else "#241C16", stroke_w=4.0)

    # Patterned runner rug in center
    ctx.move_to(745, 705)
    ctx.line_to(1175, 705)
    ctx.line_to(1385, HEIGHT)
    ctx.line_to(515, HEIGHT)
    ctx.close_path()
    ctx.set_source_rgb(*_c("#8E7868"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()

    # Background stairs going up & banister
    for st in range(10):
        draw_ink_box(ctx, 985, 345 + st * 34, 175, 34, "#8E6844" if not is_dark else "#281E15", stroke_w=3.0)
    draw_ink_box(ctx, 920, 480, 26, 220, "#6E4E32" if not is_dark else "#201710", stroke_w=3.5)

    # Left & Right apartment doors (3A on left, Chad's 3B on right)
    for dx_d, dw_d, dy_d, dh_d in [(75, 295, 25, 925), (605, 95, 225, 535), (1215, 95, 225, 535), (1495, 325, 25, 925)]:
        draw_ink_box(ctx, dx_d, dy_d, dw_d, dh_d, "#7E5B3B" if not is_dark else "#261C13", stroke_w=4.5)

    # Ceiling dome light & smoke detector
    ctx.arc(960, 95, 58, 0, math.pi * 2)
    ctx.set_source_rgb(*_c("#F5E8C8"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()

def draw_env_hallway_stairs(ctx, t, mode="trips", prog=0.0):
    ctx.save()
    if mode == "roof_access_stairs":
        # Shot 27: Peeling green/grey concrete stairwell up to grey steel ROOF ACCESS door
        draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#9BA494", stroke_w=0)
        # Concrete stairs in bottom-right
        for st in range(6):
            draw_ink_box(ctx, 745 - st * 18, 495 + st * 95, 1180, 95, "#8E8A82", stroke_w=4.5)
        # Iron handrail on left of stairs
        ctx.move_to(745, 365)
        ctx.line_to(485, HEIGHT)
        set_ink(ctx, 12.0)
        ctx.stroke()

        # Grey steel fire door with crash bar + red ROOF ACCESS sign + red alarm bell
        dx_r, dy_r, dw_r, dh_r = 985, 45, 425, 450
        draw_ink_box(ctx, dx_r, dy_r, dw_r, dh_r, "#7C8084", stroke_w=5.5)
        draw_ink_box(ctx, dx_r + 35, dy_r + 245, dw_r - 70, 28, "#9EA4AA", stroke_w=3.5, r=6)
        # Red sign on door
        draw_ink_box(ctx, dx_r + 95, dy_r + 95, 235, 115, "#C92420", stroke_w=3.5)
        if prog > 0.55:
            ctx.select_font_face("Arial Black", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(24)
            ctx.set_source_rgb(1, 1, 1)
            ctx.move_to(dx_r + 115, dy_r + 145)
            ctx.show_text("ROOF ACCESS")
            if prog > 0.75:
                ctx.set_font_size(16)
                ctx.move_to(dx_r + 112, dy_r + 182)
                ctx.show_text("ALARM WILL SOUND")
        # Red alarm bell box on right wall
        draw_ink_box(ctx, dx_r + dw_r + 55, dy_r + 65, 95, 115, "#B86858", stroke_w=4.0, r=6)
        ctx.arc(dx_r + dw_r + 102, dy_r + 122, 28, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#D42620"))
        ctx.fill_preserve()
        set_ink(ctx, 3.5)
        ctx.stroke()

        if prog < 0.45:
            ctx.arc(415, 765, 44, 0, math.pi * 2)
            ctx.set_source_rgb(*hex_rgb("#F5C838"))
            ctx.fill_preserve()
            set_ink(ctx, 3.5)
            ctx.stroke()
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(46)
            ctx.set_source_rgb(*hex_rgb("#C92420"))
            ctx.move_to(398, 782)
            ctx.show_text("4")
            ctx.move_to(485, 778)
            ctx.show_text("top floor")
        ctx.restore()
        return

    if mode == "peephole_sequence":
        # Shot 98: Circular fisheye peephole sequence of zombie neighbor
        draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#020203", stroke_w=0)
        if 0.45 <= prog < 0.65:
            # Interior floor view: 4 grey fingers with soil-blackened nails reaching under door!
            draw_ink_box(ctx, 0, 0, WIDTH, 635, "#3E3024", stroke_w=6.0)
            draw_ink_box(ctx, 0, 635, WIDTH, 445, "#281E16", stroke_w=4.0)
            draw_ink_box(ctx, 380, 695, 1160, 325, "#5C4E3E", stroke_w=5.0, r=12)
            for fi in range(4):
                fx = 825 + fi * 68
                draw_ink_box(ctx, fx, 635, 38, 85, "#7C827E", stroke_w=3.5, r=10)
                draw_ink_box(ctx, fx + 4, 695, 30, 22, "#121010", stroke_w=2.0, r=4)
            ctx.restore()
            return

        # Circular peephole fisheye viewport
        ctx.save()
        ctx.arc(WIDTH * 0.5, HEIGHT * 0.5, 495, 0, math.pi * 2)
        ctx.clip()

        surf = _get_cached_bg("hallway_dark", lambda c: _build_hallway_base(c, is_dark=True))
        ctx.set_source_surface(surf, 0, 0)
        ctx.paint()

        if prog < 0.25:
            # Neighbor standing in smoky hallway facing away in straw garden hat
            draw_neighbor(ctx, 945, 785, scale=1.55, is_zombie=True, silhouette=True, t=t)
        elif prog < 0.45:
            # Closeup of zombie neighbor's grey arm with bloody bite chunk missing from wrist!
            ctx.move_to(WIDTH * 0.5 + 480, 680)
            ctx.line_to(780, 495)
            ctx.set_source_rgb(*hex_rgb("#8C928E"))
            ctx.set_line_width(145.0)
            ctx.stroke()
            # Bite chunk semicircle on lower wrist + tooth marks
            ctx.arc(1065, 655, 48, 0, math.pi * 2)
            ctx.set_source_rgb(*hex_rgb("#3A1614"))
            ctx.fill()
            # 4 fingers with black soil nails on left
            for fi in range(4):
                fy = 425 + fi * 38
                draw_ink_box(ctx, 565, fy, 215, 34, "#8C928E", stroke_w=4.0, r=14)
                draw_ink_box(ctx, 565, fy + 4, 28, 26, "#141210", stroke_w=2.0, r=6)
        elif prog < 0.80:
            # Silhouette tilting head 38 degrees to the right
            tilt = smoothstep(0.65, 0.78, prog) * 38.0
            draw_neighbor(ctx, 960, 745, scale=1.85, is_zombie=True, head_tilt_deg=tilt, silhouette=True, t=t)
        else:
            # Extreme fisheye lunge: grey zombie face with blank white eyes & mustache right against peephole!
            draw_neighbor(ctx, 960, 885, scale=3.15, is_zombie=True, head_tilt_deg=26.0, silhouette=False, t=t)

        ctx.restore()
        # Peephole glass rim reflection arc
        ctx.arc(WIDTH * 0.5, HEIGHT * 0.5, 495, 0, math.pi * 2)
        set_ink(ctx, 18.0)
        ctx.stroke()
        ctx.arc(WIDTH * 0.5, HEIGHT * 0.5, 455, math.pi * 1.08, math.pi * 1.38)
        ctx.set_source_rgba(0.85, 0.90, 0.95, 0.35)
        ctx.set_line_width(10.0)
        ctx.stroke()
        ctx.restore()
        return

    # Standard Hallway shots
    is_dark = mode not in ("trips", "almost_knock_slide_note") or (mode == "trips" and prog > 0.78)
    surf = _get_cached_bg("hallway_dark" if is_dark else "hallway_day",
                          lambda c: _build_hallway_base(c, is_dark=is_dark))
    ctx.set_source_surface(surf, 0, 0)
    ctx.paint()

    if mode == "trips":
        # Open door on right showing growing pile of water jugs + onion-skinned Chad + TRIP 1..11 notebook
        trip_num = min(11, max(1, int(1 + prog * 10.8)))
        draw_ink_box(ctx, 1215, 225, 95, 535, "#323842", stroke_w=4.0)
        for jr in range(min(5, (trip_num + 1) // 2)):
            draw_water_jug(ctx, 1255, 725 - jr * 48, scale=0.65)

        if trip_num < 11:
            # Ghosted onion-skin trail of Chad walking from stairs into door
            for gi, gx, ga in [(0, 845, 0.28), (1, 995, 0.55), (2, 1155, 0.95)]:
                draw_chad(ctx, gx, 565, scale=1.08, facing="right", pose="walk", prop="jugs_2", t=t + gi * 0.3, alpha=ga)
        else:
            draw_chad(ctx, 1025, 585, scale=1.25, facing="right", pose="tremble_jugs",
                        expression="panting", prop="jugs_2", t=t)

        draw_notebook_card(
            ctx, 95, 75, 485, 295,
            title="TRIP",
            items=[{"type": "tally", "max_count": 11, "denom": "/11"}],
            progress=prog,
            show_pen=False
        )

    elif mode == "look_up":
        draw_chad(ctx, 1045, 565, scale=1.22, facing="left", pose="idle", expression="worried", prop="jug_1", t=t)

    elif mode == "almost_knock_slide_note":
        if prog < 0.55:
            draw_chad(ctx, 945, 565, scale=1.35, facing="left", pose="idle", expression="worried", t=t)
        else:
            # Low-angle floor shot sliding white note under door 3A
            draw_ink_box(ctx, 0, 0, WIDTH, 685, "#6E5238", stroke_w=5.0)
            draw_ink_box(ctx, 0, 685, WIDTH, 395, "#8E6E4E", stroke_w=4.0)
            nx_s = 1380 - smoothstep(0.55, 0.92, prog) * 650
            draw_ink_box(ctx, nx_s, 675, 195, 65, "#F4F1EA", stroke_w=3.5)

    elif mode == "lock_click_10pm":
        draw_slanted_stamp_banner(ctx, "10:00 PM", x=115, y=95, angle_deg=-3.5, scale=0.78)
        if prog > 0.55:
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(48)
            ctx.set_source_rgb(*hex_rgb("#F0A898"))
            ctx.move_to(565, 545)
            ctx.show_text("CLICK.")
            ctx.move_to(565, 605)
            ctx.show_text("CLICK.")

    elif mode == "red_under_doors_cut":
        doors_glow = [(285, 785, 0.25), (635, 745, 0.45), (1245, 745, 0.65), (1545, 785, 0.85)]
        for gx, gy, t_cut in doors_glow:
            if prog < t_cut:
                pat = cairo.RadialGradient(gx, gy, 10, gx, gy, 145)
                pat.add_color_stop_rgba(0.0, 0.95, 0.12, 0.12, 0.78)
                pat.add_color_stop_rgba(1.0, 0.95, 0.12, 0.12, 0.0)
                ctx.set_source(pat)
                ctx.paint()

    elif mode == "smoke_rising":
        # Orange fire glow at bottom of stairs + snaking grey smoke column rising to ceiling detector
        pat = cairo.RadialGradient(910, 665, 20, 910, 665, 420)
        pat.add_color_stop_rgba(0.0, 1.0, 0.55, 0.15, 0.75)
        pat.add_color_stop_rgba(1.0, 1.0, 0.35, 0.08, 0.0)
        ctx.set_source(pat)
        ctx.paint()
        n_puffs = int(6 + prog * 14)
        for pi in range(n_puffs):
            pf = pi / 20.0
            px_s = 910 + math.sin(pf * 8.0 + t * 2.0) * 95
            py_s = 640 - pf * 520
            ctx.arc(px_s, py_s, 36 + pf * 85, 0, math.pi * 2)
            ctx.set_source_rgba(0.45, 0.46, 0.48, 0.38)
            ctx.fill()

    elif mode == "extinguisher_fight":
        # Shot 104: Blasting white powder at zombie neighbor, then swinging extinguisher 3x into his temple!
        if prog < 0.36:
            draw_neighbor(ctx, 960, 565, scale=1.45, is_zombie=True, head_tilt_deg=14.0, t=t)
            if prog > 0.08:
                # White powder jet from bottom-left + billowing white cloud
                ctx.move_to(0, 685)
                ctx.line_to(960, 425)
                ctx.set_source_rgba(0.96, 0.97, 0.98, 0.88)
                ctx.set_line_width(68.0)
                ctx.stroke()
                for ci in range(8):
                    ang = ci * 0.8 + t * 3.0
                    ctx.arc(960 + math.cos(ang) * 125, 465 + math.sin(ang) * 95, 115, 0, math.pi * 2)
                    ctx.set_source_rgba(0.95, 0.96, 0.98, 0.65)
                    ctx.fill()
        elif prog < 0.62:
            # Closeup of zombie neighbor lunging through smoke snapping teeth
            draw_neighbor(ctx, 960, 785, scale=2.45, is_zombie=True, head_tilt_deg=-12.0, t=t)
        else:
            # 3 swings of the red fire extinguisher into his temple (like frame_520.jpg!)
            swing_phase = (prog - 0.62) / 0.38
            tilt = 28.0 if swing_phase > 0.75 else (-8.0 if int(swing_phase * 6) % 2 == 0 else 12.0)
            draw_neighbor(ctx, 1165, 765, scale=2.25, is_zombie=True, head_tilt_deg=tilt, t=t)
            # Long cartoon arms swinging extinguisher from bottom-left
            ctx.save()
            ctx.translate(480, 480)
            ctx.rotate(math.sin(swing_phase * math.pi * 6.0) * 0.35 - 0.55)
            draw_ink_box(ctx, -600, -95, 920, 68, "#4A5058", stroke_w=6.0)
            draw_ink_box(ctx, -600, 15, 920, 68, "#4A5058", stroke_w=6.0)
            draw_fire_extinguisher_prop(ctx, 320, -25, scale=2.65, angle_deg=35.0)
            ctx.restore()

    elif mode == "zombie_falls_stairs":
        # Zombie neighbor tumbles down stairs into orange fire below while Chad stands at top
        draw_fire_plume(ctx, 680, 745, 260, 165, t, seed=11)
        if prog < 0.42:
            zy = 485 + (prog / 0.42) * 320
            zx = 1285 - (prog / 0.42) * 580
            ctx.save()
            ctx.translate(zx, zy)
            ctx.rotate(prog * 8.0)
            draw_neighbor(ctx, 0, 0, scale=0.85, is_zombie=True, t=t)
            ctx.restore()
        draw_chad(ctx, 1345, 425, scale=0.82, facing="left", pose="idle", prop="backpack_extinguisher", t=t)

    elif mode == "fourth_floor_grab":
        if 0.32 <= prog < 0.52:
            # Closeup of 4 cold grey zombie fingers with yellowed nails gripping blue backpack strap!
            draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#0B0E18", stroke_w=0)
            ctx.save()
            ctx.translate(960, 580)
            ctx.rotate(-0.12)
            draw_ink_box(ctx, -980, -45, 1960, 90, "#243268", stroke_w=5.0)
            ctx.restore()
            for fi in range(4):
                fx = 745 + fi * 95
                draw_ink_box(ctx, fx, 345, 72, 235, "#7C827E", stroke_w=4.5, r=24)
                draw_ink_box(ctx, fx + 12, 515, 48, 52, "#9E9258", stroke_w=3.0, r=10)
        else:
            # 4th-floor landing: zombie hand grabs Chad's backpack out of dark doorway on left; jug bounces down
            draw_chad(ctx, 845, 585, scale=1.55, facing="right", pose="walk",
                        expression="shocked", prop="backpack_extinguisher", t=t)
            if prog < 0.65:
                ctx.move_to(265, 525)
                ctx.line_to(725, 625)
                ctx.set_source_rgb(*hex_rgb("#68706C"))
                ctx.set_line_width(34.0)
                ctx.stroke()
            else:
                # 1-gallon water jug bouncing down stairs
                draw_water_jug(ctx, 885 - (prog - 0.65) * 450, 885 + (prog - 0.65) * 280, scale=0.95)

    elif mode == "shoulder_hit_roof_door":
        # Top of stairs: Chad hits ROOF ACCESS door open; burning skyline outside + flashing red alarm
        draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#3A423C", stroke_w=0)
        for st in range(5):
            draw_ink_box(ctx, 645, 585 + st * 95, 980, 95, "#4E4C48", stroke_w=4.5)
        # Open doorway showing burning skyline
        draw_ink_box(ctx, 785, 45, 425, 540, "#2B1814", stroke_w=5.5)
        if prog > 0.35:
            draw_fire_plume(ctx, 835, 485, 295, 195, t, seed=5)
        draw_chad(ctx, 1025, 395, scale=1.35, facing="back", pose="idle", prop="backpack_extinguisher", t=t)
        # Flashing red alarm bell on right wall
        ctx.arc(1275, 145, 38, 0, math.pi * 2)
        ctx.set_source_rgb(*hex_rgb("#FF2420"))
        ctx.fill_preserve()
        set_ink(ctx, 4.0)
        ctx.stroke()
    ctx.restore()

# ==============================================================================
# 9. ROOFTOP (Flash-forward, Door Wedging, Slumped Count, Nuclear Finale!)
# ==============================================================================
def draw_env_rooftop(ctx, t, mode="flashforward", prog=0.0):
    ctx.save()
    if mode == "nuclear_finale":
        if prog > 0.82:
            # Final hard cut to black at 589.9s
            draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#000000", stroke_w=0)
            ctx.restore()
            return

        # Wide rooftop shot (Penthouse door on left, Water Tower on right, Nuclear Mushroom Cloud!)
        draw_ink_box(ctx, 0, 0, WIDTH, 615, "#1E283D", stroke_w=0)
        # Distant skyline + burning building on right
        for bx_r, bw_r, bh_r in [(540, 110, 160), (720, 95, 130), (1430, 260, 310), (1760, 140, 180)]:
            draw_ink_box(ctx, bx_r, 560 - bh_r, bw_r, bh_r, "#2B2224", stroke_w=3.5)
        draw_fire_plume(ctx, 1450, 485, 220, 145, t, seed=9)

        # Nuclear Shockwave Dome & Towering Mushroom Cloud behind skyline (prog > 0.14)
        if prog > 0.14:
            eprog = (prog - 0.14) / 0.68
            cx_n, cy_n = 1385, 495
            if eprog < 0.35:
                # Expanding white-blue hemispherical shockwave dome
                rad_d = 180 + (eprog / 0.35) * 950
                ctx.arc(cx_n, cy_n, rad_d, math.pi, 0)
                ctx.set_source_rgba(0.88, 0.94, 1.0, 0.65 * (1.0 - eprog / 0.35))
                ctx.fill_preserve()
                ctx.set_source_rgba(1.0, 1.0, 1.0, 0.9)
                ctx.set_line_width(8.0)
                ctx.stroke()

            # Rising Mushroom Cloud stem & cap
            cap_y = cy_n - 85 - min(1.0, eprog * 1.6) * 215
            # Stem
            draw_ink_box(ctx, cx_n - 75, cap_y + 45, 150, cy_n - cap_y, "#E59848", stroke_w=4.0)
            # Mushroom cap
            ctx.save()
            ctx.translate(cx_n, cap_y)
            ctx.scale(1.85, 0.95)
            ctx.arc(0, 0, 145, 0, math.pi * 2)
            ctx.set_source_rgb(*hex_rgb("#F7B862"))
            ctx.fill_preserve()
            set_ink(ctx, 4.5)
            ctx.stroke()
            ctx.restore()

        # Tar roof deck & puddles
        draw_ink_box(ctx, 0, 560, WIDTH, 520, "#3C4654", stroke_w=5.0)
        for px_p, py_p, pw_p in [(845, 625, 210), (1325, 665, 185), (1055, 895, 285)]:
            ctx.save()
            ctx.translate(px_p, py_p)
            ctx.scale(2.4, 0.35)
            ctx.arc(0, 0, pw_p * 0.4, 0, math.pi * 2)
            ctx.set_source_rgba(0.22, 0.32, 0.48, 0.85)
            ctx.fill_preserve()
            set_ink(ctx, 2.5)
            ctx.stroke()
            ctx.restore()

        # Cylindrical Rusty Water Tower on right
        draw_ink_box(ctx, 1110, 310, 185, 225, "#6E655F", stroke_w=4.5)
        ctx.move_to(1095, 310)
        ctx.line_to(1202, 265)
        ctx.line_to(1310, 310)
        ctx.close_path()
        ctx.fill_preserve()
        set_ink(ctx, 4.5)
        ctx.stroke()
        for lx_t in (1125, 1175, 1235, 1280):
            draw_ink_box(ctx, lx_t, 535, 14, 95, "#4E4A48", stroke_w=3.0)

        # Brick Penthouse Doorway on left with wedged extinguisher
        draw_ink_box(ctx, 55, 235, 485, 495, "#684238", stroke_w=5.0)
        draw_ink_box(ctx, 335, 325, 145, 375, "#5A5E64", stroke_w=4.5)
        draw_fire_extinguisher_prop(ctx, 515, 645, scale=0.82, angle_deg=-22.0)
        draw_water_jug(ctx, 595, 695, scale=0.68)

        # Chad standing by door looking right at the nuclear mushroom cloud!
        draw_chad(ctx, 655, 595, scale=0.98, facing="right", pose="phone_look",
                    expression="shocked", prop="phone", t=t)
        ctx.restore()
        return

    # Closeup Rooftop Angle (Penthouse brick wall on right, burning skyline on left)
    draw_ink_box(ctx, 0, 0, WIDTH, 560, "#1A1F2E", stroke_w=0)
    draw_ink_box(ctx, 0, 185, 295, 320, "#4E261C", stroke_w=4.0)
    draw_fire_plume(ctx, 15, 345, 265, 165, t, seed=3)

    # Roof floor & puddles on left
    draw_ink_box(ctx, 0, 510, WIDTH, 570, "#424652", stroke_w=5.0)
    for px_p, py_p in [(415, 615), (715, 565), (215, 895)]:
        ctx.save()
        ctx.translate(px_p, py_p)
        ctx.scale(2.5, 0.35)
        ctx.arc(0, 0, 85, 0, math.pi * 2)
        ctx.set_source_rgba(0.24, 0.32, 0.45, 0.85)
        ctx.fill_preserve()
        set_ink(ctx, 2.5)
        ctx.stroke()
        ctx.restore()

    # Brick Penthouse Wall & Grey Metal Door on right
    ctx.move_to(885, 85)
    ctx.line_to(WIDTH, 0)
    ctx.line_to(WIDTH, HEIGHT)
    ctx.line_to(885, 765)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#5E2E28"))
    ctx.fill_preserve()
    set_ink(ctx, 5.5)
    ctx.stroke()

    # Metal Roof Door
    dx_m, dy_m, dw_m, dh_m = 1085, 125, 415, 845
    draw_ink_box(ctx, dx_m, dy_m, dw_m, dh_m, "#4E4D50", stroke_w=6.0)
    # Lever handle
    draw_ink_box(ctx, dx_m + 295, dy_m + 465, 115, 28, "#38383A", stroke_w=4.0, r=8)

    if mode == "flashforward":
        draw_fire_extinguisher_prop(ctx, 1465, 895, scale=1.28)
        draw_chad(ctx, 1185, 715, scale=1.58, facing="left", pose="brace_door",
                    expression="shocked", t=t)
        if prog < 0.72:
            draw_slanted_stamp_banner(ctx, "6 DAYS FROM NOW", x=110, y=85, angle_deg=-2.2)

    elif mode == "wedge_door":
        # Extinguisher wedged tightly under door handle + dent marks from zombie fists inside!
        draw_fire_extinguisher_prop(ctx, 1445, 765, scale=1.55, angle_deg=-14.0)
        draw_chad(ctx, 1185, 715, scale=1.58, facing="left", pose="brace_door",
                    expression="grimace_teeth", t=t)
        if prog > 0.48:
            # Dent bulges on metal door panel
            for dy_d in (285, 415):
                ctx.arc(dx_m + 295, dy_d, 28, 0, math.pi * 2)
                ctx.set_source_rgba(0.75, 0.75, 0.78, 0.65)
                ctx.fill_preserve()
                set_ink(ctx, 3.0)
                ctx.stroke()

    elif mode == "slumped_count":
        draw_fire_extinguisher_prop(ctx, 1445, 765, scale=1.55, angle_deg=-14.0)
        # Ripped backpack & 1 remaining water jug on floor beside Chad
        draw_ink_box(ctx, 695, 785, 95, 115, "#28364A", stroke_w=4.0, r=18)
        draw_water_jug(ctx, 845, 835, scale=0.98)
        draw_chad(ctx, 1085, 765, scale=1.58, facing="left", pose="sit_chair",
                    expression="worried", prop="phone" if prog > 0.62 else None, t=t)

        if 0.12 < prog < 0.52:
            draw_notebook_card(
                ctx, 65, 95, 640, 445,
                title="",
                items=[
                    {"type": "bar_row", "icon": "water", "label": "WATER", "val": "1 gal", "frac": 0.04, "color": "#3B8EEA"},
                    {"type": "bar_row", "icon": "food", "label": "FOOD", "val": "3 days", "frac": 0.12, "color": "#E8922D"},
                ],
                progress=(prog - 0.12) / 0.35
            )
        elif prog >= 0.65:
            # 4% battery icon flashing red above Chad
            draw_ink_box(ctx, 1195, 195, 155, 68, "#221E20", stroke_w=4.0, r=8)
            draw_ink_box(ctx, 1205, 205, 28, 48, "#E52222", stroke_w=0, r=4)
            ctx.select_font_face("Segoe Print", cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(46)
            ctx.set_source_rgb(*hex_rgb("#E52222"))
            ctx.move_to(1225, 325)
            ctx.show_text("4%")
    ctx.restore()
