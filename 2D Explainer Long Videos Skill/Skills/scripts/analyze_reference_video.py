"""
Forensic Reference Video Analyzer for "2D Explainer Long Videos" Skill.
Probes resolution/FPS/duration via ffprobe, slices the reference video into
60-second preview clips, and extracts 1080p keyframes for shot-by-shot analysis.
"""
import os
import sys
import math
import json
import subprocess


def analyze_video(video_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,size,bit_rate",
        "-show_entries", "stream=index,codec_name,codec_type,width,height,r_frame_rate,nb_frames",
        "-of", "json",
        video_path
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    info = json.loads(res.stdout)
    with open(os.path.join(out_dir, "probe_info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2)

    duration = float(info.get("format", {}).get("duration", 0.0))
    print(f"[Probe] Video: {video_path} | Duration: {duration:.2f}s")

    # 1. Extract 60-second compact clips (640x360) for rapid timeline inspection
    n_clips = int(math.ceil(duration / 60.0))
    for i in range(n_clips):
        t0 = i * 60
        t1 = min(int(math.ceil(duration)), (i + 1) * 60)
        clip_out = os.path.join(out_dir, f"clip_{t0}_{t1}.mp4")
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", str(t0), "-to", str(t1), "-i", video_path,
            "-vf", "scale=640:360",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-c:a", "aac", "-b:a", "96k",
            clip_out
        ]
        subprocess.run(cmd, check=True)
        print(f"  -> Extracted clip: {clip_out}")

    # 2. Extract 1080p keyframes every 15 seconds across the video
    for ts in range(2, int(duration), 15):
        jpg_out = os.path.join(out_dir, f"frame_{ts}.jpg")
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", str(ts), "-i", video_path,
            "-frames:v", "1", "-q:v", "3",
            jpg_out
        ]
        subprocess.run(cmd, check=True)

    print(f"[Done] Saved probe metadata, {n_clips} clips, and 1080p keyframes to {out_dir}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python analyze_reference_video.py <path_to_video.mp4> <output_scratch_dir>")
        sys.exit(1)
    analyze_video(sys.argv[1], sys.argv[2])
