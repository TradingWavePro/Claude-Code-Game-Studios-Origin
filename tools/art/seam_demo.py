"""Reproduction script for references/art-pipeline-gotchas.md sections 6 and 7.

Proves, on a live measurement, two claims:
  6. Blending cannot fix a seam — only generating periodicity can.
  7. A metric whose control comes from the transform measures the transform.

Run from the repo root:
    source tools/art/env.sh && "$GS_PYTHON" tools/art/seam_demo.py

Writes its two 3x3 render PNGs to art-workspace/work/tmp/ (a scratch dir, not
a production root).
"""
import os

import numpy as np

OUT_DIR = os.path.join("art-workspace", "work", "tmp")
rng = np.random.default_rng(20261003)
S = 128


def edge_mismatch(a):
    """Seam score: mean |left col - right col| + mean |top row - bottom row| (0-255)."""
    lr = np.abs(a[:, 0].astype(np.int32) - a[:, -1].astype(np.int32)).mean()
    tb = np.abs(a[0, :].astype(np.int32) - a[-1, :].astype(np.int32)).mean()
    return float(lr + tb) / 2.0


# ---------- 1. non-periodic noise tile ----------
nonper = rng.integers(0, 256, (S, S)).astype(np.uint8)

# ---------- 2. measure its edge mismatch ----------
score_raw = edge_mismatch(nonper)

# ---------- 3. naive blend fix: roll half + cross-fade, roll back ----------
def roll_blend_fix(a, band=S // 4):
    h, w = a.shape
    r = np.roll(a, w // 2, axis=1).astype(np.float64)
    ramp = np.linspace(0.0, 1.0, band)
    # blend the two halves across a band centred on the new seam
    c = w // 2
    left = r.copy()
    shifted = np.roll(r, -w // 2, axis=1)
    for i in range(band):
        x = (c - band // 2 + i) % w
        t = ramp[i]
        left[:, x] = (1 - t) * r[:, x] + t * shifted[:, x]
    return np.roll(left, w // 2, axis=1).clip(0, 255).astype(np.uint8)


fixed = roll_blend_fix(nonper)
score_naive = edge_mismatch(fixed)

# ---------- 4. modulo-lattice value noise: periodic BY CONSTRUCTION ----------
def periodic_value_noise(n, cells=16, seed=0):
    g = np.random.default_rng(seed)
    lattice = g.random((cells, cells))
    ys = np.arange(n) * cells / n
    xs = np.arange(n) * cells / n
    y0 = np.floor(ys).astype(int) % cells      # <-- modulo makes it periodic
    x0 = np.floor(xs).astype(int) % cells
    y1 = (y0 + 1) % cells
    x1 = (x0 + 1) % cells
    fy = ys - np.floor(ys)
    fx = xs - np.floor(xs)
    sy = fy * fy * (3 - 2 * fy)                # smoothstep
    sx = fx * fx * (3 - 2 * fx)
    top = lattice[np.ix_(y0, x0)] * (1 - sx) + lattice[np.ix_(y0, x1)] * sx
    bot = lattice[np.ix_(y1, x0)] * (1 - sx) + lattice[np.ix_(y1, x1)] * sx
    out = top * (1 - sy[:, None]) + bot * sy[:, None]
    return (out * 255).astype(np.uint8)


periodic = periodic_value_noise(S, cells=8, seed=7)
score_periodic = edge_mismatch(periodic)

print("=== SECTION 6: seam fixing by post-process ===")
print(f"non-periodic noise tile      left-vs-right/top-vs-bottom mismatch = {score_raw:.2f}")
print(f"  after naive roll+cross-fade                                     = {score_naive:.2f}")
print(f"modulo-lattice value noise (periodic by construction)             = {score_periodic:.2f}")

# extra: the 5 naive attempts named in the note, for the record
roll = np.roll(nonper, S // 2, axis=1)
print("\nreference naive variants on the same tile:")
print(f"  half-shift (no blend) mismatch     = {edge_mismatch(roll):.2f}")
mirror = np.hstack([nonper, nonper[:, ::-1]])
print(f"  mirror-quadrant seam (kernel)      = {edge_mismatch(mirror):.2f}")
kaleido = np.minimum(nonper, nonper[:, ::-1])
print(f"  kaleidoscope (min) seam            = {edge_mismatch(kaleido):.2f}")


# ================= SECTION 7: metric bug =================
def buggy_metric(a):
    """Measures the image AFTER mirroring -- mirroring forces the centre
    columns equal, so this returns ~0 for EVERY input, seam or not."""
    m = np.hstack([a, a[:, ::-1]])
    c = m.shape[1] // 2
    return float(np.abs(m[:, c - 1].astype(np.int32) - m[:, c].astype(np.int32)).mean())


def corrected_metric(a):
    """Interior-based control: median of ALL adjacent-column steps in the
    artifact itself, plus the wrap seam, taken before any transform."""
    steps = np.abs(np.diff(a.astype(np.int32), axis=1))
    interior_median = float(np.median(steps))
    wrap = float(np.abs(a[:, 0].astype(np.int32) - a[:, -1].astype(np.int32)).mean())
    return interior_median, wrap


seated = periodic.copy()
seamed = periodic.copy()
seamed[:, S // 2:] = np.clip(seamed[:, S // 2:].astype(np.int32) + 120, 0, 255).astype(np.uint8)

print("\n=== SECTION 7: a metric that never changes is measuring the transform ===")
for name, tile in (("seated (periodic)", seated), ("seamed (hard step)", seamed)):
    b = buggy_metric(tile)
    im, wr = corrected_metric(tile)
    print(f"{name:20s} buggy_metric={b:.2f}   corrected: interior_median={im:.1f} wrap_seam={wr:.2f}")

# 3x3 tiling render check -- look at these, the eye is not fooled by the algebra
from PIL import Image

os.makedirs(OUT_DIR, exist_ok=True)
seated_3x3 = os.path.join(OUT_DIR, "seam_seated_3x3.png")
seamed_3x3 = os.path.join(OUT_DIR, "seam_seamed_3x3.png")
Image.fromarray(np.tile(seated, (3, 3))).save(seated_3x3)
Image.fromarray(np.tile(seamed, (3, 3))).save(seamed_3x3)
print(f"\nwrote {seated_3x3} and {seamed_3x3}")
