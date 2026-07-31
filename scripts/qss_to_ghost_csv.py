"""Export the calibrated QSS prediction as a sim-style CSV so it can be played
back through the ghost animation. The output schema matches the C++
telemetry_runner CSV, so visualize_ghost.py treats it as another sim run.

This is the physics-honest ghost: the load-sensitive tire model fitted against
real telemetry, driven at the limit on the driver's own line, with the ERS
battery managed by the dynamic-programming optimizer, deploying on exits and
straights and recharging under braking.

run:
  python scripts/qss_to_ghost_csv.py \
      --telemetry data/telemetry/2026_Japan_VER_Q.csv \
      --output data/sim_results/qss_ghost_sim.csv
"""
import argparse
import pandas as pd
import numpy as np

import qss_laptime as q
from ers_dp import dp_optimize
from visualize_track import align_path_to_centerline


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--telemetry", required=True)
    ap.add_argument("--track", default="data/tracks/suzuka/centerline.csv")
    ap.add_argument("--output", default="data/sim_results/qss_ghost_sim.csv")
    ap.add_argument("--tire", choices=["pacejka", "flat"], default="pacejka")
    args = ap.parse_args()

    tel = pd.read_csv(args.telemetry)
    m = q.compute_metrics(tel, tire=args.tire)
    r = dp_optimize(m, tire=args.tire)

    track_df = pd.read_csv(args.track)
    x_aligned, y_aligned = align_path_to_centerline(
        tel["X"].values / 10.0,
        tel["Y"].values / 10.0,
        track_df["x"].values,
        track_df["y"].values,
    )

    dist = m["dist"]
    v_sim = r["v_traj"]
    n = len(dist)
    ds = np.diff(dist)

    t = np.zeros(n)
    for i in range(1, n):
        v_avg = 0.5 * (v_sim[i - 1] + v_sim[i])
        t[i] = t[i - 1] + ds[i - 1] / max(v_avg, 1.0)

    battery_soc = np.clip(r["e_traj"] / q.ENERGY_ERS_PER_LAP, 0.0, 1.0)

    tire_temp = np.full(n, 95.0)
    fz_total = 4.0 * q.wheel_load(v_sim)
    fz_front = 0.455 * fz_total / 2.0
    fz_rear = 0.545 * fz_total / 2.0

    yaw = np.arctan2(np.gradient(y_aligned), np.gradient(x_aligned))

    out = pd.DataFrame({
        "time_s": t,
        "s_arc_m": dist,
        "v_long_mps": v_sim,
        "x_m": x_aligned,
        "y_m": y_aligned,
        "yaw_rad": yaw,
        "tire_temp_fl": tire_temp,
        "tire_temp_fr": tire_temp,
        "tire_temp_rl": tire_temp,
        "tire_temp_rr": tire_temp,
        "battery_soc": battery_soc,
        "fz_fl": fz_front,
        "fz_fr": fz_front,
        "fz_rl": fz_rear,
        "fz_rr": fz_rear,
        "aero_x": m["straight"].astype(int),
        "ers_deploy": r["deploy_mask"].astype(int),
    })
    out.to_csv(args.output, index=False)
    print(f"QSS ghost CSV written: {args.output}")
    print(f"rows: {n}")
    print(f"lap time (DP ERS): {t[-1]:.2f} s   real: {m['t_real']:.2f} s   "
          f"({100.0 * (t[-1] - m['t_real']) / m['t_real']:+.2f} % vs real)")
    print(f"ERS deployed: {r['e_used'] / 1e6:.2f} MJ over {r['deploy_n']} points, "
          f"{r['e_recovered'] / 1e6:.2f} MJ recovered under braking")
    print(f"top speed: {v_sim.max():.1f} m/s = {v_sim.max() * 3.6:.1f} km/h")


if __name__ == "__main__":
    main()
