"""Supplementary Figure A3 from Curtis et al. (2026): effect of random noise on the time to extinction.

What the paper says (Appendix 4, caption of Fig A3): "Random uniform noise trajectories (red lines,
absolute magnitude +- 2e-4) added to base q = 0.5002 (solid black line). Calculated using the
recurrence relationship equation 4.1."  Main text: "Simulations showed that random variations in the
value of alpha had only a modest effect on these predictions (Figure A3)."

What this script does
  Part 0  Which Delta t do appendix Figures A1-A4 use?  (compares curve start/end values read off the
          published figures by eye with the model under Delta t = 0.1 d and Delta t = 1/24 d)
  Part 1  Reruns the A3 experiment three ways, with recorded seeds and many runs, and reports the mean
          and the spread (not only the mean):
            "code"             as the authors' MATLAB extinction_noise is written (lines 88-110):
                               p_noisy = p + (0.5 - rand)*0.0005, one draw per trajectory, tau_1 computed
                               from the BASE p but the NEW q/p
            "code_consistent"  same noise, but tau_1 computed from the noisy p as well
            "caption"          q_noisy = 0.5002 + U(-2e-4, +2e-4), everything recomputed consistently
  Part 2  Figure: published A3 next to our "code" and "caption" versions.

Provenance: generated with Claude (Anthropic); every equation and parameter must be checked against the
paper by the authors of this repo.  Seeds: SEED (plot trajectories) and SEED + 1 (summary statistics).
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mpmath
import numpy as np

from durations import extinction_gt1, log10_M1n

SEED = 20261020
Q0, N = 0.5002, 1000
C = 1.0 / 24.0            # the authors' MATLAB default (c = 1/24); Part 0 checks it against the figure
N_PLOT, N_STATS = 20, 10000
P0 = 1.0 - Q0
ALPHA0 = Q0 / P0


# ------------------------------------------------------------------ the authors' forward recurrence
def tau1_exact(p, alpha, c=C):
    """tau_1 that keeps T finite (Eq 4.7): (c/p) * -ln(1 - 1/alpha); NaN if alpha <= 1."""
    with np.errstate(invalid="ignore", divide="ignore"):
        return -(c / p) * np.log(1.0 - 1.0 / alpha)


def extinction_curves(p_rec, alpha, tau1, n=N, c=C):
    """tau_{i+1} = alpha*tau_i - c/(p*i), T_i = cumsum(tau)   (Eqs 4.1-4.3), for R runs at once."""
    p_rec, alpha, tau1 = (np.atleast_1d(np.asarray(x, dtype=float)) for x in (p_rec, alpha, tau1))
    tau = np.empty((p_rec.size, n))
    tau[:, 0] = tau1
    with np.errstate(invalid="ignore", over="ignore"):
        for i in range(1, n):
            tau[:, i] = alpha * tau[:, i - 1] - c / (p_rec * i)
    return np.cumsum(tau, axis=1)


def draw(variant, runs, rng):
    u = rng.random(runs)
    if variant in ("code", "code_consistent"):
        p_noisy = P0 + (0.5 - u) * 0.0005                 # +/- 2.5e-4 on p, as in the MATLAB
        alpha = (1.0 - p_noisy) / p_noisy
        tau1 = tau1_exact(P0 if variant == "code" else p_noisy, alpha)
        return p_noisy, alpha, tau1
    if variant == "caption":
        q = Q0 + (2.0 * u - 1.0) * 2e-4                   # +/- 2e-4 on q, as in the caption
        p_noisy = 1.0 - q
        alpha = q / p_noisy
        return p_noisy, alpha, tau1_exact(p_noisy, alpha)
    raise ValueError(variant)


BASE = extinction_curves(P0, ALPHA0, tau1_exact(P0, ALPHA0))[0]    # the black line


# ------------------------------------------------------------------ Part 0: which Delta t?
def part0():
    print("=== Part 0: which Delta t do the appendix figures use? (log10 days; readings by eye, +/- 0.05) ===")
    readings = {
        "A1 (q/p=1.002, 1->n)":  dict(alpha=1.002, kind="M", start=-0.67, end=3.59),
        "A2 (q/p=1.002, extinction)": dict(alpha=1.002, kind="T", start=0.07, end=2.22),
        "A3 (q=0.5002, extinction)":  dict(alpha=ALPHA0, kind="T", start=-0.24, end=2.04),
    }
    for name, d in readings.items():
        out = []
        for dt in (0.1, 1 / 24):
            a = d["alpha"]
            p = 1 / (1 + a)
            if d["kind"] == "M":
                start, end = np.log10(dt / p), log10_M1n(a, 1000, dt)          # M_{1,2} = m_1 = dt/p
            else:
                t = extinction_gt1(a, [1, 1000], dt)
                start, end = np.log10(t[1]), np.log10(t[1000])
            out.append(f"dt={dt:.4f}: start {start:+.2f}, end {end:.2f}")
        print(f"  {name:<28} published start {d['start']:+.2f}, end {d['end']:.2f} | " + " | ".join(out))

    # A4: q/p = 1, T_1000 with carrying capacity K; recurrence and analytic as in the MATLAB code
    def H_code(x):  # authors' approximation of H_{x-1}, with 1/(12 (x-1)^3)
        return np.log(x - 1) + 0.57721 + 1 / (2 * (x - 1)) - 1 / (12 * (x - 1) ** 3)

    readings4 = {10**16: (3.78, 3.80), 10**4: (2.67, 2.82)}   # (analytic end, recurrence end), by eye
    for K, (an_pub, rec_pub) in readings4.items():
        for dt in (0.1, 1 / 24):
            i = 1000
            tau, T = 1 / 1000 + 2 * dt * H_code(K), 0.0   # MATLAB: Delta(1) = 1/N + 2 c H_n (N = 1000 points)
            for j in range(1, i + 1):
                T += tau
                tau -= 2 * dt / j
            # MATLAB unbiased_extinction_an, line 283: 2c*NN*(H_n - H_i) + NN/n + 2c*(H_i - 1), H_i = H_code(NN)
            an_code = 2 * dt * i * (H_code(K) - H_code(i)) + i / K + 2 * dt * (H_code(i) - 1)
            exact = float(2 * dt * i * (mpmath.harmonic(K - 1) - mpmath.harmonic(i - 1)) + mpmath.mpf(i) / K
                          + 2 * dt * (i - 1))
            print(f"  A4 (q/p=1, K=1e{int(np.log10(K))}) dt={dt:.4f}: recurrence {np.log10(T):.2f} "
                  f"(published ~{rec_pub}), MATLAB analytic line {np.log10(an_code):.2f} (published ~{an_pub}), "
                  f"paper Eq 4.17 {np.log10(exact):.2f}")


# ------------------------------------------------------------------ Part 1: the experiment
def part1():
    print(f"\n=== Part 1: noise experiment, base q = {Q0} (q/p = {ALPHA0:.6f}), dt = {C:.5f} d, "
          f"{N_STATS} runs per variant, seed {SEED + 1} ===")
    base_n = {n: BASE[n - 1] for n in (10, 100, 1000)}
    print("  base curve T_n (days): " + ", ".join(f"n={n}: {v:.4g}" for n, v in base_n.items()))
    results = {}
    for variant in ("code", "code_consistent", "caption"):
        rng = np.random.default_rng(SEED + 1)
        p_n, a_n, t1 = draw(variant, N_STATS, rng)
        curves = extinction_curves(p_n, a_n, t1)
        valid = np.isfinite(curves[:, -1]) & (a_n > 1)
        print(f"  [{variant}] q/p ranges {np.nanmin(a_n):.6f} to {np.nanmax(a_n):.6f}; "
              f"runs with q/p <= 1 (extinction time undefined): {100 * (1 - valid.mean()):.1f}%")
        for n in (10, 100, 1000):
            r = curves[valid, n - 1] / base_n[n]
            p5, p50, p95 = np.percentile(r, [5, 50, 95])
            print(f"      n={n:>4}: T/T_base  5%: {p5:.2f}  median: {p50:.2f}  95%: {p95:.2f}   mean: {r.mean():.2f}")
        results[variant] = (curves, valid)
    return results


# ------------------------------------------------------------------ Part 2: the figure
def part2():
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.9))
    pub = Path("published/app-08.png")
    if pub.exists():
        from PIL import Image
        axs[0].imshow(Image.open(pub).crop((250, 150, 800, 560)))
    axs[0].set_title("Published Fig A3 (CC BY 4.0)", fontsize=11)
    axs[0].axis("off")
    x = np.arange(1, N + 1)
    for ax, variant, title in ((axs[1], "code", "Ours: noise as in the MATLAB code"),
                               (axs[2], "caption", "Ours: noise as in the caption (consistent)")):
        rng = np.random.default_rng(SEED)
        p_n, a_n, t1 = draw(variant, N_PLOT, rng)
        curves = extinction_curves(p_n, a_n, t1)
        ok = (a_n > 1) & np.isfinite(curves[:, -1])
        for c in curves[ok]:
            ax.plot(x, np.log10(c), color="red", alpha=0.25, linewidth=1.6)
        ax.plot(x, np.log10(BASE), color="black", linewidth=2.4)
        ax.set_xlim(0, 1000)
        ax.set_ylim(-0.5, 2.5)
        ax.set_xlabel("n")
        ax.set_ylabel(r"Time $\log_{10}$(days)")
        ax.set_title(f"{title}\n({ok.sum()} of {N_PLOT} trajectories valid, seed {SEED})", fontsize=10)
        ax.grid(True, color="#d9d9d9", linewidth=0.7)
    fig.tight_layout()
    fig.savefig("figA3_comparison.png", dpi=150)
    plt.close(fig)
    print("\nSaved figA3_comparison.png")


if __name__ == "__main__":
    part0()
    part1()
    part2()
    print(f"\nSoftware: Python {sys.version.split()[0]}, numpy {np.__version__}, "
          f"matplotlib {matplotlib.__version__}, mpmath {mpmath.__version__}")
