# Unresolved differences and missing information

Reproduction of Curtis et al. (2026), *ISME J* 20, wrag195. DRAFT: every entry was found with AI help
(see ai_log.md) and must be checked by us against the paper, appendices and code before we keep it.
Numbers marked "by eye" were read off figure images.

## A. Missing information (not stated in the paper, appendices or code)

- **A1. Δt for each result.** Appendix 3 gives Δt = 0.1 d in its worked examples. Table 1 is reproduced
  with 0.1 d. Comparing the start and end of each appendix curve (by eye): A1, A2 and A4 match 0.1 d, A3 matches
  1/24 d (model start/end -0.23/2.04 against published -0.24/2.04; 0.1 d would give +0.15/2.42). The repo's
  MATLAB sets `c = 1/24` by default. Inferred, not stated.
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
  what we get. Probable typo; to confirm in the original PDF (our copy came through text extraction).
- **B4. Small gaps.** Table 1 q/p = 1.01, time to 10^3: ours 1.944e6, paper 1.96e6 (0.8%). Extinction from 10^3 at
  q/p = 1.01: ours 59.53, paper 59 (possibly truncation).
- **B5. Bioaugmentation example in the text** (i = 10^8, N = 10^10, q/p = 1.00000001): ours 6.4e-44, paper 1e-43
  (probably rounding).
- **B6. Table 1 cells marked "not calculated"** (time to 10^6 at q/p = 1.01 and 1.001): the model gives about
  10^4323 and 10^437 days, beyond ordinary floating point, which is consistent with the paper's note.
- **B7. Main-text example of events per day.** "10% of the population undergoes an event per day and there are 1000
  bacteria: mean time between events 0.001 days." By arithmetic this is 100 events per day, so 0.01 days (the
  10^14 example in the same sentence is consistent). Hand arithmetic only; not checked in code.

## C. Differences between the paper, appendix and the authors' code

- **C1. Figure A3 noise.** Caption: uniform noise of +-2e-4 added to q = 0.5002. MATLAB `extinction_noise`:
  p is perturbed by (0.5 - rand) * 0.0005 (+-2.5e-4 on p), and tau_1 is computed from the base p with the new q/p.
  With that setting 10.6% of runs have q/p <= 1, where extinction time is undefined (MATLAB would return complex
  numbers). The published figure shows no such lines and resembles our caption version (noise on q, everything
  recomputed consistently). Unresolved which setting made the published figure.
- **C2. Figure A4 gap between analytic and recurrence curves.** For carrying capacity 10^4 at i = 1000: published
  curves at about 2.67 (analytic) and 2.82 (recurrence) in log10 days. The MATLAB analytic line 283 uses
  2c(H_i - 1) and gives 2.66; the paper's own Eq 4.17 uses 2Δt(i - 1) and gives 2.82. The appendix blames
  the harmonic-number approximation. Our numbers suggest the code line instead; to verify when we reproduce A4.
- **C3. Harmonic-number approximation in MATLAB** uses 1/(12 (k-1)^3); Eqs 19 and 3.7 have (k-1)^2. Effect not
  tested.
- **C4. MATLAB `unbiased_extinction`** starts the q/p = 1 recurrence with 1/N, where N is the number of plotted
  points (1000), whereas Eq 4.10 has 1/n with n the carrying capacity. Estimated effect is under one day at i = 1000.
- **C5. Units in Eq 28 and Appendix 4.10.** The term i/n has no Δt while every other term is in days. Negligible
  for K = 10^16 and small otherwise; the MATLAB code does the same.

## D. Other inconsistencies noticed

- **D1.** Methods say weekly sampling for 5 years (258 sampling events); Results say stationarity was tested on
  data "monitored weekly for 2 years". Not related to the simulations; recorded for completeness.
- **D2.** Our PDF copy garbled some symbols (Δt appears as "t", some fractions in Eqs 16-28). Equations were read
  from the appendix text and checked numerically; confirm in the original.
