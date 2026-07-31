"""contactPatch race predictor.

FAST PATH (prediction, no network):  python scripts/predict_race.py <Circuit>
SCORING (after quali, uses FastF1):  python scripts/predict_race.py --score <Circuit>
RE-FREEZE calibration (rarely):      python scripts/predict_race.py --backtest

The calibration (config/mu/sigma) is FROZEN below. A prediction is pure local
compute (centerline -> raceline -> QSS -> offset) and runs in seconds.
"""
import sys, hashlib, warnings
warnings.filterwarnings("ignore")
from cp import config as C
sys.path.insert(0, C.SCRIPTS)
import numpy as np
import qss_laptime as q
from cp import qss as cpq, track as tr, raceline as rl, ers_dp

# ---- FROZEN calibration (2026-07-13, 4-circuit set, LOO V_CAP anchor) ----
CONFIG = "greedy"       # chosen by judgment: canonical metric, ~0 bias
MU = -0.39              # offset %  (model vs real 2026 pole)
SIGMA = 1.11            # 1-sigma error bar %
RATIO = 1.0037          # 2026/2025 top-speed ratio (mean of 8 run circuits)

# ---- circuit table: name -> (centerline, 2025 top km/h, 2026 quali round) ----
CIRCUITS = {
    "Spa": ("spa", 339.0, 10), "Budapest": ("budapest", 318.0, 11),
    "Monza": ("monza", 348.0, 13), "Austin": ("austin", 324.0, 17),
    "Mexico": ("mexicocity", 351.0, 18), "SaoPaulo": ("saopaulo", 336.0, 19),
}


def fmt(t):
    return f"{int(t // 60)}:{t % 60:06.3f}"


def blind_model_time(cl_name, top25):
    c = tr.load_centerline(cl_name)
    rx, ry, _ = rl.minimum_curvature(c["x"], c["y"], c["width_left"], c["width_right"])
    tel = rl.to_telemetry_frame(rx, ry)
    q.V_CAP = tr.vcap_from_top(top25 * RATIO / 3.6)
    m = cpq.compute_metrics(tel, tire="pacejka")
    if CONFIG == "greedy":
        return m["t_sim"], q.V_CAP
    return ers_dp.dp_optimize(m)["t_dp"], q.V_CAP


def predict(name):
    cl, top25, _ = CIRCUITS[name]
    t_model, vcap = blind_model_time(cl, top25)
    pole = t_model / (1 + MU / 100.0)
    lo1, hi1 = pole * (1 - SIGMA / 100), pole * (1 + SIGMA / 100)
    lo2, hi2 = pole * (1 - 2 * SIGMA / 100), pole * (1 + 2 * SIGMA / 100)
    top_pred = top25 * RATIO
    commit = (f"contactPatch | {name} 2026 quali POLE (dry) | frozen pre-quali | "
              f"config={CONFIG} mu={MU}% sigma={SIGMA}% | V_CAP={vcap:.1f} | "
              f"POINT={fmt(pole)} | 1sig=[{fmt(lo1)},{fmt(hi1)}] | "
              f"2sig=[{fmt(lo2)},{fmt(hi2)}] | top~{top_pred:.0f}kmh | wet=VOID")
    h = hashlib.sha256(commit.encode()).hexdigest()
    print(f"=== {name} 2026 pole prediction (dry) ===")
    print(f"POINT  {fmt(pole)}   1sig [{fmt(lo1)}, {fmt(hi1)}]   2sig [{fmt(lo2)}, {fmt(hi2)}]")
    print(f"top speed ~{top_pred:.0f} km/h   V_CAP {vcap:.1f} m/s   model {t_model:.2f}s")
    print(f"SHA-256  {h}")
    print(f"\n--- Instagram caption ---\n{ig_caption(name, pole)}")
    print(f"\n--- X/Twitter ---\n{x_caption(name, pole, h)}")
    return commit, h


def ig_caption(name, pole):
    gp = {"Spa": "Belgian GP", "Budapest": "Hungarian GP", "Monza": "Italian GP",
          "Austin": "US GP", "Mexico": "Mexico City GP", "SaoPaulo": "Sao Paulo GP"}[name]
    return (f"PREDICTION - {gp} 2026 qualifying (posted BEFORE quali)\n\n"
            f"Dry pole: {fmt(pole)}, +/- about a second.\n\n"
            f"Made with a vehicle-dynamics simulator I built from scratch. It learns "
            f"a tyre model from ONE qualifying lap, freezes it, and predicts other "
            f"circuits - calibrated on four 2026 circuits, sigma 1.11% (in-sample).\n\n"
            f"Conditional on a DRY session: if it rains this call is void (the model "
            f"is dry-only, and 2026 rules restrict active aero in the wet).\n\n"
            f"Right or wrong, the real result goes here after quali. That is the whole "
            f"point - a real model makes falsifiable calls, not vibes.\n\n"
            f"#F1 #{name} #Formula1 #simulation #physics #motorsport #engineering #datascience")


def x_caption(name, pole, h):
    return (f"Pre-quali prediction, {name} 2026 (physics sim I built).\n"
            f"Dry pole: {fmt(pole)} +/-~1s. Conditional on dry (wet=void).\n"
            f"2-param tyre fit on 1 lap, frozen; sigma 1.11% (in-sample, 4 circuits).\n"
            f"Result + hit/miss after quali.\nsha256:{h[:16]}")


def backtest():
    RATIOS = {"Melbourne": .9939, "Shanghai": 1.0061, "Suzuka": .9877, "Miami": 1.0088,
              "Montreal": 1.0000, "Barcelona": 1.0396, "Spielberg": 1.0154, "Silverstone": .9784}
    BT = {"Shanghai": ("shanghai", 2, 330.), "Montreal": ("montreal", 5, 332.),
          "Spielberg": ("spielberg", 8, 324.), "Silverstone": ("silverstone", 9, 324.)}
    import fastf1
    fastf1.Cache.enable_cache(C.CACHE)
    eg, ed = [], []
    for name, (cl, rnd, top25) in BT.items():
        loo = np.mean([v for k, v in RATIOS.items() if k != name])
        c = tr.load_centerline(cl)
        rx, ry, _ = rl.minimum_curvature(c["x"], c["y"], c["width_left"], c["width_right"])
        tel = rl.to_telemetry_frame(rx, ry)
        q.V_CAP = tr.vcap_from_top(top25 * loo / 3.6)
        m = cpq.compute_metrics(tel, tire="pacejka")
        td = ers_dp.dp_optimize(m)["t_dp"]
        s = fastf1.get_session(2026, rnd, "Q"); s.load()
        pole = float(s.laps.pick_fastest()["LapTime"].total_seconds())
        eg.append(100 * (m["t_sim"] - pole) / pole); ed.append(100 * (td - pole) / pole)
    eg, ed = np.array(eg), np.array(ed)
    print(f"greedy mu={eg.mean():+.2f} sigma={eg.std(ddof=1):.2f} | "
          f"DP mu={ed.mean():+.2f} sigma={ed.std(ddof=1):.2f}")


def score(name):
    import fastf1
    fastf1.Cache.enable_cache(C.CACHE)
    _, _, rnd = CIRCUITS[name]
    s = fastf1.get_session(2026, rnd, "Q"); s.load()
    pole = float(s.laps.pick_fastest()["LapTime"].total_seconds())
    cl, top25, _ = CIRCUITS[name]
    t_model, _ = blind_model_time(cl, top25)
    pred = t_model / (1 + MU / 100.0)
    err = 100 * (pred - pole) / pole
    verdict = "HIT" if abs(err) <= SIGMA else ("2SIG" if abs(err) <= 2 * SIGMA else "MISS")
    print(f"{name}: pred {fmt(pred)}  real {fmt(pole)}  err {err:+.2f}%  {verdict}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    if a[0] == "--backtest":
        backtest()
    elif a[0] == "--score":
        score(a[1])
    else:
        predict(a[0])
