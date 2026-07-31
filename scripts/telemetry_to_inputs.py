import pandas as pd
import numpy as np
import argparse

def main():
    parser = argparse.ArgumentParser(description="FastF1 telemetry to simulation input translator")
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    df_out = pd.DataFrame()
    df_out["time_s"] = pd.to_timedelta(df["Time"]).dt.total_seconds()
    df_out["throttle"] = (df["Throttle"] / 100.0).clip(0.0, 1.0)
    df_out["brake"] = df["Brake"].astype(float)
    df_out["distance_m"] = df["Distance"]
    df_out["speed_ref_mps"] = df["Speed"] / 3.6

    x_m = (df["X"] / 10.0).to_numpy()
    y_m = (df["Y"] / 10.0).to_numpy()
    n = len(df)
    steering_rad = np.zeros(n)

    if n > 2:
        ax, ay = x_m[:-2], y_m[:-2]
        bx, by = x_m[1:-1], y_m[1:-1]
        cx, cy = x_m[2:], y_m[2:]

        ab_x, ab_y = bx - ax, by - ay
        bc_x, bc_y = cx - bx, cy - by
        ac_x, ac_y = cx - ax, cy - ay
        cross_product = (ab_x * ac_y) - (ab_y * ac_x)

        norm_ab = np.hypot(ab_x, ab_y)
        norm_bc = np.hypot(bc_x, bc_y)
        norm_ca = np.hypot(ac_x, ac_y)

        denominador = norm_ab * norm_bc * norm_ca
        kappa = np.zeros_like(cross_product)
        safe_mask = denominador > 1e-6

        kappa[safe_mask] = (2.0 * cross_product[safe_mask]) / denominador[safe_mask]
        steering_rad[1:-1] = np.arctan(3.40 * kappa)

    df_out["steering_rad"] = steering_rad

    final_columns = ["time_s", "throttle", "brake", "steering_rad", "distance_m", "speed_ref_mps"]
    df_out = df_out[final_columns]
    df_out.to_csv(args.output, index=False)
    print(f"Successfully generated inputs in: {args.output}")
    print(f"Total rows processed: {len(df_out)}")

if __name__ == "__main__":
    main()
