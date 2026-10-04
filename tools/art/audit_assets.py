#!/usr/bin/env python3
"""Measure art artifacts and print the raw numbers. MEASURE ONLY.

This script never emits a verdict word (PASS/FAIL/COMPLIANT/WARNINGS). It walks
a set of asset roots, measures every image / audio / SVG file it finds, and
emits deterministic JSON (and optionally a markdown table). Comparing a
measurement to a spec is the caller's job -- see `.claude/skills/art-audit/`.

Rationale, from `references/art-pipeline-gotchas.md` section H: "Separate MEASURE
from VERDICT. A checker that both measures and judges will drift when the LLM
re-reasons the rule. A checker that only measures is a stable contract."

When `--spec <file>` is given, this script ATTACHES the declared budget to each
row as separate `spec_*` fields so the report layer has both sides of the
comparison in one place. It still does not compare them: no `over_budget` field,
no exit-code change for a mismatch. Exit code is about measurability only.

Usage:
    python audit_assets.py [--root DIR]... [--spec FILE] [--format json|markdown|both]
    python audit_assets.py --json                  # alias for --format json (default)

Exit codes:
    0  every discovered file was measured
    2  at least one file could not be read (the `errors` list names it)
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import math
import re
import sys
import wave
from pathlib import Path

try:
    from PIL import Image
except ImportError:  # pragma: no cover - resolved by tools/art/env.sh
    Image = None

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tga")
AUDIO_EXTS = (".ogg", ".wav", ".mp3")
SVG_EXTS = (".svg",)
ALL_EXTS = IMAGE_EXTS + AUDIO_EXTS + SVG_EXTS

#: Engine asset roots, in the order CLAUDE.md names them. Only roots that exist
#: on disk are scanned; a missing one is simply absent, never invented.
ENGINE_ASSET_ROOTS = ("assets", "Assets", "Content")


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

def repo_root() -> Path:
    """Return the project root (the directory holding ``project.yaml``).

    Resolved from this file's location (``tools/art/`` -> two parents up) so the
    output does not depend on the shell's working directory.
    """
    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "project.yaml").is_file():
        return candidate
    return Path.cwd().resolve()


def default_roots(root: Path) -> list[Path]:
    """Return the default measurement roots: the art workspace plus engine roots.

    ``art-workspace/exports`` is always first. Each of ``assets/`` (Godot),
    ``Assets/`` (Unity) and ``Content/`` (Unreal) is appended only when the
    directory actually exists -- two of the three never do.
    """
    roots = [root / "art-workspace" / "exports"]
    roots.extend(root / name for name in ENGINE_ASSET_ROOTS if (root / name).is_dir())
    return roots


def display_path(path: Path, root: Path) -> str:
    """Render ``path`` relative to ``root`` with forward slashes, when possible.

    Falls back to the absolute posix path so a root outside the project is still
    unambiguous. Deterministic: never consults the cwd or the clock.
    """
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def discover(roots: list[Path]) -> list[Path]:
    """Recursively collect candidate asset files under ``roots``, sorted.

    Dotfiles (e.g. ``.gitkeep``) are excluded. Directories that do not exist are
    skipped silently -- a root that was never created holds no files, which is
    not an error.
    """
    found: dict[str, Path] = {}
    for base in roots:
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if path.name.startswith("."):
                continue
            if path.suffix.lower() in ALL_EXTS:
                found[path.resolve().as_posix()] = path
    return [found[key] for key in sorted(found)]


# --------------------------------------------------------------------------- #
# Unit helpers
# --------------------------------------------------------------------------- #

def is_power_of_two(value: int) -> bool:
    """Return True when ``value`` is a positive power of two (1, 2, 4, ...)."""
    return value > 0 and (value & (value - 1)) == 0


def aspect_ratio(width: int, height: int) -> str:
    """Return the reduced ``W:H`` aspect ratio, or ``"W:H"`` unreduced if degenerate."""
    if width <= 0 or height <= 0:
        return f"{width}:{height}"
    divisor = math.gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def _parse_length(raw: str) -> float | None:
    """Parse a leading number out of an SVG length (``"64px"`` -> ``64.0``)."""
    match = re.match(r"\s*(-?\d+(?:\.\d+)?)", raw or "")
    return float(match.group(1)) if match else None


# --------------------------------------------------------------------------- #
# Per-format measurement
# --------------------------------------------------------------------------- #

def measure_image(path: Path) -> dict:
    """Measure a raster image: dimensions, mode, alpha, corner transparency.

    Returns a dict of raw values. Raises ``RuntimeError`` when Pillow is absent
    or the file cannot be decoded -- the caller records that as an error rather
    than guessing a value.
    """
    if Image is None:
        raise RuntimeError("Pillow is not importable (source tools/art/env.sh, use $GS_PYTHON)")
    with Image.open(path) as image:
        width, height = image.size
        mode = image.mode
        fmt = image.format or path.suffix.lstrip(".").upper()
        has_alpha = mode in ("RGBA", "LA", "PA", "La") or (
            "transparency" in image.info
        )
        row = {
            "kind": "image",
            "format": fmt.lower(),
            "width": width,
            "height": height,
            "colour_mode": mode,
            "has_alpha": bool(has_alpha),
            "aspect_ratio": aspect_ratio(width, height),
            "power_of_two": {
                "width": is_power_of_two(width),
                "height": is_power_of_two(height),
                "both": is_power_of_two(width) and is_power_of_two(height),
            },
        }
        # Corner alpha is recorded only for PNG: it is evidence for (or against)
        # a chroma-key cut, and only PNG in this pipeline is expected to carry a
        # cut-out alpha. Other formats get None, not a fabricated False.
        if path.suffix.lower() == ".png":
            rgba = image.convert("RGBA")
            corners = {
                "top_left": rgba.getpixel((0, 0))[3],
                "top_right": rgba.getpixel((width - 1, 0))[3],
                "bottom_left": rgba.getpixel((0, height - 1))[3],
                "bottom_right": rgba.getpixel((width - 1, height - 1))[3],
            }
            row["corner_alpha"] = corners
            row["all_corners_transparent"] = all(value == 0 for value in corners.values())
        else:
            row["corner_alpha"] = None
            row["all_corners_transparent"] = None
        return row


def measure_audio(path: Path) -> dict:
    """Measure an audio file: format, sample rate, channels, duration.

    Only the RIFF/WAVE container is decodable with the standard library, so only
    a ``.wav`` reports ``sample_rate``/``channels``/``duration``. For OGG and MP3
    those fields are ``None``: an honest "not derivable here", never a guess.
    """
    row = {
        "kind": "audio",
        "format": path.suffix.lstrip(".").lower(),
        "sample_rate": None,
        "channels": None,
        "duration": None,
    }
    if path.suffix.lower() != ".wav":
        return row
    with wave.open(str(path), "rb") as handle:
        frame_rate = handle.getframerate()
        frames = handle.getnframes()
        row["sample_rate"] = frame_rate
        row["channels"] = handle.getnchannels()
        row["duration"] = round(frames / frame_rate, 6) if frame_rate else None
    return row


def measure_svg(path: Path) -> dict:
    """Measure an SVG from its XML header: width, height and viewBox.

    Reads the ``<svg>`` opening tag with a regex -- no Inkscape call, no full XML
    parse, because a malformed header should yield ``None`` fields rather than an
    exception that hides the file's byte count. ``viewbox`` is a 4-float list
    (``min-x min-y width height``) or ``None``.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"<svg\b[^>]*>", text, re.IGNORECASE | re.DOTALL)

    def attr(name: str) -> str | None:
        if not match:
            return None
        found = re.search(
            rf'\b{name}\s*=\s*"([^"]*)"', match.group(0), re.IGNORECASE
        ) or re.search(rf"\b{name}\s*=\s*'([^']*)'", match.group(0), re.IGNORECASE)
        return found.group(1) if found else None

    width_raw = attr("width")
    height_raw = attr("height")
    viewbox_raw = attr("viewBox")
    viewbox = None
    if viewbox_raw:
        numbers = re.split(r"[\s,]+", viewbox_raw.strip())
        try:
            viewbox = [float(value) for value in numbers if value != ""]
        except ValueError:
            viewbox = None
    return {
        "kind": "svg",
        "format": "svg",
        "width": _parse_length(width_raw) if width_raw else None,
        "height": _parse_length(height_raw) if height_raw else None,
        "width_attr": width_raw,
        "height_attr": height_raw,
        "viewbox": viewbox,
    }


def measure_file(path: Path, root: Path) -> dict:
    """Measure one file and return its row (common fields + per-format fields).

    Raises ``RuntimeError`` on any decode failure; the caller turns that into an
    error entry instead of a partial row.
    """
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTS:
        row = measure_image(path)
    elif suffix in AUDIO_EXTS:
        row = measure_audio(path)
    elif suffix in SVG_EXTS:
        row = measure_svg(path)
    else:  # unreachable given discovery, kept explicit
        raise RuntimeError(f"unsupported extension {suffix!r}")

    row["path"] = display_path(path, root)
    row["bytes"] = path.stat().st_size
    return row


# --------------------------------------------------------------------------- #
# Spec loading (annotation only -- never a comparison)
# --------------------------------------------------------------------------- #

_SPEC_KEYS = ("match", "max_bytes", "width", "height", "power_of_two", "require_alpha")
_SPEC_ALIASES = {
    "file": "match",
    "asset": "match",
    "name": "match",
    "naming": "match",
    "filename": "match",
    "max_size": "max_bytes",
    "size": "max_bytes",
}


def _normalise_spec_entry(raw: dict) -> dict | None:
    """Coerce one spec record into ``{match, max_bytes, width, height, ...}``.

    Accepts the aliases above (a spec file is written by humans). Returns ``None``
    when the record names no target file, since a budget with nothing to attach
    to cannot be attached.
    """
    out: dict = {}
    for key, value in raw.items():
        key = str(key).strip().lower()
        key = _SPEC_ALIASES.get(key, key)
        if key not in _SPEC_KEYS:
            continue
        if key in ("max_bytes", "width", "height"):
            try:
                out[key] = int(float(str(value).strip()))
            except (TypeError, ValueError):
                continue
        elif key in ("power_of_two", "require_alpha"):
            out[key] = str(value).strip().lower() in ("true", "yes", "1")
        else:
            out[key] = str(value).strip()
    return out if out.get("match") else None


def load_spec(spec_path: Path) -> list[dict]:
    """Read a markdown or YAML spec and return normalised budget records.

    Markdown support: every fenced block whose info string is ``yaml``/``spec``
    (or empty and whose body parses as YAML) is tried, plus every markdown table
    whose header row contains a ``file``/``asset``/``match``/``name`` column.
    YAML support: a top-level list, or a mapping with an ``assets`` list.
    """
    text = spec_path.read_text(encoding="utf-8", errors="replace")
    if spec_path.suffix.lower() in (".yaml", ".yml"):
        return _spec_from_yaml(text)

    entries: list[dict] = []
    fence = re.compile(r"^```(\w*)\s*\n(.*?)^```", re.MULTILINE | re.DOTALL)
    for info, body in fence.findall(text):
        if info.lower() not in ("", "yaml", "yml", "spec"):
            continue
        entries.extend(_spec_from_yaml(body))
    entries.extend(_spec_from_markdown_tables(text))
    # De-duplicate while keeping file order (first declaration wins in matching).
    seen: set[str] = set()
    unique: list[dict] = []
    for entry in entries:
        if entry["match"].lower() in seen:
            continue
        seen.add(entry["match"].lower())
        unique.append(entry)
    return unique


def _spec_from_yaml(text: str) -> list[dict]:
    """Parse a YAML spec fragment into normalised entries (best effort)."""
    try:
        import yaml  # type: ignore
    except ImportError:  # pragma: no cover - PyYAML ships in the repo venv
        return _spec_from_yaml_minimal(text)
    try:
        data = yaml.safe_load(text)
    except Exception:
        return []
    records: list[dict] = []
    if isinstance(data, list):
        records = [item for item in data if isinstance(item, dict)]
    elif isinstance(data, dict):
        assets = data.get("assets")
        if isinstance(assets, list):
            records = [item for item in assets if isinstance(item, dict)]
        elif isinstance(assets, dict):  # name: {budgets}
            records = [dict(budgets or {}, match=name) for name, budgets in assets.items()]
        else:
            records = [data]
    out = []
    for record in records:
        entry = _normalise_spec_entry(record)
        if entry:
            out.append(entry)
    return out


def _spec_from_yaml_minimal(text: str) -> list[dict]:
    """Minimal reader for ``- match: name`` + indented budget keys.

    Used only when PyYAML is unavailable. It understands exactly the subset this
    tool's spec convention uses -- a list of mappings whose keys are the known
    budget names -- and nothing else. Anything it cannot read is dropped, and
    ``load_spec`` callers see fewer entries rather than wrong ones.
    """
    records: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        if re.match(r"^\s*#", line) or not line.strip():
            continue
        item = re.match(r"^\s*-\s*(\w+)\s*:\s*(.*)$", line)
        keyval = re.match(r"^\s+(\w+)\s*:\s*(.*)$", line)
        if item:
            if current:
                records.append(current)
            current = {item.group(1): item.group(2).strip().strip('"\'')}
        elif keyval and current is not None:
            current[keyval.group(1)] = keyval.group(2).strip().strip('"\'')
    if current:
        records.append(current)
    out = []
    for record in records:
        entry = _normalise_spec_entry(record)
        if entry:
            out.append(entry)
    return out


def _spec_from_markdown_tables(text: str) -> list[dict]:
    """Parse markdown tables whose header row has a target-file column."""
    entries: list[dict] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("|") and index + 1 < len(lines) and re.match(
            r"^\s*\|[\s:|-]+\|\s*$", lines[index + 1]
        ):
            header = [cell.strip().lower() for cell in line.strip("|").split("|")]
            if any(name in _SPEC_KEYS or name in _SPEC_ALIASES for name in header):
                index += 2
                while index < len(lines) and lines[index].strip().startswith("|"):
                    cells = [cell.strip() for cell in lines[index].strip().strip("|").split("|")]
                    if len(cells) == len(header):
                        entry = _normalise_spec_entry(dict(zip(header, cells)))
                        if entry:
                            entries.append(entry)
                    index += 1
                continue
        index += 1
    return entries


def attach_spec(rows: list[dict], entries: list[dict]) -> None:
    """Attach the declared budget (if any) to each row as ``spec_*`` fields.

    Matching is by basename: a record whose ``match`` contains ``*`` is treated
    as a glob, otherwise as a case-insensitive substring. The FIRST matching
    record wins, so spec authoring can put specific names before broad patterns.
    Every row gets the fields set (``None`` when nothing matched) so the JSON
    shape never varies between runs.
    """
    for row in rows:
        basename = Path(row["path"]).name.lower()
        match = None
        for entry in entries:
            pattern = entry["match"].lower()
            if "*" in pattern or "?" in pattern:
                if fnmatch.fnmatch(basename, pattern):
                    match = entry
                    break
            elif pattern in basename:
                match = entry
                break
        row["spec_match"] = match["match"] if match else None
        row["spec_max_bytes"] = match.get("max_bytes") if match else None
        row["spec_width"] = match.get("width") if match else None
        row["spec_height"] = match.get("height") if match else None
        row["spec_power_of_two"] = match.get("power_of_two") if match else None
        row["spec_require_alpha"] = match.get("require_alpha") if match else None


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #

def render_markdown(payload: dict) -> str:
    """Render the measurement payload as a markdown table (no verdict column)."""
    lines = [
        "# Art measurement (raw -- no verdict)",
        "",
        f"- Roots: {', '.join(payload['roots']) or '(none)'}",
        f"- Spec: {payload['spec'] or '(none)'}",
        f"- Files measured: {len(payload['files'])}",
        f"- Files unreadable: {len(payload['errors'])}",
        "",
        "| Path | Kind | Bytes | Format | W | H | Mode | Alpha | PoT | Aspect | Spec max_bytes | Spec W x H |",
        "|------|------|-------|--------|---|---|------|-------|-----|--------|----------------|------------|",
    ]
    for row in payload["files"]:
        pot = row.get("power_of_two")
        pot_text = (
            f"{pot['width']}/{pot['height']}" if isinstance(pot, dict) else "-"
        )
        width = row.get("width")
        height = row.get("height")
        spec_wh = (
            f"{row.get('spec_width')}x{row.get('spec_height')}"
            if row.get("spec_width") is not None or row.get("spec_height") is not None
            else "-"
        )
        lines.append(
            "| {path} | {kind} | {bytes} | {fmt} | {w} | {h} | {mode} | {alpha} | {pot} | {aspect} | {mb} | {swh} |".format(
                path=row["path"],
                kind=row.get("kind", "-"),
                bytes=row["bytes"],
                fmt=row.get("format", "-"),
                w=width if width is not None else "-",
                h=height if height is not None else "-",
                mode=row.get("colour_mode", "-"),
                alpha=row.get("has_alpha", "-"),
                pot=pot_text,
                aspect=row.get("aspect_ratio", "-"),
                mb=row.get("spec_max_bytes") if row.get("spec_max_bytes") is not None else "-",
                swh=spec_wh,
            )
        )
    if payload["errors"]:
        lines += ["", "## Unreadable files", ""]
        lines += [f"- {item['path']}: {item['error']}" for item in payload["errors"]]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #

def build_payload(args: argparse.Namespace) -> dict:
    """Discover, measure and annotate; return the serialisable payload dict."""
    root = repo_root()
    roots = [Path(item) for item in args.root] if args.root else default_roots(root)
    rows: list[dict] = []
    errors: list[dict] = []
    for path in discover(roots):
        try:
            rows.append(measure_file(path, root))
        except Exception as exc:  # measurement failed -> report, never invent
            errors.append({"path": display_path(path, root), "error": f"{type(exc).__name__}: {exc}"})
    rows.sort(key=lambda row: row["path"])
    errors.sort(key=lambda item: item["path"])

    spec_label = None
    if args.spec:
        spec_path = Path(args.spec)
        spec_label = spec_path.as_posix()
        try:
            entries = load_spec(spec_path)
        except Exception as exc:
            errors.append({"path": spec_label, "error": f"{type(exc).__name__}: {exc}"})
            entries = []
        attach_spec(rows, entries)
    else:
        attach_spec(rows, [])

    return {
        "roots": [display_path(base, root) for base in roots],
        "spec": spec_label,
        "files": rows,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns 0 when every file was measured, else 2."""
    parser = argparse.ArgumentParser(
        description="Measure art artifacts; emit numbers only, never a verdict."
    )
    parser.add_argument(
        "--root",
        action="append",
        default=None,
        help="Directory to scan (repeatable). Default: art-workspace/exports plus any engine asset root.",
    )
    parser.add_argument("--spec", default=None, help="Spec file (markdown or YAML) to attach declared budgets from.")
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
    if args.format == "markdown":
        print(render_markdown(payload))
    elif args.format == "both":
        print(render_markdown(payload))
    return 2 if payload["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
