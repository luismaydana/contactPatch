#pragma once

#include <cmath>
#include <fstream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#include "contactpatch/control/pure_pursuit.hpp"
#include "contactpatch/sim/batch_simulator.hpp"

namespace contactpatch {
namespace lap {

inline Real load_initial_speed(const std::string& inputs_csv) {
    std::ifstream file(inputs_csv);
    if (!file.is_open()) {
        return 80.0f;
    }
    std::string line;
    std::getline(file, line);
    if (!std::getline(file, line) || line.empty()) {
        return 80.0f;
    }
    std::stringstream ss(line);
    std::string cell;
    for (int i = 0; i < 6; ++i) {
        std::getline(ss, cell, ',');
    }
    return std::stof(cell);
}

inline physics::BatchVehicleState make_flying_start(const physics::BatchVehicleConfig& cfg,
                                                    const track::CenterlineTrack& track,
                                                    Real v0) {
    physics::BatchVehicleState st{};
    const auto& pts = track.points();
    st.x_m = pts[0].x_m;
    st.y_m = pts[0].y_m;
    st.yaw_rad = std::atan2(pts[1].y_m - pts[0].y_m, pts[1].x_m - pts[0].x_m);
    st.v_long_mps = v0;
    for (int w = 0; w < 4; ++w) {
        st.wheel_omega_rad_s[w] = v0 / cfg.wheel_radius_m;
        st.tire_temp_c[w] = cfg.tire_temp_opt_c;
    }
    st.current_gear = 8;
    for (int g = 8; g >= 1; --g) {
        const Real rpm0 = (v0 / cfg.wheel_radius_m) * cfg.gear_ratios[g - 1]
                        * (60.0f / 6.2831853f);
        if (rpm0 <= 11000.0f) {
            st.current_gear = g;
        }
    }
    return st;
}

inline control::PurePursuitConfig make_pp_config(const physics::BatchVehicleConfig& cfg) {
    control::PurePursuitConfig pp{};
    pp.lookahead_min_m = 9.0f;
    pp.lookahead_gain_s = 0.6f;
    pp.mu_effective = 1.0f;
    pp.v_max_mps = 92.0f;
    pp.speed_lookahead_m = 300.0f;
    pp.kp_accel = 1.2f;
    pp.kp_brake = 0.8f;
    pp.cl_downforce_z = 5.0f;
    pp.air_density = cfg.aero.air_density;
    pp.frontal_area_m2 = cfg.aero.frontal_area;
    pp.mass_kg = cfg.mass_kg;
    pp.max_brake_force_n = cfg.max_brake_force_n;
    pp.grip_safety_factor = 0.88f;
    pp.k_yaw_damp = 0.25f;
    pp.cd_z = cfg.aero.cd_z;
    pp.cd_x = cfg.aero.cd_x;
    return pp;
}

inline std::vector<std::pair<Real, Real>> load_ers_windows(const std::string& csv_path,
                                                           Real track_len) {
    std::vector<std::pair<Real, Real>> windows;
    std::ifstream sched(csv_path);
    if (!sched.is_open()) {
        return windows;
    }
    std::string line;
    std::getline(sched, line);
    while (std::getline(sched, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string cell;
        std::getline(ss, cell, ',');
        const Real a = std::stof(cell) * track_len;
        std::getline(ss, cell, ',');
        const Real b = std::stof(cell) * track_len;
        windows.emplace_back(a, b);
    }
    return windows;
}

inline bool ers_scheduled(const std::vector<std::pair<Real, Real>>& windows, Real s_now) {
    for (const auto& w : windows) {
        if (s_now >= w.first && s_now <= w.second) {
            return true;
        }
    }
    return false;
}

inline void load_margin_schedule(const std::string& csv_path,
                                 std::vector<Real>& s_out,
                                 std::vector<Real>& m_out) {
    std::ifstream file(csv_path);
    if (!file.is_open()) {
        return;
    }
    std::string line;
    std::getline(file, line);
    while (std::getline(file, line)) {
        if (line.empty()) continue;
        std::stringstream ss(line);
        std::string cell;
        std::getline(ss, cell, ',');
        s_out.push_back(std::stof(cell));
        std::getline(ss, cell, ',');
        m_out.push_back(std::stof(cell));
    }
}

}
}
