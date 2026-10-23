"""Sanity checks for the model. Run with:  python -m pytest tests   (or: python tests/test_model.py)"""

import os
import sys

import numpy as np
import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.model import Simulation  # noqa: E402

P = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), "..", "params", "default.yaml")))


def total_signal(r):
    return r["signal_free"] + r["signal_on_bacteria"] + r["signal_on_polymers"]


def test_signal_conserved_mm32():
    """MM32 makes no signal, so binding, unbinding and diffusion must keep the total at S0 = 10000."""
    r = Simulation(P, "MM32", K_PB=5, K_PS=10, n_polymers=3000, seed=1).run(t_end=1500)
    assert (total_signal(r) == P["strains"]["MM32"]["S0"]).all()


def test_no_clusters_without_polymer():
    r = Simulation(P, "MM32", seed=2).run(t_end=1500)
    assert (r["n_clustered"] == 0).all()


def test_p1_clusters():
    r = Simulation(P, "MM32", K_PB=5, K_PS=0, n_polymers=7000, seed=3).run(t_end=1500)
    assert r["n_clustered"][-1] > 0


def test_same_seed_same_start():
    """The paper keeps initial conditions identical across polymer conditions (S24)."""
    a = Simulation(P, "MM32", seed=4)
    b = Simulation(P, "MM32", K_PB=5, K_PS=10, n_polymers=5000, seed=4)
    assert (a.occ == b.occ).all() and (a.S == b.S).all()


def test_bb170_makes_signal_and_grows():
    r = Simulation(P, "BB170", seed=5).run(t_end=6000)
    assert total_signal(r)[-1] > 0
    assert r["n_bacteria"][-1] > r["n_bacteria"][0]


def test_growth_capped():
    r = Simulation(P, "BB170", seed=6, doubling_mean=3000).run(t_end=20000)
    assert r["n_bacteria"].max() <= P["B_max"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
