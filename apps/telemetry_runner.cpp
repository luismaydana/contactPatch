#include <cstdio>
#include <fstream>
#include <vector>
#include <string>
#include <cmath>
#include <sstream>
#include <algorithm>
#include <filesystem>

#include "contactpatch/sim/batch_simulator.hpp"
#include "contactpatch/control/pure_pursuit.hpp"
#include "lap_common.hpp"

using namespace contactpatch;
using namespace contactpatch::physics;
using namespace contactpatch::sim;
using namespace contactpatch::control;

struct InputRow {
    Real time_s;
    Real throttle;
    Real brake;
    Real steering_rad;
    Real distance_m;
    Real speed_ref_mps;
};

std::vector<InputRow> load_telemetry_inputs(const std::string& filepath) {
    std::vector<InputRow> rows;
    std::ifstream file(filepath);

    if (!file.is_open()) {
        std::printf("Cannot open the telemetry file: %s\n", filepath.c_str());
        return rows;
    }

    std::string line;
    std::getline(file, line);

    while (std::getline(file, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string cell;
        InputRow row;

        std::getline(ss, cell, ','); row.time_s = std::stof(cell);
        std::getline(ss, cell, ','); row.throttle = std::stof(cell);
        std::getline(ss, cell, ','); row.brake = std::stof(cell);
        std::getline(ss, cell, ','); row.steering_rad = std::stof(cell);
        std::getline(ss, cell, ','); row.distance_m = std::stof(cell);
        std::getline(ss, cell, ','); row.speed_ref_mps = std::stof(cell);

        rows.push_back(row);
    }

    std::printf("CSV loaded. Total rows: %zu\n", rows.size());
    return rows;
}

BatchInputs inputs_at(const std::vector<InputRow>& rows, Real t) {
    BatchInputs out{};
    if (rows.empty()) return out;

    if (t <= rows.front().time_s) {
        out.throttle = rows.front().throttle;
        out.brake = rows.front().brake;
        out.steering_rad = rows.front().steering_rad;
        return out;
    }
    if (t >= rows.back().time_s) {
        out.throttle = rows.back().throttle;
        out.brake = rows.back().brake;
        out.steering_rad = rows.back().steering_rad;
        return out;
    }

    auto it = std::upper_bound(rows.begin(), rows.end(), t, [](Real value, const InputRow& row) {
        return value < row.time_s;
    });
    const auto& next_row = *it;
    const auto& prev_row = *(it - 1);

    Real delta_t = next_row.time_s - prev_row.time_s;
    Real factor = (t - prev_row.time_s) / (delta_t > 0.0f ? delta_t : 1.0f);

    out.throttle = prev_row.throttle + factor * (next_row.throttle - prev_row.throttle);
    out.brake = prev_row.brake + factor * (next_row.brake - prev_row.brake);
    out.steering_rad = prev_row.steering_rad + factor * (next_row.steering_rad - prev_row.steering_rad);

    return out;
}

int main(int argc, char** argv) {
    (void)argc;
    (void)argv;

    BatchSimulator sim;

    std::string track_path = std::string(CONTACTPATCH_DATA_DIR) + "/tracks/suzuka/raceline_ver.csv";
    sim.load_track(track_path);

    std::string telemetry_path = std::string(CONTACTPATCH_DATA_DIR) + "/telemetry/2026_Japan_VER_Q_inputs.csv";
    auto rows = load_telemetry_inputs(telemetry_path);

    if (rows.empty()) {
        std::printf("Critical error: The input vector is empty. Aborting.\n");
        return 1;
    }

    const auto& pts = sim.get_track().points();
    if (pts.size() < 2) {
        std::printf("Critical error: The track does not contain enough geometric points.\n");
        return 1;
    }

    BatchVehicleConfig cfg{};
    BatchVehicleState st = lap::make_flying_start(cfg, sim.get_track(),
                                                  rows.front().speed_ref_mps);
    sim.initialize(cfg, st);

    PurePursuitConfig pp_cfg = lap::make_pp_config(cfg);

    std::vector<Real> margin_s;
    std::vector<Real> margin_v;
    lap::load_margin_schedule(
        std::string(CONTACTPATCH_DATA_DIR) + "/sim_results/margin_schedule.csv",
        margin_s, margin_v);
    if (margin_s.size() >= 2) {
        pp_cfg.margin_s_m = margin_s.data();
        pp_cfg.margin_value = margin_v.data();
        pp_cfg.margin_count = static_cast<int>(margin_s.size());
        std::printf("Margin schedule loaded: %zu knots.\n", margin_s.size());
    }

    PurePursuitState pp_state{};

    const std::vector<std::pair<Real, Real>> ers_windows = lap::load_ers_windows(
        std::string(CONTACTPATCH_DATA_DIR) + "/sim_results/ers_schedule.csv",
        sim.get_track().get_total_length());
    if (!ers_windows.empty()) {
        std::printf("ERS schedule loaded: %zu deploy windows.\n", ers_windows.size());
    }

    std::string output_dir = "data/sim_results";
    std::filesystem::create_directories(output_dir);
    std::string output_file = output_dir + "/2026_Japan_VER_Q_sim.csv";

    std::ofstream out(output_file);
    if (!out.is_open()) {
        std::printf("Critical error: Could not create output file at: %s\n", output_file.c_str());
        return 1;
    }

    out << "time_s,s_arc_m,v_long_mps,x_m,y_m,yaw_rad,"
        << "tire_temp_fl,tire_temp_fr,tire_temp_rl,tire_temp_rr,"
        << "battery_soc,"
        << "fz_fl,fz_fr,fz_rl,fz_rr,"
        << "throttle,brake,gear,aero_x,ers_deploy\n";

    const Real dt = 0.01f;
    int rows_written = 0;
    const int max_steps = 20000;
    Real final_sim_time = 0.0f;

    for (int i = 0; i < max_steps; ++i) {
        Real t = i * dt;

        BatchInputs in = compute_pure_pursuit_inputs(pp_cfg, pp_state, sim.get_state(), sim.get_track(), dt);

        if (!ers_windows.empty()) {
            in.ers_override = in.ers_override
                && lap::ers_scheduled(ers_windows, sim.get_state().s_arc_m);
        }

        sim.step(in, dt);

        const auto& s = sim.get_state();
        out << t << ","
            << s.s_arc_m << ","
            << s.v_long_mps << ","
            << s.x_m << ","
            << s.y_m << ","
            << s.yaw_rad << ","
            << s.tire_temp_c[0] << "," << s.tire_temp_c[1] << ","
            << s.tire_temp_c[2] << "," << s.tire_temp_c[3] << ","
            << s.battery_soc << ","
            << s.wheel_fz_n[0] << "," << s.wheel_fz_n[1] << ","
            << s.wheel_fz_n[2] << "," << s.wheel_fz_n[3] << ","
            << in.throttle << "," << in.brake << "," << s.current_gear << ","
            << (s.current_aero_mode == AeroMode::X_MODE ? 1 : 0) << ","
            << (s.ers_boost_torque_per_rear_n_m > 0.0f ? 1 : 0) << "\n";

        rows_written++;
        final_sim_time = t;

        if (sim.lap_state().lap_count >= 1) {
            break;
        }
    }

    std::printf("Simulation successfully completed.\n");
    std::printf("Results saved: %s\n", output_file.c_str());
    std::printf("Total rows written: %d | Lap time: %.3f s\n", rows_written, final_sim_time);

    return 0;
}
