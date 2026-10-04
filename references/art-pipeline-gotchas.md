# Art Pipeline Gotchas

Every failure, reproduction command, and fix from the art toolchain validation.

## A. ComfyUI SD1.5 Has No Real Alpha

**What failed**: Prompting "transparent background" in SD1.5 still produces solid backgrounds.

**Observation**: SD1.5 latent space has no alpha channel. "Transparent background" prompts produce white, gray, or off-white backgrounds, never true RGBA transparency.

**Fix**: Pipeline workaround —  
1. Generate with gray or neutral background color  
2. Chroma key via Pillow: find furthest color from all non-background blocks  
3. Export as PNG with alpha channel  
4. The neutral background MUST be far from every colour used in the block — if
   the background is close to any block colour, the chroma key eats that block
   too. Pick a background hue that appears nowhere in the palette.

**Reproduction**:
```python
# Prompt SD1.5 via ComfyUI API with "transparent background, isolated object"
# Result: image.png with RGB (255,255,255) or (240,240,240) bg, no alpha
```

---

## B. ComfyUI SD1.5 Fails on 4GB VRAM for Flat 2D Geometry

**What failed**: Four distinct flat-2D prompts failed on 4GB VRAM:
- Cuboid with shadow + emblem
- Device icon with sub-parts (button, screen, antenna)
- 15-frame chibi sprite sheet (front/side/back x 5 poses)
- Serif font rendering ("PRESS START" text as texture)

**Cause**: SD1.5 treats geometric primitives (square, cube, rectangle) as **physical 3D objects** with lighting/shadow/depth. A "flat square texture" prompt generates a photograph of a square object, not a 2D plane. 4GB VRAM blocks SDXL and Flux, which handle flat geometry better.

**Lesson**: **Geometry belongs in code, AI for texture and concept only.**  
Pillow can draw a 64×64 square in 3 lines. SD1.5 cannot.

**Impact on templates**: All 116 ComfyUI workflow templates use **new models only** (SDXL, Flux, Stable Audio). No SD1.5 template exists — projects needing SD1.5 must write API-format JSON workflows manually.

**Reproduction**:
```json
// ComfyUI API request for "flat blue square, 64x64, no shadow, solid color"
// Result on 4GB VRAM: OOM, or image of a 3D cube with lighting
```

---

## C. SaveAudioAdvanced COMBO_DYNAMICCOMBO_V3 Dropped

**What failed**: `SaveAudioAdvanced`'s `format` **input** is typed `COMBO_DYNAMICCOMBO_V3`. The API drops the dict sent for it, and the node then reports a missing/unusable parameter.

**Cause**: The `format` input's dynamic-combo type is not representable in an API-format workflow — the dict is silently discarded rather than validated.

**Fix**: Use `SaveAudio` node instead (stable, no dynamic combo issues).

**Reproduction**:
```python
# Workflow using SaveAudioAdvanced node
# POST to /prompt → 400 error: unsupported input type COMBO_DYNAMICCOMBO_V3
```

---

## D. /userdata Single-Segment Only, EDITOR Format Not API

**What failed**:
- `POST /userdata/subdir/file.json` → 405 Method Not Allowed  
- Copying EDITOR workflow JSON to API request → 400 parse errors

**Cause**:
- `/userdata/<file>` accepts single-segment paths only. Subdirectories require percent-encoding: `/userdata/subdir%2Ffile.json`
- EDITOR format is not API format — EDITOR JSON has UI metadata (node positions, colors); API format is bare node definitions

**Fix**:
- Flatten paths or percent-encode subdirs  
- Export "API format" from editor, not "Save Workflow"  
- Copying a workflow JSON into the `/userdata` directory does **not** make it appear in the UI — the server must be POSTed the API-format JSON.

**Reproduction**:
```sh
curl -X POST http://localhost:8188/userdata/a/b.json -d @workflow.json
# → 405

curl -X POST http://localhost:8188/userdata/a%2Fb.json -d @workflow.json
# → 200 (if workflow is API format)
```

---

## E. Stable Audio Needs 3 Things: CLIPLoader type, EmptyLatentAudio batch_size, VAE from Checkpoint

**What failed**:
- `CLIPLoader` with `type: "t5"` → 400 error (t5 not in valid set)
- `EmptyLatentAudio` with `batch_size: 4` → generation error
- Using `models/vae/vae-ft-mse-840000` for audio VAE → tuple index error

**Fix**:
1. **CLIPLoader `type: "stable_audio"`** — there are 29 valid clip types; `t5` is rejected, `stable_audio` is correct
2. **EmptyLatentAudio `batch_size: 1`** — Stable Audio does not support batching
3. **VAE from CheckpointLoaderSimple output[2]** — `models/vae/` only has image VAEs. Audio VAE comes from the checkpoint itself (output index 2)

**Reproduction**:
```python
# Wrong:
workflow = {
  "CLIPLoader": {"type": "t5"},  # 400 error
  "EmptyLatentAudio": {"batch_size": 4},  # generation fails
  "VAELoader": {"vae_name": "vae-ft-mse-840000"}  # tuple index error on audio decode
}

# Correct:
workflow = {
  "CLIPLoader": {"type": "stable_audio"},
  "EmptyLatentAudio": {"batch_size": 1},
  # VAE from CheckpointLoaderSimple node output[2], not VAELoader
}
```

---

## F. GIMP 3 Script-Fu Has 4 Conditions

**What failed**: GIMP 3.2 script-fu batch commands failed with:
- Missing `--batch-interpreter` → script not executed
- Multiple `-b` flags → only last one runs
- `gimp-image-width` → "undefined procedure" error
- `(if (defined? 'var) ...)` → TinyScheme parse error

**Fix**:
1. **`--batch-interpreter plug-in-script-fu-eval` required** — without it, `-b` is ignored
2. **Load and call in same `-b` expression** — each `-b` is a separate eval with no shared state
3. **GIMP 3 API renames**: `gimp-image-width` → `gimp-image-get-width`, `gimp-image-height` → `gimp-image-get-height`
4. **TinyScheme has no `defined?` or `eval`** — use `(catch ...)` for optional checks

**Conclusion**: **Use Pillow for alpha extraction instead.** Each GIMP launch costs
~30 s (startup + Script-Fu init), so probing procedure names one at a time is
prohibitively slow — that is *why* Pillow wins for alpha.

**Reproduction**:
```sh
# Wrong:
gimp-console-3.2 -i -b '(gimp-image-width 1)' -b '(gimp-quit 0)'
# → "undefined procedure gimp-image-width"

# Correct:
gimp-console-3.2 --batch-interpreter plug-in-script-fu-eval \
  -b '(let* ((img (car (gimp-file-load RUN-NONINTERACTIVE "input.png" "input.png")))) \
        (gimp-image-get-width img))' \
  -b '(gimp-quit 0)'
```

---

## G. Penpot MCP Traps (12 Distinct Issues)

**What failed**: Multiple Penpot MCP integration failures during UI design automation:

1. **`createText()` requires `text` argument** — omitting it → 400 error
2. **`appendChild` MUST come BEFORE `resize`/`setFills`** — reverse order → flex layout stretches text to 952px instead of 440px, labels gain +64px height
3. **GridLayout `columns`/`rows` are read-only** — direct assignment fails; must use `addColumn(width)`/`addRow(height)`
4. **Frozen shape objects** — `shape._flex = {...}` fails silently; must use closure or method
5. **Font via `fontFamily` + `fontWeight` + `fontVariantId`** — `fontId` is rejected, `fontStyle` only accepts `normal`/`italic`
6. **Font family mismatch**: "Barlow" → "Barlow Condensed" has 18 variants; wrong family = wrong weight
7. **`x` is PAGE-ABSOLUTE, `parentX` is relative** — don't double-count `board.x` offset
8. **Text width via `textBounds.width`, not `shape.width`** — `shape.width` is +1px for antialiasing
9. **`createShapeFromSvg` loses `font-family`** — text-as-SVG imports as paths, not text; use `createText` instead
10. **Plugin tab suspend → no heartbeat for 30s** — MCP server times out; keep tab active or restart
11. **Export one board via `export_shape`** — whole-page export (8 boards, 1080×1920 each) → 500ms timeout
12. **MCP tool changes need agent restart** — hot reload doesn't re-register tools

**Reproduction**: No reproduction commands (see list above for 12 observed traps).

---

## H. Principle: Don't Trust Logs, Measure Artifacts

**What failed**: Three separate design checkers reported **69 → 32 → 0 issues** on the **same unchanged design file**.

**Cause**: Checkers used different heuristics, log parsing, or AI scoring — none measured the actual artifact.

**Lesson**: **Separate MEASURE from VERDICT.**
- **MEASURE**: count pixels, parse SVG, extract font metrics, check file size  
- **VERDICT**: compare measurement to spec

A checker that both measures and judges will drift when the LLM re-reasons the rule. A checker that only measures is a stable contract.

**Example**:
```python
# Wrong (log-based verdict):
if "warning" in log_output:
    return "FAIL"

# Correct (artifact measurement):
text_width = shape.textBounds.width
if text_width > 440:
    return f"FAIL: text width {text_width}px exceeds 440px"
```

---

## Summary

- **A**: SD1.5 has no real alpha → chroma key pipeline
- **B**: SD1.5 can't do flat 2D on 4GB VRAM → geometry in code, AI for texture
- **C**: SaveAudioAdvanced dropped → use SaveAudio
- **D**: /userdata single-segment, EDITOR ≠ API format
- **E**: Stable Audio needs 3 exact config values
- **F**: GIMP 3 script-fu is brittle → use Pillow
- **G**: Penpot MCP has 12 distinct traps
- **H**: Measure artifacts, don't trust logs
- **6**: Blending cannot fix a seam — generate periodicity instead
- **7**: A metric that never moves with the input measures the transform

---

## 6. Seam Fixing by Post-Process Is Meaningless — Generate Periodicity Instead

**What failed**: six attempts to *fix* a non-periodic board-surface texture so its
edges tile cleanly. Scores are mean edge mismatch (lower = better; ~0 = perfect):

| attempt | seam score |
|---|---|
| affine half-shift blend | 47.5 |
| mirror-quadrant | 74.3 |
| 4-way kaleidoscope | 22.4 |
| roll cross-fade | 37.1 |
| gaussian feather | 37.1 |

**Root cause**: blending mixes pixel values but **cannot make two different edges
equal** — the average of two different values equals neither. Blending can only
move the seam; it can never erase it. Any post-process that keeps both original
edges somewhere in the tile leaves a boundary where they meet.

**Correct method**: **value noise with lattice indices taken modulo the cell
count.** The lattice wraps, so column `n` is by construction the same lattice cell
as column `0` — the tile is periodic *by definition*, before any blending. No seam
exists to fix.

**Also**: when mirroring a texture, take the **centre window of the kaleidoscope**,
not the corner quadrant. The corner quadrant **is the original image unchanged**, so
the "fix" does nothing — a classic silent no-op.

**Reproduction** (repo script `tools/art/seam_demo.py`, run with `$GS_PYTHON`
from the repo root; uses only Pillow + numpy):

Demonstration on one 128×128 random-noise tile:
```
=== SECTION 6: seam fixing by post-process ===
non-periodic noise tile      left-vs-right/top-vs-bottom mismatch = 92.65
  after naive roll+cross-fade                                     = 72.36
modulo-lattice value noise (periodic by construction)             = 0.88

reference naive variants on the same tile:
  half-shift (no blend) mismatch     = 88.59
  mirror-quadrant seam (kernel)      = 45.20
  kaleidoscope (min) seam            = 35.65
```
**Read**: the naive roll + cross-fade fix moves the score from **92.65 → 72.36** —
it *helps* but **does not reach** the periodic tile's **0.88**. The naive fix leaves
a 72-point mismatch; the modulo-lattice tile has essentially none. The claim is
confirmed on a live measurement: post-process blending is not a real fix, generating
periodic noise is.

The kernel snippets that matter:
```python
# periodic value noise — the modulo IS the periodicity
y0 = np.floor(ys).astype(int) % cells
x0 = np.floor(xs).astype(int) % cells
y1 = (y0 + 1) % cells
x1 = (x0 + 1) % cells
```
```python
# the wrong fix — blend two different edges; the average equals neither
left[:, x] = (1 - t) * roll_img[:, x] + t * shifted[:, x]
```
The 3×3 rendered tiles are written to `art-workspace/work/tmp/seam_seated_3x3.png`
and `art-workspace/work/tmp/seam_seamed_3x3.png` — repeat the tile 3×3 and
**look** at it; the seam is obvious to the eye and invisible to a transform-side
metric.

---

## 7. A Metric That Never Changes When the Input Changes Is Measuring the Transform, Not the Subject

**What failed**: a seam metric returned **0.0 (perfect) for EVERY input** — including
a texture with an obvious seam. The metric computed the mismatch **after mirroring
the image**, and mirroring *guarantees* the two centre columns are equal. So the
metric was measuring the mirror operation, not the texture.

**Fix**: take the control from the artifact's **INTERIOR** — e.g. the median of all
adjacent-column steps in the original image — not from the transform you just
applied. A control drawn from the transform will always agree with the transform.

**Cheap general method**: render the tile repeated **3×3 and look at it**. The eye
does not get fooled by the algebra.

**Same trap for geometry checkers**: if the error count changes when you change the
**checker** but not the design, the **checker is wrong** — do not edit the design to
satisfy the checker. (This is the §H principle applied to seams: MEASURE ≠ VERDICT.)

**Reproduction** (same `tools/art/seam_demo.py`):

```
=== SECTION 7: a metric that never changes is measuring the transform ===
seated (periodic)    buggy_metric=0.00   corrected: interior_median=4.0 wrap_seam=0.89
seamed (hard step)   buggy_metric=0.00   corrected: interior_median=3.0 wrap_seam=87.92
```

**Read**: the buggy metric reports **0.00 for both** the seated (periodic) tile and
the seamed tile — identical output despite a 120-level hard step being introduced.
The corrected interior-based metric distinguishes them cleanly:
`wrap_seam` **0.89** (seated) vs **87.92** (seamed), ~100× apart, while the interior
median stays ~3–4 (as it should — a hard step is a boundary feature, not a change
in interior texture).

The bug and the fix, side by side:
```python
def buggy_metric(a):
    m = np.hstack([a, a[:, ::-1]])          # mirror -> centre columns forced equal
    c = m.shape[1] // 2
    return float(np.abs(m[:, c-1].astype(np.int32) - m[:, c].astype(np.int32)).mean())

def corrected_metric(a):
    interior = float(np.median(np.abs(np.diff(a.astype(np.int32), axis=1))))
    wrap = float(np.abs(a[:, 0].astype(np.int32) - a[:, -1].astype(np.int32)).mean())
    return interior, wrap                     # control taken from the artifact itself
```
