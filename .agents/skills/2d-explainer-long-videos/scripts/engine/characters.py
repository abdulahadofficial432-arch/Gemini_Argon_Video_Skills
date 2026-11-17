import math
import cairo
from engine.primitives import hex_rgb, hex_rgba, set_ink, rounded_rect_path, draw_ink_box, clamp

# ==============================================================================
# PROPS & MINI OBJECTS HELD BY CHARACTERS
# ==============================================================================
def draw_water_jug(ctx, x, y, scale=1.0, alpha=1.0):
    """Draws the translucent blue-white 1-gallon plastic water jug with blue cap."""
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale, scale)

    # Body
    ctx.move_to(-26, -15)
    ctx.line_to(-14, -36)
    ctx.line_to(12, -36)
    ctx.line_to(26, -15)
    ctx.line_to(28, 34)
    ctx.curve_to(28, 40, 22, 42, 16, 42)
    ctx.line_to(-16, 42)
    ctx.curve_to(-22, 42, -28, 40, -28, 34)
    ctx.close_path()
    ctx.set_source_rgba(0.84, 0.91, 0.96, alpha)
    ctx.fill_preserve()
    set_ink(ctx, 3.0, alpha)
    ctx.stroke()

    # Water level shading inside jug
    ctx.save()
    ctx.rectangle(-25, -5, 50, 44)
    ctx.clip()
    ctx.set_source_rgba(0.62, 0.80, 0.93, 0.55 * alpha)
    ctx.paint()
    ctx.restore()

    # Handle cutout
    ctx.move_to(10, -24)
    ctx.line_to(20, -12)
    ctx.line_to(20, 6)
    ctx.line_to(10, 6)
    ctx.close_path()
    ctx.set_source_rgba(0.25, 0.30, 0.36, 0.65 * alpha)
    ctx.fill_preserve()
    set_ink(ctx, 2.5, alpha)
    ctx.stroke()

    # Blue cap
    rounded_rect_path(ctx, -9, -45, 16, 9, 2)
    ctx.set_source_rgba(0.18, 0.42, 0.78, alpha)
    ctx.fill_preserve()
    set_ink(ctx, 2.5, alpha)
    ctx.stroke()
    ctx.restore()

def draw_fire_extinguisher_prop(ctx, x, y, scale=1.0, angle_deg=0.0):
    """Draws the red cylindrical fire extinguisher with black hose and brass valve."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(math.radians(angle_deg))
    ctx.scale(scale, scale)

    # Red cylinder body
    rounded_rect_path(ctx, -22, -45, 44, 95, 16)
    ctx.set_source_rgb(*hex_rgb("#C92A24"))
    ctx.fill_preserve()
    set_ink(ctx, 3.5)
    ctx.stroke()

    # White label band
    ctx.rectangle(-20, -15, 40, 28)
    ctx.set_source_rgb(0.92, 0.90, 0.86)
    ctx.fill_preserve()
    set_ink(ctx, 2.0)
    ctx.stroke()

    # Metallic valve & lever at top
    ctx.rectangle(-7, -58, 14, 14)
    ctx.set_source_rgb(0.65, 0.65, 0.68)
    ctx.fill_preserve()
    set_ink(ctx, 2.5)
    ctx.stroke()

    ctx.move_to(-8, -56)
    ctx.line_to(22, -64)
    ctx.move_to(-8, -52)
    ctx.line_to(20, -48)
    set_ink(ctx, 3.5)
    ctx.stroke()

    # Black hose on left
    ctx.move_to(-8, -52)
    ctx.curve_to(-32, -45, -34, 10, -28, 38)
    set_ink(ctx, 5.0)
    ctx.stroke()
    ctx.restore()

# ==============================================================================
# PROTAGONIST RIG: CHAD (Oversized round head, backward red cap, puffy vest)
# ==============================================================================
def draw_chad(ctx, x, y, scale=1.0, facing="front", pose="idle",
                expression="neutral", prop=None, t=0.0, alpha=1.0, red_rim=0.0):
    """
    Draws Chad at (x, y) where (x, y) is the center of his torso/pelvis base,
    matching the exact proportions and design in Exact Video.mp4.
    """
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale, scale)

    # Subtle breathing / walk bob
    bob = math.sin(t * 3.2) * 2.0
    if pose == "walk":
        bob = abs(math.sin(t * 9.0)) * -8.0
    elif pose == "tremble_jugs":
        bob = math.sin(t * 35.0) * 2.5

    # Determine direction multiplier (+1 facing right, -1 facing left)
    dir_x = -1.0 if "left" in facing else 1.0
    is_back = (facing == "back")

    # --------------------------------------------------------------------------
    # 1. STICK LEGS (long thin black lines with oval feet)
    # --------------------------------------------------------------------------
    hip_y = 20 + bob * 0.4
    foot_y = 185
    if pose not in ("sit_bed", "sleep_bed"):
        leg_spread = 16
        l_foot_x, r_foot_x = -leg_spread, leg_spread
        l_knee_x, r_knee_x = -leg_spread, leg_spread
        l_foot_y, r_foot_y = foot_y, foot_y

        if pose == "walk":
            swing = math.sin(t * 9.0) * 32.0
            l_foot_x = -swing
            r_foot_x = swing
            l_foot_y = foot_y - max(0, math.cos(t * 9.0)) * 12
            r_foot_y = foot_y - max(0, -math.cos(t * 9.0)) * 12
            l_knee_x = l_foot_x * 0.5 + 6 * dir_x
            r_knee_x = r_foot_x * 0.5 + 6 * dir_x
        elif pose == "crouch":
            hip_y = 65
            l_knee_x, r_knee_x = -38 * dir_x, -18 * dir_x
            l_foot_x, r_foot_x = -15, 20
        elif pose == "brace_door":
            l_foot_x, r_foot_x = -35, 10
            l_knee_x, r_knee_x = -22, 5
        elif pose == "sit_chair":
            hip_y = 35
            l_foot_y = r_foot_y = 145

        set_ink(ctx, 6.5, alpha)
        # Left leg
        ctx.move_to(-12, hip_y)
        ctx.line_to(l_knee_x, (hip_y + l_foot_y) * 0.5)
        ctx.line_to(l_foot_x, l_foot_y)
        ctx.stroke()
        # Right leg
        ctx.move_to(12, hip_y)
        ctx.line_to(r_knee_x, (hip_y + r_foot_y) * 0.5)
        ctx.line_to(r_foot_x, r_foot_y)
        ctx.stroke()

        # Shoes
        for fx, fy in [(l_foot_x, l_foot_y), (r_foot_x, r_foot_y)]:
            ctx.save()
            ctx.translate(fx + 5 * dir_x, fy)
            ctx.scale(1.5, 0.55)
            ctx.arc(0, 0, 11, 0, math.pi * 2)
            ctx.set_source_rgba(0.08, 0.07, 0.07, alpha)
            ctx.fill()
            ctx.restore()

    # --------------------------------------------------------------------------
    # 2. BACKPACK (if wearing bug-out bag)
    # --------------------------------------------------------------------------
    torso_top = -95 + bob
    torso_bot = hip_y + 8
    if prop in ("backpack", "backpack_extinguisher"):
        bx = -34 * dir_x
        rounded_rect_path(ctx, bx - 22, torso_top + 10, 44, 82, 14)
        ctx.set_source_rgba(*hex_rgba("#2B3B54", alpha))
        ctx.fill_preserve()
        set_ink(ctx, 3.5, alpha)
        ctx.stroke()

    # --------------------------------------------------------------------------
    # 3. TORSO: QUILTED CHARCOAL PUFFY VEST (#3C3D42)
    # --------------------------------------------------------------------------
    vest_w = 72
    vest_h = torso_bot - torso_top
    ctx.save()
    if pose == "crouch":
        ctx.translate(0, 35)
        ctx.rotate(math.radians(18 * dir_x))
    elif pose == "brace_door":
        ctx.rotate(math.radians(-10 * dir_x))

    # Puffy vest silhouette
    rounded_rect_path(ctx, -vest_w * 0.5, torso_top, vest_w, vest_h, 18)
    ctx.set_source_rgba(*hex_rgba("#3D3E44", alpha))
    ctx.fill_preserve()
    set_ink(ctx, 4.0, alpha)
    ctx.stroke()

    # Quilted horizontal puffer ribs
    for rib_frac in (0.26, 0.52, 0.76):
        ry = torso_top + vest_h * rib_frac
        ctx.move_to(-vest_w * 0.46, ry)
        ctx.line_to(vest_w * 0.46, ry)
        ctx.set_source_rgba(0.16, 0.16, 0.19, 0.75 * alpha)
        ctx.set_line_width(2.8)
        ctx.stroke()

    # Center zipper line (when not facing straight back)
    if not is_back:
        zx = 8 * dir_x if ("left" in facing or "right" in facing) else 0
        ctx.move_to(zx, torso_top + 4)
        ctx.line_to(zx, torso_bot - 4)
        ctx.set_source_rgba(0.14, 0.14, 0.16, 0.85 * alpha)
        ctx.set_line_width(3.0)
        ctx.stroke()
    ctx.restore()

    # --------------------------------------------------------------------------
    # 4. ARMS & HANDS + HELD PROPS
    # --------------------------------------------------------------------------
    sh_y = torso_top + 22
    l_sh_x, r_sh_x = -vest_w * 0.44, vest_w * 0.44
    tremble_x = math.sin(t * 45.0) * 4.0 if pose == "tremble_jugs" else 0.0

    # Default hand positions
    l_hx, l_hy = -46 + tremble_x, torso_bot + 16
    r_hx, r_hy = 46 - tremble_x, torso_bot + 16

    if pose == "walk":
        arm_swing = math.sin(t * 9.0) * 24.0
        l_hx, r_hx = -20 + arm_swing, 20 - arm_swing
        l_hy, r_hy = torso_bot + 12, torso_bot + 12
    elif pose == "phone_look" or pose == "sit_bed" or pose == "sit_chair":
        l_hx, l_hy = -16, torso_top + 62
        r_hx, r_hy = 18, torso_top + 62
    elif pose == "phone_ear":
        l_hx, l_hy = -38, torso_bot + 12
        r_hx, r_hy = 42 * dir_x, torso_top - 45
    elif pose == "point_right":
        r_hx, r_hy = 85, torso_top + 10
    elif pose == "brace_door":
        l_hx, l_hy = 44, torso_top + 38
        r_hx, r_hy = 48, torso_top + 68
    elif pose == "crouch":
        l_hx, l_hy = 35 * dir_x, torso_bot + 25
        r_hx, r_hy = 52 * dir_x, torso_top + 15
    elif pose == "aim_extinguisher":
        l_hx, l_hy = 35 * dir_x, torso_top + 45
        r_hx, r_hy = 55 * dir_x, torso_top + 35

    if pose != "sleep_bed":
        set_ink(ctx, 6.0, alpha)
        # Left arm
        ctx.move_to(l_sh_x, sh_y)
        ctx.line_to((l_sh_x + l_hx) * 0.5 - 6, (sh_y + l_hy) * 0.5 + 8)
        ctx.line_to(l_hx, l_hy)
        ctx.stroke()
        # Right arm
        ctx.move_to(r_sh_x, sh_y)
        ctx.line_to((r_sh_x + r_hx) * 0.5 + 6, (sh_y + r_hy) * 0.5 + 8)
        ctx.line_to(r_hx, r_hy)
        ctx.stroke()

        # Cartoon white mitt hands
        for hx, hy in [(l_hx, l_hy), (r_hx, r_hy)]:
            ctx.arc(hx, hy, 11, 0, math.pi * 2)
            ctx.set_source_rgba(*hex_rgba("#EAE4DC", alpha))
            ctx.fill_preserve()
            set_ink(ctx, 3.2, alpha)
            ctx.stroke()

        # Held props
        if prop in ("phone", "phone_red"):
            px = (l_hx + r_hx) * 0.5 if pose != "phone_ear" else r_hx
            py = (l_hy + r_hy) * 0.5 - 12 if pose != "phone_ear" else r_hy
            fill_c = "#C91E1E" if prop == "phone_red" else "#22242A"
            draw_ink_box(ctx, px - 13, py - 22, 26, 44, fill_c, stroke_w=3.0, r=4, alpha=alpha)
        elif prop == "jugs_2":
            draw_water_jug(ctx, l_hx, l_hy + 28, scale=0.68, alpha=alpha)
            draw_water_jug(ctx, r_hx, r_hy + 28, scale=0.68, alpha=alpha)
        elif prop == "jug_1":
            draw_water_jug(ctx, r_hx, r_hy + 28, scale=0.68, alpha=alpha)
        elif prop == "cash":
            ctx.save()
            ctx.translate(l_hx + 18, l_hy - 8)
            ctx.rotate(-0.25)
            draw_ink_box(ctx, -28, -14, 56, 28, "#58B368", stroke_w=3.0, r=2, alpha=alpha)
            ctx.restore()
        elif prop in ("extinguisher", "backpack_extinguisher"):
            draw_fire_extinguisher_prop(ctx, r_hx + 8 * dir_x, r_hy + 15, scale=0.72, angle_deg=-15 * dir_x)

    # --------------------------------------------------------------------------
    # 5. HEAD & BACKWARD RED BASEBALL CAP (Signature Look)
    # --------------------------------------------------------------------------
    head_y = torso_top - 64
    head_r = 62
    if pose == "crouch":
        head_y += 28
    ctx.save()
    ctx.translate(0, head_y)

    # Head base circle (#EAE4DC off-white with subtle warm shadow on lower edge)
    ctx.arc(0, 0, head_r, 0, math.pi * 2)
    ctx.set_source_rgba(*hex_rgba("#EAE4DC", alpha))
    ctx.fill_preserve()
    if red_rim > 0:
        ctx.set_source_rgba(0.95, 0.15, 0.12, red_rim * alpha)
        ctx.set_line_width(7.0)
        ctx.stroke_preserve()
    set_ink(ctx, 4.2, alpha)
    ctx.stroke()

    # Backward Red Cap Crown (#B5423D) covering top half of head
    ctx.save()
    ctx.arc(0, -8, head_r + 2, math.pi * 1.04, math.pi * 1.96)
    ctx.curve_to(head_r * 0.6, -12, -head_r * 0.6, -12, -(head_r + 2) * math.cos(0.04 * math.pi), -8 - (head_r + 2) * math.sin(0.04 * math.pi))
    ctx.close_path()
    ctx.set_source_rgba(*hex_rgba("#B5423D", alpha))
    ctx.fill_preserve()
    set_ink(ctx, 4.0, alpha)
    ctx.stroke()
    ctx.restore()

    # Cap top button
    ctx.arc(0, -head_r - 9, 5, 0, math.pi * 2)
    ctx.set_source_rgba(*hex_rgba("#8A2E2A", alpha))
    ctx.fill_preserve()
    set_ink(ctx, 3.0, alpha)
    ctx.stroke()

    # Backward Cap Brim sticking out the back/side (#8A2E2A)
    brim_dir = -dir_x if ("left" in facing or "right" in facing) else 1.0
    ctx.move_to(brim_dir * (head_r - 12), -24)
    ctx.curve_to(brim_dir * (head_r + 34), -14,
                 brim_dir * (head_r + 38), 6,
                 brim_dir * (head_r - 4), 2)
    ctx.close_path()
    ctx.set_source_rgba(*hex_rgba("#9E3530", alpha))
    ctx.fill_preserve()
    set_ink(ctx, 3.8, alpha)
    ctx.stroke()

    # Messy dark-brown hair tufts (#3A2B24) at sides and front cap keyhole
    ctx.set_source_rgba(*hex_rgba("#3B2B23", alpha))
    # Sideburns / ear tufts
    for side in (-1, 1):
        ctx.move_to(side * (head_r - 8), -16)
        ctx.line_to(side * (head_r + 12), -4)
        ctx.line_to(side * (head_r - 2), 2)
        ctx.line_to(side * (head_r + 9), 14)
        ctx.line_to(side * (head_r - 10), 16)
        ctx.close_path()
        ctx.fill_preserve()
        set_ink(ctx, 3.2, alpha)
        ctx.stroke()

    if is_back:
        # Back of head covered in spiky brown hair under cap
        ctx.arc(0, 6, head_r - 4, -0.15, math.pi + 0.15)
        ctx.set_source_rgba(*hex_rgba("#3B2B23", alpha))
        ctx.fill_preserve()
        set_ink(ctx, 3.8, alpha)
        ctx.stroke()
    else:
        # Front cap keyhole + spiky bangs tuft
        face_shift = 14 * dir_x if ("left" in facing or "right" in facing) else 0
        # Keyhole strap
        rounded_rect_path(ctx, face_shift - 22, -28, 44, 11, 4)
        ctx.set_source_rgba(*hex_rgba("#8A2E2A", alpha))
        ctx.fill_preserve()
        set_ink(ctx, 3.0, alpha)
        ctx.stroke()

        # Hair tuft poking out of keyhole
        ctx.move_to(face_shift - 16, -24)
        ctx.line_to(face_shift - 28, -36)
        ctx.line_to(face_shift - 6, -34)
        ctx.line_to(face_shift - 12, -48)
        ctx.line_to(face_shift + 8, -36)
        ctx.line_to(face_shift + 18, -24)
        ctx.close_path()
        ctx.set_source_rgba(*hex_rgba("#3B2B23", alpha))
        ctx.fill_preserve()
        set_ink(ctx, 3.2, alpha)
        ctx.stroke()

        # ----------------------------------------------------------------------
        # 6. FACIAL EXPRESSIONS (Eyes, Eyebrows, Mouth)
        # ----------------------------------------------------------------------
        ex_l = face_shift - 18
        ex_r = face_shift + 18
        ey = 2

        # Natural blink every 3.1s
        is_blinking = (expression == "asleep") or ((t % 3.1) > 2.96)

        if is_blinking or expression == "squint":
            set_ink(ctx, 3.8, alpha)
            for ex in (ex_l, ex_r):
                ctx.move_to(ex - 7, ey)
                ctx.line_to(ex + 7, ey)
                ctx.stroke()
        else:
            for ex in (ex_l, ex_r):
                ctx.save()
                ctx.translate(ex, ey)
                ctx.scale(0.68, 1.15)
                ctx.arc(0, 0, 7.5, 0, math.pi * 2)
                ctx.set_source_rgba(0.08, 0.07, 0.07, alpha)
                ctx.fill()
                ctx.restore()
                # Under-eye fatigue bag when worried/shocked
                if expression in ("worried", "shocked", "panting"):
                    ctx.arc(ex, ey + 9, 6, 0.2, math.pi - 0.2)
                    set_ink(ctx, 2.0, alpha * 0.65)
                    ctx.stroke()

        # Eyebrows
        set_ink(ctx, 3.8, alpha)
        if expression in ("worried", "shocked", "panting"):
            ctx.move_to(ex_l - 9, ey - 13)
            ctx.line_to(ex_l + 7, ey - 19)
            ctx.move_to(ex_r - 7, ey - 19)
            ctx.line_to(ex_r + 9, ey - 13)
            ctx.stroke()
        elif expression in ("angry", "squint", "wince"):
            ctx.move_to(ex_l - 9, ey - 18)
            ctx.line_to(ex_l + 7, ey - 12)
            ctx.move_to(ex_r - 7, ey - 12)
            ctx.line_to(ex_r + 9, ey - 18)
            ctx.stroke()
        else:
            ctx.move_to(ex_l - 8, ey - 15)
            ctx.line_to(ex_l + 8, ey - 15)
            ctx.move_to(ex_r - 8, ey - 15)
            ctx.line_to(ex_r + 8, ey - 15)
            ctx.stroke()

        # Mouth
        mx, my = face_shift, 28
        if expression == "shocked":
            ctx.save()
            ctx.translate(mx, my)
            ctx.scale(0.85, 1.2)
            ctx.arc(0, 0, 8.5, 0, math.pi * 2)
            ctx.set_source_rgba(*hex_rgba("#381414", alpha))
            ctx.fill_preserve()
            set_ink(ctx, 3.2, alpha)
            ctx.stroke()
            ctx.restore()
        elif expression in ("grimace_teeth", "panting", "wince"):
            rounded_rect_path(ctx, mx - 13, my - 6, 26, 12, 5)
            ctx.set_source_rgba(0.98, 0.98, 0.96, alpha)
            ctx.fill_preserve()
            set_ink(ctx, 3.0, alpha)
            ctx.stroke()
            # Teeth vertical lines
            for tx_off in (-5, 0, 5):
                ctx.move_to(mx + tx_off, my - 5)
                ctx.line_to(mx + tx_off, my + 5)
            set_ink(ctx, 2.0, alpha)
            ctx.stroke()
        else:
            # Slight downward worried arc
            ctx.move_to(mx - 10, my + 2)
            ctx.curve_to(mx - 4, my - 2, mx + 4, my - 2, mx + 10, my + 2)
            set_ink(ctx, 3.5, alpha)
            ctx.stroke()

    ctx.restore()  # end head
    ctx.restore()  # end character

# ==============================================================================
# NEIGHBOR RIG (Normal Gardener vs Tilted-Head Zombie Neighbor)
# ==============================================================================
def draw_neighbor(ctx, x, y, scale=1.0, is_zombie=False, head_tilt_deg=0.0,
                  watering=False, t=0.0, silhouette=False):
    ctx.save()
    ctx.translate(x, y)
    ctx.scale(scale, scale)

    # Stick legs
    if not is_zombie or scale < 1.3:
        set_ink(ctx, 6.5)
        ctx.move_to(-12, 25)
        ctx.line_to(-14, 175)
        ctx.move_to(12, 25)
        ctx.line_to(14, 175)
        ctx.stroke()

    # Green/tan plaid button-up shirt torso
    torso_top, torso_w, torso_h = -85, 68, 110
    rounded_rect_path(ctx, -torso_w * 0.5, torso_top, torso_w, torso_h, 14)
    if silhouette:
        ctx.set_source_rgb(0.12, 0.10, 0.09)
        ctx.fill_preserve()
        set_ink(ctx, 4.0)
        ctx.stroke()
    else:
        ctx.set_source_rgb(*hex_rgb("#687458" if not is_zombie else "#545D49"))
        ctx.fill()
        # Plaid stripes
        ctx.save()
        rounded_rect_path(ctx, -torso_w * 0.5, torso_top, torso_w, torso_h, 14)
        ctx.clip()
        ctx.set_source_rgba(0.84, 0.80, 0.66, 0.45)
        for py in range(torso_top + 14, torso_top + torso_h, 22):
            ctx.rectangle(-torso_w * 0.5, py, torso_w, 9)
            ctx.fill()
        for px in range(-24, 30, 20):
            ctx.rectangle(px, torso_top, 8, torso_h)
            ctx.fill()
        ctx.restore()
        rounded_rect_path(ctx, -torso_w * 0.5, torso_top, torso_w, torso_h, 14)
        set_ink(ctx, 4.0)
        ctx.stroke()

    # Arms & garden hose (if watering)
    if watering:
        set_ink(ctx, 6.0)
        ctx.move_to(0, -55)
        ctx.line_to(-38, -10)
        ctx.stroke()
        # Green hose & water spray arc
        ctx.move_to(-180, -35)
        ctx.curve_to(-160, 45, -10, 75, -42, -12)
        ctx.set_source_rgb(*hex_rgb("#2E5E36"))
        ctx.set_line_width(11.0)
        ctx.stroke_preserve()
        set_ink(ctx, 2.5)
        ctx.stroke()
        # Water spray arc
        for i in range(12):
            prog = ((i / 12.0 + t * 2.5) % 1.0)
            wx = -48 - prog * 95
            wy = -16 - math.sin(prog * math.pi) * 26 + prog * 18
            ctx.arc(wx, wy, 4.5 * (1.0 - prog * 0.4), 0, math.pi * 2)
            ctx.set_source_rgba(0.82, 0.94, 1.0, 0.85)
            ctx.fill()

    # Head + Straw Hat
    ctx.save()
    ctx.translate(0, torso_top - 58)
    ctx.rotate(math.radians(head_tilt_deg))

    head_r = 56
    ctx.arc(0, 0, head_r, 0, math.pi * 2)
    if silhouette:
        ctx.set_source_rgb(0.08, 0.06, 0.06)
    elif is_zombie:
        ctx.set_source_rgb(*hex_rgb("#8F9690"))
    else:
        ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
    ctx.fill_preserve()
    set_ink(ctx, 4.2)
    ctx.stroke()

    if not silhouette:
        # Grey side hair & mustache
        ctx.set_source_rgb(*hex_rgb("#9EA2A4"))
        ctx.arc(-32, -8, 16, 0.5, 2.6)
        ctx.fill()
        ctx.arc(32, -8, 16, 0.5, 2.6)
        ctx.fill()

        # Mustache
        ctx.move_to(-22, 16)
        ctx.curve_to(-10, 4, 10, 4, 22, 16)
        ctx.curve_to(10, 14, -10, 14, -22, 16)
        ctx.close_path()
        ctx.set_source_rgb(*hex_rgb("#9EA2A4"))
        ctx.fill_preserve()
        set_ink(ctx, 2.8)
        ctx.stroke()

        if is_zombie:
            # Blank white zombie eyes
            for ex in (-20, 20):
                ctx.arc(ex, -6, 11, 0, math.pi * 2)
                ctx.set_source_rgb(0.92, 0.94, 0.93)
                ctx.fill_preserve()
                set_ink(ctx, 3.0)
                ctx.stroke()
            # Open zombie mouth with jagged teeth
            rounded_rect_path(ctx, -16, 22, 32, 14, 6)
            ctx.set_source_rgb(*hex_rgb("#3A1614"))
            ctx.fill_preserve()
            set_ink(ctx, 3.0)
            ctx.stroke()
            ctx.rectangle(-9, 23, 5, 5)
            ctx.rectangle(5, 23, 5, 5)
            ctx.set_source_rgb(0.95, 0.95, 0.9)
            ctx.fill()
        else:
            # Normal calm eyes looking left
            ctx.arc(-26, -6, 4.5, 0, math.pi * 2)
            ctx.set_source_rgb(0.1, 0.1, 0.1)
            ctx.fill()

    # Straw garden hat (#C8B388)
    # Crown
    ctx.move_to(-44, -32)
    ctx.line_to(-32, -74)
    ctx.line_to(32, -74)
    ctx.line_to(44, -32)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#C8B388" if not is_zombie else "#8A7B5E"))
    ctx.fill_preserve()
    set_ink(ctx, 3.8)
    ctx.stroke()
    # Wide brim
    ctx.save()
    ctx.translate(0, -32)
    ctx.scale(1.0, 0.26)
    ctx.arc(0, 0, 86, 0, math.pi * 2)
    ctx.set_source_rgb(*hex_rgb("#BFA87A" if not is_zombie else "#786A50"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()
    ctx.restore()

    ctx.restore()  # end head
    ctx.restore()  # end neighbor

# ==============================================================================
# CARTOON HAND WITH PEN / MARKER (For Live Kinetic Notebook & Calendar Writing)
# ==============================================================================
def draw_hand_with_pen(ctx, tip_x, tip_y, pen_color="#1A1818", angle_deg=38.0, scale=1.0):
    """
    Draws Chad's long dark-sleeved arm and white cartoon hand holding a marker/pen
    whose nib touches exact coordinates (tip_x, tip_y).
    """
    ctx.save()
    ctx.translate(tip_x, tip_y)
    ctx.scale(scale, scale)

    # Slight writing oscillation
    rad = math.radians(angle_deg)
    ctx.rotate(rad)

    # Marker nib & barrel extending right from (0, 0)
    ctx.move_to(0, 0)
    ctx.line_to(16, -5)
    ctx.line_to(16, 5)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb(pen_color))
    ctx.fill_preserve()
    set_ink(ctx, 2.5)
    ctx.stroke()

    # Marker body
    rounded_rect_path(ctx, 16, -9, 105, 18, 4)
    ctx.set_source_rgb(0.95, 0.94, 0.92)
    ctx.fill_preserve()
    set_ink(ctx, 3.0)
    ctx.stroke()
    # Color band on marker
    ctx.rectangle(65, -8, 36, 16)
    ctx.set_source_rgb(*hex_rgb(pen_color))
    ctx.fill_preserve()
    set_ink(ctx, 2.5)
    ctx.stroke()

    # Cartoon white hand gripping marker around x=52, y=10
    ctx.arc(54, 12, 24, 0, math.pi * 2)
    ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
    ctx.fill_preserve()
    set_ink(ctx, 3.5)
    ctx.stroke()

    # Index finger extended along barrel
    rounded_rect_path(ctx, 22, -4, 34, 14, 7)
    ctx.set_source_rgb(*hex_rgb("#EAE4DC"))
    ctx.fill_preserve()
    set_ink(ctx, 3.2)
    ctx.stroke()

    # Knuckle crease lines
    ctx.arc(56, 14, 12, 0.3, 1.8)
    ctx.arc(62, 18, 10, 0.3, 1.8)
    set_ink(ctx, 2.2)
    ctx.stroke()

    # Long dark sleeve extending toward bottom-right corner
    ctx.move_to(72, 2)
    ctx.line_to(520, 75)
    ctx.line_to(500, 125)
    ctx.line_to(62, 32)
    ctx.close_path()
    ctx.set_source_rgb(*hex_rgb("#353942"))
    ctx.fill_preserve()
    set_ink(ctx, 4.0)
    ctx.stroke()

    ctx.restore()
