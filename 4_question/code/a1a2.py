"""Figures A1 and A2 (Appendix 3 and 4): comparison of recurrence and analytic solutions at q/p = 1.002.

  A1  time to go from 1 cell to n          recurrence Eqs 3.3-3.4;  analytic Eq 3.6   (MATLAB time_to_i, time_to_i_an)
  A2  time to go extinct starting from n   recurrence Eqs 4.2-4.3, 4.7; analytic Eq 4.8 (MATLAB extinction, extinction_an)
Parameters: q/p = 1.002, Delta t = 0.1 d (the value that matches these figures, see noise.py part 0), n = 1..1000.
Boundary conditions: A1: state 0 reflecting (m_0 = 0 / Delta(1) = 0), target n.  A2: absorbing at 0, bounded as n -> infinity
(this fixes tau_1, Eq 4.7).  Units: days (plotted as log10 days).

Three computations per figure:  (1) our independent code (durations.py), (2) the port of the authors' MATLAB
recurrence, (3) the port of the authors' MATLAB analytic formula (with its cube harmonic term, see C3).
The published curves are read from the 300 dpi renders (published/a12hi-05.png, a12hi-07.png), black dashed line over
red line; calibration: A1 frame x = 526.5..1872.5 px is n = 0..1000, y = 2486..1440.5 px is log10 = -1..4;
A2 frame x = 667.5..1771.5 px is n = 0..1000, y = 2054.5..1197.5 px is log10 = 0..2.5.  Reading accuracy ~ +/- 0.02.
The images are optional: without them the curves are still computed and the comparison is skipped.
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
from matlab_port import m_extinction, m_extinction_an, m_time_to_i, m_time_to_i_an

HERE = Path(__file__).resolve().parent
ALPHA, DT, N = 1.002, 0.1, 1000
P = 1 / (1 + ALPHA)
CHECK = (10, 50, 100, 250, 500, 750, 990)
FIG = {  # image, frame (x0, x1, ytop, ybottom), y value at ytop, y value at ybottom
    "A1": (HERE / "published" / "a12hi-05.png", (526.5, 1872.5, 1440.5, 2486.0), 4.0, -1.0),
    "A2": (HERE / "published" / "a12hi-07.png", (667.5, 1771.5, 1197.5, 2054.5), 2.5, 0.0),
}


def measure(img, spec, n):
    """log10 days of the (black over red) curve at index n, from the raster; None if not found."""
    x0, x1, yt, yb, vt, vb = *spec[1], spec[2], spec[3]
    col = int(round(x0 + (x1 - x0) * n / 1000.0))
    px = img[int(yt) + 4:int(yb) - 4, col - 1:col + 2, :]
    ink = (px.min(axis=2) < 200).any(axis=1)                      # anything clearly non-white (red or black)
    rows = np.flatnonzero(ink) + int(yt) + 4
    if rows.size == 0:
        return None
    # the legend sits above the curve in the upper left, so the curve is the LOWEST group of ink in the column
    rows = np.split(rows, np.flatnonzero(np.diff(rows) > 3) + 1)[-1]
    return vb + (vt - vb) * (yb - rows.mean()) / (yb - yt)


def curves():
    q = ALPHA * P
    ours_a1 = np.array([10 ** log10_M1n(ALPHA, n, DT) if n > 1 else np.nan for n in range(1, N + 1)])
    ours_a2 = extinction_gt1(ALPHA, list(range(1, N + 1)), DT)
    ours_a2 = np.array([ours_a2[n] for n in range(1, N + 1)])
    a1 = dict(ours=ours_a1, rec=m_time_to_i(P, DT, ALPHA, N), an=m_time_to_i_an(P, DT, ALPHA, N))
    a2 = dict(ours=ours_a2, rec=m_extinction(P, DT, ALPHA, N), an=m_extinction_an(P, DT, ALPHA, N))
    return {"A1": a1, "A2": a2}


def main():
    c = curves()
    print(f"q/p = {ALPHA}, p = {P:.6f}, Delta t = {DT} d, n = 1..{N}\n")
    for name in ("A1", "A2"):
        d = c[name]
        print(f"=== {name} ===")
        print(f"  log10 days at n = 2 / 1000: ours {np.log10(d['ours'][1]):+.3f} / {np.log10(d['ours'][-1]):.3f}")
        for key, lab in (("rec", "MATLAB-port recurrence"), ("an", "MATLAB-port analytic")):
            with np.errstate(all="ignore"):
                rel = np.abs(d[key][[9, 99, 999]] / d["ours"][[9, 99, 999]] - 1)
            print(f"  {lab:<24} relative difference to ours at n = 10, 100, 1000: "
                  + ", ".join(f"{v:.1e}" for v in rel))
    have = all(FIG[k][0].exists() for k in FIG)
    if not have:
        print("\nNOTE: published images not found in ./published, so the comparison with the published curves is skipped.")
    else:
        for name in ("A1", "A2"):
            img = np.asarray(Image.open(FIG[name][0]).convert("RGB")).astype(int)
            d = c[name]
            print(f"\nPublished {name} (read from raster) vs ours, log10 days:")
            print(f"  {'n':>5} | {'published':>9} | {'ours (indep.)':>13} | {'MATLAB analytic':>15} | diff pub-ours")
            diffs = []
            for n in CHECK:
                v = measure(img, FIG[name], n)
                o = np.log10(d["ours"][n - 1])
                diffs.append(v - o)
                print(f"  {n:>5} | {v:>9.3f} | {o:>13.3f} | {np.log10(d['an'][n - 1]):>15.3f} | {v - o:+.3f}")
            print(f"  mean diff {np.mean(diffs):+.3f}, max |diff| {np.max(np.abs(diffs)):.3f} (reading accuracy ~0.02)")

    fig, axs = plt.subplots(2, 2, figsize=(12, 9))
    x = np.arange(1, N + 1)
    for row, name in enumerate(("A1", "A2")):
        spec = FIG[name]
        if spec[0].exists():
            im = Image.open(spec[0])
            x0, x1, yt, yb = spec[1]
            axs[row, 0].imshow(im.crop((int(x0) - 190, int(yt) - 130, int(x1) + 60, int(yb) + 230)))
        axs[row, 0].axis("off")
        axs[row, 0].set_title(f"Published Fig {name} (CC BY 4.0)", fontsize=11)
        d = c[name]
        with np.errstate(invalid="ignore"):
            pass
        axs[row, 1].plot(x[1:], np.log10(np.abs(d["an"][1:])), color="red", lw=1.8, label="Analytic (MATLAB-port)")
        axs[row, 1].plot(x[1:], np.log10(d["rec"][1:]), color="black", lw=1.4, ls="--", label="Recurrence (MATLAB-port)")
        axs[row, 1].plot(x[1:], np.log10(d["ours"][1:]), color="#1f77b4", lw=0.9, ls=":", label="Ours, independent")
        axs[row, 1].set_xlim(0, 1000)
        axs[row, 1].set_ylim(-1, 4) if name == "A1" else axs[row, 1].set_ylim(0, 2.5)
        axs[row, 1].set_xlabel("n")
        axs[row, 1].set_ylabel("Log(Time) (days)")
        axs[row, 1].set_title(f"Ours, {name}: q/p = 1.002, dt = 0.1 d", fontsize=11)
        axs[row, 1].legend(loc="lower right", fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(HERE / "figA1A2_comparison.png", dpi=130)
    print("\nSaved figA1A2_comparison.png")
    print(f"Software: Python {sys.version.split()[0]}, numpy {np.__version__}, matplotlib {matplotlib.__version__}")


if __name__ == "__main__":
    main()
