# MCP Server Choices — Step 2 Evaluation

**Date:** 2026-10-03 · **Host:** win32 10.0.26300 x64, GTX 1050 Ti 4 GB
**Method:** README + LICENSE + `commits/<branch>.atom` fetches only. Nothing installed, nothing run.
**Legend** — *Local-only*: usable with no cloud/hosted call. *Screenshot*: a tool returns an image the agent can actually look at (the difference between "exported a file" and "self-verifies its work").

## Recommendations

| Tool | Pick | Reason (one sentence) |
|---|---|---|
| ComfyUI :8188 | **Comfy-Org/comfy-mcp** | First-party and actively shipped, returns the PNG inline via `fetch_outputs(inline_images=True)`, and its `system_stats` / `free_memory` pair is exactly what a 4 GB card needs. |
| Penpot :9001 | **Official Penpot MCP** (`penpot/penpot` → `mcp/`) | It is the only first-party option and the only one that can write tokens/components, but it needs the browser tab connected, so it is a Step 3 task rather than a Step 2 blocker. |
| Inkscape 1.4.4 | **sandraschi/inkscape-mcp** | It is headless-by-default over the Inkscape CLI, so it works on Windows with the app closed — neither of the other two candidates does. |
| GIMP | **Install nothing yet; shortlist `maorcc/gimp-mcp`** | GIMP is absent so every candidate is untestable now, and when it lands `maorcc/gimp-mcp` is the only one with a Windows install path and a plain-HTTP bridge instead of a Unix socket. |
| Krita 5.3.4 | **SanSaSane/krita-mcp** | Its Windows `install.ps1` flips the `enable_krita_mcp` pykrita flag that is currently off, it is stdlib-only so the missing `.venv` does not matter, and `get_image` returns the canvas. |
| Blockbench 5.2.1 | **sosadly/blockbench-mcp** | Its `/ping` reports `blockbench_version` so the 5.2.1 install is verifiable, and 70 tools including `screenshot_views` cover model → texture → rig in one bridge. |

## ComfyUI

| Candidate | Last commit | Local-only | License | Screenshot | Install |
|---|---|---|---|---|---|
| `Comfy-Org/comfy-mcp` | 2026-09-19 | Yes (local-first; `partner_generate` is opt-in and spends credits) | AGPL-3.0-or-later OR Commercial | **Yes** — `fetch_outputs(..., inline_images=True)` | pip: `comfy-mcp` + `comfy-cli>=1.14.0` (separate installs on purpose) |
| `artokun/comfyui-mcp` | 2026-10-01 | Yes (also remote/cloud) | MIT | **Yes** — `get_image action:"view"` | npm: `npx -y comfyui-mcp` |
| `shawnrushefsky/comfyui-mcp` | 2026-01-28 | Yes | MIT | **Yes** — `get_image` | Docker (recommended) or Node 18+ build from source |

Notes: `artokun` has the widest surface (42 skills, VRAM watchdog hook) but its own README says "limited maintenance has resumed". `shawnrushefsky` defaults every snippet to port 8000 (Comfy Desktop) — this host answers on 8188, so that URL must be edited.

## Inkscape

| Candidate | Last commit | Local-only | License | Screenshot | Install |
|---|---|---|---|---|---|
| `sandraschi/inkscape-mcp` | 2026-10-03 | Yes — headless via `inkscape --actions` | MIT | Unknown — exports PNG/PDF to file, inline return not stated in README | pip/uv (`uv sync`, `just serve`), or `.mcpb` bundle / NSIS installer from Releases |
| `Shriinivas/inkmcp` | 2026-01-14 | **No on Windows** — D-Bus is Linux-only | README claims GPL-3.0, LICENSE file is **AGPL-3.0** (mismatch) | **Yes** — viewport/document export | manual: unzip extension into `~/.config/inkscape/extensions/`, `chmod +x` |
| `GianluDeveloper/inkscape-mcp` | 2026-09-20 | CLI yes; live extension bridge is **Linux-only** (`gdbus`) | MIT | **Yes** — renders PNG previews | manual clone + `uv sync --python 3.12` |

Notes: `GianluDeveloper` has an identical file tree to `sandraschi` (same `Cargo.toml`, `uv.lock`, `.opencode/skills`, `docs/`) with 0 stars / 0 forks — read it as an unmaintained mirror, not an independent option. Live-GUI editing is the capability neither Windows candidate delivers; only file/CLI mode works here.

## GIMP — not installed

| Candidate | Last commit | Local-only | License | Screenshot | Install |
|---|---|---|---|---|---|
| `TwelveTake-Studios/gimp-studio-mcp` | 2026-09-29 | Yes — loopback + per-session token | MIT | **Yes** — `get_bitmap` with region/scale/byte budget | pip/pipx: `twelvetake-gimp-studio-mcp`, then `gimp-mcp install-plugin` |
| `maorcc/gimp-mcp` | 2026-05-29 | Yes | GPL-3.0 | **Yes** — `get_state_snapshot` (full or region) | `uv sync` + copy `gimp-mcp-plugin.py` to `%APPDATA%\GIMP\3.x\plug-ins\` |
| `abelduarte/gimp-mcp` | 2026-04-12 | Yes, but defaults to `/Applications/GIMP.app` and a Unix socket | MIT | **Yes** — `gimp.get_image_bitmap` | manual clone + venv + `scripts/install_bridge.sh` |

Notes: all three require **GIMP 3.x**; `TwelveTake` has by far the best coverage (119 tools, alpha/cutout/ICC) but is DTF-print oriented. `TwelveTake` and `maorcc` both work on Windows; `abelduarte` needs adapting.

## Krita

| Candidate | Last commit | Local-only | License | Screenshot | Install |
|---|---|---|---|---|---|
| `SanSaSane/krita-mcp` | 2026-09-25 | Yes — loopback only + random per-session token | CC0-1.0 | **Yes** — `get_image` renders the canvas to PNG | manual: `install.ps1` (Windows) / `install.sh`; stdlib-only, no pip needed |
| `dcc-mcp/dcc-mcp-krita` | 2026-09-25 | Yes — typed command catalog, allow-listed roots, no arbitrary Python | MIT | **No** — returns artifact size + SHA-256, never an image | pip: `dcc-mcp-krita install --dcc-path <krita> --yes` |
| `nanayax3/krita-mcp` | 2026-02-26 | Yes, but the plugin's HTTP on `:5678` is **unauthenticated** | MIT | **Yes** — `krita_get_canvas` writes a PNG file | manual copy into `%APPDATA%\krita\pykrita\` + `pip install fastmcp httpx` |

Notes: `SanSaSane` is tested against Krita 5.3.3 (this host runs 5.3.4) and its documented failure modes are honest — `draw` bypasses undo and `close_document` can crash Krita ~1-in-5. `nanayax3` has 1 commit and 42 stars; the whole reason it exists is an export-timeout fix. `dcc-mcp-krita` is the safest by design and the least capable — no brush strokes, no canvas image.

## Blockbench

| Candidate | Last commit | Local-only | License | Screenshot | Install |
|---|---|---|---|---|---|
| `sosadly/blockbench-mcp` | 2026-09-21 | Yes — bridge on `127.0.0.1:8787` | MIT | **Yes** — `screenshot`, `screenshot_views`, `get_texture` | npm (`npm install && npm run build`) + `File ▸ Plugins ▸ Load Plugin from File` |
| `jasonjgardner/blockbench-mcp-plugin` | 2026-10-01 | Yes — desktop HTTP is loopback-only with `Origin`/`Host` checks | GPL-3.0 | Partial — headless server renders `.bbmodel`; desktop capture undocumented | `npx -y github:jasonjgardner/blockbench-mcp-plugin --root <dir>` (headless) or load plugin from URL |
| `FanyaOff/blockbench-mcp` | — | — | — | — | **Not found** — repo returns 404 |

Notes: Blockbench has no headless mode, so a plugin must be loaded into the running desktop app. `jasonjgardner` is the only candidate that also works without the editor (parallel agents, CI), but `risky_eval` runs arbitrary JS unless disabled in Settings.

## Penpot

| Candidate | Last commit | Local-only | License | Screenshot | Install |
|---|---|---|---|---|---|
| Official `penpot/penpot-mcp` | 2026-03-19 — **archived 2026-02-03** | Yes (local mode); a hosted remote mode also exists | MPL-2.0 | Partial — `export_shape` writes files, no screenshot tool | npm, from `penpot/penpot` `develop` → `mcp/` (repo moved; standalone repo is dead) |

Notes: local tools are `execute_code`, `high_level_overview`, `penpot_api_info`, `export_shape`, `import_image`. Requirements chain is Penpot on 9001 → browser tab open on the file → `File ▸ MCP Server ▸ Connect` → MCP at `localhost:4401/mcp`. Chromium 142+ private-network-access will prompt for local-network permission.

## Krita / GIMP ownership rule

| Condition | Raster owner | Reason |
|---|---|---|
| Now (GIMP absent) | **Krita** — all raster ops, layered `.kra` out | Krita is installed; GIMP candidates are untestable. |
| After GIMP 3.x is installed | **GIMP** — alpha/mask, cutouts, batch exports | `TwelveTake`/`maorcc` reach alpha and batch that Krita's MCP bridge only approximates. |
| After GIMP 3.x is installed | **Krita** keeps layered `.kra` | Only `SanSaSane` preserves Krita's own layered format and paint-layer semantics. |

Do not run both bridges against the same open document.

## Open items for Step 3

- pykrita is off on this host — `SanSaSane/install.ps1` is the only candidate whose install script flips the `enable_krita_mcp` flag for you.
- `sandraschi` and `sosadly` both require the host app running or a CLI on PATH; neither was exercised here.
- `inline_images` / `get_image` inline return was confirmed from docs, not observed — verify with one call before trusting a self-verifying loop.