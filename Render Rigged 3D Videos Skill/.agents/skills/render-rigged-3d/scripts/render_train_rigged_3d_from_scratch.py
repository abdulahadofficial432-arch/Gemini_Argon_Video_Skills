import os
import sys
import math
import shutil
import subprocess
import numpy as np
import cairo

SCRATCH_DIR = r"C:\Users\WayWe Work-Station\.gemini\antigravity\brain\8ad88795-d9fa-438b-8430-13b89b7ef998\scratch\train_project"
OUT_DIR = r"C:\Users\WayWe Work-Station\Downloads\Mate\Train Video"

W, H = 1080, 1920
FPS = 30
DURATION = 76.6694
TOTAL_FRAMES = int(round(DURATION * FPS))  # 2300 frames


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def lerp(a, b, t):
    return a + (b - a) * clamp(t)


def ease_in_out(t):
    t = clamp(t)
    return t * t * (3.0 - 2.0 * t)


# ==============================================================================
# GLITCH-FREE 3D CAMERA WITH SUTHERLAND-HODGMAN NEAR-PLANE 3D CLIPPING
# ==============================================================================

NEAR_Z = 45.0


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

    def world_to_cam(self, pt3d):
        v = np.asarray(pt3d, dtype=np.float64) - self.pos
        x_cam = float(np.dot(v, self.right))
        y_cam = float(np.dot(v, self.up))
        z_cam = float(np.dot(v, self.fwd))
        return x_cam, y_cam, z_cam

    def project(self, pt3d):
        x_cam, y_cam, z_cam = self.world_to_cam(pt3d)
        depth = max(NEAR_Z, z_cam)
        scale = self.fov / depth
        sx = W * 0.5 + x_cam * scale
        sy = H * 0.5 - y_cam * scale
        return sx, sy, depth, scale


def clip_and_project_poly(cam, pts3d):
    """
    Clips a 3D polygon against the camera near plane z_cam >= NEAR_Z
    using Sutherland-Hodgman clipping so polygons NEVER warp or glitch!
    """
    cam_pts = [cam.world_to_cam(p) for p in pts3d]
    clipped = []
    n = len(cam_pts)
    for i in range(n):
        p1 = cam_pts[i]
        p2 = cam_pts[(i + 1) % n]
        in1 = p1[2] >= NEAR_Z
        in2 = p2[2] >= NEAR_Z
        if in1 and in2:
            clipped.append(p2)
        elif in1 and not in2:
            t = (NEAR_Z - p1[2]) / (p2[2] - p1[2] - 1e-9)
            clipped.append((p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]), NEAR_Z))
        elif not in1 and in2:
            t = (NEAR_Z - p1[2]) / (p2[2] - p1[2] + 1e-9)
            clipped.append((p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]), NEAR_Z))
            clipped.append(p2)

    if len(clipped) < 3:
        return []

    proj = []
    for xc, yc, zc in clipped:
        sc = cam.fov / zc
        proj.append((W * 0.5 + xc * sc, H * 0.5 - yc * sc, zc, sc))
    return proj


def draw_poly_3d(ctx, cam, pts3d, fill_rgb, stroke_rgb=(0.10, 0.08, 0.08), stroke_w=3.6, alpha=1.0):
    proj_pts = clip_and_project_poly(cam, pts3d)
    if len(proj_pts) < 3:
        return
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


def draw_box_3d(
    ctx,
    cam,
    center,
    size,
    rot_y=0.0,
    top_rgb=(0.82, 0.82, 0.82),
    front_rgb=(0.70, 0.70, 0.70),
    side_rgb=(0.55, 0.55, 0.55),
    stroke_w=3.4,
):
    """
    Renders a 3D box using deterministic outward-normal back-face culling
    so faces NEVER pop or flicker between frames!
    """
    cx, cy, cz = center
    wx, wy, wz = size[0] * 0.5, size[1] * 0.5, size[2] * 0.5
    c, s = math.cos(rot_y), math.sin(rot_y)

    def tf(lx, ly, lz):
        rx = lx * c + lz * s
        rz = -lx * s + lz * c
        return np.array([cx + rx, cy + ly, cz + rz], dtype=np.float64)

    def tf_norm(nx, ny, nz):
        rnx = nx * c + nz * s
        rnz = -nx * s + nz * c
        return np.array([rnx, ny, rnz], dtype=np.float64)

    v = [
        tf(-wx, -wy, -wz),  # 0: front-bot-left
        tf(wx, -wy, -wz),   # 1: front-bot-right
        tf(wx, wy, -wz),    # 2: front-top-right
        tf(-wx, wy, -wz),   # 3: front-top-left
        tf(-wx, -wy, wz),   # 4: back-bot-left
        tf(wx, -wy, wz),    # 5: back-bot-right
        tf(wx, wy, wz),     # 6: back-top-right
        tf(-wx, wy, wz),    # 7: back-top-left
    ]

    faces = [
        ([v[0], v[1], v[2], v[3]], tf_norm(0, 0, -1), front_rgb),  # Front (-Z)
        ([v[5], v[4], v[7], v[6]], tf_norm(0, 0, 1), front_rgb),   # Back (+Z)
        ([v[4], v[0], v[3], v[7]], tf_norm(-1, 0, 0), side_rgb),   # Left (-X)
        ([v[1], v[5], v[6], v[2]], tf_norm(1, 0, 0), side_rgb),    # Right (+X)
        ([v[3], v[2], v[6], v[7]], tf_norm(0, 1, 0), top_rgb),     # Top (+Y)
        ([v[4], v[5], v[1], v[0]], tf_norm(0, -1, 0), side_rgb),   # Bottom (-Y)
    ]

    visible_faces = []
    for f_pts, f_norm, f_col in faces:
        f_center = (f_pts[0] + f_pts[2]) * 0.5
        to_cam = cam.pos - f_center
        if float(np.dot(f_norm, to_cam)) > 0.0:
            dist = float(np.linalg.norm(to_cam))
            visible_faces.append((dist, f_pts, f_col))

    visible_faces.sort(key=lambda x: x[0], reverse=True)
    for _, f_pts, f_col in visible_faces:
        draw_poly_3d(ctx, cam, f_pts, f_col, stroke_w=stroke_w)


def draw_3d_sphere_shaded(
    ctx,
    sx,
    sy,
    r,
    light_rgb,
    mid_rgb,
    dark_rgb,
    stroke_w=4.5,
    alpha=1.0,
    light_dir=(-0.32, -0.32),
):
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
        ctx.set_source_rgba(0.10, 0.08, 0.08, alpha)
        ctx.set_line_width(stroke_w)
        ctx.stroke()
    else:
        ctx.fill()


# ==============================================================================
# 18-JOINT 3D SKELETAL RIGGED CHARACTER ENGINE (WITH CLEAN PROP LAYERING)
# ==============================================================================

def draw_curved_limb_3d(ctx, cam, p_start, p_joint, p_end, thickness=9.5, col=(0.12, 0.09, 0.08)):
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
    role="engineer",
    expr="neutral",
    head_rot=(0.0, 0.0, 0.0),
    spine_lean=(0.0, 0.0),
    pose="stand",
    t=0.0,
    purple_anger=0.0,
    sweat=False,
    prop=None,
):
    bx, by, bz = pos3d
    cy, sy = math.cos(yaw), math.sin(yaw)
    sp_pitch, sp_side = spine_lean

    breath = math.sin(t * 3.2 + bx * 0.02) * 2.0
    walk_bounce = 0.0
    if pose == "walk":
        w_ph = t * 8.5
        walk_bounce = abs(math.sin(w_ph)) * 7.5
        sp_pitch += 0.08
    elif pose == "sawing_rail":
        sp_pitch = 0.46
        sp_side = -0.14
    elif pose == "inspect_gap":
        sp_pitch = 0.42
        sp_side = -0.38
    elif pose == "recline_chair":
        sp_pitch = -0.32

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

    # 1. Floor contact shadow
    if pose not in ("sit_beam", "coach_window"):
        sh_pts = []
        for a in range(12):
            ang = a * (2 * math.pi / 12)
            sh_pts.append((bx + math.cos(ang) * 40 * scale, by + 1.0, bz + math.sin(ang) * 30 * scale))
        draw_poly_3d(ctx, cam, sh_pts, (0.08, 0.05, 0.04), stroke_rgb=None, alpha=0.28)

    # 2. 3D Leg Joints (Hip -> Knee -> Ankle -> Foot)
    if pose == "sawing_rail":
        l_hip = local_to_world(-16, 62, 0, False)
        r_hip = local_to_world(16, 62, 0, False)
        l_knee = local_to_world(-26, 36, -22, False)
        r_knee = local_to_world(24, 32, 20, False)
        l_ank = local_to_world(-20, 4, -16, False)
        r_ank = local_to_world(28, 4, 30, False)
        l_toe = local_to_world(-22, 2, -38, False)
        r_toe = local_to_world(30, 2, 10, False)
    elif pose == "sit_beam":
        l_hip = local_to_world(-16, 68, 0, False)
        r_hip = local_to_world(16, 68, 0, False)
        l_knee = local_to_world(-18, 52, -32, False)
        r_knee = local_to_world(18, 52, -32, False)
        sw_leg = math.sin(t * 3.5 + bx * 0.05) * 10
        l_ank = local_to_world(-18, 8, -28 + sw_leg, False)
        r_ank = local_to_world(18, 8, -28 - sw_leg, False)
        l_toe = local_to_world(-20, 4, -46 + sw_leg, False)
        r_toe = local_to_world(20, 4, -46 - sw_leg, False)
    elif pose == "recline_chair":
        l_hip = local_to_world(-16, 68, -8, False)
        r_hip = local_to_world(16, 68, -8, False)
        l_knee = local_to_world(-16, 48, -42, False)
        r_knee = local_to_world(16, 48, -42, False)
        l_ank = local_to_world(-14, 12, -52, False)
        r_ank = local_to_world(14, 12, -52, False)
        l_toe = local_to_world(-16, 8, -72, False)
        r_toe = local_to_world(16, 8, -72, False)
    elif pose == "walk":
        w_ph = t * 8.5
        s_l = math.sin(w_ph)
        s_r = math.sin(w_ph + math.pi)
        l_hip = local_to_world(-16, 72, 0, False)
        r_hip = local_to_world(16, 72, 0, False)
        l_knee = local_to_world(-16, 38 + max(0, s_l) * 14, -s_l * 22, False)
        r_knee = local_to_world(16, 38 + max(0, s_r) * 14, -s_r * 22, False)
        l_ank = local_to_world(-16, 6 + max(0, -s_l) * 12, -s_l * 34, False)
        r_ank = local_to_world(16, 6 + max(0, -s_r) * 12, -s_r * 34, False)
        l_toe = local_to_world(-18, 2, -s_l * 34 - 22, False)
        r_toe = local_to_world(18, 2, -s_r * 34 - 22, False)
    else:
        l_hip = local_to_world(-16, 72, 0, False)
        r_hip = local_to_world(16, 72, 0, False)
        l_knee = local_to_world(-18, 38, -4, False)
        r_knee = local_to_world(18, 38, -4, False)
        l_ank = local_to_world(-18, 4, 0, False)
        r_ank = local_to_world(18, 4, 0, False)
        l_toe = local_to_world(-22, 2, -22, False)
        r_toe = local_to_world(22, 2, -22, False)

    if pose != "coach_window":
        for hip_p, knee_p, ank_p, toe_p in [(l_hip, l_knee, l_ank, l_toe), (r_hip, r_knee, r_ank, r_toe)]:
            draw_curved_limb_3d(ctx, cam, hip_p, knee_p, ank_p, thickness=8.8 * scale)
            sa = cam.project(ank_p)
            st = cam.project(toe_p)
            ctx.save()
            ctx.set_source_rgb(0.18, 0.12, 0.08)
            ctx.set_line_width(max(4.0, 14.0 * sa[3] * scale))
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(sa[0], sa[1])
            ctx.line_to(st[0], st[1])
            ctx.stroke()
            ctx.restore()

    # 3. 3D Torso Mesh
    p_chest = local_to_world(0, 142 + breath, 0, True)
    s_che = cam.project(p_chest)

    if role == "engineer":
        c_top, c_bot = (0.14, 0.76, 0.56), (0.06, 0.46, 0.32)
    elif role == "boss":
        c_top, c_bot = (0.88, 0.70, 0.18), (0.58, 0.44, 0.08)
    elif role == "tycoon":
        c_top, c_bot = (0.20, 0.20, 0.26), (0.08, 0.08, 0.12)
    elif role == "foreman":
        c_top, c_bot = (0.16, 0.28, 0.56), (0.08, 0.16, 0.34)
    else:
        c_top, c_bot = (0.62, 0.48, 0.34), (0.40, 0.28, 0.18)

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
    ctx.set_source_rgb(0.10, 0.08, 0.08)
    ctx.set_line_width(max(2.5, 4.8 * s_che[3] * scale))
    ctx.stroke()

    if role == "engineer":
        b_l = cam.project(local_to_world(-16, 138 + breath, -16, True))
        b_r = cam.project(local_to_world(16, 138 + breath, -16, True))
        b_tip = cam.project(local_to_world(0, 108 + breath, -18, True))
        ctx.set_source_rgb(0.86, 0.16, 0.14)
        ctx.move_to(b_l[0], b_l[1])
        ctx.line_to(b_r[0], b_r[1])
        ctx.line_to(b_tip[0], b_tip[1])
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.set_line_width(max(1.5, 3.0 * s_che[3] * scale))
        ctx.stroke()
    elif role == "boss":
        c0 = cam.project(local_to_world(0, 96 + breath, -18, True))
        c1 = cam.project(local_to_world(22, 88 + breath, -16, True))
        ctx.set_source_rgb(0.98, 0.84, 0.24)
        ctx.set_line_width(max(2.0, 3.8 * s_che[3] * scale))
        ctx.move_to(c0[0], c0[1])
        ctx.curve_to(lerp(c0[0], c1[0], 0.5), c0[1] + 14 * s_che[3], c1[0], c1[1] + 8 * s_che[3], c1[0], c1[1])
        ctx.stroke()
    elif role == "tycoon":
        b_l = cam.project(local_to_world(-14, 138 + breath, -16, True))
        b_r = cam.project(local_to_world(14, 138 + breath, -16, True))
        b_tip = cam.project(local_to_world(0, 102 + breath, -18, True))
        ctx.set_source_rgb(0.98, 0.98, 1.0)
        ctx.move_to(b_l[0], b_l[1])
        ctx.line_to(b_r[0], b_r[1])
        ctx.line_to(b_tip[0], b_tip[1])
        ctx.close_path()
        ctx.fill()
        ctx.set_source_rgb(0.86, 0.14, 0.14)
        ctx.arc((b_l[0] + b_r[0]) * 0.5, b_l[1] + 6 * s_che[3], 6 * s_che[3] * scale, 0, 2 * math.pi)
        ctx.fill()

    # 4. 3D Spherical Head (drawn BEFORE front props like newspaper so newspaper is never overlapped!)
    p_head = local_to_world(0, 186 + breath, 0, True)
    sh_x, sh_y, _, sh_s = cam.project(p_head)
    hr = 46.0 * sh_s * scale
    hyaw, hpitch, hroll = head_rot
    total_hyaw = yaw + hyaw

    ctx.save()
    ctx.translate(sh_x, sh_y)
    ctx.rotate(hroll)

    if purple_anger > 0.2:
        for sx_st in (-1, 1):
            for k in range(3):
                p_dist = hr * (1.15 + k * 0.42 + ((t * 1.8) % 0.35))
                draw_3d_sphere_shaded(
                    ctx,
                    sx_st * p_dist,
                    -hr * (0.25 + k * 0.32),
                    hr * (0.26 + k * 0.08),
                    (1.0, 1.0, 1.0),
                    (0.92, 0.92, 0.96),
                    (0.74, 0.74, 0.82),
                    stroke_w=0,
                    alpha=clamp(purple_anger),
                )

    pa = clamp(purple_anger)
    hl = (lerp(1.00, 0.74, pa), lerp(1.00, 0.32, pa), lerp(1.00, 0.96, pa))
    hm = (lerp(0.94, 0.54, pa), lerp(0.93, 0.16, pa), lerp(0.92, 0.82, pa))
    hd = (lerp(0.74, 0.34, pa), lerp(0.73, 0.08, pa), lerp(0.76, 0.56, pa))
    draw_3d_sphere_shaded(ctx, 0, 0, hr, hl, hm, hd, stroke_w=max(3.0, 5.2 * sh_s * scale))

    if role == "engineer":
        ctx.set_source_rgb(0.38, 0.24, 0.12)
        ctx.arc(-hr * 0.84, -hr * 0.12, hr * 0.22, 0, 2 * math.pi)
        ctx.arc(hr * 0.84, -hr * 0.12, hr * 0.22, 0, 2 * math.pi)
        ctx.fill()
    elif role == "boss":
        ctx.set_source_rgb(0.56, 0.56, 0.60)
        ctx.arc(-hr * 0.85, -hr * 0.10, hr * 0.20, 0, 2 * math.pi)
        ctx.arc(hr * 0.85, -hr * 0.10, hr * 0.20, 0, 2 * math.pi)
        ctx.fill()
    elif role == "veteran":
        ctx.set_source_rgb(0.74, 0.72, 0.70)
        ctx.move_to(-hr * 0.7, hr * 0.18)
        ctx.curve_to(-hr * 0.8, hr * 1.25, hr * 0.8, hr * 1.25, hr * 0.7, hr * 0.18)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.set_line_width(max(2.0, 3.8 * sh_s * scale))
        ctx.stroke()

    if role == "engineer":
        ctx.save()
        ctx.translate(0, -hr * 0.76)
        ctx.set_source_rgb(0.96, 0.98, 1.0)
        ctx.save()
        ctx.scale(1.12, 0.48)
        ctx.arc(0, 0, hr * 0.92, 0, 2 * math.pi)
        ctx.restore()
        ctx.fill_preserve()
        ctx.clip_preserve()
        ctx.set_source_rgb(0.16, 0.36, 0.68)
        ctx.set_line_width(max(2.0, 5.5 * sh_s * scale))
        for st_x in range(-8, 9):
            ctx.move_to(st_x * hr * 0.14, -hr)
            ctx.line_to(st_x * hr * 0.14, hr)
            ctx.stroke()
        ctx.restore()
        ctx.save()
        ctx.translate(0, -hr * 0.76)
        ctx.scale(1.12, 0.48)
        ctx.arc(0, 0, hr * 0.92, 0, 2 * math.pi)
        ctx.restore()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.set_line_width(max(2.5, 4.5 * sh_s * scale))
        ctx.stroke()
        ctx.set_source_rgb(0.14, 0.22, 0.38)
        ctx.move_to(-hr * 0.88, -hr * 0.56)
        ctx.curve_to(-hr * 0.3, -hr * 0.38, hr * 0.3, -hr * 0.38, hr * 0.88, -hr * 0.56)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.stroke()
    elif role in ("boss", "veteran"):
        b_col = (0.18, 0.18, 0.22) if role == "boss" else (0.46, 0.30, 0.16)
        ctx.set_source_rgb(*b_col)
        ctx.arc(0, -hr * 0.58, hr * 0.82, math.pi, 2 * math.pi)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.set_line_width(max(2.5, 4.5 * sh_s * scale))
        ctx.stroke()
        ctx.set_source_rgb(*b_col)
        ctx.move_to(-hr * 1.15, -hr * 0.58)
        ctx.curve_to(-hr * 0.5, -hr * 0.42, hr * 0.5, -hr * 0.42, hr * 1.15, -hr * 0.58)
        ctx.curve_to(hr * 0.5, -hr * 0.70, -hr * 0.5, -hr * 0.70, -hr * 1.15, -hr * 0.58)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.stroke()
    elif role == "tycoon":
        ctx.set_source_rgb(0.14, 0.14, 0.18)
        ctx.rectangle(-hr * 0.72, -hr * 1.75, hr * 1.44, hr * 1.18)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.set_line_width(max(2.5, 4.5 * sh_s * scale))
        ctx.stroke()
        ctx.set_source_rgb(0.96, 0.80, 0.20)
        ctx.rectangle(-hr * 0.72, -hr * 0.78, hr * 1.44, hr * 0.18)
        ctx.fill()
        ctx.set_source_rgb(0.14, 0.14, 0.18)
        ctx.rectangle(-hr * 1.08, -hr * 0.62, hr * 2.16, hr * 0.14)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.stroke()
    elif role == "foreman":
        ctx.set_source_rgb(0.14, 0.24, 0.48)
        ctx.arc(0, -hr * 0.65, hr * 0.88, math.pi, 2 * math.pi)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.stroke()
        ctx.set_source_rgb(0.96, 0.80, 0.20)
        ctx.rectangle(-hr * 0.82, -hr * 0.68, hr * 1.64, hr * 0.12)
        ctx.fill()

    fx = math.sin(total_hyaw) * hr * 0.38
    fy = math.sin(hpitch) * hr * 0.32
    foreshorten = max(0.50, math.cos(total_hyaw))
    is_blink = ((t + bx * 0.01) % 3.2) > 3.06

    for sx_dir in (-1, 1):
        ex = fx + sx_dir * hr * 0.31 * foreshorten
        ey = fy + hr * 0.02
        er = hr * 0.20

        if expr in ("closed_smile", "squint") or is_blink:
            ctx.set_source_rgb(0.10, 0.08, 0.08)
            ctx.set_line_width(max(2.5, 4.8 * sh_s * scale))
            ctx.arc(ex, ey + er * 0.2, er * 0.75, math.pi * 1.1, math.pi * 1.9)
            ctx.stroke()
        else:
            ctx.set_source_rgb(0.99, 0.99, 1.0)
            ctx.arc(ex, ey, er, 0, 2 * math.pi)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.10, 0.08, 0.08)
            ctx.set_line_width(max(2.0, 3.6 * sh_s * scale))
            ctx.stroke()
            ctx.arc(ex + math.sin(hyaw) * er * 0.35, ey + math.sin(hpitch) * er * 0.3, er * 0.38, 0, 2 * math.pi)
            ctx.fill()

        ctx.set_source_rgb(0.14, 0.10, 0.08)
        ctx.set_line_width(max(2.5, 5.5 * sh_s * scale))
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        by_off = -er * 1.25
        if expr in ("angry", "rage"):
            ctx.move_to(ex - er * 0.85, ey + by_off - sx_dir * er * 0.35)
            ctx.line_to(ex + er * 0.85, ey + by_off + sx_dir * er * 0.35)
        elif expr in ("panic", "worried"):
            ctx.move_to(ex - er * 0.85, ey + by_off + sx_dir * er * 0.30)
            ctx.line_to(ex + er * 0.85, ey + by_off - sx_dir * er * 0.30)
        else:
            ctx.move_to(ex - er * 0.85, ey + by_off)
            ctx.line_to(ex + er * 0.85, ey + by_off)
        ctx.stroke()

    mx, my = fx, fy + hr * 0.44
    mw = hr * 0.42 * foreshorten
    mh = hr * 0.26
    ctx.set_source_rgb(0.10, 0.08, 0.08)
    ctx.set_line_width(max(2.2, 4.2 * sh_s * scale))
    if expr in ("rage", "grin"):
        ctx.set_source_rgb(0.99, 0.99, 1.0)
        ctx.rectangle(mx - mw, my - mh * 0.5, mw * 2, mh)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.stroke()
        ctx.move_to(mx - mw, my)
        ctx.line_to(mx + mw, my)
        ctx.stroke()
        for tx_m in (-0.5, 0.0, 0.5):
            ctx.move_to(mx + tx_m * mw * 2, my - mh * 0.5)
            ctx.line_to(mx + tx_m * mw * 2, my + mh * 0.5)
            ctx.stroke()
    elif expr == "panic":
        ctx.move_to(mx - mw * 0.8, my)
        ctx.curve_to(mx - mw * 0.4, my - mh * 0.5, mx, my + mh * 0.5, mx + mw * 0.4, my - mh * 0.4)
        ctx.line_to(mx + mw * 0.8, my + mh * 0.2)
        ctx.stroke()
    elif expr == "angry":
        ctx.arc(mx, my + mh * 0.4, mw * 0.65, math.pi * 1.15, math.pi * 1.85)
        ctx.stroke()
    else:
        ctx.move_to(mx - mw * 0.6, my)
        ctx.curve_to(mx - mw * 0.1, my + mh * 0.35, mx + mw * 0.2, my + mh * 0.3, mx + mw * 0.65, my - mh * 0.15)
        ctx.stroke()

    if sweat:
        ctx.set_source_rgb(0.32, 0.78, 0.98)
        ctx.arc(-hr * 0.68, -hr * 0.10, hr * 0.14, 0, 2 * math.pi)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.set_line_width(max(1.5, 2.5 * sh_s * scale))
        ctx.stroke()

    ctx.restore()

    # 5. Compute & Draw 3D Arm Joints + Front Props (drawn AFTER head so front props like newspaper are 100% readable!)
    sh_l = local_to_world(-32, 134 + breath, 0, True)
    sh_r = local_to_world(32, 134 + breath, 0, True)

    if pose == "sawing_rail":
        saw_stroke = math.sin(t * 18.0) * 18.0
        el_l = local_to_world(-34, 98, -22 + saw_stroke * 0.5, True)
        wr_l = local_to_world(-12, 68, -42 + saw_stroke, True)
        el_r = local_to_world(36, 96, -24 + saw_stroke * 0.5, True)
        wr_r = local_to_world(16, 64, -44 + saw_stroke, True)
    elif pose == "cane_rage":
        shake = math.sin(t * 20.0) * 16.0
        el_l = local_to_world(-48, 148 + shake, -18, True)
        wr_l = local_to_world(-72, 175 + shake, -28, True)
        el_r = local_to_world(44, 112, -16, True)
        wr_r = local_to_world(56, 86, -22, True)
    elif pose == "wipe_sweat":
        el_l = local_to_world(-52, 156, -18, True)
        wr_l = local_to_world(-34, 198, -28, True)
        el_r = local_to_world(38, 102, -8, True)
        wr_r = local_to_world(36, 74, -14, True)
    elif pose == "read_newspaper":
        el_l = local_to_world(-58, 98, -24, True)
        wr_l = local_to_world(-66, 92, -48, True)
        el_r = local_to_world(58, 98, -24, True)
        wr_r = local_to_world(66, 92, -48, True)
    else:
        el_l = local_to_world(-38, 102, -8, True)
        wr_l = local_to_world(-36, 72, -14, True)
        el_r = local_to_world(38, 102, -8, True)
        wr_r = local_to_world(36, 72, -14, True)

    # Draw 3D arms first so that when holding a newspaper, the arms sit naturally BEHIND the newspaper board!
    wrist_projs = []
    for sh_p, el_p, wr_p in [(sh_l, el_l, wr_l), (sh_r, el_r, wr_r)]:
        _, _, s_wr = draw_curved_limb_3d(ctx, cam, sh_p, el_p, wr_p, thickness=8.2 * scale)
        wrist_projs.append(s_wr)

    # If holding newspaper, draw the newspaper board OVER the chest/arms, then draw the white hands gripping its outer edges!
    if prop == "newspaper":
        np_c = cam.project(local_to_world(0, 88, -50, True))
        ns = np_c[3] * scale
        ctx.save()
        ctx.translate(np_c[0], np_c[1])
        ctx.set_source_rgb(0.97, 0.94, 0.85)
        ctx.rectangle(-68 * ns, -72 * ns, 136 * ns, 154 * ns)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.14, 0.12, 0.10)
        ctx.set_line_width(3.8 * ns)
        ctx.stroke()
        ctx.select_font_face("Georgia", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(10 * ns)
        ctx.move_to(-56 * ns, -48 * ns)
        ctx.show_text("The Red Mesa Herald")
        ctx.set_font_size(13 * ns)
        ctx.set_source_rgb(0.78, 0.14, 0.14)
        ctx.move_to(-56 * ns, -22 * ns)
        ctx.show_text("THE CLICKETY")
        ctx.move_to(-52 * ns, -5 * ns)
        ctx.show_text("CLACK LINE!")
        # Cartoon train sketch box on newspaper
        ctx.set_source_rgb(0.22, 0.20, 0.18)
        ctx.set_line_width(2.2 * ns)
        ctx.rectangle(-46 * ns, 12 * ns, 92 * ns, 48 * ns)
        ctx.stroke()
        # Mini locomotive illustration inside the newspaper box
        ctx.set_source_rgb(0.25, 0.25, 0.28)
        ctx.rectangle(-30 * ns, 28 * ns, 42 * ns, 20 * ns)
        ctx.fill()
        ctx.rectangle(-24 * ns, 16 * ns, 10 * ns, 12 * ns)
        ctx.fill()
        ctx.restore()

    for s_wr in wrist_projs:
        draw_3d_sphere_shaded(ctx, s_wr[0], s_wr[1], 7.5 * s_wr[3] * scale, (1.0, 1.0, 1.0), (0.92, 0.92, 0.94), (0.75, 0.75, 0.78), stroke_w=2.5 * s_wr[3] * scale)

    if prop == "hacksaw":
        s_wl = cam.project(wr_l)
        s_wr = cam.project(wr_r)
        ks = s_wr[3] * scale
        ctx.save()
        ctx.set_source_rgb(0.28, 0.26, 0.28)
        ctx.set_line_width(5.5 * ks)
        ctx.move_to(s_wl[0], s_wl[1])
        ctx.line_to(s_wl[0], s_wl[1] - 28 * ks)
        ctx.line_to(s_wr[0] + 65 * ks, s_wr[1] - 22 * ks)
        ctx.line_to(s_wr[0] + 65 * ks, s_wr[1] + 6 * ks)
        ctx.stroke()
        ctx.set_source_rgb(0.92, 0.96, 1.0)
        ctx.set_line_width(3.8 * ks)
        ctx.move_to(s_wl[0], s_wl[1])
        ctx.line_to(s_wr[0] + 65 * ks, s_wr[1] + 6 * ks)
        ctx.stroke()
        # Bright orange saw sparks at rail cut!
        if int(t * 20) % 2 == 0:
            ctx.set_source_rgb(1.0, 0.82, 0.18)
            for sp_a in (-0.6, -0.2, 0.3, 0.7):
                ctx.move_to(s_wr[0] + 30 * ks, s_wr[1] + 4 * ks)
                ctx.line_to(s_wr[0] + (30 + math.cos(sp_a) * 24) * ks, s_wr[1] + (4 - abs(math.sin(sp_a)) * 24) * ks)
                ctx.stroke()
        ctx.restore()
    elif prop == "cane":
        s_wl = cam.project(wr_l)
        ks = s_wl[3] * scale
        ctx.save()
        ctx.set_source_rgb(0.68, 0.46, 0.16)
        ctx.set_line_width(6.0 * ks)
        ctx.move_to(s_wl[0], s_wl[1])
        if pose == "cane_rage":
            ctx.line_to(s_wl[0] - 48 * ks, s_wl[1] - 65 * ks)
        elif pose == "inspect_gap":
            ctx.line_to(s_wl[0] - 32 * ks, s_wl[1] + 62 * ks)
        else:
            ctx.line_to(s_wl[0] - 18 * ks, s_wl[1] + 95 * ks)
        ctx.stroke()
        ctx.restore()
    elif prop == "tin_mug":
        mw = cam.project(wr_l)
        ms = mw[3] * scale
        ctx.save()
        ctx.translate(mw[0], mw[1])
        ctx.set_source_rgb(0.18, 0.48, 0.86)
        ctx.rectangle(-16 * ms, -18 * ms, 32 * ms, 36 * ms)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.10, 0.08, 0.08)
        ctx.set_line_width(3 * ms)
        ctx.stroke()
        for d_i in range(3):
            ctx.set_source_rgb(0.32, 0.76, 0.98)
            ctx.arc((-12 + d_i * 12) * ms, (-26 - abs(math.sin(t * 22 + d_i)) * 18) * ms, 5 * ms, 0, 2 * math.pi)
            ctx.fill()
        ctx.restore()


# ==============================================================================
# GLITCH-FREE SEGMENTED 3D TRACK, SIDE-PROFILE MACRO RAIL JOINT & BRIDGES
# ==============================================================================

def get_rail_heat_colors(rail_heat):
    if rail_heat <= 0.01:
        return (0.72, 0.76, 0.82), (0.42, 0.45, 0.52)
    elif rail_heat < 0.5:
        u = rail_heat * 2.0
        r_top = (lerp(0.72, 0.96, u), lerp(0.76, 0.28, u), lerp(0.82, 0.86, u))
        r_side = (lerp(0.42, 0.62, u), lerp(0.45, 0.12, u), lerp(0.52, 0.58, u))
        return r_top, r_side
    else:
        u = (rail_heat - 0.5) * 2.0
        r_top = (lerp(0.96, 1.00, u), lerp(0.28, 0.94, u), lerp(0.86, 0.36, u))
        r_side = (lerp(0.62, 0.88, u), lerp(0.12, 0.68, u), lerp(0.58, 0.14, u))
        return r_top, r_side


def draw_3d_canyon_and_track(
    ctx,
    cam,
    t,
    gap_size=14.0,
    rail_heat=0.0,
    show_39ft=False,
    show_crate=False,
    cal_month="MAY",
):
    pat = cairo.LinearGradient(0, 0, 0, H)
    pat.add_color_stop_rgb(0.0, 0.16, 0.46, 0.88)
    pat.add_color_stop_rgb(0.45, 0.52, 0.74, 0.96)
    pat.add_color_stop_rgb(1.0, 0.08, 0.22, 0.64)
    ctx.set_source(pat)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    # 3D Red-Rock Striated Canyon Wall on right
    draw_poly_3d(ctx, cam, [(135, 0, -240), (135, 0, 880), (220, 620, 880), (220, 620, -240)], (0.88, 0.36, 0.14), stroke_w=4.5)
    for sy_b, scol in [(95, (0.96, 0.54, 0.18)), (210, (0.72, 0.22, 0.10)), (340, (0.94, 0.44, 0.16)), (460, (0.64, 0.18, 0.12))]:
        draw_poly_3d(ctx, cam, [(140, sy_b, -240), (140, sy_b, 880), (165, sy_b + 55, 880), (165, sy_b + 55, -240)], scol, stroke_rgb=None)

    # 3D Railroad Ledge & Gravel Ballast Bed
    draw_poly_3d(ctx, cam, [(-145, 0, -240), (145, 0, -240), (145, 0, 880), (-145, 0, 880)], (0.82, 0.54, 0.32), stroke_rgb=None)
    draw_poly_3d(ctx, cam, [(-85, 2, -240), (85, 2, -240), (85, 2, 880), (-85, 2, 880)], (0.58, 0.48, 0.44), stroke_rgb=None)

    # Draw wooden ties back-to-front so painter's order is 100% consistent
    for tz in range(840, -180, -48):
        draw_box_3d(ctx, cam, (0, 5, tz), (142, 6, 18), top_rgb=(0.48, 0.34, 0.24), front_rgb=(0.36, 0.24, 0.16), side_rgb=(0.28, 0.18, 0.12), stroke_w=2.5)
        if show_39ft and tz == -48:
            tp = cam.project((-52, 9, tz))
            ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(14 * tp[3])
            ctx.set_source_rgb(0.96, 0.96, 0.98)
            ctx.move_to(tp[0] - 18 * tp[3], tp[1])
            ctx.show_text("39 FT")

    r_top, r_side = get_rail_heat_colors(rail_heat)
    half_g = gap_size * 0.5

    # Subdivide rails into back-to-front segments so they NEVER clip or pop!
    for rx in (-46, 46):
        # Back rail segments from z=840 down to z=half_g
        z_cur = 840.0
        while z_cur > half_g + 1.0:
            z_next = max(half_g, z_cur - 120.0)
            seg_len = z_cur - z_next
            draw_box_3d(ctx, cam, (rx, 14, (z_cur + z_next) * 0.5), (10, 12, seg_len), top_rgb=r_top, front_rgb=r_side, side_rgb=r_side, stroke_w=2.8)
            z_cur = z_next

        # Dark gap shadow at z = 0 when gap_size > 1
        if gap_size > 1.0:
            draw_box_3d(ctx, cam, (rx, 13, 0.0), (11, 12, gap_size), top_rgb=(0.08, 0.06, 0.06), front_rgb=(0.08, 0.06, 0.06), side_rgb=(0.08, 0.06, 0.06), stroke_w=1.5)

        # Front rail segments from z=-half_g down to z=-140
        z_cur = -half_g
        while z_cur > -140.0:
            z_next = max(-140.0, z_cur - 90.0)
            seg_len = z_cur - z_next
            if seg_len > 1.0:
                draw_box_3d(ctx, cam, (rx, 14, (z_cur + z_next) * 0.5), (10, 12, seg_len), top_rgb=r_top, front_rgb=r_side, side_rgb=r_side, stroke_w=2.8)
            z_cur = z_next

    if show_crate:
        draw_box_3d(ctx, cam, (78, 36, 95), (68, 58, 32), top_rgb=(0.18, 0.68, 0.42), front_rgb=(0.14, 0.58, 0.34), side_rgb=(0.08, 0.42, 0.24), stroke_w=3.5)
        cp = cam.project((92, 42, 78))
        cs = cp[3]
        ctx.set_source_rgb(0.98, 0.98, 0.98)
        ctx.rectangle(cp[0] - 14 * cs, cp[1] - 18 * cs, 28 * cs, 34 * cs)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.84, 0.16, 0.14)
        ctx.rectangle(cp[0] - 14 * cs, cp[1] - 18 * cs, 28 * cs, 10 * cs)
        ctx.fill()
        ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(7.5 * cs)
        ctx.set_source_rgb(0.12, 0.12, 0.14)
        ctx.move_to(cp[0] - 10 * cs, cp[1] + 6 * cs)
        ctx.show_text(cal_month)


def draw_macro_rail_joint_side_3d(
    ctx,
    t,
    gap_px=42.0,
    rail_heat=0.5,
    cal_month="MAY",
    insert_mode=None,  # None, 'coin', 'paper', 'crush_arrows'
):
    """
    Crystal-clear side-profile 3D macro view of the steel rail joint (matching ref_sheet_02 frames 15-20!):
    - Shows the red canyon cliff & gravel ballast in 3D perspective
    - Green wooden tool chest in background with Thermometer & '1880 MAY/JUNE/JULY' Calendar + Blue Flag
    - Left & Right 3D Steel I-Beam Rail Ends in side profile with bolted fishplate bar & hex bolts
    - Sliding metal Vernier Caliper mounted on top of the rail measuring the exact gap!
    - Optional silver coin (May) or thin white sheet of paper (July) dropping into the gap!
    """
    # 1. Red Canyon & Gravel Ballast Background
    pat = cairo.LinearGradient(0, 0, 0, H)
    pat.add_color_stop_rgb(0.0, 0.72, 0.24, 0.10)
    pat.add_color_stop_rgb(0.45, 0.92, 0.44, 0.16)
    pat.add_color_stop_rgb(0.46, 0.76, 0.56, 0.42)
    pat.add_color_stop_rgb(1.0, 0.48, 0.38, 0.34)
    ctx.set_source(pat)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    # 3D River-Pebble Ballast Stones in foreground
    rng = np.random.default_rng(42)
    for _ in range(38):
        px = rng.uniform(40, W - 40)
        py = rng.uniform(1180, H - 60)
        pr = rng.uniform(18, 42)
        pcol = rng.choice([(0.68, 0.54, 0.44), (0.52, 0.44, 0.40), (0.78, 0.64, 0.52), (0.42, 0.36, 0.34)])
        draw_3d_sphere_shaded(ctx, px, py, pr, pcol, pcol * 0.85, pcol * 0.65, stroke_w=2.5)

    # 2. Green Tool Chest in Background with Thermometer, Calendar ('MAY'/'JUNE'/'JULY') & Blue Flag
    gx, gy, gw, gh = 380, 560, 260, 190
    ctx.set_source_rgb(0.14, 0.64, 0.38)
    ctx.rectangle(gx, gy, gw, gh)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.08, 0.28, 0.16)
    ctx.set_line_width(5)
    ctx.stroke()
    # Thermometer on left of crate
    ctx.set_source_rgb(0.98, 0.98, 0.98)
    ctx.rectangle(gx + 35, gy + 25, 28, 125)
    ctx.fill_preserve()
    ctx.stroke()
    merc_h = lerp(45, 108, rail_heat)
    ctx.set_source_rgb(0.90, 0.16, 0.14)
    ctx.rectangle(gx + 43, gy + 140 - merc_h, 12, merc_h)
    ctx.fill()
    ctx.arc(gx + 49, gy + 140, 11, 0, 2 * math.pi)
    ctx.fill()
    # Calendar on right of crate
    ctx.set_source_rgb(0.98, 0.98, 0.98)
    ctx.rectangle(gx + 115, gy + 25, 115, 125)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.12, 0.10, 0.10)
    ctx.stroke()
    ctx.set_source_rgb(0.86, 0.16, 0.14)
    ctx.rectangle(gx + 115, gy + 25, 115, 36)
    ctx.fill()
    ctx.select_font_face("Georgia", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(16)
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.move_to(gx + 150, gy + 49)
    ctx.show_text("1880")
    ctx.set_font_size(28)
    ctx.set_source_rgb(0.82, 0.16, 0.14)
    ctx.move_to(gx + 135, gy + 98)
    ctx.show_text(cal_month)
    # Blue flag on pole to right of crate
    ctx.set_source_rgb(0.22, 0.18, 0.14)
    ctx.set_line_width(6)
    ctx.move_to(gx + gw + 75, gy + gh)
    ctx.line_to(gx + gw + 75, gy - 65)
    ctx.stroke()
    ctx.set_source_rgb(0.12, 0.36, 0.94)
    ctx.rectangle(gx + gw + 75, gy - 65, 85, 55)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.08, 0.14, 0.38)
    ctx.stroke()

    # 3. 3D Steel I-Beam Rail Ends in Side Profile (tilted at -12 degrees across frame)
    ctx.save()
    ctx.translate(W * 0.5, 1060)
    ctx.rotate(-0.18)

    r_top, r_side = get_rail_heat_colors(rail_heat)
    half_g = gap_px * 0.5

    # Left Rail (-700 to -half_g) & Right Rail (+half_g to +700)
    for x0, x1 in [(-720, -half_g), (half_g, 720)]:
        rw = x1 - x0
        # Top 3D surface of rail head
        ctx.set_source_rgb(*r_top)
        ctx.move_to(x0, -110)
        ctx.line_to(x0 + 35, -145)
        ctx.line_to(x1 + 35, -145)
        ctx.line_to(x1, -110)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(0.12, 0.08, 0.08)
        ctx.set_line_width(5)
        ctx.stroke()

        # Front face of rail head
        ctx.set_source_rgb(*r_top)
        ctx.rectangle(x0, -110, rw, 52)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.12, 0.08, 0.08)
        ctx.stroke()

        # Dark recessed rail web
        ctx.set_source_rgb(*(np.array(r_side) * 0.65))
        ctx.rectangle(x0, -58, rw, 118)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.12, 0.08, 0.08)
        ctx.stroke()

        # Bottom rail flange
        ctx.set_source_rgb(*r_top)
        ctx.rectangle(x0, 60, rw, 44)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.12, 0.08, 0.08)
        ctx.stroke()

    # Bolted Fishplate Joint Bar straddling the web + 4 3D Hex Bolts
    ctx.set_source_rgb(0.32, 0.24, 0.22)
    ctx.rectangle(-260, -42, 520, 86)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.10, 0.08, 0.08)
    ctx.set_line_width(5)
    ctx.stroke()
    for bx_bolt in (-185, -85, 85, 185):
        draw_3d_sphere_shaded(ctx, bx_bolt, 2, 26, (0.52, 0.44, 0.42), (0.32, 0.26, 0.24), (0.14, 0.10, 0.10), stroke_w=4.0)

    # 4. Sliding Metal Vernier Caliper Mounted on Top of the Rail Measuring the Exact Gap!
    ctx.set_source_rgb(0.84, 0.80, 0.78)
    # Main horizontal scale bar
    ctx.rectangle(-160, -215, 520, 28)
    ctx.fill_preserve()
    ctx.set_source_rgb(0.18, 0.16, 0.16)
    ctx.set_line_width(4)
    ctx.stroke()
    # Left fixed jaw & Right sliding jaw clamping the gap (-half_g, +half_g)
    for jx, jdir in [(-half_g, -1), (half_g, 1)]:
        ctx.set_source_rgb(0.88, 0.84, 0.82)
        ctx.move_to(jx, -235)
        ctx.line_to(jx + jdir * 38, -235)
        ctx.line_to(jx + jdir * 38, -145)
        ctx.line_to(jx, -110)
        ctx.close_path()
        ctx.fill_preserve()
        ctx.set_source_rgb(0.18, 0.16, 0.16)
        ctx.stroke()

    # 5. Inserted Object in Gap: Silver Coin (May), Thin White Paper Sheet (July), or Crushing Stress Arrows!
    if insert_mode == "coin":
        # Gleaming silver coin dropping edge-on into the slot between the rails!
        drop_y = lerp(-280, -115, clamp((t - 48.6) / 0.55))
        ctx.save()
        ctx.translate(0, drop_y)
        ctx.scale(0.38, 1.0)
        draw_3d_sphere_shaded(ctx, 0, 0, 58, (1.0, 1.0, 1.0), (0.82, 0.88, 0.96), (0.45, 0.52, 0.62), stroke_w=4.5)
        ctx.restore()
    elif insert_mode == "paper":
        # Mechanical clamp arm lowering a thin white sheet of paper into the hairline July gap!
        drop_y = lerp(-260, -125, clamp((t - 50.6) / 0.55))
        ctx.set_source_rgb(0.22, 0.24, 0.28)
        ctx.set_line_width(18)
        ctx.move_to(-120, -480)
        ctx.line_to(0, drop_y - 85)
        ctx.stroke()
        ctx.set_source_rgb(0.99, 0.99, 1.0)
        ctx.rectangle(-6, drop_y - 85, 12, 115)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.18, 0.18, 0.22)
        ctx.set_line_width(3)
        ctx.stroke()
    elif insert_mode == "crush_arrows":
        # Rival gapless rails crushing violently against each other (`==><==`) with stress sparks!
        vib = math.sin(t * 35.0) * 6.0
        ctx.set_source_rgb(1.0, 0.95, 0.35)
        ctx.set_line_width(8)
        for s_dir in (-1, 1):
            ax = s_dir * (180 + vib)
            ctx.move_to(ax, -85)
            ctx.line_to(s_dir * 28, -85)
            ctx.line_to(s_dir * 58, -108)
            ctx.move_to(s_dir * 28, -85)
            ctx.line_to(s_dir * 58, -62)
            ctx.stroke()

    ctx.restore()


def draw_3d_steam_locomotive(ctx, cam, z_pos=320.0, x_offset=0.0, t=0.0):
    for k in range(7):
        age = k * 0.18 + ((t * 1.6) % 0.18)
        sp = cam.project((x_offset + math.sin(t * 4 + k) * 12, 165 + age * 145, z_pos + 20 + age * 85))
        draw_3d_sphere_shaded(ctx, sp[0], sp[1], (28 + k * 12) * sp[3], (0.38, 0.36, 0.38), (0.22, 0.20, 0.22), (0.08, 0.08, 0.10), stroke_w=0, alpha=clamp(0.88 - k * 0.10))

    draw_box_3d(ctx, cam, (x_offset, 88, z_pos + 95), (105, 115, 75), top_rgb=(0.14, 0.42, 0.28), front_rgb=(0.12, 0.36, 0.24), side_rgb=(0.08, 0.24, 0.16), stroke_w=4.0)
    draw_box_3d(ctx, cam, (x_offset, 68, z_pos + 15), (78, 76, 115), top_rgb=(0.22, 0.22, 0.26), front_rgb=(0.14, 0.14, 0.18), side_rgb=(0.10, 0.10, 0.12), stroke_w=4.0)
    draw_box_3d(ctx, cam, (x_offset, 128, z_pos - 20), (24, 48, 24), top_rgb=(0.24, 0.24, 0.28), front_rgb=(0.16, 0.16, 0.20), side_rgb=(0.10, 0.10, 0.14), stroke_w=3.5)
    draw_poly_3d(
        ctx,
        cam,
        [
            (x_offset - 52, 12, z_pos - 68),
            (x_offset + 52, 12, z_pos - 68),
            (x_offset, 12, z_pos - 105),
        ],
        (0.84, 0.16, 0.14),
        stroke_w=3.5,
    )
    hp = cam.project((x_offset, 96, z_pos - 45))
    draw_3d_sphere_shaded(ctx, hp[0], hp[1], 18 * hp[3], (1.0, 1.0, 0.90), (1.0, 0.88, 0.35), (0.85, 0.55, 0.10), stroke_w=3.0)


# ==============================================================================
# MASTER 20-SHOT 3D SCENE SEQUENCER (76.67s TIMELINE, ZERO CAPTIONS)
# ==============================================================================

def render_frame(ctx, t):
    ctx.set_source_rgb(0.16, 0.46, 0.88)
    ctx.rectangle(0, 0, W, H)
    ctx.fill()

    sway_x = math.sin(t * 2.5) * 4.0

    # --------------------------------------------------------------------------
    # SHOT 01 (0.00 - 3.15s): Young Engineer Sawing 39-Ft Gaps into 3D Rail
    # --------------------------------------------------------------------------
    if t < 3.15:
        p = clamp(t / 3.15)
        cam = Camera3D(pos=(0 + sway_x, 105, lerp(-215, -175, p)), target=(-10, 68, 40), fov=1080)
        draw_3d_canyon_and_track(ctx, cam, t, gap_size=16.0, show_39ft=True)
        draw_3d_steam_locomotive(ctx, cam, z_pos=lerp(520, 260, p), t=t)
        pose = "sawing_rail" if t < 2.05 else "stand"
        draw_rigged_character_3d(
            ctx,
            cam,
            pos3d=(-26, 8, -15),
            yaw=0.22,
            scale=0.88,
            role="engineer",
            expr="neutral",
            head_rot=(0.15, 0.22 if pose == "sawing_rail" else 0.0, -0.10 if pose == "sawing_rail" else 0.0),
            pose=pose,
            t=t,
            prop="hacksaw",
        )

    # --------------------------------------------------------------------------
    # SHOT 02 (3.15 - 4.75s): Steam Locomotive #7 Roars Past Startled Engineer
    # --------------------------------------------------------------------------
    elif t < 4.75:
        p = clamp((t - 3.15) / 1.60)
        cam = Camera3D(pos=(55 + sway_x * 2, 135, -210), target=(15, 85, 40), fov=1080)
        draw_3d_canyon_and_track(ctx, cam, t, gap_size=16.0)
        draw_3d_steam_locomotive(ctx, cam, z_pos=lerp(220, -60, p), x_offset=-35, t=t)
        draw_rigged_character_3d(
            ctx,
            cam,
            pos3d=(68, 8, -15),
            yaw=-0.35,
            scale=0.88,
            role="engineer",
            expr="squint",
            head_rot=(-0.25, 0.0, 0.15),
            t=t,
        )

    # --------------------------------------------------------------------------
    # SHOT 03 & 04 (4.75 - 10.20s): Two Companies Racing Across Bottomless Canyon
    # --------------------------------------------------------------------------
    elif t < 10.20:
        if t < 7.40:
            # Shot 03: Two Rival Trestle Bridges Racing Side-by-Side Across the Canyon Abyss!
            p = clamp((t - 4.75) / 2.65)
            cam = Camera3D(pos=(0 + sway_x, 260, lerp(-320, -220, p)), target=(0, 60, 180), fov=1050)
            draw_3d_canyon_and_track(ctx, cam, t, gap_size=16.0)
            # Second rival trestle bridge racing in parallel on the left over the blue canyon abyss!
            for tz_b in range(680, -120, -80):
                draw_box_3d(ctx, cam, (-220, -80, tz_b), (32, 180, 32), top_rgb=(0.45, 0.48, 0.56), front_rgb=(0.34, 0.38, 0.46), side_rgb=(0.24, 0.28, 0.36))
            draw_box_3d(ctx, cam, (-220, 14, 240), (110, 10, 720), top_rgb=(0.64, 0.44, 0.28), front_rgb=(0.48, 0.32, 0.18), side_rgb=(0.36, 0.24, 0.12))
        else:
            # Shot 04: Worker on Narrow Cantilever Beam Tilting Down into Bottomless Chasm!
            p = clamp((t - 7.40) / 2.80)
            cam = Camera3D(pos=(-155 + sway_x, lerp(210, 130, p), -175), target=(-60, lerp(85, -140, ease_in_out(p)), 90), fov=1050)
            draw_3d_canyon_and_track(ctx, cam, t, gap_size=16.0)
            draw_box_3d(ctx, cam, (-140, -60, 80), (38, 280, 38), top_rgb=(0.45, 0.48, 0.54), front_rgb=(0.34, 0.38, 0.44), side_rgb=(0.24, 0.28, 0.34))
            draw_box_3d(ctx, cam, (-95, 78, 80), (160, 12, 22), top_rgb=(0.68, 0.46, 0.24), front_rgb=(0.52, 0.34, 0.16), side_rgb=(0.38, 0.24, 0.10))
            draw_rigged_character_3d(
                ctx,
                cam,
                pos3d=(-155, 84, 80),
                yaw=-0.85,
                scale=0.68,
                role="veteran",
                expr="panic",
                spine_lean=(0.45, 0.0),
                t=t,
            )

    # --------------------------------------------------------------------------
    # SHOT 05 & 06 (10.20 - 13.80s): Arched Glass Union Station & Gold Bullion
    # --------------------------------------------------------------------------
    elif t < 13.80:
        if t < 11.45:
            # Shot 05: Fast forward zoom into Grand Arched Glass Union Station ('FIRST LINE IN GETS IT ALL!')
            p = clamp((t - 10.20) / 1.25)
            cam = Camera3D(pos=(0, 165, lerp(-420, -180, ease_in_out(p))), target=(0, 135, 260), fov=1050)
            draw_3d_canyon_and_track(ctx, cam, t, gap_size=0.0)
            # Arched glass station dome & banner
            sp_dome = cam.project((0, 180, 280))
            ctx.set_source_rgb(0.28, 0.42, 0.62)
            ctx.arc(sp_dome[0], sp_dome[1], 240 * sp_dome[3], math.pi, 2 * math.pi)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.12, 0.18, 0.28)
            ctx.set_line_width(5)
            ctx.stroke()
            draw_box_3d(ctx, cam, (0, 95, 275), (420, 180, 40), top_rgb=(0.76, 0.34, 0.24), front_rgb=(0.68, 0.28, 0.20), side_rgb=(0.48, 0.18, 0.14))
            draw_box_3d(ctx, cam, (0, 155, 250), (260, 56, 8), top_rgb=(0.98, 0.94, 0.88), front_rgb=(0.98, 0.94, 0.88), side_rgb=(0.76, 0.18, 0.18))
            bp = cam.project((0, 155, 245))
            ctx.select_font_face("Georgia", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(15 * bp[3])
            ctx.set_source_rgb(0.78, 0.14, 0.14)
            ctx.move_to(bp[0] - 95 * bp[3], bp[1] - 2 * bp[3])
            ctx.show_text("FIRST LINE IN")
            ctx.move_to(bp[0] - 95 * bp[3], bp[1] + 16 * bp[3])
            ctx.show_text("GETS IT ALL!")
        else:
            p = clamp((t - 11.45) / 2.35)
            cam = Camera3D(pos=(0 + sway_x, 145, lerp(-260, -195, p)), target=(0, 120, 60), fov=1100)
            draw_poly_3d(ctx, cam, [(-420, 0, -200), (420, 0, -200), (420, 0, 280), (-420, 0, 280)], (0.72, 0.12, 0.14))
            draw_poly_3d(ctx, cam, [(-420, 0, 180), (420, 0, 180), (420, 420, 180), (-420, 420, 180)], (0.24, 0.34, 0.48))
            draw_box_3d(ctx, cam, (0, 265, 165), (280, 68, 8), top_rgb=(0.98, 0.94, 0.88), front_rgb=(0.98, 0.94, 0.88), side_rgb=(0.76, 0.18, 0.18))
            bp = cam.project((0, 265, 160))
            ctx.select_font_face("Georgia", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(18 * bp[3])
            ctx.set_source_rgb(0.78, 0.14, 0.14)
            ctx.move_to(bp[0] - 115 * bp[3], bp[1] - 4 * bp[3])
            ctx.show_text("FIRST LINE IN")
            ctx.move_to(bp[0] - 115 * bp[3], bp[1] + 18 * bp[3])
            ctx.show_text("GETS IT ALL!")
            for gr in range(3):
                draw_box_3d(ctx, cam, (0, 22 + gr * 22, 65), (220 - gr * 45, 22, 65), top_rgb=(1.0, 0.92, 0.32), front_rgb=(0.94, 0.76, 0.16), side_rgb=(0.72, 0.54, 0.08))
            draw_rigged_character_3d(ctx, cam, pos3d=(35, 0, 10), yaw=-0.15, scale=0.98, role="tycoon", expr="grin", t=t)

    # --------------------------------------------------------------------------
    # SHOT 07 (13.80 - 15.80s): Four Engineers Sitting on High Canyon Beam
    # --------------------------------------------------------------------------
    elif t < 15.80:
        p = clamp((t - 13.80) / 2.00)
        cam = Camera3D(pos=(lerp(-35, 15, p) + sway_x, 145, -245), target=(0, 95, 40), fov=1080)
        draw_3d_canyon_and_track(ctx, cam, t, gap_size=16.0)
        draw_box_3d(ctx, cam, (0, 72, 35), (280, 14, 24), rot_y=0.18, top_rgb=(0.72, 0.52, 0.28), front_rgb=(0.56, 0.38, 0.18), side_rgb=(0.42, 0.28, 0.12))
        for idx, (bx_e, r_e, ex_e) in enumerate([(-95, "veteran", "angry"), (-45, "veteran", "angry"), (5, "veteran", "angry"), (75, "engineer", "grin")]):
            draw_rigged_character_3d(ctx, cam, pos3d=(bx_e, 12, 35 - idx * 8), yaw=-0.18, scale=0.82, role=r_e, expr=ex_e, pose="sit_beam", t=t + idx * 0.4)

    # --------------------------------------------------------------------------
    # SHOT 08 (15.80 - 19.20s): Boss Inspects Finger-Wide Gap (Centered & Clear!)
    # --------------------------------------------------------------------------
    elif t < 19.20:
        p = clamp((t - 15.80) / 3.40)
        cam = Camera3D(pos=(0 + sway_x, lerp(95, 125, p), lerp(-175, -215, p)), target=(0, 75, 10), fov=1100, roll=-0.10 if t < 17.6 else 0.0)
        draw_3d_canyon_and_track(ctx, cam, t, gap_size=22.0, show_39ft=True)
        pose = "inspect_gap" if t < 17.6 else "stand"
        draw_rigged_character_3d(
            ctx,
            cam,
            pos3d=(18, 8, 10),
            yaw=-0.15,
            scale=0.92,
            role="boss",
            expr="angry",
            head_rot=(-0.15, 0.25 if pose == "inspect_gap" else 0.0, -0.25 if pose == "inspect_gap" else 0.0),
            pose=pose,
            t=t,
            prop="cane",
        )

    # --------------------------------------------------------------------------
    # SHOT 09 & 10 (19.20 - 25.00s): Boss's Face Goes Purple & Engineer Refuses
    # --------------------------------------------------------------------------
    elif t < 25.00:
        cam = Camera3D(pos=(0 + sway_x, 135, -225), target=(0, 105, 25), fov=1080)
        draw_3d_canyon_and_track(ctx, cam, t, gap_size=20.0)
        pa = clamp(1.0 - max(0.0, (t - 22.8) / 0.8)) if t >= 19.35 else 0.0
        draw_rigged_character_3d(
            ctx,
            cam,
            pos3d=(42, 8, 20),
            yaw=-0.25,
            scale=0.95,
            role="boss",
            expr="rage",
            pose="cane_rage" if pa > 0.3 else "stand",
            t=t,
            purple_anger=pa,
            prop="cane",
        )
        if t > 20.80:
            draw_rigged_character_3d(
                ctx,
                cam,
                pos3d=(-48, 8, 20),
                yaw=0.25,
                scale=0.92,
                role="engineer",
                expr="neutral",
                head_rot=(0.25, 0.0, 0.0),
                t=t,
            )

    # --------------------------------------------------------------------------
    # SHOT 11 (25.00 - 29.90s): Rival Company Welds Rails Flush End-to-End!
    # --------------------------------------------------------------------------
    elif t < 29.90:
        if t < 27.40:
            # Sub-shot 11a: Macro 3D view of Rival Rails slamming flush together (GAP = 0.0) with welding sparks!
            p = clamp((t - 25.00) / 1.50)
            draw_macro_rail_joint_side_3d(ctx, t, gap_px=lerp(38.0, 0.0, ease_in_out(p)), rail_heat=0.0, cal_month="MAY")
        else:
            # Sub-shot 11b: Foreman & Tycoon celebrating on completed smooth welded track
            p = clamp((t - 27.40) / 2.50)
            cam = Camera3D(pos=(-25 + sway_x, 145, lerp(-230, -185, p)), target=(0, 95, 40), fov=1080)
            draw_3d_canyon_and_track(ctx, cam, t, gap_size=0.0)
            draw_box_3d(ctx, cam, (55, 165, 260), (42, 320, 42), top_rgb=(0.96, 0.78, 0.14), front_rgb=(0.88, 0.68, 0.10), side_rgb=(0.68, 0.50, 0.06))
            # Bright glowing weld bead & sparks on the flush rail between them!
            for rx_w in (-46, 46):
                wp = cam.project((rx_w, 18, -10))
                ws = wp[3]
                draw_3d_sphere_shaded(ctx, wp[0], wp[1], 11 * ws, (1.0, 1.0, 1.0), (0.35, 0.88, 1.0), (0.12, 0.45, 0.92), stroke_w=0)
            draw_rigged_character_3d(ctx, cam, pos3d=(-42, 8, 25), yaw=0.15, scale=0.94, role="foreman", expr="grin", t=t)
            draw_rigged_character_3d(ctx, cam, pos3d=(48, 8, 45), yaw=-0.20, scale=0.94, role="tycoon", expr="grin", t=t)

    # --------------------------------------------------------------------------
    # SHOT 12 (29.90 - 33.10s): Rival 'VANDERGOLD' Luxury Parlor Car Glides
    # --------------------------------------------------------------------------
    elif t < 33.10:
        p = clamp((t - 29.90) / 3.20)
        cam = Camera3D(pos=(0, 145, lerp(-265, -175, ease_in_out(p))), target=(0, 125, 60), fov=1100)
        # Plush crimson-and-gold parlor car interior with side canyon windows & brass lamps!
        draw_poly_3d(ctx, cam, [(-380, 0, 140), (380, 0, 140), (380, 380, 140), (-380, 380, 140)], (0.58, 0.10, 0.14), stroke_w=5.0)
        draw_poly_3d(ctx, cam, [(-380, 0, -200), (380, 0, -200), (380, 0, 140), (-380, 0, 140)], (0.12, 0.22, 0.48))
        # Framed parlor car windows on left and right showing blue canyon sky
        for wx_w in (-135, 135):
            draw_box_3d(ctx, cam, (wx_w, 165, 135), (85, 115, 6), top_rgb=(0.45, 0.72, 0.96), front_rgb=(0.45, 0.72, 0.96), side_rgb=(0.88, 0.72, 0.22))
        # Brass ceiling lamps
        for lx_l in (-95, 95):
            lp = cam.project((lx_l, 265, 95))
            draw_3d_sphere_shaded(ctx, lp[0], lp[1], 18 * lp[3], (1.0, 1.0, 0.90), (1.0, 0.88, 0.35), (0.82, 0.56, 0.12))
        # Velvet armchair + Rival Tycoon + side table with still teacup
        draw_box_3d(ctx, cam, (0, 85, 65), (95, 135, 65), top_rgb=(0.82, 0.14, 0.18), front_rgb=(0.72, 0.10, 0.14), side_rgb=(0.48, 0.06, 0.08))
        draw_box_3d(ctx, cam, (-75, 42, 45), (42, 58, 42), top_rgb=(0.56, 0.32, 0.16), front_rgb=(0.42, 0.22, 0.10), side_rgb=(0.32, 0.16, 0.08))
        draw_box_3d(ctx, cam, (-75, 76, 45), (18, 12, 18), top_rgb=(0.98, 0.98, 1.0), front_rgb=(0.92, 0.94, 0.98), side_rgb=(0.78, 0.80, 0.86))
        draw_rigged_character_3d(ctx, cam, pos3d=(0, 12, 45), yaw=0.0, scale=0.98, role="tycoon", expr="closed_smile", pose="recline_chair", t=t)

    # --------------------------------------------------------------------------
    # SHOT 13 (33.10 - 36.20s): Clickety-Clack Wooden Coach Rattling Over Every Gap
    # --------------------------------------------------------------------------
    elif t < 36.20:
        jolt_y = abs(math.sin(t * 18.0)) * 24.0
        cam = Camera3D(pos=(0, 145 + jolt_y * 0.5, -165), target=(0, 145, 60), fov=1120)
        draw_poly_3d(ctx, cam, [(-380, -80, 60), (380, -80, 60), (380, 380, 60), (-380, 380, 60)], (0.46, 0.24, 0.12), stroke_w=5.0)
        draw_box_3d(ctx, cam, (0, 145, 58), (125, 145, 8), top_rgb=(0.18, 0.24, 0.34), front_rgb=(0.18, 0.24, 0.34), side_rgb=(0.32, 0.16, 0.08), stroke_w=5.0)
        draw_rigged_character_3d(
            ctx,
            cam,
            pos3d=(0, -15 + jolt_y, 48),
            yaw=0.0,
            scale=0.98,
            role="boss",
            expr="panic",
            pose="coach_window",
            t=t,
            sweat=True,
            prop="tin_mug",
        )

    # --------------------------------------------------------------------------
    # SHOT 14 (36.20 - 41.20s): Unobstructed Newspaper & Passengers Switching!
    # --------------------------------------------------------------------------
    elif t < 41.20:
        if t < 38.60:
            p = clamp((t - 36.20) / 2.40)
            cam = Camera3D(pos=(0 + sway_x, 145, lerp(-235, -180, p)), target=(0, 120, 40), fov=1080)
            draw_poly_3d(ctx, cam, [(-420, 0, -200), (420, 0, -200), (420, 0, 280), (-420, 0, 280)], (0.68, 0.52, 0.34))
            draw_poly_3d(ctx, cam, [(-420, 0, 180), (420, 0, 180), (420, 380, 180), (-420, 380, 180)], (0.72, 0.32, 0.22))
            draw_rigged_character_3d(
                ctx,
                cam,
                pos3d=(0, 0, 20),
                yaw=0.0,
                scale=1.02,
                role="boss",
                expr="worried",
                pose="read_newspaper",
                t=t,
                prop="newspaper",
            )
        else:
            # Sub-shot 14b: Passengers walking away from Boss toward 'ALL ABOARD!' Quiet Train!
            p = clamp((t - 38.60) / 2.60)
            cam = Camera3D(pos=(0 + sway_x, 155, -260), target=(0, 120, 80), fov=1050)
            draw_poly_3d(ctx, cam, [(-420, 0, -200), (420, 0, -200), (420, 0, 320), (-420, 0, 320)], (0.68, 0.52, 0.34))
            draw_poly_3d(ctx, cam, [(-420, 0, 240), (420, 0, 240), (420, 420, 240), (-420, 420, 240)], (0.72, 0.32, 0.22))
            # 'ALL ABOARD!' sign clearly positioned above the passengers on the right (unobstructed!)
            draw_box_3d(ctx, cam, (65, 215, 110), (155, 62, 6), rot_y=-0.15, top_rgb=(0.96, 0.92, 0.82), front_rgb=(0.96, 0.92, 0.82), side_rgb=(0.42, 0.28, 0.16))
            ap = cam.project((65, 215, 106))
            ctx.select_font_face("Georgia", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            ctx.set_font_size(14 * ap[3])
            ctx.set_source_rgb(0.78, 0.16, 0.14)
            ctx.move_to(ap[0] - 58 * ap[3], ap[1] + 5 * ap[3])
            ctx.show_text("ALL ABOARD!")
            for p_idx, px_c in enumerate([25, 78, 130]):
                draw_rigged_character_3d(ctx, cam, pos3d=(px_c + p * 35, 0, 85 + p_idx * 25), yaw=0.65, scale=0.72, role="veteran", pose="walk", t=t + p_idx * 0.3)
            draw_rigged_character_3d(ctx, cam, pos3d=(-78, 0, 15), yaw=0.25, scale=0.92, role="boss", expr="angry", t=t, prop="cane")

    # --------------------------------------------------------------------------
    # SHOT 15 & 16 (41.20 - 53.30s): Summer Thermometer & Side-Profile Macro Gap!
    # --------------------------------------------------------------------------
    elif t < 53.30:
        if t < 43.20:
            # Sub-shot 15a: Close-up on Green Crate with Rising Thermometer & '1880 MAY' Calendar!
            p = clamp((t - 41.20) / 2.00)
            draw_macro_rail_joint_side_3d(ctx, t, gap_px=44.0, rail_heat=lerp(0.1, 0.55, p), cal_month="MAY")
        elif t < 45.50:
            # Sub-shot 15b: Sweating Young Engineer wiping brow beside track
            p = clamp((t - 43.20) / 2.30)
            cam = Camera3D(pos=(-15 + sway_x, 135, lerp(-175, -225, p)), target=(15, 95, 45), fov=1080)
            draw_3d_canyon_and_track(ctx, cam, t, gap_size=14.0, rail_heat=0.35, show_crate=True, cal_month="MAY")
            draw_rigged_character_3d(
                ctx,
                cam,
                pos3d=(-32, 8, 15),
                yaw=0.18,
                scale=0.94,
                role="engineer",
                expr="worried",
                pose="wipe_sweat",
                t=t,
                sweat=True,
            )
        else:
            # Shot 16: Side-Profile Macro 3D Rail Joint with Vernier Caliper, Coin (May) & Paper (July)!
            p = clamp((t - 45.50) / 7.80)
            gap_px = lerp(44.0, 8.0, p)
            cal_m = "MAY" if t < 49.8 else ("JUNE" if t < 50.8 else "JULY")
            ins = "coin" if (48.5 <= t < 50.5) else ("paper" if t >= 50.6 else None)
            draw_macro_rail_joint_side_3d(ctx, t, gap_px=gap_px, rail_heat=lerp(0.4, 0.95, p), cal_month=cal_m, insert_mode=ins)

    # --------------------------------------------------------------------------
    # SHOT 17 (53.30 - 56.80s): Thrilled Boss Gloats Over Shrunken '39 FT' Gap
    # --------------------------------------------------------------------------
    elif t < 56.80:
        p = clamp((t - 53.30) / 3.50)
        cam = Camera3D(pos=(0 + sway_x, 125, lerp(-185, -225, p)), target=(0, 85, 10), fov=1080)
        draw_3d_canyon_and_track(ctx, cam, t, gap_size=3.0, rail_heat=0.92, show_39ft=True, show_crate=True, cal_month="JULY")
        draw_rigged_character_3d(ctx, cam, pos3d=(-42, 8, -10), yaw=0.22, scale=0.92, role="engineer", expr="neutral", head_rot=(0.25, 0.0, 0.0), t=t)
        draw_rigged_character_3d(ctx, cam, pos3d=(38, 8, -5), yaw=-0.25, scale=0.95, role="boss", expr="grin", t=t, prop="cane")

    # --------------------------------------------------------------------------
    # SHOT 18 (56.80 - 64.10s): Rival Rails Crushing Together & Lounging Tycoon!
    # --------------------------------------------------------------------------
    elif t < 64.10:
        if t < 59.40:
            # Sub-shot 18a: Macro side-profile showing Rival Gapless Rails Crushing Together (`==><==`)!
            draw_macro_rail_joint_side_3d(ctx, t, gap_px=0.0, rail_heat=0.65, cal_month="JULY", insert_mode="crush_arrows")
        else:
            # Sub-shot 18b: Sweeping bridge shot pushing in on Rival Tycoon under Beach Umbrella!
            p = clamp((t - 59.40) / 4.70)
            cam = Camera3D(pos=(lerp(-15, 35, p) + sway_x, 120, lerp(-235, -155, ease_in_out(p))), target=(35, 85, 75), fov=1080)
            draw_poly_3d(ctx, cam, [(-240, 0, -180), (240, 0, -180), (240, 0, 880), (-240, 0, 880)], (0.58, 0.36, 0.24))
            for tz in range(800, -140, -48):
                draw_box_3d(ctx, cam, (0, 5, tz), (140, 6, 18), top_rgb=(0.34, 0.24, 0.18), front_rgb=(0.24, 0.16, 0.12), side_rgb=(0.18, 0.12, 0.08))
            for rx in (-46, 46):
                draw_box_3d(ctx, cam, (rx, 14, 260), (10, 12, 760), top_rgb=(0.98, 0.28, 0.78), front_rgb=(0.76, 0.14, 0.56), side_rgb=(0.58, 0.08, 0.42))
            # 3D Beach Umbrella canopy & pole + striped deck chair + Rival Tycoon
            draw_box_3d(ctx, cam, (88, 105, 85), (6, 190, 6), top_rgb=(0.82, 0.82, 0.86), front_rgb=(0.68, 0.68, 0.72), side_rgb=(0.52, 0.52, 0.56))
            # Multi-panel striped beach umbrella canopy above Tycoon
            draw_poly_3d(ctx, cam, [(12, 182, 80), (62, 182, 72), (88, 232, 85)], (0.96, 0.24, 0.16), stroke_w=3.5)
            draw_poly_3d(ctx, cam, [(62, 182, 72), (114, 182, 72), (88, 232, 85)], (0.98, 0.94, 0.88), stroke_w=3.5)
            draw_poly_3d(ctx, cam, [(114, 182, 72), (164, 182, 80), (88, 232, 85)], (0.96, 0.52, 0.14), stroke_w=3.5)
            draw_box_3d(ctx, cam, (88, 42, 78), (58, 68, 52), top_rgb=(0.96, 0.82, 0.16), front_rgb=(0.22, 0.20, 0.18), side_rgb=(0.88, 0.72, 0.12))
            draw_rigged_character_3d(ctx, cam, pos3d=(88, 8, 72), yaw=-0.22, scale=0.88, role="tycoon", expr="closed_smile", pose="recline_chair", t=t)

    # --------------------------------------------------------------------------
    # SHOT 19 (64.10 - 70.20s): Hottest Day — Engineer's Gaps Click Shut Flush!
    # --------------------------------------------------------------------------
    elif t < 70.20:
        if t < 66.80:
            cam = Camera3D(pos=(0 + sway_x, 135, -185), target=(0, 95, 10), fov=1100)
            draw_3d_canyon_and_track(ctx, cam, t, gap_size=2.0, rail_heat=0.98, show_39ft=True)
            draw_rigged_character_3d(ctx, cam, pos3d=(0, 8, -10), yaw=0.0, scale=0.98, role="engineer", expr="grin", t=t)
        elif t < 68.80:
            # Side-profile macro 3D view as the two glowing yellow-gold rail ends click flush together!
            close_p = clamp((t - 66.80) / 0.65)
            draw_macro_rail_joint_side_3d(ctx, t, gap_px=lerp(18.0, 0.0, ease_in_out(close_p)), rail_heat=1.0, cal_month="JULY")
        else:
            cam = Camera3D(pos=(-25, 225, -240), target=(0, 65, 180), fov=1050)
            draw_3d_canyon_and_track(ctx, cam, t, gap_size=0.0, rail_heat=0.35)
            draw_rigged_character_3d(ctx, cam, pos3d=(-25, 8, -20), yaw=0.0, scale=0.78, role="engineer", expr="closed_smile", t=t)

    # --------------------------------------------------------------------------
    # SHOT 20 (70.20 - 76.67s): Rival Bridge Track Kicks Sideways Like a Snake!
    # --------------------------------------------------------------------------
    else:
        if t < 73.95:
            p = clamp((t - 70.20) / 3.75)
            buckle = clamp((t - 72.10) / 0.85)
            cam = Camera3D(pos=(0 + sway_x * 2, 165, -260), target=(0, 75, 160), fov=1080)
            # Canyon & 3D Bridge Deck with Side Railings & Streetlamps
            draw_3d_canyon_and_track(ctx, cam, t, gap_size=0.0, rail_heat=0.85)
            draw_poly_3d(ctx, cam, [(-165, 4, -180), (165, 4, -180), (165, 4, 840), (-165, 4, 840)], (0.52, 0.32, 0.22))
            for tz_l in range(720, -100, -140):
                for sx_l in (-145, 145):
                    draw_box_3d(ctx, cam, (sx_l, 48, tz_l), (6, 85, 6), top_rgb=(0.22, 0.20, 0.22), front_rgb=(0.16, 0.14, 0.16))
            # S-Curve Buckled Glowing Steel Rails!
            for rx in (-46, 46):
                pts_r = []
                for z_s in range(-120, 620, 24):
                    s_off = math.sin(z_s * 0.022) * 76.0 * buckle * math.exp(-((z_s - 65) ** 2) / 36000.0)
                    pts_r.append(cam.project((rx + s_off, 16, z_s)))
                ctx.set_source_rgb(1.0, 0.90, 0.28)
                ctx.set_line_width(11.0)
                ctx.move_to(pts_r[0][0], pts_r[0][1])
                for pr in pts_r[1:]:
                    ctx.line_to(pr[0], pr[1])
                ctx.stroke()
            draw_3d_steam_locomotive(ctx, cam, z_pos=lerp(460, 75, p), x_offset=buckle * 24.0, t=t)
        elif t < 75.15:
            # Side profile of 3D Steel Arch Bridge across Red Canyon Gorge as Locomotive plunges off!
            p = clamp((t - 73.95) / 1.20)
            pat = cairo.LinearGradient(0, 0, 0, H)
            pat.add_color_stop_rgb(0.0, 0.96, 0.86, 0.72)
            pat.add_color_stop_rgb(0.65, 0.92, 0.72, 0.54)
            pat.add_color_stop_rgb(1.0, 0.68, 0.36, 0.22)
            ctx.set_source(pat)
            ctx.rectangle(0, 0, W, H)
            ctx.fill()
            cam = Camera3D(pos=(0, 120, -420), target=(0, 100, 0), fov=1050)
            # Left & Right Red Canyon Cliff Abutments
            draw_box_3d(ctx, cam, (-240, 20, 0), (140, 520, 90), top_rgb=(0.78, 0.34, 0.18), front_rgb=(0.68, 0.26, 0.14), side_rgb=(0.52, 0.18, 0.10))
            draw_box_3d(ctx, cam, (240, 20, 0), (140, 520, 90), top_rgb=(0.78, 0.34, 0.18), front_rgb=(0.68, 0.26, 0.14), side_rgb=(0.52, 0.18, 0.10))
            # Steel Arch & Vertical Spandrel Columns
            ctx.set_source_rgb(0.24, 0.22, 0.22)
            ctx.set_line_width(14)
            ctx.arc(W * 0.5, 1180, 420, math.pi * 1.12, math.pi * 1.88)
            ctx.stroke()
            for sp_x in range(-150, 180, 50):
                arch_h = math.cos(sp_x / 210.0) * 110.0
                draw_box_3d(ctx, cam, (sp_x, 95 + arch_h * 0.5, 0), (8, 110 - arch_h * 0.5, 12), top_rgb=(0.28, 0.26, 0.26), front_rgb=(0.22, 0.20, 0.20))
            # Bridge Deck
            draw_box_3d(ctx, cam, (0, 155, 0), (680, 18, 48), top_rgb=(0.32, 0.28, 0.24), front_rgb=(0.24, 0.20, 0.18))
            # Plunging Locomotive + tender + smoke + fire sparks!
            loco_y = 140 - (p ** 1.6) * 260
            draw_box_3d(ctx, cam, (-35, loco_y, -30), (54, 115, 48), rot_y=0.35, top_rgb=(0.18, 0.22, 0.26), front_rgb=(0.12, 0.14, 0.18), side_rgb=(0.14, 0.38, 0.24))
            draw_box_3d(ctx, cam, (-35, loco_y + 72, -30), (48, 52, 44), rot_y=0.35, top_rgb=(0.14, 0.42, 0.28), front_rgb=(0.10, 0.32, 0.20))
            for sk in range(5):
                sp = cam.project((-35 + sk * 12, loco_y + 95 + sk * 28, -30))
                draw_3d_sphere_shaded(ctx, sp[0], sp[1], (22 + sk * 8) * sp[3], (0.38, 0.36, 0.38), (0.22, 0.20, 0.22), (0.08, 0.08, 0.10), stroke_w=0, alpha=0.82)
        else:
            p = clamp((t - 75.15) / 1.50)
            rng = np.random.default_rng(999)
            for k in range(28):
                fx = rng.uniform(120, W - 120) + math.sin(t * 12 + k) * 28
                fy = rng.uniform(160, H - 160) - p * 85
                fr = rng.uniform(140, 320) * (0.75 + 0.35 * p)
                draw_3d_sphere_shaded(
                    ctx,
                    fx,
                    fy,
                    fr,
                    (1.0, 0.98, 0.68),
                    (0.98, 0.56, 0.12),
                    (0.68, 0.20, 0.04),
                    stroke_w=0,
                    alpha=0.88,
                )


def generate_preview_sheets():
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)
    tw, th = 270, 480
    cols, rows = 6, 4

    for sheet_idx in range(3):
        grid = np.zeros((rows * th, cols * tw, 3), dtype=np.uint8)
        for i in range(24):
            tile_idx = sheet_idx * 24 + i
            t = min(DURATION - 0.05, tile_idx * (DURATION / 72.0) + 0.35)
            render_frame(ctx, t)
            buf = np.frombuffer(surf.get_data(), dtype=np.uint8).reshape((H, W, 4))
            rgb = buf[::4, ::4, :3][:, :, ::-1]
            r = i // cols
            c = i % cols
            grid[r * th : (r + 1) * th, c * tw : (c + 1) * tw] = rgb

        out_jpg = os.path.join(SCRATCH_DIR, f"train_rigged_3d_sheet_{sheet_idx+1:02d}.jpg")
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
    print("Generated upgraded glitch-free train_rigged_3d_sheet_01..03.jpg!")


def render_full_video():
    generate_preview_sheets()
    muted_mp4 = os.path.join(OUT_DIR, "Video_Only_No_Captions_Muted.mp4")
    final_mp4 = os.path.join(OUT_DIR, "Final_Video_No_Captions.mp4")
    proc_mp4 = os.path.join(OUT_DIR, "Pure_3D_Procedural_From_Scratch_No_Captions.mp4")
    audio_wav = os.path.join(OUT_DIR, "Full_Mixed_Audio.wav")

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
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        muted_mp4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surf)

    for f in range(TOTAL_FRAMES):
        render_frame(ctx, f / FPS)
        proc.stdin.write(surf.get_data())
        if (f + 1) % 400 == 0:
            print(f"Rendered {f + 1} / {TOTAL_FRAMES} glitch-free rigged 3D train frames...", flush=True)

    proc.stdin.close()
    proc.wait()

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            muted_mp4,
            "-i",
            audio_wav,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            final_mp4,
        ],
        check=True,
    )
    shutil.copy2(final_mp4, proc_mp4)
    print(f"Finished rendering {final_mp4} and {proc_mp4} ({TOTAL_FRAMES} frames)!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "preview":
        generate_preview_sheets()
    else:
        render_full_video()
