import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sim", required=True)
    parser.add_argument("--real", required=True)
    args = parser.parse_args()

    sim_df = pd.read_csv(args.sim)
    real_df = pd.read_csv(args.real)

    sim_df['ds'] = sim_df['s_arc_m'].diff()
    sim_df.loc[0, 'ds'] = 1.0 

    anomaly_mask = (sim_df['v_long_mps'] < 0.0) | (sim_df['ds'] <= 0.0)
    
    if anomaly_mask.any():
        cutoff_idx = anomaly_mask.idxmax()
        sim_df = sim_df.iloc[:cutoff_idx]
    s_arc_max = sim_df['s_arc_m'].max()
    
    grid = np.arange(0.0, s_arc_max, 10.0)
    
    v_sim = np.interp(grid, sim_df['s_arc_m'], sim_df['v_long_mps'])
    v_real = np.interp(grid, real_df['distance_m'], real_df['speed_ref_mps'])
    
    rmse_mps = np.sqrt(np.mean((v_sim - v_real)**2))
    rmse_kmh = rmse_mps * 3.6
    mean_err_mps = np.mean(v_sim - v_real)
    max_diff_mps = np.max(np.abs(v_sim - v_real))
    
    print("=== Telemetry Validation Report ===")
    print(f"Valid simulation distance: {s_arc_max:.2f} m")
    print(f"Data points compared:      {len(grid)}")
    print(f"RMSE:{rmse_mps:.3f} m/s ({rmse_kmh:.2f} km/h)")
    print(f"Mean Error (Sim - Real):   {mean_err_mps:.3f} m/s")
    print(f"Max Absolute Difference:   {max_diff_mps:.3f} m/s")
    
    plt.figure(figsize=(14, 6))
    plt.plot(grid, v_real, label="Real (VER)", color="#1f77b4", linewidth=2.5)
    plt.plot(grid, v_sim, label="Simulation (Pure Pursuit)", color="#ff7f0e", linestyle="--", linewidth=2.0)
    
    plt.xlabel("Distance along centerline [m]", fontsize=12)
    plt.ylabel("Longitudinal Velocity [m/s]", fontsize=12)
    plt.title("Closed-Loop Validation: Simulated vs Real Velocity Profile", fontsize=14)
    plt.grid(True, linestyle=":", alpha=0.7)
    plt.legend(fontsize=12)
    
    output_img = "data/sim_results/speed_comparison.png"
    plt.tight_layout()
    plt.savefig(output_img, dpi=300)
    plt.close()
    
    print(f"\nPlot saved successfully to: {output_img}")

if __name__ == "__main__":
    main()