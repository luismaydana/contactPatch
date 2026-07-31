import sys, os, warnings
warnings.filterwarnings("ignore")
from cp import config as C
sys.path.insert(0, C.SCRIPTS)
import numpy as np, pandas as pd, fastf1
import qss_laptime as q
from cp import qss as cpq
from cp import track as tr

fastf1.Cache.enable_cache(C.CACHE)


def _vcap(tel):
    return tr.vcap_from_top(float(tel["Speed"].max()) / 3.6)


def field_greedy(year, rnd):
    s = fastf1.get_session(year, rnd, "Q")
    s.load()
    q.V_CAP = _vcap(s.laps.pick_fastest().get_telemetry())
    errs, reals = [], []
    for drv in list(s.laps["Driver"].unique()):
        try:
            lap = s.laps.pick_drivers(drv).pick_fastest()
            if lap is None or pd.isna(lap["LapTime"]):
                continue
            tel = lap.get_telemetry()
            if len(tel) < 100:
                continue
            m = cpq.compute_metrics(tel, tire="pacejka")
            errs.append(m["err_ers"]); reals.append(m["t_real"])
        except Exception:
            continue
    errs, reals = np.array(errs), np.array(reals)
    med = np.median(reals)
    keep = (reals < med * 1.03) & (reals > med * 0.95)
    return float(errs[keep].mean())


def fastest_greedy(year, name):
    s = fastf1.get_session(year, name, "Q")
    s.load()
    tel = s.laps.pick_fastest().get_telemetry()
    q.V_CAP = _vcap(tel)
    return float(cpq.compute_metrics(tel, tire="pacejka")["err_ers"])


def main():
    print(f"{'circuit':<11}{'greedy':>9}{'target':>9}{'delta':>8}  status")
    ok = True
    for label, year, rnd in C.FIELD:
        g = field_greedy(year, rnd)
        t = C.TARGETS[label]
        d = g - t
        passed = abs(d) <= C.TOL_FIELD
        ok = ok and passed
        print(f"{label:<11}{g:>+9.2f}{t:>+9.2f}{d:>+8.2f}  {'PASS' if passed else 'FAIL'}")
    g = fastest_greedy(C.MONZA[1], C.MONZA[2])
    t = C.TARGETS["Monza"]
    d = g - t
    passed = abs(d) <= C.TOL_MONZA
    ok = ok and passed
    print(f"{'Monza':<11}{g:>+9.2f}{t:>+9.2f}{d:>+8.2f}  {'PASS' if passed else 'FAIL'}")
    print()
    print("GATE:", "GREEN, core reproduced" if ok else "RED, a number moved, do not advance")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
