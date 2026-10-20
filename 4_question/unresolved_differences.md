# Unresolved differences and missing information

Reproduction of Curtis et al. (2026), *ISME J* 20, wrag195. DRAFT: every entry was found with AI help
(see ai_prompts.md) and must be checked by us against the paper, appendices and code before we keep it.
Numbers marked "by eye" were read off figure images.

## A. Missing information (not stated in the paper, appendices or code)

- **A1. Δt for each result.** Appendix 3 gives Δt = 0.1 d in its worked examples. Table 1 is reproduced
  with 0.1 d. Comparing the start and end of each appendix curve (by eye): A1, A2 and A4 match 0.1 d, A3 matches
  1/24 d (model start/end -0.23/2.04 against published -0.24/2.04; 0.1 d would give +0.15/2.42). The repo's
  MATLAB sets `c = 1/24` by default. Inferred, not stated.
- **A1b. Δt differs between results and is never stated per figure.** Table 1, A1, A2, A4 fit Δt = 0.1 d; A3 and
  Figure 5 fit Δt = 1 hour (= 1/24 d, the repo MATLAB default). Figure 5's axes are in HOURS while Table 1 and the
  text are in days; with Δt = 0.1 d (2.4 h) Fig 5 would be 2.4 times too high (e.g. T_1000 at q/p = 1.00001:
  24,265 h, published ~10,000 h). Inferred, not stated. Figure 5's orange series is labelled 1.00001 while
  Table 1's row is 1.0001.
- **A2b. Figure 2 grid.** The q/p grid is not stated. The published dots fit a grid of q/p = 0.99, 0.99001, ...,
  0.99998 (step 1e-5, 999 points); the top six isolated dots sit on it to within 0.002 log10. q/p = 1 is excluded
  (Eq 4 is 0/0 there; the limit is 0.9 N). Inferred, not stated.
- **A2. Axis ranges and panel details of Figure 1.** Not given; axis limits were estimated by eye from a
  300 dpi raster of page 3 (q/p about 0.92 to 1.04 in panels a and b).
- **A3. Figure 1c.** The x-axis is unlabelled as log10 N (inferred from dot positions); the dots follow three
  series, q/p = 1.0001, 1.00001, 1.000001, ending at log10 N = 6, 7, 8 (inferred). The caption names only
  q/p = 1.0001 and the colour bar runs from 1.000025 to 1.0001. The y-axis is labelled "P_i" but shows log10 P_i.
- **A4. Figure A3 settings.** Number of noise trajectories (we assumed 20), the random seed, and whether the noise
  is one draw per trajectory or varies within a run are not stated. The MATLAB draws once per trajectory.
- **A5. Software and seeds.** The authors' repo has one commit (December 2025), a one-line README, no software
  versions and no seeds. It contains no code for Figures 1 or 2.

## B. Paper numbers we could not reproduce

- **B1. Table 1, extinction from 10^6 cells, q/p > 1.** Ours (days): 196.5 (q/p = 1.01), 1,498 (1.001),
  10,380 (1.0001). Paper: 7,030, 8,730, 59,400. A back-of-envelope check gives about 197 d at q/p = 1.01, and
  our small-population simulations agree with our formula. Running the recurrence forwards in ordinary floating
  point overflows at 10^6 steps, so that does not explain the paper's finite values. Unresolved.
- **B2. Table 1, q/p = 1.0001 row.** Time to 10^3: ours 1,359 d, paper 1.30e3 (which equals the q/p = 1 value of
  1,297 d). Time to 10^6: ours 4.9e47 d, paper 5.07e9. Extinction from 10^3: ours 578 d, paper 1.01e3. Unresolved.
- **B3. Table 1, q/p = 1, time to 10^6.** Table prints 2.68e4; the main text and Appendix 3 say 2.68e6, which is
  what we get. Checked on the rendered page image (page 7): the table itself prints 2.68 x 10^4, so this is not a text-extraction artefact. Probable typo in the table.
- **B4. Small gaps.** Table 1 q/p = 1.01, time to 10^3: ours 1.944e6, paper 1.96e6 (0.8%). Extinction from 10^3 at
  q/p = 1.01: ours 59.53, paper 59 (possibly truncation).
- **B5. Bioaugmentation example in the text** (i = 10^8, N = 10^10, q/p = 1.00000001): ours 6.4e-44, paper 1e-43
  (probably rounding).
- **B6. Table 1 cells marked "not calculated"** (time to 10^6 at q/p = 1.01 and 1.001): the model gives about
  10^4323 and 10^437 days, beyond ordinary floating point, which is consistent with the paper's note.
- **B7. Main-text example of events per day.** "10% of the population undergoes an event per day and there are 1000
  bacteria: mean time between events 0.001 days." By arithmetic this is 100 events per day, so 0.01 days (the
  10^14 example in the same sentence is consistent). Hand arithmetic only; not checked in code.

- **B8. Cholera carrier example (main text, below Eq 15).** Not reproduced. The text gives N = 7.3e7 from
  8.53e3 vibrios/g x 1200 g, but that product is 1.02e7. The stated q/p range 0.999999936915 to 0.999999998351
  corresponds to ID50 = 1.1e7 (matches the text) and 4.2e8 (text says 4.4e7), and, through Eq 15 with N = 7.3e7,
  to symptomatic/infected ratios of 0.99 and 0.113, not the 1% to 30% quoted. Hand arithmetic with mpmath only;
  to check against the authors' intended definition of the ratio.

## C. Differences between the paper, appendix and the authors' code

- **C1. Figure A3 noise.** Caption: uniform noise of +-2e-4 added to q = 0.5002. MATLAB `extinction_noise`:
  p is perturbed by (0.5 - rand) * 0.0005 (+-2.5e-4 on p), and tau_1 is computed from the base p with the new q/p.
  With that setting 10.6% of runs have q/p <= 1, where extinction time is undefined (MATLAB would return complex
  numbers). The published figure shows no such lines and resembles our caption version (noise on q, everything
  recomputed consistently). Unresolved which setting made the published figure.
- **C2. Figure A4 gap between analytic and recurrence curves (explained).** For carrying capacity 10^4 at i = 1000
  the published curves are at about 2.67 (analytic) and 2.82 (recurrence), log10 days. Our port of the MATLAB
  with Δt = 0.1 d gives 2.665 (analytic) and 2.820 (recurrence), so the port reproduces both. The cause is
  MATLAB line 283, which has 2c(H_i - 1) where the paper's Eq 4.17 has 2Δt(i - 1); with Eq 4.17 the analytic
  value is 2.82 too. The appendix blames the harmonic-number approximation, which is not the cause (the
  harmonic terms are accurate to better than 1e-4 here). The gap is a code/equation mismatch, not an approximation
  error. Port, not a MATLAB run (see E).
- **C3. Harmonic-number approximation in MATLAB** uses 1/(12 (k-1)^3); Eqs 19 and 3.7 have (k-1)^2. Tested
  (q = 0.5002, analytic extinction time vs our exact recurrence): n = 10: MATLAB cube +2.2%, paper square -0.017%;
  n = 100: +1.1e-5 vs -2.3e-5; n = 1000: -5e-6 vs -5e-6. The standard expansion has the square, so the cube looks
  like a typo in the code; it matters only below about n = 30 and is invisible on the log plots.
- **C4. MATLAB `unbiased_extinction`** starts the q/p = 1 recurrence with 1/N, where N is the number of plotted
  points (1000), whereas Eq 4.10 has 1/n with n the carrying capacity. Measured with the port (Δt = 1/24 d): the
  recurrence exceeds Eq 4.17 by i/N - i/K, i.e. +0.01 d at i = 10, +0.1 d at i = 100, +1.0 d at i = 1000
  (+0.04% for K = 1e16, +0.3% for K = 1e4 at i = 1000). Invisible on a log plot.
- **C5. Units in Eq 28 and Appendix 4.10.** The term i/n has no Δt while every other term is in days. Negligible
  for K = 10^16 and small otherwise; the MATLAB code does the same.

## E0. Reproduction status of later figures

- **Figure 2** (Eq 4, N = 1e6, P_i = 0.9): reproduced. Left end 2.360 (published ~2.36); top dots agree to 0.002.
  Eq 1 evaluated at the Eq 4 inoculum returns 0.9 exactly (checked at 20 points).
- **Figures A1 and A2** (q/p = 1.002, Δt = 0.1 d): reproduced. Measured published curves agree with ours to 0.003 log10
  or better at n = 50-990 (A1) and 10-990 (A2); at n = 10 on the steep part of A1 the difference is 0.026 (one pixel
  of x error is worth that much there). The start values match (A1 at n = 2: -0.70; A2 end 2.21). The MATLAB
  analytic formula differs from the recurrence by 2.3% (A1) and 1.0% (A2) at n = 10, 3e-6 or less by n = 100
  (cube term, C3); invisible on the plots. The appendix's "no difference up to n = 1000" is true for n >= 100.
- **Figure A4**: reproduced with Δt = 0.1 d using the MATLAB port (not a MATLAB run). At i = 100-990 the measured
  published curves agree with ours to about 0.015 log10 (blue: 2.816/2.661 vs 2.817/2.662 at i = 990). The red
  recurrence curve hides under the red analytic one in the published figure, so only one red curve could be
  measured. Appendix text (below Eq 4.18) says the analytic/recurrence gap comes from the harmonic approximation
  error propagating through T_1; our numbers show it comes from MATLAB line 283 (see C2). Eq 4.18 in the
  appendix correctly has the square term (C3).

- **Figure 5** (Eq 18 and Eq 27; q/p = 1.01, 1.001, 1.00001; Δt = 1 h): reproduced. Panel b agrees to 11 h or
  better (1 pixel = 19 h) at n = 50-950; panel a to 37 h or better at n = 50-200 and the curves leave the plot at
  n = 252, 619, 797 (published about 250, 620, 800). See A1b for the Δt/units issue.
- **Figure 4** (Eq 10 for a, Eq 9 for b; ID50 grid 1..1000; q/p = 0.99999931): reproduced. The ten isolated dots in
  panel a agree to 0.002 and the sigmoid in panel b to 0.003 in P. The dose grid of panel b is inferred from its
  isolated dots: i = 1, then multiples of 100 (dots at log10 dose 0, 2.0, 2.3, 2.5). Text examples: ID50 -> q/p
  for Campylobacter (6.68e4 -> 0.9999896), Salmonella (1e6 -> 0.99999931) and Vibrio (1e8 -> 0.9999999931) all
  reproduce.

## E. Checks against the authors' code (Gap 3) and Figure A3 spread (Gap 2)

- **E1. The MATLAB was not run.** No MATLAB or Octave in our workspace. `matlab_port.py` is a line-by-line Python
  port (same constants, same quirks; the `integral` call is replaced by its exact series, spot-checked against
  scipy quad to 12 digits). To confirm on real MATLAB, run the .m file and compare with the tables printed by
  `matlab_port.py`.
- **E2. Agreement.** Port recurrence vs our independent implementation (q = 0.5002, c = 1/24): relative differences
  below 1e-13 for extinction and below 1e-15 for time to n, at n = 10, 100, 1000. Analytic MATLAB formulas agree to
  1e-5 at n >= 100 and are off by 2.2% (extinction) and 5.9% (time to n) at n = 10 because of the cube term (C3).
  At q/p = 1 the port reproduces Eq 4.17 up to the 1/N term (C4) and line 283 (C2).
- **E3. Figure A3 spread (Gap 2).** At n = 250/500/990 the published red band reaches +0.12/+0.16/+0.24 above and
  -0.09/-0.14/-0.26 below the black curve (log10 days, +-0.02, measured from a 400 dpi raster; the black curve
  matches ours to 0.003). Our caption and MATLAB versions give wider upward and narrower downward spreads
  (typically up 0.31-0.42, down 0.11-0.14 with 20 lines). A per-step noise reading (new q at every i) gives only
  about 0.005-0.02, far too small. So none of our readings reproduces the published asymmetry exactly; the number
  of lines and the exact noise model of the published figure remain unresolved, and the qualitative message (a
  modest effect on a log scale) holds in all versions.
- **E4. Small-population probabilities (Gap 1).** Direct simulation of the game vs Eqs 1-2, 8 cases incl. q = p:
  6 of 8 inside 95% intervals; the two misses were chance (2,000,000-run follow-up, z = -0.21 and +0.52).

## F. Seeds and software

| Run | Script | Seed |
| --- | --- | --- |
| Duration Monte Carlo; Fig A3 example lines | durations.py, noise.py | 20261020 |
| Fig A3 statistics | noise.py | 20261021 |
| Probability Monte Carlo | prob_check.py | 20261022 (follow-up 20261122) |
| Fig A3 spread | a3_spread.py | 20261023 |
| Figures 2, 4, 5, A1, A2, A4 | fig2.py, fig4.py, fig5.py, a1a2.py, a4.py | none (deterministic) |
| Figure 1, Table 1 analytic, MATLAB port | fig1.py, durations.py, matlab_port.py | none (deterministic) |

Python 3.13.16, numpy 2.5.3, scipy 1.18.1, matplotlib 3.11.2, mpmath 1.4.1, Pillow 12.3.0.

## D. Other inconsistencies noticed

- **D1.** Methods say weekly sampling for 5 years (258 sampling events); Results say stationarity was tested on
  data "monitored weekly for 2 years". Not related to the simulations; recorded for completeness.
- **D2.** Our PDF copy garbled some symbols (Δt appears as "t", some fractions in Eqs 16-28). Equations were read
  from the appendix text and checked numerically; confirm in the original.
