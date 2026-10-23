"""Turn saved runs into figures and summary tables comparable with the paper.

Usage:
    python analyze.py --tag Pmax7000_blocked0.1
Figures go to figures/<tag>/ and tables to figures/<tag>/summary_*.csv.
"""

import argparse
import glob
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import TwoSlopeNorm

HERE = os.path.dirname(os.path.abspath(__file__))
POLY_COLOR = {"P1": "#2a78d6", "P2": "#eb6834", "P3": "#1baf7a", "control": "#52514e"}
POLY_LABEL = {"P1": "P1 bacteria sequestrant", "P2": "P2 quorum quencher", "P3": "P3 dual action"}

plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e6e5e0", "grid.linewidth": 0.6,
                     "font.size": 9, "lines.linewidth": 1.6})


def load_condition(folder):
    """Stack all runs of one condition: dict of arrays shaped (runs, time)."""
    files = sorted(f for f in glob.glob(os.path.join(folder, "seed_*.npz")) if not f.endswith(".tmp.npz"))
    if not files:
        return None
    data = [np.load(f, allow_pickle=True) for f in files]
    keys = [k for k in data[0].files if k not in ("seed", "snapshots")]
    out = {k: np.stack([d[k] for d in data]) for k in keys}
    out["seeds"] = np.array([int(d["seed"]) for d in data])
    if "snapshots" in data[0].files:
        out["snapshots"] = data[0]["snapshots"]
    return out


def load_experiment(tag, exp):
    base = os.path.join(HERE, "runs", tag, exp)
    conds = {}
    for d in sorted(glob.glob(os.path.join(base, "*/"))):
        c = load_condition(d)
        if c is not None:
            conds[os.path.basename(os.path.normpath(d))] = c
    return conds


def mean_curve(c, key):
    return c[key].mean(axis=0)


def fold_change(c, ctrl, key="lum_per_bacterium"):
    """Ratio of run-averaged light per bacterium, polymer / no-polymer control (I10)."""
    return mean_curve(c, key) / np.maximum(mean_curve(ctrl, key), 1e-12)


def conc_of(name):
    m = re.search(r"_P(\d+)$", name)
    return int(m.group(1)) if m else 0


def conc_colors(concs):
    cmap = plt.get_cmap("Blues")
    return {c: cmap(0.35 + 0.65 * i / max(len(concs) - 1, 1)) for i, c in enumerate(concs)}


def recovery_time(t, lum):
    """Time to regain the initial light level after the minimum (Fig 4a/b; S15-S17)."""
    i_min = int(np.argmin(lum))
    after = np.nonzero(lum[i_min:] >= lum[0])[0]
    return t[i_min + after[0]] if after.size else np.nan


def foldchange_panels(conds, prefix, polymers, title, fname, outdir, n_runs_note):
    ctrl = conds.get(f"{prefix}control")
    if ctrl is None:
        return []
    t = ctrl["time"][0]
    fig, axes = plt.subplots(1, len(polymers), figsize=(3.6 * len(polymers), 3.2), sharey=True)
    axes = np.atleast_1d(axes)
    rows = []
    for ax, pol in zip(axes, polymers):
        names = sorted([n for n in conds if n.startswith(f"{prefix}{pol}_P")], key=conc_of)
        cols = conc_colors([conc_of(n) for n in names])
        ax.axhline(1, color=POLY_COLOR["control"], lw=1, label="control")
        for n in names:
            fc = fold_change(conds[n], ctrl)
            c = conc_of(n)
            ax.plot(t, fc, color=cols[c], label=f"{c}")
            i_max = int(np.argmax(fc))
            row = {"condition": n, "polymer": pol, "polymers_on_grid": c, "max_fold_change": fc.max(),
                   "time_of_max": t[i_max], "min_fold_change": fc.min(), "time_of_min": t[int(np.argmin(fc))]}
            for label, tp in (("early_5000", 5000), ("mid_15000", 15000), ("late_30000", 30000)):
                k = np.searchsorted(t, tp)
                row[f"fold_change_{label}"] = fc[min(k, len(fc) - 1)]
            rows.append(row)
        ax.set_yscale("log", base=2)
        ax.set_title(POLY_LABEL.get(pol, pol), color="#0b0b0b")
        ax.set_xlabel("time / a.u.")
    axes[0].set_ylabel("fold change in light per bacterium\n(polymer / control)")
    axes[-1].legend(title="polymers on grid", fontsize=7, title_fontsize=7, frameon=False, loc="best")
    fig.suptitle(f"{title}  ({n_runs_note})", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, fname))
    plt.close(fig)
    return rows


def write_csv(rows, path):
    if not rows:
        return
    import csv
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4g}" if isinstance(v, float) else v) for k, v in r.items()})


def analyze_strain(conds, strain, outdir, figname):
    n = len(conds["control"]["seeds"])
    note = f"model, mean of {n} runs"
    rows = foldchange_panels(conds, "", ["P1", "P2", "P3"], f"{strain}: fold change in light",
                             f"{figname}_fold_change.png", outdir, note)
    write_csv(rows, os.path.join(outdir, f"summary_{strain.lower()}.csv"))

    ctrl = conds["control"]
    t = ctrl["time"][0]
    pols = ["P1", "P2", "P3"]
    top = max(conc_of(k) for k in conds)

    # light (log) and bacteria numbers, comparable to Fig 4a and the OD curves S9-S14
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0))
    axes[0].plot(t, np.log10(mean_curve(ctrl, "lum_total")), color=POLY_COLOR["control"], label="control")
    axes[1].plot(t, mean_curve(ctrl, "n_bacteria"), color=POLY_COLOR["control"], label="control")
    for pol in pols:
        k = f"{pol}_P{top}"
        if k in conds:
            axes[0].plot(t, np.log10(mean_curve(conds[k], "lum_total")), color=POLY_COLOR[pol], label=f"{pol}, {top}")
            axes[1].plot(t, mean_curve(conds[k], "n_bacteria"), color=POLY_COLOR[pol], label=f"{pol}, {top}")
    axes[0].set_ylabel("log10 total light")
    axes[1].set_ylabel("number of bacteria")
    for ax in axes:
        ax.set_xlabel("time / a.u.")
    axes[1].legend(frameon=False, fontsize=7)
    fig.suptitle(f"{strain}: absolute light and growth ({note})", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, f"{figname}_light_and_growth.png"))
    plt.close(fig)

    # clustering over time, comparable to Fig 2a (shape only: model units, not micrometres)
    fig, ax = plt.subplots(figsize=(4.2, 3.0))
    ax.plot(t, mean_curve(ctrl, "mean_cluster_size"), color=POLY_COLOR["control"], label="control")
    for pol in pols:
        k = f"{pol}_P{top}"
        if k in conds:
            ax.plot(t, mean_curve(conds[k], "mean_cluster_size"), color=POLY_COLOR[pol], label=pol)
    ax.set_xlabel("time / a.u.")
    ax.set_ylabel("mean cluster size\n(bacteria per cluster, cell-weighted)")
    ax.legend(frameon=False, fontsize=7)
    ax.set_title(f"{strain}: clustering at {top} polymers", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, f"{figname}_clustering.png"))
    plt.close(fig)

    # recovery time (BB170, Fig 4b bottom inset; S15-S17)
    if strain == "BB170":
        rec_rows = [{"polymer": "control", "polymers_on_grid": 0,
                     "recovery_time": recovery_time(t, mean_curve(ctrl, "lum_total"))}]
        fig, axes = plt.subplots(1, 3, figsize=(9, 2.8), sharey=True)
        for ax, pol in zip(axes, pols):
            names = sorted([n for n in conds if n.startswith(f"{pol}_P")], key=conc_of)
            xs = [0] + [conc_of(n) for n in names]
            ys = [rec_rows[0]["recovery_time"]] + [recovery_time(t, mean_curve(conds[n], "lum_total")) for n in names]
            for x, y in zip(xs[1:], ys[1:]):
                rec_rows.append({"polymer": pol, "polymers_on_grid": x, "recovery_time": y})
            ax.plot(xs, ys, "o-", color=POLY_COLOR[pol], ms=5)
            ax.set_title(POLY_LABEL[pol], fontsize=9)
            ax.set_xlabel("polymers on grid")
        axes[0].set_ylabel("recovery time / a.u.")
        fig.suptitle(f"BB170: time to regain initial light ({note})", fontsize=10)
        fig.tight_layout()
        fig.savefig(os.path.join(outdir, f"{figname}_recovery_time.png"))
        plt.close(fig)
        write_csv(rec_rows, os.path.join(outdir, "summary_bb170_recovery.csv"))


def analyze_density(conds, outdir):
    rows = []
    for prefix, title in [("standard_", "B0 = 25, T = 15000 (S40)"), ("B0_2_", "B0 = 2 (S41)"),
                          ("T_10000_", "T = 10000 (S42)")]:
        if f"{prefix}control" not in conds:
            continue
        n = len(conds[f"{prefix}control"]["seeds"])
        r = foldchange_panels(conds, prefix, ["P3"], f"BB170 + P3, {title}",
                              f"S40-42_{prefix.rstrip('_')}.png", outdir, f"model, mean of {n} runs")
        rows += r
    write_csv(rows, os.path.join(outdir, "summary_density.csv"))


def analyze_sweep(conds, p_times, outdir):
    ctrl = conds.get("control")
    if ctrl is None:
        return
    t = ctrl["time"][0]
    n = len(ctrl["seeds"])
    keys = [k for k in conds if k != "control"]
    parsed = [re.match(r"KPB([\d.]+)_KPS([\d.]+)_P(\d+)", k) for k in keys]
    kpbs = sorted({float(m.group(1)) for m in parsed})
    kpss = sorted({float(m.group(2)) for m in parsed})
    concs = sorted({int(m.group(3)) for m in parsed})
    fc = {}
    for k, m in zip(keys, parsed):
        fc[(float(m.group(1)), float(m.group(2)), int(m.group(3)))] = fold_change(conds[k], ctrl)

    def at(curve, tp):
        return curve[min(np.searchsorted(t, tp), len(curve) - 1)]

    norm = TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3)
    cmap = plt.get_cmap("RdBu_r")
    rows = []
    for (kpb, kps, c), curve in fc.items():
        rows.append({"K_PB": kpb, "K_PS": kps, "polymers_on_grid": c,
                     **{f"fold_change_{lab}": at(curve, tp) for lab, tp in p_times.items()}})
    write_csv(rows, os.path.join(outdir, "summary_sweep.csv"))

    # bottom row of Fig 3: K_PB vs K_PS at each time, one figure per concentration (I11)
    for c in concs:
        fig, axes = plt.subplots(1, 3, figsize=(10, 3.2), sharey=True)
        for ax, (lab, tp) in zip(axes, p_times.items()):
            Z = np.array([[np.log2(at(fc[(kpb, kps, c)], tp)) for kps in kpss] for kpb in kpbs])
            im = ax.imshow(Z, origin="lower", cmap=cmap, norm=norm, aspect="auto")
            ax.set_xticks(range(len(kpss)), [f"{v:g}" for v in kpss])
            ax.set_yticks(range(len(kpbs)), [f"{v:g}" for v in kpbs])
            ax.set_xlabel("K_PS (polymer-signal affinity)")
            ax.set_title(f"{lab} (t = {tp})", fontsize=9)
            ax.grid(False)
            for i in range(len(kpbs)):
                for j in range(len(kpss)):
                    ax.text(j, i, f"{2 ** Z[i, j]:.2g}", ha="center", va="center", fontsize=6.5, color="#0b0b0b")
        axes[0].set_ylabel("K_PB (polymer-bacteria affinity)")
        cb = fig.colorbar(im, ax=axes, shrink=0.85)
        cb.set_label("log2 fold change\nblue = quenching, red = enhancement")
        fig.suptitle(f"Fig 3 (bottom) reproduction: {c} polymers on grid (model, mean of {n} runs)", fontsize=10, y=1.04)
        fig.savefig(os.path.join(outdir, f"fig3_affinity_P{c}.png"), bbox_inches="tight")
        plt.close(fig)

    # top row of Fig 3: [P] vs K_PB at K_PS = 0.1 (as heatmaps instead of 3D surfaces)
    kps0 = 0.1 if 0.1 in kpss else kpss[0]
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2), sharey=True)
    for ax, (lab, tp) in zip(axes, p_times.items()):
        Z = np.array([[np.log2(at(fc[(kpb, kps0, c)], tp)) for c in concs] for kpb in kpbs])
        im = ax.imshow(Z, origin="lower", cmap=cmap, norm=norm, aspect="auto")
        ax.set_xticks(range(len(concs)), [str(c) for c in concs], rotation=45)
        ax.set_yticks(range(len(kpbs)), [f"{v:g}" for v in kpbs])
        ax.set_xlabel("polymers on grid")
        ax.set_title(f"{lab} (t = {tp})", fontsize=9)
        ax.grid(False)
    axes[0].set_ylabel("K_PB")
    cb = fig.colorbar(im, ax=axes, shrink=0.85)
    cb.set_label("log2 fold change")
    fig.suptitle(f"Fig 3 (top) reproduction: K_PS = {kps0:g} (model, mean of {n} runs)", fontsize=10, y=1.04)
    fig.savefig(os.path.join(outdir, "fig3_concentration_vs_KPB.png"), bbox_inches="tight")
    plt.close(fig)


def analyze_snapshots(conds, outdir):
    order = ["P1", "P3", "P2", "control"]
    names = {pol: next((k for k in conds if k.startswith(pol)), None) for pol in order}
    rows = [(pol, names[pol]) for pol in order if names[pol]]
    if not rows:
        return
    snaps0 = conds[rows[0][1]]["snapshots"]
    ncol = len(snaps0)
    fig, axes = plt.subplots(len(rows), ncol, figsize=(1.6 * ncol, 1.6 * len(rows)), squeeze=False)
    for r, (pol, k) in enumerate(rows):
        for ccol, snap in enumerate(conds[k]["snapshots"]):
            ax = axes[r, ccol]
            ax.set_facecolor("#111111")
            col = np.where(snap["clustered"], "#9fc4f5", "#8a8a8a")
            ax.scatter(snap["by"] + 1, snap["bx"] + 1, s=9, c=col, marker="s", linewidths=0)
            ax.set_xlim(0, 50)
            ax.set_ylim(0, 50)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.grid(False)
            if r == 0:
                ax.set_title(f"t = {int(snap['t'])}", fontsize=7)
            if ccol == 0:
                ax.set_ylabel(pol, fontsize=9)
    fig.suptitle("Fig 2b reproduction: one run (blue = bacterium in a cluster)", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "fig2b_snapshots.png"))
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()
    outdir = os.path.join(HERE, "figures", args.tag)
    os.makedirs(outdir, exist_ok=True)
    p_times = {"early": 5000, "mid": 15000, "late": 30000}
    done = []
    for exp in ["test", "mm32", "bb170", "density", "sweep", "snapshots"]:
        conds = load_experiment(args.tag, exp)
        if not conds:
            continue
        if exp == "test":
            foldchange_panels(conds, "", ["P1"], "Test run: MM32 + P1", "test_fold_change.png", outdir,
                              f"mean of {len(conds['control']['seeds'])} runs")
        elif exp == "mm32":
            analyze_strain(conds, "MM32", outdir, "fig2c_MM32")
        elif exp == "bb170":
            analyze_strain(conds, "BB170", outdir, "fig4b_BB170")
        elif exp == "density":
            analyze_density(conds, outdir)
        elif exp == "sweep":
            analyze_sweep(conds, p_times, outdir)
        elif exp == "snapshots":
            analyze_snapshots(conds, outdir)
        done.append(exp)
    print(f"Analysed: {', '.join(done) or 'nothing found'}. Figures in {outdir}")


if __name__ == "__main__":
    main()
