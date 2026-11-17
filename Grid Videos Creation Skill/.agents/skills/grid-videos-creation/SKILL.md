---
name: grid-videos-creation
title: Grid Videos Creation
description: >-
  End-to-end workflow and technical specification for creating 1080x1350 (30 fps, 36.0s)
  Grid Portfolio & Intro Motion Graphics videos from a reference video ("ref video") and
  custom user assets ("My Data"), following the user's iterative instruction method.
---

# Grid Videos Creation

Use this skill whenever creating or updating a **Grid Portfolio / Intro Motion Graphics Video** (`1080x1350`, `30 fps`, `36.0s`, H.264 video + AAC audio) modeled on a reference video (`ref video/ref video.mp4`) and custom image/text assets (`My Data/`).

---

## 1. How Instructions Are Given (User's Workflow Method)

Understanding how the user structures the project and gives instructions is essential to executing this workflow smoothly:

### Phase 1: Folder Setup & Initial Prompt
1. **`ref video/` Folder**: Contains the target motion graphics reference video (`ref video.mp4`, `1080x1350`, `30 fps`, `36.0s`). Its exact frame timings, easing curves, sound effects (`-c:a copy`), and transitions are used as the master blueprint.
2. **`My Data/` Folder**: Contains the person's custom assets:
   - `Grid Background.jpg` — Dark olive-brown grid background used in Scene 1 and Scene 3.
   - `Character.jpg` — Portrait with a solid dark background and a crisp **white cutout outline** around the subject.
   - `Plain Background.jpg` — Solid olive-green background used for the Scene 1 → Scene 2 zoom transition.
   - `Bar.jpg` — Olive-green background with a centered glassmorphic search bar (`y = 646`).
   - `Outro example.jpg` & `Outro example 2.jpg` — Reference layouts for the social pills (`in`, `Bē`) and the bottom `"Let's Connect."` typography.
   - `Name and age and role.txt` — Text file specifying the person's Name, primary Role, and specialty badge text.
3. **Initial Prompt Style**:
   > *"Analyse the 'ref video' completely and carefully and 100% and After that use data from 'My Data' folder and create exact same to same video in same style and format like 'ref video'"*

### Phase 2: Fast Iterative Visual Refinements
After inspecting the first generated `Final Video.mp4`, the user gives short, targeted refinement instructions one step at a time. Typical refinement instructions include:
- **Speed & Task Handling**: *"Do not kill the task 'Render and encode Final Video.mp4' make This process fast"* → Always use the fast static-frame caching script ([`scripts/generate_video_fast.py`](../scripts/generate_video_fast.py)) which renders and encodes all 1,080 frames in **~12–16 seconds**.
- **Right-Side Text Stack Customizations**: *"remove the Age and Instead of 'Jobless' Add 'Your'"* and *"Bold the start text 'Your'"* → Omit the age line, start directly with bold `"Your"`, then type the primary role (`"Sr UI/UX"`), slide in bold `"Designer"`, and bounce in the tilted `"Graphics Expert ❤"` pill badge.
- **Character Cutout Outline Color**: *"I want Character outline white not olive"* → Preserve the original crisp **white** sticker outline around the character cutout in Scene 1 (`Character.jpg`), and zoom into the character's olive hijab during the transition into Scene 2.
- **Animated Search Bar Role Text Color**: *"Instead of white make animated role text to the same color as 'Lets Connect' text has"* → Render the cycling middle role text (`Creative`, `Brand`, `UI/UX`, `Web Graphics`, `Social Media`, `Creative Ads`, `Book Cover`, `One`) in the signature cream-lime color (`#E7F3D0` / `RGB(231, 243, 208)`), while keeping `"Your"` and `"Designer"` / `"Design"` / `"partner"` in dark charcoal (`RGB(35, 38, 22)`).
- **Adding Contact Pills in the Outro**: *"create area for gmail and add this Gmail 'syedamuskan902@gmail.com' on the end below the behance"* → Clone the pill container below Behance, place a matching circular mail icon badge on the left, and render the email address inside the third pill.

---

## 2. Visual Reference & Content Screenshots

### A. Input Assets (`My Data/` Folder)
![Input Assets Overview](../screenshots/01_input_assets_overview.png)

### B. Scene 1: Animated `"Helloo"` Intro, White-Outlined Character, Bold `"Your"`, & Badge (`00:00 – 00:18`)
![Scene 1 Intro and Character](../screenshots/02_scene1_intro_and_character.png)

### C. Scene 2: Search Bar Role Cycling (`#E7F3D0` Cream-Lime) & `"Let's Connect"` (`00:19 – 00:32`)
![Scene 2 Search Bar Animation](../screenshots/03_scene2_search_bar_animation.png)

### D. Scene 3: Radial Grid-Mosaic Transition & Final 3-Pill Outro (`00:33 – 00:36`)
![Scene 3 Mosaic and Final Outro](../screenshots/04_scene3_mosaic_and_outro.png)

---

## 3. Complete Technical Specification (`1080x1350` @ `30 fps`, `1,080 Frames`)

### Color Palette & Fonts
| Element | RGB Value | Hex | Usage |
| :--- | :--- | :--- | :--- |
| **`CREAM`** (`Let's Connect` Color) | `(231, 243, 208)` | `#E7F3D0` | `"Helloo"`, Scene 1 text, Scene 2 animated role titles (`Creative` .. `One`), `"Let's Connect"`, Outro pills & `"Let's Connect."` |
| **`DARK_TEXT`** | `(35, 38, 22)` | `#232616` | `"Your"`, `"Designer"`, `"Design"`, and cursive `"partner"` in Scene 2 |
| **`OLIVE_BG`** | `(105, 101, 63)` | `#69653F` | Plain olive background (`Plain Background.jpg`) and `"Graphics Expert ❤"` pill fill |
| **`DARK_CIRCLE_ICON`** | `(48, 51, 34)` | `#303322` | Cutout icons (`in`, `Bē`, `✉`) inside the cream circles in Scene 3 |
| **Character Outline** | `(255, 255, 255)` | `#FFFFFF` | Crisp white sticker outline around the character portrait |

- **Fonts (`Poppins` family)**:
  - `Poppins-Regular.ttf` (`28px` for `"I am <Name>"`, `34px` for typed `"Sr UI/UX"`, `40px` for animated bar roles & `"Let's "`, `48px` supersampled 2x for `"Graphics Expert"` badge)
  - `Poppins-SemiBold.ttf` (`36px` for right-side bold `"Your"` and `"Designer"`, `40px` for bar `"Your "`, `" Designer"`, and `"Connect"`)
  - `Poppins-Light.ttf` + `Poppins-Regular.ttf` (`35px` blended for the Gmail address inside the 3rd outro pill)

### Aspect Ratio Mapping (`3:4` Source Images → `4:5` Video Canvas)
The source images in `My Data/` are `896x1200` or `1792x2400` (`3:4` aspect ratio), while the target video canvas is `1080x1350` (`4:5` aspect ratio).
- **Never stretch `3:4` directly to `4:5`** (which squashes circles and faces vertically by 6.6%).
- Always resize width to `1080` (`1080x1446`, `Image.Resampling.LANCZOS`) and crop `1350px` vertically:
  - `Grid Background.jpg`: `.resize((1080, 1446)).crop((0, 48, 1080, 1398))`
  - `Plain Background.jpg` & `Bar.jpg`: `.resize((1080, 1446)).crop((0, 37, 1080, 1387))`

### Scene-by-Scene Frame Breakdown

1. **`F0001 – F0159` (`0.00s – 5.30s`) — `"Helloo"` Eye Animation & Slide-Up**:
   - Extract the `"Helloo"` alpha mask from `ref video.mp4` frames `f_0001..f_0159` via green-channel matting (`np.clip((g - 42.0) / (240.0 - 42.0), 0.0, 1.0)`) and composite `CREAM` onto `Grid Background.jpg`.
2. **`F0159 – F0190` (`5.30s – 6.33s`) — Character Pop-Up & Smile Curve**:
   - Remove the outer dark background of `Character.jpg` using connected-component labeling (`scipy.ndimage.label`) from `(0, 0)` so interior dark regions (eyes/eyebrows) remain untouched and the **white outline** is preserved.
   - Animate the character rising from `y_offset = 1050` to `0` (`CHAR_X = 58, CHAR_Y = 306`) over `F0159..F0187` using `PchipInterpolator`.
   - Extract the animated smile curve beneath the first `"o"` strictly within `y=[402, 445], x=[818, 910]` (avoiding any lower pixels from the reference video's character head).
3. **`F0204 – F0220` (`6.80s – 7.33s`) — Left Text `"I am <Name>"`**:
   - Slide up `"I "`, `"am "`, and `"<Name>"` sequentially at `(71, 418)` in `CREAM` (`Poppins-Regular`, `28px`).
4. **`F0270 – F0547` (`9.00s – 18.23s`) — Right-Side Stack (`Your` → `Sr UI/UX` → `Designer` → Badge)**:
   - **`F0270 – F0286`**: **Bold** `"Your"` (`Poppins-SemiBold`, `36px`, right-aligned at `x = 1038`) slides in at `y = 770`.
   - **`F0307 – F0334`**: Animated pointer cursor moves in and clicks at `(1032, 795)` on `F0324..F0330`.
   - **`F0330 – F0345`**: Bold `"Your"` smoothly shifts up by `52px` (`y = 718`) as the typing caret `|` appears on line 2 (`y = 770`).
   - **`F0354 – F0465`**: Typewriter animation types `"Sr UI/UX"` character-by-character synced to the keyboard audio clicks.
   - **`F0466 – F0480`**: **Bold** `"Designer"` (`Poppins-SemiBold`, `36px`) slides down into place at `y = 820`.
   - **`F0499 – F0524`**: Tilted olive pill badge `"Graphics Expert ❤"` (`-4°` angle, with a supersampled parametric vector heart) bounces up from the bottom, pushing the 3-line text stack up with an elastic physics bounce (`dy = -90px` peak settling at `dy = -28px`).
5. **`F0547 – F0574` (`18.23s – 19.13s`) — Exponential Camera Zoom Transition**:
   - Zoom exponentially (`scale = 45.0 ** (ease_in_out_cubic(t) ** 0.95)`) into the olive hijab (`fx = 445, fy = 360`) and cross-fade (`F0556..F0574`) into `Plain Background.jpg`.
6. **`F0582 – F0836` (`19.40s – 27.87s`) — Search Bar Role Cycling**:
   - Fade in `Bar.jpg` (`F0582..F0605`) and `"Your Creative Designer"` centered at `y = 646`.
   - Cycle through all 8 roles (`Creative`, `Brand`, `UI/UX`, `Web Graphics`, `Social Media`, `Creative Ads`, `Book Cover`, `One`) at frames `619, 651, 679, 706, 736, 770, 799`.
   - Render `"Your "` and `" Designer"` in `DARK_TEXT` (`(35, 38, 22)`, `Poppins-SemiBold`) and the animated middle role in `CREAM` (`(231, 243, 208)`, `Poppins-Regular`).
7. **`F0840 – F0995` (`28.00s – 33.17s`) — `"Your One Design partner"` & `"Let's Connect"`**:
   - **`F0840 – F0887`**: `"Your One Designer"` changes to `"Your One Design"`, shifts left, and cursive `"partner"` (extracted from `f_0875.jpg[620:682, 680:860]`) slides in from the right.
   - **`F0888 – F0913`**: `"Your One Design partner"` rises above the search bar (`y = 646 → 542`) while `"Let's Connect"` (`CREAM`) fades in inside the search bar.
   - **`F0953 – F0970`**: Cursor moves to `"Let's Connect"`, clicks (`F0958..F0960`), and exits right.
   - **`F0964 – F0995`**: Huge `"Let's Connect."` (`Outro example 2.jpg`) rises from the bottom of the canvas (`y = 1350 → 975`).
8. **`F0996 – F1080` (`33.20s – 36.00s`) — Radial Grid-Mosaic Reveal & 3-Pill Outro**:
   - **`F0996 – F1014`**: Radial wave (`cx0 = 540, cy0 = 580`) reveals the dark grid background cell-by-cell (`20x23` grid cells) with highlighted cell borders.
   - **`F1015 – F1080`**: Holds the final Outro screen with 3 evenly spaced contact pills (`y_top = 270`, vertical center spacing `179px`) above `"Let's Connect."`:
     1. **LinkedIn**: `in` badge + handle (`imsyedamuskan`)
     2. **Behance**: `Bē` badge + handle (`syedamuskan902`)
     3. **Gmail**: `✉` envelope badge + email (`syedamuskan902@gmail.com`)

---

## 4. Fast Rendering & Encoding (`~12–16 Seconds`)

To render or update the video in ~12–16 seconds:
1. Run [`scripts/generate_video_fast.py`](../scripts/generate_video_fast.py):
   ```powershell
   python "C:\Users\WayWe Work-Station\Downloads\Make video\Skills\scripts\generate_video_fast.py"
   ```
2. **Why it is fast and never hangs**:
   - **No FFmpeg Pipe Deadlock**: Invokes `ffmpeg -loglevel error` without `stderr=subprocess.PIPE` so OS pipe buffers never block `stdin.write()`.
   - **Static-Frame Byte Caching (`STATIC_RANGES`)**: Reuses the raw `rgb24` byte buffer (`prev_bytes`) on all 509 static frames where `frame[fn] == frame[fn - 1]`, reducing unique frame renders from `1,080` to `571`.
   - **Target-Resolution Cutout Matting**: Computes the `scipy.ndimage` character alpha matte at target scale (`779x1044`) instead of full `1792x2400` resolution, cutting initialization time to `0.38s`.
