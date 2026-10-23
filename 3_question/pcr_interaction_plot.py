"""Interaction plot for the virtual PCR 2x2 factorial (cycles x annealing temperature).

All other settings fixed at the optimised baseline:
98 C 10 s / Ta 25 s / 72 C 30 s; 1 uL each dNTP (10 mM), 1 uL each primer (10 uM),
50 ng plasmid, 1 U Phusion. Three replicates per condition.
"""
import numpy as np
import matplotlib.pyplot as plt

# (cycles, annealing temp): [(yield ng/uL, purity %), ...]
data = {
    (25, 58): [(118.8, 96.7), (122.2, 97.0), (116.4, 96.8)],  # A
    (25, 68): [(67.8, 77.0), (67.3, 76.6), (73.9, 78.9)],     # B
    (35, 58): [(118.4, 96.4), (119.8, 96.8), (119.2, 97.0)],  # C
    (35, 68): [(107.8, 91.7), (109.0, 92.4), (111.5, 93.2)],  # D
    (25, 61): [(115.8, 95.8), (119.0, 96.9), (121.1, 97.0)],  # E
    (35, 61): [(121.4, 96.9), (118.5, 97.0), (120.7, 96.9)],  # F
}

cycles = [25, 35]
temps = {58: ("tab:blue", "o", "-"),
         61: ("tab:green", "s", "--"),
         68: ("tab:red", "^", "-")}

fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
for ax, idx, label in zip(axes, [0, 1], ["Yield (ng/µL)", "Purity (%)"]):
    for ta, (colour, marker, style) in temps.items():
        means = [np.mean([r[idx] for r in data[(c, ta)]]) for c in cycles]
        sds = [np.std([r[idx] for r in data[(c, ta)]], ddof=1) for c in cycles]
        ax.errorbar(cycles, means, yerr=sds, color=colour, marker=marker,
                    linestyle=style, capsize=4, linewidth=2, markersize=7,
                    label=f"Annealing {ta} °C")
    ax.set_xticks(cycles)
    ax.set_xlim(22, 38)
    ax.set_xlabel("Number of cycles")
    ax.set_ylabel(label)
    ax.grid(alpha=0.3)

axes[0].legend(frameon=False)
fig.suptitle("Cycles × annealing temperature (mean ± SD, n = 3)")
fig.tight_layout()
fig.savefig("pcr_interaction_plot.png", dpi=300)
plt.show()
