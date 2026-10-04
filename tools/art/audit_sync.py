#!/usr/bin/env python3
"""Cross-check produced art artifacts against the declared set. MEASURE ONLY.

"Đồng bộ với toàn bộ game" (sync with the whole game): an artifact batch is only
in sync when every declared asset has a file and every file belongs to a declared
asset. This script reports the three sets that say whether that holds:

    matched                   -- declared AND produced
    declared_but_missing      -- named by registry/spec, no file on disk
    produced_but_undeclared   -- file on disk, no registry/spec entry

Like ``audit_assets.py`` it emits no verdict word. A non-empty gap is a
measurement, not a FAIL; deciding what it means belongs to the report layer
(``.claude/skills/art-audit/``).

A side with no source is reported as ``NOT ASSESSED - <what> is absent``, never as
an empty-but-clean set. That is asset-audit's rule and it exists because a
registry that does not exist and a registry that is empty produce identical
"0 problems" output -- and they are not the same finding.

Usage:
    python audit_sync.py [--root DIR]... [--json|--format markdown|both]

Exit codes:
    0  the run assessed something -- including a partially-unreadable one, whose
       unreadable sources are listed as NOT ASSESSED rows
    2  NO declared source was readable: at least one source is NOT ASSESSED and
       zero declared names were extracted across all of them, so the sync
       verified nothing
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

#: Extensions counted as produced artifacts, matching audit_assets.py.
ARTIFACT_EXTS = (
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tga",
    ".ogg", ".wav", ".mp3",
    ".svg",
)

ENGINE_ASSET_ROOTS = ("assets", "Assets", "Content")

# Declared sources, in report order.
REGISTRY_REL = "design/registry/entities.yaml"
INVENTORY_REL = "design/assets/entity-inventory.md"
MANIFEST_REL = "design/assets/asset-manifest.md"
SPECS_GLOB = "design/assets/specs/*.md"


# --------------------------------------------------------------------------- #
# Paths / discovery
# --------------------------------------------------------------------------- #

def repo_root() -> Path:
    """Return the project root (the directory holding ``project.yaml``)."""
    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "project.yaml").is_file():
        return candidate
    return Path.cwd().resolve()


def display_path(path: Path, root: Path) -> str:
    """Render ``path`` relative to ``root`` with forward slashes, when possible."""
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def artifact_roots(root: Path, extra: list[str] | None) -> list[Path]:
    """Return the directories searched for produced artifacts.

    Defaults to ``art-workspace/exports`` plus every engine asset root that
    exists (``assets/`` Godot, ``Assets/`` Unity, ``Content/`` Unreal).
    ``extra`` replaces the default set when supplied.
    """
    if extra:
        return [Path(item) for item in extra]
    roots = [root / "art-workspace" / "exports"]
    roots.extend(root / name for name in ENGINE_ASSET_ROOTS if (root / name).is_dir())
    return roots


def discover_artifacts(roots: list[Path], root: Path) -> list[str]:
    """Collect produced artifact paths relative to ``root``, sorted, deduped."""
    found: set[str] = set()
    for base in roots:
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.name.startswith("."):
                continue
            if path.suffix.lower() in ARTIFACT_EXTS:
                found.add(display_path(path, root))
    return sorted(found)


# --------------------------------------------------------------------------- #
# Minimal YAML fallback (used only when PyYAML is unimportable)
# --------------------------------------------------------------------------- #

def _yaml_load(text: str) -> tuple[object | None, str | None]:
    """Load YAML text. Returns ``(data, error)``; ``error`` explains a failure.

    PyYAML is tried first. Without it, a minimal reader is used that understands
    only the top-level list-of-mappings shape ``entities.yaml`` actually has
    (``entities:`` / ``items:`` / ... followed by ``- name: x`` items). The
    fallback is documented here rather than silent: when even that cannot parse
    the text, the error is returned and the caller marks the source NOT ASSESSED.
    """
    try:
        import yaml  # type: ignore
    except ImportError:
        return _yaml_load_minimal(text)
    try:
        return yaml.safe_load(text), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def _yaml_load_minimal(text: str) -> tuple[object | None, str | None]:
    """Read the top-level ``key:`` sections of a list-of-mappings YAML file."""
    data: dict[str, list[dict]] = {}
    current_section: str | None = None
    current_item: dict | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        section = re.match(r"^([A-Za-z_][\w]*):\s*(\[\])?\s*$", raw)
        if section and not raw.startswith(" "):
            current_section = section.group(1)
            data.setdefault(current_section, [])
            current_item = None
            continue
        item = re.match(r"^\s*-\s+([\w]+):\s*(.*)$", raw)
        if item and current_section is not None:
            current_item = {item.group(1): item.group(2).strip().strip("\"'")}
            data[current_section].append(current_item)
            continue
        kv = re.match(r"^\s+([\w]+):\s*(.*)$", raw)
        if kv and current_item is not None:
            current_item[kv.group(1)] = kv.group(2).strip().strip("\"'")
    return data, None


# --------------------------------------------------------------------------- #
# Declared sources
# --------------------------------------------------------------------------- #

def read_registry(path: Path) -> tuple[list[dict], str]:
    """Read ``entities.yaml``; return ``(names, status)``.

    ``names`` is a list of ``{"name": ..., "source": "...", "section": ...}``.
    Only entries with an explicit ``name`` are returned; the template's empty
    ``[]`` sections and fully commented examples yield no names. ``status`` is
    ``assessed`` or a ``NOT ASSESSED - ...`` string.
    """
    if not path.is_file():
        return [], "NOT ASSESSED - no registry source (design/registry/entities.yaml absent)"
    data, error = _yaml_load(path.read_text(encoding="utf-8", errors="replace"))
    if error:
        return [], f"NOT ASSESSED - yaml reader unavailable ({error})"
    if not isinstance(data, dict):
        return [], "NOT ASSESSED - registry did not parse as a mapping"
    names: list[dict] = []
    for section in ("entities", "items", "formulas", "constants"):
        entries = data.get(section) or []
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and entry.get("name"):
                names.append(
                    {
                        "name": str(entry["name"]).strip(),
                        "section": section,
                        "source": display_path(path, repo_root()),
                    }
                )
    return names, "assessed"


def read_spec_names(path: Path, root: Path) -> list[dict]:
    """Read declared asset names from one spec-style markdown file.

    An asset is declared by (in priority order) its ``Naming`` field -- the actual
    filename -- or its ``ASSET-NNN`` heading. Both are optional in a partial spec,
    so a block with neither contributes nothing rather than a guessed name.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    rel = display_path(path, root)
    names: list[dict] = []
    for block in re.split(r"^##\s+", text, flags=re.MULTILINE)[1:]:
        heading = block.splitlines()[0].strip()
        asset_id = re.match(r"(ASSET-\d+)", heading)
        naming = re.search(r"\|\s*Naming\s*\|\s*([^|]+?)\s*\|", block, re.IGNORECASE)
        if naming:
            declared = naming.group(1).strip()
        elif asset_id:
            declared = asset_id.group(1)
        else:
            continue
        names.append(
            {
                "name": declared,
                "asset_id": asset_id.group(1) if asset_id else None,
                "heading": heading,
                "source": rel,
            }
        )
    # A spec file may also carry declared filenames as ``match:`` entries in a
    # fenced yaml block (the budget convention audit_assets.py reads). Count them
    # as declarations too, so one spec file serves both tools.
    for info, body in re.findall(r"^```(\w*)\s*\n(.*?)^```", text, re.MULTILINE | re.DOTALL):
        if info.lower() not in ("", "yaml", "yml", "spec"):
            continue
        for declared in re.findall(r"^\s*-\s*match\s*:\s*[\"']?([^\"'\n]+)[\"']?\s*$", body, re.MULTILINE):
            names.append(
                {
                    "name": declared.strip(),
                    "asset_id": None,
                    "heading": "(yaml match)",
                    "source": rel,
                }
            )
    # A filename declared both by a ``Naming`` row and by a yaml ``match`` is one
    # asset, not two; keep the first occurrence (the richer heading row).
    seen: set[str] = set()
    unique: list[dict] = []
    for item in names:
        key = normalise(item["name"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def read_spec_files(root: Path, glob_pattern: str) -> tuple[list[dict], str]:
    """Read every ``design/assets/specs/*.md``; return ``(names, status)``.

    Delegates block parsing to :func:`read_spec_names`.
    """
    files = sorted(root.glob(glob_pattern))
    if not files:
        return [], "NOT ASSESSED - no spec source (design/assets/specs/*.md absent)"
    names: list[dict] = []
    for path in files:
        names.extend(read_spec_names(path, root))
    return names, "assessed"


def read_markdown_table_names(path: Path, root: Path) -> tuple[list[dict], str]:
    """Read declared names from a markdown table file, if it exists.

    Emits every first-column-named row from tables that look like an inventory or
    manifest. Returns ``NOT ASSESSED - ...`` when the file is absent so an absent
    inventory is never confused with an empty one.
    """
    if not path.is_file():
        return [], f"NOT ASSESSED - {display_path(path, root)} absent"
    text = path.read_text(encoding="utf-8", errors="replace")
    names: list[dict] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("|") and index + 1 < len(lines) and re.match(
            r"^\s*\|[\s:|-]+\|\s*$", lines[index + 1]
        ):
            header = [cell.strip().lower() for cell in line.strip("|").split("|")]
            name_col = None
            for candidate in ("name", "asset", "asset id", "screen name", "element"):
                if candidate in header:
                    name_col = header.index(candidate)
                    break
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                if name_col is not None:
                    cells = [c.strip() for c in lines[index].strip().strip("|").split("|")]
                    if len(cells) > name_col and cells[name_col]:
                        names.append(
                            {
                                "name": cells[name_col],
                                "source": display_path(path, root),
                            }
                        )
                index += 1
            continue
        index += 1
    return names, "assessed"


# --------------------------------------------------------------------------- #
# Matching
# --------------------------------------------------------------------------- #

def normalise(value: str) -> str:
    """Normalise a declared name or filename stem for comparison.

    Lowercased; runs of non-alphanumerics collapse to a single ``_``; a trailing
    file extension is dropped. ``"VFX Frost Hit 01.png"`` -> ``"vfx_frost_hit_01"``.
    """
    stem = re.sub(r"\.[A-Za-z0-9]{1,5}$", "", value.strip())
    return re.sub(r"[^a-z0-9]+", "_", stem.lower()).strip("_")


def match_sets(declared: list[dict], produced: list[str]) -> dict:
    """Build matched / declared_but_missing / produced_but_undeclared.

    Matching is substring containment on the normalised forms, in either
    direction, with a 3-character floor to keep 1-2 character declared names from
    matching everything. A declared name can match several files (a sprite sheet
    plus its frames) and a file can satisfy several declared names; both are
    reported, not collapsed.
    """
    produced_norm = {path: normalise(Path(path).name) for path in produced}
    matched: list[dict] = []
    missing: list[dict] = []
    matched_paths: set[str] = set()

    for item in declared:
        key = normalise(item["name"])
        if len(key) < 3:
            missing.append({**item, "reason": "declared name too short to match"})
            continue
        hits = [
            path
            for path, stem in produced_norm.items()
            if key in stem or (len(stem) >= 3 and stem in key)
        ]
        if hits:
            for path in sorted(hits):
                matched.append(
                    {
                        "declared": item["name"],
                        "asset_id": item.get("asset_id"),
                        "source": item["source"],
                        "file": path,
                    }
                )
                matched_paths.add(path)
        else:
            missing.append(dict(item))

    undeclared = [
        {"file": path} for path in produced if path not in matched_paths
    ]
    return {
        "matched": sorted(matched, key=lambda row: (row["declared"], row["file"])),
        "declared_but_missing": sorted(
            missing, key=lambda row: (row["source"], row["declared"] if "declared" in row else row["name"])
        ),
        "produced_but_undeclared": sorted(undeclared, key=lambda row: row["file"]),
    }


# --------------------------------------------------------------------------- #
# Building / rendering
# --------------------------------------------------------------------------- #

def build_payload(args: argparse.Namespace) -> dict:
    """Read both sides, match them, and return the serialisable payload."""
    root = repo_root()
    roots = artifact_roots(root, args.root)
    override = Path(args.declared_spec) if args.declared_spec else None

    sources: dict[str, dict] = {}
    declared: list[dict] = []

    registry_names, registry_status = read_registry(root / REGISTRY_REL)
    sources["entities_yaml"] = {
        "path": REGISTRY_REL,
        "status": registry_status,
        "count": len(registry_names),
    }
    declared.extend(
        {**item, "declared_by": "entities.yaml"} for item in registry_names
    )

    if override is not None:
        # An explicit declared-source file (used for smoke tests, or to check a
        # batch against a spec kept somewhere other than design/assets/specs/).
        if override.is_file():
            spec_names = read_spec_names(override, root)
            spec_status = "assessed"
        else:
            spec_names = []
            spec_status = f"NOT ASSESSED - declared source {display_path(override, root)} absent"
        sources["specs"] = {
            "path": display_path(override, root),
            "status": spec_status,
            "count": len(spec_names),
        }
    else:
        spec_names, spec_status = read_spec_files(root, SPECS_GLOB)
        sources["specs"] = {
            "path": SPECS_GLOB,
            "status": spec_status,
            "count": len(spec_names),
        }
    declared.extend({**item, "declared_by": "spec"} for item in spec_names)

    for key, rel in (("entity_inventory", INVENTORY_REL), ("asset_manifest", MANIFEST_REL)):
        names, status = read_markdown_table_names(root / rel, root)
        sources[key] = {"path": rel, "status": status, "count": len(names)}
        declared.extend({**item, "declared_by": key} for item in names)

    produced = discover_artifacts(roots, root)
    sets = match_sets(declared, produced)

    return {
        "roots": [display_path(base, root) for base in roots],
        "declared_sources": sources,
        "declared_count": len(declared),
        "produced_count": len(produced),
        "produced": produced,
        "sets": sets,
    }


def render_markdown(payload: dict) -> str:
    """Render the sync payload as markdown sections (no verdict column)."""
    lines = [
        "# Art/game sync (raw -- no verdict)",
        "",
        "## Declared sources",
        "",
        "| Source | Status | Declared entries |",
        "|--------|--------|------------------|",
    ]
    for key, info in sorted(payload["declared_sources"].items()):
        lines.append(f"| {info['path']} | {info['status']} | {info['count']} |")
    sets = payload["sets"]
    lines += [
        "",
        "## Sets",
        "",
        f"- matched: {len(sets['matched'])}",
        f"- declared_but_missing: {len(sets['declared_but_missing'])}",
        f"- produced_but_undeclared: {len(sets['produced_but_undeclared'])}",
        "",
        "### declared_but_missing",
        "",
        "| Declared | Source | Reason |",
        "|----------|--------|--------|",
    ]
    for row in sets["declared_but_missing"]:
        lines.append(
            f"| {row.get('declared', row.get('name', ''))} | {row['source']} | {row.get('reason', '')} |"
        )
    lines += [
        "",
        "### produced_but_undeclared",
        "",
        "| File |",
        "|------|",
    ]
    for row in sets["produced_but_undeclared"]:
        lines.append(f"| {row['file']} |")
    lines += [
        "",
        "### matched",
        "",
        "| Declared | File |",
        "|----------|------|",
    ]
    for row in sets["matched"]:
        lines.append(f"| {row['declared']} | {row['file']} |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Returns 2 only when NO declared source was readable -- at least one source
    is NOT ASSESSED and zero declared names were extracted across all of them,
    so the sync verified nothing and must not read as a clean run. A
    partially-unreadable run still exits 0: the unreadable source surfaces as a
    NOT ASSESSED row in the payload for the report layer to call out.
    """
    parser = argparse.ArgumentParser(
        description="Cross-check produced artifacts against the declared set; numbers only."
    )
    parser.add_argument(
        "--root",
        action="append",
        default=None,
        help="Artifact root to scan (repeatable). Default: art-workspace/exports plus any engine asset root.",
    )
    parser.add_argument(
        "--declared-spec",
        default=None,
        help="Spec-style markdown file to read declared names from, instead of design/assets/specs/*.md.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "markdown", "both"),
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument("--json", action="store_true", help="Alias for --format json.")
    args = parser.parse_args(argv)
    if args.json:
        args.format = "json"

    payload = build_payload(args)
    if args.format in ("json", "both"):
        print(json.dumps(payload, indent=2, sort_keys=True))
    if args.format in ("markdown", "both"):
        print(render_markdown(payload))

    degraded = any(
        not str(info["status"]).startswith("assessed") for info in payload["declared_sources"].values()
    )
    return 2 if degraded and payload["declared_count"] == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
