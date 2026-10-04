---
paths:
  - "art-workspace/**"
  - "design/art/**"
  - "references/**"
  - "assets/**"
  - "Assets/**/*.{png,jpg,jpeg,tga,psd,exr,hdr,fbx,obj,blend,svg}"
  - "Content/**"
---

# Art Tooling Rules

Art and audio assets are the one part of this project where the wrong tool
produces something that looks plausible and ships broken. Route by task type
before reaching for any generator, and treat the **NEVER** column as a hard
rule, not a preference — each entry comes from a validated failure recorded in
`references/art-pipeline-gotchas.md`.

## Routing (mandatory)

| Task | Use | NEVER use |
|------|-----|-----------|
| **Sprite / block geometry** | Code — Pillow, via `$GS_PYTHON` | AI generate — SD1.5 draws cuboids as 3D objects with lighting on 4GB VRAM |
| **UI frame, 9-slice** | Penpot vector / Inkscape | AI generate — edges are not pixel-stable |
| **Icon set** | Penpot vector / Inkscape | AI generate — style drifts per icon |
| **UI layout, design system** | Penpot flex/grid | Hand-computed coordinates — they drift when the screen size changes |
| **3D props, low-poly** | Blockbench | AI generate — this is where Blockbench is correct |
| **Board / organic texture** | ComfyUI | Ship un-tiled output |
| **SFX, BGM** | ComfyUI Stable Audio | Ship un-mastered audio |
| **HUD font** | Open-source font | AI-rendered text — SD1.5 cannot spell |
| **Alpha channel** | Pillow chroma key | a "transparent background" prompt — SD1.5 has no real alpha |
| **Paint / texture by hand** | Krita (human, interactive) | — the agent does not run Krita itself |
| **Production art** | Human artist | Ship raw AI output |

The full 11-row table, with per-task spec templates, lives in the `/art-brief`
skill. This rule carries the mandatory rows so no agent has to open the skill
to avoid the common mistakes.

## Blockbench and Krita: correct place vs wrong place

Both tools are easy to misfire because each is correct for one job and wrong
for a neighbouring one.

- **Blockbench is the correct tool for 3D props and low-poly mesh** — and the
  wrong tool for 2D pixel-art sprites, sprite sheets or flat UI. When the
  deliverable is a sprite, the output must be a flat image, not a mesh; reaching
  for Blockbench because it is a "modeling tool" produces geometry where a sprite
  was required.
- **Krita is the correct tool for human hand-painting** — and is a human tool:
  the agent does not launch or drive it. Route hand-painting to the user; do not
  script it.

## The five hard rules

1. **Source `tools/art/env.sh` before invoking ANY art tool.** `GameArtBin`
   exists in Windows `;`-separated form, which MSYS/Git Bash cannot read, so no
   tool resolves until `env.sh` converts and prepends it. Verify with
   `command -v blender krita inkscape blockbench gimp-console-3.2`, and use
   `$GS_PYTHON` (never bare `python`) for Pillow — the repo venv is the only
   interpreter that has it.
2. **Geometry is drawn in code, not prompted.** SD1.5 treats geometric
   primitives as physical 3D objects; a "flat square" prompt returns a photograph
   of a cube. Pillow draws the same square in three lines.
3. **Never ship raw AI output.** AI is for concept, texture, style-locking
   references, placeholders and cleanup only. Every generated asset passes human
   review, engine import validation, and in-game observation before it ships.
4. **Don't trust logs, measure artifacts.** Separate MEASURE (count pixels, parse
   the SVG, read file size) from VERDICT (compare the measurement to spec). A
   checker that both measures and judges drifts when the rule is re-reasoned — a
   validated example reported 69 → 32 → 0 issues on the same unchanged file.
5. **One ComfyUI / GPU generation at a time.** NEVER submit a second generation
   while another is running or queued — sequential, foreground, one job. ComfyUI
   serialises anyway, so a second submission is not parallel work: it is a queued
   job the agent has lost track of, and debugging a "stuck" job that was merely
   queued behind an earlier one wastes more time than serialising saves. Before
   starting: require ≥ 3 GB free VRAM (`nvidia-smi --query-gpu=memory.free`) and
   close the Unity editor or any game. Frame-generation and audio-generation count
   as the same GPU work. See the game project's own `MODEL-FEASIBILITY.md` §5 **if that project is present** — otherwise the rule above is the whole check.
6. **The negative prompt must never negate the style the positive asks for.**
   A negative containing `3d render / matte / flat vector / icon / chalk / outline`
   turned a `glossy soft 3D toy style` request into an anime girl; removing those
   eight terms made the same request collapse onto a single-sphere blob. Negative
   blocks *adjacent wrong subjects* (`dog, cat, butterfly, lizard, spider, human`)
   and *technique conflicts only when the positive is not asking for that
   technique*. **Never ship a recipe whose negative fights its own positive.**
   See the game project's own `GENERATION-LOG.md` §1a #18–#20, **if that project is present**.
7. **Numbers in a prompt are style noise, not anatomy.** `six legs` and
   `THREE body segments` produced a dog/blob, an anime girl, a butterfly, a lizard
   and a sphere — never once an ant with six legs. A base SD1.5 checkpoint has no
   "ant" concept. For a character that must hit a spec: **code draws the structure,
   the model fills the surface** (img2img at denoise 0.4–0.55), or use a
   **character-trained LoRA**. Anatomy from text is not measurable here.

## Where the knowledge lives

- **The working game project root, if this repo is driving one** — resolve it from
  `project.yaml`'s `engine.path` / the active project pointer, not from a hardcoded
  path. That project's own docs govern its **measured numbers**: its
  `docs/` (pipeline, model feasibility, quality playbook, generation log, audits) and
  `design/assets/specs/` (per-asset specs). Its visual authority is
  `design/art/art-bible.md`.
  **This rule governs tool choice; the project's own docs govern that project's
  measured numbers** — a LoRA strength or VRAM ceiling measured on one prompt/hardware
  is that project's datum, not a reusable constant.
- `docs/ART_TOOLCHAIN.md` — tool versions, install locations, verification, the
  MSYS PATH trap, the Python/`$GS_PYTHON` contract.
- `references/art-pipeline-gotchas.md` — the 8 validated failure modes (A–H) plus
  §6/§7 (seam + metric), with reproductions and fixes.
- `references/tool-gotchas.md` — per-tool capability notes, including the
  unverified items below.
- `tools/art/env.sh` — session PATH setup; source it before any art tool.
- `art-workspace/` — artifact staging (`inbox/`, `work/`, `exports/`,
  `provenance/`). Note the asset validation hook does not yet know this root; it
  only validates the engine asset roots (`assets/`, `Assets/`, `Content/`).
- `.claude/skills/art-brief/SKILL.md` — the full 11-row routing table and spec templates.

## Unverified capabilities

The following are **UNVERIFIED** and must not be presented as working
capability. Cross-reference `references/tool-gotchas.md` before relying on any
of them:

- **Krita CLI headless scripting** — UNVERIFIED. No headless invocation of Krita
  has been confirmed here.
- **Blockbench headless export** — UNVERIFIED. Blockbench has no headless mode;
  automation requires a plugin loaded into the running desktop app.
- **Inkscape CLI with an external font** — UNVERIFIED. Whether the Inkscape CLI
  resolves and applies a font that is not installed system-wide is not confirmed.
