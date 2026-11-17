import os
import sys
import math
import subprocess
import numpy as np
import cairo

SCRATCH_DIR = r"C:\Users\WayWe Work-Station\.gemini\antigravity\brain\8ad88795-d9fa-438b-8430-13b89b7ef998\scratch\japan_job_project"
OUT_DIR = r"C:\Users\WayWe Work-Station\Downloads\Mate\Job Culture of japan"

W, H = 1080, 1920
FPS = 30
DURATION = 64.6008
TOTAL_FRAMES = int(round(DURATION * FPS))  # 1938 frames


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * clamp(t)


def ease_in_out(t):
    t = clamp(t)
    return t * t * (3.0 - 2.0 * t)


def ease_out_back(t):
    t = clamp(t)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * ((t - 1.0) ** 3) + c1 * ((t - 1.0) ** 2)


# ==============================================================================
# TRUE 3D CAMERA, 3D POLYGON RASTERIZER & 3D BOX/FURNITURE ENGINE
# ==============================================================================

class Camera3D:
    def __init__(self, pos=(0.0, 140.0, -420.0), target=(0.0, 110.0, 0.0), fov=1100.0, roll=0.0):
        self.pos = np.array(pos, dtype=np.float64)
        self.target = np.array(target, dtype=np.float64)
        self.fov = float(fov)
        self.roll = float(roll)

        fwd = self.target - self.pos
        fwd_len = np.linalg.norm(fwd)
        self.fwd = fwd / (fwd_len if fwd_len > 1e-6 else 1.0)

        up_ref = np.array([math.sin(self.roll), math.cos(self.roll), 0.0], dtype=np.float64)
        right = np.cross(up_ref, self.fwd)
        r_len = np.linalg.norm(right)
        if r_len < 1e-6:
            right = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        else:
            right = right / r_len
        self.right = right
        self.up = np.cross(self.fwd, self.right)

    def project(self, pt3d):
        v = np.asarray(pt3d, dtype=np.float64) - self.pos
        x_cam = float(np.dot(v, self.right))
        y_cam = float(np.dot(v, self.up))
        z_cam = float(np.dot(v, self.fwd))
        depth = max(35.0, z_cam)
        scale = self.fov / depth
        sx = W * 0.5 + x_cam * scale
        sy = H * 0.5 - y_cam * scale
        return sx, sy, depth, scale


def draw_poly_3d(ctx, cam, pts3d, fill_rgb, stroke_rgb=(0.10, 0.09, 0.12), stroke_w=4.0, alpha=1.0):
    proj_pts = [cam.project(p) for p in pts3d]
    ctx.move_to(proj_pts[0][0], proj_pts[0][1])
    for p in proj_pts[1:]:
        ctx.line_to(p[0], p[1])
    ctx.close_path()
    if fill_rgb is not None:
        ctx.set_source_rgba(fill_rgb[0], fill_rgb[1], fill_rgb[2], alpha)
        if stroke_rgb is not None and stroke_w > 0:
            ctx.fill_preserve()
        else:
            ctx.fill()
    if stroke_rgb is not None and stroke_w > 0:
        ctx.set_source_rgba(stroke_rgb[0], stroke_rgb[1], stroke_rgb[2], alpha)
        ctx.set_line_width(stroke_w)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.stroke()


def draw_box_3d(ctx, cam, center, size, rot_y=0.0, top_rgb=(0.8, 0.8, 0.8), front_rgb=(0.7, 0.7, 0.7), side_rgb=(0.55, 0.55, 0.55), stroke_w=4.0):
    cx, cy, cz = center
    wx, wy, wz = size[0] * 0.5, size[1] * 0.5, size[2] * 0.5
    c, s = math.cos(rot_y), math.sin(rot_y)

    def tf(lx, ly, lz):
        rx = lx * c + lz * s
        rz = -lx * s + lz * c
        return (cx + rx, cy + ly, cz + rz)

    # 8 vertices
    v = [
        tf(-wx, -wy, -wz),  # 0: bot-left-front
        tf(wx, -wy, -wz),   # 1: bot-right-front
        tf(wx, wy, -wz),    # 2: top-right-front
        tf(-wx, wy, -wz),   # 3: top-left-front
        tf(-wx, -wy, wz),   # 4: bot-left-back
        tf(wx, -wy, wz),    # 5: bot-right-back
        tf(wx, wy, wz),     # 6: top-right-back
        tf(-wx, wy, wz),    # 7: top-left-back
    ]
    faces = [
        ([v[0], v[1], v[2], v[3]], front_rgb),
        ([v[4], v[5], v[6], v[7]], front_rgb),
        ([v[0], v[4], v[7], v[3]], side_rgb),
        ([v[1], v[5], v[6], v[2]], side_rgb),
        ([v[3], v[2], v[6], v[7]], top_rgb),
        ([v[0], v[1], v[5], v[4]], side_rgb),
    ]
    # Painter's algorithm sort by average camera depth
    face_depths = []
    for f_pts, f_col in faces:
        avg_d = sum(cam.project(p)[2] for p in f_pts) / 4.0
        face_depths.append((avg_d, f_pts, f_col))
    face_depths.sort(key=lambda x: x[0], reverse=True)
    # Draw furthest 3 back faces, then closest 3 front faces
    for _, f_pts, f_col in face_depths[3:]:
        draw_poly_3d(ctx, cam, f_pts, f_col, stroke_w=stroke_w)


def draw_3d_sphere_shaded(ctx, sx, sy, r, light_rgb, mid_rgb, dark_rgb, stroke_w=5.0, alpha=1.0, light_dir=(-0.32, -0.32)):
    if r <= 1.0:
        return
    rad = cairo.RadialGradient(sx + light_dir[0] * r, sy + light_dir[1] * r, r * 0.08, sx, sy, r)
    rad.add_color_stop_rgba(0.0, light_rgb[0], light_rgb[1], light_rgb[2], alpha)
    rad.add_color_stop_rgba(0.58, mid_rgb[0], mid_rgb[1], mid_rgb[2], alpha)
    rad.add_color_stop_rgba(1.0, dark_rgb[0], dark_rgb[1], dark_rgb[2], alpha)
    ctx.set_source(rad)
    ctx.arc(sx, sy, r, 0, 2 * math.pi)
    if stroke_w > 0:
        ctx.fill_preserve()
        ctx.set_source_rgba(0.10, 0.09, 0.12, alpha)
        ctx.set_line_width(stroke_w)
        ctx.stroke()
    else:
        ctx.fill()


# ==============================================================================
# 18-JOINT 3D SKELETAL RIGGED CHARACTER ENGINE (IK/FK + 3D HEAD/FACE RIG)
# ==============================================================================

def draw_curved_limb_3d(ctx, cam, p_start, p_joint, p_end, thickness=9.5, col=(0.10, 0.09, 0.12)):
    """
    Renders a smooth, articulated 3D limb through (shoulder/hip -> elbow/knee -> wrist/ankle)
    using cubic Bezier smoothing around the joint while preserving crisp joint articulation!
    """
    s0 = cam.project(p_start)
    s1 = cam.project(p_joint)
    s2 = cam.project(p_end)
    avg_scale = (s0[3] + s1[3] + s2[3]) / 3.0
    lw = max(3.0, thickness * avg_scale)

    ctx.save()
    ctx.set_source_rgb(*col)
    ctx.set_line_width(lw)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    # Smooth rubber-hose + joint blend
    c1x = lerp(s0[0], s1[0], 0.72)
    c1y = lerp(s0[1], s1[1], 0.72)
    c2x = lerp(s2[0], s1[0], 0.72)
    c2y = lerp(s2[1], s1[1], 0.72)
    ctx.move_to(s0[0], s0[1])
    ctx.curve_to(c1x, c1y, c2x, c2y, s2[0], s2[1])
    ctx.stroke()
    ctx.restore()
    return s0, s1, s2


def draw_rigged_character_3d(
    ctx,
    cam,
    pos3d=(0.0, 0.0, 0.0),
    yaw=0.0,
    scale=1.0,
    role="ken",
    expr="neutral",
    head_rot=(0.0, 0.0, 0.0),  # (head_yaw, head_pitch, head_roll)
    spine_lean=(0.0, 0.0),     # (forward_pitch, side_lean)
    pose="stand",
    t=0.0,
    sunglasses=False,
    prop=None,
):
    """
    Full 18-joint 3D skeletal rigged character matching Jap vid.mp4:
    - Floor shadow ellipse in 3D
    - Articulated 3D pelvis, spine, chest, neck, head
    - Articulated 3D legs (hip -> knee -> ankle -> 3D shoe)
    - Articulated 3D arms (shoulder -> elbow -> wrist -> 3D hand + fingers + prop)
    - 3D spherical head with perspective-foreshortened face, blinking eyelids, & 3D hair dome
    """
    bx, by, bz = pos3d
    cy, sy = math.cos(yaw), math.sin(yaw)
    sp_pitch, sp_side = spine_lean

    # Subtle breathing motion
    breath = math.sin(t * 3.2 + bx * 0.02) * 2.2

    # Walk cycle kinematics if pose == 'walk'
    walk_bounce = 0.0
    if pose == "walk":
        w_ph = t * 8.5
        walk_bounce = abs(math.sin(w_ph)) * 8.0
        sp_pitch += 0.08
    elif pose == "recline_feet_up":
        sp_pitch = -0.42

    def local_to_world(lx, ly, lz, apply_spine=True):
        x, y, z = lx * scale, ly * scale, lz * scale
        if apply_spine and y > 65.0 * scale:
            dy_sp = y - 65.0 * scale
            z -= math.sin(sp_pitch) * dy_sp
            x += math.sin(sp_side) * dy_sp
            y = 65.0 * scale + math.cos(sp_pitch) * math.cos(sp_side) * dy_sp
        wx = bx + (x * cy + z * sy)
        wz = bz + (-x * sy + z * cy)
        wy = by + y + walk_bounce * scale
        return (wx, wy, wz)

    # 1. Floor contact shadow in 3D
    if pose != "head_peek":
        sh_pts = []
        for a in range(12):
            ang = a * (2 * math.pi / 12)
            sh_pts.append((bx + math.cos(ang) * 42 * scale, by + 1.0, bz + math.sin(ang) * 32 * scale))
        draw_poly_3d(ctx, cam, sh_pts, (0.04, 0.06, 0.14), stroke_rgb=None, alpha=0.28)

    # 2. Compute 3D Leg Joints (Hip -> Knee -> Ankle -> Foot)
    if pose == "walk":
        w_ph = t * 8.5
        s_l = math.sin(w_ph)
        s_r = math.sin(w_ph + math.pi)
        l_hip = local_to_world(-15, 72, 0, False)
        r_hip = local_to_world(15, 72, 0, False)
        l_knee = local_to_world(-16, 38 + max(0, s_l) * 14, -s_l * 22, False)
        r_knee = local_to_world(16, 38 + max(0, s_r) * 14, -s_r * 22, False)
        l_ank = local_to_world(-16, 6 + max(0, -s_l) * 12, -s_l * 34, False)
        r_ank = local_to_world(16, 6 + max(0, -s_r) * 12, -s_r * 34, False)
        l_toe = local_to_world(-18, 2 + max(0, -s_l) * 10, -s_l * 34 - 22, False)
        r_toe = local_to_world(18, 2 + max(0, -s_r) * 10, -s_r * 34 - 22, False)
    elif pose == "recline_feet_up":
        # Seated in swivel chair with legs extended forward onto desk & crossed at ankles!
        l_hip = local_to_world(-16, 72, -10, False)
        r_hip = local_to_world(16, 72, -10, False)
        l_knee = local_to_world(-18, 86, -65, False)
        r_knee = local_to_world(14, 82, -65, False)
        l_ank = local_to_world(-6, 102, -125, False)
        r_ank = local_to_world(8, 96, -122, False)
        l_toe = local_to_world(-12, 128, -130, False)
        r_toe = local_to_world(14, 122, -128, False)
    elif pose == "bend_inspect":
        l_hip = local_to_world(-16, 72, 15, False)
        r_hip = local_to_world(16, 72, 15, False)
        l_knee = local_to_world(-18, 38, 4, False)
        r_knee = local_to_world(18, 38, 12, False)
        l_ank = local_to_world(-18, 4, 10, False)
        r_ank = local_to_world(18, 4, 18, False)
        l_toe = local_to_world(-20, 2, -14, False)
        r_toe = local_to_world(20, 2, -6, False)
    else:
        l_hip = local_to_world(-16, 72, 0, False)
        r_hip = local_to_world(16, 72, 0, False)
        l_knee = local_to_world(-18, 38, -4, False)
        r_knee = local_to_world(18, 38, -4, False)
        l_ank = local_to_world(-18, 4, 0, False)
        r_ank = local_to_world(18, 4, 0, False)
        l_toe = local_to_world(-22, 2, -22, False)
        r_toe = local_to_world(22, 2, -22, False)

    if pose != "head_peek":
        for hip_p, knee_p, ank_p, toe_p in [(l_hip, l_knee, l_ank, l_toe), (r_hip, r_knee, r_ank, r_toe)]:
            draw_curved_limb_3d(ctx, cam, hip_p, knee_p, ank_p, thickness=8.5 * scale)
            # 3D Shoe at ankle -> toe
            sh_col = (0.45, 0.24, 0.12) if role == "taro" else (0.14, 0.14, 0.18)
            sa = cam.project(ank_p)
            st = cam.project(toe_p)
            ctx.save()
            ctx.set_source_rgb(*sh_col)
            ctx.set_line_width(max(4.0, 14.0 * sa[3] * scale))
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(sa[0], sa[1])
            ctx.line_to(st[0], st[1])
            ctx.stroke()
            ctx.restore()

    # 3. 3D Torso Mesh (Pelvis -> Chest) with 3D Shading, Tie & ID Lanyard
    p_pelvis = local_to_world(0, 68, 0, True)
    p_chest = local_to_world(0, 142 + breath, 0, True)
    s_pel = cam.project(p_pelvis)
    s_che = cam.project(p_chest)

    if role == "boss":
        c_top, c_bot = (0.20, 0.20, 0.28), (0.08, 0.08, 0.12)
    elif role == "ken":
        c_top, c_bot = (0.52, 0.76, 0.98), (0.28, 0.52, 0.84)
    elif role == "taro":
        c_top, c_bot = (0.14, 0.78, 0.64), (0.06, 0.48, 0.38)
    elif role == "new_guy":
        c_top, c_bot = (0.98, 0.98, 1.00), (0.80, 0.82, 0.88)
    elif role == "coworker_purple":
        c_top, c_bot = (0.64, 0.28, 0.88), (0.38, 0.14, 0.58)
    elif role == "coworker_yellow":
        c_top, c_bot = (0.98, 0.78, 0.18), (0.76, 0.54, 0.08)
    else:
        c_top, c_bot = (0.88, 0.34, 0.28), (0.62, 0.18, 0.14)

    # Project 3D torso silhouette points
    t_tl = cam.project(local_to_world(-30, 140 + breath, 0, True))
    t_tr = cam.project(local_to_world(30, 140 + breath, 0, True))
    t_br = cam.project(local_to_world(32, 68, 0, True))
    t_bl = cam.project(local_to_world(-32, 68, 0, True))

    tpat = cairo.LinearGradient(t_tl[0], t_tl[1], t_br[0], t_br[1])
    tpat.add_color_stop_rgb(0.0, *c_top)
    tpat.add_color_stop_rgb(1.0, *c_bot)
    ctx.set_source(tpat)
    ctx.move_to(t_tl[0], t_tl[1])
    ctx.line_to(t_tr[0], t_tr[1])
    ctx.curve_to(t_br[0] + 6, lerp(t_tr[1], t_br[1], 0.5), t_br[0] + 4, t_br[1], t_br[0], t_br[1])
    ctx.line_to(t_bl[0], t_bl[1])
    ctx.curve_to(t_bl[0] - 4, t_bl[1], t_bl[0] - 6, lerp(t_tl[1], t_bl[1], 0.5), t_tl[0], t_tl[1])
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgb(0.10, 0.09, 0.12)
    ctx.set_line_width(max(2.5, 4.8 * s_che[3] * scale))
    ctx.stroke()

    # Shirt V-neck, Tie & Lanyard projected in 3D on the front of the chest
    if abs(yaw) < math.pi * 0.65:
        v_l = cam.project(local_to_world(-13, 140 + breath, -16, True))
        v_r = cam.project(local_to_world(13, 140 + breath, -16, True))
        v_b = cam.project(local_to_world(0, 108 + breath, -18, True))
        t_tip = cam.project(local_to_world(0, 82 + breath, -18, True))

        if role in ("boss", "ken", "new_guy"):
            # White collar V
            ctx.set_source_rgb(0.98, 0.98, 1.0)
            ctx.move_to(v_l[0], v_l[1])
            ctx.line_to(v_r[0], v_r[1])
            ctx.line_to(v_b[0], v_b[1])
            ctx.close_path()
            ctx.fill()
            # Tie
            tie_col = (0.88, 0.14, 0.14) if role == "boss" else ((0.14, 0.28, 0.68) if role == "ken" else (0.22, 0.72, 0.30))
            ctx.set_source_rgb(*tie_col)
            ctx.set_line_width(max(3.0, 9.0 * s_che[3] * scale))
            ctx.move_to((v_l[0] + v_r[0]) * 0.5, (v_l[1] + v_r[1]) * 0.5)
            ctx.line_to(t_tip[0], t_tip[1])
            ctx.stroke()

        if role == "ken":
            # Swinging white ID badge on lanyard
            sway_x = math.sin(t * 6.0) * 4.0 if pose == "walk" else 0.0
            b_pos = cam.project(local_to_world(sway_x, 92 + breath, -21, True))
            bw, bh = 18 * b_pos[3] * scale, 24 * b_pos[3] * scale
            ctx.set_source_rgb(0.98, 0.98, 1.0)
            ctx.rectangle(b_pos[0] - bw * 0.5, b_pos[1] - bh * 0.5, bw, bh)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.10, 0.09, 0.12)
            ctx.set_line_width(max(1.5, 2.8 * b_pos[3] * scale))
            ctx.stroke()

    # 4. Compute 3D Arm Joints (Shoulder -> Elbow -> Wrist -> Hand/Prop)
    sh_l = local_to_world(-32, 134 + breath, 0, True)
    sh_r = local_to_world(32, 134 + breath, 0, True)

    if pose == "walk":
        w_ph = t * 8.5
        a_l = math.sin(w_ph + math.pi) * 24
        a_r = math.sin(w_ph) * 24
        el_l = local_to_world(-38, 102, a_l * 0.5, True)
        wr_l = local_to_world(-36, 74, a_l - 8, True)
        el_r = local_to_world(38, 102, a_r * 0.5, True)
        wr_r = local_to_world(36, 74, a_r - 8, True)
    elif pose == "dangling_key":
        el_l = local_to_world(-40, 102, -8, True)
        wr_l = local_to_world(-36, 74, -14, True)
        el_r = local_to_world(48, 118, -22, True)
        wr_r = local_to_world(76, 136 + math.sin(t * 5) * 4, -35, True)
    elif pose == "recline_feet_up":
        el_l = local_to_world(-38, 105, -22, True)
        wr_l = local_to_world(-14, 112, -45, True)
        el_r = local_to_world(38, 105, -22, True)
        wr_r = local_to_world(14, 112 + math.sin(t * 6) * 3, -45, True)
    elif pose == "gift_box_open":
        open_p = clamp((t - 15.6) / 0.8)
        el_l = local_to_world(-42, 104, -24, True)
        wr_l = local_to_world(-26, 98, -48, True)
        el_r = local_to_world(44, 108 + open_p * 18, -24, True)
        wr_r = local_to_world(28 + open_p * 26, 104 + open_p * 34, -48, True)
    elif pose == "bend_inspect":
        el_l = local_to_world(-36, 104, -22, True)
        wr_l = local_to_world(-28, 78, -45, True)
        el_r = local_to_world(36, 102, -18, True)
        wr_r = local_to_world(28, 76, -38, True)
    elif pose == "flip_breaker":
        el_l = local_to_world(-38, 102, -8, True)
        wr_l = local_to_world(-36, 74, -12, True)
        el_r = local_to_world(48, 112, -18, True)
        wr_r = local_to_world(78, 118 - ((t * 2.2) % 1.0) * 28, -25, True)
    else:
        el_l = local_to_world(-38, 102, -6, True)
        wr_l = local_to_world(-36, 72, -12, True)
        el_r = local_to_world(38, 102, -6, True)
        wr_r = local_to_world(36, 72, -12, True)

    for sh_p, el_p, wr_p in [(sh_l, el_l, wr_l), (sh_r, el_r, wr_r)]:
        _, _, s_wr = draw_curved_limb_3d(ctx, cam, sh_p, el_p, wr_p, thickness=8.0 * scale)
        # 3D Hand sphere
        draw_3d_sphere_shaded(ctx, s_wr[0], s_wr[1], 7.5 * s_wr[3] * scale, (1.0, 1.0, 1.0), (0.92, 0.92, 0.94), (0.75, 0.75, 0.78), stroke_w=2.5 * s_wr[3] * scale)

    # Held 3D Props attached to hands
    if prop == "storage_key":
        kw = cam.project(wr_r)
        ks = kw[3] * scale
        sw_ang = math.sin(t * 5.5) * 0.14
        ctx.save()
        ctx.translate(kw[0], kw[1])
        ctx.rotate(sw_ang)
        # Metal key ring
        ctx.set_source_rgb(0.75, 0.78, 0.82)
        ctx.set_line_width(3.5 * ks)
        ctx.arc(0, 14 * ks, 10 * ks, 0, 2 * math.pi)
        ctx.stroke()
        # Red 'STORAGE' tag
        ctx.set_source_rgb(0.86, 0.16, 0.14)
        ctx.rectangle(-12 * ks, 24 * ks, 24 * ks, 64 * ks)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.09, 0.12)
        ctx.set_line_width(3 * ks)
        ctx.stroke()
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(11 * ks)
        ctx.set_source_rgb(1.0, 0.92, 0.45)
        for ch_i, ch in enumerate("STORAGE"):
            ctx.move_to(-4 * ks, (36 + ch_i * 7.5) * ks)
            ctx.show_text(ch)
        ctx.restore()
    elif prop == "phone":
        pw = cam.project(wr_r)
        ps = pw[3] * scale
        ctx.save()
        ctx.translate(pw[0] - 12 * ps, pw[1] - 28 * ps)
        ctx.set_source_rgb(0.12, 0.14, 0.18)
        ctx.rectangle(0, 0, 28 * ps, 48 * ps)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.28, 0.78, 0.96)
        ctx.rectangle(3 * ps, 4 * ps, 22 * ps, 40 * ps)
        ctx.fill()
        ctx.restore()
    elif prop == "gift_box":
        open_p = clamp((t - 15.6) / 0.8)
        box_c = local_to_world(0, 92, -48, True)
        draw_box_3d(ctx, cam, box_c, (58 * scale, 46 * scale, 48 * scale), rot_y=yaw, top_rgb=(0.18, 0.05, 0.05), front_rgb=(0.86, 0.16, 0.16), side_rgb=(0.62, 0.10, 0.10), stroke_w=4.0)
        # Lid lifting up and tilting right
        lid_c = local_to_world(open_p * 34, 118 + open_p * 24, -48, True)
        draw_box_3d(ctx, cam, lid_c, (62 * scale, 12 * scale, 52 * scale), rot_y=yaw - open_p * 0.4, top_rgb=(0.94, 0.22, 0.20), front_rgb=(0.86, 0.16, 0.16), side_rgb=(0.96, 0.80, 0.18), stroke_w=4.0)
    elif prop == "drink":
        dw = cam.project(wr_r)
        ds = dw[3] * scale
        ctx.save()
        ctx.translate(dw[0], dw[1] - 18 * ds)
        ctx.set_source_rgb(0.98, 0.72, 0.14)
        ctx.rectangle(-12 * ds, 0, 24 * ds, 32 * ds)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.09, 0.12)
        ctx.set_line_width(3 * ds)
        ctx.stroke()
        # Pink straw
        ctx.set_source_rgb(0.96, 0.28, 0.52)
        ctx.move_to(0, 0)
        ctx.line_to(8 * ds, -16 * ds)
        ctx.stroke()
        ctx.restore()

    # 5. 3D Spherical Head & Surface-Projected 3D Face + Hair
    p_head = local_to_world(0, 186 + breath, 0, True)
    sh_x, sh_y, _, sh_s = cam.project(p_head)
    hr = 46.0 * sh_s * scale

    hyaw, hpitch, hroll = head_rot
    total_hyaw = yaw + hyaw

    ctx.save()
    ctx.translate(sh_x, sh_y)
    ctx.rotate(hroll)

    # 3D shaded white head sphere
    draw_3d_sphere_shaded(ctx, 0, 0, hr, (1.0, 1.0, 1.0), (0.94, 0.93, 0.92), (0.74, 0.73, 0.76), stroke_w=max(3.0, 5.2 * sh_s * scale))

    # 3D Hair Cap (shifts with total_hyaw & hpitch)
    if role == "boss":
        hl, hd = (0.76, 0.76, 0.80), (0.48, 0.48, 0.54)
    elif role == "ken":
        hl, hd = (0.22, 0.20, 0.26), (0.08, 0.08, 0.12)
    else:
        hl, hd = (0.48, 0.30, 0.14), (0.26, 0.15, 0.06)

    hpat = cairo.LinearGradient(-hr, -hr, hr, hr * 0.2)
    hpat.add_color_stop_rgb(0.0, *hl)
    hpat.add_color_stop_rgb(1.0, *hd)
    ctx.set_source(hpat)

    if abs(total_hyaw) > math.pi * 0.65:
        # Back of head hair dome
        ctx.arc(0, -hr * 0.08, hr * 1.02, math.pi * 0.82, math.pi * 2.18)
        ctx.curve_to(hr * 0.6, hr * 0.35, -hr * 0.6, hr * 0.35, -hr * 0.98, hr * 0.25)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.09, 0.12)
        ctx.set_line_width(max(2.5, 4.5 * sh_s * scale))
        ctx.stroke()
        ctx.restore()
        return

    # Front/3-4 hair cap with side-part curve
    hx_shift = math.sin(total_hyaw) * hr * 0.22
    hy_shift = math.sin(hpitch) * hr * 0.22
    ctx.arc(0, -hr * 0.08, hr * 1.02, math.pi * 0.90, math.pi * 2.10)
    ctx.curve_to(hr * 0.45 + hx_shift, -hr * 0.22 + hy_shift, -hr * 0.25 + hx_shift, -hr * 0.12 + hy_shift, -hr * 0.98, -hr * 0.16 + hy_shift)
    ctx.close_path()
    ctx.fill_preserve()
    ctx.set_source_rgb(0.10, 0.09, 0.12)
    ctx.set_line_width(max(2.5, 4.5 * sh_s * scale))
    ctx.stroke()

    # Face center shifted by 3D spherical rotation (total_hyaw, hpitch)
    fx = math.sin(total_hyaw) * hr * 0.42
    fy = math.sin(hpitch) * hr * 0.38
    foreshorten = max(0.45, math.cos(total_hyaw))

    # Automatic natural eye blink every 3.1 seconds
    is_blink = ((t + bx * 0.01) % 3.1) > 2.96

    if sunglasses:
        ctx.set_source_rgb(0.08, 0.08, 0.10)
        for sx_dir in (-1, 1):
            gx = fx + sx_dir * hr * 0.32 * foreshorten
            gy = fy - hr * 0.04
            ctx.rectangle(gx - hr * 0.24 * foreshorten, gy - hr * 0.14, hr * 0.48 * foreshorten, hr * 0.28)
            ctx.fill()
        ctx.set_line_width(max(2.5, 4.5 * sh_s * scale))
        ctx.move_to(fx - hr * 0.65 * foreshorten, fy - hr * 0.04)
        ctx.line_to(fx + hr * 0.65 * foreshorten, fy - hr * 0.04)
        ctx.stroke()
    else:
        for sx_dir in (-1, 1):
            ex = fx + sx_dir * hr * 0.31 * foreshorten
            ey = fy + hr * 0.04
            er = hr * 0.20 * (0.85 if sx_dir * total_hyaw > 0 else 1.0)

            if expr in ("closed_smile", "boss_grin") or is_blink:
                ctx.set_source_rgb(0.10, 0.09, 0.12)
                ctx.set_line_width(max(2.5, 4.8 * sh_s * scale))
                ctx.arc(ex, ey + er * 0.2, er * 0.75, math.pi * 1.1, math.pi * 1.9)
                ctx.stroke()
            else:
                ctx.set_source_rgb(0.99, 0.99, 1.0)
                ctx.arc(ex, ey, er, 0, 2 * math.pi)
                ctx.fill_preserve()
                ctx.set_source_rgb(0.10, 0.09, 0.12)
                ctx.set_line_width(max(2.0, 3.6 * sh_s * scale))
                ctx.stroke()
                # Pupil tracking
                ctx.arc(ex + math.sin(hyaw) * er * 0.35, ey + math.sin(hpitch) * er * 0.3, er * 0.38, 0, 2 * math.pi)
                ctx.fill()

            # 3D Eyebrows
            ctx.set_source_rgb(0.14, 0.10, 0.08)
            ctx.set_line_width(max(2.5, 5.2 * sh_s * scale))
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            by_off = -er * 1.25
            if expr in ("worried", "miserable"):
                ctx.move_to(ex - er * 0.8, ey + by_off + sx_dir * er * 0.25)
                ctx.line_to(ex + er * 0.8, ey + by_off - sx_dir * er * 0.25)
            else:
                ctx.move_to(ex - er * 0.8, ey + by_off)
                ctx.line_to(ex + er * 0.8, ey + by_off)
            ctx.stroke()

    # Mouths
    mx, my = fx, fy + hr * 0.44
    mw = hr * 0.44 * foreshorten
    mh = hr * 0.26
    ctx.set_source_rgb(0.10, 0.09, 0.12)
    ctx.set_line_width(max(2.2, 4.2 * sh_s * scale))
    if expr in ("boss_grin", "grin"):
        ctx.set_source_rgb(0.99, 0.99, 1.0)
        ctx.rectangle(mx - mw, my - mh * 0.5, mw * 2, mh)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.09, 0.12)
        ctx.stroke()
        ctx.move_to(mx - mw, my)
        ctx.line_to(mx + mw, my)
        ctx.stroke()
        for tx_m in (-0.5, 0.0, 0.5):
            ctx.move_to(mx + tx_m * mw * 2, my - mh * 0.5)
            ctx.line_to(mx + tx_m * mw * 2, my + mh * 0.5)
            ctx.stroke()
    elif expr in ("worried", "miserable"):
        ctx.arc(mx, my + mh * 0.5, mw * 0.65, math.pi * 1.15, math.pi * 1.85)
        ctx.stroke()
    else:
        ctx.move_to(mx - mw * 0.6, my)
        ctx.curve_to(mx - mw * 0.1, my + mh * 0.35, mx + mw * 0.2, my + mh * 0.3, mx + mw * 0.65, my - mh * 0.15)
        ctx.stroke()

    ctx.restore()


# ==============================================================================
# TRUE 3D ENVIRONMENTS & FURNITURE MESHES (GREEN ROOM, OFFICE, HALLWAY)
# ==============================================================================

def draw_3d_green_room_and_furniture(
    ctx,
    cam,
    t,
    show_sunbeam=True,
    cal_month="APR",
    cal_day="7",
    door_open_angle=0.0,
    show_desk_tape=False,
    show_coffee_rings=False,
):
    """
    Renders the 3D Lime-Green Cinder-Block Banishment Room in true 3D perspective:
    - Back wall (z = 220), Right corner wall (x = 240), Left wall (x = -260)
    - 3D Ceiling grid (y = 320) & 3D Gray Tile Floor grid (y = 0)
    - 3D Red-rimmed ticking wall clock on back wall
    - 3D Tear-off Calendar on back wall
    - 3D Doorway with swinging light-blue 3D door ('CAREER DEVELOPMENT ROOM')
    - 3D Gray Metal Desk (with 4 legs, drawer pedestal, optional yellow tape or coffee stains)
    - 3D Swivel Office Chair
    """
    # 0. Clear full canvas with ceiling/room ambient base color
    ctx.set_source_rgb(0.88, 0.92, 0.96)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    # 1. 3D Floor (y = 0) with tile grid
    draw_poly_3d(ctx, cam, [(-420, 0, -320), (420, 0, -320), (420, 0, 320), (-420, 0, 320)], (0.52, 0.62, 0.76), stroke_rgb=None)
    for gx in range(-360, 380, 60):
        p0 = cam.project((gx, 0, -320))
        p1 = cam.project((gx, 0, 320))
        ctx.set_source_rgba(0.38, 0.48, 0.62, 0.45)
        ctx.set_line_width(2.5)
        ctx.move_to(p0[0], p0[1])
        ctx.line_to(p1[0], p1[1])
        ctx.stroke()
    for gz in range(-280, 320, 60):
        p0 = cam.project((-420, 0, gz))
        p1 = cam.project((420, 0, gz))
        ctx.move_to(p0[0], p0[1])
        ctx.line_to(p1[0], p1[1])
        ctx.stroke()

    # 2. 3D Back Wall (z = 220) & Right Wall (x = 220) with 3D brick lines
    draw_poly_3d(ctx, cam, [(-420, 0, 220), (220, 0, 220), (220, 520, 220), (-420, 520, 220)], (0.56, 0.80, 0.44), stroke_w=5.0)
    draw_poly_3d(ctx, cam, [(220, 0, 220), (220, 0, -320), (220, 520, -320), (220, 520, 220)], (0.48, 0.72, 0.36), stroke_w=5.0)

    # Brick mortar lines on back wall and right wall in 3D
    ctx.set_source_rgba(0.38, 0.58, 0.28, 0.55)
    ctx.set_line_width(2.5)
    for by_l in range(30, 480, 30):
        p0 = cam.project((-380, by_l, 219))
        p1 = cam.project((220, by_l, 219))
        ctx.move_to(p0[0], p0[1])
        ctx.line_to(p1[0], p1[1])
        ctx.stroke()
        p2 = cam.project((219, by_l, 220))
        p3 = cam.project((219, by_l, -280))
        ctx.move_to(p2[0], p2[1])
        ctx.line_to(p3[0], p3[1])
        ctx.stroke()

    # 3D Broken Printer on stand in back-left corner (-210, 0..115, 165) & 3D Bookshelf on right wall
    draw_box_3d(ctx, cam, (-205, 42, 165), (54, 84, 48), top_rgb=(0.72, 0.76, 0.82), front_rgb=(0.58, 0.62, 0.68), side_rgb=(0.45, 0.48, 0.54))
    draw_box_3d(ctx, cam, (-205, 98, 165), (46, 28, 42), top_rgb=(0.88, 0.90, 0.94), front_rgb=(0.95, 0.82, 0.22), side_rgb=(0.68, 0.70, 0.76))
    draw_box_3d(ctx, cam, (195, 85, 145), (38, 170, 65), top_rgb=(0.38, 0.42, 0.48), front_rgb=(0.76, 0.56, 0.34), side_rgb=(0.62, 0.44, 0.24))

    # Warm 3D Sunbeam across back wall
    if show_sunbeam:
        draw_poly_3d(
            ctx,
            cam,
            [(218, 260, 218), (-110, 140, 218), (-110, 55, 218), (218, 175, 218)],
            (1.0, 0.92, 0.26),
            stroke_rgb=None,
            alpha=0.58,
        )

    # 3. 3D Red-Rimmed Wall Clock at (45, 245, 216)
    clk_c = cam.project((45, 245, 216))
    cr = 38.0 * clk_c[3]
    ctx.set_source_rgb(0.78, 0.18, 0.20)
    ctx.arc(clk_c[0], clk_c[1], cr, 0, 2 * math.pi)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.10, 0.09, 0.12)
    ctx.set_line_width(4.0)
    ctx.stroke()
    ctx.set_source_rgb(0.99, 0.99, 1.0)
    ctx.arc(clk_c[0], clk_c[1], cr * 0.82, 0, 2 * math.pi)
    ctx.fill()
    # Clock hands
    sec_ang = int(t) * (2 * math.pi / 60.0) - math.pi / 2
    ctx.set_source_rgb(0.10, 0.10, 0.12)
    ctx.set_line_width(3.5)
    ctx.move_to(clk_c[0], clk_c[1])
    ctx.line_to(clk_c[0] - cr * 0.42, clk_c[1] - cr * 0.25)
    ctx.move_to(clk_c[0], clk_c[1])
    ctx.line_to(clk_c[0] + cr * 0.48, clk_c[1] - cr * 0.35)
    ctx.stroke()
    ctx.set_source_rgb(0.86, 0.16, 0.16)
    ctx.set_line_width(2.2)
    ctx.move_to(clk_c[0], clk_c[1])
    ctx.line_to(clk_c[0] + math.cos(sec_ang) * cr * 0.68, clk_c[1] + math.sin(sec_ang) * cr * 0.68)
    ctx.stroke()

    # 4. 3D Wall Calendar at (-165, 195, 216)
    cal_p = cam.project((-165, 195, 216))
    cs = cal_p[3]
    ctx.set_source_rgb(0.99, 0.99, 1.0)
    ctx.rectangle(cal_p[0] - 28 * cs, cal_p[1] - 34 * cs, 56 * cs, 68 * cs)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.10, 0.09, 0.12)
    ctx.set_line_width(3.0)
    ctx.stroke()
    ctx.set_source_rgb(0.86, 0.18, 0.16)
    ctx.rectangle(cal_p[0] - 28 * cs, cal_p[1] - 34 * cs, 56 * cs, 18 * cs)
    ctx.fill()
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(11 * cs)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(cal_p[0] - 14 * cs, cal_p[1] - 21 * cs)
    ctx.show_text(cal_month)
    ctx.set_font_size(22 * cs)
    ctx.set_source_rgb(0.12, 0.12, 0.14)
    ctx.move_to(cal_p[0] - 14 * cs, cal_p[1] + 22 * cs)
    ctx.show_text(cal_day)

    # 5. 3D Doorway at (-75, 0..220, 218) when door_open_angle > 0
    if door_open_angle > 0.01:
        draw_poly_3d(ctx, cam, [(-125, 0, 218), (-15, 0, 218), (-15, 225, 218), (-125, 225, 218)], (0.12, 0.36, 0.88), stroke_w=5.0)
        # Hinged light-blue 3D door panel
        dx_end = -15 + math.cos(door_open_angle) * (-95)
        dz_end = 218 - math.sin(door_open_angle) * 95
        draw_poly_3d(ctx, cam, [(-15, 0, 218), (dx_end, 0, dz_end), (dx_end, 225, dz_end), (-15, 225, 218)], (0.58, 0.76, 0.94), stroke_w=4.5)

    # 6. 3D Swivel Office Chair at (45, 0, 95)
    draw_box_3d(ctx, cam, (45, 58, 105), (56, 10, 52), rot_y=0.15, top_rgb=(0.24, 0.28, 0.36), front_rgb=(0.18, 0.20, 0.26), side_rgb=(0.14, 0.16, 0.22))
    draw_box_3d(ctx, cam, (45, 102, 128), (52, 72, 10), rot_y=0.15, top_rgb=(0.24, 0.28, 0.36), front_rgb=(0.22, 0.25, 0.32), side_rgb=(0.14, 0.16, 0.22))

    # 7. 3D Gray Metal Desk at (15, 0..82, 5)
    # Left & right legs + drawer pedestal
    draw_box_3d(ctx, cam, (-48, 38, 5), (32, 76, 68), rot_y=-0.12, top_rgb=(0.68, 0.72, 0.78), front_rgb=(0.58, 0.62, 0.68), side_rgb=(0.46, 0.50, 0.56))
    draw_box_3d(ctx, cam, (75, 38, 5), (8, 76, 68), rot_y=-0.12, top_rgb=(0.68, 0.72, 0.78), front_rgb=(0.58, 0.62, 0.68), side_rgb=(0.46, 0.50, 0.56))
    # Desktop slab
    draw_box_3d(ctx, cam, (14, 78, 5), (165, 8, 82), rot_y=-0.12, top_rgb=(0.76, 0.80, 0.86), front_rgb=(0.62, 0.66, 0.72), side_rgb=(0.50, 0.54, 0.60))

    if show_desk_tape:
        # Yellow tape outline rectangle on top of 3D desk
        draw_poly_3d(ctx, cam, [(-35, 83, -18), (45, 83, -18), (45, 83, 22), (-35, 83, 22)], None, stroke_rgb=(0.96, 0.82, 0.16), stroke_w=5.0)

    if show_coffee_rings:
        for cr_x, cr_z in [(5, 5), (32, 12)]:
            cp = cam.project((cr_x, 83, cr_z))
            ctx.set_source_rgba(0.46, 0.26, 0.10, 0.82)
            ctx.set_line_width(4.5)
            ctx.arc(cp[0], cp[1], 11 * cp[3], 0, 2 * math.pi)
            ctx.stroke()


# ==============================================================================
# MASTER 13-SHOT 3D SCENE SEQUENCER (64.60s, ZERO CAPTIONS)
# ==============================================================================

def render_frame(ctx, t):
    # Always clear the full 1080x1920 canvas first so no pixels bleed across shots
    ctx.set_source_rgb(0.92, 0.95, 0.98)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    # Subtle handheld 3D camera sway
    sway_x = math.sin(t * 2.4) * 4.5
    sway_y = math.cos(t * 2.1) * 3.5

    # --------------------------------------------------------------------------
    # SHOT 01 & 02 (0.00 - 2.45s): 3D 'FIRE EMPLOYEE' Button & Ejector Seat
    # --------------------------------------------------------------------------
    if t < 2.45:
        if 1.10 <= t < 1.85:
            # Shot 02a: High-angle 3D view of employee in rocket ejector office chair
            ctx.set_source_rgb(0.14, 0.36, 0.84)
            ctx.rectangle(0, 0, W, H)
            ctx.fill()
            cam = Camera3D(pos=(0 + sway_x, 260, -290), target=(0, 95, 60), fov=1050)
            draw_poly_3d(ctx, cam, [(-420, 0, -280), (420, 0, -280), (420, 0, 280), (-420, 0, 280)], (0.16, 0.38, 0.86))
            draw_poly_3d(ctx, cam, [(-420, 0, 220), (420, 0, 220), (420, 480, 220), (-420, 480, 220)], (0.20, 0.44, 0.92))
            # Shoji window with Tokyo Tower
            draw_poly_3d(ctx, cam, [(-95, 45, 218), (95, 45, 218), (95, 245, 218), (-95, 245, 218)], (0.98, 0.88, 0.72), stroke_w=5.0)
            jolt = abs(math.sin(t * 22)) * 18
            draw_box_3d(ctx, cam, (0, 145 + jolt, 80), (78, 95, 65), top_rgb=(0.18, 0.20, 0.26), front_rgb=(0.14, 0.16, 0.22))
            draw_rigged_character_3d(ctx, cam, pos3d=(0, 85 + jolt, 65), scale=0.95, role="ken", expr="worried", t=t)
        else:
            # Shot 01 & 02b: 3D Macro view of 'FIRE EMPLOYEE' hazard button on Boss's desk
            ctx.set_source_rgb(0.32, 0.18, 0.10)
            ctx.rectangle(0, 0, W, H)
            ctx.fill()
            cam = Camera3D(pos=(0 + sway_x, 155, -210), target=(0, 75, 10), fov=1150)
            # Mahogany desk & green blotter
            draw_poly_3d(ctx, cam, [(-320, 50, -180), (320, 50, -180), (320, 50, 220), (-320, 50, 220)], (0.38, 0.20, 0.12))
            draw_poly_3d(ctx, cam, [(-140, 52, -90), (140, 52, -90), (140, 52, 90), (-140, 52, 90)], (0.10, 0.36, 0.28))
            # 3D Beveled Hazard Box ('FIRE EMPLOYEE')
            draw_box_3d(ctx, cam, (0, 72, 0), (135, 38, 110), rot_y=0.05, top_rgb=(0.95, 0.78, 0.16), front_rgb=(0.92, 0.72, 0.14), side_rgb=(0.68, 0.52, 0.08), stroke_w=5.0)
            fp = cam.project((0, 68, -56))
            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(22 * fp[3])
            ctx.set_source_rgb(0.82, 0.16, 0.14)
            ctx.move_to(fp[0] - 28 * fp[3], fp[1] + 6 * fp[3])
            ctx.show_text("FIRE")

            # Glowing 3D red dome button + Boss's rigged hand pressing down!
            press = max(0.0, math.sin(t * 14.0)) * 12.0
            bp = cam.project((0, 96 - press, 0))
            draw_3d_sphere_shaded(ctx, bp[0], bp[1], 32 * bp[3], (1.0, 0.65, 0.65), (0.92, 0.16, 0.16), (0.48, 0.05, 0.05), stroke_w=4.5)
            # Boss's 3D rigged arm & hand slamming button from upper-right
            draw_curved_limb_3d(ctx, cam, (140, 185, -20), (75, 145 - press * 0.6, -10), (18, 118 - press, -5), thickness=14.0)
            hp = cam.project((12, 115 - press, -5))
            draw_3d_sphere_shaded(ctx, hp[0], hp[1], 18 * hp[3], (0.22, 0.22, 0.28), (0.12, 0.12, 0.16), (0.06, 0.06, 0.08), stroke_w=4.0)

    # --------------------------------------------------------------------------
    # SHOT 03 (2.45 - 4.60s): Boss in 3D Executive Office Dangling 'STORAGE' Key
    # --------------------------------------------------------------------------
    elif t < 4.60:
        p = clamp((t - 2.45) / 2.15)
        cam = Camera3D(pos=(0 + sway_x, 165, lerp(-285, -225, ease_in_out(p))), target=(0, 135, 40), fov=1100)
        # 3D Wood-paneled executive walls
        draw_poly_3d(ctx, cam, [(-340, 0, 180), (340, 0, 180), (340, 380, 180), (-340, 380, 180)], (0.46, 0.26, 0.12), stroke_w=5.0)
        # Framed gold calligraphy scroll '誠' on back wall
        draw_box_3d(ctx, cam, (-18, 245, 175), (68, 95, 6), top_rgb=(0.96, 0.88, 0.64), front_rgb=(0.96, 0.88, 0.64), side_rgb=(0.32, 0.20, 0.10))
        sp = cam.project((-18, 245, 171))
        ctx.select_font_face("SimSun", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(46 * sp[3])
        ctx.set_source_rgb(0.12, 0.10, 0.08)
        ctx.move_to(sp[0] - 22 * sp[3], sp[1] + 16 * sp[3])
        ctx.show_text("誠")

        # Red leather executive chair + Rigged Boss holding 'STORAGE' key + Mahogany desk in foreground
        draw_box_3d(ctx, cam, (-8, 125, 75), (88, 115, 22), top_rgb=(0.68, 0.16, 0.16), front_rgb=(0.56, 0.12, 0.12), side_rgb=(0.38, 0.08, 0.08))
        draw_rigged_character_3d(
            ctx,
            cam,
            pos3d=(-8, 0, 45),
            yaw=0.08,
            scale=1.05,
            role="boss",
            expr="boss_grin",
            head_rot=(math.sin(t * 3) * 0.08, 0.05, 0.04),
            pose="dangling_key",
            t=t,
            prop="storage_key",
        )
        draw_box_3d(ctx, cam, (0, 42, -45), (260, 45, 110), top_rgb=(0.48, 0.28, 0.14), front_rgb=(0.36, 0.20, 0.10), side_rgb=(0.28, 0.14, 0.06))

    # --------------------------------------------------------------------------
    # SHOT 04 (4.60 - 8.15s): Walking Through 3D Office to 'CAREER DEVELOPMENT ROOM'
    # --------------------------------------------------------------------------
    elif t < 8.15:
        if t < 6.95:
            p = clamp((t - 4.60) / 2.35)
            cam = Camera3D(pos=(lerp(-40, 20, p) + sway_x, 145, -310), target=(0, 115, 50), fov=1050)
            # Open-plan office floor & walls
            draw_poly_3d(ctx, cam, [(-420, 0, -280), (420, 0, -280), (420, 0, 280), (-420, 0, 280)], (0.12, 0.36, 0.88))
            draw_poly_3d(ctx, cam, [(-420, 0, 220), (420, 0, 220), (420, 360, 220), (-420, 360, 220)], (0.95, 0.96, 0.99))
            # 3D Cubicles
            draw_box_3d(ctx, cam, (-110, 52, 60), (95, 104, 85), top_rgb=(0.82, 0.86, 0.92), front_rgb=(0.74, 0.78, 0.86), side_rgb=(0.62, 0.66, 0.74))
            # Boss & Ken walking with full 3D walk-cycle rigging
            wx = lerp(65, -35, p)
            draw_rigged_character_3d(
                ctx,
                cam,
                pos3d=(wx - 32, 0, 20),
                yaw=-0.35,
                scale=0.92,
                role="boss",
                expr="boss_grin",
                head_rot=(0.25, 0.0, 0.0),
                pose="walk",
                t=t,
                prop="storage_key",
            )
            draw_rigged_character_3d(
                ctx,
                cam,
                pos3d=(wx + 32, 0, 5),
                yaw=-0.35,
                scale=0.92,
                role="ken",
                expr="worried",
                head_rot=(-0.25, -0.08, -0.05),
                pose="walk",
                t=t + 0.35,
            )
        else:
            # Close-up 3D view as the 'CAREER DEVELOPMENT ROOM' door swings open
            p = clamp((t - 6.95) / 1.20)
            cam = Camera3D(pos=(20, 145, -240), target=(-20, 125, 80), fov=1100)
            draw_poly_3d(ctx, cam, [(-320, 0, 120), (320, 0, 120), (320, 340, 120), (-320, 340, 120)], (0.92, 0.95, 0.98))
            # Green room visible inside doorway
            draw_poly_3d(ctx, cam, [(-95, 0, 118), (45, 0, 118), (45, 250, 118), (-95, 250, 118)], (0.56, 0.80, 0.44), stroke_w=5.0)
            # Swinging 3D blue door panel with crooked taped sign
            ang = lerp(0.15, 0.85, ease_in_out(p))
            dx_d = -95 + math.cos(ang) * 135
            dz_d = 118 - math.sin(ang) * 135
            draw_poly_3d(ctx, cam, [(-95, 0, 118), (dx_d, 0, dz_d), (dx_d, 250, dz_d), (-95, 250, 118)], (0.58, 0.76, 0.94), stroke_w=5.0)
            # Taped sign on door
            sp = cam.project(((-95 + dx_d) * 0.5, 115, (118 + dz_d) * 0.5 - 2))
            ctx.save()
            ctx.translate(sp[0], sp[1])
            ctx.rotate(-0.08)
            ctx.set_source_rgb(0.99, 0.99, 0.97)
            ctx.rectangle(-75 * sp[3], -32 * sp[3], 150 * sp[3], 64 * sp[3])
            ctx.fill_preserve()
            ctx.set_source_rgb(0.12, 0.14, 0.20)
            ctx.set_line_width(3.5)
            ctx.stroke()
            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(11 * sp[3])
            ctx.move_to(-62 * sp[3], -8 * sp[3])
            ctx.show_text("CAREER DEVELOPMENT")
            ctx.set_font_size(17 * sp[3])
            ctx.set_source_rgb(0.86, 0.16, 0.16)
            ctx.move_to(-28 * sp[3], 18 * sp[3])
            ctx.show_text("ROOM")
            ctx.restore()

    # --------------------------------------------------------------------------
    # SHOT 05 (8.15 - 9.65s): 3D High-Angle Empty Desk with Yellow Tape Outlines
    # --------------------------------------------------------------------------
    elif t < 9.65:
        p = clamp((t - 8.15) / 1.50)
        cam = Camera3D(pos=(-95 + p * 18, 225, -185), target=(15, 65, 25), fov=1080)
        draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=False, show_desk_tape=True)

    # --------------------------------------------------------------------------
    # SHOT 06 (9.65 - 14.80s): Ticking Clock & Taro With Feet Propped on 3D Desk
    # --------------------------------------------------------------------------
    elif t < 14.80:
        if t < 10.75:
            # Close-up on 3D ticking wall clock
            cam = Camera3D(pos=(45, 245, 65), target=(45, 245, 216), fov=1150)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=True)
        else:
            p = clamp((t - 10.75) / 4.05)
            cam = Camera3D(pos=(lerp(35, -15, p) + sway_x, lerp(185, 165, p), lerp(-95, -245, p)), target=(25, 115, 60), fov=1080)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=True)
            # Taro reclining in swivel chair with rigged legs & brown shoes propped on 3D desk!
            draw_rigged_character_3d(
                ctx,
                cam,
                pos3d=(42, -12, 95),
                yaw=-0.18,
                scale=0.96,
                role="taro",
                expr="closed_smile",
                head_rot=(0.15 if t > 12.8 else 0.0, 0.12, 0.0),
                pose="recline_feet_up",
                t=t,
                prop="phone",
            )
            if t > 12.20:
                kp = clamp((t - 12.20) / 1.40)
                draw_rigged_character_3d(
                    ctx,
                    cam,
                    pos3d=(lerp(165, 115, kp), 0, 25),
                    yaw=-0.45,
                    scale=0.98,
                    role="ken",
                    expr="neutral",
                    head_rot=(-0.35, 0.05, 0.0),
                    pose="walk" if kp < 0.9 else "stand",
                    t=t,
                )

    # --------------------------------------------------------------------------
    # SHOT 07 (14.80 - 19.10s): Boss Opens Empty 3D Gift Box ('Your New Job Is Nothing')
    # --------------------------------------------------------------------------
    elif t < 19.10:
        if t < 17.55:
            p = clamp((t - 14.80) / 2.75)
            cam = Camera3D(pos=(-65 + sway_x, 145, lerp(-45, -15, p)), target=(-70, 125, 218), fov=1100)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=False, door_open_angle=0.85)
            draw_rigged_character_3d(
                ctx,
                cam,
                pos3d=(-70, 0, 185),
                yaw=0.0,
                scale=0.98,
                role="boss",
                expr="boss_grin",
                head_rot=(0.0, 0.05, 0.04 * math.sin(t * 5)),
                pose="gift_box_open",
                t=t,
                prop="gift_box",
            )
        else:
            # High-angle over-the-shoulder behind Ken looking at Boss in doorway
            cam = Camera3D(pos=(15 + sway_x, 215, -195), target=(-55, 115, 180), fov=1050)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=False, door_open_angle=0.75)
            draw_rigged_character_3d(ctx, cam, pos3d=(-70, 0, 195), yaw=0.0, scale=0.85, role="boss", expr="boss_grin", t=t)
            draw_rigged_character_3d(ctx, cam, pos3d=(18, 0, -85), yaw=math.pi, scale=1.05, role="ken", t=t)

    # --------------------------------------------------------------------------
    # SHOT 08 (19.10 - 23.55s): '+$4,850' Paycheck Alert & Sunbeam Paradise
    # --------------------------------------------------------------------------
    elif t < 23.55:
        if t < 20.40:
            cam = Camera3D(pos=(14, 215, -55), target=(14, 78, 5), fov=1100)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=False, show_desk_tape=True)
            # Phone glowing on desk
            draw_box_3d(ctx, cam, (14, 83, 5), (22, 3, 38), top_rgb=(0.32, 0.86, 0.62), front_rgb=(0.12, 0.14, 0.18))
        elif t < 21.80:
            cam = Camera3D(pos=(0 + sway_x, 155, -175), target=(0, 145, 20), fov=1150)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=True)
            draw_rigged_character_3d(ctx, cam, pos3d=(0, 0, 20), yaw=0.0, scale=1.12, role="ken", expr="grin", pose="recline_feet_up", t=t, prop="phone")
        else:
            # Overhead Dutch-angle top-down shot of Ken & Taro sunbathing in sunglasses
            cam = Camera3D(pos=(0, 285, -140), target=(0, 45, 40), fov=1050, roll=-0.38)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=True)
            draw_rigged_character_3d(ctx, cam, pos3d=(-35, 0, 35), yaw=0.0, scale=0.92, role="ken", expr="grin", sunglasses=True, t=t)
            draw_rigged_character_3d(ctx, cam, pos3d=(35, 0, 35), yaw=0.0, scale=0.92, role="taro", expr="grin", sunglasses=True, t=t)

    # --------------------------------------------------------------------------
    # SHOT 09 (23.55 - 29.95s): Coworkers Staring, Inbox (0), & Replaced at Desk
    # --------------------------------------------------------------------------
    elif t < 29.95:
        if t < 25.95:
            p = clamp((t - 23.55) / 2.40)
            cam = Camera3D(pos=(0 + sway_x, 155, lerp(-280, -180, p)), target=(0, 115, 120), fov=1050)
            draw_poly_3d(ctx, cam, [(-420, 0, -280), (420, 0, -280), (420, 0, 320), (-420, 0, 320)], (0.12, 0.36, 0.88))
            draw_poly_3d(ctx, cam, [(-420, 0, 280), (420, 0, 280), (420, 380, 280), (-420, 380, 280)], (0.94, 0.96, 0.99))
            # Rows of staring coworkers in 3D cubicles
            for cz, c_role in [(40, "coworker_purple"), (120, "coworker_yellow"), (200, "new_guy")]:
                draw_box_3d(ctx, cam, (85, 45, cz), (75, 75, 55), top_rgb=(0.82, 0.86, 0.92), front_rgb=(0.72, 0.76, 0.82))
                draw_rigged_character_3d(ctx, cam, pos3d=(-75, 0, cz), yaw=0.45, scale=0.88, role=c_role, expr="neutral", head_rot=(0.35, 0.0, 0.0), t=t)
                draw_rigged_character_3d(ctx, cam, pos3d=(75, 0, cz), yaw=-0.45, scale=0.88, role="ken", expr="neutral", head_rot=(-0.35, 0.0, 0.0), t=t)
        elif t < 27.10:
            # Close-up on smartphone 'Inbox (0) / No new mail' with cobwebbed mailbox
            ctx.set_source_rgb(0.14, 0.24, 0.48)
            ctx.rectangle(0, 0, W, H)
            ctx.fill()
            ctx.set_source_rgb(0.10, 0.12, 0.16)
            ctx.rectangle(160, 120, 760, 1680)
            ctx.fill()
            ctx.set_source_rgb(0.99, 0.99, 1.0)
            ctx.rectangle(185, 155, 710, 1610)
            ctx.fill()
            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(64)
            ctx.set_source_rgb(0.12, 0.14, 0.18)
            ctx.move_to(235, 320)
            ctx.show_text("Inbox (0)")
            # Blue mailbox icon with cobweb
            ctx.set_source_rgb(0.32, 0.58, 0.92)
            ctx.rectangle(420, 780, 240, 160)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.10, 0.12, 0.16)
            ctx.set_line_width(6)
            ctx.stroke()
            ctx.set_font_size(42)
            ctx.set_source_rgb(0.52, 0.54, 0.58)
            ctx.move_to(390, 1160)
            ctx.show_text("No new mail")
        else:
            # New Guy sitting at Ken's old 3D desk next to a framed family photo
            p = clamp((t - 27.10) / 2.85)
            cam = Camera3D(pos=(lerp(20, -25, p) + sway_x, 145, -245), target=(10, 110, 40), fov=1080)
            draw_poly_3d(ctx, cam, [(-420, 0, -280), (420, 0, -280), (420, 0, 280), (-420, 0, 280)], (0.12, 0.36, 0.88))
            draw_poly_3d(ctx, cam, [(-420, 0, 220), (420, 0, 220), (420, 360, 220), (-420, 360, 220)], (0.94, 0.96, 0.99))
            draw_box_3d(ctx, cam, (55, 42, 25), (125, 78, 75), top_rgb=(0.88, 0.90, 0.94), front_rgb=(0.76, 0.28, 0.22), side_rgb=(0.58, 0.20, 0.16))
            # Framed family photo on desk
            draw_box_3d(ctx, cam, (45, 95, 5), (38, 28, 6), rot_y=-0.25, top_rgb=(0.56, 0.34, 0.14), front_rgb=(0.36, 0.78, 0.94), side_rgb=(0.42, 0.24, 0.10))
            draw_rigged_character_3d(ctx, cam, pos3d=(-65, 0, 45), yaw=0.35, scale=0.92, role="ken", expr="worried", head_rot=(0.25, 0.0, 0.0), t=t)
            draw_rigged_character_3d(ctx, cam, pos3d=(15, 0, 35), yaw=-0.25, scale=0.92, role="new_guy", expr="grin", t=t)

    # --------------------------------------------------------------------------
    # SHOT 10 (29.95 - 35.45s): 'NOV FRI 25' Calendar & Boss Peeking In Doorway
    # --------------------------------------------------------------------------
    elif t < 35.45:
        if t < 31.20:
            cam = Camera3D(pos=(-165, 195, 85), target=(-165, 195, 216), fov=1150)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=False, cal_month="NOV", cal_day="25")
        else:
            p = clamp((t - 31.20) / 4.25)
            cam = Camera3D(pos=(-70 + sway_x, 145, lerp(15, 85, ease_in_out(p))), target=(-70, 135, 218), fov=1100)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=False, door_open_angle=0.85)
            # Boss leaning his torso & head sideways around the 3D doorframe!
            draw_rigged_character_3d(
                ctx,
                cam,
                pos3d=(-105, 0, 205),
                yaw=0.15,
                scale=0.98,
                role="boss",
                expr="boss_grin",
                head_rot=(0.12, 0.05, 0.22),
                spine_lean=(0.08, 0.42),
                pose="stand",
                t=t,
            )

    # --------------------------------------------------------------------------
    # SHOT 11 (35.45 - 45.65s): Three Years in Corner -> Skyscraper -> Both Feet Up
    # --------------------------------------------------------------------------
    elif t < 45.65:
        if t < 38.20:
            p = clamp((t - 35.45) / 2.75)
            cam = Camera3D(pos=(lerp(-35, 35, p) + sway_x, 165, -185), target=(25, 105, 65), fov=1080)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=True)
            draw_rigged_character_3d(ctx, cam, pos3d=(42, -12, 95), yaw=-0.22, scale=0.96, role="taro", expr="closed_smile", pose="recline_feet_up", t=t)
        elif t < 42.25:
            # Exterior 3D Glass Office Skyscraper at Twilight with 1 Warm Golden Window!
            p = clamp((t - 38.20) / 4.05)
            cam = Camera3D(pos=(lerp(-20, 20, p), 180, lerp(-260, -340, p)), target=(0, 180, 120), fov=1050)
            ctx.set_source_rgb(0.08, 0.12, 0.28)
            ctx.rectangle(0, 0, W, H)
            ctx.fill()
            for r_i in range(5):
                for c_i in range(3):
                    wx = -130 + c_i * 130
                    wy = 40 + r_i * 95
                    is_warm = (r_i == 2 and c_i == 1)
                    w_col = (1.0, 0.88, 0.36) if is_warm else (0.16, 0.42, 0.82)
                    draw_box_3d(ctx, cam, (wx, wy, 120), (115, 82, 12), top_rgb=w_col, front_rgb=w_col, side_rgb=(0.08, 0.14, 0.32), stroke_w=4.5)
                    draw_rigged_character_3d(
                        ctx,
                        cam,
                        pos3d=(wx, wy - 42, 112),
                        scale=0.36,
                        role="taro" if is_warm else "ken",
                        expr="closed_smile" if is_warm else "miserable",
                        pose="recline_feet_up" if is_warm else "stand",
                        t=t,
                    )
        else:
            # Both Ken & Taro reclining side-by-side with all 4 shoes propped on the 3D desk sipping drinks!
            p = clamp((t - 42.25) / 3.40)
            cam = Camera3D(pos=(25 + sway_x, 155, lerp(-215, -145, ease_in_out(p))), target=(25, 115, 65), fov=1100)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=True)
            draw_rigged_character_3d(ctx, cam, pos3d=(5, -12, 95), yaw=-0.12, scale=0.96, role="taro", expr="closed_smile", pose="recline_feet_up", t=t, prop="drink")
            draw_rigged_character_3d(ctx, cam, pos3d=(58, -12, 95), yaw=-0.15, scale=0.96, role="ken", expr="closed_smile", pose="recline_feet_up", t=t + 0.5, prop="drink")

    # --------------------------------------------------------------------------
    # SHOT 12 (45.65 - 52.20s): One Monday ('APR 28') He's Gone — Coffee Stain Rings
    # --------------------------------------------------------------------------
    elif t < 52.20:
        if t < 47.40:
            p = clamp((t - 45.65) / 1.75)
            cam = Camera3D(pos=(-25 + sway_x, 165, -235), target=(15, 95, 55), fov=1080)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=False, cal_month="APR", cal_day="28", door_open_angle=0.75, show_coffee_rings=True)
            # Ken bending over at the waist to inspect the empty desk!
            draw_rigged_character_3d(
                ctx,
                cam,
                pos3d=(-35, 0, 45),
                yaw=0.65,
                scale=0.96,
                role="ken",
                expr="worried",
                head_rot=(0.15, 0.35, 0.0),
                spine_lean=(0.68, 0.0),
                pose="bend_inspect",
                t=t,
            )
        else:
            p = clamp((t - 47.40) / 4.80)
            cam = Camera3D(pos=(lerp(-45, -10, p) + sway_x, lerp(195, 165, p), lerp(-145, -65, ease_in_out(p))), target=(14, 78, 15), fov=1100)
            draw_3d_green_room_and_furniture(ctx, cam, t, show_sunbeam=False, cal_month="APR", cal_day="28", show_coffee_rings=True)

    # --------------------------------------------------------------------------
    # SHOT 13 (52.20 - 64.60s): Padlocked Alarm, Breaker Box ('HOPE/WORK/FRIENDS'), & Alone Forever
    # --------------------------------------------------------------------------
    else:
        ctx.set_source_rgb(0.14, 0.24, 0.58)
        ctx.rectangle(0, 0, W, H)
        ctx.fill()
        if t < 56.00:
            # 3D Corridor Pan to Red 'FIRE' Pull-Box Locked by Brass 'LABOR LAW' Padlock
            p = clamp((t - 52.20) / 3.80)
            cam = Camera3D(pos=(lerp(-35, 25, p) + sway_x, 145, lerp(-180, -65, ease_in_out(p))), target=(lerp(-35, 25, p), 140, 180), fov=1100)
            draw_poly_3d(ctx, cam, [(-480, -120, 180), (480, -120, 180), (480, 520, 180), (-480, 520, 180)], (0.28, 0.44, 0.82), stroke_w=5.0)
            draw_box_3d(ctx, cam, (25, 145, 174), (62, 86, 12), top_rgb=(0.88, 0.16, 0.16), front_rgb=(0.86, 0.14, 0.14), side_rgb=(0.56, 0.08, 0.08))
            draw_box_3d(ctx, cam, (25, 114, 168), (34, 34, 10), top_rgb=(0.96, 0.80, 0.22), front_rgb=(0.92, 0.74, 0.18), side_rgb=(0.64, 0.48, 0.10))
            lp = cam.project((25, 114, 162))
            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(10 * lp[3])
            ctx.set_source_rgb(0.12, 0.10, 0.08)
            ctx.move_to(lp[0] - 14 * lp[3], lp[1])
            ctx.show_text("LABOR")
            ctx.move_to(lp[0] - 10 * lp[3], lp[1] + 11 * lp[3])
            ctx.show_text("LAW")
        elif t < 61.55:
            # Boss in moody blue 3D corridor flipping off breaker switches ('HOPE', 'WORK', 'FRIENDS')
            p = clamp((t - 56.00) / 5.55)
            cam = Camera3D(pos=(lerp(15, -25, p) + sway_x, 145, -210), target=(0, 130, 140), fov=1080)
            draw_poly_3d(ctx, cam, [(-480, 0, -280), (480, 0, -280), (480, 0, 280), (-480, 0, 280)], (0.08, 0.18, 0.56))
            draw_poly_3d(ctx, cam, [(-480, 0, 180), (480, 0, 180), (480, 520, 180), (-480, 520, 180)], (0.22, 0.36, 0.74), stroke_w=5.0)
            # Warm wall sconce glow cone
            sp_g = cam.project((10, 245, 175))
            rad = cairo.RadialGradient(sp_g[0], sp_g[1], 10, sp_g[0], sp_g[1] + 120, 340)
            rad.add_color_stop_rgba(0.0, 1.0, 0.88, 0.45, 0.75)
            rad.add_color_stop_rgba(1.0, 1.0, 0.88, 0.45, 0.0)
            ctx.set_source(rad)
            ctx.arc(sp_g[0], sp_g[1] + 120, 340, 0, 2 * math.pi)
            ctx.fill()
            # 3D Open Breaker Box on wall with 6 labeled switches
            draw_box_3d(ctx, cam, (55, 145, 172), (88, 82, 12), top_rgb=(0.24, 0.26, 0.30), front_rgb=(0.18, 0.20, 0.24), side_rgb=(0.12, 0.14, 0.18))
            labels = ["HOPE", "A/C", "LUNCH", "WI-FI", "WORK", "FRIENDS"]
            for idx, lbl in enumerate(labels):
                lx = 36 + (idx % 2) * 38
                ly = 168 - (idx // 2) * 22
                lp0 = cam.project((lx, ly, 165))
                ctx.set_source_rgb(0.95, 0.80, 0.22)
                ctx.rectangle(lp0[0] - 14 * lp0[3], lp0[1] - 5 * lp0[3], 28 * lp0[3], 10 * lp0[3])
                ctx.fill()
                ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
                ctx.set_font_size(5.2 * lp0[3])
                ctx.set_source_rgb(0.10, 0.10, 0.12)
                ctx.move_to(lp0[0] - 11 * lp0[3], lp0[1] + 2 * lp0[3])
                ctx.show_text(lbl)
            draw_rigged_character_3d(
                ctx,
                cam,
                pos3d=(-35, 0, 115),
                yaw=0.12,
                scale=1.02,
                role="boss",
                expr="boss_grin",
                pose="flip_breaker",
                t=t,
            )
        else:
            # Final 3D push-in through 'CAREER DEVELOPMENT ROOM' door window on Ken trapped alone inside
            p = clamp((t - 61.55) / 3.05)
            cam = Camera3D(pos=(0 + sway_x * 0.4, 145, lerp(-165, -45, ease_in_out(p))), target=(0, 142, 180), fov=1120)
            draw_poly_3d(ctx, cam, [(-480, -120, 180), (480, -120, 180), (480, 520, 180), (-480, 520, 180)], (0.18, 0.30, 0.66))
            # 3D Door frame
            draw_box_3d(ctx, cam, (0, 130, 176), (145, 280, 8), top_rgb=(0.34, 0.52, 0.84), front_rgb=(0.28, 0.46, 0.78), side_rgb=(0.18, 0.30, 0.56), stroke_w=5.5)
            # Window opening showing Ken sitting alone inside the dim green room
            draw_box_3d(ctx, cam, (0, 168, 174), (68, 82, 6), top_rgb=(0.38, 0.56, 0.34), front_rgb=(0.38, 0.56, 0.34), side_rgb=(0.22, 0.34, 0.20), stroke_w=4.5)
            draw_rigged_character_3d(ctx, cam, pos3d=(0, 78, 168), yaw=0.0, scale=0.45, role="ken", expr="miserable", t=t)
            # Crooked taped door sign below window
            sp = cam.project((0, 98, 170))
            ctx.save()
            ctx.translate(sp[0], sp[1])
            ctx.rotate(0.08)
            ctx.set_source_rgb(0.96, 0.96, 0.98)
            ctx.rectangle(-62 * sp[3], -26 * sp[3], 124 * sp[3], 52 * sp[3])
            ctx.fill_preserve()
            ctx.set_source_rgb(0.10, 0.12, 0.18)
            ctx.set_line_width(3.5)
            ctx.stroke()
            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(9.0 * sp[3])
            ctx.move_to(-52 * sp[3], -6 * sp[3])
            ctx.show_text("CAREER DEVELOPMENT")
            ctx.set_font_size(15 * sp[3])
            ctx.set_source_rgb(0.86, 0.16, 0.16)
            ctx.move_to(-24 * sp[3], 15 * sp[3])
            ctx.show_text("ROOM")
            ctx.restore()


def generate_preview_sheets():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    tw, th = 270, 480
    cols, rows = 6, 4

    for sheet_idx in range(3):
        grid = np.zeros((rows * th, cols * tw, 3), dtype=np.uint8)
        for i in range(24):
            sec = sheet_idx * 24 + i
            if sec >= int(math.ceil(DURATION)):
                break
            t = min(DURATION - 0.05, sec + 0.35)
            render_frame(ctx, t)
            buf = np.frombuffer(surf.get_data(), dtype=np.uint8).reshape((H, W, 4))
            rgb = buf[::4, ::4, :3][:, :, ::-1]
            r = i // cols
            c = i % cols
            grid[r * th : (r + 1) * th, c * tw : (c + 1) * tw] = rgb

        out_jpg = os.path.join(SCRATCH_DIR, f"japan_rigged_3d_sheet_{sheet_idx+1:02d}.jpg")
        cmd = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{cols*tw}x{rows*th}",
            "-i",
            "-",
            "-q:v",
            "3",
            out_jpg,
        ]
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        p.communicate(input=grid.tobytes())
    print("Generated japan_rigged_3d_sheet_01..03.jpg!")


def render_procedural_video():
    generate_preview_sheets()
    audio_wav = os.path.join(OUT_DIR, "Full_Mixed_Audio.wav")
    out_mp4 = os.path.join(OUT_DIR, "Pure_3D_Procedural_From_Scratch_No_Captions.mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr0",
        "-s",
        f"{W}x{H}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-i",
        audio_wav,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        out_mp4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)

    for f in range(TOTAL_FRAMES):
        render_frame(ctx, f / FPS)
        proc.stdin.write(surf.get_data())
        if (f + 1) % 400 == 0:
            print(f"Rendered {f + 1} / {TOTAL_FRAMES} rigged 3D frames...", flush=True)

    proc.stdin.close()
    proc.wait()
    print(f"Finished rendering {out_mp4} ({TOTAL_FRAMES} frames)!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        generate_preview_sheets()
    else:
        render_procedural_video()
