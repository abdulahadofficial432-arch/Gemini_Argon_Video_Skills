# Gemini Argon Video Skills (`Argon Skills`)

A modular, extensible repository of **Antigravity / Gemini Video Production Skills** for forensic frame-by-frame reference analysis and 100% from-scratch procedural video & audio generation.

---

## Included Video Production Skills

| # | Skill Folder | Primary Skill File | Target Format & Style |
| :--- | :--- | :--- | :--- |
| **1** | [`2D Explainer Long Videos Skill`](./2D%20Explainer%20Long%20Videos%20Skill/) | [`2D Explainer Long Videos.md`](./2D%20Explainer%20Long%20Videos%20Skill/Skills/2D%20Explainer%20Long%20Videos.md) | **`1920×1080` @ `30 fps`** — Long-form 2D explainer & survival storytelling videos featuring rigged 2D protagonist **"Chad"**, spiral notebooks with live writing hand, wall calendars, and emergency alert overlays. |
| **2** | [`Grid Videos Creation Skill`](./Grid%20Videos%20Creation%20Skill/) | [`Grid Videos Creation.md`](./Grid%20Videos%20Creation%20Skill/Skills/Grid%20Videos%20Creation.md) | **`1080×1350` @ `30 fps` (`36.0s`)** — Grid portfolio & intro motion graphics videos built from a reference video (`ref video/`) and custom portrait/role assets (`My Data/`). |
| **3** | [`Render Rigged 3D Videos Skill`](./Render%20Rigged%203D%20Videos%20Skill/) | [`Render Rigged 3D.md`](./Render%20Rigged%203D%20Videos%20Skill/Skills/Render%20Rigged%203D.md) | **`1080×1920` @ `30 fps`** — Glitch-free **18-Joint 3D Skeletal Rigged Procedural Animation** with sequential frame-by-frame inspection (`Frame 0..N-1`), macro 3D physics explanations, zero captions, and 100% from-scratch `Voiceover`, `SFX`, and `Music` stems. |

---

## Repository Directory Structure

Every skill inside `Argon Skills` follows a clean, standardized layout so new skills can be added seamlessly in the future:

```text
Argon Skills/
├── README.md                                  # Master catalog & guide for adding future skills
├── .agents/
│   └── skills/                                # Unified auto-discovered skills for Antigravity IDE/CLI
│       ├── 2d-explainer-long-videos/
│       ├── grid-videos-creation/
│       └── render-rigged-3d/
│
├── 2D Explainer Long Videos Skill/
│   ├── .agents/skills/2d-explainer-long-videos/
│   └── Skills/
│       ├── 2D Explainer Long Videos.md        # Main skill runbook with embedded screenshots
│       ├── 2D Explainer Long Videos/SKILL.md
│       ├── screenshots/                       # Visual reference & recreated frame comparisons
│       └── scripts/                           # Modular 2D PyCairo engine & timeline scripts
│
├── Grid Videos Creation Skill/
│   ├── .agents/skills/grid-videos-creation/
│   └── Skills/
│       ├── Grid Videos Creation.md            # Main skill runbook with embedded screenshots
│       ├── grid-videos-creation/SKILL.md
│       ├── screenshots/                       # Scene 1–3 visual reference & asset previews
│       └── scripts/                           # Fast static-frame cached motion graphics generator
│
├── Render Rigged 3D Videos Skill/
│   ├── .agents/skills/render-rigged-3d/
│   └── Skills/
│       ├── Render Rigged 3D.md                # Main 18-Joint 3D Rigged skill runbook
│       ├── Render Rigged 3D/SKILL.md
│       ├── screenshots/                       # 3D rigged contact sheets (Train Video & Japan Job Culture)
│       └── scripts/                           # 3D camera/rig engine, frame inspector & audio synthesizers
│
└── _Skill_Template/                           # Ready-to-copy template for adding new skills in the future
    └── Skills/
        └── Skill_Template.md
```

---

## How to Add a New Skill in the Future

1. **Duplicate `_Skill_Template/`**:
   - Copy `_Skill_Template` to a new folder at the root of `Argon Skills`, e.g. `<New Skill Name> Skill/`.
2. **Add the Skill Markdown, Scripts & Screenshots**:
   - Place your main skill documentation in `<New Skill Name> Skill/Skills/<New Skill Name>.md` and `<New Skill Name> Skill/Skills/<New Skill Name>/SKILL.md`.
   - Place Python rendering/analysis scripts in `<New Skill Name> Skill/Skills/scripts/`.
   - Place preview images/contact sheets in `<New Skill Name> Skill/Skills/screenshots/`.
3. **Register in `.agents/skills/` (Optional Auto-Discovery)**:
   - Copy the skill folder to `.agents/skills/<kebab-case-skill-name>/SKILL.md` so Antigravity automatically discovers it.
4. **Commit & Push to GitHub**:
   ```bash
   git add .
   git commit -m "Add <New Skill Name> Skill"
   git push
   ```
