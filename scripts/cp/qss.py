import numpy as np
import qss_laptime as q
from cp import aero

V_SM = 70.0


def corner_speed(kappa, tire, margin=1.0):
    v = np.full_like(kappa, 25.0)
    for _ in range(40):
        v_new = np.sqrt(margin * aero.mu_lat(v, tire, False)
                        * (q.M * q.G + aero.downforce(v, False))
                        / (q.M * np.maximum(kappa, 1e-9)))
        v = 0.5 * v + 0.5 * np.minimum(v_new, q.V_CAP)
    return np.minimum(v, q.V_CAP)


def compute_metrics(tel, tire="pacejka", margin=1.0):
    x = tel["X"].values / 10.0
    y = tel["Y"].values / 10.0
    dist = tel["Distance"].values
    v_real = tel["Speed"].values / 3.6
    kappa = q.calculate_curvature(x, y)
    straight = np.abs(kappa) < q.KAPPA_STRAIGHT
    n = len(dist)
    ds = np.diff(dist)
    v_env = corner_speed(kappa, tire, margin)

    v_back = v_env.copy()
    for i in range(n - 2, -1, -1):
        v = v_back[i + 1]
        st = bool(straight[i + 1])
        a_lat = v * v * kappa[i + 1]
        ay = margin * aero.grip_lat(v, tire, False)
        ax = margin * aero.grip_long(v, tire, False)
        r = min(1.0, a_lat / max(ay, 1e-9))
        a_long = ax * np.sqrt(max(0.0, 1.0 - r * r))
        a_tire = min(a_long, q.F_BRAKE / q.M)
        a_brake = a_tire + aero.drag(v, st) / q.M
        v_allow = np.sqrt(v * v + 2.0 * a_brake * ds[i])
        v_back[i] = min(v_env[i], v_allow)

    def forward_pass(deploy_mask=None):
        v = v_back.copy()
        for i in range(1, n):
            vp = v[i - 1]
            st = bool(straight[i - 1])
            sm = st and vp > V_SM
            a_lat = vp * vp * kappa[i - 1]
            ay = margin * aero.grip_lat(vp, tire, sm)
            ax = margin * aero.grip_long(vp, tire, sm)
            r = min(1.0, a_lat / max(ay, 1e-9))
            a_long = ax * np.sqrt(max(0.0, 1.0 - r * r))
            p_ers = 0.0
            if deploy_mask is not None and deploy_mask[i - 1]:
                p_ers = q.P_ERS * q.ETA_ERS * q.mguk_taper(vp)
            a_drive = min(q.F_DRIVE, (q.P_ICE + p_ers) / max(vp, 1.0)) / q.M
            a_tire = min(a_long, a_drive)
            a_accel = max(0.0, a_tire - aero.drag(vp, st) / q.M)
            v_allow = np.sqrt(vp * vp + 2.0 * a_accel * ds[i - 1])
            v[i] = min(v_back[i], v_allow)
        return v

    v_no_ers = forward_pass(None)

    v_FL = q.P_ICE / q.F_DRIVE
    is_accel = np.zeros(n, dtype=bool)
    for i in range(n - 1):
        if v_no_ers[i + 1] > v_no_ers[i] and v_no_ers[i] >= v_FL:
            is_accel[i] = True
    zones = []
    start = None
    for i in range(n):
        if is_accel[i]:
            if start is None:
                start = i
        else:
            if start is not None:
                zones.append((start, i - 1))
                start = None
    if start is not None:
        zones.append((start, n - 2))
    zones.sort(key=lambda z: -(z[1] - z[0]))

    deploy_mask = np.zeros(n, dtype=bool)
    energy_used = 0.0
    for (a, b) in zones:
        for i in range(a, b + 1):
            dt_i = ds[i] / max(v_no_ers[i], 1.0)
            energy_i = q.P_ERS * q.mguk_taper(v_no_ers[i]) * dt_i
            if energy_i <= 1e-6:
                continue
            if energy_used + energy_i > q.ENERGY_ERS_PER_LAP:
                break
            deploy_mask[i] = True
            energy_used += energy_i
        if energy_used >= q.ENERGY_ERS_PER_LAP:
            break

    v_sim = forward_pass(deploy_mask)

    def lap_time(vv):
        v_seg = 0.5 * (vv[:-1] + vv[1:])
        return float(np.sum(ds / np.maximum(v_seg, 1.0)))

    t_no_ers = lap_time(v_no_ers)
    t_sim = lap_time(v_sim)
    t_real = lap_time(v_real)
    return {
        "n": n, "t_no_ers": t_no_ers, "t_sim": t_sim, "t_real": t_real,
        "err_ers": 100.0 * (t_sim - t_real) / t_real,
        "err_no": 100.0 * (t_no_ers - t_real) / t_real,
        "rmse": float(np.sqrt(np.mean((v_sim - v_real) ** 2))),
        "top_sim": float(v_sim.max()), "top_real": float(v_real.max()),
        "energy_used": energy_used, "deployed_n": int(deploy_mask.sum()),
        "dist": dist, "v_env": v_env, "v_no_ers": v_no_ers, "v_sim": v_sim,
        "v_real": v_real, "v_back": v_back, "kappa": kappa, "straight": straight,
    }
