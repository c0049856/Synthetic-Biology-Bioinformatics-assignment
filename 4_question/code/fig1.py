"""Reproduction of Figure 1 (panels a, b and c) from Curtis et al. (2026), ISME J 20, wrag195.

Panel a : log10 P_i against q/p, i = 1, N = 10^4  (Eq 1, Eq 2)      -> fig1a.py already did this
Panel b : inset, the same P_i on a linear (not log) axis near q/p = 1
Panel c : log10 P_i against log10 N for i = 1 and q/p very slightly above 1

Model (gambler's ruin), r = q/p:  P_i = (1 - r**i)/(1 - r**N)  for r != 1,  P_i = i/N for r == 1.
Boundary conditions: P_0 = 0, P_N = 1.  No time scale is involved.

ASSUMPTIONS THAT THE PAPER DOES NOT STATE (inferred, see ai_log.md and the printed checks):
  * Panel c x-axis is log10(N): dots are evenly spaced at 0.1 steps from 1.0.
  * Panel c shows THREE series, q/p = 1.0001, 1.00001, 1.000001, ending at log10 N = 6, 7, 8.
    The caption names only q/p = 1.0001 and the colour bar labels 1.000025 to 1.0001; neither
    matches what the dots follow. The inference rests on dot positions read off the figure by eye.
  * Axis limits of all panels were estimated by eye from a 300 dpi raster of page 3.

Provenance: generated with Claude (Anthropic); all equations and parameters must be checked
against the paper by the authors of this repo. No random numbers are used (no seed).

Page raster used for the comparison image was made with:
    pdftoppm -r 300 -f 3 -l 3 -png wrag195.pdf published/page
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mpmath
import numpy as np

from fig1a import I_START, N_TARGET, log10_prob, log10_prob_mp, log_abs_expm1

# (q/p - 1, largest log10 N, colour). Drawn in this order, so the darkest series is on top.
SERIES_C = [
    (1e-4, 6.0, "#c43a9d", "1.0001"),
    (1e-5, 7.0, "#5a2d9c", "1.00001"),
    (1e-6, 8.0, "#1b1b72", "1.000001"),
]


def log10_prob_vs_n(eps, n_values, i=I_START):
    """log10 P_i (Eq 1) for q/p = 1 + eps, over an array of target abundances N."""
    ln_r = np.log1p(eps)  # ln(q/p), accurate even when q/p is within 1e-6 of 1
    num = log_abs_expm1(np.array([i * ln_r]))[0]
    den = log_abs_expm1(np.asarray(n_values, dtype=float) * ln_r)
    return (num - den) / np.log(10)


def series_c(eps, xmax):
    x = np.round(np.arange(1.0, xmax + 1e-9, 0.1), 1)  # log10 N, 0.1 steps (read from the figure)
    return x, log10_prob_vs_n(eps, 10.0**x)


def validate():
    print("=== Panel c: endpoints against 60-digit arithmetic ===")
    for eps, xmax, _, label in SERIES_C:
        x, y = series_c(eps, xmax)
        ref = float(log10_prob_mp(label, I_START, int(10**xmax)))
        print(f"  q/p = {label:>8}: log10 N = {x[-1]:.1f} -> log10 P = {y[-1]:.4f} (mpmath {ref:.4f})")
        assert abs(y[-1] - ref) < 1e-6

    print("\n=== Panel c: dots read off the published figure by eye (+/- 0.5) vs computed ===")
    # (series label, log10 N, y read off the published panel)
    eyeballed = [("1.0001", 5.5, -17.7), ("1.0001", 6.0, -47.4),
                 ("1.00001", 6.5, -18.6), ("1.00001", 7.0, -48.4),
                 ("1.000001", 7.5, -19.8), ("1.000001", 8.0, -49.3)]
    lookup = {s[3]: s[0] for s in SERIES_C}
    for label, xn, y_pub in eyeballed:
        y_ours = float(log10_prob_vs_n(lookup[label], np.array([10.0**xn]))[0])
        print(f"  q/p = {label:>8}, log10 N = {xn}: published ~{y_pub:6.1f}   ours {y_ours:6.2f}")

    print("\n=== Why the three series have the same shape ===")
    a = float(log10_prob_vs_n(1e-4, np.array([1e5]))[0])
    b = float(log10_prob_vs_n(1e-5, np.array([1e6]))[0])
    print(f"  (q/p-1)=1e-4 at N=1e5: {a:.4f};  (q/p-1)=1e-5 at N=1e6: {b:.4f};  difference {b - a:.4f} (about -1)")


def make_figure(path):
    fig = plt.figure(figsize=(12, 5.2))
    gs = fig.add_gridspec(1, 2, width_ratios=[1, 1.05], wspace=0.28)
    ax_a = fig.add_subplot(gs[0])
    ax_c = fig.add_subplot(gs[1])
    grey = "#bdbdbd"

    # ---- panel a (same as fig1a.py), plus panel b as an inset ----
    r = np.linspace(0.92, 1.04, 2401)
    ax_a.plot(r, log10_prob(r, I_START, N_TARGET), color="black", linewidth=2.4)
    ax_a.axvline(1.0, color="black", linestyle=":", linewidth=1.4)
    ax_a.set_xlim(0.914, 1.046)
    ax_a.set_ylim(-180, 8)
    ax_a.set_xticks([0.95, 1.00])
    ax_a.set_yticks([0, -50, -100, -150])
    ax_a.set_xlabel("Ratio of deaths to births  (q/p)")
    ax_a.set_ylabel(r"$\log_{10}(P_i)$  probability of $10^4$ individuals")
    ax_a.grid(True, color=grey, linewidth=0.8)
    ax_a.set_axisbelow(True)
    ax_a.text(0.97, 0.97, "a", transform=ax_a.transAxes, ha="right", va="top", fontsize=14)

    ax_b = ax_a.inset_axes([0.175, 0.175, 0.395, 0.176])
    ax_b.plot(r, 10 ** log10_prob(r, I_START, N_TARGET), color="black", linewidth=2.4)
    ax_b.axvline(1.0, color="black", linestyle=":", linewidth=1.0)
    ax_b.set_xlim(0.914, 1.046)
    ax_b.set_ylim(-0.003, 0.085)
    ax_b.set_xticks([0.95, 1.00])
    ax_b.set_yticks([0, 0.02, 0.04, 0.06, 0.08])
    ax_b.tick_params(labelsize=6.5, length=2)
    ax_b.set_xlabel("Ratio of deaths to births (q/p)", fontsize=7, labelpad=2)
    ax_b.set_ylabel(r"$P_i$  Probability of $10^4$ individuals", fontsize=6.5, labelpad=2)
    ax_b.grid(True, color=grey, linewidth=0.5)
    ax_b.set_facecolor("white")
    ax_b.text(0.96, 0.92, "b", transform=ax_b.transAxes, ha="right", va="top", fontsize=11)

    # ---- panel c ----
    for eps, xmax, colour, label in SERIES_C:
        x, y = series_c(eps, xmax)
        ax_c.plot(x, y, "o", ms=4.2, color=colour, mec="#1b1b72", mew=0.5, label=f"q/p = {label}")
    ax_c.set_xlim(0.60, 9.2)
    ax_c.set_ylim(-52.4, 2.4)
    ax_c.set_xticks([2.5, 5.0, 7.5])
    ax_c.set_yticks([0, -10, -20, -30, -40, -50])
    ax_c.set_xlabel(r"$\log_{10}(N)$  population size")
    ax_c.set_ylabel(r"$\log_{10}(P_i)$")
    ax_c.grid(True, color=grey, linewidth=0.8)
    ax_c.set_axisbelow(True)
    ax_c.legend(loc="lower left", frameon=True, fontsize=9, title=r"$i = 1$", title_fontsize=9)
    ax_c.text(0.97, 0.97, "c", transform=ax_c.transAxes, ha="right", va="top", fontsize=14)

    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def make_comparison(repro_png, out_png):
    """Published Figure 1 above, our reproduction below, for the side-by-side record."""
    from PIL import Image

    page = Path("published/page-03.png")
    if not page.exists():
        print("published/page-03.png not found; skipping comparison image")
        return None
    pub = Image.open(page).crop((100, 180, 2350, 1060))
    rep = Image.open(repro_png)
    fig, axs = plt.subplots(2, 1, figsize=(11, 10.4))
    axs[0].imshow(pub)
    axs[0].set_title("Published: Curtis et al. (2026), Figure 1 (CC BY 4.0)", fontsize=11)
    axs[1].imshow(rep)
    axs[1].set_title("Reproduction: fig1.py", fontsize=11)
    for a in axs:
        a.axis("off")
    fig.tight_layout()
    fig.savefig(out_png, dpi=150)
    plt.close(fig)
    return out_png


if __name__ == "__main__":
    validate()
    out = make_figure("fig1_reproduction.png")
    print(f"\nSaved {out}")
    cmp_out = make_comparison(out, "fig1_comparison.png")
    if cmp_out:
        print(f"Saved {cmp_out}")
    print(f"Software: Python {sys.version.split()[0]}, numpy {np.__version__}, "
          f"matplotlib {matplotlib.__version__}, mpmath {mpmath.__version__}")
