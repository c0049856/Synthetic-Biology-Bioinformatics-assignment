"""Run the simulation experiments and save one file per run.

Usage examples (run from the repository folder):
    python run.py test                       # quick check, ~1-2 minutes
    python run.py mm32                       # Fig 2c (MM32, P1/P2/P3, all concentrations, 10 runs)
    python run.py bb170                      # Fig 4b (BB170)
    python run.py density                    # Figs S40-S42 (BB170, P3, B0 and doubling time)
    python run.py sweep --runs 3             # Fig 3 (25 affinity pairs x concentrations)
    python run.py snapshots                  # Fig 2b-style pictures of one run
    python run.py all                        # everything above except test

Interpretation variants (see docs/interpretations.md):
    --scale 10        polymer counts 0-70000 instead of 0-7000 (I7)
    --blocked 0       small molecules cannot enter cells of another bacterium (I4)

Results go to runs/<tag>/<experiment>/<condition>/seed_<seed>.npz. Runs that already
exist are skipped, so an interrupted batch can simply be restarted.
"""

import argparse
import csv
import os
import sys
import time

import numpy as np
import yaml
from joblib import Parallel, delayed

from src.model import Simulation

HERE = os.path.dirname(os.path.abspath(__file__))


def load_params(path):
    with open(path) as f:
        return yaml.safe_load(f)


def conditions(experiment, p, scale, only_concs=None):
    """List of (condition name, Simulation keyword arguments) for an experiment."""
    base = p["polymer_counts"]
    if only_concs:
        base = [0] + [c for c in base if c in only_concs]
    concs = [int(c * scale) for c in base]
    pols = p["polymers"]
    out = []

    def polymer_set(strain, extra=None, prefix=""):
        extra = extra or {}
        out.append((f"{prefix}control", dict(strain=strain, **extra)))
        for name, aff in pols.items():
            for c in concs[1:]:
                out.append((f"{prefix}{name}_P{c}", dict(strain=strain, K_PB=aff["K_PB"], K_PS=aff["K_PS"],
                                                          n_polymers=c, **extra)))

    if experiment == "mm32":
        polymer_set("MM32")
    elif experiment == "bb170":
        polymer_set("BB170")
    elif experiment == "density":
        p3 = pols["P3"]
        for label, extra in [("standard", {}), ("B0_2", {"B0": 2}), ("T_10000", {"doubling_mean": 10000})]:
            out.append((f"{label}_control", dict(strain="BB170", **extra)))
            for c in concs[1:]:
                out.append((f"{label}_P3_P{c}", dict(strain="BB170", K_PB=p3["K_PB"], K_PS=p3["K_PS"],
                                                     n_polymers=c, **extra)))
    elif experiment == "sweep":
        out.append(("control", dict(strain="MM32")))
        for kpb in p["affinity_sweep"]:
            for kps in p["affinity_sweep"]:
                for c in concs[1:]:
                    out.append((f"KPB{kpb}_KPS{kps}_P{c}", dict(strain="MM32", K_PB=kpb, K_PS=kps, n_polymers=c)))
    elif experiment == "snapshots":
        c = concs[-1]
        out.append(("control", dict(strain="MM32")))
        for name, aff in pols.items():
            out.append((f"{name}_P{c}", dict(strain="MM32", K_PB=aff["K_PB"], K_PS=aff["K_PS"], n_polymers=c)))
    elif experiment == "test":
        c = concs[-1]
        out.append(("control", dict(strain="MM32")))
        out.append((f"P1_P{c}", dict(strain="MM32", K_PB=5.0, K_PS=0.0, n_polymers=c)))
    else:
        raise ValueError(f"unknown experiment {experiment}")
    return out


def one_run(params, outdir, cond, kwargs, seed, blocked, dt, t_end, snapshots, cluster_rule=None, bridges=True):
    path = os.path.join(outdir, cond, f"seed_{seed}.npz")
    if os.path.exists(path):
        return path, 0.0
    t0 = time.time()
    snap_times = [0, 5000, 10000, 15000, 20000, 25000, 30000] if snapshots else ()
    sim = Simulation(params, seed=seed, blocked_factor=blocked, dt=dt, record_snapshots=snap_times,
                     cluster_diffusion=cluster_rule, allow_bridges=bridges, **kwargs)
    res = sim.run(t_end=t_end)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    extra = {}
    if snapshots:
        extra["snapshots"] = np.array(sim.snapshots, dtype=object)
    np.savez_compressed(path + ".tmp.npz", seed=seed, **res, **extra)
    os.replace(path + ".tmp.npz", path)  # write-then-rename: no half-written files if interrupted
    return path, time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("experiment", choices=["test", "mm32", "bb170", "density", "sweep", "snapshots", "all"])
    ap.add_argument("--params", default=os.path.join(HERE, "params", "default.yaml"))
    ap.add_argument("--runs", type=int, default=None, help="independent runs per condition (default 10; sweep 3)")
    ap.add_argument("--scale", type=float, default=1, help="multiply polymer counts (I7): 1 or 10")
    ap.add_argument("--blocked", type=float, default=None, help="diffusion factor into another bacterium's cells (I4)")
    ap.add_argument("--dt", type=float, default=None, help="time step (default from params)")
    ap.add_argument("--t-end", type=float, default=None)
    ap.add_argument("--jobs", type=int, default=-1, help="parallel processes (-1 = all cores)")
    ap.add_argument("--concs", default=None,
                    help="only these polymer counts (before --scale), e.g. 1000,4000,7000; the control is always run")
    ap.add_argument("--cluster-diffusion", choices=["D_B_over_m", "D_S_over_m"], default=None,
                    help="I5: cluster diffusion rule (default D_B_over_m)")
    ap.add_argument("--no-bridges", action="store_true",
                    help="control experiment: polymers coat bacteria but cannot link them into clusters")
    ap.add_argument("--polymers", default=None, help="only these polymer types, e.g. P1 or P1,P3")
    ap.add_argument("--tag", default=None, help="name of the results folder (default from scale and blocked)")
    args = ap.parse_args()

    p = load_params(args.params)
    blocked = args.blocked if args.blocked is not None else p["blocked_factor"]
    tag = args.tag or f"Pmax{int(p['polymer_counts'][-1] * args.scale)}_blocked{blocked:g}"
    if args.cluster_diffusion == "D_S_over_m" and not args.tag:
        tag += "_clusterDS"
    if args.no_bridges and not args.tag:
        tag += "_nobridge"
    only = [int(c) for c in args.concs.split(",")] if args.concs else None
    exps = ["mm32", "bb170", "density", "sweep", "snapshots"] if args.experiment == "all" else [args.experiment]

    for exp in exps:
        n_runs = args.runs or {"sweep": 3, "snapshots": 1, "test": 2}.get(exp, p["n_runs"])
        t_end = args.t_end or (3000 if exp == "test" else p["t_end"])
        seeds = [p["base_seed"] + k for k in range(n_runs)]
        outdir = os.path.join(HERE, "runs", tag, exp)
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "seeds.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["run", "seed"])
            w.writerows(enumerate(seeds))
        conds = conditions(exp, p, args.scale, only)
        if args.polymers:
            keep = args.polymers.split(",")
            conds = [(c, kw) for c, kw in conds if "control" in c or any(c.startswith(k + "_") for k in keep)]
        jobs = [(c, kw, s) for c, kw in conds for s in seeds]
        print(f"[{tag}/{exp}] {len(conds)} conditions x {n_runs} runs = {len(jobs)} simulations", flush=True)
        t0 = time.time()
        results = Parallel(n_jobs=args.jobs, verbose=5)(
            delayed(one_run)(p, outdir, c, kw, s, blocked, args.dt, t_end, exp == "snapshots",
                             args.cluster_diffusion, not args.no_bridges) for c, kw, s in jobs)
        took = [r[1] for r in results if r[1] > 0]
        print(f"[{tag}/{exp}] done in {(time.time() - t0) / 60:.1f} min "
              f"({len(took)} new runs, {np.mean(took) if took else 0:.0f} s each)", flush=True)
    print(f"Now run:  python analyze.py --tag {tag}")


if __name__ == "__main__":
    sys.exit(main())
