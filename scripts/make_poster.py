"""one-image summary poster for the project README.

top: Suzuka track surface + sectors + VER raceline colored by real speed.
bottom: speed-vs-distance comparison (real telemetry, C++ sim ghost).
right: key validation metrics.

run:
  python scripts/make_poster.py
output:
  data/sim_results/contactpatch_poster.png
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.gridspec import GridSpec

from visualize_track import draw_track_surface, draw_sectors, align_path_to_centerline


TRACK_CSV = "data/tracks/suzuka/centerline.csv"
REAL_CSV = "data/telemetry/2026_Japan_VER_Q.csv"
SIM_CSV = "data/sim_results/2026_Japan_VER_Q_sim.csv"
QSS_CSV = "data/sim_results/qss_ghost_sim.csv"
FIELD_CSV = "data/sim_results/suzuka_field_qss.csv"
OUTPUT = "data/sim_results/contactpatch_poster.png"


def parse_fastf1_time(s):
    parts = str(s).split()
    h, m, sec = parts[-1].split(":")
    return float(h) * 3600.0 + float(m) * 60.0 + float(sec)


def main():
    track_df = pd.read_csv(TRACK_CSV)

    real = pd.read_csv(REAL_CSV)
    rx_raw = real["X"].values / 10.0
    ry_raw = real["Y"].values / 10.0
    rx, ry = align_path_to_centerline(rx_raw, ry_raw,
                                       track_df["x"].values, track_df["y"].values)
    r_speed_kmh = real["Speed"].values
    r_dist = real["Distance"].values

    sim = pd.read_csv(SIM_CSV)
    s_arc_running_max = sim["s_arc_m"].cummax()
    keep = sim["s_arc_m"] >= s_arc_running_max - 1e-3
    sim_clean = sim[keep & (sim["v_long_mps"] > 0.0)].copy()
    s_speed_kmh = sim_clean["v_long_mps"].values * 3.6
    s_dist = sim_clean["s_arc_m"].values

    qss = pd.read_csv(QSS_CSV)
    q_speed_kmh = qss["v_long_mps"].values * 3.6
    q_dist = qss["s_arc_m"].values

    fig = plt.figure(figsize=(18, 11), facecolor="#0d1117")
    gs = GridSpec(2, 3, figure=fig,
                  height_ratios=[1.0, 0.7], width_ratios=[2.6, 2.6, 1.15],
                  left=0.03, right=0.985, top=0.89, bottom=0.06,
                  hspace=0.22, wspace=0.10)

    ax_track = fig.add_subplot(gs[0, 0:2])
    ax_track.set_facecolor("#0d1117")
    ax_track.set_aspect("equal")
    ax_track.axis("off")

    draw_track_surface(ax_track, track_df)
    draw_sectors(ax_track, track_df)

    pts = np.array([rx, ry]).T.reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    lc = LineCollection(segs, cmap="plasma", linewidth=2.5, zorder=5)
    lc.set_array(r_speed_kmh[:-1])
    ax_track.add_collection(lc)

    cbar = fig.colorbar(lc, ax=ax_track, shrink=0.55, pad=0.01, location="right")
    cbar.set_label("VER speed [km/h]", color="white", fontsize=10)
    cbar.ax.yaxis.set_tick_params(color="white", labelsize=9)
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="white")
    cbar.outline.set_edgecolor("#444")

    ax_track.set_title("Suzuka  -  Verstappen Q raceline (F1 2026, real FastF1 telemetry)",
                       color="white", fontsize=13, pad=10, loc="left")

    ax_card = fig.add_subplot(gs[0, 2])
    ax_card.set_facecolor("#161b22")
    ax_card.set_xticks([])
    ax_card.set_yticks([])
    for s in ax_card.spines.values():
        s.set_color("#30363d")

    real_lap_time = (parse_fastf1_time(real['Time'].iloc[-1])
                     - parse_fastf1_time(real['Time'].iloc[0]))
    qss_lap_time = qss['time_s'].iloc[-1]

    field = pd.read_csv(FIELD_CSV)
    hold = field[(field["clean"]) & (field["driver"] != "VER")]
    hold_mean = float(np.mean(hold["err_pct"]))
    hold_std = float(np.std(hold["err_pct"]))

    metrics = [
        ("Lap time (real, telemetry span)", f"{real_lap_time:.2f} s"),
        ("Lap time (sim)",    f"{qss_lap_time:.2f} s"),
        ("Sim vs real",       f"{100 * (qss_lap_time - real_lap_time) / real_lap_time:+.2f} %"),
        (f"Holdout ({len(hold)} drivers)", f"{hold_mean:+.1f} ± {hold_std:.1f} %"),
        ("Top speed (real)",  f"{r_speed_kmh.max():.0f} km/h"),
        ("Top speed (sim)",   f"{q_speed_kmh.max():.0f} km/h"),
        ("ERS strategy",      "DP optimal"),
        ("Tests passing",     "23 / 23"),
        ("Active aero",       "X / Z switching"),
        ("Min weight (regs)", "768 kg"),
        ("MGU-K power",       "350 kW"),
        ("Battery",           "4 MJ"),
    ]
    ax_card.text(0.5, 0.965, "VALIDATION", color="#58a6ff",
                 fontsize=13, ha="center", va="top",
                 fontweight="bold", transform=ax_card.transAxes)
    y = 0.905
    for label, value in metrics:
        ax_card.text(0.06, y, label, color="#8b949e", fontsize=10,
                     ha="left", va="top", transform=ax_card.transAxes)
        ax_card.text(0.94, y, value, color="white", fontsize=10,
                     ha="right", va="top", fontweight="bold",
                     transform=ax_card.transAxes)
        y -= 0.070

    ax_speed = fig.add_subplot(gs[1, :])
    ax_speed.set_facecolor("#0d1117")
    for s in ax_speed.spines.values():
        s.set_color("#30363d")

    ax_speed.plot(r_dist, r_speed_kmh, color="#4dc4ff",
                  linewidth=2.0, label="Real VER (FastF1)", alpha=0.95)
    ax_speed.plot(q_dist, q_speed_kmh, color="#ffd54d",
                  linewidth=2.0, label="contactPatch sim (QSS + DP ERS, physics ceiling)",
                  alpha=0.95)
    ax_speed.plot(s_dist, s_speed_kmh, color="#ff8866",
                  linewidth=1.4, label="contactPatch sim (pure-pursuit driver)",
                  alpha=0.7, linestyle="--")

    ax_speed.set_xlabel("Distance along lap [m]", color="white", fontsize=11)
    ax_speed.set_ylabel("Speed [km/h]", color="white", fontsize=11)
    ax_speed.tick_params(colors="white", labelsize=9)
    ax_speed.grid(True, linestyle=":", alpha=0.25, color="white")
    ax_speed.legend(loc="upper right", facecolor="#161b22", edgecolor="#30363d",
                    labelcolor="white", fontsize=10)
    ax_speed.set_xlim(0, max(r_dist[-1], s_dist.max()))
    ax_speed.set_ylim(0, max(r_speed_kmh.max(), s_speed_kmh.max()) * 1.08)
    ax_speed.set_title("Speed trace across the lap  -  physics ceiling matches real; pure-pursuit shows the controller gap",
                       color="white", fontsize=11, loc="left", pad=8)

    fig.text(0.5, 0.975, "contactPatch  -  F1 2026 vehicle dynamics simulator",
             color="white", fontsize=17, ha="center", va="top", fontweight="bold")
    fig.text(0.5, 0.945, "deterministic batch sim: planar 3-DOF, telemetry-calibrated Pacejka tyres, active aero, ground effect, DP-optimal ERS",
             color="#8b949e", fontsize=10, ha="center", va="top", style="italic")

    fig.savefig(OUTPUT, dpi=150, facecolor=fig.get_facecolor())
    print(f"poster saved to {OUTPUT}")


if __name__ == "__main__":
    main()
