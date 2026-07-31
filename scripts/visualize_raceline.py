import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from visualize_track import draw_track_surface, draw_sectors, align_path_to_centerline

def main():
    parser = argparse.ArgumentParser(description="Visualize Verstappen's Q raceline colored by speed on Suzuka track surface.")
    parser.add_argument("--track", required=True, help="Path to the centerline track CSV.")
    parser.add_argument("--telemetry", required=True, help="Path to the raw FastF1 telemetry CSV.")
    parser.add_argument("--output", default="data/sim_results/raceline_speed.png", help="Output path for the rendered image.")
    args = parser.parse_args()

    track_df = pd.read_csv(args.track)
    tel_df = pd.read_csv(args.telemetry)

    fig, ax = plt.subplots(figsize=(14, 8), facecolor='#111111')
    ax.set_facecolor('#111111')
    ax.axis("off")
    ax.set_aspect("equal")

    draw_track_surface(ax, track_df)
    draw_sectors(ax, track_df)

    x = tel_df["X"].values / 10.0
    y = tel_df["Y"].values / 10.0
    speed = tel_df["Speed"].values

    x, y = align_path_to_centerline(x, y, track_df["x"].values, track_df["y"].values)

    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    lc = LineCollection(segments, cmap="plasma", linewidth=2.5, zorder=5)
    lc.set_array(speed[:-1])

    ax.add_collection(lc)

    cbar = fig.colorbar(lc, ax=ax, shrink=0.6, pad=0.02)
    cbar.set_label("Speed [km/h]", color="white", fontsize=12)

    cbar.ax.yaxis.set_tick_params(color="white")
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color="white")

    plt.title("Suzuka - Verstappen Q raceline (colored by speed)", color="white", fontsize=16, pad=15)

    fig.tight_layout()
    fig.savefig(args.output, dpi=150, facecolor=fig.get_facecolor())
    print(f"Raceline visualization saved successfully to: {args.output}")

if __name__ == "__main__":
    main()
