# Tool Gotchas — Headless Art Toolchain, Verified On This Machine

Every section below was **executed on this workstation** (Windows 11, Git Bash,
2026-10-03) unless it is explicitly marked **UNVERIFIED**. Where a claim could not
be exercised, the section says what was attempted and why it failed — no claim is
presented as fact without a raw command and its raw output.

Machine: `Windows_NT BenHan 10.0 26300 x86_64 MS/Windows`. Shell: Git Bash
(MINGW64). Repo: `C:/Users/bx9ga/Documents/GitHub/Claude-Code-Game-Studios-Origin`.

Always: `source tools/art/env.sh` first. `$GS_PYTHON` = `.venv/Scripts/python.exe`
(Pillow 12.3.0, numpy 2.5.3).

---

## A. GIMP 3 script-fu needs 4 exact conditions

**Claim tested**: (1) `--batch-interpreter plug-in-script-fu-eval` is mandatory;
(2) load + call in the SAME `-b`; (3) `gimp-image-width` renamed to
`gimp-image-get-width`; (4) TinyScheme has neither `defined?` nor usable dynamic
`eval`. Conclusion: use Pillow for alpha work; each GIMP launch is ~5–30 s.

**Test input** (Pillow, no GIMP involved):
```sh
"$GS_PYTHON" -c "from PIL import Image, ImageDraw; im=Image.new('RGBA',(96,64),(40,90,160,255)); d=ImageDraw.Draw(im); d.rectangle([10,10,50,40],fill=(230,180,40,255)); im.save('art-workspace/work/probe_gimp_in.png')"
# wrote (96, 64) RGBA
```

**Working call** (load a PNG and print its width):
```sh
timeout 110 "C:/Users/bx9ga/AppData/Local/Programs/GIMP 3/bin/gimp-console-3.2.exe" \
  --batch-interpreter plug-in-script-fu-eval \
  -b '(let* ((img (car (gimp-file-load RUN-NONINTERACTIVE "art-workspace/work/probe_gimp_in.png" "probe_gimp_in.png")))) (gimp-message (string-append "WIDTH=" (number->string (car (gimp-image-get-width img))))) (gimp-image-delete img))' \
  -b '(gimp-quit 0)'
```
Raw output (elapsed ~13 s):
```
GIMP-Message: Welcome to GIMP 3.2.6!

script-fu.exe-Warning: WIDTH=96

batch command executed successfully
EXIT=0
```

**Condition 1 — the interpreter flag is mandatory.**
```sh
timeout 110 <gimp-console> -b '(gimp-message "HELLO-NO-INTERP")' -b '(gimp-quit 0)'
```
Raw output:
```
GIMP-Message: Welcome to GIMP 3.2.6!

No batch interpreter specified.

Available interpreters are:
- plug-in-script-fu-eval (Script-fu (scheme))
- python-fu-eval (Python 3)

Specify one of these interpreters as --batch-interpreter option.
```
Note: GIMP then **hangs** (no `gimp-quit` executed) — the command had to be killed
after the 300 s shell cap. So a wrong invocation is not merely ignored: it leaves a
process alive. Always wrap this tool in `timeout`.

**Condition 3 — the rename is real.**
```sh
timeout 110 <gimp-console> --batch-interpreter plug-in-script-fu-eval \
  -b '(gimp-message (number->string (car (gimp-image-width 1))))' -b '(gimp-quit 0)'
```
Raw output:
```
batch command experienced an execution error:
Error: eval: unbound variable: gimp-image-width
Stopping at failing batch command [0]: (gimp-message (number->string (car (gimp-image-width 1))))
```
It is not "undefined procedure" but **`unbound variable`** in 3.2.6 — the symbol
does not exist at all. Same rename applies to height (`gimp-image-get-height`).

**Condition 2 — separate `-b` flags share NO state.**
```sh
timeout 110 <gimp-console> --batch-interpreter plug-in-script-fu-eval \
  -b '(define img (car (gimp-file-load RUN-NONINTERACTIVE "art-workspace/work/probe_gimp_in.png" "p.png")))' \
  -b '(gimp-message (number->string (car (gimp-image-get-width img))))' \
  -b '(gimp-quit 0)'
```
Raw output:
```
batch command executed successfully
batch command experienced an execution error:
Error: eval: unbound variable: img
Stopping at failing batch command [1]
```
Each `-b` is a fresh eval; `define` in one is invisible in the next. Load and use
must therefore live in ONE expression (use `let*`).

**Condition 4 — TinyScheme `defined?` and `eval`.**
```sh
# defined?
timeout 45 <gimp-console> --batch-interpreter plug-in-script-fu-eval \
  -b '(gimp-message (if (defined? (quote x)) "yes" "no"))' -b '(gimp-quit 0)'
# script-fu.exe-Warning: no
```
So `(defined? 'x)` **does not error** — but it always answers `no` even for a bound
symbol in this TinyScheme, so it is useless as an existence test in a batch. This
**corrects** the older note that said `defined?` is a "parse error".

```sh
# eval
timeout 45 <gimp-console> --batch-interpreter plug-in-script-fu-eval \
  -b '(gimp-message (number->string (eval (list (quote +) 2 3))))' -b '(gimp-quit 0)'
# script-fu.exe-Warning: 5
```
`eval` **does exist** and works dynamically (`(procedure? eval)` → `eval-is-proc`).
The trap is not that `eval` is missing — it is that the first attempt
`(gimp-message (eval ...))` failed with
`expected type: string for argument 1 to gimp-message` because `eval` returned a
*number* and Script-Fu does no implicit coercion. Wrap in `number->string`.

**Side-observation (real, and worth knowing)**: on *execution errors* GIMP 3.2.6
`gimp-console` prints `fatal error: GIMP crashed` and exits by signal rather than
returning an exit code — e.g. after the `gimp-image-width` and split-`-b` errors
above. The healthy path returns `EXIT=0` cleanly. So "GIMP crashed" in the log can
simply mean "a batch expression errored".

**Conclusion**: GIMP script-fu works, but every condition must be exact, and the
tool costs seconds-to-minutes per launch. For alpha/pixel work use Pillow.

---

## B. ComfyUI SD1.5 has no real alpha — chroma key is a separate stage

**Claim tested**: a "transparent background" prompt still yields a solid background;
alpha is a pipeline stage (neutral bg → chroma key → prep), and the background must
be far from every block colour. The generation-dependent half of this cannot be
tested here (see constraint: no generation). The **structural** half *can* be, and
was.

**Test — does the installed ComfyUI have any alpha-producing or background-removal
node?**
```sh
curl -sS http://127.0.0.1:8188/object_info | python -c "
import sys,json
d=json.load(sys.stdin)
print('alpha/rgba nodes:', [k for k in d if 'Alpha' in k or 'RGBA' in k or 'rgba' in k])
print('rembg/chroma:', [k for k in d if any(s in k.lower() for s in ['rembg','chroma','key','matte','segment'])][:20])
print('total node classes:', len(d))
"
```
Raw output:
```
alpha/rgba nodes: ['SplitImageWithAlpha', 'JoinImageWithAlpha', 'CLIPTextEncodePixArtAlpha']
rembg/chroma: ['LTXVAddGeneratedKeyframes', ... 'TripoSegmentNode', 'TripoSmartSegmentNode']
total node classes: 970
```
Across **970 node classes** there is `SplitImageWithAlpha` / `JoinImageWithAlpha`
(these *consume/produce a MASK* — they do not invent alpha from a render) and no
`rembg` / background-removal / chroma-key node. So the graph itself offers no node
that turns a generated RGB image into an alpha image: **alpha must be added by an
external stage** (Pillow), consistent with the claim.

**Corroborating structural fact** — `CheckpointLoaderSimple` model list on this
machine contains no latent-space model with an alpha channel:
```sh
curl -sS 'http://127.0.0.1:8188/object_info/CheckpointLoaderSimple' | grep -o '"ckpt_name": \[\[[^]]*\]'
# "ckpt_name": [["dreamshaper8_pruned.safetensors", "sd_turbo.safetensors", "stable-audio-open-1.0.safetensors", "stable_audio_3_small_sfx.safetensors", "yue2_3b_int8_convrot.safetensors"]
```

**The prompt-to-output half — UNVERIFIED — not run.** A generation was explicitly
out of scope (4 GB VRAM). The claim "a 'transparent background' prompt still yields
a solid RGB background" is therefore *not independently reproduced here*; it is
carried by the node-inventory evidence above (nothing in the graph can emit alpha)
plus the prior note. Re-run only on a machine where a generation is acceptable.

---

## C. ComfyUI SD1.5 fails flat-2D on 4 GB VRAM; no SD1.5 template exists

**Claim tested**: the bundled template gallery has **no SD1.5 template**; all
templates use newer models.

**Test** — query the gallery through the `comfyui` MCP tool `search_templates`:

| query | `total` |
|---|---|
| `stable diffusion` | 0 |
| `sd15` | 0 |
| `sd1.5` | 3 (none are SD1.5 — see below) |
| `text2image` | 0 |

The `sd1.5` hits are keyword noise, not SD1.5 templates — full raw rows:
```json
"total": 3, "shown": 3,
rows: [ image_lotus_depth_v1_1 ("Depth Estimation: Lotus"),
        templates_purz_animatediff_simple_weighted_ipadapters_looping_animation,
        templates_mjm_Injected ("Noise Injected VideoGen") ]
```
None of the three is a Stable Diffusion 1.5 text-to-image workflow. For scale, the
same tool returns `image` → 484, `flux` → 42, `audio` → 82, `sdxl` → 6 rows.

**Additional local evidence**: no SD1.5 checkpoint is installed at all —
`find <ComfyUI-Desktop> -iname '*v1-5*' -o -iname '*sd15*' -o -iname '*sd1.5*'`
returned nothing; `CheckpointLoaderSimple` lists only SDXL-lineage
(`dreamshaper8_pruned`, `sd_turbo`) plus audio models.

**The "SD1.5 draws cubes with shadows" half — UNVERIFIED — not run** (no generation).
The template-absence and checkpoint-absence claims are verified above.

---

## D. ComfyUI `SaveAudioAdvanced` is unusable via the API

**Claim tested**: `format` is typed `COMBO_DYNAMICCOMBO_V3`; the dict is dropped and
the node reports a missing/unusable parameter → use `SaveAudio`.

**Evidence 1 — the declared type.**
```sh
curl -sS http://127.0.0.1:8188/object_info/SaveAudioAdvanced
```
Raw (excerpt):
```json
{"SaveAudioAdvanced": {"input": {"required": {
  "audio": ["AUDIO", ...],
  "filename_prefix": ["STRING", ...],
  "format": ["COMBO_DYNAMICCOMBO_V3", {"tooltip": "The file format...",
     "options": [{"key":"flac","inputs":{"required":{}}},
                 {"key":"mp3","inputs":{"required":{"quality":[...]}}},
                 {"key":"opus","inputs":{"required":{"quality":[...]}}}]}]}, ...
```

**Evidence 2 — actual execution.** Submitting an API graph
`EmptyAudio → SaveAudioAdvanced` three ways:
```sh
EMPTY='"1":{"class_type":"EmptyAudio","inputs":{"channels":1,"duration":0.2,"sample_rate":44100}}'
# A: format as dict   {"format":"flac"}
# B: format as string "flac"
# C: no format key
# D: same graph into SaveAudio
```
All four **passed `/prompt` validation** and returned a `prompt_id`. But history
for A and C:
```
execution_error  node_type SaveAudioAdvanced
exception_message: "SaveAudioAdvanced.execute() missing 1 required positional argument: 'format'"
exception_type: TypeError
```
while B (`format: "flac"`) succeeded:
```
status success completed True
```
and D (`SaveAudio`) succeeded.

**Reading**: the node's `format` is a dynamic combo whose value the API layer
discards — so at execute time `format` is absent and the node raises `TypeError`.
The **string** form `"format": "flac"` passes through and works; the **dict** form
and the **absent** form both fail at execution. Either way `SaveAudio` is the safe
choice, as claimed. (The older note's "400 unsupported input type" is imprecise —
validation passes; the failure is at execution. Corrected here from the raw trace.)

---

## E. ComfyUI Stable Audio needs 3 things

**Claim tested**: `CLIPLoader` type must be `stable_audio`; `EmptyLatentAudio`
`batch_size` = 1; the audio VAE comes from `CheckpointLoaderSimple` output 2, since
`models/vae/` has no audio VAE.

**Test 1 — CLIPLoader valid types.**
```sh
curl -sS http://127.0.0.1:8188/object_info/CLIPLoader
```
Raw (excerpt):
```json
"type": [["stable_diffusion","stable_cascade","sd3","stable_audio","mochi","ltxv",
          "pixart","cosmos","lumina2","wan","hidream","chroma","ace","omnigen2",
          "qwen_image","hunyuan_image","flux2","ovis","longcat_image","cogvideox",
          "lens","pixeldit","ideogram4","boogu","krea2","joyimage","mage","minimax","yue2"]]
```
`stable_audio` **is** in the list. There is no `type: "t5"` option — `t5` appears
only as a *model filename* (`"clip_name": ["t5-base.safetensors", ...]`), which is
exactly the confusion the claim warns about: `t5` is not a loader *type*.

**Test 2 — EmptyLatentAudio**:
```sh
curl -sS http://127.0.0.1:8188/object_info/EmptyLatentAudio
# "seconds": ["FLOAT", {"default":47.6,"min":1.0,"max":1000.0,"step":0.1}]
# "batch_size": ["INT", {"default":1,"min":1,"max":4096}]
```
`batch_size` default is **1**, min 1 (no `max:1`), so batching is not structurally
forbidden, but the default matches the claim.

**Test 3 — VAELoader has no audio VAE.**
```sh
curl -sS http://127.0.0.1:8188/object_info/VAELoader | grep -o '"vae_name": \[\[[^]]*\]'
# "vae_name": [["vae-ft-mse-840000.safetensors", "pixel_space"]
```
Only an image VAE and `pixel_space` are offered — no audio VAE. Meanwhile
`VAEDecodeAudio` exists and consumes a VAE:
```sh
# VAEDecode output: ["IMAGE"]  (image decoder)
# and among 970 classes: VAEDecodeAudio ['AUDIO'], VAEDecodeAudioTiled ['AUDIO']
```
So an audio VAE must be sourced from the audio checkpoint (`CheckpointLoaderSimple`
output 2) rather than a standalone `VAELoader`, as claimed — consistent with
`stable-audio-open-1.0.safetensors` and `stable_audio_3_small_sfx.safetensors`
being present as checkpoints.

**The end-to-end audio generation — UNVERIFIED — not run** (no generation allowed).

---

## F. ComfyUI `/userdata`: single path segment, EDITOR format, must POST

**Claim tested**: `/userdata/a/b.json` → 405; percent-encoded subdirs work; a file
copied into the dir does not appear in the UI, it must be POSTed.

**Test**:
```sh
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' -X POST -H 'Content-Type: application/json' \
  -d '{"nodes":[]}' http://127.0.0.1:8188/userdata/a/b.json          # subdir
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' -X POST -H 'Content-Type: application/json' \
  -d '{"nodes":[]}' 'http://127.0.0.1:8188/userdata/a%2Fprobe_b.json' # percent-encoded
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' -X POST -H 'Content-Type: application/json' \
  -d '{"nodes":[]}' http://127.0.0.1:8188/userdata/probe_b.json       # single segment
```
Raw output:
```
### POST /userdata/a/b.json (subdir)                  HTTP 405
### POST /userdata/probe%2Fb.json (percent-encoded)   HTTP 200
### POST /userdata/probe_b.json (single segment)      HTTP 200
```
**Confirmed**: a raw subdir path is rejected `405`; percent-encoding the separator
(`%2F`) is accepted. The server then wrote the files here
(`find "$LOCALAPPDATA" -name 'probe_b.json'`):
```
.../ComfyUI/user/default/a/probe_b.json
.../ComfyUI/user/default/probe_b.json
```

**UI-visibility / format caveats — UNVERIFIED — not exercised.** Testing "copy a
file in and it does not show in the UI" and "EDITOR ≠ API format" requires driving
the GUI, which is out of scope here. The 405 behaviour above is verified; the rest
of the claim is carried from the prior note.

---

## G. ComfyUI YuE2 is blocked locally; the HF URLs in the note 401/404

**Claim tested**: template `audio_yue2_music_cover` needs
`sheetsage2_bf16.safetensors` + `yue2_3b_int8_convrot.safetensors`; HF returns 401;
Stable Audio (keyless) is the fallback.

**Test 1 — the template exists and what it reports.**
```sh
$GS_PYTHON tools/mcp-servers/smoke.py comfyui --call search_templates --args '{"query":"yue"}'
# rows: audio_yue2_music_cover ("YuE2: Music Cover"), audio_yue2_text2music
$GS_PYTHON tools/mcp-servers/smoke.py comfyui --call get_template --args '{"name":"audio_yue2_music_cover"}'
```
Raw `local_check`:
```json
{"checked": true, "runnable": false,
 "summary": "1 problem(s): ... node 33/43: 'sheetsage2_bf16.safetensors' is unavailable:
             the server reports 0 installed options for audio_encoder_name",
 "error_count": 1}
```
So the template is **present but not runnable** on this install — exactly the claim.

**Test 2 — the URLs.** The exact URLs named in the prior note:
```sh
curl -sS -o /dev/null -w '%{http_code}\n' \
  "https://huggingface.co/ai4b00/sheetsage2/resolve/main/sheetsage2_bf16.safetensors"   # 401
curl -sS -o /dev/null -w '%{http_code}\n' \
  "https://huggingface.co/multimodalart/yue2/resolve/main/yue2_3b_int8_convrot.safetensors"  # 401
```
Raw:
```
sheetsage2 401
yue2 401
```
**But** the 401 here is because those two repos do not exist / are wrong — a 401 on
a non-existent HF path is the anonymous-access response. The **real** files live
elsewhere, and were located:
```sh
curl -sS "https://huggingface.co/api/models/Comfy-Org/YuE2?blobs=true"
# gated: False
#   audio_encoders/sheetsage2_bf16.safetensors
#   checkpoints/yue2_3b_bf16.safetensors
#   checkpoints/yue2_3b_int8_convrot.safetensors
curl -sSL -o /dev/null -w 'HTTP %{http_code}\n' -r 0-0 \
  "https://huggingface.co/Comfy-Org/YuE2/resolve/main/audio_encoders/sheetsage2_bf16.safetensors"
# HTTP 206   (range request succeeds — file is public, not gated)
```
`m-a-p/SheetSage2` exists (`gated: False`) but has **no** `sheetsage2_bf16.safetensors`
at its root → `HTTP 404` for `m-a-p/SheetSage2/resolve/main/sheetsage2_bf16.safetensors`.

**Corrected conclusion**: YuE2 is blocked **by missing local model files**, not by a
HuggingFace 401 — `Comfy-Org/YuE2` is public and its two files download with no
token. The fix is to fetch them (or use the keyless Stable Audio checkpoints, which
are already installed: `stable-audio-open-1.0`, `stable_audio_3_small_sfx`). The
"401" in the original note came from probing two URLs that do not exist.

---

## H. ComfyUI background runner and `stdin is not a tty`

**Claim tested**: the background runner needs a real stdin; run foreground with
`< /dev/null`.

**What could be verified here**: the `comfy` CLI and its `launch --background` flag
exist, and non-tty stdin is detectable.
```sh
timeout 60 .venv/Scripts/comfy.exe --version
# {"schema":"envelope/1","type":"envelope","ok":true,"command":"version","version":"1.22.0",...}
timeout 60 .venv/Scripts/comfy.exe launch --help
# Usage: comfy launch [OPTIONS] [extra]...
#   --background  --no-background   Launch ComfyUI in background  [default: no-background]
```
Non-tty detection is real:
```sh
echo | python -c "import sys;print('isatty',sys.stdin.isatty())"   # isatty False
python -c "import sys;print('isatty',sys.stdin.isatty())"          # isatty True (pty)
```
The comfy CLI guards exactly this:
```
.venv/Lib/site-packages/comfy_cli/command/run/__init__.py:105:
  ``sys.stdin.isatty()`` assumes stdin is a live stream, but in detached /
  ... :112:  return stream_is_tty(getattr(sys, "stdin", None))
```
`comfy launch --help < /dev/null` and `comfy launch --help 0<&-` both returned the
usage text (exit 1, help path), i.e. a redirected stdin does not break the CLI.

**The exact `stdin is not a tty` failure — UNVERIFIED — not reproduced.** The string
`stdin is not a tty` does not occur in `comfy_cli` nor under `references/`,
`tools/`, `docs/` (grep, no matches). A recursive grep over the whole
`Comfy-Desktop/ComfyUI-Installs` tree did not finish before the 300 s shell cap, so
the install tree was only partially searched — the absence is confirmed for the CLI
and the repo, and *not fully* confirmed for the ComfyUI source tree. It is a
Python-`termios`/`getpass`-style message from another launcher, not this CLI, so
there is nothing here to reproduce. The `< /dev/null` workaround is stated as a
technique, not as a verified failure on this machine.

---

## I. numpy 2.x removed `ndarray.ptp()`

**Claim tested**: `arr.ptp()` is gone; use `np.ptp(arr)`.

**Test**:
```sh
"$GS_PYTHON" -c "import numpy as np; a=np.array([1,3,2]); print('np.ptp =', np.ptp(a));
try:
    a.ptp()
except Exception as e:
    print('arr.ptp ->', type(e).__name__, ':', e)
print('numpy', np.__version__)"
```
Raw output:
```
np.ptp = 2
arr.ptp -> AttributeError : 'numpy.ndarray' object has no attribute 'ptp'
numpy 2.5.3
```
**Confirmed** exactly. `np.ptp(a)` works; the method is gone on numpy 2.5.3.

---

## J. Penpot MCP API traps

**UNVERIFIED — Penpot MCP server not running on 4401.** Confirmed down:
```sh
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' --max-time 5 http://127.0.0.1:4401/mcp
# curl: (7) Failed to connect to 127.0.0.1:4401 after 2025 ms: Could not connect to server
# HTTP 000
```
None of the 13 traps below could be exercised. They are retained **verbatim as a
checklist**, not as verified facts:

1. `createText()` requires the `text` argument — omitting it → 400.
2. `appendChild` MUST come BEFORE `resize()`/`fills`, else flex stretches text to
   **952 px** instead of **440 px**.
3. `GridLayout.columns` / `.rows` are **read-only** — use `addColumn('fixed', px)` /
   `addRow(...)`.
4. Shapes are **frozen objects** — `shape._flex = {...}` fails silently; use a
   closure or a method.
5. Font via `fontFamily` + `fontWeight`; `fontId` is rejected; `fontStyle` accepts
   only `normal`/`italic`.
6. `alignItems` accepts only `center` | `stretch`, while `justifyContent` accepts
   `flex-start` / `flex-end` / `space-between`.
7. `addFlexLayout()` works only on a **BOARD**.
8. Grid padding sizes the box but does **not** move the child.
9. `shape.x` is **page-absolute**; `shape.parentX` is relative.
10. Text width via `textBounds.width` (never `shape.width`).
11. `createShapeFromSvg` **loses `font-family`**.
12. The plugin runs in a browser tab: suspend → no heartbeat → MCP call fails.
13. MCP tool changes need an **agent restart** (hot reload does not re-register).

---

## K. Penpot export must go through MCP, not HTTP

**UNVERIFIED — Penpot MCP server not running on 4401** (see J for the connection
refusal). The claim — `mcp__penpot__export_shape` returns `MEDIA:<path>` (a real PNG
on disk); `/api/export` is a dead end (400 missing `:cmd`, guessed RPCs 404); batch
via `shape.metadata.exports = [{type:'png', scale:1}]`; the Penpot HTTP token lives
in the Postgres `access_token` table where `type='mcp'` and `file` has no
`storage_id` — is retained as an unverified checklist. No Penpot HTTP endpoint was
probed because none is reachable.

---

## L. Inkscape 1.x for SVG checking, not bulk PNG export

**Claim tested**: `--export-type=png --export-filename=out.png` works headless;
`--query-all` gives shape bboxes; `--export-id=<id>` exports one shape. The font
question (does CLI handle a `font-family` outside its list?) was tested.

**Input** — a multi-shape SVG with a deliberately unknown font:
```svg
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="120" viewBox="0 0 200 120">
  <rect id="rectA" x="10" y="10" width="60" height="40" fill="#205aa0"/>
  <circle id="circleB" cx="140" cy="40" r="28" fill="#e0b428"/>
  <path id="triC" d="M20 110 L80 70 L110 110 Z" fill="#40a060"/>
  <text id="txtD" x="12" y="60" font-family="NoSuchFontXYZ" font-size="16" fill="#000">FontProbe</text>
</svg>
```

**Version**:
```sh
timeout 60 "C:/Program Files/Inkscape/bin/inkscape.com" --version
# Inkscape 1.4.4 (dcaf3e7, 2026-05-05)
```

**Export**:
```sh
timeout 90 <inkscape.com> --export-type=png \
  --export-filename=art-workspace/work/probe_inkscape_out.png \
  art-workspace/work/probe_inkscape_in.svg
# EXIT=0; output 3317 bytes, 200x120
```

**`--query-all`** (the fast way to check geometry without rendering):
```sh
timeout 90 <inkscape.com> --query-all art-workspace/work/probe_inkscape_in.svg
```
Raw:
```
svg1,10,10,158,100
rectA,10,10,60,40
circleB,112,12,56,56
triC,20,70,90,40
txtD,13.5625,47.8438,78.2891,12.3984
```

**`--export-id`** (single shape):
```sh
timeout 90 <inkscape.com> --export-id=rectA --export-id-only --export-type=png \
  --export-filename=art-workspace/work/probe_inkscape_id.png art-workspace/work/probe_inkscape_in.svg
# Exporting only object with id="rectA"; all other objects hidden.
# EXIT=0; output 194 bytes
```

**Font question — answered.** The SVG asks for `font-family="NoSuchFontXYZ"`, which
is not installed. Inkscape did **not** error, and it **did render text**: counting
dark pixels in the `txtD` region of the PNG gave `505` dark pixels — the glyphs are
present. Inkscape substituted a fallback font (glyph advances match a sans face:
`textBounds` width 78.29 at size 16). **So: an unknown `font-family` is silently
substituted, not dropped and not raised.** Anything that depends on *which* font was
used (metrics, exact widths) is therefore unreliable headless — always query
`textBounds.width`/`--query-all` rather than assuming the requested metrics.

**Performance caveat — UNVERIFIED.** "Slow for a whole page of shapes" was not
benchmarked here (the probe is 4 shapes). It is carried as a caution, not a
measurement.

---

## M. Krita 5.x CLI is very limited

**Claim tested**: `krita --export` is not a complete command; the export form exists
but takes no Python scripting; conclusion — Krita is for the human artist.

**Version** (with timeout — never block on a GUI binary):
```sh
timeout 60 "C:/Program Files/Krita (x64)/bin/krita.exe" --version
# krita 5.3.4 (git c5b23e3)
```

**Full `--help` option list** (raw, complete):
```
-v, --version                                Displays version information.
-?, -h, --help                               Displays help on commandline options.
--help-all                                   Displays help including Qt specific options.
--template                                   Open a new document with a template
--new-image <colorspace,depth,width,height>  Create a new image.
--workspace <workspace>                      The name of the workspace to open Krita with
--windowlayout <windowlayout>                The name of the window layout to open Krita with
--load-session <load-session>                The name of the session to open Krita with
--canvasonly                                 Start Krita in canvas-only mode
--nosplash                                   Do not show the splash screen
--fullscreen                                 Start Krita in full-screen mode
--export                                     Export to the given filename and exit
--export-sequence                            Export animation to the given filename and exit
--export-filename <filename>                 Filename for export
--file-layer <file-layer>                    File layer to be added to existing or new file
--resource-location <file-layer>             A location that overrides the configured
                                             location for Krita's resources
Arguments: [file(s)]                         File(s) or URL(s) to open
```

**Reading**:
- `--export` alone is incomplete: it **requires** `--export-filename <filename>`.
- There is **no** `--script`, no `--run-python`, no batch/headless scripting flag
  anywhere in `--help`. The previously-UNVERIFIED question is now **answered: no
  `--script` flag exists** in Krita 5.3.4's CLI. The only scripting route is the
  in-app `pykrita` plugin (not enabled here), which is not driveable from this CLI.
- Conclusion holds: **Krita is for the human artist; the agent does not auto-run it.**

*(No `.kra` round-trip was run — that would open a GUI document, which the
constraints forbid.)*

---

## N. Blockbench 5.x is a 3D-mesh tool with no headless CLI export

**Claim tested**: Blockbench output is a 3D mesh (wrong for 2D sprites); it *has* a
headless CLI export (`blockbench export -i in.json -o out.fbx`) but the path is
UNVERIFIED.

**Test — locate the executable and the CLI.**
```sh
ls "C:/Users/bx9ga/AppData/Local/Programs/Blockbench/"
# Blockbench.exe  + Electron runtime (app.asar, *.dll, locales/, resources/)
```

**Test — does the binary accept CLI flags?**
```sh
timeout 40 "C:/Users/bx9ga/.../Blockbench/Blockbench.exe" --version
timeout 40 "C:/Users/bx9ga/.../Blockbench/Blockbench.exe" --help
```
Raw output (both):
```
Checking for update
Update for version 5.2.1 is not available (latest version: 5.2.1, downgrade is disallowed).
EXIT=124   (killed by timeout — it is a GUI, not a CLI)
```
So `--version` / `--help` are **ignored**; the app boots its GUI and the updater.
**No CLI output, no exit.**

**Test — read the packaged entry point.**
```sh
# resources/app.asar:package.json
{ "name": "Blockbench", "version": "5.2.1", "main": "electron/main.js", "type": "module" }
```
Reading `resources/app.asar:electron/main.js` shows the only `process.argv` handling
is:
```js
const index = process.argv.findIndex(arg => arg === '--userData');
```
and the single-instance handler forwards an *already-open* file to a running window.
There is **no `export` subcommand, no `-i`/`-o` argument parsing, no headless
export path** in the shipped Electron main process.

**Corrected conclusion**: the claim of a headless CLI export
(`blockbench export -i in.json -o out.fbx`) is **not supported by this 5.2.1
install** — the shipped executable is a GUI-only Electron app and ignores CLI
arguments other than `--userData`. Any "headless export" would require a separate
Node package (`blockbench` on npm) run under Node, not this `Blockbench.exe`;
that package was not present here. The 2D-vs-3D tool-fit claim stands: Blockbench
produces 3D meshes and is the wrong tool for 2D pixel art/flat UI.

---

## O. Unity importer settings — not present in this repo

**Claim tested**: if `SpriteForge.cs` exists, its constants are fact (Texture 256,
PPU 256, pad 9, radius 26, bevel 11 px, outline 2 px, pivot bottom-centre `(0.5,0)`,
9-slice border 12 px, `SpriteDrawMode.Simple` ignores `spriteBorder` so `Sliced` is
required, `alphaIsTransparency=true`). Otherwise say so.

**Test**:
```sh
find <repo> -iname "SpriteForge.cs"
ls -d <repo>/Assets <repo>/Packages <repo>/ProjectSettings
```
Raw:
```
(find: no output)
ls: cannot access .../Assets: No such file or directory
ls: cannot access .../Packages: No such file or directory
ls: cannot access .../ProjectSettings: No such file or directory
```
**Result: `SpriteForge.cs` is ABSENT.** This repo is the agent/tooling framework, not
a Unity project — there is no `Assets/`, `Packages/`, or `ProjectSettings/` at the
root. The constants above are therefore **UNVERIFIED here**; they belong to a
different (Unity) project and must be re-read from that project's `SpriteForge.cs`
before being treated as fact. Do not apply them from this document.

---

## Test matrix

| Tool | Command run | Result | Evidence (paste location) |
|---|---|---|---|
| GIMP 3.2.6 | `gimp-console-3.2 --batch-interpreter plug-in-script-fu-eval -b <load+width>` | **WORKS** — printed `WIDTH=96`, exit 0 | §A raw output |
| GIMP 3.2.6 | same without `--batch-interpreter` | Fails + **hangs** (killed at 300 s) | §A |
| GIMP 3.2.6 | `(gimp-image-width 1)` | `unbound variable: gimp-image-width` | §A |
| GIMP 3.2.6 | load in one `-b`, use in next | `unbound variable: img` | §A |
| GIMP 3.2.6 | `(defined? 'x)` | returns `no` (no error) | §A |
| GIMP 3.2.6 | `(eval (list '+ 2 3))` | returns `5` (works) | §A |
| ComfyUI | `/object_info` alpha-node scan | 970 classes, no rembg/chroma node | §B |
| ComfyUI | `search_templates` SD1.5 queries | no SD1.5 template (0/0/0; `sd1.5`→3 irrelevant) | §C |
| ComfyUI | `SaveAudioAdvanced` execute | `TypeError: missing 1 required positional argument: 'format'` | §D |
| ComfyUI | `SaveAudio` execute | success | §D |
| ComfyUI | `CLIPLoader` types | `stable_audio` present, no `t5` type | §E |
| ComfyUI | `VAELoader` options | image VAE + `pixel_space` only, no audio VAE | §E |
| ComfyUI | `POST /userdata/a/b.json` | **HTTP 405** | §F |
| ComfyUI | `POST /userdata/a%2Fb.json` | **HTTP 200** | §F |
| ComfyUI | `get_template audio_yue2_music_cover` | `runnable:false` — `sheetsage2_bf16` missing | §G |
| HuggingFace | probe note's two URLs | `401` / `401` (both paths do not exist) | §G |
| HuggingFace | `Comfy-Org/YuE2` real files | `HTTP 206`, public, not gated | §G |
| comfy CLI | `comfy --version` / `launch --help` | 1.22.0; `--background` exists | §H |
| comfy CLI | `< /dev/null` redirect | help path returns, no tty error | §H |
| numpy | `arr.ptp()` vs `np.ptp(arr)` | `AttributeError` vs `2` | §I |
| Penpot MCP | connect 4401 | **DOWN** (`curl (7)`, HTTP 000) | §J, §K |
| Inkscape 1.4.4 | `--version` | `Inkscape 1.4.4 (dcaf3e7, 2026-05-05)` | §L |
| Inkscape 1.4.4 | `--export-type=png` | PNG written, exit 0 | §L |
| Inkscape 1.4.4 | `--query-all` | 5 bbox rows | §L |
| Inkscape 1.4.4 | `--export-id=rectA --export-id-only` | isolated PNG, exit 0 | §L |
| Inkscape 1.4.4 | unknown `font-family` export | renders via fallback (505 dark px) | §L |
| Krita 5.3.4 | `--version` (timeout) | `krita 5.3.4 (git c5b23e3)` | §M |
| Krita 5.3.4 | `--help` (full) | no `--script`; `--export` needs `--export-filename` | §M |
| Blockbench 5.2.1 | `Blockbench.exe --version`/`--help` | GUI boots, flags ignored, exit 124 | §N |
| Blockbench 5.2.1 | read `app.asar:electron/main.js` | only `--userData`; no export CLI | §N |
| Unity | `find SpriteForge.cs`, Unity dirs | **ABSENT** — no Unity project | §O |
| Blender 4.5.10 | `--background --python-expr` | `BLENDER_OK 4.5.10 LTS` | (context) |

## What still blocks

- **Penpot MCP** (§J, §K) — server down on 4401; all Penpot traps unverified.
- **ComfyUI generations** (§B, §C, §E) — no generation permitted here (4 GB VRAM);
  only the static node/model/template facts are verified.
- **ComfyUI UI behaviour** (§F) — "copied file does not appear in UI" and
  EDITOR-vs-API format need the GUI; only the 405 is verified.
- **`stdin is not a tty`** (§H) — absent from the CLI and repo; the full ComfyUI
  source-tree grep exceeded the 300 s shell cap, so its absence there is not fully
  confirmed. No failure to reproduce, so no fix to verify.
- **Inkscape bulk-export speed** (§L) — 4-shape probe only, no page-scale benchmark.
- **Krita `.kra` round-trip** (§M) — opening a document would start the GUI, which is
  forbidden; only the CLI surface is verified.
- **Blockbench headless export** (§N) — the claim is contradicted by this install;
  a separate npm `blockbench` package was not present to test the alternative.
- **Unity importer constants** (§O) — no Unity project in this repo; constants must
  be read from the other project before use.
