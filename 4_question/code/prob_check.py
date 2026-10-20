"""Monte Carlo check of the gambler's-ruin probabilities (paper Eq 1 and Eq 2) for small populations.

The game: start with i cells; each event is a birth (probability p) or a death (probability q), p + q = 1,
q/p = r. Stop when the population hits 0 (extinct) or N (success). P_i = probability of hitting N first.
  Eq 1 (r != 1):  P_i = (1 - r**i) / (1 - r**N)        Eq 2 (r == 1):  P_i = i / N
This simulates the game directly, so it tests the formulas without using them.

Random numbers: numpy.random.default_rng(SEED), ONE generator used for all cases in the order listed below.
Provenance: generated with Claude (Anthropic); AI-generated, see ai_log.md.
"""
import sys

import numpy as np

from fig1a import log10_prob

SEED = 20261022
RUNS = 200_000
# (i, N, r = q/p): small populations, equal births and deaths (r = 1), and both sides of r = 1
CASES = [(1, 10, 0.9), (1, 10, 1.0), (1, 10, 1.1), (3, 10, 1.0), (3, 10, 1.1),
         (5, 20, 0.95), (2, 5, 1.0), (1, 2, 1.0)]


def simulate(i, n, r, runs, rng):
    """Fraction of runs that hit N before 0."""
    p = 1.0 / (1.0 + r)
    s = np.full(runs, i, dtype=np.int64)
    active = np.ones(runs, dtype=bool)
    while active.any():
        idx = np.flatnonzero(active)
        s[idx] += np.where(rng.random(idx.size) < p, 1, -1)
        active[idx[(s[idx] == 0) | (s[idx] == n)]] = False
    return float((s == n).mean())


def main():
    rng = np.random.default_rng(SEED)
    print(f"Seed {SEED}, {RUNS} runs per case; 95% interval = estimate +/- 1.96 * sqrt(P(1-P)/runs)\n")
    print(f"{'i':>2} {'N':>3} {'q/p':>5} | {'simulated P':>11} {'+/- 95%':>8} | {'formula P':>9} | z-score | inside interval?")
    inside, oks = 0, []
    for i, n, r in CASES:
        est = simulate(i, n, r, RUNS, rng)
        half = 1.96 * np.sqrt(est * (1 - est) / RUNS)
        formula = float(10 ** log10_prob(np.array([r]), i, n)[0])
        z = (est - formula) / np.sqrt(formula * (1 - formula) / RUNS)
        ok = abs(est - formula) <= half
        inside += ok
        oks.append(bool(ok))
        print(f"{i:>2} {n:>3} {r:>5} | {est:>11.5f} {half:>8.5f} | {formula:>9.5f} | {z:>+7.2f} | {'yes' if ok else 'NO'}")
    print(f"\n{inside} of {len(CASES)} formula values fall inside the 95% interval "
          f"(about {0.05 * len(CASES):.1f} misses are expected by chance).")

    # Follow-up (reported alongside, not instead of, the first run): a real bias in the formula or the
    # simulation would persist and grow in z with more runs; a chance fluctuation would not.
    misses = [(i, n, r) for (i, n, r), ok in zip(CASES, oks) if not ok]
    if misses:
        big, seed2 = RUNS * 10, SEED + 100
        rng2 = np.random.default_rng(seed2)
        print(f"\nFollow-up for the misses: {big} runs each, new seed {seed2}")
        for i, n, r in misses:
            est = simulate(i, n, r, big, rng2)
            formula = float(10 ** log10_prob(np.array([r]), i, n)[0])
            z = (est - formula) / np.sqrt(formula * (1 - formula) / big)
            half = 1.96 * np.sqrt(est * (1 - est) / big)
            print(f"  i={i} N={n} q/p={r}: simulated {est:.5f} +/- {half:.5f}, formula {formula:.5f}, z = {z:+.2f}, "
                  f"{'inside' if abs(est - formula) <= half else 'OUTSIDE'} the interval")
    print(f"Software: Python {sys.version.split()[0]}, numpy {np.__version__}")


if __name__ == "__main__":
    main()
