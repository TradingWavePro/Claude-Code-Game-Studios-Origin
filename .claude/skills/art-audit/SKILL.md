---
name: art-audit
description: "Audit produced art artifacts against their specs and against the game-wide declared set. Measures with tools/art/audit_assets.py + audit_sync.py, then verdicts. Sits between /asset-spec (the spec producer) and /asset-audit (repo-wide conventions)."
argument-hint: "[batch|all] [--spec <file>]"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash(source tools/art/env.sh*), Bash("$GS_PYTHON" tools/art/audit_assets.py *), Bash("$GS_PYTHON" tools/art/audit_sync.py *), Bash(bash tools/art/audit_assets.py *), Bash(bash tools/art/audit_sync.py *)
model: sonnet
# Read-only diagnostic skill — measures and reports, writes nothing.
---

# Art Audit — Spec Conformance and Game-Wide Sync

Audit a batch of **produced** art artifacts two ways:

1. **Spec conformance** — does each file's measurement match the budget its spec
   declares (bytes, dimensions, power-of-two, alpha)?
2. **Game-wide sync** — do the produced files line up with the *declared* set:
   the entity registry, the entity inventory / asset manifest, and
   `design/assets/specs/*.md`?

## The scripts MEASURE. This skill VERDICTS.

`references/art-pipeline-gotchas.md` §H: **"Don't trust logs, measure artifacts.
Separate MEASURE from VERDICT."** The two scripts measure and emit numbers; they
never print `PASS`, `FAIL`, `COMPLIANT` or `WARNINGS`. You — this skill — compare
the measurement to the spec and choose the verdict. Keeping the boundary sharp is
why the parser cannot drift: it is a stable contract, and only the comparison
layer reasons about rules.

The three art skills fit together:

| Skill | Role | Writes |
|-------|------|--------|
| `/asset-spec` | **Produces** `design/assets/specs/[target]-assets.md` — the per-asset spec | yes |
| `/asset-audit` | Checks repo-wide **conventions** — naming, size budgets, formats, orphans, missing refs | no |
| `/art-audit` **(this)** | Checks a **produced batch** against its spec, and syncs it against the whole game | no |

Run `/asset-spec` first so a spec exists; run `/art-audit` on a delivered batch;
run `/asset-audit` for the repo-wide conventions pass. They do not overlap.

## Inputs — check before producing any report

Establish FOUND / ABSENT for each, **before** measuring:

| Input | Path | Feeds |
|-------|------|-------|
| Artifact roots (**production**) | `art-workspace/exports/` — the one export root that counts as produced — plus `assets/` (Godot) / `Assets/` (Unity) / `Content/` (Unreal) | the produced set |
| Scratch dir (**NOT** a root) | `art-workspace/work/tmp/` — audit and e2e smoke **fixtures** only. Never scan it and never report its files: they are test data, and treating them as produced output manufactures `produced_but_undeclared` findings out of nothing. | nothing |
| Per-asset spec | `design/assets/specs/*.md` — or `--spec <file>` | spec budgets |
| Entity registry | `design/registry/entities.yaml` | declared set |
| Entity inventory | `design/assets/entity-inventory.md` | declared set |
| Asset manifest | `design/assets/asset-manifest.md` | declared set |
| Art bible (Asset Standards, §8) | `design/art/art-bible.md` | fallback budget source |

**If a source is ABSENT, its side of the report is `NOT ASSESSED`** — never an
empty-clean result. `audit_sync.py` already encodes this: an absent source prints
`NOT ASSESSED - <what> is absent` with a count of `0`, which is *not* the same
finding as a present-and-empty source. Do not "clean it up" to a blank cell.

**Absence of evidence is never evidence of absence.** A sync run that reports zero
gaps because *nothing was declared* has verified nothing. Say which of the two
happened.

## Commands

Run both from the repo root. `$GS_PYTHON` comes from `tools/art/env.sh` (Pillow +
numpy live only in the repo venv; a bare `python` has no Pillow).

```sh
# 1. MEASURE every artifact: bytes, dimensions, mode, alpha, PoT, corner alpha,
#    audio rate/channels/duration, SVG viewBox — with declared budgets attached.
source tools/art/env.sh && "$GS_PYTHON" tools/art/audit_assets.py --spec design/assets/specs/<target>-assets.md --format json

# 1b. With no spec yet, or for a one-off batch spec:
source tools/art/env.sh && "$GS_PYTHON" tools/art/audit_assets.py --root art-workspace/exports --format json

# 2. SYNC the produced set against the declared set (json; or --format markdown).
source tools/art/env.sh && "$GS_PYTHON" tools/art/audit_sync.py --format json

# 2b. Point the declared side at a specific spec instead of design/assets/specs/:
source tools/art/env.sh && "$GS_PYTHON" tools/art/audit_sync.py --declared-spec art-workspace/work/<batch>-spec.md --format both
```

`audit_assets.py` exits `0` when every file measured, `2` when a file could not
be read (its `errors` list names it — report that, do not skip it).
`audit_sync.py` exits `2` **only when no declared source was readable** — some
source is `NOT ASSESSED` *and* zero declared names came back across all of them,
so the sync verified nothing. A **partially-unreadable run exits 0**: surface
each unreadable source as a `NOT ASSESSED` row rather than treating the exit code
as permission to drop it.

## Phase 1 — Read the budgets

Read the spec file(s) and `design/art/art-bible.md`'s Asset Standards (§8) if it
exists. The **spec is authoritative** for a named asset; the art bible is the
fallback for a file no spec names. If neither exists, size/dimension checks are
**`NOT ASSESSED — no budget source`**, naming `/asset-spec` and `/art-bible`.

Do not invent a budget. A budget you cannot source makes every row a fabricated
comparison.

## Phase 2 — Conformance table

For each measured file, put **declared vs measured** side by side. The comparison
is mechanical — the script already put `spec_*` next to the measured value; you
copy them into columns and mark each as **within** or **over/under**. A field the
spec did not declare is `—` (not a violation, not a pass — simply not declared).

- `bytes` over `spec_max_bytes` → a size violation
- `width`/`height` ≠ `spec_width`/`spec_height` → a dimension violation
- `power_of_two.both` false where `spec_power_of_two` true → a PoT violation
- `has_alpha` false where `spec_require_alpha` true → an alpha violation
- `all_corners_transparent` false for a cut-out spec, or true for a
  full-bleed spec, is **evidence**, not a verdict by itself — read it against
  what the spec asked for (gotcha A: SD1.5 emits no real alpha)

## Phase 3 — Sync sets

From `audit_sync.py`: report the three sets, each with counts and rows —
**matched**, **declared-but-missing**, **produced-but-undeclared** — and the
status of every declared source. A source marked `NOT ASSESSED - …` belongs in the
"Sections not assessed" list with its reason, not in a set count.

## Phase 4 — Verdict and report

```markdown
# Art Audit Report — [batch] — [date]

## Summary
- **Files measured**: [N]  (unreadable: [N])
- **Spec violations**: [N]  (size: [N] · dimension: [N] · PoT: [N] · alpha: [N])
- **Sync**: matched [N] · declared-but-missing [N] · produced-but-undeclared [N]
- **Sections not assessed**: [none | each source and why]

## Spec Conformance
| File | Bytes | Max bytes | W×H | Spec W×H | PoT | Alpha | Result |
|------|-------|-----------|-----|----------|-----|-------|--------|
| [path] | [n] | [n] | [w]×[h] | [w]×[h] | [y/n] | [y/n] | [within \| over bytes \| wrong size \| …] |

## Sync Sets
### Declared but missing (in spec/registry, no file)
| Declared | Source | Asset ID |
|----------|--------|----------|

### Produced but undeclared (file, no spec/registry entry)
| File |
|------|

### Matched
| Declared | File |
|----------|------|

## Unreadable Files
| File | Error |
|------|-------|

## Sections Not Assessed
| Section | Why |
|---------|-----|

## Recommendations
[One per finding, naming the fix: re-export at the declared size, supply the
file the spec names, or write a spec for the undeclared output.]

## Verdict: [NOT ASSESSED / COMPLIANT / WARNINGS / NON-COMPLIANT]
```

Choose the verdict the way `/asset-audit` does — **first match wins**:

- **NON-COMPLIANT** — any spec violation (a measured value outside its declared
  budget), or any declared-but-missing asset.
- **WARNINGS** — only produced-but-undeclared files, or a source-readable but
  roundly unmatched batch (no violations, some gaps).
- **NOT ASSESSED** — the run did not cover its scope: no spec/budget source, zero
  files measured, or any section `NOT ASSESSED`. Name which. It ranks below the
  two finding verdicts (a measured violation is more actionable than a gap) and
  above COMPLIANT.
- **COMPLIANT** — files measured, every row within its declared budget, every
  declared source assessed, sync gaps none.

**A verdict of `NOT ASSESSED` is a success.** It is the correct answer to "does
this batch conform?" when there is no budget to conform to — and it is the only
answer that does not quietly claim the batch passed.

This skill is read-only: it runs measurements and produces a report. It writes no
files; it never edits an asset.

## Next Steps

- Size/dimension/alpha violations → re-export the file to the spec's declared
  values.
- Declared-but-missing → produce the asset, or correct the spec/registry if the
  entry is stale.
- Produced-but-undeclared → run `/asset-spec` to spec the output (or delete it if
  it is a stray export).
- Missing budget source → run `/asset-spec` (per-asset) and/or `/art-bible`
  (§8 Asset Standards).
- For repo-wide naming/format/orphan checks, run `/asset-audit`.
