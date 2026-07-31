"""Two-parameter tire calibration against one reference lap, with holdout.

Fits the lateral peak friction pair (p_dy1, p_dy2) of the load-sensitive
tire model by grid search, minimizing the speed-trace RMSE of the QSS
prediction against a single driver's real lap. The longitudinal pair
follows the fitted lateral one with the historical +0.1 peak offset and
the same slope.

The fitted tire is then evaluated, untouched, on every other clean lap of
the session. If a fit on one lap generalizes to eighteen laps it never
saw, it is calibration; if it only helped the lap it saw, the holdout
exposes it as overfitting.

run:
  python scripts/calibrate_tire.py
"""
import glob
import os
import numpy as np
import pandas as pd
import qss_laptime as q

FIT_LAP = "data/telemetry/2026_Japan_VER_Q.csv"
FIELD_DIR = "data/telemetry/field"
EXCLUDE = {"ANT", "OCO", "COL"}


def set_tire(d1, d2):
    q.P_DY1 = d1
    q.P_DY2 = d2
    q.P_DX1 = d1 + 0.1
    q.P_DX2 = d2


def holdout_errors():
    errs = {}
    for f in sorted(glob.glob(os.path.join(FIELD_DIR, "*.csv"))):
        abbr = os.path.basename(f).split("_")[2]
        if abbr in EXCLUDE or abbr == "VER":
            continue
        m = q.compute_metrics(pd.read_csv(f), tire="pacejka")
        errs[abbr] = m["err_ers"]
    return errs


def main():
    tel = pd.read_csv(FIT_LAP)

    best = None
    for d1 in np.arange(1.40, 2.01, 0.05):
        for d2 in np.arange(-0.20, -0.019, 0.01):
            set_tire(float(d1), float(d2))
            m = q.compute_metrics(tel, tire="pacejka")
            if best is None or m["rmse"] < best[0]:
                best = (m["rmse"], float(d1), float(d2), m["err_ers"], m["t_sim"])

    rmse, d1, d2, err, t_sim = best
    print(f"fit lap: VER   objective: speed-trace RMSE")
    print(f"best params: p_dy1={d1:.2f}  p_dy2={d2:.2f}  "
          f"(p_dx1={d1+0.1:.2f}, p_dx2={d2:.2f})")
    print(f"VER with fit: rmse {rmse:.2f} m/s   lap {t_sim:.3f} s   err {err:+.2f}%")

    set_tire(d1, d2)
    v130 = 297.0 / 3.6
    cap = float(q.grip_accel_lat(v130, "pacejka")) / q.G
    print(f"envelope at 297 km/h: {cap:.2f} g  (130R demand was ~5.3 g)")
    for vv in (20.0, 30.0, 50.0, 70.0, 90.0):
        print(f"  mu_y({vv:.0f} m/s) = {float(q.mu_lat(vv, 'pacejka')):.3f}  "
              f"load {q.wheel_load(vv)/1e3:.1f} kN")

    print("\nholdout (18 clean drivers the fit never saw):")
    set_tire(1.40, -0.11)
    before = holdout_errors()
    set_tire(d1, d2)
    after = holdout_errors()
    b = np.array(list(before.values()))
    a = np.array(list(after.values()))
    print(f"  before (1.40/-0.11): mean {b.mean():+.2f}%  median {np.median(b):+.2f}%  std {b.std(ddof=1):.2f}")
    print(f"  after  ({d1:.2f}/{d2:.2f}): mean {a.mean():+.2f}%  median {np.median(a):+.2f}%  std {a.std(ddof=1):.2f}")
    worst = sorted(after.items(), key=lambda kv: -abs(kv[1]))[:3]
    print(f"  worst after: " + "  ".join(f"{k} {v:+.2f}%" for k, v in worst))


if __name__ == "__main__":
    main()
