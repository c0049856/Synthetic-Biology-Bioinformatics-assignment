# Interpretations and ambiguities

Where the paper and supplement are unclear, contradictory or silent, the choice made in this reproduction is recorded here. Each entry is referenced from `params/default.yaml`. Status: **proposed** until reviewed by Regina, then **agreed**.

| ID | Issue | Source | Our choice | Status |
|---|---|---|---|---|
| I1 | Boundary conditions are not defined; S19 only says molecules move in 4 directions "except at the boundaries". | S19 | Reflecting walls: a move off the grid is rejected. | agreed |
| I2 | Main text says each *quadrant* of a bacterium has B_S signal sites; S21 gives 60 per bacterium. | Main p.9, S21 | 60 per bacterium in total, 15 in each of its 4 cells. | agreed |
| I3 | Only the ratios K_PB and K_PS are given, not the forward and backward rates. Only B–S has explicit rates (k+ = 0.001, k− = 0.002). | S21 | k_off = 0.002 for every reaction; k_on = K × 0.002. | agreed |
| I4 | Small-molecule diffusion into a direction blocked by a bacterium: S19 says "significantly smaller", S22 item 7 says "not available", and the S22 sketch shows a low rate. | S19, S22 | Rate multiplied by 0.1. Sensitivity check with 0. | agreed |
| I5 | S22 item 9 gives cluster diffusion as D_S/m, but calls D_S "the diffusion rate of bacteria". | S22 | D_B / m, with m the number of bacteria in the cluster. | agreed |
| I6 | K_degrad is given as "−0.01", while the equation already carries a minus sign. | S22 | K_degrad = +0.01, so expression decays. | agreed |
| I7 | [P] is "0–7000 a.u." in the text but the legends end at "70000". It is not stated whether [P] is a total or per-cell amount. f(P) (λ = 8) and P_c = 10 only take effect at more than ~8 polymers per cell, which a total of 7000 on 2500 cells (2.8 per cell) rarely reaches. | S26, S22–S23 | Total number of polymer molecules placed at random on the grid, 0–7000. Test 0–70000 as an alternative and report which matches the published trends. | agreed |
| I8 | Figure captions S31–S42 say time = 0–3000 a.u.; the text says 0–30000. | S26–S30 | 0–30000 (consistent with Fig 3 time points 5000/15000/30000). | agreed |
| I9 | The supplement uses an exact Gillespie algorithm. Exact simulation of ~10⁸ events per run is not feasible in the time available. | S20 | Fixed time step dt = 0.5 a.u. with binomial draws for diffusion and binding (tau-leaping). Check against an exact simulation on a short window if time allows. | agreed |
| I10 | How luminescence is normalised in the model is not stated (experiments divide light by OD). | S22, Methods | Mean light per bacterium; fold change = mean over runs (polymer) / mean over runs (control). | agreed |
| I11 | Fig 3 bottom heatmaps do not state the polymer concentration used. | Fig 3 | Heatmaps drawn for every concentration; 4,000 polymers used in the write-up (the concentration with the richest time dependence). No concentration reproduces the published diagonal boundary, so the conclusion does not depend on this choice. | agreed |
| I12 | Text says B₀ was "reduced by an order of magnitude" for S41; the caption gives B₀ = 2. | Main p.5, S30 | B₀ = 2, as in the caption. | agreed |
| I13 | How small molecules are "pushed" when a cluster moves is only sketched (S23 figure). | S20, S23 | Free S and P in the cells a cluster leaves move with it; bound molecules move with their bacterium. | agreed |
| I14 | The text refers to "Figs S23–S25" for simulation screenshots; these are actually S28–S30. | S24 | Citation typo; no effect on the model. | noted |
| I15 | What a daughter cell inherits is not stated beyond "not bound to any polymers or AI-2". | S20 | Daughter starts with no bound signal or polymer but inherits the parent's expression level (proteins shared at division). | agreed |
| I16 | Starting division times are not stated. If every cell started at age 0, the population would divide in synchrony. | S23 | First division time drawn uniformly between 0 and one doubling time. | agreed |
| I17 | Starting expression level (BS_express at t = 0) is not stated. BB170 must start "bright" for the decay phase of Fig 4a to appear (cells come from a dense preculture). | S21–S22, Fig 4a | BS_express = BS_c at t = 0 (half-maximal light), for both strains. | agreed |
| I18 | The crowding rule removes signal sites on polymers when local polymer ≥ P_c. Whether polymers attached to bacteria count towards "local polymer" is not stated. | S23 | They do: attached polymers are spread over the bacterium's 4 cells (a bridging polymer counts half on each partner). | agreed |
| I19 | The model plots in the paper (Fig 2c bottom, 4b middle, S31–S42) have no numeric y-axis except the line at 1, and model time is in arbitrary units. | Figs 2c, 4b, S31–S42 | Magnitudes of fold change cannot be compared with the paper; we compare direction, ordering with concentration, and timing. | noted |

## Decisions informed by test runs

**I7 ([P] range), decided 21 Oct.** Both readings were run for MM32 (5 runs per condition; `figures/Pmax7000_blocked0.1/` and `figures/Pmax70000_blocked0.1/`).

- With 0–7,000 polymers, the published concentration trends are reproduced. P1 enhancement increases with [P], P2 quenching deepens with [P], and P3 shows an early dip followed by enhancement, with the switch earlier at higher [P].
- With 0–70,000, P1 enhancement **decreases** with [P]: the maximum fold change is 433× at 10,000 but 3.7× at 70,000. P3 loses its dual behaviour above 20,000, and P2 quenching saturates by 20,000.
- Explanation: above about 8 polymers per cell, f(P) slows signal diffusion everywhere and the crowding rule removes polymer signal sites everywhere, so clusters lose their *local* advantage. In this model the P1 effect is therefore non-monotonic in [P], peaking at roughly 7,000–10,000.
- **Choice: 0–7,000 total polymer molecules.** The 70,000 results are kept as a documented sensitivity check.

**Magnitude of fold changes (I19).** The no-polymer MM32 control is very dim: about 10 bound signals per bacterium, against BS_c = 38, on the steep part of the light function. Small increases in bound signal under P1 therefore give fold changes of up to ~250× (7,000 reading), against ~2× in the experiments. The published model plots carry no numeric scale, so the model magnitude cannot be checked against them.
