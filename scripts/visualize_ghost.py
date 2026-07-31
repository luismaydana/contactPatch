"""ghost-car animation (real vs sim) with sim-exclusive hud.

real lap = FastF1 telemetry (reference).
sim lap  = contactPatch sim run (CSV emitted by the C++ runner or QSS).

both run from t=0 simultaneously. real is sampled from FastF1, sim is sampled
from the runner CSV. the bottom-right HUD panels show channels only the sim
produces: tire temperatures per corner, battery SOC, and vertical loads (Fz)
per axle.

usage:
  python scripts/visualize_ghost.py \
    --track data/tracks/suzuka/centerline.csv \
    --real data/telemetry/2026_Japan_VER_Q.csv \
    --sim data/sim_results/2026_Japan_VER_Q_sim.csv \
    --output data/sim_results/ghost_animation.mp4
"""
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.collections import LineCollection
from matplotlib.patches import Rectangle

from visualize_track import draw_track_surface, draw_sectors, align_path_to_centerline

try:
    import imageio_ffmpeg
    plt.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    pass


def parse_fastf1_time(s):
    parts = str(s).split()
    hms = parts[-1]
    h, m, sec = hms.split(":")
    return float(h) * 3600.0 + float(m) * 60.0 + float(sec)


def resample(t, arrays, t_grid):
    return [np.interp(t_grid, t, a) for a in arrays]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", required=True)
    ap.add_argument("--real", required=True)
    ap.add_argument("--sim", required=True)
    ap.add_argument("--sim2")
    ap.add_argument("--sim2-label", default="SIM 2")
    ap.add_argument("--output", default="data/sim_results/ghost_animation.mp4")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--gif", action="store_true")
    args = ap.parse_args()

    track_df = pd.read_csv(args.track)

    rt = pd.read_csv(args.real)
    rx_raw = rt["X"].values / 10.0
    ry_raw = rt["Y"].values / 10.0
    r_speed = rt["Speed"].values
    r_thr = rt["Throttle"].values
    r_brk = rt["Brake"].astype(bool).astype(float).values * 100.0
    r_gear = rt["nGear"].values
    r_dist = rt["Distance"].values
    r_t = np.array([parse_fastf1_time(s) for s in rt["Time"].values])
    r_t = r_t - r_t[0]

    rx, ry = align_path_to_centerline(rx_raw, ry_raw, track_df["x"].values, track_df["y"].values)

    st = pd.read_csv(args.sim)
    s_t = st["time_s"].values
    s_x = st["x_m"].values
    s_y = st["y_m"].values
    s_speed = st["v_long_mps"].values * 3.6
    s_temps = [st[f"tire_temp_{w}"].values for w in ("fl", "fr", "rl", "rr")]
    temps_assumed = all(float(np.ptp(T)) < 1e-6 for T in s_temps)
    s_soc = st["battery_soc"].values
    s_fz_front = st["fz_fl"].values + st["fz_fr"].values
    s_fz_rear = st["fz_rl"].values + st["fz_rr"].values
    s_aero_x = st["aero_x"].values if "aero_x" in st else np.zeros(len(st))
    s_deploy = st["ers_deploy"].values if "ers_deploy" in st else np.zeros(len(st))

    t_end = min(r_t[-1], s_t[-1])
    n = max(2, int(round(t_end * args.fps)))
    t_grid = np.linspace(0.0, t_end, n)

    rx_f, ry_f, r_speed_f, r_thr_f, r_brk_f, r_gear_f, r_dist_f = resample(
        r_t, [rx, ry, r_speed, r_thr, r_brk, r_gear, r_dist], t_grid)
    r_gear_f = np.round(r_gear_f).astype(int)

    sx_f, sy_f, s_speed_f, s_soc_f, s_fzf_f, s_fzr_f = resample(
        s_t, [s_x, s_y, s_speed, s_soc, s_fz_front, s_fz_rear], t_grid)
    s_temp_f = [np.interp(t_grid, s_t, T) for T in s_temps]
    s_aero_f = np.interp(t_grid, s_t, s_aero_x)
    s_deploy_f = np.interp(t_grid, s_t, s_deploy)

    r_head = np.arctan2(np.gradient(ry_f), np.gradient(rx_f))
    s_head = np.arctan2(np.gradient(sy_f), np.gradient(sx_f))

    has2 = args.sim2 is not None
    if has2:
        st2 = pd.read_csv(args.sim2)
        s2x_raw, s2y_raw = align_path_to_centerline(
            st2["x_m"].values, st2["y_m"].values,
            track_df["x"].values, track_df["y"].values)
        s2x = np.interp(t_grid, st2["time_s"].values, s2x_raw)
        s2y = np.interp(t_grid, st2["time_s"].values, s2y_raw)
        s2_head = np.arctan2(np.gradient(s2y), np.gradient(s2x))

    fig = plt.figure(figsize=(17, 9), facecolor="#101418")

    ax_track = fig.add_axes([0.02, 0.05, 0.60, 0.9])
    ax_track.set_facecolor("#101418")
    ax_track.axis("off")
    ax_track.set_aspect("equal")
    draw_track_surface(ax_track, track_df)
    draw_sectors(ax_track, track_df)

    pts = np.array([rx, ry]).T.reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    lc = LineCollection(segs, cmap="plasma", linewidth=1.2, zorder=4, alpha=0.30)
    lc.set_array(r_speed[:-1])
    ax_track.add_collection(lc)

    (real_dot,) = ax_track.plot([], [], marker=(3, 0, 0), color="#4dc4ff",
                                markersize=16, markeredgecolor="black",
                                markeredgewidth=1.0, zorder=10)
    (sim_dot,) = ax_track.plot([], [], marker=(3, 0, 0), color="#ffaa33",
                               markersize=16, markeredgecolor="black",
                               markeredgewidth=1.0, zorder=10)
    if has2:
        (sim2_dot,) = ax_track.plot([], [], marker=(3, 0, 0), color="#ff5555",
                                    markersize=16, markeredgecolor="black",
                                    markeredgewidth=1.0, zorder=10)
        fig.text(0.215, 0.96, args.sim2_label, color="#ff5555",
                 fontsize=11, fontweight="bold")

    fig.text(0.025, 0.96, "REAL (VER)", color="#4dc4ff", fontsize=11, fontweight="bold")
    fig.text(0.110, 0.96, "SIM (contactPatch)", color="#ffaa33", fontsize=11, fontweight="bold")
    fig.text(0.46, 0.965, "Suzuka - Ghost: real vs sim",
             color="white", fontsize=14, ha="center", va="center")

    def panel(rect, accent=None):
        a = fig.add_axes(rect)
        a.set_facecolor("#1a1f25")
        a.set_xticks([])
        a.set_yticks([])
        for s in a.spines.values():
            s.set_color(accent if accent else "#3a4048")
        return a

    ax_r_speed = panel([0.65, 0.74, 0.16, 0.20], accent="#4dc4ff")
    ax_r_speed.text(0.5, 0.85, "REAL SPEED", color="#4dc4ff", fontsize=10,
                    ha="center", va="center", transform=ax_r_speed.transAxes)
    r_speed_text = ax_r_speed.text(0.5, 0.42, "0", color="white", fontsize=38,
                                   ha="center", va="center", fontweight="bold",
                                   transform=ax_r_speed.transAxes)
    ax_r_speed.text(0.5, 0.13, "km/h", color="#8a9098", fontsize=10,
                    ha="center", va="center", transform=ax_r_speed.transAxes)

    ax_r_bars = panel([0.65, 0.59, 0.16, 0.13])
    ax_r_bars.text(0.02, 0.78, "THR", color="#8a9098", fontsize=9,
                   ha="left", va="center", transform=ax_r_bars.transAxes)
    r_thr_bar = Rectangle((0.20, 0.60), 0.0, 0.25, color="#33cc66",
                          transform=ax_r_bars.transAxes)
    ax_r_bars.add_patch(r_thr_bar)
    ax_r_bars.text(0.02, 0.28, "BRK", color="#8a9098", fontsize=9,
                   ha="left", va="center", transform=ax_r_bars.transAxes)
    r_brk_bar = Rectangle((0.20, 0.10), 0.0, 0.25, color="#ff3344",
                          transform=ax_r_bars.transAxes)
    ax_r_bars.add_patch(r_brk_bar)

    ax_r_gear = panel([0.83, 0.74, 0.07, 0.20], accent="#4dc4ff")
    ax_r_gear.text(0.5, 0.82, "GEAR", color="#8a9098", fontsize=9,
                   ha="center", va="center", transform=ax_r_gear.transAxes)
    r_gear_text = ax_r_gear.text(0.5, 0.42, "N", color="#ffcc33", fontsize=34,
                                 ha="center", va="center", fontweight="bold",
                                 transform=ax_r_gear.transAxes)

    ax_r_time = panel([0.91, 0.74, 0.07, 0.20], accent="#4dc4ff")
    ax_r_time.text(0.5, 0.82, "TIME", color="#8a9098", fontsize=9,
                   ha="center", va="center", transform=ax_r_time.transAxes)
    r_time_text = ax_r_time.text(0.5, 0.42, "0.0", color="white", fontsize=18,
                                 ha="center", va="center", fontweight="bold",
                                 transform=ax_r_time.transAxes)

    ax_s_speed = panel([0.65, 0.36, 0.16, 0.20], accent="#ffaa33")
    ax_s_speed.text(0.5, 0.85, "SIM SPEED", color="#ffaa33", fontsize=10,
                    ha="center", va="center", transform=ax_s_speed.transAxes)
    s_speed_text = ax_s_speed.text(0.5, 0.42, "0", color="white", fontsize=38,
                                   ha="center", va="center", fontweight="bold",
                                   transform=ax_s_speed.transAxes)
    ax_s_speed.text(0.5, 0.13, "km/h", color="#8a9098", fontsize=10,
                    ha="center", va="center", transform=ax_s_speed.transAxes)

    ax_temp = panel([0.83, 0.36, 0.15, 0.20], accent="#ffaa33")
    temp_title = "TIRE TEMP [C] (assumed)" if temps_assumed else "TIRE TEMP [C]"
    ax_temp.text(0.5, 0.88, temp_title, color="#ffaa33", fontsize=9,
                 ha="center", va="center", transform=ax_temp.transAxes)
    temp_texts = []
    positions = [(0.25, 0.55), (0.75, 0.55), (0.25, 0.20), (0.75, 0.20)]
    labels_pos = [(0.25, 0.72), (0.75, 0.72), (0.25, 0.37), (0.75, 0.37)]
    corner_labels = ["FL", "FR", "RL", "RR"]
    for (lx, ly), lab in zip(labels_pos, corner_labels):
        ax_temp.text(lx, ly, lab, color="#8a9098", fontsize=8,
                     ha="center", va="center", transform=ax_temp.transAxes)
    for px, py in positions:
        t_text = ax_temp.text(px, py, "80", color="white", fontsize=16,
                              ha="center", va="center", fontweight="bold",
                              transform=ax_temp.transAxes)
        temp_texts.append(t_text)

    ax_soc = panel([0.65, 0.21, 0.33, 0.10], accent="#33cc66")
    ax_soc.text(0.02, 0.5, "ERS BATTERY", color="#33cc66", fontsize=9,
                ha="left", va="center", transform=ax_soc.transAxes)
    soc_bar = Rectangle((0.30, 0.25), 0.0, 0.50, color="#33cc66",
                        transform=ax_soc.transAxes)
    ax_soc.add_patch(soc_bar)
    soc_text = ax_soc.text(0.97, 0.5, "100%", color="white", fontsize=12,
                           ha="right", va="center", fontweight="bold",
                           transform=ax_soc.transAxes)

    ax_aero = panel([0.65, 0.315, 0.33, 0.038])
    aero_text = ax_aero.text(0.02, 0.5, "AERO: Z", color="#ffaa33", fontsize=9,
                             ha="left", va="center", fontweight="bold",
                             transform=ax_aero.transAxes)
    deploy_text = ax_aero.text(0.98, 0.5, "ERS ----", color="#555a60", fontsize=9,
                               ha="right", va="center", fontweight="bold",
                               transform=ax_aero.transAxes)

    ax_fz = panel([0.65, 0.06, 0.33, 0.12], accent="#ffaa33")
    ax_fz.text(0.5, 0.85, "VERTICAL LOAD Fz [N]", color="#ffaa33", fontsize=9,
               ha="center", va="center", transform=ax_fz.transAxes)
    ax_fz.text(0.25, 0.55, "FRONT", color="#8a9098", fontsize=8,
               ha="center", va="center", transform=ax_fz.transAxes)
    ax_fz.text(0.75, 0.55, "REAR", color="#8a9098", fontsize=8,
               ha="center", va="center", transform=ax_fz.transAxes)
    fz_f_text = ax_fz.text(0.25, 0.25, "0", color="white", fontsize=16,
                           ha="center", va="center", fontweight="bold",
                           transform=ax_fz.transAxes)
    fz_r_text = ax_fz.text(0.75, 0.25, "0", color="white", fontsize=16,
                           ha="center", va="center", fontweight="bold",
                           transform=ax_fz.transAxes)

    def init():
        return ()

    def update(i):
        real_dot.set_data([rx_f[i]], [ry_f[i]])
        real_dot.set_marker((3, 0, np.degrees(r_head[i]) - 90.0))
        sim_dot.set_data([sx_f[i]], [sy_f[i]])
        sim_dot.set_marker((3, 0, np.degrees(s_head[i]) - 90.0))
        if has2:
            sim2_dot.set_data([s2x[i]], [s2y[i]])
            sim2_dot.set_marker((3, 0, np.degrees(s2_head[i]) - 90.0))

        r_speed_text.set_text(f"{int(round(r_speed_f[i]))}")
        r_gear_text.set_text(f"{int(r_gear_f[i])}" if r_gear_f[i] >= 1 else "N")
        r_time_text.set_text(f"{t_grid[i]:.1f}")
        r_thr_bar.set_width(0.78 * (r_thr_f[i] / 100.0))
        r_brk_bar.set_width(0.78 * (r_brk_f[i] / 100.0))

        s_speed_text.set_text(f"{int(round(s_speed_f[i]))}")
        for k, tt in enumerate(temp_texts):
            tt.set_text(f"{int(round(s_temp_f[k][i]))}")
        soc_bar.set_width(0.65 * float(np.clip(s_soc_f[i], 0.0, 1.0)))
        soc_text.set_text(f"{int(round(100.0 * s_soc_f[i]))}%")
        fz_f_text.set_text(f"{int(round(s_fzf_f[i]))}")
        fz_r_text.set_text(f"{int(round(s_fzr_f[i]))}")
        if s_aero_f[i] > 0.5:
            aero_text.set_text("AERO: X (low drag)")
            aero_text.set_color("#4dc4ff")
        else:
            aero_text.set_text("AERO: Z (downforce)")
            aero_text.set_color("#ffaa33")
        if s_deploy_f[i] > 0.5:
            deploy_text.set_text("ERS DEPLOY")
            deploy_text.set_color("#33ff66")
        else:
            deploy_text.set_text("ERS ----")
            deploy_text.set_color("#555a60")
        return ()

    anim = animation.FuncAnimation(fig, update, init_func=init,
                                   frames=len(t_grid), interval=1000 / args.fps,
                                   blit=False)

    out = args.output
    if args.gif or out.endswith(".gif"):
        if not out.endswith(".gif"):
            out = out.rsplit(".", 1)[0] + ".gif"
        print(f"saving GIF to {out} (slow)...")
        anim.save(out, writer=animation.PillowWriter(fps=args.fps))
        print(f"saved {out}")
    else:
        print(f"saving MP4 to {out}...")
        try:
            anim.save(out, writer=animation.FFMpegWriter(fps=args.fps, bitrate=4000))
            print(f"saved {out}")
        except Exception as e:
            print(f"ffmpeg failed ({e}); falling back to GIF")
            out_gif = out.rsplit(".", 1)[0] + ".gif"
            anim.save(out_gif, writer=animation.PillowWriter(fps=args.fps))
            print(f"saved {out_gif}")


if __name__ == "__main__":
    main()
