"""Lattice model of polymer-induced bacterial clustering and quorum sensing.

Reimplementation of the model in the Supplementary Information of
Lui et al. (2013) Nature Chemistry 5:1058-1065, pages S19-S23.

Implementation choices that differ from, or fill gaps in, the published
description are marked with their ID from docs/interpretations.md (I1, I2, ...).

Main difference (I9): the paper uses an exact Gillespie algorithm. Here time
advances in fixed steps. Signal diffusion and signal binding are updated every
`dt`; the slower processes (polymer diffusion, polymer-bacterium binding,
cluster formation, cluster movement, division) every `slow_every * dt`.
Within a step, the number of molecules that move or react is drawn from a
binomial distribution with probability 1 - exp(-rate * dt).

Grid layout: arrays are indexed [i, j]; a bacterium with top-left corner (i, j)
occupies cells (i, j), (i+1, j), (i, j+1), (i+1, j+1).
"""

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

# (di, dj) for the four lattice directions
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def triangular_doubling(rng, mean, width, size=None):
    """Division time drawn from a triangular distribution (S23 item 11)."""
    left = max(mean - width / 2, 0.0)  # T = 10000 (S42) with width 20000 starts at 0
    return np.maximum(rng.triangular(left, mean, mean + width / 2, size=size), 1.0)


def shift(arr, di, dj):
    """Move array contents one cell in direction (di, dj); content pushed off the edge is dropped.
    Callers make sure nothing is ever pushed off the edge (reflecting walls, I1)."""
    out = np.zeros_like(arr)
    n = arr.shape[0]
    src_i = slice(max(0, -di), n - max(0, di))
    dst_i = slice(max(0, di), n - max(0, -di))
    src_j = slice(max(0, -dj), n - max(0, dj))
    dst_j = slice(max(0, dj), n - max(0, -dj))
    out[dst_i, dst_j] = arr[src_i, src_j]
    return out


def edge_mask(n, di, dj):
    """True where a move in direction (di, dj) stays inside the grid (reflecting walls, I1)."""
    m = np.ones((n, n), dtype=bool)
    if di == -1:
        m[0, :] = False
    if di == 1:
        m[-1, :] = False
    if dj == -1:
        m[:, 0] = False
    if dj == 1:
        m[:, -1] = False
    return m


class Simulation:
    def __init__(self, params, strain="MM32", K_PB=0.0, K_PS=0.0, n_polymers=0,
                 seed=0, B0=None, doubling_mean=None, blocked_factor=None, dt=None,
                 record_snapshots=(), cluster_diffusion=None, allow_bridges=True):
        p = params
        self.p = p
        self.N = p["grid_size"]
        self.dt = dt if dt is not None else p["dt"]
        self.slow_every = p.get("slow_every", 10)
        self.dt_slow = self.dt * self.slow_every
        self.blocked = blocked_factor if blocked_factor is not None else p["blocked_factor"]
        # I5: cluster of m bacteria moves at D_B/m (default) or, read literally, D_S/m
        self.cluster_rule = cluster_diffusion or p.get("cluster_diffusion", "D_B_over_m")
        # control experiment (not in the paper): polymers coat bacteria but cannot link them
        self.allow_bridges = allow_bridges
        st = p["strains"][strain]
        self.strain = strain
        self.BS_c = st["BS_c"]
        self.production = st["production_rate"]
        self.B_max = p["B_max"]
        self.doubling_mean = doubling_mean if doubling_mean is not None else p["doubling_mean"]
        self.doubling_width = p["doubling_width"]

        # binding constants: k_on = K * k_off (I3); K_BS uses its stated rates
        k_off = p["k_off"]
        self.k_off = k_off
        self.kon_PB = K_PB * k_off
        self.kon_PS = K_PS * k_off
        self.kon_BS = p["K_BS"] * k_off  # 0.5 * 0.002 = 0.001, as stated on S21
        self.n_PB, self.n_PS = p["polymer_sites_for_bacteria"], p["polymer_sites_for_signal"]
        self.n_BP, self.n_BS = p["bacterium_sites_for_polymer"], p["bacterium_sites_for_signal"]
        self.P_crit = p["P_crit"]
        self.lam = p["lambda_viscosity"]

        # Separate random streams. Initial bacteria and signal placement depends only
        # on the seed, so every polymer condition with the same seed starts from the
        # same cells and signals, as the paper states for its simulations (S24, Fig 2).
        ss = np.random.SeedSequence(seed)
        rng_init, rng_poly, rng_dyn = [np.random.default_rng(s) for s in ss.spawn(3)]
        self.rng = rng_dyn

        N = self.N
        self.S = np.zeros((N, N), dtype=np.int64)    # free signals
        self.P = np.zeros((N, N), dtype=np.int64)    # free polymers (not attached to a bacterium)
        self.PS = np.zeros((N, N), dtype=np.int64)   # signals bound to free polymers
        self.occ = -np.ones((N, N), dtype=np.int64)  # bacterium index occupying each cell

        Bm = self.B_max
        self.alive = np.zeros(Bm, dtype=bool)
        self.bx = np.zeros(Bm, dtype=np.int64)
        self.by = np.zeros(Bm, dtype=np.int64)
        self.BS = np.zeros(Bm, dtype=np.int64)       # signals bound to the bacterium (sensed)
        self.n1 = np.zeros(Bm, dtype=np.int64)       # polymers attached to this bacterium only
        self.L = np.zeros((Bm, Bm), dtype=np.int64)  # L[a, b]: polymers owned by a that also bind b
        self.PSatt = np.zeros(Bm, dtype=np.int64)    # signals bound to polymers owned by a
        self.expr = np.zeros(Bm)                     # BS_express (S21-S22 item 5)
        self.next_div = np.full(Bm, np.inf)

        # initial bacteria: random non-overlapping 2x2 positions
        B0 = B0 if B0 is not None else p["B0"]
        placed = 0
        while placed < B0:
            i, j = rng_init.integers(0, N - 1, size=2)
            if (self.occ[i:i + 2, j:j + 2] < 0).all():
                self._add_bacterium(placed, i, j)
                placed += 1
        init_expr = p.get("initial_expression", "BS_c")  # I17
        self.expr[:B0] = self.BS_c if init_expr == "BS_c" else float(init_expr)
        # random phase in the division cycle so the population does not divide in step (I16)
        first = triangular_doubling(rng_init, self.doubling_mean, self.doubling_width, B0)
        self.next_div[:B0] = rng_init.uniform(0, 1, B0) * first

        # signals and polymers spread uniformly at random over the grid (I7)
        np.add.at(self.S, (rng_init.integers(0, N, st["S0"]), rng_init.integers(0, N, st["S0"])), 1)
        if n_polymers > 0:
            np.add.at(self.P, (rng_poly.integers(0, N, n_polymers), rng_poly.integers(0, N, n_polymers)), 1)

        self.t = 0.0
        self.edge = {d: edge_mask(N, *d) for d in DIRECTIONS}
        self.snap_times = sorted(record_snapshots)
        self.snapshots = []
        self._refresh_bacteria_fields()

    # ------------------------------------------------------------------ helpers
    def _add_bacterium(self, a, i, j):
        self.alive[a] = True
        self.bx[a], self.by[a] = i, j
        self.occ[i:i + 2, j:j + 2] = a

    def _cells(self, idx):
        """Coordinates of the 4 cells of each bacterium in idx: arrays of shape (len(idx), 4)."""
        ci = np.stack([self.bx[idx], self.bx[idx] + 1, self.bx[idx], self.bx[idx] + 1], axis=1)
        cj = np.stack([self.by[idx], self.by[idx], self.by[idx] + 1, self.by[idx] + 1], axis=1)
        return ci, cj

    def _split4(self, counts):
        """Split counts per bacterium at random over its 4 cells (shape (n, 4))."""
        rng = self.rng
        c0 = rng.binomial(counts, 1 / 4)
        r = counts - c0
        c1 = rng.binomial(r, 1 / 3)
        r = r - c1
        c2 = rng.binomial(r, 1 / 2)
        return np.stack([c0, c1, c2, r - c2], axis=1)

    def _release(self, target, counts):
        """Put counts[a] molecules back into the cells of each alive bacterium a."""
        idx = np.nonzero(self.alive & (counts > 0))[0]
        if idx.size == 0:
            return
        ci, cj = self._cells(idx)
        np.add.at(target, (ci.ravel(), cj.ravel()), self._split4(counts[idx]).ravel())

    def _refresh_bacteria_fields(self):
        """Recompute per-cell quantities derived from the bacteria (after slow updates)."""
        a = self.occ
        occ_mask = a >= 0
        ai = np.where(occ_mask, a, 0)
        bridges_out = self.L.sum(axis=1)
        bridges_in = self.L.sum(axis=0)
        self.att_owned = self.n1 + bridges_out
        self.BP_used = self.n1 + bridges_out + bridges_in
        # attached polymers counted towards local polymer density; a bridge counts half
        # on each partner, and a bacterium's polymers are spread over its 4 cells
        load = (self.n1 + 0.5 * (bridges_out + bridges_in)) / 4.0
        self.att_cell = np.where(occ_mask, load[ai], 0.0)
        self.occ_mask = occ_mask
        self.ai = ai
        # small molecules entering a cell of a different bacterium are slowed (I4)
        self.factor = {}
        for d in DIRECTIONS:
            dest = shift(a, -d[0], -d[1])  # occupant of the cell each molecule would move into
            dest = np.where(self.edge[d], dest, -1)
            blocked = (dest >= 0) & (dest != a)
            self.factor[d] = np.where(self.edge[d], np.where(blocked, self.blocked, 1.0), 0.0)

    # ------------------------------------------------------------------ diffusion
    def _diffuse(self, X, prob_base, carried=None):
        """Move molecules in X one cell in each of the four directions.
        prob_base: per-direction move probability before blocking (array or scalar).
        carried: optional array of molecules bound to X that travel with it (PS with P)."""
        rng = self.rng
        remaining = X.copy()
        rem_c = carried.copy() if carried is not None else None
        left = np.ones_like(X, dtype=float)
        newX = np.zeros_like(X)
        newC = np.zeros_like(carried) if carried is not None else None
        for d in DIRECTIONS:
            pd = prob_base * self.factor[d]
            cond = np.clip(np.divide(pd, left, out=np.zeros_like(left), where=left > 0), 0, 1)
            moved = rng.binomial(remaining, cond)
            if carried is not None:
                frac = np.divide(moved, remaining, out=np.zeros(moved.shape), where=remaining > 0)
                movedc = rng.binomial(rem_c, frac)
                rem_c = rem_c - movedc
                newC += shift(movedc, *d)
            remaining = remaining - moved
            left = left - pd
            newX += shift(moved, *d)
        X[:] = remaining + newX
        if carried is not None:
            carried[:] = rem_c + newC

    def _f_viscosity(self, Ploc):
        """f(P) from S22 item 8: (1/2.2) * (tanh((lambda - P)/2) + 1.2)."""
        return (np.tanh((self.lam - Ploc) / 2.0) + 1.2) / 2.2

    # ------------------------------------------------------------------ fast step
    def _fast_step(self):
        rng, dt = self.rng, self.dt
        Ploc = self.P + self.att_cell
        crowded = Ploc >= self.P_crit  # S23 item 10: polymer signal sites lost (I18)

        # signal diffusion, slowed by local polymer (S22 item 8) and by bacteria (I4)
        p_move = 1 - np.exp(-self.p["D_S"] * self._f_viscosity(Ploc) * dt)
        self._diffuse(self.S, p_move)

        # signal binding: free signals compete for free-polymer, attached-polymer and bacterium sites
        a, m = self.ai, self.occ_mask
        sites_fp = np.where(crowded, 0, np.maximum(self.n_PS * self.P - self.PS, 0)).astype(float)
        sites_ap = np.where(m & ~crowded,
                            np.maximum(self.n_PS * self.att_owned - self.PSatt, 0)[a] / 4.0, 0.0)
        sites_b = np.where(m, np.maximum(self.n_BS - self.BS, 0)[a] / 4.0, 0.0)  # I2
        r_fp = self.kon_PS * sites_fp
        r_ap = self.kon_PS * sites_ap
        r_b = self.kon_BS * sites_b
        r = r_fp + r_ap + r_b
        n = rng.binomial(self.S, 1 - np.exp(-r * dt))
        n_b = rng.binomial(n, np.divide(r_b, r, out=np.zeros_like(r), where=r > 0))
        rest = n - n_b
        r2 = r_fp + r_ap
        n_ap = rng.binomial(rest, np.divide(r_ap, r2, out=np.zeros_like(r2), where=r2 > 0))
        n_fp = np.minimum(rest - n_ap, sites_fp.astype(np.int64))
        back = rest - n_ap - n_fp
        self.S -= n - back
        self.PS += n_fp
        Bm = self.B_max
        add_b = np.bincount(a[m], weights=n_b[m], minlength=Bm).astype(np.int64)
        add_ap = np.bincount(a[m], weights=n_ap[m], minlength=Bm).astype(np.int64)
        # cap at the sites available; any excess goes straight back as free signal
        over_b = np.maximum(self.BS + add_b - self.n_BS, 0)
        over_ap = np.maximum(self.PSatt + add_ap - self.n_PS * self.att_owned, 0)
        self.BS += add_b - over_b
        self.PSatt += add_ap - over_ap
        self._release(self.S, over_b + over_ap)

        # unbinding (all binding is reversible, main-text Methods)
        pu = 1 - np.exp(-self.k_off * dt)
        u = rng.binomial(self.PS, pu)
        self.PS -= u
        self.S += u
        ub = rng.binomial(self.BS, pu) * self.alive
        ua = rng.binomial(self.PSatt, pu) * self.alive
        self.BS -= ub
        self.PSatt -= ua
        self._release(self.S, ub + ua)

        # signal production by BB170 (S23 item 12)
        if self.production > 0:
            made = rng.poisson(self.production * dt, self.B_max) * self.alive
            self._release(self.S, made)

        # expression dynamics (S21-S22 item 5), explicit Euler
        sense = self.BS.astype(float)
        under = sense > self.expr
        self.expr = np.where(under, self.expr + self.p["K_syn"] * (sense - self.expr) * dt,
                             self.expr - self.p["K_degrad"] * self.expr * dt)  # I6

    # ------------------------------------------------------------------ slow step
    def _slow_step(self):
        rng, dts = self.rng, self.dt_slow
        kon, koff = self.kon_PB, self.k_off

        # polymer diffusion, carrying bound signals (S22 item 7, I4)
        p_move = 1 - np.exp(-self.p["D_P"] * dts)
        self._diffuse(self.P, p_move, carried=self.PS)

        if kon > 0:
            self._polymer_bacterium_binding(dts)
        self._bridges(dts)
        self._move_clusters(dts)
        self._divide()
        self._refresh_bacteria_fields()

    def _polymer_bacterium_binding(self, dts):
        rng, kon, koff = self.rng, self.kon_PB, self.k_off
        Bm = self.B_max
        a, m = self.ai, self.occ_mask
        free_BP = np.maximum(self.n_BP - self.BP_used, 0)
        # each free polymer in a bacterium's cell binds with rate k_on * (its 2 sites) * (free sites in that cell)
        rate = np.where(m, kon * self.n_PB * free_BP[a] / 4.0, 0.0)
        nb = rng.binomial(self.P, 1 - np.exp(-rate * dts))
        frac = np.divide(nb, self.P, out=np.zeros(nb.shape), where=self.P > 0)
        nps = rng.binomial(self.PS, frac)
        self.P -= nb
        self.PS -= nps
        add = np.bincount(a[m], weights=nb[m], minlength=Bm).astype(np.int64)
        addps = np.bincount(a[m], weights=nps[m], minlength=Bm).astype(np.int64)
        over = np.maximum(add - free_BP, 0)  # more polymers than free sites: return the excess
        if over.any():
            overps = rng.binomial(addps, np.divide(over, add, out=np.zeros(Bm), where=add > 0))
            add -= over
            addps -= overps
            self._release(self.P, over)
            self._release(self.PS, overps)
        self.n1 += add
        self.PSatt += addps

        # single attachments let go (polymer and its bound signals return to the bacterium's cells)
        d = rng.binomial(self.n1, 1 - np.exp(-koff * dts)) * self.alive
        owned = self.n1 + self.L.sum(axis=1)
        dps = rng.binomial(self.PSatt, np.divide(d, owned, out=np.zeros(Bm), where=owned > 0))
        self.n1 -= d
        self.PSatt -= dps
        self._release(self.P, d)
        self._release(self.PS, dps)

    def _adjacency(self):
        idx = np.nonzero(self.alive)[0]
        A = np.zeros((self.B_max, self.B_max), dtype=bool)
        if idx.size < 2:
            return A
        dx = np.abs(self.bx[idx, None] - self.bx[None, idx])
        dy = np.abs(self.by[idx, None] - self.by[None, idx])
        touch = (dx <= 2) & (dy <= 2)
        np.fill_diagonal(touch, False)
        A[np.ix_(idx, idx)] = touch
        return A

    def _bridges(self, dts):
        """Polymers attached to one bacterium bind a touching neighbour (S20 item 4, main-text Methods)."""
        rng, kon, koff = self.rng, self.kon_PB, self.k_off
        # breaking: either end of a bridging polymer can let go
        if self.L.any():
            br = rng.binomial(self.L, 1 - np.exp(-2 * koff * dts))
            lose_owner_end = rng.binomial(br, 0.5)  # polymer stays on b and now belongs to b
            keep = br - lose_owner_end              # polymer stays on a as a single attachment
            self.L -= br
            self.n1 += keep.sum(axis=1)
            moved = lose_owner_end.sum(axis=1)
            self.n1 += lose_owner_end.sum(axis=0)
            # bound signals follow the polymers that changed owner
            owned = self.n1 + self.L.sum(axis=1)
            for a in np.nonzero(moved)[0]:
                tot = owned[a] + moved[a]
                k = rng.binomial(self.PSatt[a], moved[a] / tot) if tot > 0 else 0
                self.PSatt[a] -= k
                targets = lose_owner_end[a]
                if k > 0:
                    self.PSatt += rng.multinomial(k, targets / targets.sum())
        if kon == 0 or not self.allow_bridges:
            return
        A = self._adjacency()
        free_BP = np.maximum(self.n_BP - (self.n1 + self.L.sum(axis=1) + self.L.sum(axis=0)), 0)
        for a in np.nonzero((self.n1 > 0) & A.any(axis=1))[0]:
            rates = kon * free_BP * A[a]
            R = rates.sum()
            if R <= 0:
                continue
            k = rng.binomial(self.n1[a], 1 - np.exp(-R * dts))
            if k == 0:
                continue
            new = rng.multinomial(k, rates / R)
            new = np.minimum(new, free_BP)
            self.L[a] += new
            self.n1[a] -= new.sum()
            free_BP -= new

    def _move_clusters(self, dts):
        """Bacteria joined by polymers move as one unit at D_B / m (S22 item 9, I5) and push
        small molecules ahead of them (S20, S23 sketch, I13)."""
        rng = self.rng
        idx = np.nonzero(self.alive)[0]
        G = csr_matrix((self.L + self.L.T)[np.ix_(idx, idx)] > 0)
        ncomp, labels = connected_components(G, directed=False)
        self.cluster_sizes = np.bincount(labels)
        for c in range(ncomp):
            members = idx[labels == c]
            m = len(members)
            if m > 1 and self.cluster_rule == "D_S_over_m":
                D = self.p["D_S"] / m   # literal reading of S22 item 9 (sensitivity check)
            else:
                D = self.p["D_B"] / m   # single bacteria always move at D_B
            pm = 1 - np.exp(-D * dts)
            u = rng.random()
            if u >= 4 * pm:
                continue
            di, dj = DIRECTIONS[int(u / pm)]
            ni, nj = self.bx[members] + di, self.by[members] + dj
            if (ni < 0).any() or (nj < 0).any() or (ni > self.N - 2).any() or (nj > self.N - 2).any():
                continue
            ci, cj = self._cells(members)
            ti, tj = ci + di, cj + dj
            occ_t = self.occ[ti, tj]
            if ((occ_t >= 0) & ~np.isin(occ_t, members)).any():
                continue  # blocked by another bacterium
            old = set(zip(ci.ravel(), cj.ravel()))
            new = set(zip(ti.ravel(), tj.ravel()))
            entering = list(new - old)
            for X in (self.S, self.P, self.PS):
                # molecules in the cells being entered are pushed one cell further on
                carry_e = [X[e] for e in entering]
                for e in entering:
                    X[e] = 0
                carry_o = X[ci, cj].copy()
                X[ci, cj] = 0
                np.add.at(X, (ti.ravel(), tj.ravel()), carry_o.ravel())
                for (ei, ej), v in zip(entering, carry_e):
                    fi, fj = ei + di, ej + dj
                    if 0 <= fi < self.N and 0 <= fj < self.N:
                        X[fi, fj] += v
                    else:
                        X[ei, ej] += v
            self.occ[ci, cj] = -1
            self.bx[members] = ni
            self.by[members] = nj
            ci2, cj2 = self._cells(members)
            self.occ[ci2, cj2] = np.repeat(members, 4).reshape(-1, 4)

    def _divide(self):
        """Division (S20, S23 item 11); the daughter goes to the nearest empty 2x2 space and
        carries no bound polymer or signal. The daughter inherits the parent's expression (I15)."""
        rng = self.rng
        due = np.nonzero(self.alive & (self.next_div <= self.t))[0]
        for a in due:
            free_slots = np.nonzero(~self.alive)[0]
            if free_slots.size == 0:
                self.next_div[self.alive] = np.inf  # population cap reached (B_max = 80)
                return
            empty = self.occ < 0
            ok = empty[:-1, :-1] & empty[1:, :-1] & empty[:-1, 1:] & empty[1:, 1:]
            cand = np.argwhere(ok)
            if cand.size == 0:
                self.next_div[a] = self.t + triangular_doubling(rng, self.doubling_mean, self.doubling_width)
                continue
            dist = (cand[:, 0] - self.bx[a]) ** 2 + (cand[:, 1] - self.by[a]) ** 2
            best = cand[dist == dist.min()]
            i, j = best[rng.integers(len(best))]
            b = free_slots[0]
            self._add_bacterium(b, i, j)
            self.BS[b] = self.n1[b] = self.PSatt[b] = 0
            self.L[b, :] = 0
            self.L[:, b] = 0
            self.expr[b] = self.expr[a]
            for x in (a, b):
                self.next_div[x] = self.t + triangular_doubling(rng, self.doubling_mean, self.doubling_width)

    # ------------------------------------------------------------------ output
    def luminescence(self):
        """Light per bacterium (S22 item 6): scale * (1 - tanh(dBS / 2)), dBS = 0.25 * (BS_c - BS_express)."""
        dBS = 0.25 * (self.BS_c - self.expr)
        lum = self.p["lum_scale"] * (1 - np.tanh(dBS / 2))
        return np.where(self.alive, lum, 0.0)

    def observe(self):
        lum = self.luminescence()
        nb = int(self.alive.sum())
        sizes = getattr(self, "cluster_sizes", np.ones(nb, dtype=int))
        return {
            "n_bacteria": nb,
            "lum_total": lum.sum(),
            "lum_per_bacterium": lum.sum() / max(nb, 1),
            "mean_cluster_size": float((sizes ** 2).sum() / max(sizes.sum(), 1)),  # size seen by an average bacterium
            "n_clustered": int(sizes[sizes > 1].sum()),
            "signal_free": int(self.S.sum()),
            "signal_on_bacteria": int(self.BS[self.alive].sum()),
            "signal_on_polymers": int(self.PS.sum() + self.PSatt[self.alive].sum()),
            "polymers_attached": int(self.n1.sum() + self.L.sum()),
        }

    def snapshot(self):
        idx = np.nonzero(self.alive)[0]
        return {"t": self.t, "bx": self.bx[idx].copy(), "by": self.by[idx].copy(),
                "lum": self.luminescence()[idx], "clustered": (self.n1[idx] >= 0) &
                ((self.L[idx].sum(axis=1) + self.L[:, idx].sum(axis=0)) > 0)}

    def run(self, t_end=None, t_record=None):
        t_end = t_end if t_end is not None else self.p["t_end"]
        t_record = t_record if t_record is not None else self.p["t_record"]
        n_steps = int(round(t_end / self.dt))
        rec_every = max(1, int(round(t_record / self.dt)))
        self._move_clusters(0.0)  # initialises cluster sizes without moving anything
        out = {k: [] for k in self.observe()}
        times = []
        snaps = list(self.snap_times)
        for step in range(n_steps + 1):
            if step % rec_every == 0:
                times.append(self.t)
                for k, v in self.observe().items():
                    out[k].append(v)
            while snaps and self.t >= snaps[0]:
                self.snapshots.append(self.snapshot())
                snaps.pop(0)
            if step == n_steps:
                break
            self._fast_step()
            if (step + 1) % self.slow_every == 0:
                self._slow_step()
            self.t += self.dt
        res = {k: np.asarray(v) for k, v in out.items()}
        res["time"] = np.asarray(times)
        return res
