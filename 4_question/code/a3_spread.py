"""Gap 2: compare the SPREAD of the red noise lines in published Figure A3 with our simulations.

Method
  1. Take a 400 dpi raster of appendix page 8 (published/a3hi-08.png), find the plot frame, and calibrate the
     axes (x: n = 0..1000, y: log10 days = -0.5..2.5, as printed on the axes).
  2. At n = 250, 500, 990 measure (a) the black base curve and (b) the top and bottom of the coloured band
     (the red lines). Report the band as 'up' = top - black and 'down' = black - bottom, in log10 days.
  3. Simulate the experiment many times (K experiments of L noise lines each, seed below), measure the same
     'up' and 'down' for each experiment, and see where the published values fall in that distribution.
The number of red lines in the published figure is not stated, so L = 10, 20 and 40 are all tried.
Measurement uncertainty from the raster is about +/- 0.02 log10 units (line width and anti-aliasing).

Provenance: generated with Claude (Anthropic); AI-generated, see ai_log.md.  Seed: SEED_A3 for all simulations.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from noise import BASE, SEED, draw, extinction_curves

SEED_A3 = SEED + 3          # 20261023
NS = (250, 500, 990)
K_EXPERIMENTS = 2000
CHUNK = 5000
IMG = Path("published/a3hi-08.png")
CROP = (700, 400, 2530, 1790)   # generous box around the plot at 400 dpi


def clusters(idx):
    """Centres of runs of consecutive integers."""
    if idx.size == 0:
        return []
    splits = np.flatnonzero(np.diff(idx) > 1) + 1
    return [g.mean() for g in np.split(idx, splits)]


def measure_published():
    im = np.asarray(Image.open(IMG).convert("RGB").crop(CROP)).astype(int)
    dark = (im < 110).all(axis=2)
    cols, rows = dark.sum(axis=0), dark.sum(axis=1)
    xs = clusters(np.flatnonzero(cols > 0.5 * cols.max()))
    ys = clusters(np.flatnonzero(rows > 0.5 * rows.max()))
    x0, x1, ytop = xs[0], xs[-1], ys[0]
    # a third long dark line (caption/text) can sit below the plot, so pick the horizontal line closest to the
    # frame height expected from the page-8 layout at 130 dpi (327 px high for 440 px wide, i.e. 0.743)
    ybot = min(ys[1:], key=lambda y: abs(y - (ytop + 0.743 * (x1 - x0))))
    print(f"Frame found at x = {x0:.1f}..{x1:.1f} px, y = {ytop:.1f}..{ybot:.1f} px (crop coordinates)")
    to_log = lambda row: 2.5 - 3.0 * (row - ytop) / (ybot - ytop)
    out = {}
    for n in NS:
        col = int(round(x0 + (x1 - x0) * n / 1000.0))
        r0, r1 = int(ytop) + 6, int(ybot) - 6
        band = im[r0:r1, col - 1:col + 2, :].mean(axis=1)          # average the 3 neighbouring columns
        nonwhite = np.flatnonzero(band.min(axis=1) < 245) + r0
        black = np.flatnonzero((im[r0:r1, col - 1:col + 2, :] < 110).all(axis=2).any(axis=1)) + r0
        centre = black.mean()
        out[n] = dict(black=to_log(centre),
                      up=to_log(nonwhite.min()) - to_log(centre),      # top of the band (smallest pixel row)
                      down=to_log(centre) - to_log(nonwhite.max()))    # bottom of the band
    return out


def stepnoise_curves(m, rng, n=1000):
    """'per_step' reading of the caption: a fresh uniform +/-2e-4 added to q at EVERY step i of the recurrence
    (a noise 'trajectory' along the population size), with tau_1 taken from the base case."""
    from noise import ALPHA0, C, P0, Q0, tau1_exact
    q = Q0 + (2.0 * rng.random((m, n)) - 1.0) * 2e-4
    p = 1.0 - q
    alpha = q / p
    tau = np.empty((m, n))
    tau[:, 0] = tau1_exact(P0, ALPHA0)
    for i in range(1, n):
        tau[:, i] = alpha[:, i - 1] * tau[:, i - 1] - C / (p[:, i - 1] * i)
    return np.cumsum(tau, axis=1)


def simulate_envelopes(variant, lines, experiments, rng):
    """Returns arrays up, down of shape (experiments, len(NS)) in log10 days relative to the base curve."""
    total = lines * experiments
    cols = [n - 1 for n in NS]
    picked = np.empty((total, len(NS)))
    for start in range(0, total, CHUNK):
        m = min(CHUNK, total - start)
        if variant == "per_step":
            picked[start:start + m] = stepnoise_curves(m, rng)[:, cols]
        else:
            p_n, a_n, t1 = draw(variant, m, rng)
            picked[start:start + m] = extinction_curves(p_n, a_n, t1)[:, cols]
    with np.errstate(invalid="ignore", divide="ignore"):
        logt = np.log10(picked).reshape(experiments, lines, len(NS))
    logt[~np.isfinite(logt)] = np.nan
    base = np.log10(BASE[cols])
    up = np.nanmax(logt, axis=1) - base
    down = base - np.nanmin(logt, axis=1)
    return up, down


def main():
    print("=== Published Figure A3 (measured from the 400 dpi raster; +/- 0.02 log10) ===")
    pub = measure_published()
    for n in NS:
        d = pub[n]
        print(f"  n = {n:>4}: black curve {d['black']:.3f} (our base {np.log10(BASE[n - 1]):.3f}); "
              f"red band reaches +{d['up']:.3f} above and -{d['down']:.3f} below (log10 days)")

    print(f"\n=== Our simulated experiments (seed {SEED_A3}, {K_EXPERIMENTS} experiments per row) ===")
    print("  'up' / 'down' = how far the highest / lowest red line is above / below the black curve (log10 days).")
    print("  rank = share of simulated experiments whose value is at or below the published one.\n")
    rng = np.random.default_rng(SEED_A3)
    for variant in ("caption", "code", "per_step"):
        for lines in (10, 20, 40):
            up, down = simulate_envelopes(variant, lines, K_EXPERIMENTS, rng)
            for j, n in enumerate(NS):
                line = (f"  [{variant:<7} L={lines:>2}] n={n:>4}: "
                        f"up median {np.nanmedian(up[:, j]):.3f} (5-95%: {np.nanpercentile(up[:, j], 5):.3f}-"
                        f"{np.nanpercentile(up[:, j], 95):.3f}), published {pub[n]['up']:.3f}, "
                        f"rank {np.mean(up[:, j] <= pub[n]['up']):.2f} | "
                        f"down median {np.nanmedian(down[:, j]):.3f} (5-95%: {np.nanpercentile(down[:, j], 5):.3f}-"
                        f"{np.nanpercentile(down[:, j], 95):.3f}), published {pub[n]['down']:.3f}, "
                        f"rank {np.mean(down[:, j] <= pub[n]['down']):.2f}")
                print(line)
            print()
    print(f"Software: Python {sys.version.split()[0]}, numpy {np.__version__}")


if __name__ == "__main__":
    main()
