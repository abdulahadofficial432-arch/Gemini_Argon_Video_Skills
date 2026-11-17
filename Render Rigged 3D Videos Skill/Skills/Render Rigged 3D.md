---
name: Render Rigged 3D
description: Complete 18-Joint 3D Skeletal Rigged Procedural Animation, Sequential Frame-by-Frame Video Inspection, and From-Scratch Audio Production Skill following the user's exact folder-based instruction workflow.
---

# Render Rigged 3D — Complete Skill & User Instruction Workflow

## 1. How the User Gives Instructions (The User's Workflow Method)

Whenever the user starts a new video recreation task, they follow this exact workflow:

1. **New Project Folder in Main Workspace (`C:\Users\WayWe Work-Station\Downloads\Mate\<Project Folder>\`)**:
   - The user creates a new folder inside the main workspace folder named after the video topic (for example: `"Train Video"`, `"Job Culture of japan"`, `"Railroad Video"`, `"The Window That Breaks Japan's Gambling Law"`, `"80 Victories in a Plane Nobody Could See"`).
2. **Reference Video + Voiceover Inside the Project Folder**:
   - Inside that project folder, the user places:
     - **A Reference Video** (e.g., `"Example video 1.mp4"`, `"Jap vid.mp4"`, `"My video 0.mp4"`, `"My video 2.mp4"`).
     - **A Voiceover Audio File** placed either directly in the project folder or inside a voiceover subfolder (`"VoiceOver"`, `"VoiceOver 01"`, `"VoiceOver 02"`), named e.g. `"Voiceover.mp3"` or `"Audio.mp3"`.
3. **The User's Prompting Pattern**:
   - The user asks you to:
     1. **Read and analyze the reference video frame-by-frame (`Frame 0` to `Frame N-1`)** in strict chronological order without skipping or sampling frames, checking every single frame for:
        - Exact frame number & timestamp (`frame / fps`)
        - Camera position, angle, movement (`dx, dy`, zoom, tilt, roll), and shot framing
        - Every visible person, position, movement, facial expression, body pose, hands/fingers, and clothing/accessories
        - Objects, vehicles, background/environment, lighting, shadows, text/logos/signage, and visual effects
        - Frame-to-frame comparison (what changed, what stayed the same, direction/amount of movement, new/removed objects, morphing, flickering, or generation artifacts)
     2. **Recreate the exact same video 100% from scratch** using the user's **Voiceover** file, matching the exact visuals, hyper-active audience-grabbing animation, character rigging/movements, camera choreography, and clear visual explanations — rendered in the **locked 18-Joint 3D Skeletal Rigged Procedural Animation style** with **zero captions** and **100% from-scratch SFX and Music stems**.

---

## 2. Visual Reference & Rendered 3D Contact Sheets (`screenshots/`)

### A. Train Video — 18-Joint 3D Rigged Recreation & Macro Thermal Physics (`train_rigged_3d_sheet_01..03.jpg`)
![Train Video 3D Sheet 01 (0s–25s): Crouched Hacksaw on 3D Rail, Steam Locomotive Pass-By, Parallel Canyon Bridges, Union Station Gold Bullion & Purple-Faced Boss](./screenshots/train_rigged_3d_sheet_01.jpg)

![Train Video 3D Sheet 02 (25s–50s): Side-Profile Macro 3D Rail Joint with Vernier Caliper, Welded Rival Track, Vandergold Parlor Car, Jolting Coach & Unobstructed Newspaper](./screenshots/train_rigged_3d_sheet_02.jpg)

![Train Video 3D Sheet 03 (50s–76.67s): Silver Coin in May Gap, White Paper in July Gap, Crushing Rival Rails, Beach Umbrella Tycoon & Steel Arch Bridge Plunge](./screenshots/train_rigged_3d_sheet_03.jpg)

### B. Job Culture of Japan — 18-Joint 3D Rigged Corporate Animation (`japan_rigged_3d_sheet_01..03.jpg`)
![Japan Job Culture 3D Sheet 01: 3D Office Environments, Reclining Desk-Propped Poses & Articulated 18-Joint Walk Cycles](./screenshots/japan_rigged_3d_sheet_01.jpg)

![Japan Job Culture 3D Sheet 02: Dynamic 3D Camera Angles, Expressive Spherical Heads & Prop Interactions](./screenshots/japan_rigged_3d_sheet_02.jpg)

![Japan Job Culture 3D Sheet 03: Climax 3D Sequences & Zero-Caption Studio Finish](./screenshots/japan_rigged_3d_sheet_03.jpg)

---

## 3. Locked 18-Joint 3D Skeletal Rigged Animation Architecture

All videos created with **Render Rigged 3D** must use a **100% from-scratch 3D procedural engine (`PyCairo` + `NumPy` + `FFmpeg` at `1080×1920`, `30.00 fps`)** with zero 2D stick-figure shortcuts and zero polygon glitches:

### A. Glitch-Free 3D Camera & Polygon Pipeline (`Camera3D`, `clip_and_project_poly`, `draw_box_3d`)
1. **True 3D Perspective Camera (`Camera3D`)**:
   - Supports world-space `pos = (x, y, z)`, `target = (tx, ty, tz)`, `fov`, Dutch-angle `roll`, organic handheld sway (`math.sin(t * 2.5) * 4.0`), fast dolly push-ins, whip pans, crane tilts, and high-frequency jolt shakes.
2. **Sutherland-Hodgman 3D Near-Plane Polygon Clipping (`NEAR_Z = 45.0`)**:
   - **Mandatory Anti-Glitch Rule**: Never project 3D vertices that cross behind the camera by simply clamping `z_cam`. Always clip every 3D polygon (`clip_and_project_poly`) against the camera near plane `z_cam >= 45.0` before perspective division so long rails, floors, walls, and bridges never fold or warp across the screen.
3. **Deterministic 3D Outward-Normal Back-Face Culling**:
   - **Mandatory Anti-Flicker Rule**: In `draw_box_3d`, never sort box faces by average vertex depth (which causes adjacent faces to swap depth order and flicker as the camera moves). Always use outward-normal back-face culling (`np.dot(face_normal, cam.pos - face_center) > 0`) and subdivide long geometry (such as railroad rails and ties) into back-to-front segments.

### B. 18-Joint 3D Articulated Character Rig (`draw_rigged_character_3d`)
Every character is animated in 3D world space using an **18-joint skeletal hierarchy**:
- **Torso & Head Chain (5 joints)**: `pelvis` -> `spine` -> `chest` -> `neck` -> `head`
- **Left & Right Arm Chains (8 joints)**: `clavicle_L/R` -> `shoulder_L/R` -> `elbow_L/R` -> `wrist_L/R` -> `hand_L/R`
- **Left & Right Leg Chains (6 joints)**: `hip_L/R` -> `knee_L/R` -> `ankle_L/R` -> `toe_L/R`
- **Curved 3D Articulated Limbs (`draw_curved_limb_3d`)**:
  - Smooth cubic-Bezier articulated limbs through `(shoulder, elbow, wrist)` and `(hip, knee, ankle)` with shaded 3D spherical hands and 3D shoes.
- **3D Spherical Head, Hats & Facial Rig**:
  - Radial-gradient 3D shaded sphere head with perspective-foreshortened eyes, pupils, eyebrows, and mouth expressions (`neutral`, `grin`, `angry`, `rage`, `panic`, `worried`, `squint`, `closed_smile`) that rotate across the 3D sphere surface according to `(head_yaw, head_pitch, head_roll)`.
  - Includes periodic eye blinking, chest breathing (`math.sin(t * 4.5)`), sweat droplets, role-specific 3D hats/vests/suits (`engineer`, `boss`, `tycoon`, `foreman`, `veteran`, `worker`), and special visual states (e.g., `purple_anger` transitioning the head to violet-purple with 3D white steam puffs erupting from both ears).
- **Unobstructed Front-Prop Layering Rule**:
  - Whenever a character holds a readable front prop (such as a newspaper, sign, or document), draw the 3D upper/lower arms **first** (so they tuck naturally behind the prop), draw the prop **second** in front of the chest, and draw the white 3D spherical hands **third** gripping the left and right outer edges so arm lines never cross over text or illustrations.

### C. Crystal-Clear Visual Storytelling & Macro Physics Views
- Every concept described in the voiceover must be **visually explained on screen** through clear 3D staging, props, and dedicated macro shots:
  - **Macro 3D Cutaways & Gauges**: When explaining measurements, physics, or mechanisms (e.g., thermal rail expansion), build a dedicated side-profile 3D macro view (`draw_macro_rail_joint_side_3d`) featuring 3D I-beam profiles, bolted fishplates, a sliding metal **Vernier caliper** clamping the exact gap, a rising mercury **thermometer**, a flipping **calendar (`MAY` -> `JUNE` -> `JULY`)**, physical comparison objects dropping into the gap (**silver coin** vs. **thin sheet of paper**), and **force/stress arrows (`==><==`)**.
  - **Multi-Sub-Shot Visual Pacing**: Break longer narrative sentences into distinct visual sub-shots (e.g., Sub-shot A showing the macro mechanism -> Sub-shot B showing the characters reacting; or Sub-shot A showing the newspaper headline -> Sub-shot B showing passengers walking toward `'ALL ABOARD!'`) so the visual pacing stays hyper-active and engaging.

---

## 3. Step-by-Step Execution Protocol

Whenever triggered on a new project folder:

### Step 1: Complete Sequential Frame-by-Frame Inspection (`Frame 0` to `Frame N-1`)
1. Run `analyze_every_frame.py` on the reference `.mp4` video to inspect **every single frame from `Frame 0` to `Frame N-1`** in chronological order without skipping frames.
2. Save the complete sequential per-frame report to `<Project Folder>\Frame_By_Frame_Complete_Analysis_<N>_Frames.md`.
3. Extract `6×4` contact sheet `.jpg` grids (1 frame per second) and a 48kbps `.mp3` audio preview into `scratch/`, and inspect every contact sheet and audio file using `read_file` (never call `read_file` on a raw `.mp4`).

### Step 2: Synthesize 100% From-Scratch Audio Stems Synced to the User's Voiceover
1. Measure the exact duration (`VO_DURATION`) of the user's voiceover file (`Voiceover.mp3` / `Audio.mp3`) and convert it to `44.1 kHz` 16-bit stereo `Voiceover.wav` and `Voiceover.mp3` in `<Project Folder>\`.
2. Write and run `build_<project>_audio_stems.py` using `NumPy` + `SciPy` (`scipy.signal.butter`) to synthesize:
   - **`SFX.wav` & `SFX.mp3`**: 100% from-scratch physical-modeling foley synced to every visual action (e.g., hacksaw strokes, steam chugs, whistle Doppler, metallic clanks, coin/paper drops, thermal groans, crashes, explosions).
   - **`Music.wav` & `Music.mp3`**: 100% from-scratch multi-act cinematic/atmospheric score matched to the emotional arc.
   - **`Full_Mixed_Audio.wav` & `Full_Mixed_Audio.mp3`**: Master mix combining `Voiceover + SFX + Music` with automatic envelope ducking so the voiceover remains crystal clear.

### Step 3: Build & Preview-Verify the 18-Joint 3D Rigged Render Script
1. Write `render_<project>_rigged_3d_from_scratch.py` mapping every reference shot and visual explanation onto the exact `VO_DURATION` (`TOTAL_FRAMES = int(math.ceil(VO_DURATION * 30))`).
2. **Mandatory Pre-Render Visual Check (`preview` mode)**:
   - Run `python render_<project>_rigged_3d_from_scratch.py preview` to generate 3 contact sheets (`sheet_01.jpg`, `sheet_02.jpg`, `sheet_03.jpg`, 72 tiles evenly spanning `0.0s .. VO_DURATION`).
   - Inspect all 3 contact sheets via `read_file` to verify:
     - Zero 3D polygon warping or box-face flickering
     - Zero prop/limb overlaps (hands on outer edges of newspapers/signs, hats/umbrellas properly layered)
     - Every story beat and physical mechanism is visually clear
     - Zero voiceover captions

### Step 4: Render Full 30-FPS 1080×1920 Video & Verify Deliverables
1. Run `python render_<project>_rigged_3d_from_scratch.py` to render all `TOTAL_FRAMES` frames at `1080×1920` (`30.00 fps`) and mux with `Full_Mixed_Audio.wav`.
2. Verify that `<Project Folder>\` contains all required deliverables:
   - `Final_Video_No_Captions.mp4` (Full Mixed Audio, Zero Captions)
   - `Pure_3D_Procedural_From_Scratch_No_Captions.mp4` (Pure 3D Rigged Render Copy)
   - `Video_Only_No_Captions_Muted.mp4` (Clean Muted Video Master)
   - `Frame_By_Frame_Complete_Analysis_<N>_Frames.md`
   - `Voiceover.wav` & `Voiceover.mp3`
   - `SFX.wav` & `SFX.mp3`
   - `Music.wav` & `Music.mp3`
   - `Full_Mixed_Audio.wav` & `Full_Mixed_Audio.mp3`
   - `scripts/` containing the complete Python generator scripts.
