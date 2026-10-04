# Art Toolchain Documentation

**Date**: 2026-10-03  
**Engine**: Unity 6000.3.17f1 + URP  
**Platform**: Windows 11 (MSYS/Git Bash environment)

## Overview

This document describes the art production toolchain for the project, including local tool setup, PATH configuration, and integration points with ComfyUI and Penpot.

## Critical: Source env.sh Every Session

**GameArtBin exists in Windows form but MSYS/Git Bash cannot read it** — it is a `;`-separated Windows variable, not a POSIX PATH, so no art tool (Blender, Krita, Inkscape, Blockbench, GIMP) resolves by default. `env.sh` converts and prepends its entries.

```sh
source tools/art/env.sh
```

**Verification command**:
```sh
command -v blender krita inkscape blockbench gimp-console-3.2
```

If all five tools return paths, env.sh worked. Missing tools either aren't installed or need different paths in `tools/art/env.sh`.

## The MSYS PATH Trap

**Problem**: In Git Bash/MSYS2, `PATH=$PATH:C:/Program Files/Blender` does NOT resolve.  
**Cause**: Spaces in the path cause shell tokenization — `C:/Program` and `Files/Blender` are separate arguments.  
**Solution**: Convert via `cygpath -u` to `/c/Program Files/Blender` form before adding to PATH.

**GameArtBin is inherited from Windows, not set by `env.sh`.** On this machine it already exists and contains audio/video tool paths as well as art tools. `env.sh` is still required because `GameArtBin` is a Windows-form, `;`-separated variable — not a POSIX PATH — and MSYS/Git Bash does not read it, so none of its entries resolve via `command -v` until `env.sh` converts and prepends them.

`tools/art/env.sh` handles this conversion for all tools. Do NOT use `$HOME/c/Program Files/...` — `$HOME` is `/c/Users/<user>`, so that path doesn't exist. Use `/c/...` absolute paths.

## Tool Inventory

| Tool | Version | Location / Port | Notes |
|------|---------|-----------------|-------|
| **Blender** | 4.5 | `C:/Program Files/Blender Foundation/Blender 4.5/` | 3D modeling, geometry export |
| **Krita** | 5.3.4 | `C:/Program Files/Krita (x64)/bin/` | Texture painting, concept art |
| **Inkscape** | 1.4.4 | `C:/Program Files/Inkscape/bin/` | Vector graphics, icon cleanup |
| **Blockbench** | 5.2.1 | `%LOCALAPPDATA%/Programs/blockbench/` | Voxel/low-poly modeling |
| **GIMP** | 3.2.6 | `%LOCALAPPDATA%/Programs/GIMP 3/bin/` | Console binary `gimp-console-3.2.exe`; per-user install, not Program Files |
| **ComfyUI** | — | `http://localhost:8188` | Local SD1.5 only (4GB VRAM total, ~3.4GB free — SDXL/Flux require 8GB+) |
| **Penpot** | — | `http://localhost:9001` | Vector UI design + MCP integration |
| **ffmpeg** | — | `C:/ffmpeg/bin/` (optional) | Video/audio processing |

## Python Environment

**`$GS_PYTHON`** points to the repo venv at `<repo-root>/.venv/Scripts/python.exe` (absolute — resolved from `env.sh`'s own location, not the current directory). If the venv is missing, `GS_PYTHON` is set to empty and the rebuild command is echoed to stderr. There is no `python`/`python3` fallback.

**Why**: Pillow (PIL) is only installed in the repo venv. Hermes Python 3.14 has no PIL, so falling back to a system interpreter would hand you one without Pillow. Always use `$GS_PYTHON`, not bare `python`, and treat an empty `$GS_PYTHON` as "venv not built yet".

**Rebuild venv with Pillow + NumPy**:
```sh
uv venv .venv --python 3.12
uv pip install --python .venv/Scripts/python.exe Pillow numpy
```

## What's NOT Available

- **ImageMagick**: `magick` not found; `convert` is the Windows filesystem tool, not ImageMagick.
- **Alpha extraction**: Pillow (`$GS_PYTHON` with the repo venv). GIMP 3.2.6 **is** installed and `gimp-console-3.2` is a working route, but Pillow is preferred — each GIMP launch costs ~30 s (see `references/art-pipeline-gotchas.md` §F).
- **rembg**: Not installed. Background removal via chroma key (Pillow) or manual masking.

## Penpot MCP

`.mcp.json` targets the Penpot MCP server at `http://127.0.0.1:4401/mcp`. That endpoint is **DOWN right now** — nothing is listening on 4401. The Penpot *application* runs separately on `9001`. Both must be true before any Penpot MCP tool answers: the **MCP server must be started** *and* a **browser tab connected** to it (the plugin runs in a tab; a suspended tab stops sending heartbeats and tools fail — see `references/art-pipeline-gotchas.md` §G). **Do not change the port in `.mcp.json` — 4401 is the official MCP port.**

## Don't Run GUI --version in Blocking Shell

Running `blender --version` or `krita --version` in a blocking shell hangs for 300s (the default command timeout). GUI tools spawn windows even for version checks.

**Instead**:
- Use `test -x /path/to/tool` to check existence.
- Read version from metadata files (`.desktop`, app manifests, or docs).
- Use `command -v tool` to verify PATH resolution.

## Quick Verification Checklist

1. Source env.sh: `source tools/art/env.sh`
2. Check tools: `command -v blender krita inkscape blockbench gimp-console-3.2`
3. Check Python + Pillow: `[ -n "$GS_PYTHON" ] && $GS_PYTHON -c "from PIL import Image; print('Pillow OK')"` (empty `$GS_PYTHON` = venv not built — see the rebuild command under **Python Environment**)
4. Check ComfyUI: `curl -s http://localhost:8188/system_stats | head -n 5`
5. Check Penpot: `curl -s http://localhost:9001/health` (if endpoint exists)

If any check fails, see **Tool Inventory** above for expected install locations.
