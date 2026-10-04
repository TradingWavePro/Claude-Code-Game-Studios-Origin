# ENV-TRUTH — verified local art-toolchain ground truth

Collected **2026-10-03** on this machine by *running* commands (no doc inference).
Everything below is raw observed output. Anything not observed is marked UNKNOWN.

Repo: `C:/Users/bx9ga/Documents/GitHub/Claude-Code-Game-Studios-Origin`

> **Shell note that changes several results.** The persistent shell used here does
> **not** resolve MSYS-style `/c/...` PATH entries and does **not** resolve absolute
> `/c/...` command paths — `/c/Program Files/.../blender.exe` returns
> `error: command not found` (exit 127) even though `ls` of the same path succeeds.
> Only **Windows-form** paths (`C:/Program Files/...`) execute. Every binary check
> below that matters was therefore repeated with a `C:/...` path and **did** run.

---

## 1. GIMP installed?

```
$ ls "/c/Program Files/" | grep -i gimp
(no output)                                                        exit=1
$ ls "/c/Program Files/GIMP 3/bin" 2>&1
ls: cannot access '/c/Program Files/GIMP 3/bin': No such file or directory   exit=2
$ command -v gimp-console-3.2 gimp-console-3 gimp
(no output)                                                        exit=1
```

**Not in Program Files. But GIMP *is* installed, per-user:**

```
$ ls "$LOCALAPPDATA/Programs" | grep -i gimp
GIMP 3
$ ls "/c/Users/bx9ga/AppData/Local/Programs/GIMP 3/bin"   (partial)
SDL2.dll  config8  dot.exe  gdbus.exe  gegl.exe  gimp-3.2.exe  gimp-3.exe
gimp-console-3.2.exe  gimp-console-3.exe  gimp-console.exe  gimp.exe  gimptool-3.2.exe  ...
$ "C:/Users/bx9ga/AppData/Local/Programs/GIMP 3/bin/gimp-console-3.2.exe" --version
GNU Image Manipulation Program version 3.2.6                   GIMP_EXIT=0
```

**VERDICT: INSTALLED — GIMP 3.2.6, console binary at
`C:\Users\bx9ga\AppData\Local\Programs\GIMP 3\bin\gimp-console-3.2.exe`.**

Consequence (as observed at the time): `tools/art/env.sh` added
`C:/Program Files/GIMP 3/bin` — a directory that does not exist — so `add_to_path`'s
`[ -d "$posix_path" ]` test failed and GIMP was not on PATH.
**UPDATE 2026-10-03: since fixed.** `env.sh` now also adds the per-user
`$LOCALAPPDATA/Programs/GIMP 3/bin` (lines 56–59, keeping the system-wide paths as
fallbacks), and `command -v gimp-console-3.2` resolves in a real Git Bash (§9).

Also observed: `$LOCALAPPDATA/GIMP/3.2/` contains **only** `CrashLog` (no binaries),
and `$APPDATA/GIMP/3.2` exists (per-user config) — residue, not an install.

## 2. Repo venv Python

```
$ ls -la .venv/Scripts/python.exe
-rwxrwxrwx 1 somebody somegroup 274424 Apr  8  2025 .venv/Scripts/python.exe
$ .venv/Scripts/python.exe -c "import PIL, numpy; print(PIL.__version__, numpy.__version__)"
12.3.0 2.5.3                                                      exit=0
```

**VERDICT: PRESENT. Pillow 12.3.0, numpy 2.5.3.**

## 3. Every `.mcp.json` command path on disk

| Server | Path from `.mcp.json` | On disk |
|---|---|---|
| comfyui | `.venv/Scripts/comfy-mcp.exe` | **EXISTS** |
| comfyui (env) | `.venv/Scripts/comfy.exe` | **EXISTS** |
| inkscape | `.venv/Scripts/inkscape-mcp.exe` | **EXISTS** |
| inkscape (arg) | `tools/mcp-servers/config/inkscape-mcp.yaml` | **EXISTS** |
| krita | `.venv/Scripts/python.exe` | **EXISTS** |
| krita (arg) | `tools/mcp-servers/krita-mcp/mcp_server.py` | **EXISTS** |
| blockbench | `C:/Program Files/nodejs/node.exe` | **EXISTS** |
| blockbench (arg) | `tools/mcp-servers/blockbench-mcp/dist/index.js` | **EXISTS** (dist has `client.js index.js tools.js`) |
| penpot | `http://127.0.0.1:4401/mcp` | **URL, not a path — target NOT listening (see §6)** |

**VERDICT: 8/8 file paths exist. Zero missing files.** The only non-working entry is
Penpot, which is not a file at all — its MCP server is simply not running (see §6).

## 4. `tools/mcp-servers/` contents

```
$ ls tools/mcp-servers/
blockbench-mcp
config
krita-mcp
penpot-mcp
smoke.py
```

Repo-wide `find` for `*gimp*` / `*blender*mcp*` returned **only** Pillow internals:
`./.venv/Lib/site-packages/PIL/GimpGradientFile.py`, `GimpPaletteFile.py` (+pycache).

**VERDICT: NO GIMP MCP server. NO Blender MCP server.** Servers present: Blockbench,
Krita, Penpot (+ comfyui/inkscape via pip entry points in `.venv/Scripts`).

## 5. Smoke suite

```
$ .venv/Scripts/python.exe tools/mcp-servers/smoke.py
comfyui    PASS      stdio 39 tools: auth_login, auth_status, discover, download,
                     download_model, emit_partner_workflow, fetch_outputs, fetch_template,
                     free_memory, generate_image, get_logs, get_template ...
2026-10-03 22:46:19.310 | INFO | inkscape_mcp.main:initialize:206 | Initializing Inkscape MCP Server...
2026-10-03 22:46:19.310 | INFO | inkscape_mcp.main:initialize:219 | Using configured Inkscape: C:/Program Files/Inkscape/bin/inkscape.exe
2026-10-03 22:46:19.312 | INFO | inkscape_mcp.main:initialize:233 | Initialized Inkscape CLI wrapper
2026-10-03 22:46:19.381 | INFO | inkscape_mcp.main:initialize:248 | MCP prompts and resources registered
2026-10-03 22:46:19.382 | INFO | inkscape_mcp.main:initialize:260 | Extension bridge: plugins up to date (v11)
WARNING:inkscape_mcp.prefab:prefab-ui not installed — Prefab UI unavailable. Run: uv add 'prefab-ui>=0.14.0'
INFO:inkscape_mcp.transport:Starting Inkscape MCP Server v4.0.10
INFO:inkscape_mcp.transport:Transport: STDIO
[FastMCP 4.0.10 banner]
inkscape   PASS      stdio 8 tools: inkscape_analysis, inkscape_extension, inkscape_file,
                     inkscape_gradient, inkscape_live, inkscape_metadata,
                     inkscape_system, inkscape_vector
penpot     FAIL      http  ConnectError: All connection attempts failed
krita      DEFERRED  host app krita.exe is not running
blockbench DEFERRED  host app Blockbench.exe is not running
EXIT_CODE=1
```

**VERDICT: 2 PASS (comfyui, inkscape) · 1 FAIL (penpot) · 2 DEFERRED (krita,
blockbench). Exit code 1, caused solely by penpot.**

## 6. Penpot on 4401

```
$ curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:4401/mcp
000                                                            curl_exit=7 (refused)
$ netstat -ano | grep 4401
(no output)                                                     grep_exit=1
```

**Nothing is listening on 4401** — the Penpot MCP server is not running.

Port 9001 is the **Penpot application** (web UI / self-host frontend), **not an MCP
server**. Its `/mcp` returns 200 only because the SPA has a catch-all route —
verified by body:

```
$ curl -s http://127.0.0.1:9001/mcp | head -c 400
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta http-equiv="x-ua-compatible" content="ie=edge" />
    <title>Penpot | Full-stack design</title>
    <meta name="description" content="Penpot is the open-source design platform for teams that build digital products at scale.">
    <meta property="og:locale" content="en_US">
    <meta property="og:title" content="Penpo
```

That is the identical Penpot SPA page served at `/` — **not an MCP endpoint at all.**

```
$ netstat -ano | grep -E ":9001|:4401"
  TCP    0.0.0.0:9001   0.0.0.0:0    LISTENING    14228
  TCP       [::]:9001      [::]:0    LISTENING    14228
  TCP    [::1]:9001     [::1]:0       LISTENING     9164
```

**VERDICT: no port mismatch — `.mcp.json` correctly points at `127.0.0.1:4401/mcp`,
the MCP server's default port, and the server is simply not started.** `tools/art/env.sh`
line 94 exports `PENPOT_URL="http://localhost:9001"`, which is the Penpot **app** URL.
App (9001) and MCP (4401) are different things, not conflicting configs.

## 7. ComfyUI

```
$ curl -s http://127.0.0.1:8188/system_stats      (parsed)
comfyui_version: 0.38.2
python_version : 3.13.12 (main, Feb 12 2026, 00:38:53) [MSC v.1944 64 bit (AMD64)]
pytorch_version: 2.12.1+cu126
device         : cuda:0 NVIDIA GeForce GTX 1050 Ti : cudaMallocAsync
vram_total     : 4294836224   (4.00 GiB)
vram_free      : 2566101247   (2.39 GiB)
ram_total      : 34281422848  (31.9 GiB)   ram_free: 9718980608 (9.05 GiB)
```

**VERDICT: UP.** Served by `Comfy Desktop.exe` (12 Electron processes). **GPU is a
4 GB GTX 1050 Ti with ~2.4 GB free** — consistent with the repo's "SD1.5 on 4 GB VRAM
draws cubes with shadows" warning.

## 8. Running GUI host processes

```
$ tasklist | grep -i -E "krita|blockbench|gimp|blender|inkscape|penpot|comfy"
Comfy Desktop.exe   10104 Console  1  162.408 K
Comfy Desktop.exe   14000 Console  1   36.764 K
Comfy Desktop.exe    3952 Console  1  131.364 K
Comfy Desktop.exe   11240 Console  1   59.084 K
Comfy Desktop.exe    4220 Console  1   90.584 K
Comfy Desktop.exe    7916 Console  1   93.944 K
Comfy Desktop.exe   14604 Console  1   79.268 K
Comfy Desktop.exe   15124 Console  1   89.948 K
Comfy Desktop.exe   21224 Console  1  239.092 K
Comfy Desktop.exe   21232 Console  1  100.592 K
Comfy Desktop.exe   11556 Console  1  102.212 K
inkscape-mcp.exe    27168 Console  1    5.224 K
comfy-mcp.exe       27460 Console  1    5.224 K
```

**VERDICT: `krita.exe` NOT running. `Blockbench.exe` NOT running.** (Matches the two
DEFERRED lines in §5.) Also: no GIMP, no Blender, no standalone Inkscape GUI, no
Penpot process under those names. Only Comfy Desktop + the two MCP stdio shims.

## 9. `source tools/art/env.sh`

> **CORRECTION (re-verified 2026-10-03).** The `0 of 4 / exit 1` result in this
> section is an artefact of the persistent harness shell, **not** of `env.sh`.
> Re-running the same line in a **real Git Bash** after the later env.sh GIMP-path
> fix resolves **5 of 5**:
>
> ```
> $ "C:/Program Files/Git/bin/bash.exe" -lc 'source tools/art/env.sh && command -v blender krita inkscape blockbench gimp-console-3.2'
> /c/Program Files/Blender Foundation/Blender 4.5/blender
> /c/Program Files/Krita (x64)/bin/krita
> /c/Program Files/Inkscape/bin/inkscape
> /c/Users/bx9ga/AppData/Local/Programs/Blockbench/blockbench
> /c/Users/bx9ga/AppData/Local/Programs/GIMP 3/bin/gimp-console-3.2
> EXIT_CODE=0
> ```
>
> The raw harness output below is retained for the record; read it as historical.

```
$ source tools/art/env.sh            -> exit 0
$ command -v blender krita inkscape blockbench
(no output)                                       which_exit=1
$ echo "GS_PYTHON=[$GS_PYTHON]"
GS_PYTHON=[C:\Users\bx9ga\Documents\GitHub\Claude-Code-Game-Studios-Origin/.venv/Scripts/python.exe]
```

**VERDICT (superseded — see the dated correction above): env.sh sources cleanly and
`$GS_PYTHON` is NON-EMPTY (venv interpreter). In this harness shell `0 of 4` tool names
resolved (exit 1); in a real Git Bash it is `5 of 5`, exit 0.**

PATH after sourcing (first 5 entries) — `/c/...` MSYS form:

```
/c/Users/bx9ga/AppData/Local/Programs/Blockbench
/c/Users/bx9ga/AppData/Local/Programs/blockbench
/c/Program Files/Inkscape/bin
/c/Program Files/Krita (x64)/bin
/c/Program Files/Blender Foundation/Blender 4.5
c
\Users\bx9ga\AppData\Roaming\Code\User/globalStorage/github.copilot-chat/debugCommand;c
\Users\bx9ga\AppData\Roaming\Code/User/globalStorage/github.copilot-chat/copilotCli;C
```

Two observations about the PATH dump above:
1. env.sh's `/c/...` entries are unusable **in this harness shell only** — even
   `.exe`-suffixed probes fail (`command -v inkscape.com` / `blender.exe` /
   `krita.exe` / `Blockbench.exe` all exit 1), while the same binaries run fine by
   `C:/...` path. A real Git Bash resolves all five (see the correction above), so
   this is a harness artefact, **not an env.sh defect**.
2. The inherited Windows PATH is `;`-separated, so after one `:`-separated prepend
   it shreds into fragments (`c`, `\Users\...\debugCommand;c`, …) in this shell.

Ambient env after sourcing (`GameArtBin` is inherited from the Windows environment —
`tools/art/env.sh` never **sets or exports** it; the name appears only in a comment on
the script's line 3):

```
GS_ART_ENV_LOADED=1
GameArtBin=C:\Program Files\Blender Foundation\Blender 4.5;C:\Program Files\Krita (x64)\bin;
            C:\Program Files\Inkscape\bin;
            C:\Users\bx9ga\AppData\Local\Programs\Blockbench;
            C:\Users\bx9ga\AppData\Local\Programs\GIMP 3\bin
COMFYUI_URL=http://localhost:8188
```

(`GameArtBin` is the one entry that has GIMP's *real* location.)

## 10. Blender headless

```
$ "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --python-expr "import sys;print('BLENDER_OK',sys.version)"
BLENDER_OK 3.11.11 (main, May 31 2025, 09:35:27) [MSC v.1929 64 bit (AMD64)]
Blender 4.5.10 LTS (hash 6dc0b208d1b5 built 2026-05-19 01:33:42)
Blender quit
PIPE_EXIT=0     (wall time ~2.9 s)
```

**VERDICT: WORKS. `BLENDER_OK` printed. Blender 4.5.10 LTS, Python 3.11.11.**

## 11. Inkscape CLI

```
$ "C:/Program Files/Inkscape/bin/inkscape.com" --version
Inkscape 1.4.4 (dcaf3e7, 2026-05-05)                             exit=0
```

(`inkscape --version` bare returns `command not found`, exit 1 — PATH issue, not a
missing binary. Used `inkscape.com`, the console shim, per the no-GUI rule.)

**VERDICT: WORKS. Inkscape 1.4.4.**

## 12. Unity project / `Assets/` in repo

```
$ ls -d Assets assets art-workspace
ls: cannot access 'Assets': No such file or directory
ls: cannot access 'assets': No such file or directory
art-workspace                                              exit=2
$ ls -d Packages ProjectSettings Assets
(all three: No such file or directory)
$ git ls-files | grep -E "^(Assets|assets|art-workspace)/"    -> no output
$ ls -1 art-workspace
exports  inbox  provenance  work
$ ls -d */
CCGS Skill Testing Framework/  art-workspace/  design/  docs/
production/  references/  src/  tools/
```

**VERDICT: NO Unity project exists in this repo.** No `Assets/`, no `Packages/`,
no `ProjectSettings/`, nothing tracked under `assets/`. `art-workspace/` is present
and is the only art output tree. Root has `src/` (the Godot code root) while
`project.yaml` declares `engine: Unity` — the repo is not laid out for its declared
engine.

---

# § Environment claims vs reality

| Claim | Reality (observed) | Verdict |
|---|---|---|
| GIMP 3.2.6 installed | **Yes — 3.2.6**, but at `C:\Users\bx9ga\AppData\Local\Programs\GIMP 3\bin`, **not** `C:\Program Files\GIMP 3\bin`. On PATH after env.sh? **No when first measured; yes since env.sh's per-user GIMP-path fix (verified 5/5 in real Git Bash, §9).** | **MISLEADING** — installed, wrong location assumed |
| ffmpeg 9.0.1 | `ffmpeg version 9.0-full_build-www.gyan.dev` (gcc 16.1.0), WinGet `Gyan.FFmpeg` package. `/c/ffmpeg/bin` does not exist. | **PARTLY FALSE** — installed, but 9.0 not 9.0.1; env.sh's ffmpeg paths are no-ops |
| Unity 2022.3.62f3 | Confirmed — that is the only editor installed | **TRUE** |
| Unity 6000.3.17f1 (project.yaml / CLAUDE.md pin) | **Not installed.** Hub has only `2022.3.62f3` | **FALSE** — pin is unbacked |
| URP 17 | No Unity project, no `Packages/manifest.json` anywhere → no URP package can be present | **UNKNOWN / unbacked** (cannot verify a package in a project that doesn't exist) |
| 49 agents | `.claude/agents/*.md` → **49** | **TRUE** |
| 72 skills | `.claude/skills/*/` → **75** | **FALSE** — 75, not 72 |

## A. Exact verification line requested

```
$ source tools/art/env.sh && command -v blender krita inkscape blockbench gimp-console-3.2
(no output)
EXIT_CODE=1
```

**0 of 5 resolve.** `command -v` returned non-zero (1), which is expected when *some*
names are unresolvable; here **all five** are.

## B. GIMP — prove or disprove

```
$ ls "/c/Program Files/" | grep -i gimp                       -> (nothing)      exit=1
$ ls "/c/Program Files/GIMP 3/bin" 2>&1
  ls: cannot access '/c/Program Files/GIMP 3/bin': No such file or directory   exit=2
$ ls "/c/Program Files/GIMP 3/bin/gimp-console-3.2.exe" 2>&1
  ls: cannot access '/c/Program Files/GIMP 3/bin/gimp-console-3.2.exe': No such file or directory   exit=2
$ command -v gimp-console-3.2 gimp-console-3 gimp-console gimp -> (nothing)     exit=1
$ ls "$LOCALAPPDATA/Programs" | grep -i gimp                  -> GIMP 3          exit=0
$ "C:/Users/bx9ga/AppData/Local/Programs/GIMP 3/bin/gimp-console-3.2.exe" --version
  GNU Image Manipulation Program version 3.2.6                                  exit=0
```

**INSTALLED.** Path `C:\Users\bx9ga\AppData\Local\Programs\GIMP 3\bin`, version
**3.2.6** (console binary `gimp-console-3.2.exe` confirmed by execution). The claim's
*version* is right; the *Program Files location* was wrong. That is why `env.sh`'s
`add_to_path "C:/Program Files/GIMP 3/bin"` silently skipped it — **since fixed on
2026-10-03**: `env.sh` now adds the per-user `$LOCALAPPDATA/Programs/GIMP 3/bin` and
`command -v gimp-console-3.2` resolves 5/5 in a real Git Bash (§9).

## C. ffmpeg

```
$ source tools/art/env.sh && command -v ffmpeg
C:\Users\bx9ga\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin\ffmpeg.exe   exit=0
$ ls /c/ffmpeg/bin 2>&1
  ls: cannot access '/c/ffmpeg/bin': No such file or directory                  exit=2
$ timeout 10 ffmpeg -version | head -1
  ffmpeg version 9.0-full_build-www.gyan.dev Copyright (c) 2000-2026 the FFmpeg developers
  built with gcc 16.1.0 (Rev2, Built by MSYS2 project)                        FFMPEG_EXIT=0
```

**INSTALLED** — via WinGet, version string **9.0-full_build** (not 9.0.1). It
resolves because WinGet put it on the machine PATH, **not** because of env.sh; both
env.sh ffmpeg candidates (`C:/ffmpeg/bin`, `C:/Program Files/ffmpeg/bin`) do not
exist and are dropped by the `-d` guard.

## D. Unity editors actually installed

```
$ ls "/c/Program Files/Unity/Hub/Editor/" 2>&1
2022.3.62f3
exit=0
$ ls "/c/Program Files/Unity"
Hub
$ ls "/c/Program Files/Unity 2022.3.62f3"
Editor
```

Verbatim Hub listing: **`2022.3.62f3`** — one editor, nothing else. A second
non-Hub editor also exists at `/c/Program Files/Unity 2022.3.62f3/Editor`.

`project.yaml` lines 29–32 pin `engine: name: Unity, version: 6000.3.17f1`. That
editor is **not installed**, and no project targets it. Nothing was changed.

## E. Skill / agent counts

```
$ ls -d .claude/skills/*/ | wc -l
75
$ ls .claude/agents/*.md | wc -l
49
```

**75 skills** (claim said 72) · **49 agents** (claim correct).

---

# What actually blocks, ranked

1. **Penpot MCP server is not running** — nothing listening on `127.0.0.1:4401`
   (`curl` exit 7). `.mcp.json` points at the correct default MCP port; the 200 on
   `9001` is the Penpot app's SPA, not MCP. This is the *only* hard FAIL and the
   *only* cause of `smoke.py` exit 1.
2. **Krita + Blockbench host apps are not running** — both DEFERRED. Their MCP
   servers exist and their binaries are correct; nothing is broken but the apps.
3. **Not a real blocker — `env.sh` PATH.** In this harness shell `command -v` resolved
   0/5; in a real Git Bash it resolves 5/5 (see §9's dated correction). env.sh's
   GIMP path is also already fixed to the per-user `LOCALAPPDATA` location.
4. **No GIMP MCP server and no Blender MCP server exist** — if a task needs scripted
   GIMP or Blender, the only routes today are CLI/Script-Fu and `blender --background`
   (which is confirmed working).
5. **Engine/editor mismatch** — declared Unity 6000.3.17f1, installed 2022.3.62f3,
   no Unity project on disk. Any "open it in Unity" step is blocked.
6. **Not blockers (confirmed good):** ComfyUI + comfy-mcp (39 tools), Inkscape MCP
   (8 tools) + Inkscape 1.4.4 CLI, Blender 4.5.10 headless, GIMP 3.2.6 console,
   venv Pillow 12.3.0 + numpy 2.5.3, ffmpeg 9.0, node.exe, all 8 MCP file paths.

**UNKNOWNs:** URP 17 presence (no project to inspect); whether the `/c/...` PATH
entries work in a stock Git Bash (this shell is not one); GIMP GUI-mode behaviour
(GUI binary deliberately never launched).

---

## § ComfyUI MCP — live re-check (2026-10-03)

Run on demand, after the sections above; nothing in them was edited by this pass.

**1. Handshake + tool listing**

```
$ .venv/Scripts/python.exe tools/mcp-servers/smoke.py comfyui
comfyui    PASS      stdio 39 tools: auth_login, auth_status, discover, download,
                     download_model, emit_partner_workflow, fetch_outputs,
                     fetch_template, free_memory, generate_image, get_logs, get_template ...
EXIT_CODE=0
```

**PASS · 39 tools · no error · exit 0.**

**2. Real read-only tool call through the MCP** — `server_info`, raw payload:

```
$ .venv/Scripts/python.exe tools/mcp-servers/smoke.py comfyui --call server_info --args '{}'
comfyui    PASS      stdio 39 tools: ... | call server_info -> is_error=False {
  "python": {
    "version": "3.12.10",
    "executable": "C:\\Users\\bx9ga\\Documents\\GitHub\\Claude-Code-Game-Studios-Origin\\.venv\\Scripts\\python.exe",
    "virtualenv": null,
    "conda_env": null
  },
  "config": {
    "path": "C:\\Users\\bx9ga\\AppData\\Local\\comfy-cli\\config.ini",
    "default_workspace": null,
    "default_launch_extras": null,
    "recent_workspace": null,
    "tracking_enabled": false,
    "background": null
  },
  "server": {
    "running": true,
    "url": "http://127.0.0.1:8188"
  },
  "hardware": {
    "os": "Windows",
    "os_version": "11",
    "arch": "AMD64",
    "cpu": "Intel64 Family 6 Model 165 Stepping 3, GenuineIntel",
    "ram_bytes": 34281422848,
    "gpu": {
      "vendor": "nvidia",
      "model": "NVIDIA GeForce GTX 1050 Ti",
      "vram_bytes": 4294967296,
      "unified_memory": false
    }
  },
  "workspace": {
    "path": "C:\\Users\\bx9ga\\Documents\\comfy\\ComfyUI",
    "type": "default",
    "manager_mode": "not-installed",
    "manager_detected": "none",
    "uv_compile_default": false
  },
  "compatibility": {
    "comfy_cli_version": "1.22.0",
    "min_comfy_cli_version": "1.14.0",
    "envelope_schema_major": 1,
    "warnings": [],
    "envelope_schema": "envelope/1"
  },
  "freshness": {
    "core": { "installed": null, "commit": null, "latest": null, "outdated": false },
    "packs": [],
    "checked_at": "2026-10-03T16:33:24.717982+00:00"
  }
}
EXIT_CODE=0
```

`is_error=False`, exit 0 — the MCP answers a real call right now, and independently
reports `"server": {"running": true, "url": "http://127.0.0.1:8188"}`.

**3. Backend directly**

```
$ curl -s -o /dev/null -w "%{http_code}\n" --max-time 15 http://127.0.0.1:8188/system_stats
200
curl_exit=23
```

**HTTP 200 — backend up.** (`curl_exit=23` is a *local* write error on `/dev/null`
in this harness shell, not an HTTP failure; the emitted status code is 200, and §7's
`/system_stats` body parses — ComfyUI 0.38.2, torch 2.12.1+cu126.)

**4. Registration + executables**

```
$ grep -n -A6 '"comfyui"' .mcp.json
3:    "comfyui": {
4-      "command": "C:/Users/bx9ga/Documents/GitHub/Claude-Code-Game-Studios-Origin/.venv/Scripts/comfy-mcp.exe",
5-      "args": [],
6-      "env": {
7-        "COMFY_LOCAL_URL": "http://127.0.0.1:8188",
8-        "COMFY_BIN": "C:/Users/bx9ga/Documents/GitHub/Claude-Code-Game-Studios-Origin/.venv/Scripts/comfy.exe",
9-        "COMFY_CLI_MIN_VERSION": "1.14.0"

$ ls -la .venv/Scripts/comfy-mcp.exe .venv/Scripts/comfy.exe
-rwxrwxrwx 1 somebody somegroup 46080 Oct  3 22:10 .venv/Scripts/comfy-mcp.exe
-rwxrwxrwx 1 somebody somegroup 46080 Oct  3 22:10 .venv/Scripts/comfy.exe
```

`.mcp.json` unchanged (not modified by this check).

**5. Override / hiding check**

```
$ ls -la .claude/settings.local.json .mcp.json 2>&1
ls: cannot access '.claude/settings.local.json': No such file or directory
-rwxrwxrwx 1 somebody somegroup 1396 Oct  3 22:18 .mcp.json

$ grep -rn "enableAllProjectMcpServers\|enabledMcpjsonServers\|disabledMcpjsonServers\|mcp__" \
      .claude/settings.json .claude/settings.local.json 2>/dev/null
(no output)                                                grep_exit=2
```

No `.claude/settings.local.json` exists, and the override grep matches nothing
(exit 2 = `.claude/settings.local.json` does not exist). **No local override can be
hiding the comfyui server.**

**VERDICT — registered: yes · server answers now: yes (PASS, 39 tools, live
`server_info` `is_error=False`) · backend up: yes (HTTP 200, `"running": true`).**