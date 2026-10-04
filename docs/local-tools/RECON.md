# Step 0 Recon — Local Tools MCP Integration

**Date**: 2026-10-03  
**Status**: Read-only reconnaissance complete — awaiting approval to proceed

---

## What Exists Today

### Template Identity
This is **IdoCohen560/claude-unity-game-studio** — a Claude Code game-studio template with 49 agents, 74 skills, 12 hooks, and 13 rules. Forked for local customization.

- **Framework version**: 1.1.2 (last upgraded 2026-09-25)
- **Current branch**: `main` → will work on new branch `local-tools-mcp`
- **Engine**: [SUPERSEDED 2026-10-03] Unity 6000.3.17f1 configured in project.yaml
- **Default rigor**: `minimal` (no `modes:` block in `project.yaml` means unconfigured)

### Asset and Art Pipeline Agents

**Directors (Tier 2)**:
- `art-director` — Owns visual identity, art bible, style guides, asset standards. Model: inherit. Tools: Read, Glob, Grep, Write, Edit, WebSearch (no Bash).
- `audio-director` — Owns sonic identity, sound palette, audio strategy. Model: inherit. Tools: Read, Glob, Grep, Write, Edit, WebSearch (no Bash).

**Specialists (Tier 3)**:
- `technical-artist` — Shaders, VFX, rendering optimization, art pipeline tools. Model: inherit. Tools: Read, Glob, Grep, Write, Edit, Bash.
- `ux-designer` — User flows, interaction design, information architecture. Model: inherit. Tools: Read, Glob, Grep, Write, Edit, WebSearch (no Bash).
- `ui-programmer` — Implements UI systems (menus, HUDs, screens, data binding). Model: inherit. Tools: Read, Glob, Grep, Write, Edit, Bash.
- `unity-ui-specialist` — Unity-specific UI (UI Toolkit, UGUI, data binding, cross-platform). Model: **sonnet**. Tools: Read, Glob, Grep, Write, Edit, Bash.
- `unity-specialist` — Unity architecture authority. Model: inherit. Can spawn sub-specialists: unity-dots-specialist, unity-shader-specialist, unity-addressables-specialist, unity-ui-specialist.
- `sound-designer` — SFX specifications, mixing parameters, sound category definitions. Model: inherit. Tools: Read, Glob, Grep, Write, Edit (no Bash).

**None of these agents currently have MCP tool access.** The template has no `.mcp.json` at project or user scope.

### Existing Skills Related to Assets

**Art & Asset Skills**:
- `/art-bible` — Authors the 9-section art bible (visual identity statement, mood, shape language, color system, character/environment/UI direction, asset standards, references). Delegates to `art-director`, `ux-designer`, `technical-artist`. Required at `workflow: standard/full`, optional at `minimal`.
- `/asset-spec` — Per-asset visual specs + AI generation prompts. Takes `system:<name>`, `level:<name>`, or `character:<name>`. Spawns `art-director` + `technical-artist` in `full` mode, `art-director` only in `lean`, neither in `solo`. Writes to `design/assets/specs/[target-name]-assets.md`.
- `/asset-audit` — Read-only audit: naming conventions, file size budgets, format standards, orphaned assets, missing references. Uses Bash tools (`stat`, `file`, `du`). Produces report only, does not fix.

**UI Skills**:
- `/ux-design` — Authors UX specs for screens, flows, HUDs, patterns. Delegates to `ux-designer`.
- `/ux-review` — Validates completed UX specs before implementation.
- `/team-ui` — Full pipeline: UX authoring → visual design → implementation → review → polish. Orchestrates `ux-designer`, `ui-programmer`, `art-director`, engine UI specialist, `accessibility-specialist` (depending on `team.size`).

**Audio Skills**:
- `/team-audio` — Team orchestration for audio (not read in detail during recon).

**All skills delegate to agents; none directly call external tools like ComfyUI or GIMP.**

### Hooks and Validation

**`validate-assets.sh`** (PostToolUse hook on Write/Edit):
- Checks files under `assets/` (Godot), `Assets/` (Unity), or `Content/` (Unreal).
- **Naming convention** (Godot only): lowercase with underscores, pattern `[category]_[name]_[variant]_[size].[ext]`. Unity and Unreal use PascalCase; hook does not enforce naming there.
- **JSON validation**: Blocks on invalid JSON in `**/[Dd]ata/*.json` under any engine's asset root (exit 2 → Claude sees the error).
- **Advisory warnings** for naming issues on Godot (exit 0 → logged, not blocking).
- Does **not** check dimensions, file sizes, or formats — those are `/asset-audit` territory.

**Other hooks**: `session-start.sh`, `validate-commit.sh`, `validate-push.sh`, `validate-skill-change.sh`, `session-stop.sh`, `pre-compact.sh`, `post-compact.sh`, `notify.sh`, `log-agent.sh`, `log-agent-stop.sh`, `detect-gaps.sh`, `log-instructions.sh`.

### Directory Structure

Per `.claude/docs/directory-structure.md`:

```
/
├── CLAUDE.md, project.yaml, .claude/
├── <code root>/          # Engine-specific: src/ (Godot), Assets/ (Unity), Source/<Module>/ (Unreal)
├── assets/              # Godot art/audio/vfx/shaders/data — DOES NOT EXIST YET
├── design/              # GDDs, narrative, levels, balance
│   ├── art/            # art-bible.md lives here
│   ├── assets/         # entity-inventory.md, asset-manifest.md, specs/
│   └── ux/             # UX specs, interaction-patterns.md, accessibility-requirements.md
├── docs/               # Architecture, API, postmortems
│   └── engine-reference/  # Curated engine API snapshots (version-pinned)
├── tests/              # Unit, integration, performance, playtest
├── tools/              # Build and pipeline tools
├── prototypes/         # Throwaway prototypes
├── production/         # Sprints, milestones, releases, session-state/, session-logs/
└── CCGS Skill Testing Framework/
```

**The workspace-level `assets/` folder does not exist yet.** Unity projects would have their own `Assets/` folder inside a Unity project directory (not found in the workspace root during recon).

### Unity MCP

**NOT FOUND** during recon:
- `find . -name '*unity*mcp*'` → no results
- `find . -name '*mcp*unity*'` → no results
- No Unity project folder detected in workspace root

The README mentions "Unity MCP bridge" as part of the fork's identity, but it is not present in the current file tree. **Will need to verify with user whether Unity MCP exists elsewhere or was planned but not yet added.**

### Naming Conventions (from agents and hooks)

**Art assets** (Godot, from `art-director` agent and `validate-assets.sh`):
- `[category]_[name]_[variant]_[size].[ext]`
- Examples: `env_tree_oak_large.png`, `char_hero_idle_01.png`, `ui_btn_primary_hover.png`, `vfx_explosion_loop_small.png`
- Must be lowercase with underscores (Godot only; Unity and Unreal use PascalCase)

**Audio assets** (from `audio-director` agent):
- `[category]_[context]_[name]_[variant].[ext]`
- Examples: `sfx_combat_sword_swing_01.ogg`, `sfx_ui_button_click_01.ogg`, `mus_explore_forest_calm_loop.ogg`, `amb_env_cave_drip_loop.ogg`

**Unity assets**: PascalCase with type prefixes (not enforced by hook, but mentioned in `validate-assets.sh` comments).

### Workspace-to-Unity Asset Flow (Current State)

**NO FLOW EXISTS YET** because:
1. [SUPERSEDED 2026-10-03] Engine now configured: Unity 6000.3.17f1 — see project.yaml engine: block.
2. No Unity project folder exists in the workspace.
3. No Unity MCP found during recon.
4. Workspace `assets/` folder does not exist.

**Expected flow** (once configured, per template design):
- Art and audio files live in the workspace's `assets/` (Godot) or a Unity project's `Assets/` (Unity).
- The `validate-assets.sh` hook checks them on Write/Edit.
- `/asset-spec` produces specifications in `design/assets/specs/`.
- `/asset-audit` checks compliance against art bible standards.
- **No automation exists for moving files from a workspace `assets/` to a Unity project `Assets/` folder** — that would be the Unity MCP's job, which is not present.

### Model Settings of Asset-Related Agents

From agent frontmatter:

| Agent | Model | Typical Token Cost |
|-------|-------|--------------------|
| `art-director` | inherit | Uses session model (default: your active model) |
| `technical-artist` | inherit | Uses session model |
| `ux-designer` | inherit | Uses session model |
| `ui-programmer` | inherit | Uses session model |
| `unity-ui-specialist` | **sonnet** | Explicitly requests Sonnet (higher cost) |
| `unity-specialist` | inherit | Uses session model |
| `audio-director` | inherit | Uses session model |
| `sound-designer` | inherit | Uses session model |

**Note**: "inherit" means the agent uses whatever model the user's session is running on (e.g., if you're on Haiku, the agent runs on Haiku; if you're on Sonnet, it runs on Sonnet). Only `unity-ui-specialist` has a pinned model.

The three **directors** (Tier 1: `creative-director`, `technical-director`, `producer`) explicitly request **Opus**, but none of them are art/asset-focused.

---

## Summary for User Approval

**What was found**:
- 8 agents touch art/audio/UI: `art-director`, `technical-artist`, `ux-designer`, `ui-programmer`, `unity-ui-specialist`, `unity-specialist`, `audio-director`, `sound-designer`.
- 3 core asset skills: `/art-bible`, `/asset-spec`, `/asset-audit`.
- 3 UI skills: `/ux-design`, `/ux-review`, `/team-ui`.
- 1 audio skill: `/team-audio`.
- 1 validation hook: `validate-assets.sh` (naming + JSON validation).
- **No MCP servers configured** — no `.mcp.json` exists.
- **No Unity MCP found** despite README claim.
- **No workspace `assets/` folder** exists yet.
- **[SUPERSEDED 2026-10-03]** Engine now configured: Unity 6000.3.17f1 in project.yaml.

**Naming conventions enforced**:
- Godot: lowercase_with_underscores, pattern `[category]_[name]_[variant]_[size].[ext]` for art, `[category]_[context]_[name]_[variant].[ext]` for audio.
- Unity/Unreal: PascalCase (mentioned but not enforced by hook).

**Asset flow today**: None — no engine, no Unity project, no MCP, no automation.

**Next step**: Proceed to **Step 1 (Local Tool Inventory)** if approved.
