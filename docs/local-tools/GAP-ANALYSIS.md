# Art Toolchain Configuration — Conformance Gap Analysis

**Date**: 2026-10-03
**Auditor**: `art-gap-check` (read-only conformance pass)
**Scope**: The 5-task art-toolchain request, verified against the ACTUAL artifact
files (`tools/art/env.sh`, `docs/ART_TOOLCHAIN.md`,
`references/art-pipeline-gotchas.md`, `.claude/skills/art-brief/SKILL.md`,
`CLAUDE.md`). Prior-session summaries in `docs/local-tools/*.md` are **not**
accepted as proof — every verdict below cites the artifact itself.

---

## 0. Real Verification Run (reproduced)

Command from the request was executed in Git Bash:

```sh
source tools/art/env.sh && command -v blender krita inkscape blockbench gimp-console-3.2
```

**Output** (via `C:\Program Files\Git\bin\bash.exe -lc`, cwd = repo root):

```
/c/Program Files/Blender Foundation/Blender 4.5/blender
/c/Program Files/Krita (x64)/bin/krita
/c/Program Files/Inkscape/bin/inkscape
/c/Users/bx9ga/AppData/Local/Programs/Blockbench/blockbench
EXIT=0
```

**Result: 4 of 5 tools resolve. `gimp-console-3.2` does NOT resolve — but this is
a WRONG-PATH CONFIG BUG in `env.sh`, not an install gap.** `env.sh:53` added only
`C:/Program Files/GIMP 3/bin`, which does not exist on this machine, so
`add_to_path`'s `[ -d ]` guard dropped it and GIMP never reached PATH. **GIMP is
installed** — 3.2.6, per-user at
`C:\Users\bx9ga\AppData\Local\Programs\GIMP 3\bin\gimp-console-3.2.exe`, proven by
*executing* the binary (`--version` → `GNU Image Manipulation Program version
3.2.6`, exit 0). Authority: `docs/local-tools/ENV-TRUTH.md` §B and §1. **See
PHASE 2 below — this is now FIXED.**

> **Harness note (corrected).** The shell this auditor is *embedded in* does not
> resolve `.exe` names against any PATH entry — not `/c/...`, not even Windows-form
> `C:/...` — while `ls` and `test -x` on the same paths succeed. Running the
> identical script through `C:\Program Files\Git\bin\bash.exe -lc` resolves all
> four correctly, and `$GS_PYTHON` is non-empty. **This is a harness artifact of
> the embedded shell, not a property of `env.sh`.** `docs/local-tools/ENV-TRUTH.md`
> §9 is the authority for the PATH question; my first-pass "0 of 4 resolve" reading
> was the same artifact and must not be relied on. All verification in PHASE 2
> below was run through real `bash.exe -lc`.

Environment facts confirmed directly:

| Probe | Result |
|---|---|
| `command -v convert` | `C:\WINDOWS\system32\convert.exe` → **confirms gotcha D** (`convert` is the Windows filesystem tool, not ImageMagick) |
| `[ -x /c/Program Files/Inkscape/bin/inkscape.exe ]` | EXEC-OK |
| `ls /c/Program Files/Krita (x64)/bin/krita.exe` | present |
| `ls /c/Program Files/Inkscape/bin/inkscape.exe` | present |
| `ls "$LOCALAPPDATA/Programs/blockbench/Blockbench.exe"` | present |
| `ls .venv/Scripts/python.exe` | present → `GS_PYTHON` resolves non-empty |
| `project.yaml` line 30 | `name: Unity` |

---

## 1. ENGINE CONFLICT — REPORT, DO NOT CHANGE

The request's background claims the project is **"Unity 2022.3.62f3 + URP 17"**.
The repo pins something different:

| Source | Value |
|---|---|
| `project.yaml:30` | `name: Unity` |
| `project.yaml:31` | `version: 6000.3.17f1` |
| `project.yaml:33` | `rendering: URP` (rendering value `URP`; **no URP major version is recorded anywhere**) |
| `CLAUDE.md:8` | `- **Engine**: Unity 6000.3.17f1` |
| `docs/engine-reference/unity/VERSION.md:5` | `| **Engine Version** | Unity 6.3 LTS |` |
| `docs/ART_TOOLCHAIN.md:4` | `**Engine**: Unity 6000.3.17f1 + URP` |

**Conflict**: request background says **Unity 2022.3.62f3**; repo says **Unity
6000.3.17f1 (Unity 6.3 LTS)**. Both are Unity, so `engine.name: Unity` is present
and **Task 1's "ask the user" branch never triggers** — no config was written
blindly on engine grounds. But the *version* disagrees by a full major release
(2022 LTS vs Unity 6.3 LTS), and **"URP 17" cannot be verified** because the repo
records only the pipeline name, never its version.

**Verdict: FLAG FOR USER — engine pin NOT changed** (per instruction).

---

## 2. TASK-BY-TASK CONFORMANCE

### Task 1 — `project.yaml` `engine.name` check

**Verdict: PRESENT**

- **Evidence**: `project.yaml:29-33`
  ```yaml
  engine:
    name: Unity
    version: 6000.3.17f1
    language: C#
    rendering: URP
  ```
- `engine.name: Unity` exists → the request's mandatory "ask before writing
  config" gate is satisfied (no pre-write ask was required).
- **Delta**: none. Engine-root rule for Unity is `Assets/` — noted, but no source
  files were written by this task so no code-root decision was forced.

---

### Task 2 — `tools/art/env.sh` + `docs/ART_TOOLCHAIN.md`

Files exist: `tools/art/env.sh` (96 lines), `docs/ART_TOOLCHAIN.md` (82 lines).

#### 2.A — Why source every session + verify command incl. `gimp-console-3.2`

**Verdict: PARTIAL**

- **Evidence (env.sh)**: `tools/art/env.sh:4`
  ```
  # Usage: source tools/art/env.sh && command -v blender krita inkscape blockbench gimp-console-3.2
  ```
  ✅ `gimp-console-3.2` IS listed in env.sh's header comment. ✅ The "GameArtBin is
  EMPTY" rationale is at `env.sh:3`.
- **Evidence (ART_TOOLCHAIN.md)**: `docs/ART_TOOLCHAIN.md:21` and `:77`
  ```
  command -v blender krita inkscape blockbench
  ```
  ❌ **`gimp-console-3.2` is MISSING from BOTH `command -v` lines in
  `docs/ART_TOOLCHAIN.md`** (the prose line 21 and the checklist line 77). Every
  other `command -v` line inside that doc omits it too.
- **Delta** (2 edits in `docs/ART_TOOLCHAIN.md`):
  - line 21, replace:
    `command -v blender krita inkscape blockbench`
    with:
    `command -v blender krita inkscape blockbench gimp-console-3.2`
  - line 77, replace:
    `2. Check tools: `command -v blender krita inkscape blockbench``
    with:
    `2. Check tools: `command -v blender krita inkscape blockbench gimp-console-3.2``
  - Also line 21's following sentence says *"If all **four** tools return paths"* —
    update to *five* (or note GIMP returns nothing until installed).

#### 2.B — MSYS PATH trap: `cygpath -u`, `$LOCALAPPDATA` backslash+space, never `$HOME`

**Verdict: PRESENT**

- **env.sh**: `:6-9` (trap explained), `:16-21` (cygpath detection), `:23-38`
  (`add_to_path` calls `cygpath -u "$win_path"` and prepends the POSIX result),
  `:58-59` (`$LOCALAPPDATA/Programs/blockbench` converted via the same helper).
  The conversion is real: the verification run showed PATH head became
  `/c/Program Files/Inkscape/bin` and `/c/Program Files/Krita (x64)/bin`, i.e.
  the `cygpath -u` output, not `C:/Program Files/...`.
- **ART_TOOLCHAIN.md**: `:24-32` — the trap ("Spaces in the path cause shell
  tokenization"), the `cygpath -u` solution, and the explicit *"Do NOT use
  `$HOME/c/Program Files/...`"* rule at `:32`.
- **Delta**: none.

#### 2.C — Python: Pillow-only-in-venv, `$GS_PYTHON`, exact rebuild command, never bare python

**Verdict: PRESENT**

- **env.sh**: `:68-80` — `GS_PYTHON` set to `$REPO_ROOT/.venv/Scripts/python.exe`;
  empty + stderr warning if absent; comment at `:69-71` states bare python has no
  Pillow so there is no fallback. Rebuild command at `:78`.
- **ART_TOOLCHAIN.md**: `:47-57` — `$GS_PYTHON` semantics, "there is no
  `python`/`python3` fallback", and the exact rebuild pair:
  ```sh
  uv venv .venv --python 3.12
  uv pip install --python .venv/Scripts/python.exe Pillow numpy
  ```
- **Delta**: none. (Verified `.venv/Scripts/python.exe` exists → `GS_PYTHON`
  resolves non-empty: `C:\Users\bx9ga\...\Claude-Code-Game-Studios-Origin/.venv/Scripts/python.exe`.)

#### 2.D — No ImageMagick, no rembg; `convert` is the Windows tool; alpha via GIMP console or Pillow

**Verdict: PRESENT**

- **env.sh**: `:87-89` — "No ImageMagick: magick not found, convert is Windows
  filesystem tool. Alpha channel ops via GIMP console mode or Pillow."
- **ART_TOOLCHAIN.md**: `:61-63` — ImageMagick row ("`convert` is the Windows
  filesystem tool, not ImageMagick"), alpha extraction via Pillow, and
  "rembg: Not installed".
- **Live confirmation**: `command -v convert` → `C:\WINDOWS\system32\convert.exe`.
- **Delta**: none.

#### 2.E — Never run GUI binary with `--version` in a blocking shell

**Verdict: PRESENT**

- **env.sh**: `:91-92` — "Don't run GUI binaries with --version in blocking shell
  — hangs 300s. Use test -x and metadata files for version checks."
- **ART_TOOLCHAIN.md**: `:65-72` — dedicated section, names `blender --version` /
  `krita --version`, 300s hang, and prescribes `test -x`, metadata files, and
  `command -v`.
- **Delta**: none.

---

### Task 3 — `references/art-pipeline-gotchas.md` (A–H)

File exists (206 lines). All eight sections present, each with repro/fix:

| § | Heading (line) | Verdict |
|---|---|---|
| A | `:5` "A. ComfyUI SD1.5 Has No Real Alpha" | PRESENT |
| B | `:24` "B. ComfyUI SD1.5 Fails on 4GB VRAM for Flat 2D Geometry" | PRESENT |
| C | `:47` "C. SaveAudioAdvanced COMBO_DYNAMICCOMBO_V3 Dropped" | PRESENT |
| D | `:63` "D. /userdata Single-Segment Only, EDITOR Format Not API" | PRESENT |
| E | `:88` "E. Stable Audio Needs 3 Things…" | PRESENT |
| F | `:119` "F. GIMP 3 Script-Fu Has 4 Conditions" | PRESENT |
| G | `:150` "G. Penpot MCP Traps (12 Distinct Issues)" | PRESENT |
| H | `:171` "H. Principle: Don't Trust Logs, Measure Artifacts" | PRESENT |

Sub-item detail checks:

- **3.A (alpha pipeline) — PARTIAL.** `:11-14` describes "Generate with gray or
  neutral background → Chroma key via Pillow → export PNG with alpha". ❌ The
  request's fourth clause — *"background must be far from all block colors"* — is
  **not stated**. The nearest text is `:13` "find furthest color from all
  non-background blocks", which is a different (weaker) instruction.
  - **Delta** — append to the Fix list at `:11-14`:
    `4. Choose the generation background so it is FAR from every block colour in`
    `the palette — a background near a block colour keys that block out too.`
- **3.B — PRESENT.** `:24-44`: all four failures listed (`:26-29`), cause
  ("SD1.5 treats geometric primitives as physical 3D objects", `:31-32`), the
  geometry-in-code lesson (`:36`), and the template clause — `:38` "All 116
  ComfyUI workflow templates use new models only… No SD1.5 template exists —
  projects needing SD1.5 must write API-format JSON workflows manually."
- **3.C — PRESENT.** `:47-61`: `SaveAudioAdvanced` → `COMBO_DYNAMICCOMBO_V3`,
  fix = use `SaveAudio`, repro at `:56-58`.
  ⚠️ Minor fidelity gap: request says "`format` is COMBO_DYNAMICCOMBO_V3, dict
  dropped"; doc says the *node* "returned COMBO_DYNAMICCOMBO_V3 dict type error"
  (`:50`) — the offending **`format` input** is not named.
  - **Delta** — amend `:50` to:
    `**What failed**: `SaveAudioAdvanced``s `format` input is typed`
    `` COMBO_DYNAMICCOMBO_V3``; the API drops the dict and the node errors.`
- **3.D — PRESENT, and the "copy doesn't show on UI, must POST" nuance IS
  captured.** `:67-78`:
  - single path segment: `:69` "`POST /userdata/subdir/file.json` → 405";
  - percent-encoding: `:73` + repro `:82-83` (`/userdata/a%2Fb.json`);
  - EDITOR ≠ API format: `:74`, `:76`, and the fix `:79` "Export 'API format' from
    editor, not 'Save Workflow'".
  - The copy nuance is present via equivalence rather than the literal word
    "copying": the request's *"copying a file into the dir does NOT show on UI,
    must POST"* is the same failure as "Save Workflow (= a file in the dir) is not
    API format". It is captured **implicitly**; a literal sentence is absent.
  - **Delta (optional hardening)** — add to §D Fix (`:78-79`):
    `- Dropping an EDITOR-format file into the userdata dir does NOT make it`
    `runnable in the UI — the server must be POSTed the API-format JSON.`
- **3.E — PRESENT.** `:88-118`: `CLIPLoader type: "stable_audio"` (`:96-97`,
  `:107`), `EmptyLatentAudio batch_size: 1` (`:98`, `:108`), VAE from
  `CheckpointLoaderSimple` output[2] (`:99-100`, `:110`), and the exact
  `vae-ft-mse-840000` → "tuple index error" failure (`:93`, `:104`).
- **3.F — PARTIAL.** `:119-149` covers: `--batch-interpreter`
  `plug-in-script-fu-eval` (`:125`, `:131`), same-expression load+call (`:126`,
  `:132`), the two renames `gimp-image-width`→`gimp-image-get-width` and
  `…height` (`:127-128`), and TinyScheme lacking `defined?`/`eval` (`:129`).
  ❌ **The "each GIMP launch ~30s → just use Pillow" timing claim is missing.**
  `:147` says only "GIMP console mode is brittle and slow" — no ~30s figure, and
  "Use Pillow" is at `:147` but the cost rationale is vague.
  - **Delta** — replace `:147`:
    current: `**Conclusion**: **Use Pillow for alpha extraction instead.** GIMP console mode is brittle and slow.`
    with: `**Conclusion**: **Use Pillow for alpha extraction instead.** Each GIMP`
    `launch costs ~30s (startup + Script-Fu init) and the API above is brittle —`
    `Pillow does the same key in milliseconds.`
- **3.G — PARTIAL (structure) / PRESENT (content).** `:150-169` enumerates **12**
  traps; the request lists **14** required points, with three of its points each
  bundling two facts:
  - item 5 = `fontFamily`+`fontWeight` **and** `fontId` rejected **and**
    `fontStyle` only normal/italic → covered as doc item 5 (`:155`);
  - item 6 = `findByName('Barlow')` returns "Barlow Condensed" 18 variants, choose
    by `fontVariantId` → covered as doc item 6 (`:156`);
  - item 13 = browser TAB / suspend / 30s heartbeat **and** the literal `export_shape`
    name → covered as doc item 10 (`:165`) but ❌ **the literal `export_shape` API
    name is NOT stated** (doc item 11 `:166` says "Export one board via
    `export_shape`" — so the name does appear, in item 11, for the export-size
    trap rather than the heartbeat trap).
  - **Delta** — none strictly required (content is present); optionally retitle
    `:150` from "(12 Distinct Issues)" to the request's own grouping so the
    one-to-one mapping is obvious. **No MISSING trap found.**
- **3.H — PRESENT.** `:171-195`: the 69→32→0 checker story (`:173`), MEASURE vs
  VERDICT (`:177-181`), and a worked example (`:183-194`).

**Task 3 overall: PARTIAL** (3.A missing "far from block colors"; 3.F missing the
~30s figure). All 8 headings exist; nothing MISSING.

---

### Task 4 — skill `art-brief` routing table

**Verdict: PARTIAL**

- File: `.claude/skills/art-brief/SKILL.md` (exists, 136 lines, has `name:
  art-brief` frontmatter at `:2`).
- **Routing table row count: 9** (`SKILL.md:26-34`) — matches the 9 requested rows:

  | # | line | Task | Use | NEVER column |
  |---|---|---|---|---|
  | 1 | `:26` | Sprite/block geometry | Code (Pillow) | `AI generate` ✅ |
  | 2 | `:27` | UI frame, 9-slice | Penpot vector | `AI generate` ✅ |
  | 3 | `:28` | Icon set | Penpot vector | `AI generate` ✅ |
  | 4 | `:29` | UI layout, design system | Penpot flex/grid | `Manual coords` ✅ |
  | 5 | `:30` | Board texture, organic surface | ComfyUI | **`—` ❌** |
  | 6 | `:31` | SFX, ambience | ComfyUI Stable Audio | **`—` ❌** |
  | 7 | `:32` | HUD font | Open-source font | `AI render text` ✅ |
  | 8 | `:33` | Alpha channel | Pillow chroma key | `"transparent background" prompt` ✅ |
  | 9 | `:34` | Production art | Human artist | `Ship raw AI output` ✅ |

- **Rows whose "NEVER" column is missing: 2 — rows 5 (Board texture) and 6
  (SFX/ambience), both literally `—`.**
  This is *semantically intentional* (the request itself gives both rows no
  "NEVER AI" — AI is the correct tool there). The request's phrasing "NEVER-ship
  rules" and the table's own legend ("The **NEVER use** column is load-bearing")
  make a bare `—` read as an omission rather than a decision.
  - **Delta (recommended, not required)** — in `SKILL.md`, replace the two `—`
    cells so the exemption is explicit and self-documenting:
    - `:30` NEVER cell `—` → `` `Ship un-tiled` `` (must be seamless; tile-offset
      check before shipping)
    - `:31` NEVER cell `—` → `` `Ship un-mastered audio` ``
    (Alternatively add a footnote below `:34`: *"`—` = AI is the correct tool;
    the NEVER column applies only to the non-AI rows."*)
- **Mandated skill statements** (the request's MUST-state content):
  - "AI is for concept + texture + style-lock + cleanup" → **PRESENT**
    (`:79-85`, "AI is for … Concept exploration / Texture generation /
    Style-locking references / Placeholder art / Cleanup assistance").
  - "NEVER ship raw AI output" → **PRESENT** (`:87` heading "Reminder: AI for
    Concept, Not Shipping"; `:89` "Never ship raw AI output." + 3-step gate
    `:90-93`).
  - "AI cannot hold cross-frame consistency, pivot, or atlas packing" →
    **PRESENT** (`:96-100`, "AI does NOT: Preserve cross-frame consistency … /
    Understand pivot points or atlas packing / …").

**Task 4 overall: PARTIAL** — table complete (9 rows), content complete, but 2
NEVER cells are empty `—` and the request phrases them as NEVER-ship rules.

---

### Task 5 — `CLAUDE.md` (+ `AGENTS.md` if it exists)

**Verdict: PARTIAL**

- **`CLAUDE.md`**: section present at `:66` `## Art Toolchain`, intro at `:68`
  names all tools and points to `docs/ART_TOOLCHAIN.md`. The 3 warnings at
  `:71-73`:

  | Requested warning | CLAUDE.md text | Match |
  |---|---|---|
  | (a) source `tools/art/env.sh` before using art tools | `:71` "**Source `tools/art/env.sh` every session** — `source tools/art/env.sh && command -v blender krita inkscape blockbench` — GameArtBin is EMPTY in Git Bash without it." | ✅ (same gimp-console omission as 2.A) |
  | (b) draw geometry in code, don't prompt AI | `:72` "**Geometry in code, not AI prompts** — SD1.5 draws cubes with shadows on 4GB VRAM. Pillow draws squares correctly. See `references/art-pipeline-gotchas.md` §B." | ✅ |
  | (c) don't trust logs, measure artifacts | `:73` "**Don't trust logs, measure artifacts** — a checker that counts 69→32→0 on the same file measures nothing. Separate MEASURE from VERDICT. See `references/art-pipeline-gotchas.md` §H." | ✅ |

  **All 3 warnings present and matching.** Δ: warning (a)'s inline `command -v`
  line omits `gimp-console-3.2` (same delta as 2.A; **GIMP IS installed** — this is
  a text omission, not an install gap; FIXED in PHASE 2 below). The quoted text
  above is the *pre-fix* CLAUDE.md.
- **`AGENTS.md` at repo root: DOES NOT EXIST.**
  ```
  $ ls -la AGENTS.md
  ls: cannot access 'AGENTS.md': No such file or directory
  ```
  The only `AGENTS.md` in the tree is the unrelated
  `tools/mcp-servers/penpot-mcp/AGENTS.md` — correctly ignored per instructions.
  → Task 5's "and `AGENTS.md` if it exists" branch is **correctly not taken**.
  - **Delta**: none (conditional not met).

---

## 3. CROSS-CUTTING CHECKS REQUESTED

| Check | Result |
|---|---|
| Root `AGENTS.md` exists? | **NO** — absent. Unrelated `tools/mcp-servers/penpot-mcp/AGENTS.md` (8135 bytes) ignored. |
| `project.yaml` `engine.name` | **YES — `Unity`** (`project.yaml:30`); version `6000.3.17f1` (`:31`), rendering `URP` (`:33`). Conflicts with request background's "Unity 2022.3.62f3". |
| `docs/ART_TOOLCHAIN.md` checklist `gimp-console-3.2`? | **NO.** Line 77: `` 2. Check tools: `command -v blender krita inkscape blockbench` `` — GIMP missing. (Also line 21.) |
| `env.sh` adds GIMP `bin` dirs to PATH? | **YES** — `tools/art/env.sh:53-54`: `add_to_path "C:/Program Files/GIMP 3/bin"` and `add_to_path "C:/Program Files/GIMP 2/bin"  # fallback for older installs`. |
| `env.sh` header lists `gimp-console-3.2` in verify example? | **YES** — `tools/art/env.sh:4`. |
| Gotchas A–H headings present? | **YES, all 8** (lines 5, 24, 47, 63, 88, 119, 150, 171). |
| Gotcha §D "copy doesn't show on UI, must POST" captured? | **IMPLICITLY** — §D `:63-86` captures single-segment 405, percent-encoding, and EDITOR≠API-format, and the fix "Export API format, not Save Workflow" (`:79`). No literal "copy a file into the dir doesn't show on UI" sentence → optional hardening delta in §2 3.D. |
| `art-brief/SKILL.md` table rows | **9 rows** (`:26-34`). Empty NEVER cells: **2** — rows 5,6 (`—`). |
| `CLAUDE.md` 3 warnings | **All 3 present** at `:71-73`; all match the request. Warning (a)'s `command -v` omits `gimp-console-3.2`. |
| Skills count `.claude/skills/*/` | **75** |
| Agents count `.claude/agents/*.md` | **49** |
| Files from the request that DON'T exist at all | **None.** All five artifact paths exist: `tools/art/env.sh`, `docs/ART_TOOLCHAIN.md`, `references/art-pipeline-gotchas.md`, `.claude/skills/art-brief/SKILL.md`, `CLAUDE.md`. Root `AGENTS.md` is conditional and legitimately absent. |

Note: `tools/art/` contains **only** `env.sh` — no `tools/art/*.py` exists yet,
which is consistent with the request (it described the Python rules for future
scripts, not an existing one).

---

## 4. VERDICT SUMMARY

| Task | Sub-item | Verdict |
|---|---|---|
| 1 | `engine.name` present | **PRESENT** (version CONFLICT flagged) |
| 2 | A — source/verify incl. gimp | **PARTIAL** (docs omit gimp in 2 `command -v` lines) |
| 2 | B — MSYS/cygpath | **PRESENT** |
| 2 | C — Python/GS_PYTHON | **PRESENT** |
| 2 | D — no ImageMagick/rembg | **PRESENT** |
| 2 | E — no GUI `--version` | **PRESENT** |
| 3 | A — alpha pipeline | **PARTIAL** (missing "far from all block colors") |
| 3 | B — SD1.5 4GB/templates | **PRESENT** |
| 3 | C — SaveAudioAdvanced | **PRESENT** (minor: `format` input not named) |
| 3 | D — /userdata | **PRESENT** (copy/POST nuance implicit) |
| 3 | E — Stable Audio 3 things | **PRESENT** |
| 3 | F — GIMP script-fu | **PARTIAL** (missing ~30s launch figure) |
| 3 | G — Penpot traps | **PARTIAL**-structure / PRESENT-content (12 headings vs 14 grouped points) |
| 3 | H — measure vs verdict | **PRESENT** |
| 4 | Routing table (9 rows) | **PARTIAL** (2 NEVER cells empty `—`; implications complete) |
| 5 | `CLAUDE.md` 3 warnings | **PARTIAL** (all 3 present; warning (a) omits gimp) |
| 5 | `AGENTS.md` | **N/A** (does not exist) |

**Aggregate: 12 PRESENT, 5 PARTIAL, 0 MISSING.**

No requested artifact is entirely absent. The PARTIALs are three
`gimp-console-3.2` omissions from `command -v` lines, one missing phrase in
gotcha A, one missing timing figure in gotcha F, and two empty NEVER cells —
every one fixable with a one-line edit. **Nothing was changed by this pass**
**(per instruction); this document is the only file created.**

> **PARTIALs 2.A, 3.A, 3.F, 4, 5 have since been FIXED — see PHASE 2 below.**
> The verdict table above is the *pre-fix* first-pass record.

### Flag for the user — engine mismatch (not a task delta)

`project.yaml:31` and `CLAUDE.md:8` pin **Unity 6000.3.17f1**, but the Unity Hub on
this machine installs **only `2022.3.62f3`** (`ENV-TRUTH.md` §D), and the repo
contains **no Unity project** (`Assets/`, `Packages/`, `ProjectSettings/` all
absent; `ENV-TRUTH.md` §12). The request background's *"Unity 2022.3.62f3 + URP
17"* matches the **installed editor**, not the **repo pin** — i.e. the pin is the
unbacked one. Engine pin was **not** changed. **Decision for the user:** align the
pin to 2022.3.62f3 (and create the Unity project skeleton), or install 6000.3.17f1.

---

## PHASE 2 — APPLIED (2026-10-03)

All five deltas were applied. Ground truth for GIMP and the PATH question is
`docs/local-tools/ENV-TRUTH.md` (§B, §1, §9), not the first-pass probes.

### Corrections to Phase 1

| Phase-1 claim | Correction | Authority |
|---|---|---|
| "4/5 resolve; GIMP not installed, neither `C:/Program Files/GIMP 3` nor `GIMP 2` exists" | **WRONG.** GIMP **IS** installed — 3.2.6 at `%LOCALAPPDATA%\Programs\GIMP 3\bin\gimp-console-3.2.exe`, proven by *executing* it (`--version` → 3.2.6, exit 0). Real defect was a **wrong-path config bug in `env.sh`** (only Program Files was added), not an install gap. | ENV-TRUTH §B, §1 |
| "Harness note: `/c/...` entries fail" text implying env.sh is suspect | **Harness artifact.** The embedded shell resolves no `.exe` against ANY PATH entry; real `bash.exe -lc` resolves 4/4 pre-fix (and 5/5 post-fix). ENV-TRUTH §9 is authoritative. | ENV-TRUTH §9 |
| Engine | Request background's Unity 2022.3.62f3 is the **installed** editor; repo pin 6000.3.17f1 is **unbacked** (not installed, no project). | ENV-TRUTH §D, §12 |

### Deltas → FIXED

| # | File | Delta applied | Status |
|---|---|---|---|
| 1 | `tools/art/env.sh` | Added `if [ -n "$LOCALAPPDATA" ]` block with `add_to_path "$LOCALAPPDATA/Programs/GIMP 3/bin"` + `GIMP 2/bin` fallback, **above** the retained Program Files variants; corrected the `# GIMP 3.2.6` comment to state the real per-user location. cygpath logic, `$GS_PYTHON` block, and ComfyUI/Penpot exports untouched. | **FIXED** |
| 2a | `docs/ART_TOOLCHAIN.md:21` | `command -v …blockbench` → appended `gimp-console-3.2`; "all four tools" → "all five tools". | **FIXED** |
| 2b | `docs/ART_TOOLCHAIN.md:77` | Checklist step 2 appended `gimp-console-3.2`. | **FIXED** |
| 2c | `docs/ART_TOOLCHAIN.md:42` | GIMP row `Not installed` / `—` → `3.2.6` / `%LOCALAPPDATA%/Programs/GIMP 3/bin/` / "Console binary `gimp-console-3.2.exe`; per-user install, not Program Files". | **FIXED** |
| 2d | `docs/ART_TOOLCHAIN.md:62` | Alpha line: "would work if GIMP 3.x were installed, but it is not" → "GIMP 3.2.6 **is** installed and `gimp-console-3.2` is a working route, but Pillow is preferred — each GIMP launch costs ~30 s (§F)". | **FIXED** |
| 2e | `docs/ART_TOOLCHAIN.md:32` | Added GameArtBin sentence: inherited from Windows (already holds audio/video too), but is a `;`-separated Windows-form var not a POSIX PATH, so env.sh is still required. | **FIXED** |
| 2f | `docs/ART_TOOLCHAIN.md:67-69` | Added **Penpot MCP** section: `.mcp.json` targets `127.0.0.1:4401/mcp`, DOWN now, app on 9001, server must be started AND a browser tab connected, **do not change the port**. | **FIXED** |
| 3a | `references/art-pipeline-gotchas.md:15-17` | §A Fix list got the 4th step: background must be far from every block colour or the key eats that block. | **FIXED** |
| 3b | `…:52,54` | §C now names the `format` **input** typed `COMBO_DYNAMICCOMBO_V3`; dict dropped, node reports missing/unusable parameter. | **FIXED** |
| 3c | `…:137-139` | §F conclusion now gives the ~30 s-per-launch cost rationale for why Pillow wins. | **FIXED** |
| 3d | `…:79` | §D Fix list gained: copying a workflow JSON into `/userdata` does **not** make it appear in the UI — must be POSTed. | **FIXED** |
| 4 | `.claude/skills/art-brief/SKILL.md:30-31` | Row 5 NEVER `—` → `Ship un-tiled output`; row 6 NEVER `—` → `Ship un-mastered audio`. No rows renamed or renumbered. | **FIXED** |
| 5 | `CLAUDE.md:71` | Warning (a) inline `command -v …blockbench` → appended `gimp-console-3.2`. Warnings (b)/(c) untouched. | **FIXED** |

### PHASE 2 VERIFICATION (raw, via `C:\Program Files\Git\bin\bash.exe -lc`)

```sh
cd /c/Users/bx9ga/Documents/GitHub/Claude-Code-Game-Studios-Origin
source tools/art/env.sh && command -v blender krita inkscape blockbench gimp-console-3.2
echo "EXIT=$?"
echo "GS_PYTHON=[$GS_PYTHON]"
```
```
/c/Program Files/Blender Foundation/Blender 4.5/blender
/c/Program Files/Krita (x64)/bin/krita
/c/Program Files/Inkscape/bin/inkscape
/c/Users/bx9ga/AppData/Local/Programs/Blockbench/blockbench
/c/Users/bx9ga/AppData/Local/Programs/GIMP 3/bin/gimp-console-3.2
EXIT=0
GS_PYTHON=[/c/Users/bx9ga/Documents/GitHub/Claude-Code-Game-Studios-Origin/.venv/Scripts/python.exe]
```

**5 of 5 resolve. `gimp-console-3.2` now resolves to the LOCALAPPDATA path
(`/c/Users/bx9ga/AppData/Local/Programs/GIMP 3/bin/gimp-console-3.2`).**
`$GS_PYTHON` non-empty. Exit 0.

Smoke suite:
```sh
.venv/Scripts/python.exe tools/mcp-servers/smoke.py
```
```
comfyui    PASS      stdio 39 tools: auth_login, auth_status, discover, download, download_model, emit_partner_workflow, fetch_outputs, fetch_template, free_memory, generate_image, get_logs, get_template ...
inkscape   PASS      stdio 8 tools: inkscape_analysis, inkscape_extension, inkscape_file, inkscape_gradient, inkscape_live, inkscape_metadata, inkscape_system, inkscape_vector
penpot     FAIL      http  ConnectError: All connection attempts failed
krita      DEFERRED  host app krita.exe is not running
blockbench DEFERRED  host app Blockbench.exe is not running
SMOKE_EXIT=1
```

**2 PASS · 1 FAIL · 2 DEFERRED · exit 1.** Penpot's FAIL is an **environment
state** (MCP server on 4401 not started), not a config defect — `.mcp.json` is
correct and must not be re-pointed. Krita/Blockbench DEFERRED means their host
apps are closed. Exit 1 is caused solely by Penpot.

Line counts after edits:
```
tools/art/env.sh                              103 lines
docs/ART_TOOLCHAIN.md                          88 lines
references/art-pipeline-gotchas.md            212 lines
.claude/skills/art-brief/SKILL.md             136 lines
CLAUDE.md                                      86 lines
```

### Phase-2 residual (not fixed, reported)

- **Penpot MCP server not running** → smoke exit 1. Start the server on 4401 and
  connect a browser tab; no file change needed.
- **Krita / Blockbench host apps closed** → their MCP servers DEFER. Not a defect.
- **No GIMP MCP server, no Blender MCP server exist** in the repo (ENV-TRUTH §4).
  Routes are `gimp-console-3.2` (CLI/Script-Fu) and `blender --background`.
- **Engine pin still mismatched** (6000.3.17f1 pinned / 2022.3.62f3 installed / no
  Unity project) — user decision, deliberately untouched (see *Flag for the user*
  above).

---

## END-TO-END MCP PROOF (2026-10-03)

Requirement: skills/agents can actually DRIVE the toolchain, not just read docs.
One real tool call per working server, via the project's own harness. **No
generation run** (ComfyUI call is read-only). Krita/Blockbench/Penpot NOT started.

Both calls used the existing CLI path (no throwaway script needed):

```sh
.venv/Scripts/python.exe tools/mcp-servers/smoke.py <server> --call <tool> [--args '<json>']
```

### 1. Inkscape — authoring → artifact (SVG → PNG)

**Input artifact** (authored for this proof, 277 bytes):
`art-workspace/work/e2e-proof.svg`

```sh
.venv/Scripts/python.exe tools/mcp-servers/smoke.py inkscape \
  --call inkscape_file \
  --args '{"operation":"convert","input_path":"art-workspace/work/e2e-proof.svg","output_path":"art-workspace/work/e2e-proof.png","format":"png"}'
```

Raw output:
```
inkscape   PASS      stdio 8 tools: inkscape_analysis, inkscape_extension, inkscape_file, inkscape_gradient, inkscape_live, inkscape_metadata, inkscape_system, inkscape_vector | call inkscape_file -> is_error=False {"success":true,"operation":"convert","message":"Converted art-workspace/work/e2e-proof.svg to art-workspace/work/e2e-proof.png","data":{"input_path":"C:\\Users\\bx9ga\\Documents\\GitHub\\Claude-Code-Game-Studios-Origin\\art-workspace\\work\\e2e-proof.svg","output_path":"art-workspace/work/e2e-proof.png","format":"png"},"execution_time_ms":2200.394630432129,"error":""}
SMOKE_INKSCAPE_EXIT=0
```

Artifact produced:
```
$ ls -l art-workspace/work/e2e-proof.png
-rw-r--r-- 1 bx9ga 197609 2431 Oct  3 22:59 art-workspace/work/e2e-proof.png
$ stat -c%s art-workspace/work/e2e-proof.png
2431
$ file art-workspace/work/e2e-proof.png
PNG image data, 128 x 128, 8-bit/color RGBA, non-interlaced
```

**RESULT: WORKS.** `inkscape_file` convert returned `is_error=False`,
`success:true`; real 128×128 RGBA PNG of **2431 bytes** written to
`art-workspace/work/e2e-proof.png`. This is the full authoring→artifact loop
driven through the MCP server.

### 2. ComfyUI — read-only call

`get_logs` (first attempt) reached the server and returned a valid payload, but the
payload was a "no log captured" notice:
```
comfyui    PASS      stdio 39 tools: ... | call get_logs -> is_error=False {
  "error": "no_log_file",
  "message": "comfy logs --tail 200 failed [no_log_file]: No captured ComfyUI log was found. ... hint: start ComfyUI with `comfy launch` so its output is captured"
}
SMOKE_COMFYUI_EXIT=0
```
So a second, definitionally-positive read-only call was made:

```sh
.venv/Scripts/python.exe tools/mcp-servers/smoke.py comfyui --call server_info
```
```
comfyui    PASS      stdio 39 tools: auth_login, auth_status, discover, download, download_model, emit_partner_workflow, fetch_outputs, fetch_template, free_memory, generate_image, get_logs, get_template ... | call server_info -> is_error=False {
  "python": { "version": "3.12.10", "virtualenv": "...\\.venv" },
  "server": { "running": true, "url": "http://127.0.0.1:8188" },
  "hardware": {
    "os": "Windows", "os_version": "11", "arch": "AMD64",
    "ram_bytes": 34281422848,
    "gpu": { "vendor": "nvidia", "model": "NVIDIA GeForce GTX 1050 Ti", "vram_bytes": 4294967296 }
  },
  "workspace": { "path": "C:\\Users\\bx9ga\\Documents\\comfy\\ComfyUI", "type": "default" },
  "compatibility": { "comfy_cli_version": "1.22.0", "min_comfy_cli_version": "1.14.0",
                     "envelope_schema": "envelope/1", "warnings": [] }
}
EXIT=0
```

**RESULT: WORKS.** `server_info` returned `is_error=False` with live data:
server running on 8188, GPU GTX 1050 Ti / 4 GiB VRAM (4294967296 bytes), comfy-cli
1.22.0 meeting the 1.14.0 minimum, no compatibility warnings. No generation run.

### Contradiction fix (item A)

The "GameArtBin is EMPTY in Git Bash" claim contradicted the corrected §The MSYS
PATH Trap. Corrected in all three places it appeared:

| File:line | Before | After |
|---|---|---|
| `docs/ART_TOOLCHAIN.md:13` | "GameArtBin is EMPTY in Git Bash — no art tool (Blender, Krita, Inkscape, Blockbench) is on PATH by default." | "GameArtBin exists in Windows form but MSYS/Git Bash cannot read it — it is a `;`-separated Windows variable, not a POSIX PATH, so no art tool (Blender, Krita, Inkscape, Blockbench, **GIMP**) resolves by default. `env.sh` converts and prepends its entries." |
| `tools/art/env.sh:3-4` | "Why: GameArtBin is EMPTY in Git Bash, no art tool is on PATH without this." | "Why: GameArtBin exists in Windows/`;`-separated form, which MSYS/Git Bash cannot read — no art tool is on PATH without this." |
| `CLAUDE.md:71` | "— GameArtBin is EMPTY in Git Bash without it." | "— GameArtBin is Windows-form and unreadable by MSYS without it." |

All three now agree with §The MSYS PATH Trap (`docs/ART_TOOLCHAIN.md:32`).

### What did NOT work / could not be done

- **Penpot MCP** — server on 4401 not started → `ConnectError`. Environment state,
  not a config defect; not started per instruction.
- **Krita / Blockbench MCP** — host apps not running → DEFERRED. Not started per
  instruction.
- **ComfyUI `get_logs`** — call itself returned `is_error=False` (the MCP path
  works), but the payload was `no_log_file` because ComfyUI was launched via
  `Comfy Desktop.exe`, not `comfy launch`. Using `server_info` instead, which
  returned positive live data. No generation was run.
