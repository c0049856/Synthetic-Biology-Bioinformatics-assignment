"""Duration calculations from Curtis et al. (2026), ISME J 20, wrag195 (main text Eqs 16-28,
appendices 3 and 4): how long it takes a population to grow from 1 cell to n cells, and how
long it takes to go extinct.

Model recap (plain words)
  * Each event is a birth (probability p) or a death (probability q); p + q = 1, alpha = q/p,
    so p = 1/(1+alpha).
  * DT (the paper's "Delta t") is the expected time for ONE cell to subdivide. With i cells the
    expected time to the next event is DT/i (Appendix 3, Eq 3.1).
  * Time to reach n from 1 cell: m_i = DT/(i p) + alpha*m_{i-1}, m_0 = 0, M_{1,n} = sum_{i<n} m_i
    (Eqs 16, 17; m_0 = 0 means a death at 1 cell is treated as an instant restart at 1).
  * Time to extinction from i cells, alpha > 1: tau_{i+1} = -DT/(i p) + alpha*tau_i, with tau_1
    chosen so that T_i stays finite (Eqs 24-26; Appendix 4.2-4.7).  T_i = sum_{j<=i} tau_j.
  * alpha = 1: extinction is only finite with a ceiling (carrying capacity K); Eq 28.

Provenance: generated with Claude (Anthropic); every equation and parameter must be checked
against the paper by the authors of this repo.  AI-generated, see ai_log.md.

Numerical notes: for alpha > 1 the plain recurrences produce numbers like 10^4000 (overflow) or
lose all precision going forward, so (a) time-to-n is computed in a scaled form (u_i = m_i/alpha^i)
and combined in log space, and (b) extinction times use the recurrence run BACKWARDS, which is
numerically stable for alpha > 1.  Both are algebraic rearrangements of the paper's recurrences.

Random numbers: only the Monte Carlo cross-check uses them, with numpy.random.default_rng(SEED).
"""
import csv
import sys

import mpmath
import numpy as np
from mpmath import mp, mpf

DT = 0.1          # days; value used in the paper's worked examples (Appendix 3)
SEED = 20261020   # recorded seed for the Monte Carlo cross-check
LN10 = np.log(10.0)


def p_of(alpha):
    return 1.0 / (1.0 + alpha)


# ---------------------------------------------------------------- time from 1 cell to n cells
def log10_M1n(alpha, n, dt=DT):
    """log10 of the expected time (days) to go from 1 cell to n cells (Eqs 16-17)."""
    p, ln_a = p_of(alpha), np.log(alpha)
    k = np.arange(1, n, dtype=float)                 # i = 1 .. n-1
    u = np.cumsum(dt / (p * k) * np.exp(-k * ln_a))  # u_i = m_i / alpha^i
    logm = k * ln_a + np.log(u)                      # log m_i
    top = logm.max()
    return (top + np.log(np.exp(logm - top).sum())) / LN10


def M1n_plain(alpha, n, dt=DT):
    """The recurrence exactly as written (Eq 16/17), plain floats. Only for small n."""
    p, m, total = p_of(alpha), 0.0, 0.0
    for i in range(1, n):
        m = dt / (i * p) + alpha * m
        total += m
    return total


def M1n_alpha1_eq23(n, dt=DT):
    """Eq 23 (alpha = 1) with the paper's harmonic-number approximation."""
    g = 0.5772156649
    return 2 * dt * (n * np.log(n) + n * (-1 + g + 1 / (2 * n) - 1 / (12 * n**2)))


def M1n_alpha1_exact(n, dt=DT):
    """alpha = 1: m_i = 2 DT H_i, so M_{1,n} = 2 DT (n H_{n-1} - (n-1)) exactly."""
    return float(2 * dt * (n * mpmath.harmonic(n - 1) - (n - 1)))


# ---------------------------------------------------------------- time to extinction
def extinction_gt1(alpha, i_values, dt=DT):
    """T_i for alpha > 1: Eq 24 run backwards (stable), then T_i = sum_{j<=i} tau_j (Eq 26)."""
    p, imax = p_of(alpha), max(i_values)
    start = imax + int(45 / np.log(alpha)) + 1000    # tau is ~0 far above imax; errors die as alpha^-k
    taus, tau = np.zeros(imax + 1), 0.0
    for j in range(start - 1, 0, -1):
        tau = (tau + dt / (j * p)) / alpha           # tau_j from tau_{j+1}
        if j <= imax:
            taus[j] = tau
    cum = np.cumsum(taus)
    return {i: float(cum[i]) for i in i_values}


def extinction_alpha1_eq28(i, K, dt=DT):
    """Eq 28 (alpha = 1, carrying capacity K) with exact harmonic numbers."""
    mp.dps = 30
    H = mpmath.harmonic
    return float(2 * dt * i * (H(K - 1) - H(i - 1)) + mpf(i) / K + 2 * dt * (i - 1))


def extinction_alpha1_recurrence(i_values, K, dt=DT):
    """Appendix 4.10-4.12 recurrence for alpha = 1: tau_1 = 1/K + 2 DT H_{K-1}, tau_{i+1} = tau_i - 2DT/i."""
    mp.dps = 30
    tau, cum, out = 1.0 / K + 2 * dt * float(mpmath.harmonic(K - 1)), 0.0, {}
    wanted = set(i_values)
    for i in range(1, max(i_values) + 1):
        cum += tau
        if i in wanted:
            out[i] = cum
        tau -= 2 * dt / i
    return out


# ---------------------------------------------------------------- Monte Carlo cross-check
def mc_time_to_n(alpha, n, runs, seed, dt=DT):
    """Simulate the jump chain (up w.p. p, down w.p. q, reflecting at 1 cell), each event at i cells
    costing DT/i days.  Returns mean time and its standard error."""
    rng, p = np.random.default_rng(seed), p_of(alpha)
    s, t = np.ones(runs, dtype=np.int64), np.zeros(runs)
    active = np.ones(runs, dtype=bool)
    while active.any():
        idx = np.flatnonzero(active)
        t[idx] += dt / s[idx]
        up = rng.random(idx.size) < p
        s[idx] = np.where(up, s[idx] + 1, np.maximum(s[idx] - 1, 1))
        active[idx[s[idx] >= n]] = False
    return t.mean(), t.std(ddof=1) / np.sqrt(runs)


def mc_extinction(alpha, i0, runs, seed, dt=DT):
    """Same chain, absorbed at 0 cells; returns mean time to extinction and its standard error."""
    rng, p = np.random.default_rng(seed), p_of(alpha)
    s, t = np.full(runs, i0, dtype=np.int64), np.zeros(runs)
    active = np.ones(runs, dtype=bool)
    while active.any():
        idx = np.flatnonzero(active)
        t[idx] += dt / s[idx]
        s[idx] += np.where(rng.random(idx.size) < p, 1, -1)
        active[idx[s[idx] == 0]] = False
    return t.mean(), t.std(ddof=1) / np.sqrt(runs)


# ---------------------------------------------------------------- Table 1 as printed
# None = the paper says the value "could not be calculated by recursion or analytically".
PAPER = {
    1.01:   dict(t1e3=1.96e6, t1e6=None,    x1e3=59,    x1e6=7.03e3),
    1.001:  dict(t1e3=2.13e3, t1e6=None,    x1e3=234,   x1e6=8.73e3),
    1.0001: dict(t1e3=1.30e3, t1e6=5.07e9,  x1e3=1.01e3, x1e6=5.94e4),
    1.0:    dict(t1e3=1.30e3, t1e6=2.68e4,  x1e3=6.19e3, x1e6=4.80e6),   # 2.68e4 as printed in Table 1
}
COLS = [("t1e3", "time to 10^3 (d)"), ("t1e6", "time to 10^6 (d)"),
        ("x1e3", "extinction from 10^3 (d)"), ("x1e6", "extinction from 10^6 (d)")]
K_CAP = 10**16   # carrying capacity quoted for the q/p = 1 extinction entries


def status(ours, paper):
    if paper is None:
        return "paper: not calculated"
    rel = abs(ours / paper - 1)
    return "agrees (<0.5%)" if rel < 0.005 else ("close (<5%)" if rel < 0.05 else "DIFFERS")


def fmt_days(x_log10):
    return f"{10 ** x_log10:.3g}" if x_log10 < 300 else f"10^{x_log10:.1f}"


def build_table():
    rows = []
    for alpha in (1.01, 1.001, 1.0001, 1.0):
        ours = {}
        ours["t1e3"] = 10 ** log10_M1n(alpha, 10**3)
        lg = log10_M1n(alpha, 10**6)
        ours["t1e6"] = 10**lg if lg < 300 else None
        ours["t1e6_log10"] = lg
        if alpha > 1:
            ext = extinction_gt1(alpha, [10**3, 10**6])
            ours["x1e3"], ours["x1e6"] = ext[10**3], ext[10**6]
        else:
            ours["x1e3"] = extinction_alpha1_eq28(10**3, K_CAP)
            ours["x1e6"] = extinction_alpha1_eq28(10**6, K_CAP)
        for key, name in COLS:
            paper = PAPER[alpha][key]
            val = ours[key]
            if val is None:  # astronomically large: report log10
                shown, st = f"10^{ours['t1e6_log10']:.1f}", status(float("inf"), paper) if paper else "paper: not calculated"
                if paper is not None:
                    st = "DIFFERS"
                ratio = ""
            else:
                shown, st = f"{val:.4g}", status(val, paper)
                ratio = f"{val / paper:.4f}" if paper else ""
            rows.append(dict(alpha=alpha, quantity=name, ours=shown,
                             paper="not calculated" if paper is None else f"{paper:.3g}",
                             ours_over_paper=ratio, status=st))
        if alpha == 1.0 and ours["t1e6"]:
            rows.append(dict(alpha=alpha, quantity="time to 10^6 (d), vs the text's 2.68e6",
                             ours=f"{ours['t1e6']:.4g}", paper="2.68e+06",
                             ours_over_paper=f"{ours['t1e6'] / 2.68e6:.4f}",
                             status=status(ours["t1e6"], 2.68e6)))
    return rows


def main():
    print("=== Part 1: text numbers (alpha = 1, DT = 0.1 d) ===")
    m3, m6 = M1n_alpha1_eq23(10**3), M1n_alpha1_eq23(10**6)
    print(f"  1 -> 10^3 cells: Eq 23 {m3:.6g} d (paper 1.297e3);  exact sum {M1n_alpha1_exact(10**3):.6g};"
          f"  scaled recurrence {10 ** log10_M1n(1.0, 10**3):.6g}")
    print(f"  1 -> 10^6 cells: Eq 23 {m6:.6g} d = {m6 / 365.25:.0f} years (paper 2.68e6 d, ~7000 y);"
          f"  exact sum {M1n_alpha1_exact(10**6):.6g}")
    for i, label in ((10**3, "17 years"), (10**6, "over 13 thousand years")):
        t_eq = extinction_alpha1_eq28(i, K_CAP)
        t_rec = extinction_alpha1_recurrence([i], K_CAP)[i]
        print(f"  extinction from {i:.0e}, K = 1e16: Eq 28 {t_eq:.6g} d = {t_eq / 365.25:,.1f} years "
              f"(paper: {label});  recurrence {t_rec:.6g} d")

    print("\n=== Part 2: Table 1 ===")
    rows = build_table()
    with open("table1_comparison.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"  q/p = {r['alpha']:<7} {r['quantity']:<42} ours {r['ours']:>10}   paper {r['paper']:>14}   {r['status']}")

    print("\n=== Part 3: small populations and q/p = 1 (exact sums vs the paper's approximation) ===")
    for n in (2, 3, 5, 10, 1000):
        ex, ap = M1n_alpha1_exact(n), M1n_alpha1_eq23(n)
        print(f"  alpha = 1, 1 -> {n:>4} cells: exact {ex:.6f} d, Eq 23 approx {ap:.6f} d "
              f"(relative error {abs(ap / ex - 1):.1e}); plain recurrence {M1n_plain(1.0, n):.6f}")

    print(f"\n=== Part 4: Monte Carlo cross-check of the model itself (seed {SEED}, 20000 runs) ===")
    for alpha, n in ((1.0, 10), (1.1, 10)):
        mean, se = mc_time_to_n(alpha, n, 20000, SEED)
        print(f"  time 1 -> {n} cells, alpha = {alpha}: simulation {mean:.4f} +/- {1.96 * se:.4f} d (95%), "
              f"recurrence {M1n_plain(alpha, n):.4f} d")
    for alpha, i0 in ((1.2, 5), (1.2, 20)):
        mean, se = mc_extinction(alpha, i0, 20000, SEED)
        ref = extinction_gt1(alpha, [i0])[i0]
        print(f"  extinction from {i0} cells, alpha = {alpha}: simulation {mean:.4f} +/- {1.96 * se:.4f} d (95%), "
              f"formula (backward recurrence) {ref:.4f} d")

    print(f"\nSoftware: Python {sys.version.split()[0]}, numpy {np.__version__}, mpmath {mpmath.__version__}")


if __name__ == "__main__":
    main()
