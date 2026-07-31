"""Convert a real driver's GPS lap into a drivable track file.

Takes the FastF1 telemetry of one lap, smooths the GPS trace, resamples it
to uniform 5 m arc-length spacing, closes the loop at the start line, and
writes it in the centerline.csv schema. The closed-loop simulator can then
drive the expert's racing line instead of the geometric centerline, which
raises every corner radius to what the real driver actually used.

run:
  python scripts/make_expert_line.py \
      --telemetry data/telemetry/2026_Japan_VER_Q.csv \
      --output data/tracks/suzuka/raceline_ver.csv
"""
import argparse
import numpy as np
import pandas as pd


def smooth(a, k):
    w = 2 * k + 1
    kernel = np.ones(w) / w
    return np.convolve(np.pad(a, k, mode="wrap"), kernel, mode="valid")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--telemetry", required=True)
    ap.add_argument("--output", default="data/tracks/suzuka/raceline_ver.csv")
    ap.add_argument("--step", type=float, default=5.0)
    args = ap.parse_args()

    tel = pd.read_csv(args.telemetry)
    x = tel["X"].values / 10.0
    y = tel["Y"].values / 10.0

    x = smooth(x, 2)
    y = smooth(y, 2)

    seam = np.hypot(x[-1] - x[0], y[-1] - y[0])
    x = np.append(x, x[0])
    y = np.append(y, y[0])

    ds = np.hypot(np.diff(x), np.diff(y))
    s = np.concatenate([[0.0], np.cumsum(ds)])
    total = s[-1]

    s_u = np.arange(0.0, total, args.step)
    x_u = np.interp(s_u, s, x)
    y_u = np.interp(s_u, s, y)

    x_u = smooth(x_u, 1)
    y_u = smooth(y_u, 1)

    sector = np.where(s_u < total / 3.0, 1, np.where(s_u < 2.0 * total / 3.0, 2, 3))

    out = pd.DataFrame({
        "s_arc": np.round(s_u, 4),
        "x": np.round(x_u, 4),
        "y": np.round(y_u, 4),
        "z": 0.0,
        "width_left": 7.5,
        "width_right": 7.5,
        "sector": sector,
    })
    out.to_csv(args.output, index=False)
    print(f"wrote {args.output}: {len(out)} points, length {total:.1f} m, seam gap was {seam:.1f} m")


if __name__ == "__main__":
    main()
