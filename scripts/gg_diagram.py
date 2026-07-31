"""g-g diagram: measured accelerations from a real telemetry lap plotted
against the model's acceleration envelope (load-sensitive Pacejka peaks,
downforce, drag, and the 2026 power unit on the drive side).

The measured points come straight from the telemetry: longitudinal from
differentiating the speed trace, lateral from v^2 * curvature of the GPS
line. The envelope is what the model says the car could do at that speed.

usage:
  python scripts/gg_diagram.py --telemetry data/telemetry/2026_Japan_VER_Q.csv
"""
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import qss_laptime as q

P_TOT = q.P_ICE + q.P_ERS * q.ETA_ERS


def smooth(a, k=7):
    kernel = np.ones(k) / k
    return np.convolve(np.pad(a, k // 2, mode="edge"), kernel, mode="valid")


def signed_curvature(x, y, k=3):
    w = 2 * k + 1
    kernel = np.ones(w) / w
    xs = np.convolve(np.pad(x, k, mode="edge"), kernel, mode="valid")
    ys = np.convolve(np.pad(y, k, mode="edge"), kernel, mode="valid")
    dx = np.gradient(xs)
    dy = np.gradient(ys)
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)
    return (dx * ddy - dy * ddx) / np.power(dx ** 2 + dy ** 2, 1.5)


def accel_caps(v, straight, tire):
    ay = q.grip_accel_lat(v, tire)
    d = q.drag(v, straight) / q.M
    ax_pos = min(q.F_DRIVE, P_TOT / max(v, 1.0)) / q.M - d
    ax_neg = q.grip_accel_long(v, tire) + d
    return ay, max(ax_pos, 1e-3), ax_neg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--telemetry", required=True)
    ap.add_argument("--output", default="data/sim_results/gg_diagram.png")
    ap.add_argument("--tire", choices=["pacejka", "flat"], default="pacejka")
    args = ap.parse_args()

    tel = pd.read_csv(args.telemetry)
    t_raw = pd.to_timedelta(tel["Time"]).dt.total_seconds().values
    t_raw, idx = np.unique(t_raw, return_index=True)
    v_raw = tel["Speed"].values[idx] / 3.6
    x_raw = tel["X"].values[idx] / 10.0
    y_raw = tel["Y"].values[idx] / 10.0

    dt = 0.1
    t = np.arange(t_raw[0], t_raw[-1], dt)
    v = smooth(np.interp(t, t_raw, v_raw), 5)
    x = np.interp(t, t_raw, x_raw)
    y = np.interp(t, t_raw, y_raw)

    kappa = signed_curvature(x, y, k=5)
    a_lat = smooth(v * v * kappa, 5)
    a_long = smooth(np.gradient(v, dt), 5)

    keep = v > 12.0
    keep[:5] = False
    keep[-5:] = False
    v, a_lat, a_long, kappa = v[keep], a_lat[keep], a_long[keep], kappa[keep]
    straight = np.abs(kappa) < q.KAPPA_STRAIGHT

    g = 9.81
    n = len(v)
    outside = 0
    outside_hard = 0
    for i in range(n):
        ay_max, ax_pos, ax_neg = accel_caps(v[i], bool(straight[i]), args.tire)
        ax_max = ax_pos if a_long[i] >= 0.0 else ax_neg
        e = (a_lat[i] / ay_max) ** 2 + (a_long[i] / ax_max) ** 2
        if e > 1.0:
            outside += 1
        if e > 1.21:
            outside_hard += 1

    i_lat = int(np.argmax(np.abs(a_lat)))
    i_brk = int(np.argmin(a_long))
    ay_at_peak, _, _ = accel_caps(v[i_lat], False, args.tire)
    _, _, axn_at_peak = accel_caps(v[i_brk], bool(straight[i_brk]), args.tire)

    print(f"tire model: {args.tire}")
    print(f"samples kept: {n}")
    print(f"peak |lateral|: {abs(a_lat[i_lat])/g:.2f} g at {v[i_lat]*3.6:.0f} km/h "
          f"(model cap there: {ay_at_peak/g:.2f} g)")
    print(f"peak braking:   {-a_long[i_brk]/g:.2f} g at {v[i_brk]*3.6:.0f} km/h "
          f"(model cap there: {axn_at_peak/g:.2f} g)")
    print(f"peak accel:     {a_long.max()/g:.2f} g")
    print(f"outside envelope: {100.0*outside/n:.1f} %  (beyond 10% margin: {100.0*outside_hard/n:.1f} %)")

    fig, ax = plt.subplots(figsize=(9, 9))
    sc = ax.scatter(a_lat / g, a_long / g, c=v * 3.6, s=6, cmap="viridis", alpha=0.7)
    fig.colorbar(sc, ax=ax, label="speed [km/h]")

    phi = np.linspace(0.0, np.pi / 2.0, 60)
    for vv_kmh, col in [(150, "#d62728"), (250, "#9467bd"), (320, "#8c564b")]:
        vv = vv_kmh / 3.6
        ay_max, ax_pos, ax_neg = accel_caps(vv, False, args.tire)
        for sx in (1.0, -1.0):
            ax.plot(sx * ay_max * np.cos(phi) / g, ax_pos * np.sin(phi) / g,
                    color=col, linewidth=1.4)
            ax.plot(sx * ay_max * np.cos(phi) / g, -ax_neg * np.sin(phi) / g,
                    color=col, linewidth=1.4,
                    label=f"{vv_kmh} km/h envelope" if sx > 0 else None)

    ax.axhline(0, color="gray", linewidth=0.6)
    ax.axvline(0, color="gray", linewidth=0.6)
    ax.set_xlabel("lateral acceleration [g]")
    ax.set_ylabel("longitudinal acceleration [g]")
    ax.set_title(f"g-g diagram: real lap vs model envelope ({args.tire} tires)")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.3, linestyle=":")
    plt.tight_layout()
    plt.savefig(args.output, dpi=150)
    print(f"saved {args.output}")


if __name__ == "__main__":
    main()
