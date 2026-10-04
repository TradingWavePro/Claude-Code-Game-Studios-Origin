# Step 6 Rescope — Asset Production on Headless-Only Paths

**Date:** 2026-10-03 · **Host:** win32 10.0.26300 x64, GTX 1050 Ti 4 GB
**Source of truth for tool facts:** `docs/local-tools/INVENTORY.md` · **Blocker source:** `MCP-CHOICES.md`
**Constraint:** only paths already proven scriptable with the app closed — ComfyUI API (`:8188`), `inkscape --actions/--export-type`, `blender --background --python`.

## Original Step 6 (4 deliverables)

| # | Deliverable | Named tools | Blocker |
|---|---|---|---|
| 1 | 4-icon set | ComfyUI + **GIMP**/**Krita** | GIMP not installed (no Script-Fu/Python-Fu at all); Krita's pykrita plugin is **off** — `%APPDATA%/krita/pykrita` absent, so no scripted Krita call |
| 2 | Button 9-slice | **Penpot**/Inkscape | Penpot MCP repo archived 2026-02-03; live one moved to `penpot/penpot` `develop:mcp/` → needs npm install from that subpath **plus** a live Chromium tab with `File ▸ MCP Server ▸ Connect` at `localhost:4401/mcp`. No browser, no MCP. |
| 3 | Low-poly prop | **Blockbench** (if approved) | No headless mode — a plugin must be loaded into the running desktop app. Executable alone is not sufficient. |
| 4 | Hand-touched sprite | **Krita** | Same pykrita blocker as #1; also needs a manual app launch. |

Three of four deliverables have the same single blocker class: **a GUI that must be launched by a human and held open**. Only #2's Inkscape half and #1's ComfyUI half survive unattended.

## New Step 6 scope — 3 deliverables, headless only

| # | Deliverable | Chain | Exit evidence |
|---|---|---|---|
| A | 4-icon set (256² RGBA PNG) | ComfyUI `:8188` `/prompt` → `/history` poll → Inkscape `--actions` (trim to alpha bbox, resize, normalize opacity) → PNG | 4 files in `Assets/Art/Icons/` + one retained contact sheet |
| B | Vector button, 9-slice | Author `.svg` by hand → Inkscape `--export-type=svg` normalize + `--export-area-drawing` PNG proof → border/border-center/border-t/r/b/l slices + 32² **fixed center** | `.svg` + `_9s` sibling texture in `Assets/Art/UI/` |
| C | Simple prop mesh | Blender `--background --python` (build from script, no GUI) → `bpy.ops.export_scene.fbx` / glTF → drop into `Assets/Art/Props/` | `.fbx`/`.glb` + retained render preview |

**Inkscape replaces GIMP/Krita as the cleanup stage** — it is the only installed raster/vector editor that runs with the app closed, and `--actions` covers the two ops the icon set actually needs (alpha-bbox trim, size normalize). No layer semantics, no brushwork, no cutout: nothing in this scope needs them.

## Deferred — do not schedule until unblocked

| Item | Unblocks when | Then it replaces |
|---|---|---|
| Hand-touched sprite (orig #4) | pykrita enabled in Krita settings (or `SanSaSane/krita-mcp` `install.ps1` run) + Krita launched by user | extends A with paint layers; exports `.kra` + flattened PNG |
| True Penpot button (orig #2) | npm install from `penpot/penpot` `develop:mcp/` **and** a connected Chromium tab | B gains design tokens/components; the `.svg` stays the export of record |
| Blockbench low-poly (orig #3) | Blockbench launched with `sosadly/blockbench-mcp` plugin loaded | C gains cube/UV authoring; Blender keeps the export step |
| GIMP raster ops | GIMP **3.x** installed | none yet — no Step 6 deliverable needs alpha/mask batch work |

Two notes the rescope does not fix: the Unity project folder does not exist at the workspace root, so `Assets/…` destinations are the convention to create, not a path that exists; and `blender --background` export targets the Unity 6000.3.17f1 pin but the editor path itself is still `UNVERIFIED` (`project.yaml`).