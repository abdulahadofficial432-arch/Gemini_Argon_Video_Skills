import os
import sys
import time
import math
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
import cairo

from engine.primitives import WIDTH, HEIGHT, FPS
from engine.timeline import render_frame

WORKSPACE_DIR = r"c:\Users\WayWe Work-Station\Downloads\Die"
SOURCE_VIDEO = os.path.join(
    WORKSPACE_DIR,
    "Zombie Outbreak Starts In 6 Days And Only YOU Know (Animated)",
    "Exact Video.mp4"
)
OUT_VIDEO_ROOT = os.path.join(WORKSPACE_DIR, "Recreated_Exact_Video.mp4")
OUT_VIDEO_SUBDIR = os.path.join(
    WORKSPACE_DIR,
    "Zombie Outbreak Starts In 6 Days And Only YOU Know (Animated)",
    "Recreated_Exact_Video.mp4"
)
ARTIFACT_DIR = r"C:\Users\WayWe Work-Station\.gemini\antigravity\brain\3a936ec6-f35a-41e5-b46a-76bb7ce5f9ff"
SCRATCH_DIR = os.path.join(ARTIFACT_DIR, "scratch")

TOTAL_DURATION = 590.866667
TOTAL_FRAMES = 17726  # Exact frame count of Exact Video.mp4 (590.866667s @ 30fps)


def render_segment_worker(args):
    """
    Renders a contiguous range of frames [start_frame, end_frame) in a worker process
    and pipes raw BGRA frames directly into FFmpeg.
    """
    seg_idx, start_frame, end_frame, seg_path, use_nvenc = args
    t0 = time.time()

    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surf)

    vcodec = (
        ["-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20", "-b:v", "4500k"]
        if use_nvenc else
        ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]
    )

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-pix_fmt", "bgra",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS),
        "-i", "-",
        *vcodec,
        "-pix_fmt", "yuv420p",
        seg_path
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    buf = surf.get_data()

    try:
        for f_idx in range(start_frame, end_frame):
            t = f_idx / float(FPS)
            render_frame(ctx, t)
            surf.flush()
            proc.stdin.write(buf)
    finally:
        proc.stdin.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"FFmpeg worker {seg_idx} exited with code {ret}")

    elapsed = time.time() - t0
    n_frames = end_frame - start_frame
    return seg_idx, n_frames, elapsed


def export_sample_keyframes():
    """Exports 1080p PNG keyframes at the exact timestamps inspected from Exact Video.mp4."""
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    os.makedirs(SCRATCH_DIR, exist_ok=True)

    sample_times = [
        2, 4, 18, 42, 54, 60, 77, 95, 115, 125,
        142, 150, 162, 168, 185, 210, 222, 238,
        245, 270, 285, 300, 315, 325, 348, 355,
        395, 405, 415, 440, 460, 475, 503, 520,
        535, 555, 575, 584, 588
    ]
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, WIDTH, HEIGHT)
    ctx = cairo.Context(surf)

    for ts in sample_times:
        render_frame(ctx, float(ts))
        surf.flush()
        out_png = os.path.join(ARTIFACT_DIR, f"recreated_frame_{ts}.png")
        surf.write_to_png(out_png)
        # Also copy corresponding original reference frame into ARTIFACT_DIR for side-by-side comparison
        orig_jpg = os.path.join(SCRATCH_DIR, f"frame_{ts}.jpg")
        if os.path.exists(orig_jpg):
            shutil.copyfile(orig_jpg, os.path.join(ARTIFACT_DIR, f"orig_frame_{ts}.jpg"))

    print(f"[Keyframes] Exported {len(sample_times)} 1080p PNG keyframes to {ARTIFACT_DIR}")


def main():
    os.makedirs(SCRATCH_DIR, exist_ok=True)
    export_sample_keyframes()

    # Use 6 parallel workers: first 3 on NVENC hardware encoder, 3 on fast multi-core libx264
    num_workers = 6
    frames_per_seg = math.ceil(TOTAL_FRAMES / float(num_workers))
    tasks = []
    seg_paths = []

    for i in range(num_workers):
        sf = i * frames_per_seg
        ef = min(TOTAL_FRAMES, (i + 1) * frames_per_seg)
        if sf >= ef:
            break
        seg_path = os.path.join(SCRATCH_DIR, f"recreated_seg_{i:02d}.mp4")
        seg_paths.append(seg_path)
        use_nvenc = (i < 3)  # GTX 1660 SUPER supports up to 3 concurrent NVENC sessions
        tasks.append((i, sf, ef, seg_path, use_nvenc))

    print(f"[Render] Launching {len(tasks)} parallel workers to render {TOTAL_FRAMES} frames (1920x1080 @ 30fps)...")
    t_start = time.time()

    with ProcessPoolExecutor(max_workers=num_workers) as ex:
        futures = [ex.submit(render_segment_worker, task) for task in tasks]
        for fut in as_completed(futures):
            seg_idx, n_f, el = fut.result()
            print(f"  -> Segment {seg_idx:02d} finished: {n_f} frames in {el:.1f}s ({n_f/el:.1f} FPS)")

    t_render = time.time() - t_start
    print(f"[Render] All {TOTAL_FRAMES} frames rendered in {t_render:.1f}s ({TOTAL_FRAMES/t_render:.1f} effective FPS)!")

    # Write FFmpeg concat list
    concat_list_path = os.path.join(SCRATCH_DIR, "recreated_concat.txt")
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for sp in seg_paths:
            sp_escaped = sp.replace("\\", "/")
            f.write(f"file '{sp_escaped}'\n")

    # Concatenate video segments and mux stereo audio from Exact Video.mp4
    print("[Mux] Concatenating segments and muxing audio track...")
    mux_cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", concat_list_path,
        "-i", SOURCE_VIDEO,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        OUT_VIDEO_ROOT
    ]
    subprocess.run(mux_cmd, check=True)

    # Copy to original subfolder as well
    shutil.copyfile(OUT_VIDEO_ROOT, OUT_VIDEO_SUBDIR)
    print(f"[Done] Saved full recreated video to:\n  1) {OUT_VIDEO_ROOT}\n  2) {OUT_VIDEO_SUBDIR}")


if __name__ == "__main__":
    main()
