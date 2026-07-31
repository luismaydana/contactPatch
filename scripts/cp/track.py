import os
import csv
import numpy as np
from cp import config as C
from cp import energy as en

REGISTRY = {
    "Suzuka": {"year": 2026, "round": 3, "top_kmh": 321},
    "Melbourne": {"year": 2026, "round": 1, "top_kmh": 327},
    "Shanghai": {"year": 2026, "round": 2, "top_kmh": 332},
    "Montreal": {"year": 2026, "round": 5, "top_kmh": 332},
    "Barcelona": {"year": 2026, "round": 7, "top_kmh": 341},
    "Monza": {"year": 2025, "round": "Monza", "top_kmh": 348},
}


def vcap_from_top(top_mps):
    return max(92.0, top_mps * 1.04)


def vcap(track):
    return vcap_from_top(REGISTRY[track]["top_kmh"] / 3.6)


def recovery_cap(track):
    return en.RECOVERY_CAP_BY_TRACK.get(track, en.RECOVERY_CAP_J)


def session(track):
    r = REGISTRY[track]
    return r["year"], r["round"]


def centerline_path(track):
    return os.path.join(C.ROOT, "data", "tracks", track.lower(), "centerline.csv")


def load_centerline(track):
    path = centerline_path(track)
    s, x, y, wl, wr = [], [], [], [], []
    with open(path) as f:
        rd = csv.DictReader(f)
        for row in rd:
            s.append(float(row["s_arc"])); x.append(float(row["x"]))
            y.append(float(row["y"])); wl.append(float(row["width_left"]))
            wr.append(float(row["width_right"]))
    return {"s": np.array(s), "x": np.array(x), "y": np.array(y),
            "width_left": np.array(wl), "width_right": np.array(wr)}
