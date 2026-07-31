"""animated 2d top-down with telemetry hud.

renders the FastF1 lap as an animation. car marker moves along the racing line;
the right-side hud shows speed, throttle/brake bars, gear, lap time and distance.

writes MP4 through imageio-ffmpeg when available; --gif or a missing encoder
falls back to a Pillow GIF.

usage:
  python scripts/visualize_animation.py \
    --track data/tracks/suzuka/centerline.csv \
    --telemetry data/telemetry/2026_Japan_VER_Q.csv \
    --output data/sim_results/lap_animation.mp4
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


def resample_uniform(t, arrays, fps):
    t0, t1 = t[0], t[-1]
    n = max(2, int(round((t1 - t0) * fps)))
    t_grid = np.linspace(t0, t1, n)
    out = [np.interp(t_grid, t, a) for a in arrays]
    return t_grid, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", required=True)
    ap.add_argument("--telemetry", required=True)
    ap.add_argument("--output", default="data/sim_results/lap_animation.mp4")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--gif", action="store_true", help="save as GIF instead of MP4")
    args = ap.parse_args()

    track_df = pd.read_csv(args.track)
    tel = pd.read_csv(args.telemetry)

    x_raw = tel["X"].values / 10.0
    y_raw = tel["Y"].values / 10.0
    speed = tel["Speed"].values
    throttle = tel["Throttle"].values
    brake = tel["Brake"].astype(bool).astype(float).values * 100.0
    gear = tel["nGear"].values
    distance = tel["Distance"].values
    t = np.array([parse_fastf1_time(s) for s in tel["Time"].values])
    t = t - t[0]

    x, y = align_path_to_centerline(x_raw, y_raw, track_df["x"].values, track_df["y"].values)

    t_grid, (x_f, y_f, v_f, th_f, br_f, g_f, d_f) = resample_uniform(
        t, [x, y, speed, throttle, brake, gear, distance], args.fps
    )
    g_f = np.round(g_f).astype(int)

    dx = np.gradient(x_f)
    dy = np.gradient(y_f)
    heading = np.arctan2(dy, dx)

    fig = plt.figure(figsize=(16, 9), facecolor="#101418")

    ax_track = fig.add_axes([0.02, 0.05, 0.65, 0.9])
    ax_track.set_facecolor("#101418")
    ax_track.axis("off")
    ax_track.set_aspect("equal")

    draw_track_surface(ax_track, track_df)
    draw_sectors(ax_track, track_df)

    pts = np.array([x, y]).T.reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    lc = LineCollection(segs, cmap="plasma", linewidth=1.5, zorder=4, alpha=0.35)
    lc.set_array(speed[:-1])
    ax_track.add_collection(lc)

    (car_dot,) = ax_track.plot([], [], marker=(3, 0, 0), color="white",
                               markersize=18, markeredgecolor="black",
                               markeredgewidth=1.5, zorder=10)

    def hud_axes(rect):
        a = fig.add_axes(rect)
        a.set_facecolor("#1a1f25")
        a.set_xticks([])
        a.set_yticks([])
        for s in a.spines.values():
            s.set_color("#3a4048")
        return a

    ax_speed = hud_axes([0.70, 0.70, 0.28, 0.22])
    ax_speed.text(0.5, 0.85, "SPEED", color="#8a9098", fontsize=12,
                  ha="center", va="center", transform=ax_speed.transAxes)
    speed_text = ax_speed.text(0.5, 0.42, "0", color="white", fontsize=56,
                               ha="center", va="center", fontweight="bold",
                               transform=ax_speed.transAxes)
    ax_speed.text(0.5, 0.10, "km/h", color="#8a9098", fontsize=12,
                  ha="center", va="center", transform=ax_speed.transAxes)

    ax_thr = hud_axes([0.70, 0.59, 0.28, 0.06])
    ax_thr.text(0.01, 0.5, "THR", color="#8a9098", fontsize=11,
                ha="left", va="center", transform=ax_thr.transAxes)
    thr_bar = Rectangle((0.12, 0.15), 0.0, 0.70, color="#33cc66",
                        transform=ax_thr.transAxes)
    ax_thr.add_patch(thr_bar)
    ax_thr.plot([0.12, 0.99], [0.15, 0.15], color="#3a4048",
                transform=ax_thr.transAxes, linewidth=0.5)

    ax_brk = hud_axes([0.70, 0.51, 0.28, 0.06])
    ax_brk.text(0.01, 0.5, "BRK", color="#8a9098", fontsize=11,
                ha="left", va="center", transform=ax_brk.transAxes)
    brk_bar = Rectangle((0.12, 0.15), 0.0, 0.70, color="#ff3344",
                        transform=ax_brk.transAxes)
    ax_brk.add_patch(brk_bar)

    ax_gear = hud_axes([0.70, 0.32, 0.13, 0.16])
    ax_gear.text(0.5, 0.85, "GEAR", color="#8a9098", fontsize=11,
                 ha="center", va="center", transform=ax_gear.transAxes)
    gear_text = ax_gear.text(0.5, 0.40, "N", color="#ffcc33", fontsize=48,
                             ha="center", va="center", fontweight="bold",
                             transform=ax_gear.transAxes)

    ax_time = hud_axes([0.85, 0.32, 0.13, 0.16])
    ax_time.text(0.5, 0.85, "LAP TIME", color="#8a9098", fontsize=11,
                 ha="center", va="center", transform=ax_time.transAxes)
    time_text = ax_time.text(0.5, 0.40, "0.00", color="white", fontsize=28,
                             ha="center", va="center", fontweight="bold",
                             transform=ax_time.transAxes)

    ax_dist = hud_axes([0.70, 0.13, 0.28, 0.16])
    ax_dist.text(0.5, 0.85, "DISTANCE", color="#8a9098", fontsize=11,
                 ha="center", va="center", transform=ax_dist.transAxes)
    dist_text = ax_dist.text(0.5, 0.40, "0 m", color="white", fontsize=24,
                             ha="center", va="center", fontweight="bold",
                             transform=ax_dist.transAxes)

    fig.text(0.36, 0.965, "Suzuka - VER - F1 2026 Q (real telemetry)",
             color="white", fontsize=14, ha="center", va="center")

    def init():
        car_dot.set_data([], [])
        return car_dot, speed_text, gear_text, time_text, dist_text, thr_bar, brk_bar

    def update(i):
        car_dot.set_data([x_f[i]], [y_f[i]])
        car_dot.set_marker((3, 0, np.degrees(heading[i]) - 90.0))
        speed_text.set_text(f"{int(round(v_f[i]))}")
        gear_text.set_text(f"{int(g_f[i])}" if g_f[i] >= 1 else "N")
        time_text.set_text(f"{t_grid[i]:.2f}")
        dist_text.set_text(f"{int(round(d_f[i]))} m")
        thr_bar.set_width(0.87 * (th_f[i] / 100.0))
        brk_bar.set_width(0.87 * (br_f[i] / 100.0))
        return car_dot, speed_text, gear_text, time_text, dist_text, thr_bar, brk_bar

    anim = animation.FuncAnimation(fig, update, init_func=init,
                                   frames=len(t_grid), interval=1000 / args.fps,
                                   blit=True)

    if args.gif or args.output.endswith(".gif"):
        out = args.output if args.output.endswith(".gif") else args.output.rsplit(".", 1)[0] + ".gif"
        print(f"saving GIF to {out} (this is slow)...")
        anim.save(out, writer=animation.PillowWriter(fps=args.fps))
        print(f"saved {out}")
    else:
        out = args.output
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
