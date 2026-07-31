"""Plot the optimized per-position grip margin m(s) over the track curvature,
so the learned limit of every corner is visible at a glance.

run:
  python scripts/plot_margins.py
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


MARGIN_CSV = "data/sim_results/margin_schedule.csv"
TRACK_CSV = "data/tracks/suzuka/raceline_ver.csv"
OUTPUT = "data/sim_results/margin_schedule.png"


def curvature(x, y):
    dx = np.gradient(x)
    dy = np.gradient(y)
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)
    return np.abs(dx * ddy - dy * ddx) / np.power(dx ** 2 + dy ** 2, 1.5)


def main():
    m = pd.read_csv(MARGIN_CSV)
    trk = pd.read_csv(TRACK_CSV)
    kappa = curvature(trk["x"].values, trk["y"].values)
    s_trk = trk["s_arc"].values

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 7), sharex=True,
                                   facecolor="#0d1117",
                                   gridspec_kw={"height_ratios": [2, 1]})
    for ax in (ax1, ax2):
        ax.set_facecolor("#0d1117")
        for sp in ax.spines.values():
            sp.set_color("#30363d")
        ax.tick_params(colors="white", labelsize=9)
        ax.grid(True, linestyle=":", alpha=0.25, color="white")

    ax1.step(m["s_m"], m["margin"], where="mid", color="#33cc66", lw=1.6,
             label="optimized margin m(s)")
    ax1.axhline(0.88, color="#ff8866", lw=1.2, ls="--", label="previous global 0.88")
    ax1.set_ylabel("grip margin", color="white", fontsize=11)
    ax1.set_ylim(0.78, 1.0)
    ax1.legend(loc="lower left", facecolor="#161b22", edgecolor="#30363d",
               labelcolor="white", fontsize=10)
    ax1.set_title("Learned per-corner grip margin vs track curvature",
                  color="white", fontsize=13, loc="left", pad=10)

    ax2.fill_between(s_trk, 0, kappa, color="#4dc4ff", alpha=0.6, lw=0)
    ax2.set_ylabel("curvature [1/m]", color="white", fontsize=11)
    ax2.set_xlabel("distance along lap [m]", color="white", fontsize=11)

    plt.tight_layout()
    plt.savefig(OUTPUT, dpi=150, facecolor=fig.get_facecolor())
    print(f"saved {OUTPUT}")


if __name__ == "__main__":
    main()
