"""Figure 4 of Curtis et al. (2026): (a) log10 ID50 against q/p; (b) theoretical dose-response curve for Salmonella.

Equations: Eq 10 (ID50: 0.5^(1/i) = q/p, i.e. i = ID50 = ln(0.5)/ln(q/p)) for (a);  Eq 9 (P_i = 1 - (q/p)^i) for (b).
Parameters: (a) grid of ID50 = 1, 2, ..., 1000 (inferred: the dots start at q/p = 0.5, 0.7071, 0.7937, ... and end at
log10 ID50 = 3.0); (b) q/p = 0.99999931 (caption; Salmonella ID50 ~ 1e6 gives 0.5^(1e-6) = 0.999999307).
Boundary conditions: Eq 9 is Eq 1 with N -> infinity (valid for q/p < 1, N >> 1) so only the absorbing state 0 matters.
Units: q/p dimensionless; dose = number of cells (plotted as log10 dose).  No time, so no Delta t.
Not stated in the paper: the dose grid in (b) (inferred from the dots, see output).
Published figure read from published/page-06.png (300 dpi, optional); calibration from the printed tick marks:
(a) x: 0.5 at 493.5 px, 1.0 at 1169.5 px; y: 3.0 at 248 px, 0 at 759 px.
(b) x: log10 dose 0 at 1370.5 px, 8 at 2061 px; y: P = 1 at 250 px, 0 at 757.5 px.
Deterministic.  Provenance: generated with Claude (Anthropic); see ai_log.md.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mpmath as mp
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

mp.mp.dps = 40
HERE = Path(__file__).resolve().parent
PAGE = HERE / "published" / "page-06.png"
QP_B = 0.99999931
A = dict(x0=493.5, x1=1169.5, xv0=0.5, xv1=1.0, y0=759.0, y1=248.0, yv0=0.0, yv1=3.0)
B = dict(x0=1370.5, x1=2061.0, xv0=0.0, xv1=8.0, y0=757.5, y1=250.0, yv0=0.0, yv1=1.0)


def to_val(c, px, axis):
    p0, p1, v0, v1 = (c["x0"], c["x1"], c["xv0"], c["xv1"]) if axis == "x" else (c["y0"], c["y1"], c["yv0"], c["yv1"])
    return v0 + (px - p0) / (p1 - p0) * (v1 - v0)


def prob(i, r=QP_B):
    """Eq 9: P_i = 1 - r^i, evaluated as -expm1(i ln r) to keep precision when r^i is near 1."""
    return -np.expm1(np.asarray(i, dtype=float) * np.log(r))


def circles(im, box):
    """Centres (px) of isolated open circles inside box = (xa, xb, ya, yb)."""
    xa, xb, ya, yb = box
    lab, n = ndi.label(im[ya:yb, xa:xb] < 150)
    out = []
    for k in range(1, n + 1):
        ys, xs = np.nonzero(lab == k)
        if 15 <= ys.size <= 120 and xs.max() - xs.min() <= 16 and ys.max() - ys.min() <= 16:
            out.append((xs.mean() + xa, ys.mean() + ya))
    return sorted(out)


def main():
    # ---------------- (a)
    ids = np.arange(1, 1001)
    qp = 0.5 ** (1.0 / ids)
    print("Panel a: q/p = 0.5^(1/i), y = log10 i;  i = 1..1000")
    print(f"  first q/p values: {', '.join(f'{v:.4f}' for v in qp[:6])};  last: q/p = {qp[-1]:.5f}, log10 ID50 = 3.0")
    # check Eq 10 against Eq 9: P_i at i = ID50 must be 0.5
    print(f"  check: Eq 9 at i = ID50 gives P = {float(1 - mp.mpf(qp[9]) ** 10):.6f} (i = 10)")
    ok = PAGE.exists()
    if not ok:
        print(f"\nNOTE: {PAGE} not found, so the comparison with the published figure is skipped.")
    else:
        im = np.asarray(Image.open(PAGE).convert("L")).astype(int)
        dots = circles(im, (480, 1190, 240, 770))
        print(f"\n  isolated published dots in panel a: {len(dots)}; first ones vs ours (i = 1, 2, 3, ...):")
        print(f"  {'dot':>3} | {'pub q/p':>8} {'pub log10 ID50':>14} | {'ours q/p':>8} {'ours log10 i':>12} | dq/p, dy")
        worst = 0.0
        for k, (cx, cy) in enumerate(dots[:12]):
            xq, yv = to_val(A, cx, "x"), to_val(A, cy, "y")
            print(f"  {k + 1:>3} | {xq:>8.4f} {yv:>14.3f} | {qp[k]:>8.4f} {np.log10(ids[k]):>12.3f} | "
                  f"{xq - qp[k]:+.4f}, {yv - np.log10(ids[k]):+.3f}")
            worst = max(worst, abs(xq - qp[k]), abs(yv - np.log10(ids[k])))
        print(f"  largest difference {worst:.4f} (1 pixel = {0.1 / 135.2:.4f} in q/p, {1 / 170.1:.4f} in log10)")

    # ---------------- (b)
    print(f"\nPanel b: P_i = 1 - (q/p)^i with q/p = {QP_B}")
    id50 = float(mp.log(0.5) / mp.log(mp.mpf(QP_B)))
    print(f"  ID50 = ln 0.5 / ln(q/p) = {id50:.4g} (log10 {np.log10(id50):.3f}); q/p implied by ID50 = 1e6: {0.5 ** 1e-6:.9f}")
    if ok:
        b_dots = circles(im, (1352, 2085, 700, 775))      # the isolated dots sitting on P ~ 0
        xs = [to_val(B, cx, "x") for cx, _ in b_dots]
        print(f"  isolated dots near P = 0 (log10 dose): {', '.join(f'{v:.2f}' for v in xs[:12])} ... ({len(xs)} found)")
        print(f"  implied doses i = 10^x: {', '.join(f'{10 ** v:.0f}' for v in xs[:8])} -> grid inferred as i = 1, then multiples of 100")
        print(f"\n  published curve (centre of the black stroke at each log10 dose) vs Eq 9:")
        print(f"  {'log10 dose':>10} | {'pub P':>7} | {'ours P':>7} | diff")
        diffs = []
        for xv in (4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0):
            col = int(round(B["x0"] + xv / 8.0 * (B["x1"] - B["x0"])))
            rows = np.flatnonzero((im[255:760, col - 1:col + 2] < 110).all(axis=1)) + 255
            if rows.size == 0:
                continue
            pv = to_val(B, rows.mean(), "y")
            ours = float(prob(10 ** xv))
            diffs.append(pv - ours)
            print(f"  {xv:>10.1f} | {pv:>7.3f} | {ours:>7.3f} | {pv - ours:+.3f}")
        print(f"  largest difference {np.max(np.abs(diffs)):.3f} (1 pixel = {1 / 507.5:.4f} in P; stroke is ~12 px thick)")

    fig, axs = plt.subplots(2, 2, figsize=(12, 9))
    if ok:
        pim = Image.open(PAGE)
        axs[0, 0].imshow(pim.crop((380, 200, 1215, 830)))
        axs[0, 1].imshow(pim.crop((1230, 200, 2160, 830)))
    for ax in axs[0]:
        ax.axis("off")
    axs[0, 0].set_title("Published Fig 4a (CC BY 4.0)", fontsize=11)
    axs[0, 1].set_title("Published Fig 4b (CC BY 4.0)", fontsize=11)
    axs[1, 0].scatter(qp, np.log10(ids), s=10, facecolors="none", edgecolors="k", linewidths=0.6)
    axs[1, 0].set(xlim=(0.46, 1.02), ylim=(-0.1, 3.1), xlabel="q/p The ratio of deaths to births", ylabel="Log10 ID50")
    axs[1, 0].set_title("Ours 4a: q/p = 0.5^(1/ID50), ID50 = 1..1000", fontsize=11)
    dose = np.unique(np.concatenate([[1], np.arange(100, 10**8 + 1, 100)])).astype(float)
    axs[1, 1].plot(np.log10(dose), prob(dose), color="k", lw=3)
    axs[1, 1].set(xlim=(-0.3, 8.3), ylim=(-0.03, 1.03), xlabel="Log10 dose", ylabel="Probability of infection")
    axs[1, 1].set_title(f"Ours 4b: P = 1-(q/p)^i, q/p = {QP_B}", fontsize=11)
    fig.tight_layout()
    fig.savefig(HERE / "fig4_comparison.png", dpi=130)
    print("\nSaved fig4_comparison.png")
    print(f"Software: Python {sys.version.split()[0]}, numpy {np.__version__}, mpmath {mp.__version__}, "
          f"matplotlib {matplotlib.__version__}")


if __name__ == "__main__":
    main()
