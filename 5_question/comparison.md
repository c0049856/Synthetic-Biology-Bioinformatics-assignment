# Comparison with the published results

*Draft generated with Claude (Opus 5.5) from my simulation outputs; to be checked against the paper's figures and revised.*

All model results use the settings in `params/default.yaml` and the interpretations in `interpretations.md` (polymer counts 0–7,000, I7). Fold change = run-averaged light per bacterium with polymer ÷ the same for the no-polymer control (I10). The published model plots have no numeric y-axis (I19), so comparisons are of **direction, ordering with concentration and timing**, not magnitude.

## Summary

| Paper figure | What is compared | Trend | Timing | Magnitude | Notes |
|---|---|---|---|---|---|
| Fig 2a, 2b (S28–S30) | Clustering by P1, P2, P3 | ✅ P1 and P3 cluster, P2 does not | ⚠️ gradual over the run, not within minutes | n/a (model units) | Clusters are mostly clonal (daughters stay bridged to parents) |
| Fig 2c bottom, P1 | Fold change vs time and [P] | ✅ > 1, stronger and earlier with [P] | ⚠️ declines only ~30% after peak | ❌ up to ~400× | See discrepancies 1 and 2 |
| Fig 2c bottom, P2 | | ✅ < 1, deeper with [P] | ✅ sustained | not comparable | |
| Fig 2c bottom, P3 | | ✅ early dip, then enhancement; dip earlier at higher [P] | ✅ dip first | not comparable | Late enhancement peaks at ~4,000 polymers |
| Fig 3 top (K_PS = 0.1) | [P] × K_PB | ✅ weak K_PB quenches at all [P] and times; higher K_PB enhances, from lower [P] as K_PB rises | ✅ | not comparable | |
| Fig 3 bottom | K_PB × K_PS | ⚠️ low K_PB quenches, high K_PB enhances, but the boundary is almost horizontal: K_PS changes magnitude, rarely sign | ❌ quenching region shrinks with time (paper: grows) | not comparable | Paper's diagonal boundary not reproduced |
| Fig 4a | BB170 control light curve | ✅ decay then enhancement | ⚠️ decay much shorter | ⚠️ shallower decay | |
| Fig 4b middle, P1 | Fold change | ✅ > 1, stronger with [P] | ✅ peak, then decline | plausible (max ~11×) | Relaxes, unlike MM32 |
| Fig 4b middle, P2 | | ✅ < 1, deeper with [P] | ✅ | not comparable | |
| Fig 4b middle, P3 | | ✅ dual: quench at low [P], enhance at high [P] | | not comparable | Threshold-like switch |
| Fig 4b bottom | Recovery time | ✅ P1 earlier, ✅ P2 delayed, ❌ P3 earlier at ≥ 4,000 | | | Paper: P3 delays recovery |
| I5 check (D_S/m) | Cluster diffusion rule | ✅ all light trends unchanged | | | Clusters ~6× larger, light almost the same |
| Coating-only control | P1, P3 without bridges | Clustering needed at moderate [P] and for P3's switch to enhancement | | | Not in the paper |
| S40–S42 | Density and growth effects on P3 | ✅ few cells → enhancement at almost all [P]; faster growth shifts the threshold towards quenching | ✅ | not comparable | Matches the paper's "tip the balance" claim |

## Clustering snapshots (Fig 2b, S28–S30)

*Figure: `figures/Pmax7000_blocked0.1/fig2b_snapshots.png`. One run (seed 20261021), MM32, 7,000 polymers, t = 0 to 30,000 a.u.*

- All four conditions start from identical positions, as the paper specifies (S24).
- With P1 and P3, most cells are already in small groups by t = 5,000, growing to clusters of roughly 5–15 cells by t = 30,000. With P2 and in the control, cells remain single and spread over the grid. This matches the published screenshots qualitatively.
- Each cluster grows **where a single cell started**: clusters in this model are mostly a cell's own descendants. A daughter is placed next to its parent (S20) and is immediately bridged to it by the parent's polymers. Because single bacteria diffuse very slowly (D_B = 0.0005), separate cells rarely meet. In the experiments, aggregation by collision is complete within minutes (Fig 2a), long before division. This is the mechanism behind discrepancy 3 below, and may also contribute to discrepancy 1, since cells stay clustered and coated for the whole run.

## MM32 (Fig 2c), 0–7,000 polymers

*Figures: `figures/Pmax7000_blocked0.1/fig2c_MM32_*.png`; table `summary_mm32.csv`. 10 runs per condition, all 7 concentrations. The 5-run and 10-run results are almost identical, so the trends are robust to the number of runs.*

- **P1 (bacteria sequestrant).** No effect at 1,000 polymers. Above that, the maximum fold change rises steeply with concentration: 12× (2,000), 101× (3,000), 236× (4,000), 318× (5,000), 362× (6,000), 400× (7,000). Higher concentrations peak earlier (about 15,000 a.u. at 2,000 polymers vs about 10,000 at 7,000), matching the ordering in Fig 2c. After the peak the effect declines by only about 30% (7,000 polymers: 400× at 10,300 a.u., 280× at 30,000). The paper's curve returns towards 1.
- **P2 (quorum quencher).** Fold change falls below 1 within the first ~1,000 a.u. and stays stable, deepening smoothly with concentration: 0.74× (1,000) to 0.24× (7,000) at 30,000 a.u. This matches the paper's model and experiment.
- **P3 (dual action).** Every concentration first dips strongly (minimum 0.09–0.12× at 2,000–7,000; 0.28× at 1,000), and the dip comes earlier at higher concentration (about 2,600 a.u. at 2,000 polymers, about 1,200 at 7,000). From 2,000 polymers upwards it then switches to enhancement; 1,000 never switches. The late enhancement is **non-monotonic** in concentration: 8× (2,000), 51× (3,000), a maximum of 112× (4,000), then 89× (5,000), 35× (6,000) and 14× (7,000) at 30,000 a.u. With more polymer, more free polymer binds signal, so the quenching side regains ground. This is the clustering-vs-quenching balance the paper describes, and the same tipping region (~3,000–4,000) appears in BB170.
- **Clustering.** P1 and P3 reach a mean cluster size of about 10–11 bacteria by 30,000 a.u.; P2 never clusters.
- **Growth** is unaffected by any polymer, consistent with the paper's OD and viability data (S9–S11, S27), although in the model this is by construction.

## BB170 (Fig 4), 0–7,000 polymers

*Figures: `figures/Pmax7000_blocked0.1/fig4b_BB170_*.png`; tables `summary_bb170.csv`, `summary_bb170_recovery.csv`. 10 runs per condition, all 7 concentrations.*

- **Control light curve (Fig 4a).** Two phases, as published: log₁₀ total light falls from 4.8 to about 3.5, then rises steadily to about 4.9 by 30,000 a.u. The decay is shallower (about 1.3 log units against about 2) and much shorter than in the paper: the minimum comes at roughly 500 a.u., not a third of the way through the experiment. The decay comes from cells starting bright (I17) and losing expression at K_degrad = 0.01 before their own signal accumulates.
- **P1.** Fold change above 1 at every concentration, increasing with [P]: maximum 1.2× at 1,000 up to 11.2× at 7,000, reached at about 13,000–17,000 a.u. It then declines (4.7× at 30,000 for 7,000 polymers). Unlike MM32, the effect relaxes over time, matching the published shape. Magnitudes are of the same order as the experiments.
- **P2.** Fold change below 1, deepening with [P] and over time: 0.81× (1,000) to 0.38× (7,000) at 30,000 a.u.
- **P3.** Dual behaviour with a threshold. At 1,000–2,000 polymers it quenches (0.49× and 0.44× at 30,000 a.u.). At 3,000 it enhances transiently (peak 2.8×, back to about 1 by 30,000). At 4,000–7,000 it enhances throughout (peak about 4.3×).
- **Recovery time** (time to regain the t = 0 light level; Fig 4b bottom, S15–S17):

  | Polymer | 0 | 1,000 | 2,000 | 3,000 | 4,000 | 5,000 | 6,000 | 7,000 |
  |---|---|---|---|---|---|---|---|---|
  | P1 | 26,100 | 25,000 | 21,900 | 13,800 | 10,900 | 9,300 | 8,700 | 8,300 |
  | P2 | 26,100 | 28,400 | n.r. | n.r. | n.r. | n.r. | n.r. | n.r. |
  | P3 | 26,100 | n.r. | n.r. | 26,000 | 14,600 | 14,500 | 14,800 | 14,800 |

  n.r. = not recovered within 30,000 a.u. P1 shortens recovery and P2 delays it, as published. P3 delays recovery at low concentration but **shortens** it at ≥ 4,000, whereas the paper reports P3 acting as a quorum quencher for BB170 (Fig 4b bottom right).
- **Clustering and growth** behave as in MM32: P1 and P3 cluster (mean cluster size about 10 bacteria by 30,000 a.u.), P2 does not, and growth is identical in all conditions.

## Cell density and growth rate (S40–S42), BB170 + P3

*Figures: `figures/Pmax7000_blocked0.1/S40-42_*.png`; table `summary_density.csv`. 10 runs per condition, all 7 concentrations. K_PB = 5, K_PS = 10, as in the paper.*

The paper claims (main text p.5) that with ten-fold fewer starting cells P3 induces QS throughout and regardless of concentration (S41 vs S40), and that a different growth rate "significantly" changes whether P3 induces or inhibits (S42 vs S40), without stating the direction.

- **S40, standard (B₀ = 25, T = 15,000).** Dual action with a threshold: quenching at 1,000–2,000 polymers (0.49× and 0.44× at 30,000 a.u.), a transient enhancement at 3,000 (peak 2.8×, back to 1.07× at the end), and enhancement at 4,000–7,000 (peak about 4.3×).
- **S41, few starting cells (B₀ = 2).** Enhancement at 2,000–7,000, ending at 5.5–7.2×, higher than at the standard density. No sustained quenching at any concentration (lowest point 0.80×). Only 1,000 stays near 1 (0.86× at the end). The lower concentrations switch later (2,000 at about 20,000 a.u.). Curves are noisier because each run starts from only two cells. **Reproduces the published claim**, with the small exception of the lowest concentration.
- **S42, faster growth (T = 10,000).** The quench/enhance threshold moves up from about 3,000 to about 4,000 polymers: 3,000 now quenches through mid-run (0.76× at 15,000 a.u.) and reaches only 1.26× by the end, 4,000 is weaker (2.27× vs 2.64×), and 2,000 quenches slightly more (0.39× vs 0.44×). **Reproduces the claim that growth rate changes P3's behaviour**; in this model, faster growth favours quenching.
- **Interpretation.** The same polymer at the same concentration can enhance or quench QS depending on cell number and growth rate (3,000 polymers: transient enhancer at standard settings, quencher with faster growth, strong enhancer with few starting cells). A plausible reason for the B₀ = 2 result is that each cell receives far more polymer, becomes fully coated and clustered, while the control stays dim for longer because little signal is produced; this was not tested. As in the paper, these are model-only predictions with no experimental test.

## Affinity sweep (Fig 3, S31–S39), MM32 + P3-type polymers

*Figures: `figures/Pmax7000_blocked0.1/fig3_concentration_vs_KPB.png` and `fig3_affinity_P*.png`; table `summary_sweep.csv`. K_PB and K_PS each in {0.1, 0.5, 1, 5, 10} (25 pairs) × 7 concentrations, read at t = 5,000, 15,000 and 30,000 a.u. 5 runs per condition (paper: 10).*

The paper (Fig 3 and caption; main text pp. 4–5, 7) states: with weak polymer–bacteria affinity, dual-action polymers quench regardless of [P] and time; as K_PB increases, enhancement appears at higher concentrations; the outcome depends on the balance between K_PB and K_PS and on time; polymers with high K_PB enhance "regardless of their concentration and the time of the analysis, even if they showed a high affinity towards the signals"; and consistent quenching requires low K_PB. Its bottom heatmaps show a diagonal boundary (enhancement at high K_PB / low K_PS, quenching at low K_PB / high K_PS), with the quenching region growing from early to late time.

- **Top row ([P] × K_PB at K_PS = 0.1): reproduced.** K_PB = 0.1 quenches at every concentration and time (0.32–0.87×), except a slight rise at 7,000 polymers late (1.37×). For K_PB ≥ 0.5, enhancement appears above a concentration threshold that falls as K_PB rises (mid time: from 3,000 polymers at K_PB = 0.5, from 2,000 at K_PB ≥ 1). The lowest concentration (1,000) gives fold change slightly below 1 for every K_PB.
- **Bottom row (K_PB × K_PS): partly reproduced.**
  - *Low K_PB quenches, high K_PB enhances*: ✅. At 4,000 and 7,000 polymers, K_PB = 0.1 quenches at every K_PS and time (down to 0.08×), and every K_PB ≥ 0.5 enhances by mid and late time, even at K_PS = 10 (e.g. K_PB = 10, K_PS = 10, 4,000 polymers: 144× late). This matches "high affinity for bacteria enhanced light regardless … even with high affinity towards the signals" and the design rule that quenching needs low K_PB.
  - *Effect of K_PS*: ⚠️ weaker than published. Higher K_PS reduces enhancement substantially (7,000 polymers, K_PB = 10, late: 195× at K_PS = 0.1 vs 12× at K_PS = 10) and deepens quenching at K_PB = 0.1 (0.64× → 0.085× at 4,000 late), so the direction agrees. But K_PS rarely changes the *sign*: the boundary between quenching and enhancement is almost horizontal (set by K_PB alone), not diagonal as in the paper.
  - *Time dependence*: ❌ opposite. In the paper the quenching region grows with time. Here it shrinks: at 4,000 polymers early, K_PB = 0.5 still quenches at K_PS = 0.5–5 (0.44–0.98×), but by mid time every K_PB ≥ 0.5 enhances.
  - *Concentration (I11)*: at 1,000 polymers every affinity pair quenches (0.27–0.97×), deepening with K_PS and almost independent of K_PB, because too little polymer is present to cluster cells. At 4,000 and 7,000 the pattern above holds. No concentration gives the published diagonal boundary, so this discrepancy does not depend on the unstated concentration.
- **Likely causes.** (1) The crowding rule (I18) removes signal-binding sites on polymer that has accumulated on bacteria, so in clusters K_PS has no effect; only free polymer can quench. (2) Clustering in this model is very effective (fold changes of tens to hundreds; discrepancy 1), so signal binding has to overcome a much larger enhancement than in the paper. (3) Clusters keep growing throughout the run (discrepancy 3), so the enhancing side gains ground over time instead of fading.
- **Coating-only comparison.** In the control experiment above, P3 (K_PB = 5, K_PS = 10) without bridging stayed a quencher up to 4,000 polymers, whereas the sweep shows the same affinities enhancing strongly with clustering (130× at 4,000 late). Clustering is therefore what makes K_PB dominate K_PS here.

## Sensitivity check: cluster diffusion D_S/m (I5)

*Figures: `figures/Pmax7000_blocked0.1_clusterDS/`; table `summary_mm32.csv` in that folder. MM32, all 7 concentrations, 5 runs per condition. Clusters of m > 1 bacteria move at D_S/m (literal reading of S22 item 9) instead of D_B/m; single bacteria still move at D_B.*

- **Clustering changes dramatically.** The mean cluster size reaches about 55–60 bacteria by 30,000 a.u. (vs about 10 with D_B/m) and passes 10 already at about 6,000 a.u. (vs about 30,000). Fast-moving clusters collide and merge, so most of the population (maximum 80) ends up in one or two large clusters.
- **Light responses barely change.** P1: maximum fold change 434× at 7,000 (vs 400×) and 122× at 3,000 (vs 101×), with the same concentration ordering; a small effect now also appears at 1,000 polymers (4.3× vs 1.2×). P2: unchanged (0.25× vs 0.24× at 7,000). P3: same dip-then-enhancement pattern, with the late-time optimum at about 5,000 instead of about 4,000. Differences are of the size expected from 5 vs 10 runs.
- **Conclusions.** (1) The qualitative results are robust to the I5 choice. (2) In this implementation the light response is nearly insensitive to cluster size: six-fold larger clusters give almost the same fold changes. This suggested either that the enhancement comes mainly from polymer coating each bacterium (f(P) counting attached polymer, I18), or that the effect saturates once cells are in any cluster. The coating-only control below distinguishes the two.

## Control experiment: coating without clustering (not in the paper)

*Figures: `figures/Pmax7000_blocked0.1_nobridge/` (the empty P2 panel is expected: P2 was not rerun, since it does not bind bacteria). MM32, P1 and P3 at all 7 concentrations, 5 runs per condition, run in Claude's environment rather than on my laptop. Polymers can bind bacteria as normal but cannot bridge two bacteria, so no clusters form (`run.py --no-bridges`). This separates the effect of polymer coating each cell (which slows signal diffusion around it, f(P) with I18) from the effect of clustering.*

| P1, maximum fold change | 2,000 | 3,000 | 4,000 | 5,000 | 6,000 | 7,000 |
|---|---|---|---|---|---|---|
| With clustering (10 runs) | 12× | 101× | 236× | 318× | 362× | 400× |
| Coating only (5 runs) | 1.4× | 9.3× | 67× | 192× | 289× | 334× |

| P3, fold change at 30,000 a.u. | 2,000 | 3,000 | 4,000 | 5,000 | 6,000 | 7,000 |
|---|---|---|---|---|---|---|
| With clustering (10 runs) | 8.0× | 51× | 112× | 89× | 35× | 14× |
| Coating only (5 runs) | 0.15× | 0.11× | 0.28× | 1.1× | 2.5× | 4.5× |

- **P1.** Without clustering, the enhancement largely disappears at low and intermediate concentrations (2,000–4,000: 1.4–67× instead of 12–236×) but mostly survives at the highest concentrations (6,000–7,000: 80–90% of the clustered value), where coating alone slows diffusion around each cell enough. The effect also fades more over time without clustering (4,000 polymers: 12.6× at 30,000 a.u. vs 164× with clustering).
- **P3.** Without clustering, P3 behaves mainly as a **quencher**: it stays below 1 up to 4,000 polymers and reaches only 4.5× at 7,000. With clustering it switches to strong enhancement from 2,000 polymers upwards. The non-monotonic optimum at ~4,000 seen with clustering disappears; without it, the response simply increases with concentration.
- **Conclusions.** Both mechanisms contribute in this model. Clustering is what produces the effect at moderate polymer concentrations and what turns P3 from a quencher into an enhancer, which supports the paper's central claim. Coating alone accounts for most of P1's effect at the highest concentrations. Together with the D_S/m check (six-fold larger clusters gave almost the same light), this indicates that the effect of clustering saturates: being in a cluster matters, but the size of the cluster beyond a few cells matters little.

## Discrepancies and likely causes

1. **Fold-change magnitude.** The control becomes very dim (about 10 bound signals per bacterium against BS_c = 38, where the light function is steep), so modest increases in bound signal give very large fold changes (up to ~400× for P1 at 7,000 polymers). The experiments show about 2×, and BB170 in this model reaches only ~11×. The paper does not report model magnitudes, so we cannot tell whether its model behaved the same way.
2. **No relaxation of the P1 effect in MM32** (it does relax in BB170). In the paper, the advantage of clustering fades as growth raises density everywhere. In this implementation, polymer-coated bacteria keep slowing signal diffusion around themselves (f(P) falls with local polymer, including attached polymer, I18), so the advantage persists. In BB170 the cells keep producing signal, so the control brightens over time and the fold change falls back, as published. The difference may therefore come from MM32's fixed signal supply (S₀ = 10,000, no production) being shared among more and more cells.
3. **Clustering speed and mechanism.** The paper states aggregation is much faster than the light response. Here clusters grow over the whole run, and the snapshots show they are mostly clonal: daughters placed next to their parents are bridged at once, while single bacteria diffuse too slowly (D_B = 0.0005) to collide often. The experimental clusters form by collision within minutes.
4. **P3 in BB170 at high concentration.** The paper reports P3 delaying recovery (quenching); here it shortens recovery at ≥ 4,000 polymers, so clustering wins over signal binding. Candidate causes: the crowding rule removes signal sites on polymers attached to bacteria (I18), which weakens P3's quenching exactly where polymer is concentrated; P3's forward and backward rates are not given (I3); and the paper's own Fig 3 shows the P3 outcome is highly sensitive to the K_PB/K_PS balance.
5. **Fig 3: K_PS rarely changes the sign of the effect.** The published quench/enhance boundary is diagonal in K_PB × K_PS and the quenching region grows with time; here the boundary is set almost entirely by K_PB and quenching shrinks with time. Likely causes as for discrepancy 4 (crowding rule I18 disabling polymer signal sites on bacteria; very strong clustering effect; clusters growing throughout the run).
6. **Length of the BB170 decay phase.** Expression decays within about 100 a.u. (K_degrad = 0.01), so the light minimum comes very early, whereas experimentally it falls about a third of the way through. The starting expression level is not given in the paper (I17).
7. **Sensitivity to the [P] interpretation (I7).** With 0–70,000 polymers the P1 effect *decreases* with concentration, because crowding and viscosity act everywhere rather than only near clusters. The model's response to polymer is therefore non-monotonic, which the paper does not mention.
