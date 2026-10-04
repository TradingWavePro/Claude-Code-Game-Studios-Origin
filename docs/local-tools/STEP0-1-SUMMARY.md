# Step 0+1 Summary — Art Toolchain Discovery & Engine Pin

**Date:** 2026-10-03
**Host:** win32 10.0.26300 (x64)
**Scope:** Step 0 = local art-tool discovery; Step 1 = engine pin + toolchain docs.
**Source of truth for tool facts:** `docs/local-tools/INVENTORY.md`

## Changeset applied (7 files)

| File | State | Change |
|---|---|---|
| `project.yaml` | modified | Added `engine` (Unity 6000.3.17f1, C#, URP, PhysX, editor path), `specialists` (6 unity-*), `naming`, `commands` (test/smoke wired, build/run `[TO BE CONFIGURED]`). Editor path + `constants` convention marked `UNVERIFIED`. |
| `tools/art/env.sh` | new | PATH bootstrap via `cygpath -u` (MSYS space trap). Idempotent via `GS_ART_ENV_LOADED`. Sets `GS_PYTHON`, `COMFYUI_URL=8188`, `PENPOT_URL=9001`. No `python` fallback. |
| `docs/ART_TOOLCHAIN.md` | new | Setup guide: env.sh sourcing, MSYS PATH trap, tool inventory, Python env, unavailable tooling, verification checklist. |
| `references/art-pipeline-gotchas.md` | new | §§A–H pipeline gotchas (incl. §B geometry-in-code, §H measure-vs-verdict). |
| `.claude/skills/art-brief/SKILL.md` | new | Art brief authoring skill. |
| `CLAUDE.md` | modified | Engine/Language/Build/Asset lines → Unity; engine-reference import → `unity`; added `## Art Toolchain` section with 3 callouts. |
| `.claude/docs/technical-preferences.md` | modified | Filled engine/language/rendering/physics, naming conventions, 6 specialists + routing, per-file-type routing table. |

## Shell verification — `source tools/art/env.sh` then `command -v`

| Tool | Resolves to | Result |
|---|---|---|
| `blender` | `/c/Program Files/Blender Foundation/Blender 4.5/blender` | OK (4.5) |
| `krita` | `/c/Program Files/Krita (x64)/bin/krita` | OK (5.3.4) |
| `inkscape` | `/c/Program Files/Inkscape/bin/inkscape` | OK (1.4.4) |
| `blockbench` | `/c/Users/bx9ga/AppData/Local/Programs/Blockbench/blockbench` | OK (5.2.1) |
| `gimp-console-3.2` | — | **MISSING** |
| `GS_PYTHON` | `[]` (empty) | **FAIL** — venv absent |
| `.venv/Scripts/python.exe` | — | **MISSING** |
| `%APPDATA%/krita/pykrita` | — | **MISSING** |

**4/5 tools OK.** Versions from binary file metadata (`VersionInfo.ProductVersion`), not from executing the apps — GUI `--version` in a blocking shell hangs 300s.

## Inventory (11 rows, from INVENTORY.md)

| Tool | Installed | Version / Port |
|---|---|---|
| Blender | Yes | 4.5 — CLI-capable (`--background --python`) |
| Krita | Yes | 5.3.4 — under `C:\Program Files\Krita (x64)\bin`, not `%LOCALAPPDATA%\Programs` |
| Inkscape | Yes | 1.4.4 — batch CLI available |
| GIMP | **No** | 2.10 console absent; needs 3.x for Script-Fu/Python-Fu |
| Blockbench | Yes | 5.2.1 — no headless mode, plugin API only |
| ComfyUI | Yes (running) | **8188**, v0.38.2 — port 8000 (Desktop default) closed |
| Penpot | Yes (running) | **9001** — HTTP live; MCP also needs browser + extension |
| Python | Yes | 3.12.10 system; `python3` on PATH is the WindowsApps stub |
| uv | Yes | 0.12.9 |
| Project venv | **No** | Python tooling has no Pillow-capable interpreter |
| GPU | Yes | GTX 1050 Ti, 4096 MiB, driver 560.94 — ~3.4 GB VRAM free |

## Blockers

| # | Blocker | Impact | Fix |
|---|---|---|---|
| 1 | GIMP not installed | No Script-Fu/Python-Fu alpha extraction; `gimp-console-3.2` missing from PATH | Install GIMP 3.x, or use Pillow only |
| 2 | Project venv missing (`GS_PYTHON` empty) | Any Pillow/numpy script fails — no interpreter fallback | `uv venv .venv --python 3.12 && uv pip install --python .venv/Scripts/python.exe Pillow numpy` |
| 3 | pykrita disabled (`%APPDATA%/krita/pykrita` absent) | No scripted Krita access | Enable Python plugin in Krita settings |
| 4 | Unity editor path unverified | `commands.test` / `commands.smoke` in `project.yaml` point at a probed, not confirmed, `Unity.exe` | Confirm install path; set `commands.build` / `commands.run` |

Discrepancy noted: `CLAUDE.md` § Art Toolchain lists GIMP 3.2.6 among local art tools; GIMP is not installed (blocker 1).

## Next

| Item | State |
|---|---|
| Step 2 — MCP evaluation (Penpot, ComfyUI) | Running |
| Approval gate after Step 2 | Pending user approval |
| Blockers 1–4 | Open — user decision required |