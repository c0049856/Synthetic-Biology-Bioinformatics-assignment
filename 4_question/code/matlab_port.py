"""Gap 3: line-by-line Python port of the authors' MATLAB (beadyallen/ppd_immigration_microbe,
Figures/gamblers_ruin_bacteria.m), compared with our independent implementations.

IMPORTANT: neither MATLAB nor Octave was available in this workspace, so the authors' code was NOT run.
This is a PORT: each MATLAB function is re-typed in Python with the same formulas, the same constants
(c = 1/24, 0.57721 for Euler's constant, the 1/(12 (k-1)^3) term, N = 1000 plotted points) and the same
quirks.  The comparison therefore tests (a) that our independent code and the authors' formulas agree and
(b) what the authors' approximations do numerically.  It does not prove the MATLAB itself runs as written.
MATLAB's integral(@(t)(1-t.^(k-1))./(1-t),0,1/r) is evaluated in closed form as sum_{j=1}^{k-1} r^-j / j
(exact expansion of the integrand); scipy.integrate.quad is used to spot-check that equivalence.

Provenance: generated with Claude (Anthropic); AI-generated, see ai_log.md.  No random numbers (deterministic).
"""
import sys

import numpy as np
import scipy
from scipy.integrate import quad

from durations import extinction_alpha1_eq28, extinction_gt1, log10_M1n

C = 1.0 / 24.0
N = 1000


# ---------------------------------------------------------------- MATLAB functions, ported
def m_extinction(p, c, r, N):                       # lines 64-84
    delta = np.zeros(N)
    delta[0] = -(c / p) * np.log(1 - 1 / r)
    for i in range(1, N):                           # MATLAB i = 1:N-1 -> Delta(i+1) = r*Delta(i) - c/(p*i)
        delta[i] = r * delta[i - 1] - c / (p * i)
    return np.cumsum(delta)


def _integral(r, k):                                # integral(@(t)(1-t.^(k-1))./(1-t),0,1/r)
    j = np.arange(1, k)
    return float(np.sum(r ** (-j) / j))


def m_term2(k):                                     # line 119 / 217: harmonic approximation (CUBE term)
    return np.log(k - 1) + 0.57721 + 1 / (2 * (k - 1)) - 1 / (12 * (k - 1) ** 3)


def m_extinction_an(p, c, r, N):                    # lines 115-123
    T = np.zeros(N)
    for k in range(2, N + 1):
        term1 = _integral(r, k)
        term3 = (r ** k - 1) * np.log(r / (r - 1))
        T[k - 1] = -c / (p * (r - 1)) * ((r ** k) * term1 - m_term2(k) - term3)
    return T


def m_time_to_i(p, c, r, N):                        # lines 191-206
    delta = np.zeros(N)
    for i in range(2, N + 1):
        delta[i - 1] = r * delta[i - 2] + c / (p * (i - 1))
    return np.cumsum(delta)


def m_time_to_i_an(p, c, r, N):                     # lines 208-222
    M = np.zeros(N)
    for k in range(2, N + 1):
        M[k - 1] = c / (p * (r - 1)) * ((r ** k) * _integral(r, k) - m_term2(k))
    return M


def m_unbiased_extinction(p, r, c, N, n):           # lines 256-274  (note 1/N, N = number of points)
    delta = np.zeros(N)
    delta[0] = 1 / N + 2 * c * m_term2(n)
    for i in range(1, N):
        delta[i] = r * delta[i - 1] - c / (p * i)
    return np.cumsum(delta)


def m_unbiased_extinction_an(p, r, c, N, n):        # lines 276-284  (2c(H_i - 1) term)
    NN = np.arange(2, N + 1, dtype=float)
    H_n = m_term2(n)
    H_i = m_term2(NN)
    T = np.zeros(N)
    T[1:] = 2 * c * NN * (H_n - H_i) + NN / n + 2 * c * (H_i - 1)
    return T


# ---------------------------------------------------------------- comparison
def rel(a, b):
    return (a - b) / b


def main():
    # --- (1) q = 0.5002 (alpha > 1)
    q = 0.5002
    p = 1 - q
    r = q / p
    pts = (10, 100, 1000)
    print(f"Python {sys.version.split()[0]}, numpy {np.__version__}, scipy {scipy.__version__}")
    print("MATLAB/Octave not available: this is a port, not a run of the authors' code.\n")
    print(f"=== q = {q}, q/p = {r:.7f}, c = 1/24 d ===")

    # quadrature spot-check of the integral/series equivalence
    for k in (10, 1000):
        quad_val = quad(lambda t: (1 - t ** (k - 1)) / (1 - t), 0, 1 / r, epsabs=1e-13, epsrel=1e-13)[0]
        print(f"  integral check k={k}: series {_integral(r, k):.12f}  quad {quad_val:.12f}")

    ours = extinction_gt1(r, list(range(1, N + 1)), C)       # our independent backward recurrence
    rec = m_extinction(p, C, r, N)
    an = m_extinction_an(p, C, r, N)
    print("\n  Time to extinction from n cells (days)")
    print(f"  {'n':>5} | {'ours (durations.py)':>20} | {'MATLAB recurrence':>18} | {'MATLAB analytic':>16} | "
          f"rec vs ours | an vs ours")
    for n in pts:
        print(f"  {n:>5} | {ours[n]:>20.10g} | {rec[n-1]:>18.10g} | {an[n-1]:>16.10g} | "
              f"{rel(rec[n-1], ours[n]):>+10.2e} | {rel(an[n-1], ours[n]):>+10.2e}")

    mrec = m_time_to_i(p, C, r, N)
    man = m_time_to_i_an(p, C, r, N)
    print("\n  Time to go from 1 to n cells (days)")
    print(f"  {'n':>5} | {'ours (durations.py)':>20} | {'MATLAB recurrence':>18} | {'MATLAB analytic':>16} | "
          f"rec vs ours | an vs ours")
    for n in pts:
        o = 10 ** log10_M1n(r, n, C)
        print(f"  {n:>5} | {o:>20.10g} | {mrec[n-1]:>18.10g} | {man[n-1]:>16.10g} | "
              f"{rel(mrec[n-1], o):>+10.2e} | {rel(man[n-1], o):>+10.2e}")

    # --- (2) q = p, carrying capacity K
    p = 0.5
    r = 1.0
    print("\n=== q/p = 1, c = 1/24 d: extinction from i cells with carrying capacity K ===")
    for K in (10 ** 16, 10 ** 4):
        rec = m_unbiased_extinction(p, r, C, N, K)
        an = m_unbiased_extinction_an(p, r, C, N, K)
        print(f"  K = 1e{int(np.log10(K))}")
        print(f"  {'i':>5} | {'paper Eq 4.17 exact':>20} | {'MATLAB recurrence':>18} | {'MATLAB analytic':>16} | "
              f"rec vs exact | an vs exact")
        for i in pts:
            ex = float(extinction_alpha1_eq28(i, K, C))
            print(f"  {i:>5} | {ex:>20.10g} | {rec[i-1]:>18.10g} | {an[i-1]:>16.10g} | "
                  f"{rel(rec[i-1], ex):>+10.2e} | {rel(an[i-1], ex):>+10.2e}")


if __name__ == "__main__":
    main()
