"""Quasi-steady-state lap time simulation over a race line,
validated against the real FastF1 speed trace.

Uses the contactPatch BatchVehicleConfig parameters (drive force, brake force,
mode-dependent aero) plus the documented F1 2026 power split. Nothing is tuned
to match the real lap time; the residual is the expected QSS optimism (a
perfect driver always at the limit, vs the real driver's margin).

Two tire models:
  "flat"     single friction coefficient MU, the original point-mass model.
  "pacejka"  load-sensitive peak friction from the C++ tire model
             (p_d1 + p_d2 * dfz at the per-wheel load including downforce),
             separate longitudinal and lateral peaks combined as an ellipse.

Method:
  1. grip envelope  -> max cornering speed (tyre + Z-mode downforce)
  2. backward pass  -> brake into each corner (grip + brake hardware + drag)
  3. forward pass   -> accelerate out (grip + drive force / power + drag)
  4. integrate dt = ds / v -> predicted lap time vs the real lap.
"""
import argparse
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def calculate_curvature(x, y, k=3):
    w = 2 * k + 1
    kernel = np.ones(w)/w
    xp = np.pad(x, k, mode="edge")
    yp = np.pad(y, k, mode="edge")
    x = np.convolve(xp, kernel, mode="valid")
    y = np.convolve(yp, kernel, mode="valid")
    dx = np.gradient(x)
    dy = np.gradient(y)
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)
    return np.abs(dx * ddy - dy * ddx) / np.power(dx ** 2 + dy ** 2, 1.5)


M = 768.0
MU = 1.4
RHO = 1.225
A = 1.5
CL_Z = 5.0
CD_Z = 1.0
CD_X = 0.6
G = 9.81
F_DRIVE = 12000.0
F_BRAKE = 38000.0
V_CAP = 92.0
P_ICE = 400_000.0
P_ERS = 350_000.0
ENERGY_ERS_PER_LAP = 4_000_000.0
ETA_ERS = 0.92
KAPPA_STRAIGHT = 0.003
MGUK_TAPER_START = 80.56
MGUK_TAPER_END = 98.61

GE_MAX = 2.0
V_REF = 40.0

P_DY1 = 1.8
P_DY2 = -0.17
P_DX1 = 1.9
P_DX2 = -0.17
FZ0 = 2000.0
MU_MIN = 0.3


def ground_effect_mult(v):
    return 1.0 + (GE_MAX - 1.0) * (v * v / (v * v + V_REF * V_REF))


def downforce_z(v):
    return 0.5 * RHO * CL_Z * A * v * v * ground_effect_mult(v)


def drag(v, straight):
    cd = CD_X if straight else CD_Z
    return 0.5 * RHO * cd * A * v * v


def mguk_taper(v):
    span = MGUK_TAPER_END - MGUK_TAPER_START
    return min(1.0, max(0.0, (MGUK_TAPER_END - v) / span))


def wheel_load(v):
    return (M * G + downforce_z(v)) / 4.0


def mu_peak(v, d1, d2):
    dfz = (wheel_load(v) - FZ0) / FZ0
    return np.maximum(d1 + d2 * dfz, MU_MIN)


def mu_lat(v, tire):
    return MU if tire == "flat" else mu_peak(v, P_DY1, P_DY2)


def mu_long(v, tire):
    return MU if tire == "flat" else mu_peak(v, P_DX1, P_DX2)


def grip_accel_lat(v, tire):
    return mu_lat(v, tire) * (M * G + downforce_z(v)) / M


def grip_accel_long(v, tire):
    return mu_long(v, tire) * (M * G + downforce_z(v)) / M


def corner_speed(kappa, tire):
    v = np.full_like(kappa, 25.0)
    for _ in range(40):
        v_new = np.sqrt(mu_lat(v, tire) * (M * G + downforce_z(v))
                        / (M * np.maximum(kappa, 1e-9)))
        v = 0.5 * v + 0.5 * np.minimum(v_new, V_CAP)
    return np.minimum(v, V_CAP)


def compute_metrics(tel, tire="pacejka"):
    x = tel["X"].values / 10.0
    y = tel["Y"].values / 10.0
    dist = tel["Distance"].values
    v_real = tel["Speed"].values / 3.6
    kappa = calculate_curvature(x, y)
    straight = np.abs(kappa) < KAPPA_STRAIGHT

    n = len(dist)
    ds = np.diff(dist)

    v_env = corner_speed(kappa, tire)

    v_back = v_env.copy()
    for i in range(n - 2, -1, -1):
        v = v_back[i + 1]
        a_lat = v * v * kappa[i + 1]
        ay_max = grip_accel_lat(v, tire)
        ax_max = grip_accel_long(v, tire)
        r = min(1.0, a_lat / max(ay_max, 1e-9))
        a_long = ax_max * np.sqrt(max(0.0, 1.0 - r * r))
        a_tire = min(a_long, F_BRAKE / M)
        a_brake = a_tire + drag(v, straight[i + 1]) / M
        v_allow = np.sqrt(v * v + 2.0 * a_brake * ds[i])
        v_back[i] = min(v_env[i], v_allow)

    def forward_pass(deploy_mask=None):
        """forward integrate; deploy_mask[i] adds tapered ERS power on segment i."""
        v = v_back.copy()
        for i in range(1, n):
            v_prev = v[i - 1]
            a_lat = v_prev * v_prev * kappa[i - 1]
            ay_max = grip_accel_lat(v_prev, tire)
            ax_max = grip_accel_long(v_prev, tire)
            r = min(1.0, a_lat / max(ay_max, 1e-9))
            a_long = ax_max * np.sqrt(max(0.0, 1.0 - r * r))
            p_ers = 0.0
            if deploy_mask is not None and deploy_mask[i - 1]:
                p_ers = P_ERS * ETA_ERS * mguk_taper(v_prev)
            a_drive = min(F_DRIVE, (P_ICE + p_ers) / max(v_prev, 1.0)) / M
            a_tire = min(a_long, a_drive)
            a_accel = max(0.0, a_tire - drag(v_prev, straight[i - 1]) / M)
            v_allow = np.sqrt(v_prev * v_prev + 2.0 * a_accel * ds[i - 1])
            v[i] = min(v_back[i], v_allow)
        return v

    v_no_ers = forward_pass(None)

    v_FL = P_ICE / F_DRIVE
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
            energy_i = P_ERS * mguk_taper(v_no_ers[i]) * dt_i
            if energy_i <= 1e-6:
                continue
            if energy_used + energy_i > ENERGY_ERS_PER_LAP:
                break
            deploy_mask[i] = True
            energy_used += energy_i
        if energy_used >= ENERGY_ERS_PER_LAP:
            break

    v_sim = forward_pass(deploy_mask)

    def lap_time(v):
        v_seg = 0.5 * (v[:-1] + v[1:])
        return float(np.sum(ds / np.maximum(v_seg, 1.0)))

    t_no_ers = lap_time(v_no_ers)
    t_sim = lap_time(v_sim)
    t_real = lap_time(v_real)
    err_ers = 100.0 * (t_sim - t_real) / t_real
    err_no = 100.0 * (t_no_ers - t_real) / t_real
    rmse = float(np.sqrt(np.mean((v_sim - v_real) ** 2)))

    return {
        "n": n,
        "t_no_ers": t_no_ers,
        "t_sim": t_sim,
        "t_real": t_real,
        "err_ers": err_ers,
        "err_no": err_no,
        "rmse": rmse,
        "top_sim": float(v_sim.max()),
        "top_real": float(v_real.max()),
        "ers_contribution": t_no_ers - t_sim,
        "energy_used": energy_used,
        "deployed_n": int(deploy_mask.sum()),
        "dist": dist,
        "v_env": v_env,
        "v_no_ers": v_no_ers,
        "v_sim": v_sim,
        "v_real": v_real,
        "v_back": v_back,
        "kappa": kappa,
        "straight": straight,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--telemetry", required=True)
    ap.add_argument("--output", default="data/sim_results/qss_laptime.png")
    ap.add_argument("--tire", choices=["pacejka", "flat"], default="pacejka")
    args = ap.parse_args()

    tel = pd.read_csv(args.telemetry)
    r = compute_metrics(tel, tire=args.tire)

    print(f"tire model: {args.tire}")
    if args.tire == "pacejka":
        for vv in (30.0, 50.0, 70.0, 90.0):
            print(f"  mu_y({vv:.0f} m/s) = {float(mu_lat(vv, 'pacejka')):.3f}  "
                  f"wheel load {wheel_load(vv)/1000:.1f} kN")
    print(f"ERS energy deployed: {r['energy_used']/1e6:.2f} / 4.00 MJ "
          f"({100*r['energy_used']/ENERGY_ERS_PER_LAP:.0f}%) over "
          f"{r['deployed_n']} of {r['n']} points")

    print("=== QSS Lap-Time Simulation vs Real ===")
    print(f"Top speed sim/real:   {r['top_sim']:.1f} / {r['top_real']:.1f} m/s")
    print(f"No-ERS lap time:      {r['t_no_ers']:7.3f} s   ({r['err_no']:+6.2f} % vs real)")
    print(f"Greedy-ERS lap time:  {r['t_sim']:7.3f} s   ({r['err_ers']:+6.2f} % vs real)")
    print(f"Greedy ERS gain:      {r['ers_contribution']:.3f} s   (optimal schedule: scripts/ers_dp.py)")
    print(f"Real lap time:        {r['t_real']:7.3f} s")
    print(f"Speed-trace RMSE:     {r['rmse']:6.2f} m/s ({r['rmse'] * 3.6:.1f} km/h)")

    dist = r["dist"]
    plt.figure(figsize=(14, 6))
    plt.plot(dist, r["v_env"], color="lightcoral", alpha=0.4, label="Grip envelope")
    plt.plot(dist, r["v_no_ers"], color="orange", linewidth=1.5, linestyle="--",
             label=f"QSS ICE only ({r['t_no_ers']:.2f} s)")
    plt.plot(dist, r["v_sim"], color="red", linewidth=2.0,
             label=f"QSS + ERS greedy ({r['t_sim']:.2f} s)")
    plt.plot(dist, r["v_real"], color="black", alpha=0.6, linewidth=2.0,
             label=f"Real ({r['t_real']:.2f} s)")
    plt.xlabel("Distance [m]")
    plt.ylabel("Velocity [m/s]")
    plt.title(f"QSS Lap-Time Simulation vs Real Telemetry ({args.tire} tire model)")
    plt.grid(True, linestyle=":", alpha=0.5)
    plt.legend()
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    plt.savefig(args.output, dpi=150)
    print(f"Plot saved to {args.output}")


if __name__ == "__main__":
    main()
