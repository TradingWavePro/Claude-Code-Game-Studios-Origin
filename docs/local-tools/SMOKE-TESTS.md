# MCP Server Smoke Tests

**Date:** 2026-10-03
**Method:** `tools/mcp-servers/smoke.py`
**Result:** exit code `0`, elapsed `6.7s`, **0 failures**

## Results

| Server | Result | Tools | Notes |
|---|---|---|---|
| comfyui | PASS | 39 | stdio. Includes `fetch_outputs` with inline images, `system_stats`, `free_memory`. |
| inkscape | PASS | 8 | stdio. `prefab-ui` not installed — non-blocking WARNING. |
| penpot | PASS | 5 | HTTP at `:4401/mcp`. `execute_code`, `export_shape`, `import_image`. |
| krita | DEFERRED | — | `krita.exe` not running. Manual launch + rerun required. |
| blockbench | DEFERRED | — | `Blockbench.exe` not running. Manual launch + plugin load required. |

## Deferred servers

Both DEFERRED entries are an application-not-running condition, not a server
defect — the smoke script only exercises servers whose host app is up.

| Server | To unblock |
|---|---|
| krita | Launch `krita.exe`, then enable pykrita via the SanSaSane `install.ps1`. |
| blockbench | Launch `Blockbench.exe`, then load the plugin from `tools/mcp-servers/blockbench-mcp/plugin/`. |

## Rerun

```bash
.venv/Scripts/python.exe tools/mcp-servers/smoke.py
```

Exit code `0` means every probed server answered; `1` marks at least one failure.
