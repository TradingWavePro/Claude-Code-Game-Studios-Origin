---
name: art-brief
description: "Art tool routing — which tool for which job, with hard rules on what NOT to use."
argument-hint: ""
user-invocable: true
allowed-tools: Read, Glob, Grep, Write, Edit, AskUserQuestion
model: sonnet
---

# Art Brief — Tool Routing and Task Assignment

Before producing any art asset, check the **art bible** for visual identity constraints, then route the task to the correct tool using the table below.

## Phase 0: Check Art Bible

Read `design/art/art-bible.md` if it exists. If not:
- For projects at `rigor: full` or `standard`, run `/art-bible` first — asset production is gated on the art bible.
- For projects at `rigor: minimal`, the art bible is optional. Proceed with the game brief (`design/game-brief.md`) as the visual guide.

## Phase 1: Route by Task Type

Use this table to decide which tool handles which task. The **NEVER use** column is load-bearing — these are **hard rules** from validated failures.

| Task | Use | NEVER use | Why |
|------|-----|-----------|-----|
| **Sprite/block geometry** | Code (Pillow) | AI generate | SD1.5 draws cuboid/sprite sheet as 3D objects with lighting. Failed 4x on 4GB VRAM. |
| **UI frame, 9-slice** | Penpot vector / Inkscape | AI generate | Edges must be sharp and pixel-perfect. AI can't maintain edge alignment. |
| **Icon set** | Penpot vector | AI generate | AI style drifts per icon. Guaranteed inconsistency across 10+ icons. |
| **UI layout, design system** | Penpot flex/grid | Manual coords | Manual coord → drift when screen size changes. Flex/grid self-align. |
| **3D props, low-poly** | Blockbench | AI generate | This is where Blockbench is correct. |
| **Board texture, organic surface** | ComfyUI | Ship un-tiled output | AI wins here. Must make seamless (tile offset checks). |
| **SFX, BGM** | ComfyUI Stable Audio | Ship un-mastered audio | AI wins for sound effects and BG music. |
| **HUD font** | Open-source font | AI render text | SD1.5 can't render readable text. Use real fonts. |
| **Alpha channel** | Pillow chroma key | "transparent background" prompt | SD1.5 has no real alpha channel. See gotcha A. |
| **Paint / texture by hand** | Krita | — | Agent cannot run it itself. |
| **Production art** | Human artist | Ship raw AI output | AI doesn't preserve pivot, atlas packing, or cross-frame consistency. |

### Correct place vs wrong place

Two tools in the table are easy to misfire, because each is right for one job and
wrong for a neighbouring one:

- **Blockbench — correct place: 3D props and low-poly mesh.** Wrong place: 2D
  pixel-art sprites, sprite sheets, or flat UI. When the deliverable is a sprite,
  the output must be a flat image, not a mesh — do not reach for Blockbench
  because it is a "modeling tool".
- **Krita — correct place: human hand-painting.** It is a human tool: the agent
  does not launch or drive it. Route hand-painting to the user; do not script it.

### Unverified capabilities

The following are **UNVERIFIED** and must not be treated as working capability.
Cross-reference `references/tool-gotchas.md` before relying on any of them:

- **Krita CLI headless scripting** — UNVERIFIED.
- **Blockbench headless export** — UNVERIFIED (Blockbench has no headless mode;
  automation needs a plugin loaded into the running desktop app).
- **Inkscape CLI with an external font** — UNVERIFIED (whether the CLI resolves
  and applies a font not installed system-wide is unconfirmed).

### One GPU generation at a time

**NEVER run two ComfyUI generations concurrently.** Sequential, foreground, one
job; wait for the first to write its output files before submitting the next.
Frame-generation and audio-generation are the same GPU work. ComfyUI serialises
anyway, so a second submission is not parallel work — it is a queued job you have
lost track of, and the failure mode is an agent debugging a "stuck" job that was
merely waiting its turn. Before starting, require **≥ 3 GB free VRAM**
(`nvidia-smi --query-gpu=memory.free`) and close the Unity editor or any game.

On 4 GB Pascal this is not caution, it is arithmetic: a 512² SD1.5 job peaks at
~3.45 GB used, leaving ~0.6 GB. And the model tier is capped — SDXL fp16 ≈ 7.8 GB,
Flux GGUF Q4 ≈ 11 GB, Z-Image 4.2 GB all exceed a ~3.3 GB budget. The one
borderline case (SDXL GGUF Q4 ≈ 3.9 GB) is untestable until `ComfyUI-GGUF` is
installed. Full measurements: the game project's own `MODEL-FEASIBILITY.md`, **if that
project is present** — otherwise re-measure on the machine you are driving.

### Raising quality: fix the subject first, then the pixels

Two runs with the same seed proved the levers below do **not** change *what* is
drawn — a checkpoint's semantics decide that. Apply them only once the subject is
already right. Measured detail: the game project's own `QUALITY-PLAYBOOK.md` **if that project is present** — otherwise apply the principles above.

1. **Subject** — prompt, checkpoint, or a style **LoRA**. On this card `loras/` is
   empty; an SD1.5 game-icon LoRA is the one install worth making, and it is the
   real fix for the flat-geometry failure.
2. **Resolution via hires fix, not a native large render** — generate at 512, then
   `LatentUpscale` → second sampler at **denoise 0.5–0.6**. Measured 126 s for
   512→1024 vs 167 s native, and sharper. Never ask SD1.5 for a native 1024² and
   expect flat surface.
3. **FreeU / FreeU_V2** (built-in) — free contrast and detail, **composition-preserving**
   at the same seed (measured: same seed 424242 → same diagonal-tile composition, more
   grime/contrast, +2 s). Worth enabling by default for surface work; still eyeball it,
   because it amplifies whatever the checkpoint drew — including a wrong subject.
4. **Upscale model** — final crispness only; `upscale_models/` is empty today.

**Style vs anatomy — measured, and the key lesson for characters.** An SD1.5
**game-icon LoRA** (now installed: `game_icons_epoch2.safetensors`, strength 0.8–1.2)
**fixes the style** — a soft 3D toy becomes a flat bold-outline vector icon — but it
**does not fix anatomy**: across strengths 0.85/1.0/1.2 the "ant" became a sphere, a
butterfly, then a baby lizard, with **no run ever showing 6 legs or 3 segments**.
Higher strength = more generic mascot, less insect. So for a character that must hit an
exact spec, route to **code-drawn mask + AI texture fill** (the `art-brief` routing
table's third route), not another prompt or strength tweak. Full data: the game
project's own docs — e.g. its `QUALITY-PLAYBOOK.md` §4a / `GENERATION-LOG.md` §1a **if
that project is present**; these are the game project's own records, not this repo's.

### Model choice per task — principles (portable) vs constants (that project's datum)

> **Two kinds of content below.** The **portable principles** apply to any project.
> The **measured constants** (a LoRA strength, a VRAM ceiling, a resolution) are one
> box/prompt's datum — they live in the *game project's own* docs with an `n=` tag, and
> you should re-measure them for a new project/hardware rather than reuse them as law.

**Portable principles — these transfer:**

1. **The checkpoint's semantics beat the prompt.** A base SD1.5 checkpoint with a
   creature prompt + a counter-prompt negative (`photograph, dog, cat, spider, extra
   limbs`) still produced a dog/blob, an anime girl, a butterfly, a lizard and a single
   sphere — **never once the requested creature**. Do not expect prompt phrasing to fix
   a missing concept in the checkpoint.
2. **Numbers in a prompt are style noise.** "six legs", "THREE body segments" — SD1.5
   does not count. Anatomy from a text prompt is **not measurable**. The reliable routes
   are a **LoRA trained on that creature**, or **code supplies the structure and the
   model supplies the surface** (img2img, denoise 0.4–0.55).
3. **The negative prompt must never negate the style the positive asks for.** A negative
   carrying `3d render / matte / flat vector / icon / outline` turned a
   clay-3D-style request into an anime girl; removing those eight terms made the same
   request collapse onto a single-sphere blob. Negative blocks **adjacent wrong
   subjects** (`dog, cat, butterfly, lizard, spider, human`) and **technique conflicts
   only when the positive is not asking for that technique**. Never ship a recipe
   whose negative fights its own positive.
4. **Hold the seed in any A/B**, or you measure the seed, not the knob. (Measured: a
   FreeU A/B that used two different seeds concluded "FreeU changed the subject"; the
   same A/B with one seed showed the *same* composition, only more detail.)
5. **Resolution is a composition knob, not just a sharpness knob** — with one seed, a
   lower resolution gave a flat tile and a higher one gave a photographic scene. Fetch
   detail with a **hires pass**, not a native large render.
6. **无缝-tileable texture: generate it in code** (modulo-lattice noise) — a diffusion
   model returns a photographic scene even at the same seed; code is byte-exact
   repeatable and seamless by construction.
7. **A style LoRA fixes style, not anatomy** — a LoRA trained on UI icons steers look
   and contrast, not creature structure.
8. **Do not reach for a bigger model to fix a style problem** — see the tool-routing
   table in Phase 1.

**Measured constants — one box/prompt's datum; re-measure, do not reuse as law:**

- This card (4 GB, compute cap 6.1) runs SD1.5-class models only; the ceiling is
  ~3.3 GB usable. SDXL fp16 ≈ 7.8 GB and Flux ≈ 11 GB exceed it.
- A style LoRA measured icon-flat at **0.85**, drifted at ≥1.0, and produced the best
  render at **1.2 only when the positive named its material** (`glossy soft 3D toy
  style`, `smooth clay-like plastic`) — n=1 per arm, so treat as a starting point, not
  a recipe.
- Hires 512→1024 measured 126 s vs 167 s native, and sharper.
- Where those constants came from: the game project's own
  `MODEL-FEASIBILITY.md` / `QUALITY-PLAYBOOK.md` / `GENERATION-LOG.md` — **if the
  project you are driving has those files, read them; if not, measure yours.**

## Phase 2: Produce the Spec

Based on the routed tool, produce a spec with:

### For Code (Pillow) Tasks
- Exact dimensions (width, height in px)
- Color palette (hex codes from art bible)
- Output format (PNG, JPG, BMP)
- Example: "64×64 blue square, #3B82F6, PNG with alpha, centered on 128×128 canvas"

### For Penpot Tasks
- Board size: **match the target device** — read it from the project (Stackyard is
  portrait **1080×1920** mobile; 1920×1080 desktop and 390×844 mobile are other
  common cases). Do not assume desktop landscape.
- Component structure (frame hierarchy, flex direction)
- Typography (font family, weight, size from art bible)
- Color fills (named colors from art bible palette)
- Export format (SVG for icons, PNG for mockups)

### For ComfyUI Tasks
- Workflow type (text-to-image, image-to-image, Stable Audio)
- Model — **verify it can run before speccing it.** On a 4 GB Pascal card only
  SD1.5-class models run (measured: SD1.5 fp16 ✅ up to 1024², SDXL fp16 ❌,
  Flux ❌). Never spec a model the card cannot load; see the project's
  the game project's own `MODEL-FEASIBILITY.md` (if present) for the per-family arithmetic.
- Prompt (positive + negative)
- Dimensions — **512–768 for SD1.5.** Larger is reachable but SD1.5 composes
  *scenes* rather than flat surface above ~512² (measured: 1024² returned an
  object in perspective). For a larger deliverable, generate at 512 and run a
  **hires pass** (`LatentUpscale` → second sampler at denoise ~0.55), which is
  both sharper and cheaper than a native large render.
- Seed (for reproducibility)
- Output format

### For Open-Source Font Tasks
- Font name and weight (e.g., "Barlow Condensed Bold")
- License check (OFL, Apache, MIT — must be compatible with game license)
- Fallback font for missing glyphs

## Phase 3: Reference Gotchas

Before executing, check `references/art-pipeline-gotchas.md` for known failures matching this task type:
- **Gotcha A**: ComfyUI SD1.5 no real alpha → use chroma key pipeline
- **Gotcha B**: SD1.5 fails on flat 2D geometry on 4GB VRAM → use code
- **Gotcha C**: SaveAudioAdvanced dropped → use SaveAudio
- **Gotcha D**: /userdata single-segment only, EDITOR format ≠ API format
- **Gotcha E**: Stable Audio needs 3 exact config values
- **Gotcha F**: GIMP 3 script-fu brittle → use Pillow
- **Gotcha G**: Penpot MCP has 12 distinct traps
- **Gotcha H**: Measure artifacts, don't trust logs

## Reminder: AI for Concept, Not Shipping

**AI is for**:
- Concept exploration ("show me 5 visual directions for this boss")
- Texture generation (tileable surfaces, organic materials)
- Style-locking references ("this is the color treatment")
- Placeholder art during prototyping
- Cleanup assistance (background removal, upscaling)

**AI does NOT**:
- Preserve cross-frame consistency (animation, sprite sheets)
- Understand pivot points or atlas packing
- Maintain UI alignment across screen sizes
- Follow engine import constraints (poly count, texture size, material slots)
- Respect technical budgets (draw calls, VRAM, file size)

**Never ship raw AI output.** Every AI-generated asset must pass through:
1. Human review for technical correctness
2. Engine import validation (does it build?)
3. In-game observation (does it look right at play distance?)

## Phase 4: Environment Check

Before executing, verify the environment:

```sh
# Source art tools (required every session)
source tools/art/env.sh

# Verify tools available
command -v blender krita inkscape blockbench gimp-console-3.2

# Check Python + Pillow (GS_PYTHON is empty if the repo venv is not built)
[ -n "$GS_PYTHON" ] && $GS_PYTHON -c "from PIL import Image; print('Pillow OK')"

# Check ComfyUI (if needed)
curl -s http://localhost:8188/system_stats | head -n 5

# Check Penpot (if needed)
curl -s http://localhost:9001/health
```

If any check fails, see `docs/ART_TOOLCHAIN.md` for setup instructions.

## Phase 5: Execute and Validate

After producing the asset:
1. **Measure, don't trust logs** (Gotcha H)
2. Check file size against budget
3. Import into Unity and observe at game camera distance
4. Verify alpha channel (if required) via `$GS_PYTHON -c "from PIL import Image; img=Image.open('out.png'); print(img.mode)"`
5. Retain artifact in `assets/` with source files in `assets/.source/` (XCF, blend, svg)

## References

- `tools/art/env.sh` — Art tool PATH setup (source every session)
- `docs/ART_TOOLCHAIN.md` — Tool versions, install locations, verification
- `references/art-pipeline-gotchas.md` — All 8 validated failure modes and fixes
- `design/art/art-bible.md` — Visual identity constraints (if exists)
