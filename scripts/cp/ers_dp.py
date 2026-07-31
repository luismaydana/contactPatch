import numpy as np
import qss_laptime as q
from cp import energy as en


def dp_optimize(m, tire="pacejka", dv=0.5, de=50e3, p_clip=en.P_CLIP,
                recovery_cap=en.RECOVERY_CAP_J):
    dist = m["dist"]
    ds = np.diff(dist)
    kappa = m["kappa"]
    straight = m["straight"]
    v_back = m["v_back"]
    n = len(dist)
    E_MAX = q.ENERGY_ERS_PER_LAP

    v_grid = np.arange(4.0, q.V_CAP + dv, dv)
    e_grid = np.arange(0.0, E_MAX + de, de)
    nv, ne = len(v_grid), len(e_grid)

    V = np.zeros((nv, ne))
    policy = np.zeros((n, nv, ne), dtype=np.int8)
    rows = np.arange(nv)[:, None]
    taper_grid = np.clip((q.MGUK_TAPER_END - v_grid)
                         / (q.MGUK_TAPER_END - q.MGUK_TAPER_START), 0.0, 1.0)

    for i in range(n - 2, -1, -1):
        vb_next = v_back[i + 1]
        st = bool(straight[i])
        costs = []
        for act in (0, 1, 2):
            if act == 2 and not st:
                costs.append(np.full((nv, ne), np.inf))
                continue
            if act == 0:
                p_extra = 0.0
            elif act == 1:
                p_extra = q.P_ERS * q.ETA_ERS * taper_grid
            else:
                p_extra = -p_clip
            v_next = en.step_speed(v_grid, kappa[i], st, ds[i], tire, p_extra,
                                   decel=(act == 2))
            v_next = np.clip(np.minimum(v_next, vb_next), v_grid[0], v_grid[-1])
            dt = ds[i] / np.maximum(0.5 * (v_grid + v_next), 1.0)
            jv = np.clip(np.searchsorted(v_grid, v_next), 1, nv - 1)
            wv = (v_next - v_grid[jv - 1]) / (v_grid[jv] - v_grid[jv - 1])
            Vv = (1.0 - wv)[:, None] * V[jv - 1] + wv[:, None] * V[jv]
            if act == 1:
                e_next = e_grid[None, :] - (q.P_ERS * taper_grid * dt)[:, None]
                feasible = e_next >= 0.0
            elif act == 0:
                gain = en.brake_harvest(v_grid, v_next, ds[i], st, dt)
                e_next = e_grid[None, :] + gain[:, None]
                feasible = np.ones_like(e_next, dtype=bool)
            else:
                gain = p_clip * en.ETA_REGEN * dt
                e_next = e_grid[None, :] + gain[:, None]
                feasible = np.ones_like(e_next, dtype=bool)
            e_c = np.clip(e_next, 0.0, e_grid[-1])
            je = np.clip(np.searchsorted(e_grid, e_c), 1, ne - 1)
            we = (e_c - e_grid[je - 1]) / (e_grid[je] - e_grid[je - 1])
            Vint = (1.0 - we) * Vv[rows, je - 1] + we * Vv[rows, je]
            costs.append(np.where(feasible, dt[:, None] + Vint, np.inf))
        stacked = np.stack(costs, axis=0)
        best = np.argmin(stacked, axis=0)
        policy[i] = best.astype(np.int8)
        V = np.take_along_axis(stacked, best[None], axis=0)[0]

    v = float(min(v_back[0], v_grid[-1]))
    e = E_MAX
    t_dp = 0.0
    e_used = 0.0
    e_recovered = 0.0
    superclip_n = 0
    deploy_mask = np.zeros(n, dtype=bool)
    for i in range(n - 1):
        iv = int(np.clip(round((v - v_grid[0]) / dv), 0, nv - 1))
        ie = int(np.clip(round(e / de), 0, ne - 1))
        act = int(policy[i][iv, ie])
        st = bool(straight[i])
        if act == 1:
            taper = q.mguk_taper(v)
            vn = en.step_speed(np.array([v]), kappa[i], st, ds[i], tire,
                               q.P_ERS * q.ETA_ERS * taper)[0]
            vn = min(vn, float(v_back[i + 1]), float(v_grid[-1]))
            dt = ds[i] / max(0.5 * (v + vn), 1.0)
            need = q.P_ERS * taper * dt
            if need > e or need <= 1e-9:
                act = 0
            else:
                e -= need; e_used += need
        if act == 2:
            vn = en.step_speed(np.array([v]), kappa[i], st, ds[i], tire, -p_clip,
                               decel=True)[0]
            vn = min(vn, float(v_back[i + 1]), float(v_grid[-1]))
            dt = ds[i] / max(0.5 * (v + vn), 1.0)
            gain = p_clip * en.ETA_REGEN * dt
            gain = min(gain, E_MAX - e, max(0.0, recovery_cap - e_recovered))
            e = min(E_MAX, e + gain); e_recovered += gain
            superclip_n += 1
        if act == 0:
            vn = en.step_speed(np.array([v]), kappa[i], st, ds[i], tire, 0.0)[0]
            vn = min(vn, float(v_back[i + 1]), float(v_grid[-1]))
            dt = ds[i] / max(0.5 * (v + vn), 1.0)
            gain = float(en.brake_harvest(np.array([v]), np.array([vn]), ds[i], st,
                                          np.array([dt]))[0])
            gain = min(gain, E_MAX - e, max(0.0, recovery_cap - e_recovered))
            e = min(E_MAX, e + gain); e_recovered += gain
        t_dp += dt
        v = vn
        deploy_mask[i] = (act == 1)

    return {"t_dp": t_dp, "e_used": e_used, "e_recovered": e_recovered,
            "deploy_n": int(deploy_mask.sum()), "superclip_n": superclip_n,
            "deploy_mask": deploy_mask}
