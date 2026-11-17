---
name: e-films
description: Locked 18-Joint 3D Skeletal Rigged Procedural Animation & From-Scratch Audio Production Engine. Use whenever the user asks to analyze a reference video and recreate a brand-new 3D animated video from scratch with zero captions and separate Voiceover, SFX, and Music stems.
---

# E-Films — Locked 18-Joint 3D Skeletal Rigged Procedural Animation Skill

## 1. Core Mandate (Permanently Locked Standard)

Whenever analyzing a reference video and recreating a new video from scratch:
1. **Locked Animation Style — 18-Joint 3D Skeletal Rigged Procedural Animation (`Camera3D` + `RiggedCharacter3D` + `Room3D`/`Box3D`)**:
   - **Never** draw flat 2D stick figures or static 2D rectangles.
   - Always render through a true 3D perspective camera (`Camera3D` with `pos`, `target`, `fov`, `roll`, handheld sway, dolly push-ins, pans, tilts, and Dutch angles).
   - Always build environments and props as **3D world-space meshes** (`draw_poly_3d` and `draw_box_3d` with painter's-algorithm depth sorting, top/front/side directional shading, floor contact shadows, and bold cel-shaded outlines).
   - Always animate characters using the **18-Joint 3D Articulated Skeletal Rig (`draw_rigged_character_3d`)**:
     - **Joint Hierarchy**: `pelvis` -> `spine` -> `chest` -> `neck` -> `head`, `clavicle_L/R` -> `shoulder_L/R` -> `elbow_L/R` -> `wrist_L/R` -> `hand_L/R`, and `hip_L/R` -> `knee_L/R` -> `ankle_L/R` -> `toe_L/R`.
     - **Articulated Curved 3D Limbs (`draw_curved_limb_3d`)**: Smooth Bezier-articulated limbs through `(shoulder, elbow, wrist)` and `(hip, knee, ankle)` with 3D hands and 3D shoes.
     - **Full 3D Walk Cycles & Poses**: 4-phase walk cycle (pelvis bounce, hip sway, opposite arm/leg swing, knee/elbow flexion), reclining desk-propped poses (`recline_feet_up` with crossed ankles on 3D desks), waist-bending inspection poses (`bend_inspect`), sideways doorframe leans (`spine_lean`), and dynamic prop interaction (`storage_key`, `phone`, `gift_box`, `drink`, `flip_breaker`).
     - **3D Spherical Head & Facial Rig**: 3D shaded sphere head with perspective-foreshortened eyes, pupils, eyebrows, mouth, and 3D hair dome that rotate across the sphere surface with `(head_yaw, head_pitch, head_roll)`, plus natural periodic eye blinks and breathing motion.
2. **Complete Sequential Frame-by-Frame Analysis (`Frame 0` to `Frame N-1`)**:
   - Never call `read_file` directly on raw `.mp4` files.
   - Use `scripts/analyze_every_frame.py` (OpenCV + NumPy phase-correlation optical flow, `MAD`, luminance/contrast, RGB, shadow percentage, and caption mask tracking) to inspect every single frame `0..N-1` in chronological order without skipping frames, and output `Frame_By_Frame_Complete_Analysis_<N>_Frames.md`.
   - Extract 1-fps `6×4` contact sheet `.jpg` grids and 48kbps `.mp3` audio previews into `scratch/` for direct visual and audio inspection via `read_file`.
3. **100% From-Scratch Studio SFX & Music Stems**:
   - Synthesize all sound effects (`SFX.wav`/`.mp3`) and background score (`Music.wav`/`.mp3`) 100% from scratch using physical-modeling modal synthesis and Butterworth band-passed foley (`scipy.signal.butter`) synced to the user's voiceover (`Voiceover.wav`/`.mp3`), with auto-ducking under speech in `Full_Mixed_Audio.wav`/`.mp3`.
4. **Zero Captions**:
   - All rendered videos (`Final_Video_No_Captions.mp4`, `Pure_3D_Procedural_From_Scratch_No_Captions.mp4`, `Video_Only_No_Captions_Muted.mp4`) must have **zero on-screen captions**.

---

## 2. Standard Deliverables in Every Project Folder

For every project folder, always generate and verify:
- `Final_Video_No_Captions.mp4` (`1080×1920`, `30 fps`, zero captions, synced to user's voiceover + `Full_Mixed_Audio.wav`)
- `Pure_3D_Procedural_From_Scratch_No_Captions.mp4` (`1080×1920`, `30 fps`, 18-joint 3D skeletal rigged procedural animation from scratch)
- `Video_Only_No_Captions_Muted.mp4` (`1080×1920`, `30 fps`, muted clean video master)
- `Frame_By_Frame_Complete_Analysis_<N>_Frames.md` (complete sequential log of every frame `0..N-1`)
- `Voiceover.wav` & `Voiceover.mp3`
- `SFX.wav` & `SFX.mp3` (100% from-scratch studio foley & sound design)
- `Music.wav` & `Music.mp3` (100% from-scratch atmospheric/cinematic score)
- `Full_Mixed_Audio.wav` & `Full_Mixed_Audio.mp3`
- `scripts/` containing the reusable Python generator scripts (`render_japan_job_3d_from_scratch.py`, `build_japan_audio_stems.py`, `analyze_japan_every_frame.py`)
