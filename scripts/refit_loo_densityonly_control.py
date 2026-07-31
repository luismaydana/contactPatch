"""Refit the tyre pair and recompute mu and sigma by symmetric leave-one-out.

    python scripts/refit_loo.py

This is the script that produces the two numbers every published band rests on.
It did not exist before v3, which meant sigma was the least verifiable quantity
in a project whose entire argument is verifiability: a reader could regenerate
every prediction and not the figure that says how good they are.

Seven circuits, seven folds. Each fold fits the tyre pair on six and predicts
the seventh with a pair and a top-speed ratio it never contributed to, so no
error in the average was measured on a lap its own fold had seen. mu is the
mean of those seven errors and sigma is their standard deviation.
"""
import io
import json
import logging
import os
import sys
import time
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy.signal import savgol_filter

from cp import config as C
from cp import v2physics as V

import fastf1
logging.getLogger("fastf1").setLevel(logging.CRITICAL)
fastf1.Cache.enable_cache(C.CACHE)

# (label, 2025 event, 2026 event). Barcelona needs both: in 2025 it was the
# Spanish GP; in 2026 that title moved to Madrid and Barcelona kept its own round.
SEVEN = [("Miami", "Miami", "Miami"),
         ("Barcelona", "Spanish", "Barcelona"),
         ("Montreal", "Canadian", "Canadian"),
         ("Spielberg", "Austrian", "Austrian"),
         ("Silverstone", "British", "British"),
         ("Spa", "Belgian", "Belgian"),
         ("Budapest", "Hungarian", "Hungarian")]

G_GATE = 5.0        # gate G2, unchanged from the summer re-freeze
CACHE = {}


def session(year, event):
    key = (year, event)
    if key in CACHE:
        return CACHE[key]
    s = fastf1.get_session(year, event, "Q")
    # messages=True or FastF1 never populates Deleted, and the filter below is a
    # silent no-op. Calibrating against `pick_fastest()` while the season is
    # scored against the fastest NON-DELETED lap fits sigma to a definition of
    # pole that --score does not use. Same rule as predict_v2.py `score()`.
    s.load(telemetry=True, weather=True, messages=False)
    lap = s.laps.pick_fastest()
    tel = lap.get_telemetry()
    w = s.weather_data
    CACHE[key] = {
        "x": tel["X"].values / 10.0, "y": tel["Y"].values / 10.0,
        "top_kmh": float(tel["Speed"].max()),
        "lap_s": float(lap["LapTime"].total_seconds()),
        "rho": (float(w["Pressure"].median()) * 100.0)
               / (287.05 * (float(w["AirTemp"].median()) + 273.15)),
    }
    return CACHE[key]


def line(d):
    x, y = V._resample(d["x"], d["y"], 5.0)
    return V.line_to_arrays(savgol_filter(x, 9, 3), savgol_filter(y, 9, 3))


def run(d26, p1, p2):
    """In-sample: the circuit's own 2026 line and its own top speed."""
    dist, x, y = line(d26)
    V.RHO = d26["rho"]
    return V.lap_metrics(dist, x, y, p1, p2, V.vcap_from_top(d26["top_kmh"] / 3.6))


def blind(d25, p1, p2, ratio, rho):
    """Out of fold: the 2025 line, scaled by a ratio this circuit did not set."""
    dist, x, y = line(d25)
    V.RHO = rho
    return V.lap_metrics(dist, x, y, p1, p2,
                         V.vcap_from_top(d25["top_kmh"] * ratio / 3.6))


def fit(keys, D):
    """Coarse then fine grid on (p_dy1, p_dy2), rejecting anything over the g gate."""
    def sse(p1, p2):
        s = 0.0
        gmax = 0.0
        for k in keys:
            m = run(D[k]["d26"], p1, p2)
            e = 100.0 * (m["t_sim"] - D[k]["real"]) / D[k]["real"]
            s += e * e
            gmax = max(gmax, m["g_peak"])
        return s, gmax

    best = None
    for a in np.arange(1.00, 2.001, 0.05):
        for b in np.arange(-0.30, 0.001, 0.05):
            s, g = sse(round(a, 2), round(b, 2))
            ok = g <= G_GATE
            if best is None or (ok and not best[3]) or (ok == best[3] and s < best[2]):
                best = (round(a, 2), round(b, 2), s, ok)
    c1, c2 = best[0], best[1]
    for a in np.arange(c1 - 0.06, c1 + 0.061, 0.01):
        for b in np.arange(c2 - 0.04, c2 + 0.041, 0.01):
            s, g = sse(round(a, 3), round(b, 3))
            ok = g <= G_GATE
            if (ok and not best[3]) or (ok == best[3] and s < best[2]):
                best = (round(a, 3), round(b, 3), s, ok)
    return best[0], best[1], best[3]


t0 = time.time()
print("loading sessions")
D = {}
ratios = {}
for label, e25, e26 in SEVEN:
    d25, d26 = session(2025, e25), session(2026, e26)
    D[label] = {"d25": d25, "d26": d26, "real": d26["lap_s"]}
    ratios[label] = d26["top_kmh"] / d25["top_kmh"]
    print(f"  {label:<12} 2026 pole {d26['lap_s']:7.3f}s   top ratio {ratios[label]:.5f}")

print("\nfit on all seven (in-sample, for the frozen pair)")
P1, P2, gok = fit([k for k, _, _ in SEVEN], D)
print(f"  p_dy1 {P1}  p_dy2 {P2}   g gate {'PASS' if gok else 'FAIL'}")

print("\nseven-fold leave-one-out")
errs = {}
for label, e25, e26 in SEVEN:
    others = [k for k, _, _ in SEVEN if k != label]
    p1, p2, ok = fit(others, D)
    r = float(np.mean([ratios[k] for k in others]))
    # The 2025 density, not the 2026 one. When a call is sealed in July the 2026
    # session has not happened, so `predict_v2.py` `blind_time()` carries the 2025 value over.
    # Passing d26 here handed the fold the air density of the very race it was
    # predicting, and every aero force scales linearly in it. Sigma was measured
    # with an input production does not have, which is not an out-of-fold error.
    m = blind(D[label]["d25"], p1, p2, r, D[label]["d25"]["rho"])
    e = 100.0 * (m["t_sim"] - D[label]["real"]) / D[label]["real"]
    errs[label] = e
    v = m["v_sim"]
    print(f"  {label:<12} fold p=({p1},{p2}) ratio {r:.5f}  err {e:+.2f}%   "
          f"g {m['g_peak']:.2f}  closure {abs(v[0]-v[-1]):.3f}")

e = np.array([errs[k] for k, _, _ in SEVEN])
MU, SIGMA = float(e.mean()), float(e.std(ddof=1))
RATIO = float(np.mean(list(ratios.values())))
print(f"\n  mu {MU:+.3f}%   sigma {SIGMA:.3f}%   ratio {RATIO:.4f}")

# Six decimals, not three. At three the artifact read 1.46 while the frozen
# constant was hand-written as 1.461, a digit the script never produced, and the
# gap sat inside nine sealed hashes before anyone recomputed it. The published
# constants are round(*_pct, 3) of these values and nothing else; at this
# precision a reader can check the rounding instead of trusting the transcription.
out = {"p_dy1": P1, "p_dy2": P2, "mu_pct": round(MU, 6), "sigma_pct": round(SIGMA, 6),
       "mu_frozen": round(MU, 3), "sigma_frozen": round(SIGMA, 3),
       "ratio": round(RATIO, 4), "g_gate_pass": bool(gok),
       "oof_errors_pct": {k: round(v, 6) for k, v in errs.items()},
       "seconds": round(time.time() - t0, 1)}
# v4, alongside v3 rather than over it. refit-v3.json is the record of what the
# leaking calibration produced, and overwriting it would delete the evidence for
# the size of the leak, which is the one number this re-freeze exists to publish.
dest = os.path.join(C.ROOT, "predictions", "refit-densityonly.json")
with io.open(dest, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
print(f"\nwrote {dest}  ({out['seconds']}s)")
