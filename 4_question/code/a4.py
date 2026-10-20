"""Figure A4 (Appendix 4): time to extinction at q/p = 1 with carrying capacity n = 1e16 (red) and 1e4 (blue);
solid = analytic, dashed = recurrence.  Equations: Eq 4.17 (analytic) and the recurrence of Eq 4.10-4.12.

We compute the curves with the PORT of the authors' MATLAB (matlab_port.py; the MATLAB itself was not run) at
Delta t = 0.1 d (the value that matches A4 in noise.py part 0), and ALSO the paper's own Eq 4.17 with exact
harmonic numbers, then compare both with the published curves read from a 300 dpi raster (+/- 0.02 log10).
Calibration: frame x = 599.0..1910.5 px is i = 0..1000, frame bottom 1567.5 px is log10 = 0 and the top 548.5 px is 4.
Deterministic.  Provenance: generated with Claude (Anthropic); see ai_log.md.
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from durations import extinction_alpha1_eq28
from matlab_port import m_unbiased_extinction, m_unbiased_extinction_an

DT, N = 0.1, 1000
X0, X1, YB, YT = 599.0, 1910.5, 1567.5, 548.5
IMG = "published/a4hi-10.png"
CHECK = (100, 250, 500, 750, 990)


def measure(im, colour, i):
    col = int(round(X0 + (X1 - X0) * i / 1000.0))
    px = im[int(YT) + 4:int(YB) - 4, col - 1:col + 2, :]
    if colour == "blue":
        m = (px[..., 2] > 180) & (px[..., 0] < 90) & (px[..., 1] < 90)
    else:
        m = (px[..., 0] > 180) & (px[..., 1] < 90) & (px[..., 2] < 90)
    rows = np.flatnonzero(m.any(axis=1)) + int(YT) + 4
    if rows.size == 0:
        return []
    groups = np.split(rows, np.flatnonzero(np.diff(rows) > 3) + 1)
    return [4.0 * (YB - g.mean()) / (YB - YT) for g in groups]


def main():
    im = np.asarray(Image.open(IMG).convert("RGB")).astype(int)
    curves = {}
    for K in (10**16, 10**4):
        rec = m_unbiased_extinction(0.5, 1.0, DT, N, K)
        an = m_unbiased_extinction_an(0.5, 1.0, DT, N, K)
        eq = np.array([np.nan] + [float(extinction_alpha1_eq28(i, K, DT)) for i in range(2, N + 1)])
        curves[K] = dict(rec=rec, an=an, eq=eq)

    print(f"Delta t = {DT} d.  log10 days at i = 1000 (ours | published read by eye earlier):")
    for K, pub in ((10**16, (3.80, 3.78)), (10**4, (2.82, 2.67))):
        c = curves[K]
        print(f"  K = 1e{int(np.log10(K))}: MATLAB-port recurrence {np.log10(c['rec'][-1]):.3f} (pub ~{pub[0]}), "
              f"MATLAB-port analytic {np.log10(c['an'][-1]):.3f} (pub ~{pub[1]}), paper Eq 4.17 exact {np.log10(c['eq'][-1]):.3f}")

    print("\nMeasured published curves (log10 days) vs ours at several i:")
    print(f"{'i':>5} | {'colour':>5} | published curves found | ours: recurrence, analytic(MATLAB), Eq 4.17")
    for K, colour in ((10**4, "blue"), (10**16, "red")):
        c = curves[K]
        for i in CHECK:
            found = measure(im, colour, i)
            print(f"{i:>5} | {colour:>5} | {', '.join(f'{v:.3f}' for v in found):<22} | "
                  f"{np.log10(c['rec'][i-1]):.3f}, {np.log10(c['an'][i-1]):.3f}, {np.log10(c['eq'][i-1]):.3f}")

    fig, axs = plt.subplots(1, 2, figsize=(13, 5.2))
    axs[0].imshow(Image.open(IMG).crop((380, 440, 2020, 2050)))
    axs[0].axis("off")
    axs[0].set_title("Published Fig A4 (CC BY 4.0)", fontsize=11)
    x = np.arange(1, N + 1)
    for K, col in ((10**16, "red"), (10**4, "blue")):
        c = curves[K]
        axs[1].plot(x[1:], np.log10(c["an"][1:]), color=col, lw=1.6, label=f"Analytic (MATLAB line) n = 1e{int(np.log10(K))}")
        axs[1].plot(x, np.log10(c["rec"]), color=col, lw=1.6, ls="--", label=f"Recurrence n = 1e{int(np.log10(K))}")
        axs[1].plot(x[1:], np.log10(c["eq"][1:]), color="k", lw=0.8, ls=":", label="Eq 4.17 exact" if K == 10**4 else None)
    axs[1].set_xlim(0, 1000)
    axs[1].set_ylim(0, 4)
    axs[1].set_xlabel("i")
    axs[1].set_ylabel("Log(Time) (days)")
    axs[1].set_title("Ours (port of the authors' MATLAB, dt = 0.1 d)", fontsize=11)
    axs[1].legend(loc="lower right", fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig("figA4_comparison.png", dpi=150)
    print("\nSaved figA4_comparison.png")
    print(f"Software: Python {sys.version.split()[0]}, numpy {np.__version__}, matplotlib {matplotlib.__version__}")


if __name__ == "__main__":
    main()
