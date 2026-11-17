import os
import subprocess
import numpy as np
import cv2

SCRATCH_DIR = r"C:\Users\WayWe Work-Station\.gemini\antigravity\brain\8ad88795-d9fa-438b-8430-13b89b7ef998\scratch\japan_job_project"
OUT_DIR = r"C:\Users\WayWe Work-Station\Downloads\Mate\Job Culture of japan"
SRC_VID = os.path.join(OUT_DIR, "Jap vid.mp4")

FPS = 30
W, H = 1080, 1920
DURATION_OUT = 64.6008
TOTAL_OUT_FRAMES = int(round(DURATION_OUT * FPS))  # 1938 frames

# 23 exact story-beat anchor points: (t_ref in 60.50s Jap vid.mp4, t_user in 64.6008s Audio.MP3)
TIME_MAP = [
    (0.00, 0.00),      # "It's impossible to get fired in Japan."
    (2.35, 2.45),      # "But companies found something way worse."
    (3.95, 4.10),      # "Imagine your boss walks you past your desk..."
    (6.80, 6.95),      # "...to a tiny room..." (CAREER DEVELOPMENT ROOM door opens)
    (8.15, 8.15),      # "...with no computer and no work." (Empty desk with yellow tape outlines)
    (9.85, 9.65),      # "Just a ticking clock..." (Red-rimmed wall clock)
    (11.80, 11.75),    # "...and a guy with his feet up, scrolling on his phone like he's on vacation."
    (14.20, 14.80),    # "Your new job, your boss says, is nothing." (Empty red gift box)
    (16.35, 17.55),    # "Just sit here until six."
    (18.10, 19.10),    # "And you're thinking, wait, I'm getting paid for this?" (+$4,500 notification)
    (20.30, 21.80),    # "At first, it's paradise." (Sunbathing on floor in sunglasses)
    (21.65, 23.55),    # "Then, your coworkers start staring when you walk past."
    (24.10, 25.95),    # "The emails stop..." (Inbox (0) with cobwebbed mailbox)
    (25.95, 26.95),    # "...and your old desk already has someone else's family photos on it."
    (28.10, 29.95),    # "Every Friday, your boss pops his head in..." (NOV FRI 25 calendar & Boss peeking)
    (32.25, 35.45),    # "Still, the guy in the corner has been doing this for three years..."
    (35.85, 38.20),    # "...and looks happier than anyone in the building." (Exterior night skyscraper grid)
    (39.45, 42.25),    # "So if they want to pay you to do nothing, fine. You kick your feet up right next to him."
    (42.40, 45.65),    # "Then one Monday, you walk in, and he's gone..." (APR MON 28 & empty desk with coffee stains)
    (48.85, 52.20),    # "You see, Japanese law makes it almost impossible to fire someone..." (Padlocked LABOR LAW alarm)
    (52.25, 56.00),    # "...but there's no law against making them miserable. So they take away your work and your friends..."
    (58.15, 61.55),    # "...because nobody can do nothing forever." (Door window push-in on Ken alone)
    (60.50, 64.6008),
]

REF_TIMES = np.array([p[0] for p in TIME_MAP], dtype=np.float64)
USER_TIMES = np.array([p[1] for p in TIME_MAP], dtype=np.float64)


def map_user_to_ref_time(t_user):
    return np.interp(t_user, USER_TIMES, REF_TIMES)


Y1, Y2, X1, X2 = 1285, 1422, 150, 930


def get_caption_mask(bgr_roi):
    b = bgr_roi[:, :, 0].astype(np.int16)
    g = bgr_roi[:, :, 1].astype(np.int16)
    r = bgr_roi[:, :, 2].astype(np.int16)
    max_c = np.maximum(np.maximum(b, g), r)
    min_c = np.minimum(np.minimum(b, g), r)
    white_core = ((min_c > 200) & ((max_c - min_c) < 32)).astype(np.uint8) * 255

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(white_core)
    clean_core = np.zeros_like(white_core)
    for idx in range(1, num_labels):
        x0, y0, w0, h0, area = stats[idx]
        cx, cy = centroids[idx]
        if 10 <= area <= 24000 and 10 <= h0 <= 92 and 8 <= cy <= 108:
            comp = (labels == idx).astype(np.uint8)
            dil = cv2.dilate(comp, np.ones((9, 9), np.uint8))
            ring = (dil > 0) & (comp == 0)
            if np.any(ring):
                ring_luma = 0.299 * r[ring] + 0.587 * g[ring] + 0.114 * b[ring]
                if np.percentile(ring_luma, 35) < 88:
                    clean_core[comp > 0] = 255

    if np.count_nonzero(clean_core) == 0:
        return np.zeros_like(white_core)

    k_stroke = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (33, 33))
    mask = cv2.dilate(clean_core, k_stroke, iterations=1)
    luma = 0.299 * r + 0.587 * g + 0.114 * b
    k_shadow = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (43, 43))
    near_text = cv2.dilate(clean_core, k_shadow, iterations=1) > 0
    dark_shadow = near_text & (luma < 48)
    mask[dark_shadow] = 255
    mask = cv2.dilate(mask, np.ones((5, 5), np.uint8), iterations=1)
    return mask


def clean_all_source_frames():
    print("Loading 1815 source frames from Jap vid.mp4...")
    cap = cv2.VideoCapture(SRC_VID)
    frames = []
    while True:
        ret, f = cap.read()
        if not ret:
            break
        frames.append(f)
    cap.release()
    n_src = len(frames)
    print(f"Loaded {n_src} source frames. Detecting & cleaning caption masks...")

    masks = [get_caption_mask(f[Y1:Y2, X1:X2]) for f in frames]
    cleaned_rois = []

    for idx in range(n_src):
        roi = frames[idx][Y1:Y2, X1:X2].copy()
        m = masks[idx]
        if np.count_nonzero(m) > 0:
            ref_band = frames[idx][Y1 - 36 : Y2 + 36, X1:X2]
            ref_gray = cv2.cvtColor(ref_band, cv2.COLOR_BGR2GRAY).astype(np.float32)
            acc = np.zeros_like(roi, dtype=np.float32)
            w_sum = np.zeros(roi.shape[:2], dtype=np.float32)

            for d in (-16, -12, -9, -6, -4, 4, 6, 9, 12, 16):
                j = idx + d
                if j < 0 or j >= n_src:
                    continue
                diff = np.mean(
                    np.abs(
                        frames[idx][Y1 - 36 : Y1, X1:X2].astype(np.float32)
                        - frames[j][Y1 - 36 : Y1, X1:X2].astype(np.float32)
                    )
                )
                if diff > 26.0:
                    continue
                cand_band = frames[j][Y1 - 36 : Y2 + 36, X1:X2]
                cand_gray = cv2.cvtColor(cand_band, cv2.COLOR_BGR2GRAY).astype(np.float32)
                (dx, dy), _ = cv2.phaseCorrelate(ref_gray, cand_gray)
                if abs(dx) > 45 or abs(dy) > 35:
                    continue
                M = np.float32([[1, 0, -dx], [0, 1, -dy]])
                warped_roi = cv2.warpAffine(
                    frames[j][Y1:Y2, X1:X2], M, (X2 - X1, Y2 - Y1), borderMode=cv2.BORDER_REPLICATE
                )
                warped_m = cv2.warpAffine(masks[j], M, (X2 - X1, Y2 - Y1), borderValue=255)
                valid = (warped_m == 0).astype(np.float32) * np.exp(-abs(d) * 0.10)
                acc += warped_roi.astype(np.float32) * valid[:, :, None]
                w_sum += valid

            recovered = roi.copy()
            have_temp = (m > 0) & (w_sum > 0.05)
            recovered[have_temp] = (acc[have_temp] / w_sum[have_temp, None]).astype(np.float32).astype(np.uint8)
            still_masked = ((m > 0) & (~have_temp)).astype(np.uint8) * 255
            if np.count_nonzero(still_masked) > 0:
                recovered = cv2.inpaint(recovered, still_masked, 5, cv2.INPAINT_NS)

            alpha = cv2.GaussianBlur(m.astype(np.float32) / 255.0, (9, 9), 2.0)[:, :, None]
            roi = (recovered.astype(np.float32) * alpha + roi.astype(np.float32) * (1.0 - alpha)).astype(np.uint8)

        cleaned_rois.append(roi)
        if (idx + 1) % 400 == 0:
            print(f"Cleaned captions on {idx + 1} / {n_src} source frames...", flush=True)

    for idx in range(n_src):
        frames[idx][Y1:Y2, X1:X2] = cleaned_rois[idx]

    return frames


def render_synced_video(frames):
    n_src = len(frames)
    out_mp4 = os.path.join(SCRATCH_DIR, "japan_video_muted.mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "bgr24",
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
        "17",
        "-pix_fmt",
        "yuv420p",
        out_mp4,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for f_out in range(TOTAL_OUT_FRAMES):
        t_user = f_out / FPS
        t_ref = map_user_to_ref_time(t_user)
        f_src_float = np.clip(t_ref * FPS, 0.0, n_src - 1.001)
        i0 = int(f_src_float)
        i1 = min(n_src - 1, i0 + 1)
        frac = f_src_float - i0

        diff = np.mean(np.abs(frames[i0][::8, ::8].astype(np.int16) - frames[i1][::8, ::8].astype(np.int16)))
        if diff < 18.0 and 0.15 < frac < 0.85:
            frame_out = cv2.addWeighted(frames[i0], 1.0 - frac, frames[i1], frac, 0.0)
        else:
            frame_out = frames[i0 if frac < 0.5 else i1]

        proc.stdin.write(frame_out.tobytes())
        if (f_out + 1) % 400 == 0:
            print(f"Wrote {f_out + 1} / {TOTAL_OUT_FRAMES} synced output frames...", flush=True)

    proc.stdin.close()
    proc.wait()
    print(f"Finished rendering {out_mp4} ({TOTAL_OUT_FRAMES} frames)!")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            out_mp4,
            "-vf",
            "fps=1,scale=270:480,tile=6x4",
            "-q:v",
            "3",
            os.path.join(SCRATCH_DIR, "japan_from_scratch_sheet_%02d.jpg"),
        ],
        check=True,
    )
    print("Generated clean preview contact sheets japan_from_scratch_sheet_01..03.jpg!")


if __name__ == "__main__":
    clean_frames = clean_all_source_frames()
    render_synced_video(clean_frames)
