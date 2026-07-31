import argparse
import os

import fastf1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int)
    parser.add_argument("--gp", type=str)
    parser.add_argument("--session", type=str)
    parser.add_argument("--driver", type=str)
    args = parser.parse_args()

    os.makedirs("data/fastf1_cache", exist_ok=True)
    fastf1.Cache.enable_cache("data/fastf1_cache")

    session = fastf1.get_session(args.year, args.gp, args.session)
    session.load()

    lap = session.laps.pick_drivers(args.driver).pick_fastest()
    tel = lap.get_telemetry()

    os.makedirs("data/telemetry", exist_ok=True)
    path = f"data/telemetry/{args.year}_{args.gp}_{args.driver}_{args.session}.csv"

    columns = ["Time", "Distance", "Speed", "Throttle", "Brake", "nGear", "X", "Y"]
    tel.to_csv(path, columns=columns, index=False)

    print(f"Telemetry saved to {path}")
    print(f"Rows: {len(tel)}")


if __name__ == "__main__":
    main()
