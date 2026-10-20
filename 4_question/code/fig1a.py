"""Reproduction of Figure 1a from Curtis et al. (2026), ISME J 20, wrag195.

Figure 1a: log10 of the probability P_i that a single organism (i = 1) reaches an
abundance N = 10^4, plotted against the ratio of deaths to births, q/p.

Model (gambler's ruin, paper Eq 1 and Eq 2), with r = q/p:
    r != 1 :  P_i = (1 - r**i) / (1 - r**N)
    r == 1 :  P_i = i / N
Boundary conditions: P_0 = 0 (extinction is final), P_N = 1 (reaching N counts as success).
No time scale is involved (births and deaths are counted as events, not days).

Provenance: initial version generated with Claude (Anthropic), see ai_log.md.
Every equation and parameter below must be checked against the paper by the authors of this repo.

Numerical note: r**N with N = 10^4 overflows or loses all precision in plain floating
point for r somewhat above 1, so the calculation is done in log space using
log|e^x - 1| = x + log1p(-e^-x) for x > 0 and log(-expm1(x)) for x < 0.
No random numbers are used, so there is no seed.
"""
import sys

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mpmath
from mpmath import mp, mpf

I_START = 1        # starting abundance i (Figure 1 caption: single organism)
N_TARGET = 10**4   # target abundance N (Figure 1a caption)


def log_abs_expm1(x):
    """log|exp(x) - 1|, stable for large positive and small negative/positive x (x != 0)."""
    x = np.asarray(x, dtype=float)
    out = np.empty_like(x)
    pos = x > 0
    out[pos] = x[pos] + np.log1p(-np.exp(-x[pos]))
    out[~pos] = np.log(-np.expm1(x[~pos]))
    return out


def log10_prob(r, i=I_START, n=N_TARGET):
    """log10 of P_i from Eq 1 (r != 1) or Eq 2 (r == 1), computed in log space."""
    r = np.asarray(r, dtype=float)
    ln_r = np.log(r)
    res = np.empty_like(r)
    exact_one = ln_r == 0.0
    ok = ~exact_one
    # Eq 1: (1 - r^i)/(1 - r^n) = expm1(i ln r) / expm1(n ln r); both have the same sign
    res[ok] = (log_abs_expm1(i * ln_r[ok]) - log_abs_expm1(n * ln_r[ok])) / np.log(10)
    # Eq 2: P_i = i / N
    res[exact_one] = np.log10(i / n)
    return res


def log10_prob_mp(r, i, n, dps=60):
    """Reference value with arbitrary-precision arithmetic (direct use of Eq 1)."""
    mp.dps = dps
    r = mpf(r)
    if r == 1:
        return mpmath.log10(mpf(i) / n)
    return mpmath.log10((1 - r**i) / (1 - r**n))


def validate():
    print("=== Check 1: log-space code vs 60-digit arithmetic ===")
    worst = 0.0
    for r in ["0.92", "0.95", "0.99", "0.9999", "1.0001", "1.01", "1.04"]:
        a = float(log10_prob(np.array([float(r)]))[0])
        b = float(log10_prob_mp(r, I_START, N_TARGET))
        worst = max(worst, abs(a - b))
        print(f"  r = {r:>7}: log10 P = {a:.10f}  (mpmath {b:.10f})")
    print(f"  largest absolute difference in log10 P: {worst:.2e}")
    assert worst < 1e-8

    print("\n=== Check 2: numbers quoted in the paper's text (computed with mpmath) ===")
    p95 = 10 ** float(log10_prob_mp("0.95", 1, 10**4))
    print(f"  i=1, N=1e4, q/p=0.95  : P = {p95:.4f}; extinct:success = {(1 - p95) / p95:.1f}"
          "   (paper: ~20 times more likely to go extinct)")
    print(f"  i=1, N=1e4, q/p=1     : P = {10 ** float(log10_prob_mp(1, 1, 10**4)):.1e}   (Eq 2: 1/N)")
    v = float(log10_prob_mp("1.05", 1, 10**3))
    print(f"  i=1, N=1e3, q/p=1.05  : log10 P = {v:.2f}   (paper: less than 1e-21)")
    v = float(log10_prob_mp("1.00000001", 10**8, 10**10, dps=80))
    print(f"  i=1e8, N=1e10, q/p=1.00000001: log10 P = {v:.2f} (P = {10 ** v:.1e})   (paper: 1e-43)")


def make_figure(path):
    # Axis limits were estimated by eye from the published figure; the paper does not state them.
    r = np.linspace(0.92, 1.04, 2401)
    y = log10_prob(r)

    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.plot(r, y, color="black", linewidth=2.2)
    ax.axvline(1.0, color="black", linestyle=":", linewidth=1.2)
    ax.set_xlim(0.92, 1.04)
    ax.set_ylim(-180, 5)
    ax.set_xticks([0.95, 1.00])
    ax.set_yticks([0, -50, -100, -150])
    ax.set_xlabel("Ratio of deaths to births  (q/p)")
    ax.set_ylabel(r"$\log_{10}(P_i)$  probability of $10^4$ individuals")
    ax.grid(True, color="#d9d9d9", linewidth=0.7)
    ax.set_axisbelow(True)
    ax.text(0.9985, -100, "q/p = 1", fontsize=9, ha="right", va="center")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    return path


if __name__ == "__main__":
    validate()
    out = make_figure("fig1a_reproduction.png")
    print(f"\nSaved {out}")
    print(f"Software: Python {sys.version.split()[0]}, numpy {np.__version__}, "
          f"matplotlib {matplotlib.__version__}, mpmath {mpmath.__version__}")
