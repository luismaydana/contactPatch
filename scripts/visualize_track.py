"""2d top-down track surface renderer.

draws the asphalt ribbon from the centerline plus its left/right widths.
later visualization stages (speed line, sectors, animated car, hud) draw on
top of the axes this module returns.

geometry:
  tangent t = normalized d(x,y)/ds
  left normal n = (-t_y, t_x)
  left edge  = center + n * width_left
  right edge = center - n * width_right
the asphalt is the filled polygon between left and right edges.
"""
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def align_path_to_centerline(x_src, y_src, x_ref, y_ref):
    """rigid 2d transform (translation + rotation) that maps a source path
    into the centerline's coordinate frame. matches start point and initial
    heading. used to overlay FastF1 telemetry (which lives in its own frame)
    on top of our centerline.csv."""
    theta_src = np.arctan2(y_src[1] - y_src[0], x_src[1] - x_src[0])
    theta_ref = np.arctan2(y_ref[1] - y_ref[0], x_ref[1] - x_ref[0])
    dtheta = theta_ref - theta_src
    cos_t = np.cos(dtheta)
    sin_t = np.sin(dtheta)
    dx = x_src - x_src[0]
    dy = y_src - y_src[0]
    xr = cos_t * dx - sin_t * dy
    yr = sin_t * dx + cos_t * dy
    return xr + x_ref[0], yr + y_ref[0]


def edges_from_centerline(x, y, width_left, width_right):
    dx = np.gradient(x)
    dy = np.gradient(y)
    norm = np.hypot(dx, dy)
    norm[norm < 1e-9] = 1e-9
    tx = dx / norm
    ty = dy / norm

    nx = -ty
    ny = tx

    left_x = x + nx * width_left
    left_y = y + ny * width_left
    right_x = x - nx * width_right
    right_y = y - ny * width_right
    return (left_x, left_y), (right_x, right_y)


def _normals(x, y):
    dx = np.gradient(x)
    dy = np.gradient(y)
    norm = np.hypot(dx, dy)
    norm[norm < 1e-9] = 1e-9
    return -dy / norm, dx / norm


def draw_sectors(ax, df):
    """draw a perpendicular line across the track at every sector transition,
    plus a start/finish line at s_arc=0. sector lines are color-coded."""
    x = df["x"].values
    y = df["y"].values
    wl = df["width_left"].values
    wr = df["width_right"].values
    sectors = df["sector"].values
    nx, ny = _normals(x, y)

    sector_colors = {1: "#ff4d4d", 2: "#4dff88", 3: "#4da6ff"}

    flag_overhang = 35.0

    transitions = np.where(np.diff(sectors) != 0)[0] + 1
    for i in transitions:
        x0 = x[i] + nx[i] * (wl[i] + flag_overhang)
        y0 = y[i] + ny[i] * (wl[i] + flag_overhang)
        x1 = x[i] - nx[i] * (wr[i] + flag_overhang)
        y1 = y[i] - ny[i] * (wr[i] + flag_overhang)
        color = sector_colors.get(int(sectors[i]), "white")
        ax.plot([x0, x1], [y0, y1], color=color, linewidth=2.5, zorder=6)

    x0 = x[0] + nx[0] * (wl[0] + flag_overhang)
    y0 = y[0] + ny[0] * (wl[0] + flag_overhang)
    x1 = x[0] - nx[0] * (wr[0] + flag_overhang)
    y1 = y[0] - ny[0] * (wr[0] + flag_overhang)
    ax.plot([x0, x1], [y0, y1], color="white", linewidth=4.0, zorder=7)
    ax.plot([x0, x1], [y0, y1], color="black", linewidth=4.0, linestyle=(0, (3, 3)), zorder=8)


def draw_track_surface(ax, df):
    x = df["x"].values
    y = df["y"].values
    wl = df["width_left"].values
    wr = df["width_right"].values

    (lx, ly), (rx, ry) = edges_from_centerline(x, y, wl, wr)

    poly_x = np.concatenate([lx, rx[::-1]])
    poly_y = np.concatenate([ly, ry[::-1]])
    ax.fill(poly_x, poly_y, color="#555a60", zorder=1, label="_asphalt")

    ax.plot(lx, ly, color="white", linewidth=1.0, zorder=2)
    ax.plot(rx, ry, color="white", linewidth=1.0, zorder=2)

    ax.plot(x, y, color="#888888", linewidth=0.5, linestyle=":", zorder=2)

    return ax


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--track", default="data/tracks/suzuka/centerline.csv")
    ap.add_argument("--output", default="data/sim_results/track_surface.png")
    args = ap.parse_args()

    df = pd.read_csv(args.track)

    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor("#101418")
    ax.set_facecolor("#101418")

    draw_track_surface(ax, df)

    ax.set_aspect("equal", adjustable="datalim")
    ax.axis("off")
    ax.set_title("Suzuka Circuit - track surface", color="white", fontsize=14)

    fig.tight_layout()
    fig.savefig(args.output, dpi=150, facecolor=fig.get_facecolor())
    print(f"track surface saved to {args.output}")


if __name__ == "__main__":
    main()
