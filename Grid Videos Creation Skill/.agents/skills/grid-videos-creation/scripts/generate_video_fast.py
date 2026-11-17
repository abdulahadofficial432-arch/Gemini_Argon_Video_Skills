import os
import time
import subprocess
import numpy as np
from scipy import ndimage
from scipy.interpolate import PchipInterpolator
from PIL import Image, ImageDraw, ImageFont

t0 = time.time()
workspace_dir = r"C:\Users\WayWe Work-Station\Downloads\Make video"
data_dir = os.path.join(workspace_dir, "My Data")
ref_video_path = os.path.join(workspace_dir, "ref video", "ref video.mp4")
scratch_dir = r"C:\Users\WayWe Work-Station\.gemini\antigravity\brain\37972dcb-033f-4d00-a7de-f932e8a0c15e\scratch"
fdir = os.path.join(scratch_dir, "frames")
font_dir = os.path.join(scratch_dir, "fonts")
out_video_path = os.path.join(workspace_dir, "Muskan_Syed_Video.mp4")
out_video_path2 = os.path.join(workspace_dir, "Final Video.mp4")

W, H = 1080, 1350
CREAM = (231, 243, 208)
CREAM_ARR = np.array([231.0, 243.0, 208.0], dtype=np.float32)
DARK_TEXT = (35, 38, 22)

def ease_out_cubic(t):
    t = float(np.clip(t, 0.0, 1.0))
    return 1.0 - (1.0 - t) ** 3

def ease_in_out_cubic(t):
    t = float(np.clip(t, 0.0, 1.0))
    return 4.0 * t * t * t if t < 0.5 else 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0

print("1. Preparing base assets...")
grid_im = Image.open(os.path.join(data_dir, "Grid Background.jpg"))
grid_1080_pil = grid_im.resize((1080, 1446), Image.Resampling.LANCZOS).crop((0, 48, 1080, 1398))
grid_1080 = np.array(grid_1080_pil, dtype=np.float32)

plain_im = Image.open(os.path.join(data_dir, "Plain Background.jpg"))
plain_1080_pil = plain_im.resize((1080, 1446), Image.Resampling.LANCZOS).crop((0, 37, 1080, 1387))
plain_1080 = np.array(plain_1080_pil, dtype=np.float32)
olive_col = np.median(plain_1080.reshape(-1, 3), axis=0)

bar_im = Image.open(os.path.join(data_dir, "Bar.jpg"))
bar_1080_pil = bar_im.resize((1080, 1446), Image.Resampling.LANCZOS).crop((0, 37, 1080, 1387))
bar_1080 = np.array(bar_1080_pil, dtype=np.float32)

# Character cutout (compute at target resolution for 5x faster initialization!)
char_scale = 0.435
cw, ch = int(1792 * char_scale), int(2400 * char_scale)
char_small_im = Image.open(os.path.join(data_dir, "Character.jpg")).resize((cw, ch), Image.Resampling.LANCZOS)
char_arr = np.array(char_small_im, dtype=np.float32)

bg_color = np.array([65.0, 62.0, 44.0], dtype=np.float32)
dist_to_bg = np.sqrt(np.sum((char_arr - bg_color) ** 2, axis=2))
labeled, _ = ndimage.label(dist_to_bg < 65)
outer_bg_mask = (labeled == labeled[0, 0])

luma = 0.299 * char_arr[:, :, 0] + 0.587 * char_arr[:, :, 1] + 0.114 * char_arr[:, :, 2]
sat = np.max(char_arr, axis=2) - np.min(char_arr, axis=2)
is_white_cand = (luma > 175) & (sat < 40)

boundary = ndimage.binary_dilation(outer_bg_mask, iterations=2) & (~ndimage.binary_erosion(outer_bg_mask, iterations=1))
alpha = np.where(outer_bg_mask, 0.0, 1.0)
alpha = np.where(boundary, np.clip((luma - 63.0) / (240.0 - 63.0), 0.0, 1.0), alpha)
alpha = ndimage.gaussian_filter(alpha, sigma=0.5)

# Keep original white outline from Character.jpg!
rgba_white = np.dstack([char_arr.astype(np.uint8), (alpha * 255).astype(np.uint8)])
char_pil = Image.fromarray(rgba_white)
CHAR_X, CHAR_Y = 58, 306

popup_f = [159, 162, 165, 168, 170, 173, 175, 178, 180, 183, 185, 187]
popup_y = [1050, 980, 890, 680, 530, 280, 155, 72, 38, 10, 2, 0]
char_popup_interp = PchipInterpolator(popup_f, popup_y)

# Static "Helloo" + smile composite base (Helloo from F155[:405] + pure smile from F190[402:445, 818:910]!)
f155_ref = np.array(Image.open(os.path.join(fdir, "f_0155.jpg")), dtype=np.float32)
f190_ref = np.array(Image.open(os.path.join(fdir, "f_0190.jpg")), dtype=np.float32)
helloo_with_smile_alpha = np.zeros((450, W), dtype=np.float32)
helloo_with_smile_alpha[:405, :] = np.clip((f155_ref[:405, :, 1] - 42.0) / (240.0 - 42.0), 0.0, 1.0)
smile_clean = np.clip((f190_ref[402:445, 818:910, 1] - 42.0) / (240.0 - 42.0), 0.0, 1.0)
helloo_with_smile_alpha[402:445, 818:910] = np.maximum(helloo_with_smile_alpha[402:445, 818:910], smile_clean)

base_helloo_smile = grid_1080.copy()
for c in range(3):
    base_helloo_smile[:450, :, c] = base_helloo_smile[:450, :, c] * (1.0 - helloo_with_smile_alpha) + CREAM_ARR[c] * helloo_with_smile_alpha
base_helloo_smile_pil = Image.fromarray(base_helloo_smile.astype(np.uint8))

f_left = ImageFont.truetype(os.path.join(font_dir, "Poppins-Regular.ttf"), 28)
f_right_reg = ImageFont.truetype(os.path.join(font_dir, "Poppins-Regular.ttf"), 34)
f_right_bold = ImageFont.truetype(os.path.join(font_dir, "Poppins-SemiBold.ttf"), 36)
f_bar_bold = ImageFont.truetype(os.path.join(font_dir, "Poppins-SemiBold.ttf"), 40)
f_bar_reg = ImageFont.truetype(os.path.join(font_dir, "Poppins-Regular.ttf"), 40)

# Pre-build tilted pill badge "Graphics Expert ❤"
badge_w, badge_h = 284, 52
bw2, bh2 = badge_w * 2, badge_h * 2
badge_im = Image.new("RGBA", (bw2, bh2), (0, 0, 0, 0))
bdraw = ImageDraw.Draw(badge_im)
bdraw.rounded_rectangle([0, 0, bw2 - 1, bh2 - 1], radius=28, fill=(int(olive_col[0]), int(olive_col[1]), int(olive_col[2]), 255))
f_badge = ImageFont.truetype(os.path.join(font_dir, "Poppins-Regular.ttf"), 48)
bdraw.text((bw2 // 2 - 24, bh2 // 2), "Graphics Expert", fill=(231, 243, 208, 255), font=f_badge, anchor="mm")
hx, hy = bw2 - 46, bh2 // 2 + 2
hr = 16
t_heart = np.linspace(0, 2 * np.pi, 100)
px = hx + hr * (16 * np.sin(t_heart) ** 3) / 16.0 * 1.15
py = hy - hr * (13 * np.cos(t_heart) - 5 * np.cos(2 * t_heart) - 2 * np.cos(3 * t_heart) - np.cos(4 * t_heart)) / 16.0 * 1.15
bdraw.polygon(list(zip(px, py)), fill=(231, 243, 208, 255))
badge_im = badge_im.resize((badge_w, badge_h), Image.Resampling.LANCZOS)
badge_rot = badge_im.rotate(-4.0, resample=Image.Resampling.BICUBIC, expand=True)

bounce_f = [499, 502, 504, 506, 508, 510, 512, 514, 516, 518, 520, 522, 524]
bounce_dy = [0, -8, -48, -78, -88, -90, -88, -80, -58, -40, -30, -28, -28]
text_bounce_interp = PchipInterpolator(bounce_f, bounce_dy)

badge_f = [499, 502, 505, 508, 510, 513, 516, 519, 522, 524]
badge_y_vals = [940, 890, 845, 825, 820, 824, 835, 844, 848, 848]
badge_bounce_interp = PchipInterpolator(badge_f, badge_y_vals)

def make_cursor_sprite(scale_factor=1.0):
    sz = int(64 * scale_factor)
    cim = Image.new("RGBA", (sz * 2, sz * 2), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(cim)
    pts = [(4, 4), (4, 44), (14, 34), (22, 50), (28, 47), (20, 31), (34, 31)]
    pts_scaled = [(x * 2 * scale_factor, y * 2 * scale_factor) for x, y in pts]
    cdraw.polygon(pts_scaled, fill=(255, 255, 255, 255), outline=(25, 25, 25, 255), width=max(2, int(3 * scale_factor)))
    return cim.resize((sz, sz), Image.Resampling.LANCZOS)

cursor_normal = make_cursor_sprite(1.0)
cursor_clicked = make_cursor_sprite(0.86)

f875_ref = np.array(Image.open(os.path.join(fdir, "f_0875.jpg")), dtype=np.float32)
partner_roi = f875_ref[620:682, 680:860, 1]
partner_alpha = np.clip((195.0 - partner_roi) / (195.0 - 40.0), 0.0, 1.0)
partner_h, partner_w = partner_alpha.shape
partner_rgba = np.zeros((partner_h, partner_w, 4), dtype=np.uint8)
partner_rgba[:, :, 0] = DARK_TEXT[0]
partner_rgba[:, :, 1] = DARK_TEXT[1]
partner_rgba[:, :, 2] = DARK_TEXT[2]
partner_rgba[:, :, 3] = (partner_alpha * 255).astype(np.uint8)
partner_pil = Image.fromarray(partner_rgba)

o1_arr = np.array(Image.open(os.path.join(data_dir, "Outro example.jpg")).resize((1080, 1446), Image.Resampling.LANCZOS), dtype=np.float32)
o2_arr = np.array(Image.open(os.path.join(data_dir, "Outro example 2.jpg")).resize((1080, 1446), Image.Resampling.LANCZOS), dtype=np.float32)

pills_roi = o1_arr[200:580, :, :]
pills_alpha = np.clip((pills_roi[:, :, 1] - 75.0) / (235.0 - 75.0), 0.0, 1.0)

lc_roi = o2_arr[1060:1425, :, :]
lc_alpha = np.clip((lc_roi[:, :, 1] - 75.0) / (235.0 - 75.0), 0.0, 1.0)
lc_h, lc_w = lc_alpha.shape
lc_rgba = np.zeros((lc_h, lc_w, 4), dtype=np.uint8)
lc_rgba[:, :, 0] = CREAM[0]
lc_rgba[:, :, 1] = CREAM[1]
lc_rgba[:, :, 2] = CREAM[2]
lc_rgba[:, :, 3] = (lc_alpha * 255).astype(np.uint8)
lc_pil = Image.fromarray(lc_rgba)

# Build 3rd pill (Gmail: syedamuskan902@gmail.com) below Behance
pill3_alpha = pills_alpha[25:178, :].copy()
pill3_alpha[25:128, 310:845] = 0.0
yy_p3, xx_p3 = np.ogrid[0:153, 0:1080]
inside_c3 = ((xx_p3 - 222) ** 2 + (yy_p3 - 76) ** 2) <= 54 ** 2
pill3_alpha[inside_c3] = 1.0

_scale_i = 4
_icon_im = Image.new("L", (140 * _scale_i, 140 * _scale_i), 0)
_idraw = ImageDraw.Draw(_icon_im)
_cxi, _cyi = 70 * _scale_i, 70 * _scale_i
_w_env, _h_env = 35 * _scale_i, 26 * _scale_i
_stroke = int(6.8 * _scale_i)
_idraw.rounded_rectangle([_cxi - _w_env, _cyi - _h_env, _cxi + _w_env, _cyi + _h_env], radius=int(8 * _scale_i), outline=255, width=_stroke)
_idraw.line([(_cxi - _w_env + 3 * _scale_i, _cyi - _h_env + 4 * _scale_i), (_cxi, _cyi + 5 * _scale_i), (_cxi + _w_env - 3 * _scale_i, _cyi - _h_env + 4 * _scale_i)], fill=255, width=_stroke, joint="curve")
_icon_small = np.array(_icon_im.resize((140, 140), Image.Resampling.LANCZOS), dtype=np.float32) / 255.0
pill3_alpha[6:146, 152:292] = np.clip(pill3_alpha[6:146, 152:292] - _icon_small, 0.0, 1.0)

_txt_im_l = Image.new("L", (1080, 153), 0)
_tdraw_l = ImageDraw.Draw(_txt_im_l)
_f_email_l = ImageFont.truetype(os.path.join(font_dir, "Poppins-Light.ttf"), 35)
_tdraw_l.text((355, 77), "syedamuskan902@gmail.com", fill=255, font=_f_email_l, anchor="lm")

_txt_im_r = Image.new("L", (1080, 153), 0)
_tdraw_r = ImageDraw.Draw(_txt_im_r)
_f_email_r = ImageFont.truetype(os.path.join(font_dir, "Poppins-Regular.ttf"), 35)
_tdraw_r.text((355, 77), "syedamuskan902@gmail.com", fill=255, font=_f_email_r, anchor="lm")

_txt_alpha = (0.65 * np.array(_txt_im_l, dtype=np.float32) + 0.35 * np.array(_txt_im_r, dtype=np.float32)) / 255.0
pill3_alpha = np.maximum(pill3_alpha, np.clip(_txt_alpha * 1.08, 0.0, 1.0))

outro_1080 = grid_1080.copy()
y_top = 270
yy, xx = np.ogrid[0:380, 0:1080]
circles_12 = (((xx - 222) ** 2 + (yy - 101) ** 2) <= 58 ** 2) | (((xx - 222) ** 2 + (yy - 280) ** 2) <= 58 ** 2)
circle_3 = ((xx_p3 - 222) ** 2 + (yy_p3 - 76) ** 2) <= 58 ** 2
y3_top = y_top + 383
for c_idx, val in enumerate([48.0, 51.0, 34.0]):
    region = outro_1080[y_top:y_top+380, :, c_idx]
    region[circles_12] = val
    outro_1080[y_top:y_top+380, :, c_idx] = region * (1.0 - pills_alpha) + CREAM_ARR[c_idx] * pills_alpha

    reg3 = outro_1080[y3_top:y3_top+153, :, c_idx]
    reg3[circle_3] = val
    outro_1080[y3_top:y3_top+153, :, c_idx] = reg3 * (1.0 - pill3_alpha) + CREAM_ARR[c_idx] * pill3_alpha

    outro_1080[975:1340, :, c_idx] = outro_1080[975:1340, :, c_idx] * (1.0 - lc_alpha) + CREAM_ARR[c_idx] * lc_alpha
outro_1080_pil = Image.fromarray(outro_1080.astype(np.uint8))

x_edges = [0, 48, 102, 157, 211, 266, 321, 375, 430, 485, 540, 592, 647, 701, 756, 811, 865, 920, 975, 1029, 1080]
y_edges = [0, 62, 124, 186, 248, 309, 371, 432, 494, 553, 613, 673, 734, 794, 855, 915, 976, 1036, 1097, 1157, 1217, 1278, 1338, 1350]

print(f"Assets ready in {time.time() - t0:.2f}s")


def render_scene1_frame(fn):
    if fn <= 159:
        canvas = grid_1080.copy()
        ref_im = np.array(Image.open(os.path.join(fdir, f"f_{fn:04d}.jpg")), dtype=np.float32)
        h_alpha = np.clip((ref_im[:, :, 1] - 42.0) / (240.0 - 42.0), 0.0, 1.0)
        for c in range(3):
            canvas[:, :, c] = canvas[:, :, c] * (1.0 - h_alpha) + CREAM_ARR[c] * h_alpha
        return Image.fromarray(canvas.astype(np.uint8))
    elif fn <= 186:
        canvas = grid_1080.copy()
        h_alpha = np.zeros((450, W), dtype=np.float32)
        h_alpha[:405, :] = helloo_with_smile_alpha[:405, :]
        ref_im = np.array(Image.open(os.path.join(fdir, f"f_{fn:04d}.jpg")), dtype=np.float32)
        s_roi = np.clip((ref_im[402:445, 818:910, 1] - 42.0) / (240.0 - 42.0), 0.0, 1.0)
        h_alpha[402:445, 818:910] = np.maximum(h_alpha[402:445, 818:910], s_roi)
        for c in range(3):
            canvas[:450, :, c] = canvas[:450, :, c] * (1.0 - h_alpha) + CREAM_ARR[c] * h_alpha
        frame_pil = Image.fromarray(canvas.astype(np.uint8))
    else:
        frame_pil = base_helloo_smile_pil.copy()

    if fn >= 204:
        if fn >= 220:
            tdraw = ImageDraw.Draw(frame_pil)
            tdraw.text((71, 418), "I am Muskan Syed", fill=CREAM, font=f_left)
        else:
            txt_layer = Image.new("RGBA", (400, 90), (0, 0, 0, 0))
            tdraw = ImageDraw.Draw(txt_layer)
            p1 = ease_out_cubic((fn - 204) / 4.0)
            tdraw.text((0, int(20 * p1)), "I ", fill=(231, 243, 208, int(255 * p1)), font=f_left)
            w1 = tdraw.textlength("I ", font=f_left)
            if fn >= 209:
                p2 = ease_out_cubic((fn - 209) / 4.0)
                tdraw.text((w1, int(20 * p2)), "am ", fill=(231, 243, 208, int(255 * p2)), font=f_left)
            w2 = tdraw.textlength("I am ", font=f_left)
            if fn >= 214:
                p3 = ease_out_cubic((fn - 214) / 6.0)
                tdraw.text((w2, int(20 * p3)), "Muskan Syed", fill=(231, 243, 208, int(255 * p3)), font=f_left)
            txt_cropped = txt_layer.crop((0, 14, 400, 90))
            frame_pil.paste(txt_cropped, (71, 412), txt_cropped)

    if fn >= 270:
        r_layer = Image.new("RGBA", (360, 420), (0, 0, 0, 0))
        rdraw = ImageDraw.Draw(r_layer)
        # Local coordinates inside r_layer pasted at (700, 620)
        dy_bounce = float(text_bounce_interp(min(fn, 524))) if fn >= 499 else 0.0

        # Line 1: Bold "Your" slides in at F270..286 at y=770, then moves up to y=718 when line 2 starts (F330..345)
        p_your = ease_out_cubic((fn - 270) / 16.0)
        x_your = int((830 - 700) + (1038 - 830) * p_your)
        a_your = int(255 * np.clip((fn - 270) / 7.0, 0.0, 1.0))
        p_up = ease_in_out_cubic((fn - 330) / 15.0) if fn >= 330 else 0.0
        y_your = int((770 - 620) - 52 * p_up + dy_bounce)
        rdraw.text((x_your, y_your), "Your", fill=(231, 243, 208, a_your), font=f_right_bold, anchor="ra")

        # Line 2: Caret appears at F335, then types "Sr UI/UX" across F354..465
        y_line2 = int((770 - 620) + dy_bounce)
        if 335 <= fn < 354:
            rdraw.text((1038 - 700, y_line2), "|", fill=(231, 243, 208, 255), font=f_right_reg, anchor="ra")
        elif fn >= 354:
            if fn < 364: role_str = "S|"
            elif fn < 374: role_str = "Sr|"
            elif fn < 384: role_str = "Sr |"
            elif fn < 395: role_str = "Sr U|"
            elif fn < 406: role_str = "Sr UI|"
            elif fn < 417: role_str = "Sr UI/|"
            elif fn < 428: role_str = "Sr UI/U|"
            elif fn < 432: role_str = "Sr UI/UX|"
            elif fn < 435: role_str = "Sr UI/UX"
            elif fn < 465: role_str = "Sr UI/UX|"
            else: role_str = "Sr UI/UX"
            rdraw.text((1038 - 700, y_line2), role_str, fill=(231, 243, 208, 255), font=f_right_reg, anchor="ra")

        if fn >= 466:
            p_des = ease_out_cubic((fn - 466) / 14.0)
            y_des = int((782 - 620) + (820 - 782) * p_des + dy_bounce)
            a_des = int(255 * np.clip((fn - 466) / 6.0, 0.0, 1.0))
            rdraw.text((1038 - 700, y_des), "Designer", fill=(231, 243, 208, a_des), font=f_right_bold, anchor="ra")

        if fn >= 499:
            by_pos = int(badge_bounce_interp(min(fn, 524))) - 620
            bx_pos = (1046 - 700) - badge_rot.width
            r_layer.paste(badge_rot, (bx_pos, by_pos), badge_rot)

        frame_pil.paste(r_layer, (700, 620), r_layer)

    cy_off = int(char_popup_interp(min(fn, 187))) if fn < 187 else 0
    frame_pil.paste(char_pil, (CHAR_X, CHAR_Y + cy_off), char_pil)

    if 307 <= fn <= 334:
        p_cur = ease_out_cubic((fn - 307) / 8.0)
        cx_cur = int(1085 + (1032 - 1085) * p_cur)
        cy_cur = int(855 + (795 - 855) * p_cur)
        cur_im = cursor_clicked if (324 <= fn <= 330) else cursor_normal
        frame_pil.paste(cur_im, (cx_cur, cy_cur), cur_im)

    return frame_pil


scene1_f547_pil = render_scene1_frame(547)


def render_zoom_frame(fn):
    t = (fn - 546) / 28.0
    scale = 1.0 * (45.0 ** (ease_in_out_cubic(t) ** 0.95))
    t_focus = ease_in_out_cubic(np.clip((fn - 546) / 14.0, 0.0, 1.0))
    fx = 445.0
    # Zoom into the olive hijab (y=360) and blend smoothly into plain_1080
    fy = 400.0 * (1.0 - t_focus) + 360.0 * t_focus

    crop_w = W / scale
    crop_h = H / scale
    x0 = np.clip(fx - crop_w * 0.48, 0.0, W - crop_w)
    y0 = np.clip(fy - crop_h * 0.35, 0.0, H - crop_h)

    cropped = scene1_f547_pil.crop((int(x0), int(y0), max(int(x0) + 1, int(x0 + crop_w)), max(int(y0) + 1, int(y0 + crop_h))))
    zoomed_pil = cropped.resize((W, H), Image.Resampling.BILINEAR)

    if fn >= 556:
        blend_p = ease_in_out_cubic((fn - 556) / 18.0)
        z_arr = np.array(zoomed_pil, dtype=np.float32)
        blended = z_arr * (1.0 - blend_p) + plain_1080 * blend_p
        return Image.fromarray(blended.astype(np.uint8))
    return zoomed_pil


BAR_ROLES = [
    ("Creative", 0, 0),
    ("Brand", 619, 640),
    ("UI/UX", 651, 673),
    ("Web Graphics", 679, 703),
    ("Social Media", 706, 729),
    ("Creative Ads", 736, 758),
    ("Book Cover", 770, 786),
    ("One", 799, 822),
]

_dummy_draw = ImageDraw.Draw(Image.new("RGB", (10, 10)))
W_YOUR = _dummy_draw.textlength("Your ", font=f_bar_bold)
W_DESIGNER = _dummy_draw.textlength(" Designer", font=f_bar_bold)
ROLE_WIDTHS = {r[0]: _dummy_draw.textlength(r[0], font=f_bar_reg) for r in BAR_ROLES}


def render_scene2_frame(fn):
    if fn <= 581:
        return plain_1080_pil

    if fn <= 605:
        p_bar = ease_in_out_cubic((fn - 582) / 23.0)
        bg_arr = plain_1080 * (1.0 - p_bar) + bar_1080 * p_bar
        frame_pil = Image.fromarray(bg_arr.astype(np.uint8))
        if fn >= 584:
            p_txt = ease_in_out_cubic((fn - 584) / 21.0)
            txt_layer = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
            tdraw = ImageDraw.Draw(txt_layer)
            w_mid = ROLE_WIDTHS["Creative"]
            tot_w = W_YOUR + w_mid + W_DESIGNER
            sx = (W - tot_w) / 2.0
            a_main = int(255 * p_txt)
            a_mid = int(255 * (p_txt ** 1.4))
            tdraw.text((sx, 56), "Your ", fill=(*DARK_TEXT, a_main), font=f_bar_bold, anchor="lm")
            tdraw.text((sx + W_YOUR, 56), "Creative", fill=(*CREAM, a_mid), font=f_bar_reg, anchor="lm")
            tdraw.text((sx + W_YOUR + w_mid, 56), " Designer", fill=(*DARK_TEXT, a_main), font=f_bar_bold, anchor="lm")
            frame_pil.paste(txt_layer, (0, 590), txt_layer)
        return frame_pil

    frame_pil = bar_1080_pil.copy()
    cy = 646

    if fn <= 836:
        curr_idx = 0
        in_trans = False
        trans_p = 0.0
        for idx in range(1, len(BAR_ROLES)):
            _, f_start, f_end = BAR_ROLES[idx]
            if fn >= f_end:
                curr_idx = idx
            elif f_start <= fn < f_end:
                curr_idx = idx - 1
                in_trans = True
                trans_p = ease_in_out_cubic((fn - f_start) / float(f_end - f_start))
                break

        tdraw = ImageDraw.Draw(frame_pil)
        if not in_trans:
            role_name = BAR_ROLES[curr_idx][0]
            w_mid = ROLE_WIDTHS[role_name]
            tot_w = W_YOUR + w_mid + W_DESIGNER
            sx = (W - tot_w) / 2.0
            tdraw.text((sx, cy), "Your ", fill=DARK_TEXT, font=f_bar_bold, anchor="lm")
            tdraw.text((sx + W_YOUR, cy), role_name, fill=CREAM, font=f_bar_reg, anchor="lm")
            tdraw.text((sx + W_YOUR + w_mid, cy), " Designer", fill=DARK_TEXT, font=f_bar_bold, anchor="lm")
        else:
            r_old = BAR_ROLES[curr_idx][0]
            r_new = BAR_ROLES[curr_idx + 1][0]
            w_old = ROLE_WIDTHS[r_old]
            w_new = ROLE_WIDTHS[r_new]
            w_mid = w_old * (1.0 - trans_p) + w_new * trans_p
            tot_w = W_YOUR + w_mid + W_DESIGNER
            sx = (W - tot_w) / 2.0
            tdraw.text((sx, cy), "Your ", fill=DARK_TEXT, font=f_bar_bold, anchor="lm")
            tdraw.text((sx + W_YOUR + w_mid, cy), " Designer", fill=DARK_TEXT, font=f_bar_bold, anchor="lm")

            slot_layer = Image.new("RGBA", (W, 96), (0, 0, 0, 0))
            sdraw = ImageDraw.Draw(slot_layer)
            y_old = 48 - int(66 * trans_p)
            a_old = int(255 * (1.0 - trans_p))
            y_new = 48 + int(66 * (1.0 - trans_p))
            a_new = int(255 * trans_p)
            mid_cx = sx + W_YOUR + w_mid / 2.0
            sdraw.text((mid_cx, y_old), r_old, fill=(*CREAM, a_old), font=f_bar_reg, anchor="mm")
            sdraw.text((mid_cx, y_new), r_new, fill=(*CREAM, a_new), font=f_bar_reg, anchor="mm")
            frame_pil.paste(slot_layer, (0, 598), slot_layer)
        return frame_pil

    if fn <= 887:
        tdraw = ImageDraw.Draw(frame_pil)
        w_one = ROLE_WIDTHS["One"]
        tot_init = W_YOUR + w_one + W_DESIGNER
        sx_init = (W - tot_init) / 2.0
        p_shift = ease_in_out_cubic(np.clip((fn - 840) / 18.0, 0.0, 1.0))
        p_settle = ease_in_out_cubic(np.clip((fn - 858) / 18.0, 0.0, 1.0))

        x_your = sx_init * (1.0 - p_shift) + (215.0 * (1.0 - p_settle) + 258.0 * p_settle) * p_shift
        x_one = (sx_init + W_YOUR) * (1.0 - p_shift) + (315.0 * (1.0 - p_settle) + 372.0 * p_settle) * p_shift
        x_des = (sx_init + W_YOUR + w_one) * (1.0 - p_shift) + (415.0 * (1.0 - p_settle) + 466.0 * p_settle) * p_shift

        des_word = "Designer" if fn < 846 else " Design"
        tdraw.text((x_your, cy), "Your ", fill=DARK_TEXT, font=f_bar_bold, anchor="lm")
        tdraw.text((x_one, cy), "One", fill=CREAM, font=f_bar_reg, anchor="lm")
        tdraw.text((x_des, cy), des_word, fill=DARK_TEXT, font=f_bar_bold, anchor="lm")

        if fn >= 840:
            p_part = ease_out_cubic(np.clip((fn - 840) / 15.0, 0.0, 1.0))
            x_part = int(985 * (1.0 - p_part) + (705 * (1.0 - p_settle) + 648 * p_settle) * p_part)
            if x_part < 995:
                part_layer = Image.new("RGBA", (895, 115), (0, 0, 0, 0))
                part_layer.paste(partner_pil, (x_part - 100, 30), partner_pil)
                frame_pil.paste(part_layer, (100, 590), part_layer)
        return frame_pil

    p_up = ease_in_out_cubic(np.clip((fn - 888) / 25.0, 0.0, 1.0))
    cy_top = int(646 * (1.0 - p_up) + 542 * p_up)
    y_part_top = int(620 * (1.0 - p_up) + 516 * p_up)

    tdraw = ImageDraw.Draw(frame_pil)
    tdraw.text((258, cy_top), "Your ", fill=DARK_TEXT, font=f_bar_bold, anchor="lm")
    tdraw.text((372, cy_top), "One", fill=CREAM, font=f_bar_reg, anchor="lm")
    tdraw.text((466, cy_top), " Design", fill=DARK_TEXT, font=f_bar_bold, anchor="lm")
    frame_pil.paste(partner_pil, (648, y_part_top), partner_pil)

    if fn >= 890:
        p_lc = ease_in_out_cubic(np.clip((fn - 890) / 23.0, 0.0, 1.0))
        a_lc = int(255 * p_lc)
        cy_lc = int(76 * (1.0 - p_lc) + 56 * p_lc)
        lc_bar_layer = Image.new("RGBA", (W, 120), (0, 0, 0, 0))
        ldraw = ImageDraw.Draw(lc_bar_layer)
        w_lets = ldraw.textlength("Let's ", font=f_bar_reg)
        w_conn = ldraw.textlength("Connect", font=f_bar_bold)
        sx_lc = (W - (w_lets + w_conn)) / 2.0
        ldraw.text((sx_lc, cy_lc), "Let's ", fill=(*CREAM, a_lc), font=f_bar_reg, anchor="lm")
        ldraw.text((sx_lc + w_lets, cy_lc), "Connect", fill=(*CREAM, a_lc), font=f_bar_bold, anchor="lm")
        frame_pil.paste(lc_bar_layer, (0, 590), lc_bar_layer)

    if 953 <= fn <= 970:
        if fn <= 958:
            p_c = ease_out_cubic((fn - 953) / 5.0)
            cx_c = int(780 + (648 - 780) * p_c)
            cy_c = int(760 + (660 - 760) * p_c)
        elif fn <= 960:
            cx_c, cy_c = 648, 660
        else:
            p_c = ease_in_out_cubic((fn - 960) / 10.0)
            cx_c = int(648 + (1090 - 648) * p_c)
            cy_c = int(660 + (795 - 660) * p_c)
        cur_im = cursor_clicked if (958 <= fn <= 960) else cursor_normal
        frame_pil.paste(cur_im, (cx_c, cy_c), cur_im)

    if fn >= 964:
        p_rise = ease_out_cubic(np.clip((fn - 964) / 30.0, 0.0, 1.0))
        y_lc_bot = int(1350 * (1.0 - p_rise) + 975 * p_rise)
        frame_pil.paste(lc_pil, (0, y_lc_bot), lc_pil)

    return frame_pil


scene2_f995_pil = render_scene2_frame(995)
scene2_f995_arr = np.array(scene2_f995_pil, dtype=np.float32)


def render_mosaic_frame(fn):
    prog = (fn - 995) / 19.0
    out = scene2_f995_arr.copy()
    cx0, cy0 = 540.0, 580.0
    max_dist = 820.0
    wave_r = prog * (max_dist + 260.0)

    for r in range(len(y_edges) - 1):
        y0, y1 = y_edges[r], y_edges[r + 1]
        cy = 0.5 * (y0 + y1)
        for c in range(len(x_edges) - 1):
            x0, x1 = x_edges[c], x_edges[c + 1]
            cx = 0.5 * (x0 + x1)
            dx = abs(cx - cx0)
            dy = abs(cy - cy0)
            dist = 0.75 * np.hypot(dx, dy) + 0.25 * (dx + dy)
            cell_p = float(np.clip((wave_r - dist) / 240.0, 0.0, 1.0))
            if cell_p > 0.0:
                alpha_cell = cell_p * cell_p * (3.0 - 2.0 * cell_p)
                cell_s2 = scene2_f995_arr[y0:y1, x0:x1]
                cell_s3 = outro_1080[y0:y1, x0:x1]
                blended = cell_s2 * (1.0 - alpha_cell) + cell_s3 * alpha_cell
                border_strength = np.sin(cell_p * np.pi) * 0.65
                if border_strength > 0.05:
                    dark_grid = np.array([35.0, 36.0, 22.0], dtype=np.float32)
                    blended[0:2, :, :] = blended[0:2, :, :] * (1.0 - border_strength) + dark_grid * border_strength
                    blended[:, 0:2, :] = blended[:, 0:2, :] * (1.0 - border_strength) + dark_grid * border_strength
                out[y0:y1, x0:x1] = blended

    for ch_idx in range(3):
        out[975:1340, :, ch_idx] = out[975:1340, :, ch_idx] * (1.0 - lc_alpha) + CREAM_ARR[ch_idx] * lc_alpha
    return Image.fromarray(out.astype(np.uint8))


# Static frame ranges where frame[fn] == frame[fn-1] so we can reuse raw bytes in 0.0ms!
STATIC_RANGES = [
    (12, 16), (21, 24), (29, 36), (46, 61), (72, 86), (94, 102), (136, 157),
    (189, 203), (221, 269), (287, 306), (346, 353),
    (355, 363), (365, 373), (375, 383), (385, 394), (396, 405), (407, 416), (418, 427),
    (429, 431), (433, 434), (436, 464), (481, 498), (525, 545),
    (575, 581), (606, 618), (641, 650), (674, 678), (704, 705), (730, 735),
    (759, 769), (787, 798), (823, 839), (877, 887), (915, 952), (1015, 1080)
]

def is_same_as_prev(fn):
    for a, b in STATIC_RANGES:
        if a <= fn <= b:
            return True
    return False

def render_frame(fn):
    if fn <= 547:
        return render_scene1_frame(fn)
    elif fn <= 574:
        return render_zoom_frame(fn)
    elif fn <= 995:
        return render_scene2_frame(fn)
    elif fn <= 1014:
        return render_mosaic_frame(fn)
    else:
        return outro_1080_pil

print("2. Encoding with FFmpeg (no stderr pipe deadlock, fast preset + static frame caching)...")
cmd = [
    "ffmpeg",
    "-y",
    "-loglevel", "error",
    "-f", "rawvideo",
    "-vcodec", "rawvideo",
    "-s", f"{W}x{H}",
    "-pix_fmt", "rgb24",
    "-r", "30",
    "-i", "-",
    "-i", ref_video_path,
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-c:v", "libx264",
    "-preset", "veryfast",
    "-crf", "16",
    "-pix_fmt", "yuv420p",
    "-c:a", "copy",
    "-shortest",
    out_video_path,
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
prev_bytes = None
rendered_count = 0

for fn in range(1, 1081):
    if prev_bytes is not None and is_same_as_prev(fn):
        proc.stdin.write(prev_bytes)
    else:
        im = render_frame(fn)
        prev_bytes = im.tobytes()
        proc.stdin.write(prev_bytes)
        rendered_count += 1
    if fn % 270 == 0 or fn == 1080:
        print(f"  Frame {fn}/1080 ({rendered_count} unique frames rendered, {time.time() - t0:.1f}s elapsed)")

proc.stdin.close()
proc.wait()

# Also copy to Final Video.mp4
import shutil
try:
    shutil.copyfile(out_video_path, out_video_path2)
except Exception as e:
    print("Note copying to Final Video.mp4:", e)

print(f"Done in {time.time() - t0:.2f}s! Output saved to {out_video_path}")
