#!/bin/sh
# tools/art/env.sh — source this every session: source tools/art/env.sh
# Why: GameArtBin exists in Windows/`;`-separated form, which MSYS/Git Bash cannot
# read — no art tool is on PATH without this.
# Usage: source tools/art/env.sh && command -v blender krita inkscape blockbench gimp-console-3.2

# MSYS PATH trap: C:/Program Files/... with spaces does NOT resolve in Git Bash.
# The shell sees "C:/Program" and "Files/Blender" as separate tokens.
# Must convert via cygpath -u to /c/Program Files/... form before adding to PATH.
# LOCALAPPDATA has backslashes + spaces → cygpath handles both.

# Idempotent check — prevent duplicate PATH entries on repeated sourcing
if [ -n "$GS_ART_ENV_LOADED" ]; then
  return 0
fi

# Detect cygpath availability (Git Bash, MSYS2, Cygwin)
HAS_CYGPATH=0
if command -v cygpath >/dev/null 2>&1; then
  HAS_CYGPATH=1
fi

# Helper: convert Windows path to MSYS form, add to PATH if exists
add_to_path() {
  local win_path="$1"
  local posix_path

  if [ $HAS_CYGPATH -eq 1 ]; then
    posix_path=$(cygpath -u "$win_path" 2>/dev/null)
  else
    # Fallback: naive conversion C:\ → /c/ (won't handle all edge cases)
    posix_path=$(echo "$win_path" | sed 's|^\([A-Za-z]\):|/\L\1|' | tr '\\' '/')
  fi

  if [ -d "$posix_path" ]; then
    # Prepend to PATH (prioritize over system defaults)
    PATH="$posix_path:$PATH"
  fi
}

# Art tool installation candidates — convert each via cygpath before adding
# Blender 4.5.10 LTS
add_to_path "C:/Program Files/Blender Foundation/Blender 4.5"
add_to_path "C:/Program Files/Blender Foundation/Blender"

# Krita 5.3.4
add_to_path "C:/Program Files/Krita (x64)/bin"
add_to_path "C:/Program Files/Krita/bin"

# Inkscape 1.4.4
add_to_path "C:/Program Files/Inkscape/bin"

# GIMP 3.2.6 — the real install is PER-USER under LOCALAPPDATA, not Program Files.
# C:/Program Files/GIMP 3/bin does not exist on this machine; add_to_path's
# [ -d ] guard silently drops it, which is why GIMP never reached PATH.
if [ -n "$LOCALAPPDATA" ]; then
  add_to_path "$LOCALAPPDATA/Programs/GIMP 3/bin"  # GIMP 3.2.6 (verified)
  add_to_path "$LOCALAPPDATA/Programs/GIMP 2/bin"  # older per-user installs
fi
# System-wide install variants (present only if GIMP was installed all-users)
add_to_path "C:/Program Files/GIMP 3/bin"
add_to_path "C:/Program Files/GIMP 2/bin"  # fallback for older installs

# Blockbench 5.2.1 — Electron app in LOCALAPPDATA
if [ -n "$LOCALAPPDATA" ]; then
  add_to_path "$LOCALAPPDATA/Programs/blockbench"
  add_to_path "$LOCALAPPDATA/Programs/Blockbench"
fi

# ffmpeg (optional)
add_to_path "C:/ffmpeg/bin"
add_to_path "C:/Program Files/ffmpeg/bin"

export PATH

# Python: Pillow only in repo venv, Hermes Python 3.14 has no PIL.
# Use $GS_PYTHON not bare python — a bare python/python3 fallback yields an
# interpreter without Pillow, so there is no fallback: venv or nothing.
# Rebuild: uv venv .venv --python 3.12 && uv pip install --python .venv/Scripts/python.exe Pillow numpy
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if [ -f "$REPO_ROOT/.venv/Scripts/python.exe" ]; then
  GS_PYTHON="$REPO_ROOT/.venv/Scripts/python.exe"
else
  GS_PYTHON=""
  echo "env.sh: no venv at $REPO_ROOT/.venv/Scripts/python.exe — GS_PYTHON left empty (system python has no Pillow)." >&2
  echo "env.sh: rebuild with: cd \"$REPO_ROOT\" && uv venv .venv --python 3.12 && uv pip install --python .venv/Scripts/python.exe Pillow numpy" >&2
fi
export GS_PYTHON

# ComfyUI local server default
export COMFYUI_URL="http://localhost:8188"

# Penpot local server default
export PENPOT_URL="http://localhost:9001"

# No ImageMagick: magick not found, convert is Windows filesystem tool.
# Alpha channel ops via GIMP console mode or Pillow.

# Don't run GUI binaries with --version in blocking shell — hangs 300s.
# Use test -x and metadata files for version checks.

# Mark env as loaded
GS_ART_ENV_LOADED=1
export GS_ART_ENV_LOADED
