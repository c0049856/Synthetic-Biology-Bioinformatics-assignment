"""Figure 2 of Curtis et al. (2026): inoculum i needed for a 90% chance of reaching N = 10^6, vs q/p.

Equation: Eq 4 (Eq 1 rearranged for i):  i = ln(P_i * (q/p)^N + 1 - P_i) / ln(q/p),  P_i = 0.9, N = 1e6.
Boundary conditions: P_0 = 0, P_N = 1 (Eq 1).  Units: i in cells (plotted as log10 cells), q/p dimensionless.
Not stated in the paper (inferred, see unresolved_differences.md): the q/p grid.  The published dots run from
q/p = 0.990 to about 0.99998 in steps of 1e-5; q/p = 1 itself is excluded (Eq 4 is 0/0 there; limit is 0.9 N).

What this script does
  1. computes Eq 4 with mpmath (60 digits; (q/p)^N is tiny/huge so plain floats would lose the 1 - P_i term),
  2. checks Eq 4 against Eq 1: plugging the computed i back into Eq 1 must return 0.9,
  3. measures the published dots (page-03.png crop, calibrated on the printed tick marks) and compares,
  4. draws our figure next to the published one (fig2_comparison.png).
Deterministic: no random numbers.  Provenance: generated with Claude (Anthropic); see ai_log.md.
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mpmath as mp
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

mp.mp.dps = 60
N, P = 10**6, 0.9
STEP, FIRST, LAST_E = 1e-5, 0.99, 2e-5          # inferred grid: q/p = 0.99 ... 0.99998


def inoculum(r, n=N, p=P):
    r = mp.mpf(r)
    return mp.log(mp.mpf(p) * r**n + 1 - mp.mpf(p)) / mp.log(r)           # Eq 4


def eq1(i, r, n=N):
    r = mp.mpf(r)
    return (1 - r**i) / (1 - r**n)                                         # Eq 1


def grid():
    k = np.arange(0, int(round((1 - LAST_E - FIRST) / STEP)) + 1)
    return FIRST + k * STEP


def measure_published():
    """Centres of the isolated open circles in the top part of the published panel, in (q/p, log10 i)."""
    im = np.asarray(Image.open("published/fig2_crop.png").convert("L"))
    ypix = lambda y: 5.0 - (y - 40.5) / 208.2          # ticks: 5.0 at row 40.5, 2.5 at 561.5
    xval = lambda x: 0.990 + (x - 182.0) / 837.5 * 0.010   # ticks: 0.990 at col 182, 1.000 at col 1019.5
    lab, n = ndi.label(im[:, 160:1045] < 140)
    out = []
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if ys.size < 20 or ys.size > 400 or xs.max() - xs.min() > 14 or ys.max() - ys.min() > 14:
            continue
        if ys.mean() > 600:                       # tick labels below the frame, not data
            continue
        out.append((xval(xs.mean() + 160), ypix(ys.mean())))
    return sorted(out)


def main():
    r = grid()
    logi = np.array([float(mp.log10(inoculum(x))) for x in r])
    print(f"grid: {r.size} points from {r[0]:.5f} to {r[-1]:.5f}")
    print(f"log10 i at q/p = 0.990: {logi[0]:.4f} (published ~2.36);  at {r[-1]:.5f}: {logi[-1]:.4f} (published ~5.06)")
    print(f"limit q/p -> 1: i = 0.9 N = {0.9 * N:.3g} (log10 {np.log10(0.9 * N):.3f}); Eq 4 at q/p = 1 - 1e-9: "
          f"{float(inoculum(1 - mp.mpf('1e-9'))):.6g}")

    # check Eq 4 against Eq 1
    worst = max(abs(float(eq1(inoculum(x), x)) - P) for x in r[::50])
    print(f"Eq 1 evaluated at the Eq 4 inoculum returns 0.9 to within {worst:.1e} (worst of {r[::50].size} points)")

    pub = measure_published()
    print(f"\nisolated published dots found: {len(pub)} (top of the curve; the dense part merges into a band)")
    print(f"{'q/p (pub)':>10} {'log10 i pub':>11} | {'log10 i ours at nearest grid pt':>34} | diff")
    diffs = []
    for x, y in pub:
        xg = r[np.argmin(np.abs(r - x))]            # nearest grid point (the dots sit on the grid)
        ours = float(mp.log10(inoculum(xg)))
        diffs.append(y - ours)
        print(f"{x:>10.6f} {y:>11.3f} | {ours:>16.3f} (grid {xg:.5f}) | {y - ours:+.3f}")
    print(f"mean diff {np.mean(diffs):+.3f}, max |diff| {np.max(np.abs(diffs)):.3f} (reading accuracy about 0.02)")

    # figure
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
    axs[0].imshow(Image.open("published/fig2_crop.png").crop((30, 0, 1060, 680)))
    axs[0].set_title("Published Fig 2 (CC BY 4.0)", fontsize=11)
    axs[0].axis("off")
    axs[1].scatter(r, logi, s=14, facecolors="none", edgecolors="k", linewidths=0.6)
    axs[1].set_xlim(0.9895, 1.0004)
    axs[1].set_ylim(2.2, 5.2)
    axs[1].set_xlabel("q/p  Ratio of deaths to births")
    axs[1].set_ylabel("Log10 inoculum size for success")
    axs[1].set_title(f"Ours: Eq 4, N = 1e6, P_i = 0.9 ({r.size} points, step 1e-5)", fontsize=11)
    fig.tight_layout()
    fig.savefig("fig2_comparison.png", dpi=150)
    print("\nSaved fig2_comparison.png")
    print(f"Software: Python {sys.version.split()[0]}, numpy {np.__version__}, mpmath {mp.__version__}, "
          f"matplotlib {matplotlib.__version__}")


if __name__ == "__main__":
    main()
