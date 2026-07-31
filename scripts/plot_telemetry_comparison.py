"""Side-by-side lap telemetry: speed, per-driver pedal traces, gear, the
closed-loop aero mode and ERS deploy strip, and the cumulative time delta vs
Verstappen. One image to read where time is won and lost.

run:
  python scripts/plot_telemetry_comparison.py
output:
  data/sim_results/telemetry_comparison.png
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

VER = "data/telemetry/2026_Japan_VER_Q.csv"
ANT = "data/telemetry/field/2026_Japan_ANT_Q.csv"
QSS = "data/sim_results/qss_ghost_sim.csv"
SIM = "data/sim_results/2026_Japan_VER_Q_sim.csv"
OUT = "data/sim_results/telemetry_comparison.png"


def main():
    ver = pd.read_csv(VER)
    ant = pd.read_csv(ANT)
    qss = pd.read_csv(QSS)
    sim = pd.read_csv(SIM)

    dv = ver["Distance"].values - ver["Distance"].values[0]
    vv = ver["Speed"].values / 3.6
    thr_v = ver["Throttle"].values
    brk_v = ver["Brake"].astype(bool).astype(float).values * 100.0
    gear_v = ver["nGear"].values
    D = float(dv[-1])

    da = ant["Distance"].values - ant["Distance"].values[0]
    da = da / da[-1] * D
    va = ant["Speed"].values / 3.6
    thr_a = ant["Throttle"].values
    brk_a = ant["Brake"].astype(bool).astype(float).values * 100.0

    dq = qss["s_arc_m"].values - qss["s_arc_m"].values[0]
    vq = qss["v_long_mps"].values

    sm = sim[sim["v_long_mps"] > 0]
    ds_ = sm["s_arc_m"].values
    o = np.argsort(ds_)
    ds_ = ds_[o]
    vs_ = sm["v_long_mps"].values[o]
    thr_s = sm["throttle"].values[o] * 100.0
    brk_s = sm["brake"].values[o] * 100.0
    gear_s = sm["gear"].values[o]
    aero_s = sm["aero_x"].values[o] if "aero_x" in sm else np.zeros(len(ds_))
    dep_s = sm["ers_deploy"].values[o] if "ers_deploy" in sm else np.zeros(len(ds_))
    ds_ = ds_ / ds_[-1] * D
    t_lap = float(sim["time_s"].iloc[-1])

    grid = np.arange(0.0, D - 10.0, 5.0)

    def t_of(d, v):
        vi = np.maximum(np.interp(grid, d, v), 1.0)
        return np.concatenate([[0.0], np.cumsum(5.0 / vi[:-1])])

    tv = t_of(dv, vv)
    ta = t_of(da, va)
    tq = t_of(dq, vq)
    ts = t_of(ds_, vs_)
    vqg = np.interp(grid, dq, vq)
    corner = vqg < 70.0

    fig, axes = plt.subplots(7, 1, figsize=(17, 17), sharex=True,
                             facecolor="#0d1117",
                             gridspec_kw={"height_ratios":
                                          [2.0, 0.7, 0.7, 0.7, 0.7, 0.55, 1.2]})
    ax1, axv, axa, axp, axg, axx, ax2 = axes
    for ax in axes:
        ax.set_facecolor("#0d1117")
        for s in ax.spines.values():
            s.set_color("#30363d")
        ax.tick_params(colors="white", labelsize=9)
        ax.grid(True, linestyle=":", alpha=0.22, color="white")
        on = False
        a0 = 0.0
        for i in range(len(grid)):
            if corner[i] and not on:
                a0 = grid[i]
                on = True
            if on and (not corner[i] or i == len(grid) - 1):
                ax.axvspan(a0, grid[i], color="white", alpha=0.05)
                on = False

    ax1.plot(dv, vv * 3.6, color="#4dc4ff", lw=1.8, label="VER real (90.27 s)")
    ax1.plot(da, va * 3.6, color="#b0b8c0", lw=1.3, alpha=0.85,
             label="ANT real (88.60 s, GPS rescaled)")
    ax1.plot(grid, vqg * 3.6, color="#ffd54d", lw=1.8, label="QSS + DP ERS (ceiling)")
    ax1.plot(ds_, vs_ * 3.6, color="#ff8866", lw=1.6, ls="--",
             label=f"pure pursuit ({t_lap:.2f} s)")
    ax1.set_ylabel("Speed [km/h]", color="white", fontsize=11)
    ax1.legend(loc="lower left", facecolor="#161b22", edgecolor="#30363d",
               labelcolor="white", fontsize=9, ncol=2)
    ax1.set_title("Suzuka Q 2026: speed, inputs, gear, aero/ERS, and delta vs VER",
                  color="white", fontsize=13, loc="left", pad=10)

    def pedals(ax, d, thr, brk, who, color):
        ax.fill_between(d, 0, thr, color="#33cc66", alpha=0.75, lw=0)
        ax.fill_between(d, 0, -brk, color="#ff3344", alpha=0.75, lw=0)
        ax.set_ylim(-105, 105)
        ax.set_yticks([-100, 0, 100])
        ax.set_yticklabels(["BRK", "0", "THR"])
        ax.text(0.004, 0.82, who, color=color, fontsize=10, fontweight="bold",
                transform=ax.transAxes)

    pedals(axv, dv, thr_v, brk_v, "VER real", "#4dc4ff")
    pedals(axa, da, thr_a, brk_a, "ANT real (GPS rescaled)", "#b0b8c0")
    pedals(axp, ds_, thr_s, brk_s, "PURE PURSUIT sim", "#ff8866")

    axg.step(dv, gear_v, where="post", color="#4dc4ff", lw=1.4, label="VER real")
    axg.step(ds_, gear_s, where="post", color="#ff8866", lw=1.4, ls="--",
             label="pure pursuit")
    axg.set_ylim(0.5, 8.5)
    axg.set_yticks([2, 4, 6, 8])
    axg.set_ylabel("Gear", color="white", fontsize=10)
    axg.legend(loc="lower left", facecolor="#161b22", edgecolor="#30363d",
               labelcolor="white", fontsize=9, ncol=2)

    axx.fill_between(ds_, 1.0, 2.0, where=aero_s > 0.5, color="#4dc4ff",
                     alpha=0.7, step="mid")
    axx.fill_between(ds_, 0.0, 1.0, where=dep_s > 0.5, color="#33ff66",
                     alpha=0.7, step="mid")
    axx.set_ylim(0, 2)
    axx.set_yticks([0.5, 1.5])
    axx.set_yticklabels(["ERS", "X-mode"])
    axx.text(0.004, 0.80, "PURE PURSUIT aero mode (X) and ERS deploy",
             color="#ffaa33", fontsize=9, fontweight="bold", transform=axx.transAxes)

    ax2.plot(grid, ta - tv, color="#b0b8c0", lw=1.3, label="ANT - VER")
    ax2.plot(grid, tq - tv, color="#ffd54d", lw=1.8, label="QSS - VER")
    ax2.plot(grid, ts - tv, color="#ff8866", lw=1.8, ls="--", label="pure pursuit - VER")
    ax2.axhline(0, color="#4dc4ff", lw=1.0, alpha=0.7)
    ax2.set_xlabel("Distance along lap [m]", color="white", fontsize=11)
    ax2.set_ylabel("Delta vs VER [s]", color="white", fontsize=11)
    ax2.legend(loc="upper left", facecolor="#161b22", edgecolor="#30363d",
               labelcolor="white", fontsize=9)

    plt.tight_layout()
    plt.savefig(OUT, dpi=150, facecolor=fig.get_facecolor())
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
