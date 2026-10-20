"""Figure 5 of Curtis et al. (2026): (a) time for a single cell to reach n, (b) time to extinction from n,
for q/p = alpha = 1.01 (red), 1.001 (blue), 1.00001 (orange; the legend says 1.00001, Table 1 uses 1.0001).

Equations: (a) Eq 18 / recurrence Eq 16-17;  (b) Eq 27 / recurrence Eq 24-26.  Boundary conditions: (a) m_0 = 0 (cannot
leave 0 cells... i.e. reflecting at 0), target n;  (b) absorbing at 0, bounded T as n grows (fixes tau_1, Eq 25).
Units: the axes say HOURS.  Delta t is not given for this figure; Delta t = 1 hour (= 1/24 d, the repo MATLAB default,
also used for A3) reproduces the published curves (see output), whereas Delta t = 0.1 d = 2.4 h does not.
Computation: durations.py with dt = 1.0 (time then comes out in hours, since time is proportional to dt).
Published curves are read from published/page-07.png (300 dpi); frames: a x 511..1188.5 px = n 0..1000,
b x 1384.5..2062.5 px = n 0..1000, y 1379 px = 0 h and 844 px = 10000 h.  Reading accuracy about 100 h (~1 px = 19 h
plus line width).  The image is optional; without it the comparison is skipped.
Deterministic.  Provenance: generated with Claude (Anthropic); see ai_log.md.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from durations import extinction_gt1, log10_M1n

HERE = Path(__file__).resolve().parent
PAGE = HERE / "published" / "page-07.png"
ALPHAS = [(1.01, "red", "#ff0000"), (1.001, "blue", "#0000ff"), (1.00001, "orange", "#ff9d00")]
FRAMES = {"a": (511.0, 1188.5), "b": (1384.5, 2062.5)}
YTOP, YBOT, YMAX = 844.0, 1379.0, 10000.0
N = 1000
CHECK = {"a": (50, 100, 150, 200), "b": (50, 100, 200, 400, 600, 800, 950)}


def mask(px, colour):
    r, g, b = px[..., 0], px[..., 1], px[..., 2]
    if colour == "red":
        return (r > 190) & (g < 90) & (b < 90)
    if colour == "blue":
        return (b > 190) & (r < 90) & (g < 90)
    return (r > 200) & (g > 110) & (g < 190) & (b < 80)       # orange


def measure(img, panel, colour, n):
    x0, x1 = FRAMES[panel]
    col = int(round(x0 + (x1 - x0) * n / 1000.0))
    px = img[int(YTOP) + 3:int(YBOT) - 3, col - 1:col + 2, :]
    rows = np.flatnonzero(mask(px, colour).any(axis=1)) + int(YTOP) + 3
    if rows.size == 0:
        return None
    rows = np.split(rows, np.flatnonzero(np.diff(rows) > 3) + 1)[-1]      # lowest ink group: the legend is above
    v = YMAX * (YBOT - rows.mean()) / (YBOT - YTOP)
    if v > 8000 and n < 250:      # only the legend was found (curve hidden under another colour): not a data point
        return None
    return v


def compute(dt):
    out = {}
    for a, *_ in ALPHAS:
        M = np.array([np.nan] + [10 ** log10_M1n(a, n, dt) for n in range(2, N + 1)])   # M_{1,n}, hours; index n-1
        T = extinction_gt1(a, list(range(1, N + 1)), dt)
        out[a] = dict(M=M, T=np.array([T[n] for n in range(1, N + 1)]))
    return out


def main():
    ours = compute(1.0)
    other = compute(2.4)
    print("Delta t = 1 h (= 1/24 d).  Where the published curves leave the plot / end:")
    for a, *_ in ALPHAS:
        n10k = int(np.flatnonzero(ours[a]["M"] >= YMAX)[0]) + 1 if np.nanmax(ours[a]["M"]) >= YMAX else None
        n10k_alt = int(np.flatnonzero(other[a]["M"] >= YMAX)[0]) + 1
        print(f"  alpha = {a}: (a) M_1,n reaches 10000 h at n = {n10k} (dt = 2.4 h would give {n10k_alt}); "
              f"(b) T_1000 = {ours[a]['T'][-1]:.0f} h (dt = 2.4 h: {other[a]['T'][-1]:.0f})")
    print("  published, read from the figure: (a) about n = 250, 620, 800; (b) T_1000 about 600, 2350, 10000 h")

    if not PAGE.exists():
        print(f"\nNOTE: {PAGE} not found, so the comparison with the published curves is skipped.")
    else:
        img = np.asarray(Image.open(PAGE).convert("RGB")).astype(int)
        for panel, key in (("a", "M"), ("b", "T")):
            print(f"\nPanel {panel}: published (read from raster) vs ours with dt = 1 h and dt = 2.4 h, hours")
            print(f"  {'alpha':>8} {'n':>5} | {'published':>9} | {'ours dt=1h':>10} | {'ours dt=2.4h':>12} | pub - ours(1h)")
            diffs = []
            for a, colour, _ in ALPHAS:
                for n in CHECK[panel]:
                    v = measure(img, panel, colour, n)
                    if v is None:
                        continue
                    o, o2 = ours[a][key][n - 1], other[a][key][n - 1]
                    if o > YMAX * 1.02:       # beyond the plotted range
                        continue
                    diffs.append(v - o)
                    print(f"  {a:>8} {n:>5} | {v:>9.0f} | {o:>10.0f} | {o2:>12.0f} | {v - o:>+8.0f}")
            print(f"  mean diff {np.mean(diffs):+.0f} h, max |diff| {np.max(np.abs(diffs)):.0f} h (1 pixel = {YMAX / (YBOT - YTOP):.0f} h)")

    fig, axs = plt.subplots(2, 2, figsize=(12, 9))
    if PAGE.exists():
        im = Image.open(PAGE)
        axs[0, 0].imshow(im.crop((400, 780, 1250, 1450)))
        axs[0, 1].imshow(im.crop((1280, 780, 2130, 1450)))
    for ax in axs[0]:
        ax.axis("off")
    axs[0, 0].set_title("Published Fig 5a (CC BY 4.0)", fontsize=11)
    axs[0, 1].set_title("Published Fig 5b (CC BY 4.0)", fontsize=11)
    x = np.arange(1, N + 1)
    for ax, key, title in ((axs[1, 0], "M", "Ours 5a: time from 1 to n (Eq 18), dt = 1 h"),
                           (axs[1, 1], "T", "Ours 5b: time to extinction from n (Eq 27), dt = 1 h")):
        for a, _, hexc in ALPHAS:
            ax.plot(x, ours[a][key], color=hexc, lw=1.4, label=str(a))
        ax.set_xlim(0, 1000)
        ax.set_ylim(0, 10000)
        ax.set_xlabel("n")
        ax.set_ylabel("Time (Hours)")
        ax.set_title(title, fontsize=11)
        ax.legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(HERE / "fig5_comparison.png", dpi=130)
    print("\nSaved fig5_comparison.png")
    print(f"Software: Python {sys.version.split()[0]}, numpy {np.__version__}, matplotlib {matplotlib.__version__}")


if __name__ == "__main__":
    main()
