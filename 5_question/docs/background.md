# Background: how polymers could change quorum sensing

*Draft generated with Claude (Opus 5.5), to be revised by Regina. Logged in `ai_prompts.md`.*

Reproduction of the simulations in Lui et al. (2013) *Nature Chemistry* 5, 1058–1065, "Bacteria clustering by polymers induces the expression of quorum sense controlled phenotypes".

## 1. Mechanism: polymer binding, clustering and signal transport

Quorum sensing (QS) is usually described as a response to population density. Cells release an autoinducer, and once it passes a threshold concentration, target genes switch on. In the *Vibrio harveyi* reporters used here, the output is the *lux* operon, so light. What a cell actually senses, though, is the **local** signal concentration around it. That depends on how quickly the signal is produced, removed and transported away, not only on how many cells there are. Polymers can change all three. The paper sets up three idealised polymer classes.

```
                    ┌── binds cell surface ──► cells cross-linked ──► clusters ──► signal retained locally ──► QS ON earlier  (P1)
 polymer in culture ┤
                    └── binds signal ─────────► less free AI-2 ─────────────────────────────────────────────► QS delayed/reduced (P2)

 P3 (both routes): net effect set by K_PB vs K_PS, [P], time, cell density and growth rate
```

**Bacteria sequestrant (P1, cationic pDMAPMAm).**
- **Binding.** The polymer binds the negatively charged cell surface through multivalent electrostatic interactions. Raising the ionic strength reduces clustering (Fig. S5), which supports this.
- **Clustering.** Each chain can bind more than one cell, so cells become cross-linked into aggregates. In the experiments these reached roughly 25–30 µm within minutes (Fig. 2a).
- **Signal transport.** Inside a cluster, cells are packed together and the surrounding medium is more crowded and viscous. AI-2 near the cells is therefore expected to diffuse away more slowly. The cells experience a higher local signal concentration than the bulk culture would suggest, so QS switches on earlier or more strongly. P1 has no signal-binding chemistry, yet it **induces** the response it was originally meant to prevent (the "anti-adhesive" goal).

**Quorum quencher (P2, poly(vinyl alcohol)).** Its diol groups compete for the boron in the AI-2 borate ester (Fig. 1b). This lowers the amount of active signal in solution, so luminescence falls and QS onset is delayed. It does not cluster cells (Fig. 2a).

**Dual-action polymer (P3, catechol + cationic copolymer).** P3 both clusters cells and binds signal, so the two routes compete. Which one wins depends on several factors:
- the polymer's relative affinities for bacteria (K_PB) and for signal (K_PS)
- polymer concentration
- the time point
- initial cell density and growth rate

The same polymer can therefore enhance or quench QS under only slightly different conditions (Figs. 2c, 3, 4b; S40–S42).

**Timing.** The effect is largest **early** in culture. At that stage cell numbers are low, aggregation (minutes) is much faster than the light response (hours), and clustering makes a large relative difference. As growth raises density throughout the well, the advantage of being in a cluster shrinks, and fold change returns towards 1 (Fig. 2c). This links to a wider debate the paper cites: QS may partly report confinement and diffusion ("diffusion sensing"), not only population size.

## 2. Experimental measurements vs model predictions

| Question | Experimental measurement | Model prediction |
|---|---|---|
| Do polymers cluster cells? | Coulter counter cluster size over 60 min (Fig. 2a, S2–S6); optical microscopy (S7, S8) | Simulated clustering on a 50×50 lattice (Fig. 2b, S28–S30) |
| Is clustering electrostatic? | Clustering reduced in 0.15 M NaCl (S5) | Not modelled; the binding affinity K_PB is simply assigned |
| Are the polymers toxic? | OD600 growth curves (S9–S14); live/dead staining (S27) | Not modelled; growth is a fixed probability distribution |
| Effect on QS in MM32 (responds to AI-2 but cannot make it) | Luminescence / OD fold change (Fig. 2c top, S9–S11) | Simulated fold change vs time (Fig. 2c bottom) |
| Effect on QS in BB170 (makes its own DPD) | Two-phase luminescence and recovery time (Fig. 4a, 4b top and bottom, S12–S17) | Simulated fold change and recovery time (Fig. 4b middle and inset) |
| How do affinities shape the outcome? | **No direct measurement** | Sweep of K_PB × K_PS × [P] at three time points (Fig. 3, S31–S39) |
| Effect of density and growth rate | **No direct measurement** | Varying B₀ and doubling time (S40–S42) |
| Does it generalise? | *E. coli* AHL reporters and *P. aeruginosa* PQS reporter, with P1 only (S19–S26) | Not modelled |

### Where the two meet, and where the claims go beyond the data

- **The mechanism linking clustering to QS is assumed, not observed.** The experiments show two things: polymers cluster cells, and polymers change light output. Nobody measured signal concentration inside clusters. "Slow signal diffusion within clusters" enters the model as rules (blocked diffusion directions, a viscosity factor f(P), and loss of binding sites above a crowding threshold P_c). It is not a result.
- **Luminescence is a proxy for QS.** It is read out as light normalised by OD. Changes in growth or viability can shift it independently of signalling. This matters for *E. coli*, whose growth P1 compromised.
- **Agreement is partly built in.** The methods state that parameters were refined against the measured binding and luminescence. So the match between Fig. 2c top and bottom shows the model *can* reproduce the observed trends. It does not independently confirm the mechanism.
- **Model and experiment use different units.** Model time and concentration are arbitrary units, and the 2D lattice is not a well plate. Only qualitative trends and relative timing can be compared, not absolute magnitudes.
- **The design rules are model-only.** These include "quorum quenchers need very low affinity for bacteria" and "dual-action polymers need low K_PB to quench reliably" (Fig. 3, Discussion). The P3 affinities used (K_PB = 5, K_PS = 10) were assigned in the model, not measured for the real polymer. The text's "the model predicted, and experiments showed" overstates the experimental side here.
- **The generality claim is stretched.** The Discussion says the *E. coli* and *P. aeruginosa* results establish the mechanism of the dual-action polymers, but those experiments used P1 only.

These assumptions are exactly the parts of the model that the reproduction has to implement. They are therefore also the main places where the published settings are ambiguous; see `interpretations.md`.
