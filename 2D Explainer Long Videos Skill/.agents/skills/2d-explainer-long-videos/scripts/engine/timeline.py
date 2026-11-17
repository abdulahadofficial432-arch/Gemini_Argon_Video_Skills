import math
import cairo
from engine.primitives import (
    WIDTH, HEIGHT, hex_rgb, set_ink, clamp, smoothstep,
    apply_camera, draw_vignette, draw_red_alarm_pulse,
    draw_ink_box, draw_speech_bubble
)

def lerp(a, b, t):
    return a + (b - a) * t
from engine.characters import draw_chad, draw_water_jug
from engine.overlays import (
    draw_notebook_card, draw_sticky_note_pad, draw_taped_label,
    draw_october_calendar, draw_smartphone_alert
)
from engine.diagrams import (
    draw_county_website_phone, draw_phone_call_hangup, draw_deleted_videos_grid,
    draw_pixel_macro_ew04, draw_email_printout, draw_ellen_ward_board,
    draw_door_cross_section, draw_strike_plate_ruler, draw_calorie_tube_overlay,
    draw_pantry_receipt, draw_water_stack_120_diagram, draw_backpack_xray,
    draw_calendar_6_summary, draw_card_terminal_split, draw_cart_topdown,
    draw_power_out_atms, draw_fridge_4h_diagram, draw_water_heater_50gal_diagram,
    draw_folded_note_doormat, draw_hospital_phone_video
)
from engine.environments import (
    draw_env_brownstone_exterior, draw_env_apocalypse_street,
    draw_env_bedroom, draw_env_window_garden
)
from engine.environments_part2 import (
    draw_env_living_room, draw_env_front_door, draw_env_supermarket,
    draw_env_bank_atms, draw_env_tv_news, draw_env_bathroom_and_heater,
    draw_env_hallway_stairs, draw_env_rooftop
)

# ==============================================================================
# COMPOSITE SCENE HELPERS FOR MULTI-LAYER SHOTS
# ==============================================================================
def _shot_window_garden_month_droplets(ctx, t, prog):
    """Shot 23 (104.5-108.8s): Window garden POV with Chad & cart + 30 GAL = 1 MONTH + WATER bar."""
    draw_env_window_garden(ctx, t, mode="chad_cart", prog=prog)
    if prog < 0.58:
        draw_notebook_card(
            ctx, 75, 45, 585, 515,
            title="",
            items=[
                {"type": "text", "text": "30 GAL = 1 MONTH", "size": 42, "color": "#162955"},
                {"type": "month_droplets"},
            ],
            progress=prog / 0.55,
            angle_deg=-1.5
        )
    else:
        draw_notebook_card(
            ctx, 68, 45, 655, 295,
            title="6 DAYS LEFT", sub_title="FRI",
            items=[
                {"type": "bar_row", "icon": "water", "label": "WATER", "val": "2 gal",
                 "new_val": "30 gal", "frac": 0.96, "color": "#3B8EEA"},
            ],
            progress=(prog - 0.58) / 0.42,
            angle_deg=-1.2
        )

def _shot_sticky_survival_rule(ctx, t, prog):
    """Shot 17 (79.8-86.8s): Yellow sticky note pad on dark background ('3 MIN AIR / 3 DAYS WATER / 3 WEEKS FOOD')."""
    draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#141518", stroke_w=0)
    draw_sticky_note_pad(
        ctx, 635, 195, 650, 650,
        ["3 MIN AIR", "3 DAYS WATER", "3 WEEKS FOOD"],
        progress=prog, circle_word="WATER", show_pen=True
    )

def _shot_bedroom_day2_wait(ctx, t, prog):
    """Shot 29 (130.8-139.8s): Bedroom clock wait 2:59 -> 3:00 + speech bubble '5 DAYS. / THURSDAY, 9 P.M. / STAY INSIDE.'."""
    is_3am = (prog > 0.32)
    draw_env_bedroom(ctx, t, mode="clock_wait", clock_str="3:00" if is_3am else "2:59", prog=prog)
    if is_3am:
        draw_speech_bubble(
            ctx, 265, 285, 520, 225, 815, 615,
            ["5 DAYS.", "THURSDAY, 9 P.M.", "STAY INSIDE."],
            red_last_line=True,
            scale=clamp((prog - 0.32) * 3.5, 0.0, 1.0)
        )

def _shot_bedroom_squint_screenshot(ctx, t, prog):
    """Shot 31 (143.5-147.5s): Bedroom Chad squinting closely at phone screenshot."""
    draw_env_bedroom(ctx, t, mode="clock_wait", clock_str="3:01", prog=1.0)
    if prog > 0.38:
        draw_taped_label(ctx, 485, 345, "Operator: EW04?", color="#D42620", angle_deg=-3.5,
                         scale=clamp((prog - 0.38) * 3.0, 0, 1))

def _shot_living_pb_calorie_pour(ctx, t, prog):
    """Shot 35 (159.8-164.5s): Living room table with Peanut Butter jar pouring into CALORIES tube (2,500 crack)."""
    draw_env_living_room(ctx, t, mode="cereal_hide_cash", props_level=1, prog=prog)
    kcal = lerp(450.0, 2500.0, clamp(prog * 1.25, 0.0, 1.0))
    draw_calorie_tube_overlay(ctx, 1345, 515, kcal_val=kcal, pouring_pb=True, prog=prog)

def _shot_bedroom_day3_wait_and_search(ctx, t, prog):
    """Shot 44 (195.8-205.8s): Bedroom 3:00 alert ('4 DAYS. / REINFORCE YOUR DOOR.') + email search 'Ashford County'."""
    is_3am = (prog > 0.18)
    draw_env_bedroom(ctx, t, mode="clock_wait", clock_str="3:00" if is_3am else "2:59", prog=prog)
    if 0.18 < prog < 0.62:
        draw_speech_bubble(
            ctx, 235, 265, 565, 215, 815, 615,
            ["4 DAYS.", "REINFORCE YOUR DOOR."],
            red_last_line=True,
            scale=clamp((prog - 0.18) * 4.0, 0.0, 1.0)
        )
    elif prog >= 0.62:
        # Searching "Ashford County" in phone email bar
        sprog = clamp((prog - 0.62) / 0.35, 0.0, 1.0)
        draw_ink_box(ctx, 410, 195, 760, 115, "#F5F2EA", stroke_w=4.5, r=24, shadow=True)
        q_str = "Ashford County"[:max(2, int(14 * sprog))]
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(42)
        ctx.set_source_rgb(*hex_rgb("#181615"))
        ctx.move_to(445, 268)
        ctx.show_text(q_str)

def _shot_ew04_spotlight_cone(ctx, t, prog):
    """Shot 89 (420.0-424.8s): Pitch-black background with crimson 'EW04' casting red spotlight cone onto Chad."""
    draw_ink_box(ctx, 0, 0, WIDTH, HEIGHT, "#030305", stroke_w=0)
    # Red spotlight cone from top center
    pat = cairo.LinearGradient(960, 125, 960, 960)
    pat.add_color_stop_rgba(0.0, 0.92, 0.12, 0.12, 0.55)
    pat.add_color_stop_rgba(1.0, 0.92, 0.12, 0.12, 0.05)
    ctx.move_to(845, 145)
    ctx.line_to(1075, 145)
    ctx.line_to(1420, 985)
    ctx.line_to(500, 985)
    ctx.close_path()
    ctx.set_source(pat)
    ctx.fill()

    ctx.select_font_face("Consolas", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(92)
    ctx.set_source_rgb(*hex_rgb("#E52222"))
    ctx.move_to(845, 130)
    ctx.show_text("EW04")

    draw_chad(ctx, 960, 745, scale=1.45, facing="front", pose="phone_look",
                expression="shocked", prop="phone_red", t=t, red_rim=0.85)

def _shot_dark_living_room_left_behind(ctx, t, prog):
    """Shot 111 (559.8-565.5s): Empty dark living room with stockpiled supplies + notebook '120 gal water / 24 days food / door: never broke.'."""
    draw_env_living_room(ctx, t, mode="cereal_hide_cash", cardboard=True, dark_mode=True, props_level=2, prog=prog)
    # Draw notebook without Chad
    draw_notebook_card(
        ctx, 1145, 125, 685, 495,
        title="",
        items=[
            {"type": "text", "text": "120 gal water", "size": 46, "color": "#162955"},
            {"type": "text", "text": "24 days food", "size": 46, "color": "#162955"},
            {"type": "text", "text": "door: never broke.", "size": 46, "color": "#D42620"},
        ],
        progress=prog,
        angle_deg=1.8
    )

# ==============================================================================
# MASTER 115-SHOT TIMELINE TABLE (0.00s -> 590.87s)
# ==============================================================================
SHOTS = [
    # --- MINUTE 0:00 - 1:00 (Day 1: Friday 3:12 AM Wakeup & Flash-forwards) ---
    (0.0, 2.0, 1.00, 1.04, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_brownstone_exterior(c, t, mode="night_title", prog=p)),
    (2.0, 6.0, 1.02, 1.10, 0, 0, 0.25, True,
     lambda c, t, p: draw_env_apocalypse_street(c, t, prog=p)),
    (6.0, 8.0, 1.00, 1.05, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_bedroom(c, t, mode="sleep", prog=p)),
    (8.0, 11.8, 1.00, 1.12, 0, 0, 0.35, True,
     lambda c, t, p: draw_env_bedroom(c, t, mode="closeup_wake", prog=p)),
    (11.8, 14.8, 1.00, 1.10, 0, 0, 0.20, True,
     lambda c, t, p: draw_env_bedroom(c, t, mode="closeup_ecg", prog=p)),
    (14.8, 25.5, 1.00, 1.14, 0, 0, 0.15, True,
     lambda c, t, p: draw_smartphone_alert(
         c, t, clock_str="3:12", header_tag="COUNTY ALERT · now",
         big_title="EMERGENCY\nALERT",
         body_lines=[
             "Containment failure.",
             "Shelter in place begins",
             "Thursday, 9 p.m.",
             "You have 6 days to prepare.",
             "This is not a test."
         ],
         highlight_phrase="6 days to prepare.", progress=p)),
    (25.5, 30.5, 1.04, 1.00, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_bedroom(c, t, mode="blink_gone", prog=p)),
    (30.5, 35.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_window_garden(c, t, mode="watering", prog=p)),
    (35.8, 38.8, 1.00, 1.08, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_brownstone_exterior(c, t, mode="day_to_night_beacon", prog=p)),
    (38.8, 45.8, 1.02, 1.14, 0, 0, 0.45, True,
     lambda c, t, p: draw_env_rooftop(c, t, mode="flashforward", prog=p)),
    (45.8, 50.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="day1_turn", prog=p)),
    (50.8, 57.5, 1.00, 1.05, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="day1_check", prog=p)),
    (57.5, 61.0, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_october_calendar(
         c, t, crossed_days=[], active_day=17,
         bottom_title="6 DAYS LEFT", bottom_sub="FRIDAY", prog=p)),

    # --- MINUTE 1:00 - 2:00 (Day 1: Water Stockpile & 11 Stair Trips) ---
    (61.0, 64.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_county_website_phone(c, t, prog=p)),
    (64.8, 69.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="call_friend", prog=p)),
    (69.8, 73.8, 1.00, 1.10, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="broken_or_purpose", prog=p)),
    (73.8, 79.8, 1.00, 1.08, 0, 0, 0.15, False,
     lambda c, t, p: draw_env_front_door(c, t, mode="price_tags", prog=p)),
    (79.8, 86.8, 1.00, 1.06, 0, 0, 0.0, False,
     _shot_sticky_survival_rule),
    (86.8, 89.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_front_door(c, t, mode="sticky_water", prog=p)),
    (89.8, 92.8, 1.00, 1.08, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_supermarket(c, t, mode="aisle_walk", prog=p)),
    (92.8, 96.8, 1.00, 1.06, 0, 0, 0.15, False,
     lambda c, t, p: draw_env_supermarket(c, t, mode="cart_stack_28", prog=p)),
    (96.8, 99.8, 1.00, 1.04, 0, 0, 0.0, False,
     lambda c, t, p: draw_card_terminal_split(c, t, prog=p)),
    (99.8, 104.5, 1.00, 1.05, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_supermarket(c, t, mode="aisle_notes", prog=p)),
    (104.5, 108.8, 1.00, 1.05, 0, 0, 0.0, False,
     _shot_window_garden_month_droplets),
    (108.8, 111.8, 1.00, 1.08, 0, -20, 0.0, False,
     lambda c, t, p: draw_env_brownstone_exterior(c, t, mode="floor_numbers", prog=p)),
    (111.8, 116.8, 1.00, 1.06, 0, 0, 0.12, False,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="trips", prog=p)),
    (116.8, 120.0, 1.00, 1.08, 0, -15, 0.0, False,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="look_up", prog=p)),

    # --- MINUTE 2:00 - 3:00 (Day 2: Saturday 3:00 AM, EW04, Calories & Pantry Mart) ---
    (120.0, 127.8, 1.00, 1.18, 80, -70, 0.0, False,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="roof_access_stairs", prog=p)),
    (127.8, 130.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_october_calendar(
         c, t, crossed_days=[17], active_day=18,
         bottom_title="5 DAYS LEFT", bottom_sub="SATURDAY · 3:00 AM", prog=p)),
    (130.8, 139.8, 1.00, 1.08, 0, 0, 0.15, False,
     _shot_bedroom_day2_wait),
    (139.8, 143.5, 1.00, 1.08, 0, 0, 0.15, True,
     lambda c, t, p: draw_smartphone_alert(
         c, t, clock_str="3:00", header_tag="COUNTY ALERT · now",
         big_title="5 DAYS",
         body_lines=[
             "Thursday, 9 PM.",
             "Stay inside.",
             "Lock your door. Cover",
             "your windows. Do not go",
             "outside after dark."
         ],
         footer_code="EW04",
         screenshot_flash=clamp((p - 0.65) / 0.35, 0.0, 1.0),
         progress=p)),
    (143.5, 147.5, 1.04, 1.22, -45, 20, 0.0, False,
     _shot_bedroom_squint_screenshot),
    (147.5, 151.8, 1.00, 1.08, 0, 0, 0.0, True,
     lambda c, t, p: draw_pixel_macro_ew04(c, t, prog=p)),
    (151.8, 155.5, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_bedroom(c, t, mode="ew04_beam", clock_str="3:01", prog=p)),
    (155.5, 159.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_front_door(c, t, mode="todo_calories", prog=p)),
    (159.8, 164.5, 1.00, 1.08, 0, 0, 0.10, False,
     _shot_living_pb_calorie_pour),
    (164.5, 165.8, 1.00, 1.06, 0, 0, 0.20, False,
     lambda c, t, p: draw_env_supermarket(c, t, mode="pb_drop_4", prog=p)),
    (165.8, 170.5, 1.00, 1.05, 0, 0, 0.0, False,
     lambda c, t, p: draw_pantry_receipt(c, t, prog=p)),
    (170.5, 172.8, 1.00, 1.05, 0, 0, 0.0, False,
     lambda c, t, p: draw_cart_topdown(c, t, prog=p)),
    (172.8, 176.8, 1.00, 1.04, 0, 0, 0.0, False,
     lambda c, t, p: draw_power_out_atms(c, t, prog=p)),
    (176.8, 180.0, 1.00, 1.05, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_bank_atms(c, t, mode="wide", prog=p)),

    # --- MINUTE 3:00 - 4:00 (Day 3: Sunday 3:00 AM, Ellen Ward & Door Cross-Section) ---
    (180.0, 185.8, 1.00, 1.08, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_bank_atms(c, t, mode="pan_withdraw", prog=p)),
    (185.8, 188.0, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="cereal_hide_cash", props_level=1, prog=p)),
    (188.0, 192.5, 1.00, 1.05, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="day2_check", props_level=1, prog=p)),
    (192.5, 195.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_october_calendar(
         c, t, crossed_days=[17, 18], active_day=19,
         bottom_title="4 DAYS LEFT", bottom_sub="SUNDAY · 3:00 AM",
         show_cardboard=True, prog=p)),
    (195.8, 205.8, 1.00, 1.08, 0, 0, 0.12, False,
     _shot_bedroom_day3_wait_and_search),
    (205.8, 216.5, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_email_printout(c, t, prog=p)),
    (216.5, 223.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_ellen_ward_board(c, t, prog=p)),
    (223.8, 231.8, 1.00, 1.08, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="test_channel_you", props_level=1, prog=p)),
    (231.8, 236.8, 1.00, 1.08, 0, 0, 0.45, False,
     lambda c, t, p: draw_env_front_door(c, t, mode="boot_kick", prog=p)),
    (236.8, 240.0, 1.00, 1.06, 0, 0, 0.25, False,
     lambda c, t, p: draw_door_cross_section(c, t, prog=p)),

    # --- MINUTE 4:00 - 5:00 (Day 4: Monday 3:00 AM, 3-Inch Screws, Hospital Outbreak & Fridge) ---
    (240.0, 243.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_strike_plate_ruler(c, t, prog=p)),
    (243.8, 248.0, 1.00, 1.05, 0, 0, 0.15, False,
     lambda c, t, p: draw_env_front_door(c, t, mode="screw_reinforce", prog=p)),
    (248.0, 250.5, 1.00, 1.05, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="tape_cardboard", cardboard=True, props_level=1, prog=p)),
    (250.5, 253.8, 1.00, 1.10, 0, -25, 0.0, False,
     lambda c, t, p: draw_env_brownstone_exterior(c, t, mode="night_target_window", prog=p)),
    (253.8, 256.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_october_calendar(
         c, t, crossed_days=[17, 18, 19], active_day=20,
         bottom_title="3 DAYS LEFT", bottom_sub="MONDAY · 3:00 AM",
         show_cardboard=True, prog=p)),
    (256.8, 261.8, 1.00, 1.08, 0, 0, 0.15, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="chair_3days_alert", cardboard=True, dark_mode=True, props_level=1, prog=p)),
    (261.8, 265.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_tv_news(c, t, mode="anchor", prog=p)),
    (265.8, 273.5, 1.00, 1.08, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_tv_news(c, t, mode="hospital", prog=p)),
    (273.5, 275.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="chair_1hour_later", cardboard=True, dark_mode=True, props_level=1, prog=p)),
    (275.8, 285.8, 1.00, 1.12, 0, 0, 0.35, False,
     lambda c, t, p: draw_hospital_phone_video(c, t, prog=p, show_hands=(p > 0.85))),
    (285.8, 288.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_deleted_videos_grid(c, t, prog=p)),
    (288.8, 292.8, 1.00, 1.06, -30, 0, 0.0, False,
     lambda c, t, p: draw_env_supermarket(c, t, mode="survival_aisle_radio", prog=p)),
    (292.8, 298.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="place_gear_and_eat_fridge", cardboard=True, props_level=2, prog=p)),
    (298.8, 303.5, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_fridge_4h_diagram(c, t, prog=p)),

    # --- MINUTE 5:00 - 6:00 (Day 5: Tuesday 3:00 AM, Bathtub, Water Heater, Bleach & Bug-Out Bag) ---
    (303.5, 306.0, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_october_calendar(
         c, t, crossed_days=[17, 18, 19, 20], active_day=21,
         bottom_title="2 DAYS LEFT", bottom_sub="TUESDAY · 3:00 AM",
         show_cardboard=True, prog=p)),
    (306.0, 311.8, 1.00, 1.08, 0, 0, 0.15, True,
     lambda c, t, p: draw_smartphone_alert(
         c, t, clock_str="3:00", header_tag="COUNTY ALERT · now",
         big_title="Tuesday, 3 AM.\n2 DAYS",
         body_lines=[
             "Water pressure drops",
             "after the grid fails.",
             "Fill every container",
             "you have."
         ],
         footer_code="EW04", progress=p)),
    (311.8, 316.0, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_bathroom_and_heater(c, t, mode="tub_fill", prog=p)),
    (316.0, 323.5, 1.00, 1.08, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_bathroom_and_heater(c, t, mode="heater_closet", prog=p)),
    (323.5, 327.2, 1.00, 1.05, 0, 0, 0.0, False,
     lambda c, t, p: draw_water_heater_50gal_diagram(c, t, prog=p)),
    (327.2, 330.8, 1.00, 1.08, 0, 20, 0.0, False,
     lambda c, t, p: draw_env_bathroom_and_heater(c, t, mode="heater_drain", prog=p)),
    (330.8, 333.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_bathroom_and_heater(c, t, mode="tub_treat", prog=p)),
    (333.8, 343.5, 1.00, 1.08, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="bleach_water", cardboard=True, props_level=2, prog=p)),
    (343.5, 349.5, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_water_stack_120_diagram(c, t, prog=p)),
    (349.5, 351.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_front_door(c, t, mode="pack_bag", prog=p)),
    (351.8, 356.5, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_backpack_xray(c, t, prog=p)),
    (356.5, 360.0, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="pack_bag_timer", cardboard=True, props_level=2, prog=p)),

    # --- MINUTE 6:00 - 7:00 (Day 6: Wednesday -> 1 Day Left -> Thursday 9:00 PM HOUR ZERO) ---
    (360.0, 365.5, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_bedroom(c, t, mode="sunrise_cardboard", prog=p)),
    (365.5, 368.8, 1.00, 1.06, 0, 0, 0.0, True,
     lambda c, t, p: draw_october_calendar(
         c, t, crossed_days=[17, 18, 19, 20, 21], active_day=22,
         bottom_title="1 DAY LEFT", show_cardboard=True, red_siren=True, prog=p)),
    (368.8, 376.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="call_ellen_ward", cardboard=True, props_level=2, prog=p)),
    (376.8, 379.8, 1.00, 1.08, 0, 0, 0.0, False,
     lambda c, t, p: draw_phone_call_hangup(c, t, prog=p)),
    (379.8, 384.5, 1.00, 1.08, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_window_garden(c, t, mode="cardboard_gap_watering", prog=p)),
    (384.5, 390.5, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="almost_knock_slide_note", prog=p)),
    (390.5, 395.5, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_folded_note_doormat(c, t, prog=p)),
    (395.5, 399.8, 1.00, 1.08, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="lock_click_10pm", prog=p)),
    (399.8, 403.0, 1.00, 1.08, 0, 0, 0.20, True,
     lambda c, t, p: draw_october_calendar(
         c, t, crossed_days=[17, 18, 19, 20, 21, 22], active_day=23,
         bottom_title="HOUR ZERO", show_cardboard=True, red_siren=True, prog=p)),
    (403.0, 408.8, 1.00, 1.10, 0, 0, 0.35, True,
     lambda c, t, p: draw_env_living_room(c, t, mode="thursday_9pm_all_scream", cardboard=True, dark_mode=True, props_level=2, prog=p)),
    (408.8, 413.5, 1.00, 1.12, 0, 0, 0.30, True,
     lambda c, t, p: draw_env_brownstone_exterior(c, t, mode="night_all_red_alerts", prog=p)),
    (413.5, 420.0, 1.00, 1.12, 0, 0, 0.25, True,
     lambda c, t, p: draw_smartphone_alert(
         c, t, clock_str="9:00", header_tag="PUBLIC SAFETY",
         big_title="EMERGENCY\nALERT",
         body_lines=[
             "Shelter in place",
             "immediately.",
             "Lock all doors and",
             "windows. Do not go",
             "outside."
         ],
         footer_code="EW04" if p > 0.65 else None,
         two_hands=True, progress=p)),

    # --- MINUTE 7:00 - 8:00 (Outbreak Night: Alarms Cut Short, Smoke & Peephole Horror) ---
    (420.0, 424.8, 1.00, 1.08, 0, 0, 0.0, True,
     _shot_ew04_spotlight_cone),
    (424.8, 428.5, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="red_under_doors_cut", prog=p)),
    (428.5, 431.8, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="alarms_cut_short", cardboard=True, dark_mode=True, props_level=2, prog=p)),
    (431.8, 435.5, 1.00, 1.06, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="power_out_940", cardboard=True, dark_mode=True, props_level=2, prog=p)),
    (435.5, 445.5, 1.00, 1.12, 0, 0, 0.15, False,
     lambda c, t, p: draw_env_window_garden(c, t, mode="cardboard_gap_bathrobe_man", prog=p)),
    (445.5, 452.8, 1.00, 1.12, 0, 0, 0.25, False,
     lambda c, t, p: draw_env_living_room(c, t, mode="woman_screams_downstairs", cardboard=True, dark_mode=True, props_level=2, prog=p)),
    (452.8, 456.5, 1.00, 1.08, 0, -25, 0.15, True,
     lambda c, t, p: draw_env_living_room(c, t, mode="smoke_alarm_11pm", cardboard=True, dark_mode=True, props_level=2, prog=p)),
    (456.5, 462.5, 1.00, 1.08, 0, -20, 0.15, False,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="smoke_rising", prog=p)),
    (462.5, 465.0, 1.00, 1.08, 0, 0, 0.25, False,
     lambda c, t, p: draw_env_front_door(c, t, mode="knocks", prog=p)),
    (465.0, 480.0, 1.00, 1.16, 0, 0, 0.35, False,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="peephole_sequence", prog=p)),

    # --- MINUTE 8:00 - 9:00 (Fire Escape, P-A-S-S Notebook & Hallway Extinguisher Fight) ---
    (480.0, 482.8, 1.00, 1.08, 0, 0, 0.0, False,
     lambda c, t, p: draw_env_window_garden(c, t, mode="hose_abandoned_night", prog=p)),
    (482.8, 487.8, 1.00, 1.08, 0, 0, 0.45, False,
     lambda c, t, p: draw_env_front_door(c, t, mode="brace_3in", prog=p)),
    (487.8, 499.8, 1.00, 1.10, 0, 0, 0.25, True,
     lambda c, t, p: draw_env_front_door(c, t, mode="smoke_fire_escape", prog=p)),
    (499.8, 505.8, 1.00, 1.05, 0, 0, 0.15, False,
     lambda c, t, p: draw_env_front_door(c, t, mode="pass_notebook", prog=p)),
    (505.8, 507.8, 1.00, 1.08, 0, 0, 0.25, False,
     lambda c, t, p: draw_env_front_door(c, t, mode="aim_extinguisher", prog=p)),
    (507.8, 522.8, 1.00, 1.14, 0, 0, 0.55, False,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="extinguisher_fight", prog=p)),
    (522.8, 528.8, 1.00, 1.08, 0, 0, 0.25, False,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="zombie_falls_stairs", prog=p)),
    (528.8, 540.0, 1.00, 1.12, 0, 0, 0.45, False,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="fourth_floor_grab", prog=p)),

    # --- MINUTE 9:00 - 9:50.87 (Rooftop Climax, 6-Day Summary, EW04 Rescue & Nuclear Finale) ---
    (540.0, 542.8, 1.00, 1.10, 0, 0, 0.45, True,
     lambda c, t, p: draw_env_hallway_stairs(c, t, mode="shoulder_hit_roof_door", prog=p)),
    (542.8, 544.8, 1.00, 1.08, 0, -25, 0.25, True,
     lambda c, t, p: draw_env_brownstone_exterior(c, t, mode="night_fire", prog=p)),
    (544.8, 554.8, 1.00, 1.12, 0, 0, 0.45, True,
     lambda c, t, p: draw_env_rooftop(c, t, mode="wedge_door", prog=p)),
    (554.8, 559.8, 1.00, 1.05, 0, 0, 0.0, False,
     lambda c, t, p: draw_calendar_6_summary(c, t, prog=p)),
    (559.8, 565.5, 1.00, 1.05, 0, 0, 0.0, False,
     _shot_dark_living_room_left_behind),
    (565.5, 568.5, 1.00, 1.08, 0, -20, 0.20, True,
     lambda c, t, p: draw_env_brownstone_exterior(c, t, mode="night_fire", prog=p)),
    (568.5, 580.5, 1.00, 1.08, 0, 0, 0.12, False,
     lambda c, t, p: draw_env_rooftop(c, t, mode="slumped_count", prog=p)),
    (580.5, 585.8, 1.00, 1.10, 0, 0, 0.15, True,
     lambda c, t, p: draw_smartphone_alert(
         c, t, clock_str="4%", header_tag="TEST CHANNEL · ZONE 4",
         big_title="Zone Four:",
         body_lines=[
             "Do not leave your",
             "building.",
             "Rescue in 7 days.",
             "Stay on the roof.",
             "Signed, EW04"
         ],
         highlight_phrase="Stay on the roof.",
         progress=p)),
    (585.8, 591.0, 1.00, 1.06, 0, 0, 0.55, False,
     lambda c, t, p: draw_env_rooftop(c, t, mode="nuclear_finale", prog=p)),
]

def render_frame(ctx, t):
    """
    Renders the exact 1920x1080 animation frame at timestamp `t` (in seconds).
    """
    ctx.save()
    # Default clear
    ctx.set_source_rgb(0.04, 0.04, 0.05)
    ctx.paint()

    # Locate active shot
    active_shot = SHOTS[-1]
    for s in SHOTS:
        if s[0] <= t < s[1]:
            active_shot = s
            break

    t0, t1, z0, z1, px, py, shake, red_pulse, draw_fn = active_shot
    dur = max(0.001, t1 - t0)
    prog = clamp((t - t0) / dur, 0.0, 1.0)

    # Smooth camera zoom/pan + trauma shake
    zoom = lerp(z0, z1, prog)
    cur_px = lerp(0.0, float(px), prog)
    cur_py = lerp(0.0, float(py), prog)

    ctx.save()
    apply_camera(ctx, zoom=zoom, pan_x=cur_px, pan_y=cur_py, shake_amp=shake * 16.0, t=t)
    draw_fn(ctx, t, prog)
    ctx.restore()

    # Global red emergency pulse & cinematic dark vignette
    if red_pulse:
        draw_red_alarm_pulse(ctx, t, max_alpha=0.32)
    draw_vignette(ctx, strength=0.46)
    ctx.restore()
