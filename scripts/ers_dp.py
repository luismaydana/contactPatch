"""Optimal ERS deployment by dynamic programming over the QSS model.

State: (track point, speed, battery energy). Action: deploy the MGU-K on
this segment or not. The transition physics is the same forward step the
QSS uses (friction-ellipse traction, power-or-grip-limited drive, drag),
and the precomputed backward braking pass keeps every speed reachable.
Braking segments recharge the battery the same way the C++ vehicle model
does: rear-axle brake power into the MGU-K, capped at 350 kW, recovered
at 0.70 efficiency into a 4 MJ store. Deployment over a lap can therefore
exceed the stored 4 MJ, and spending before a heavy braking zone pays off
because recovery against a full battery is wasted. The regulatory 8.5 MJ
per-lap recovery cap is not modeled; physical recovery here stays near
2 MJ, well under it.
Value iteration runs backward over the lap; the recovered policy is then
re-simulated forward so the reported time comes from an exact trajectory,
not from interpolated values.

The greedy allocator in qss_laptime.py (longest acceleration zones first)
is the baseline this is judged against.

run:
  python scripts/ers_dp.py --telemetry data/telemetry/2026_Japan_VER_Q.csv
"""
import argparse
import numpy as np
import pandas as pd
import qss_laptime as q

ETA_REGEN = 0.70
REAR_BRAKE_SHARE = 0.42
E_CAPACITY = q.ENERGY_ERS_PER_LAP


def step_speed(v, kappa_i, straight_i, deploy, ds_i, tire):
    a_lat = v * v * abs(kappa_i)
    ay_max = q.grip_accel_lat(v, tire)
    ax_max = q.grip_accel_long(v, tire)
    r = np.minimum(1.0, a_lat / np.maximum(ay_max, 1e-9))
    a_long = ax_max * np.sqrt(np.maximum(0.0, 1.0 - r * r))
    taper = np.clip((q.MGUK_TAPER_END - v)
                    / (q.MGUK_TAPER_END - q.MGUK_TAPER_START), 0.0, 1.0)
    p_wheels = q.P_ICE + (q.P_ERS * q.ETA_ERS * taper if deploy else 0.0)
    a_drive = np.minimum(q.F_DRIVE, p_wheels / np.maximum(v, 1.0)) / q.M
    a_tire = np.minimum(a_long, a_drive)
    a_accel = np.maximum(0.0, a_tire - q.drag(v, straight_i) / q.M)
    return np.sqrt(v * v + 2.0 * a_accel * ds_i)


def dp_optimize(m, tire="pacejka", dv=0.5, de=50e3):
    dist = m["dist"]
    ds = np.diff(dist)
    kappa = m["kappa"]
    straight = m["straight"]
    v_back = m["v_back"]
    n = len(dist)

    E_MAX = E_CAPACITY

    v_grid = np.arange(4.0, q.V_CAP + dv, dv)
    e_grid = np.arange(0.0, E_MAX + de, de)
    nv, ne = len(v_grid), len(e_grid)

    V = np.zeros((nv, ne))
    policy = np.zeros((n, nv, ne), dtype=bool)
    rows = np.arange(nv)[:, None]
    taper_grid = np.clip((q.MGUK_TAPER_END - v_grid)
                         / (q.MGUK_TAPER_END - q.MGUK_TAPER_START), 0.0, 1.0)

    def regen_energy(v_entry, v_exit, ds_i, straight_i, dt):
        v_mid = 0.5 * (v_entry + v_exit)
        a_dec = np.maximum(0.0, (v_entry * v_entry - v_exit * v_exit) / (2.0 * ds_i))
        a_brk = np.maximum(0.0, a_dec - q.drag(v_mid, straight_i) / q.M)
        p_rear = REAR_BRAKE_SHARE * q.M * a_brk * v_mid
        return np.minimum(p_rear, q.P_ERS) * ETA_REGEN * dt

    for i in range(n - 2, -1, -1):
        vb_next = v_back[i + 1]
        cost_by_action = []
        for deploy in (False, True):
            v_next = step_speed(v_grid, kappa[i], bool(straight[i]), deploy, ds[i], tire)
            v_next = np.clip(np.minimum(v_next, vb_next), v_grid[0], v_grid[-1])
            dt = ds[i] / np.maximum(0.5 * (v_grid + v_next), 1.0)
            jv = np.clip(np.searchsorted(v_grid, v_next), 1, nv - 1)
            wv = (v_next - v_grid[jv - 1]) / (v_grid[jv] - v_grid[jv - 1])
            Vv = (1.0 - wv)[:, None] * V[jv - 1] + wv[:, None] * V[jv]
            if deploy:
                e_next = e_grid[None, :] - (q.P_ERS * taper_grid * dt)[:, None]
                feasible = e_next >= 0.0
            else:
                gain = regen_energy(v_grid, v_next, ds[i], bool(straight[i]), dt)
                e_next = e_grid[None, :] + gain[:, None]
                feasible = np.ones_like(e_next, dtype=bool)
            e_c = np.clip(e_next, 0.0, e_grid[-1])
            je = np.clip(np.searchsorted(e_grid, e_c), 1, ne - 1)
            we = (e_c - e_grid[je - 1]) / (e_grid[je] - e_grid[je - 1])
            Vint = (1.0 - we) * Vv[rows, je - 1] + we * Vv[rows, je]
            cost = np.where(feasible, dt[:, None] + Vint, np.inf)
            cost_by_action.append(cost)
        c_keep, c_dep = cost_by_action
        act = c_dep < c_keep - 1e-12
        policy[i] = act
        V = np.where(act, c_dep, c_keep)

    def sim_step(v, i, deploy):
        v_next = float(step_speed(np.array([v]), kappa[i], bool(straight[i]), deploy, ds[i], tire)[0])
        v_next = min(v_next, float(v_back[i + 1]), float(v_grid[-1]))
        dt = ds[i] / max(0.5 * (v + v_next), 1.0)
        return v_next, dt

    v = float(min(v_back[0], v_grid[-1]))
    e = E_MAX
    t_dp = 0.0
    e_used = 0.0
    e_recovered = 0.0
    v_traj = np.zeros(n)
    v_traj[0] = v
    e_traj = np.zeros(n)
    e_traj[0] = e
    deploy_mask = np.zeros(n, dtype=bool)
    for i in range(n - 1):
        iv = int(np.clip(round((v - v_grid[0]) / dv), 0, nv - 1))
        ie = int(np.clip(round(e / de), 0, ne - 1))
        dep = bool(policy[i][iv, ie])
        if dep:
            v_next, dt = sim_step(v, i, True)
            need = q.P_ERS * q.mguk_taper(v) * dt
            if need > e or need <= 1e-9:
                dep = False
            else:
                e -= need
                e_used += need
        if not dep:
            v_next, dt = sim_step(v, i, False)
            gain = float(regen_energy(v, v_next, ds[i], bool(straight[i]), dt))
            e_recovered += min(gain, E_MAX - e)
            e = min(E_MAX, e + gain)
        t_dp += dt
        v = v_next
        v_traj[i + 1] = v
        e_traj[i + 1] = e
        deploy_mask[i] = dep

    return {
        "t_dp": t_dp,
        "e_used": e_used,
        "e_recovered": e_recovered,
        "deploy_n": int(deploy_mask.sum()),
        "v_traj": v_traj,
        "e_traj": e_traj,
        "deploy_mask": deploy_mask,
    }


def main():
    import matplotlib.pyplot as plt
    ap = argparse.ArgumentParser()
    ap.add_argument("--telemetry", required=True)
    ap.add_argument("--tire", choices=["pacejka", "flat"], default="pacejka")
    ap.add_argument("--dv", type=float, default=0.5)
    ap.add_argument("--de", type=float, default=50e3)
    ap.add_argument("--output", default="data/sim_results/ers_dp.png")
    ap.add_argument("--schedule-output", default="data/sim_results/ers_schedule.csv")
    args = ap.parse_args()

    import os
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(args.schedule_output) or ".", exist_ok=True)

    tel = pd.read_csv(args.telemetry)
    m = q.compute_metrics(tel, tire=args.tire)
    r = dp_optimize(m, tire=args.tire, dv=args.dv, de=args.de)

    dist = m["dist"]
    mask = r["deploy_mask"]
    d0, span = float(dist[0]), float(dist[-1] - dist[0])
    runs = []
    i = 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]:
                j += 1
            runs.append(((dist[i] - d0) / span,
                         (dist[min(j, len(mask) - 1)] - d0) / span))
            i = j
        else:
            i += 1
    pd.DataFrame(runs, columns=["start_frac", "end_frac"]).to_csv(
        args.schedule_output, index=False)
    print(f"deploy schedule: {len(runs)} windows -> {args.schedule_output}")
    t_real = m["t_real"]
    t_no = m["t_no_ers"]
    t_greedy = m["t_sim"]
    t_dp = r["t_dp"]
    print(f"tire model: {args.tire}   grid: dv={args.dv} m/s  de={args.de/1e3:.0f} kJ")
    print(f"real lap:        {t_real:8.3f} s")
    print(f"QSS no ERS:      {t_no:8.3f} s")
    print(f"QSS greedy ERS:  {t_greedy:8.3f} s   (gain {t_no - t_greedy:+.3f} s, "
          f"{m['energy_used']/1e6:.2f} MJ over {m['deployed_n']} pts)")
    print(f"QSS DP ERS:      {t_dp:8.3f} s   (gain {t_no - t_dp:+.3f} s, "
          f"{r['e_used']/1e6:.2f} MJ deployed, {r['e_recovered']/1e6:.2f} MJ "
          f"recovered, {r['deploy_n']} pts)")
    print(f"DP vs greedy:    {t_greedy - t_dp:+.3f} s")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True,
                                   gridspec_kw={"height_ratios": [4, 1]})
    ax1.plot(dist, m["v_real"], color="black", alpha=0.4, lw=1.5, label=f"real ({t_real:.2f} s)")
    ax1.plot(dist, m["v_no_ers"], color="gray", lw=1.0, ls="--", label=f"no ERS ({t_no:.2f} s)")
    ax1.plot(dist, m["v_sim"], color="tab:orange", lw=1.6, label=f"greedy ERS ({t_greedy:.2f} s)")
    ax1.plot(dist, r["v_traj"], color="tab:red", lw=1.6, label=f"DP ERS ({t_dp:.2f} s)")
    ax1.set_ylabel("speed [m/s]")
    ax1.grid(alpha=0.3, linestyle=":")
    ax1.legend(fontsize=9)
    ax1.set_title("ERS deployment: greedy heuristic vs dynamic programming")

    greedy_mask = m["v_sim"] > m["v_no_ers"] + 1e-6
    ax2.fill_between(dist, 0, 1, where=greedy_mask, color="tab:orange", alpha=0.6, step="mid")
    ax2.fill_between(dist, 1, 2, where=r["deploy_mask"], color="tab:red", alpha=0.6, step="mid")
    ax2.set_yticks([0.5, 1.5])
    ax2.set_yticklabels(["greedy", "DP"])
    ax2.set_xlabel("distance [m]")
    ax2.set_ylim(0, 2)
    ax2.grid(alpha=0.3, axis="x", linestyle=":")

    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"saved {args.output}")


if __name__ == "__main__":
    main()
