# Local Art Tool Inventory

**Date:** 2026-10-03
**Host:** win32 10.0.26300 (x64)
**Method:** filesystem probes + local HTTP probes only. No GUI was launched.
Versions were read from binary file metadata (`VersionInfo.ProductVersion`), not by
executing the apps.

## Tool status

| Tool | Installed | Version / Port | Notes |
|---|---|---|---|
| Blender | Yes | 4.5 | `C:\Program Files\Blender Foundation\Blender 4.5\blender.exe`. CLI-capable (`--background --python`). Installed version matches the 4.x line referenced in docs. |
| Krita | Yes | 5.3.4 | `C:\Program Files\Krita (x64)\bin\` — **not** under `%LOCALAPPDATA%\Programs`, which is where the usual probe looks. Python plugin (`%APPDATA%\krita\pykrita`) **not present**. |
| Inkscape | Yes | 1.4.4 | `C:\Program Files\Inkscape\bin\inkscape.exe`. Batch CLI available (`--export-type`, `--actions`). |
| GIMP | No | — | Not installed. Neither `C:\Program Files\GIMP *` nor a 2.10 console binary. Needs 3.x for Script-Fu/Python-Fu batch work. |
| Blockbench | Yes | 5.2.1 | `%LOCALAPPDATA%\Programs\blockbench\Blockbench.exe`. |
| ComfyUI | Yes (running) | **8188** — v0.38.2 | `/system_stats` responds. Frontend 1.53.6, bundled Python 3.13.12, PyTorch 2.12.1+cu12, CUDA device live. Port 8000 (Desktop default) is **closed** — this is a manual-port instance. |
| Penpot | Yes (running) | **9001** | HTTP responds with an HTML document. |
| Python | Yes | 3.12.10 | `…\AppData\Local\Programs\Python\Python312\python.exe`. `python3` on PATH is the WindowsApps store stub, not a real interpreter. |
| uv | Yes | 0.12.9 | `…\AppData\Local\hermes\bin\uv.exe`. |
| Project venv | **No** | — | `.venv/Scripts/python.exe` does not exist in the repo root. Any Python tooling must run against system 3.12 or create a venv first. |
| GPU | Yes | NVIDIA GeForce GTX 1050 Ti, 4096 MiB | Driver 560.94. CUDA compute. ~3.4 GB VRAM free while ComfyUI is up. |

## Known facts

- **ComfyUI ports.** ComfyUI Desktop serves on **8000** by default; a manual
  (`python main.py`) launch serves on **8188**. This machine answers on **8188**,
  so assume a manual start unless Desktop is opened. If a tool needs Desktop,
  port 8000 must be probed separately — do not treat 8188 as interchangeable.
- **GIMP requires 3.x.** Script-Fu/Python-Fu batch scripting targets the GIMP 3
  API. GIMP 2.10's Python-Fu is Python 2 and its Script-Fu signatures differ —
  do not write automation against 2.10 and expect it to work here. GIMP is not
  installed at all right now.
- **Krita Python plugin.** pykrita lives in `%APPDATA%\krita\pykrita` and must be
  enabled in Krita's Python plugin settings before any scripted call works. The
  directory does not exist, so the plugin is off. Once enabled it exposes a
  Python console on a socket, which is the scripting entry point.
- **Blockbench plugin.** Blockbench has no headless mode; automation goes through
  its plugin API, which requires the app to be running with the plugin loaded.
  The executable alone is not sufficient.
- **Penpot MCP needs a browser.** Penpot's MCP server drives a real Chromium
  session — the user must have Penpot open at 9001 *and* a browser attached with
  the Penpot extension before any MCP tool call succeeds. A reachable HTTP port
  is necessary but not sufficient.

## Start these manually — confirm with the user

Everything below is either already running, or needs a launch that no probe can
do. Tell me which to start:

- [ ] **ComfyUI** — already up on 8188. Restart it if a job needs a clean VRAM.
- [ ] **Penpot** — already up on 9001. Needs the browser session attached for MCP.
- [ ] **Krita + Python plugin** — must be launched by hand, and pykrita enabled in
      settings before scripted work is possible.
- [ ] **Blockbench + plugin** — must be launched by hand with the plugin loaded.
- [ ] **GIMP** — not installed; install 3.x first if it is needed at all.
- [ ] **Blender / Inkscape** — no manual start needed. Both are fully scriptable
      from the CLI with the app closed.