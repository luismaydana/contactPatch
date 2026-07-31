"""pull every driver's fastest qualifying lap at suzuka from the cached
fastf1 session, run the qss predictor on each, and write one csv with the
per-driver model error so the whole grid can be compared at once.
"""
import os
import fastf1
import pandas as pd
import qss_laptime as qss
import ers_dp

YEAR = 2026
GP = "Japan"
SESSION = "Q"
TEL_COLS = ["Time", "Distance", "Speed", "Throttle", "Brake", "nGear", "X", "Y"]


def driver_info(results, drv):
    try:
        row = results.loc[drv]
        return str(row["Abbreviation"]), str(row["TeamName"]), row.get("Position", None)
    except Exception:
        return str(drv), "?", None


def main():
    os.makedirs("data/fastf1_cache", exist_ok=True)
    fastf1.Cache.enable_cache("data/fastf1_cache")

    s = fastf1.get_session(YEAR, GP, SESSION)
    s.load()
    results = s.results

    os.makedirs("data/telemetry/field", exist_ok=True)
    rows = []

    for drv in s.drivers:
        abbr, team, pos = driver_info(results, drv)
        lap = s.laps.pick_drivers(drv).pick_fastest()
        if lap is None or pd.isnull(lap["LapTime"]):
            print(f"skip {abbr}: no valid fastest lap")
            continue
        try:
            tel = lap.get_telemetry()
        except Exception as e:
            print(f"skip {abbr}: telemetry error ({e})")
            continue

        path = f"data/telemetry/field/{YEAR}_{GP}_{abbr}_{SESSION}.csv"
        tel.to_csv(path, columns=TEL_COLS, index=False)

        df = pd.read_csv(path)
        if len(df) < 20:
            print(f"skip {abbr}: only {len(df)} telemetry points")
            continue
        try:
            mp = qss.compute_metrics(df, tire="pacejka")
            dp = ers_dp.dp_optimize(mp, tire="pacejka")
        except Exception as e:
            print(f"skip {abbr}: qss failed ({e})")
            continue

        t_dp = dp["t_dp"]
        err_dp = 100.0 * (t_dp - mp["t_real"]) / mp["t_real"]
        rows.append({
            "driver": abbr,
            "team": team,
            "grid_pos": pos,
            "real_lap_s": round(mp["t_real"], 3),
            "qss_dp_s": round(t_dp, 3),
            "err_pct": round(err_dp, 2),
            "qss_greedy_s": round(mp["t_sim"], 3),
            "err_greedy_pct": round(mp["err_ers"], 2),
            "top_sim_mps": round(mp["top_sim"], 1),
            "top_real_mps": round(mp["top_real"], 1),
            "rmse_mps": round(mp["rmse"], 2),
            "lap_dist_m": round(float(mp["dist"].max()), 0),
        })
        print(f"{abbr:4s} {team:20s} real {mp['t_real']:7.3f}  "
              f"dp {t_dp:7.3f} ({err_dp:+5.2f}%)  "
              f"greedy {mp['t_sim']:7.3f} ({mp['err_ers']:+5.2f}%)")

    if not rows:
        print("no drivers processed")
        return

    out = pd.DataFrame(rows).sort_values("real_lap_s").reset_index(drop=True)
    med_dist = out["lap_dist_m"].median()
    out["clean"] = ((out["lap_dist_m"] - med_dist).abs() / med_dist) < 0.025

    os.makedirs("data/sim_results", exist_ok=True)
    csv_path = "data/sim_results/suzuka_field_qss.csv"
    out.to_csv(csv_path, index=False)
    print(f"\nwrote {csv_path} ({len(out)} drivers)")

    excluded = out[~out["clean"]]["driver"].tolist()
    if excluded:
        print(f"excluded (telemetry distance off median by >2.5%): {excluded}")

    for model, col in [("dp", "err_pct"), ("greedy", "err_greedy_pct")]:
        for label, sub in [("all", out), ("clean", out[out["clean"]])]:
            e = sub[col]
            print(f"{model:10s} {label:6s} n={len(sub):2d}  err% mean {e.mean():+.2f}  "
                  f"median {e.median():+.2f}  std {e.std():.2f}  range {e.min():+.2f} to {e.max():+.2f}")

    plot_field(out)


def plot_field(out):
    import matplotlib.pyplot as plt
    d = out.sort_values("err_pct")
    colors = []
    for clean, e in zip(d["clean"], d["err_pct"]):
        if not clean:
            colors.append("#bbbbbb")
        elif e < 0:
            colors.append("#2ca02c")
        else:
            colors.append("#1f77b4")
    plt.figure(figsize=(11, 8))
    plt.barh(d["driver"], d["err_pct"], color=colors)
    m = d[d["clean"]]["err_pct"].mean()
    plt.axvline(m, color="black", linestyle="--", linewidth=1.2, label=f"clean mean {m:+.2f}%")
    plt.axvline(0, color="gray", linewidth=0.8)
    plt.gca().invert_yaxis()
    plt.xlabel("QSS lap-time error vs real (%)")
    plt.title("contactPatch QSS vs 2026 Suzuka qualifying field (calibrated tires, DP ERS)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("data/sim_results/suzuka_field_error.png", dpi=150)
    print("saved data/sim_results/suzuka_field_error.png")


if __name__ == "__main__":
    main()
