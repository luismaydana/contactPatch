#!/usr/bin/env python3
"""
converts a track CSV from the TUMFTM racetrack-database format to the
project's centerline.csv schema.
TUMFTM format:
    x_m, y_m, w_tr_right_m, w_tr_left_m
project schema:
    s_arc, x, y, z, width_left, width_right, sector
usage:
    python scripts/convert_tumftm_to_centerline.py Suzuka.csv data/tracks/suzuka/centerline.csv

source data license: TUMFTM/racetrack-database is LGPL v3.0. cite the
repo in docs/references.md when committing the output.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path


def convert(src: Path, dst: Path) -> None:
    with src.open("r") as f:
        reader = csv.reader(f)
        rows = []
        for row in reader:
            if row and row[0].strip().lstrip("#").strip().startswith("x_m"):
                continue
            if not row or not row[0].strip():
                continue
            x, y, w_right, w_left = (float(v) for v in row[:4])
            rows.append((x, y, w_left, w_right))

    if len(rows) < 2:
        raise SystemExit(f"not enough points in {src} (got {len(rows)})")

    s_arc = [0.0]
    for i in range(1, len(rows)):
        dx = rows[i][0] - rows[i - 1][0]
        dy = rows[i][1] - rows[i - 1][1]
        s_arc.append(s_arc[-1] + math.hypot(dx, dy))

    total = s_arc[-1]
    third = total / 3.0

    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["s_arc", "x", "y", "z", "width_left", "width_right", "sector"])
        for i, (x, y, wl, wr) in enumerate(rows):
            s = s_arc[i]
            if s < third:
                sector = 1
            elif s < 2 * third:
                sector = 2
            else:
                sector = 3
            w.writerow([f"{s:.4f}", f"{x:.4f}", f"{y:.4f}", "0.0000",
                        f"{wl:.4f}", f"{wr:.4f}", sector])

    print(f"wrote {len(rows)} points to {dst}")
    print(f"total arc length: {total:.2f} m")
    print(f"sector boundaries: {third:.2f} m and {2*third:.2f} m")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: convert_tumftm_to_centerline.py <src.csv> <dst.csv>", file=sys.stderr)
        return 1
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
