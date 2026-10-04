# Claude Code Game Studios -- Game Studio Agent Architecture

Indie game development managed through 49 coordinated Claude Code subagents.
Each agent owns a specific domain, enforcing separation of concerns and quality.

## Technology Stack

- **Engine**: Unity 6000.3.17f1
- **Language**: C#
- **Version Control**: Git with trunk-based development
- **Build System**: Unity Build Pipeline
- **Asset Pipeline**: Unity Asset Import Pipeline + Addressables

> **Note**: Engine-specialist agents exist for Godot, Unity, and Unreal with
> dedicated sub-specialists. Use the set matching your engine.

## Project Structure

@.claude/docs/directory-structure.md

## Engine Version Reference

<!-- ENGINE-REFERENCE-IMPORT: the line below is engine-specific. /setup-engine
     rewrites it to @docs/engine-reference/<engine>/VERSION.md for the chosen
     engine, so a Unity or Unreal project stops loading the Godot reference every
     session. It defaults to Godot (the template's example engine); skills that
     need the pinned version read docs/engine-reference/<engine>/VERSION.md on
     demand regardless of this import. -->
@docs/engine-reference/unity/VERSION.md


## Technical Preferences

`project.yaml` at the repo root is the primary config store — engine, specialists,
naming, platform, performance, modes. Skills resolve it via `resolve_config`
(see `.claude/docs/config-resolution.md`).

`.claude/docs/technical-preferences.md` is the **legacy fallback**, read on demand
when a key is absent from `project.yaml`. It is no longer imported here: before
`/setup-engine` runs it is almost entirely `[TO BE CONFIGURED]` placeholders, and
after it runs `project.yaml` holds the real values.

## Coordination Rules

@.claude/docs/coordination-rules.md

## Collaboration Protocol

**User-driven collaboration, not autonomous execution.**
Every task follows: **Question -> Options -> Decision -> Draft -> Approval**

- Agents MUST ask "May I write this to [filepath]?" before using Write/Edit tools
- Agents MUST show drafts or summaries before requesting approval
- Multi-file changes require explicit approval for the full changeset
- No commits without user instruction

See `docs/COLLABORATIVE-DESIGN-PRINCIPLE.md` for full protocol and examples.

> **First session?** If the project has no engine configured and no game concept,
> run `/start` to begin the guided onboarding flow.

## Coding Standards

@.claude/docs/coding-standards.md

## Art Toolchain

@.claude/rules/art-tooling.md

Local art tools: Blender 4.5, Krita 5.3.4, Inkscape 1.4.4, Blockbench 5.2.1, GIMP 3.2.6, ComfyUI (localhost:8188), Penpot (localhost:9001). Full setup: `docs/ART_TOOLCHAIN.md`.

> [!WARNING]
> 1. **Source `tools/art/env.sh` every session** — `source tools/art/env.sh && command -v blender krita inkscape blockbench gimp-console-3.2` — GameArtBin is Windows-form and unreadable by MSYS without it.
> 2. **Geometry in code, not AI prompts** — SD1.5 draws cubes with shadows on 4GB VRAM. Pillow draws squares correctly. See `references/art-pipeline-gotchas.md` §B.
> 3. **Don't trust logs, measure artifacts** — a checker that counts 69→32→0 on the same file measures nothing. Separate MEASURE from VERDICT. See `references/art-pipeline-gotchas.md` §H.
> 4. **One GPU generation at a time** — never submit a second ComfyUI job while one is running. Sequential, foreground; require ≥ 3 GB free VRAM first. ComfyUI serialises anyway, so a second submit is only a queued job you have lost track of. See `.claude/rules/art-tooling.md` rule 5.

## Context Management

Read `.claude/docs/context-management.md` on demand — it is a reference, not
session context. Two of its conventions are load-bearing and cited by name
elsewhere in the repo, so they are restated here rather than lost:

- **`production/session-state/active.md` is the session checkpoint.** The file is
  the memory, not the conversation. Read it first after any compaction, crash, or
  `/clear`.
- **Helpers in `.claude/scripts/` emit observations, never verdicts.** A script
  that scores or judges will eventually contradict a mode or override it cannot
  see. (Cited by `artifact-check.sh` and `adr-dep-graph.sh`.)
