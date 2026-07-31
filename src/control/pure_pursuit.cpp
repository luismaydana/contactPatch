#include "contactpatch/control/pure_pursuit.hpp"

#include <algorithm>
#include <cmath>

namespace contactpatch {
namespace control{

physics::BatchInputs compute_pure_pursuit_inputs(const PurePursuitConfig& config,PurePursuitState& state,const physics::BatchVehicleState& vehicle_state,const track::CenterlineTrack& track,Real dt){
    physics::BatchInputs inputs{};

    if (track.points().size() < 2) {
        return inputs;
    }

    const Real track_length = track.get_total_length();
    if (track_length < 1e-3f) {
        return inputs;
    }

    const Real v_long = vehicle_state.v_long_mps;
    const Real Ld = std::max(
        config.lookahead_min_m,
        config.lookahead_min_m + config.lookahead_gain_s * v_long);

    const Real s_target = vehicle_state.s_arc_m + Ld;
    const track::CenterlinePoint target = track.sample_at_s(s_target);

    const Real dx = target.x_m - vehicle_state.x_m;
    const Real dy = target.y_m - vehicle_state.y_m;
    const Real cos_y = std::cos(vehicle_state.yaw_rad);
    const Real sin_y = std::sin(vehicle_state.yaw_rad);
    const Real local_x = dx * cos_y + dy * sin_y;
    const Real local_y = -dx * sin_y + dy * cos_y;
    const Real alpha = std::atan2(local_y, local_x);
    const Real delta = std::atan2(2.0f * config.wheelbase_m * std::sin(alpha), Ld);
    Real steer_cmd = std::clamp(delta, -config.max_steer_rad, config.max_steer_rad);

    if (state.initialized && dt > 0.0f){
        const Real max_delta = config.max_steer_rate_rad_s * dt;
        const Real change = std::clamp(steer_cmd - state.last_steering_rad, -max_delta, max_delta);
        steer_cmd = state.last_steering_rad + change;
    }
    state.last_steering_rad = steer_cmd;
    state.initialized = true;

    const Real yaw_expected = v_long * std::tan(steer_cmd)
                            / std::max(config.wheelbase_m, 1e-3f);
    const Real yaw_excess = vehicle_state.yaw_rate_rps - yaw_expected;
    const Real counter = std::clamp(-config.k_yaw_damp * yaw_excess, -0.15f, 0.15f);
    inputs.steering_rad = std::clamp(steer_cmd + counter,
                                     -config.max_steer_rad, config.max_steer_rad);

    Real t_avg = 0.0f;
    for (int w = 0; w < 4; ++w) t_avg += vehicle_state.tire_temp_c[w];
    t_avg *= 0.25f;
    const Real t_diff = (t_avg - config.tire_temp_opt_c) / std::max(config.tire_temp_sigma, 1e-3f);
    const Real thermal = std::max(0.5f, std::exp(-t_diff * t_diff));

    const Real cl_now = (vehicle_state.current_aero_mode == physics::AeroMode::X_MODE)
        ? config.cl_downforce_x
        : config.cl_downforce_z;

    const auto margin_at = [&](Real s_pos) -> Real {
        if (config.margin_count < 2 || config.margin_s_m == nullptr
            || config.margin_value == nullptr) {
            return config.grip_safety_factor;
        }
        Real sw = std::fmod(s_pos, track_length);
        if (sw < 0.0f) sw += track_length;
        const Real* beg = config.margin_s_m;
        const Real* end_p = beg + config.margin_count;
        const int j = static_cast<int>(std::upper_bound(beg, end_p, sw) - beg);
        const int i0 = (j == 0) ? config.margin_count - 1 : j - 1;
        const int i1 = (j == config.margin_count) ? 0 : j;
        const Real s0 = config.margin_s_m[i0];
        Real seg = config.margin_s_m[i1] - s0;
        if (seg <= 0.0f) seg += track_length;
        Real ds = sw - s0;
        if (ds < 0.0f) ds += track_length;
        const Real w = (seg > 1e-6f) ? std::min(ds / seg, 1.0f) : 0.0f;
        return config.margin_value[i0]
             + w * (config.margin_value[i1] - config.margin_value[i0]);
    };

    const auto a_max_of = [&](Real v, Real cl, Real s_pos) -> Real {
        const Real v_ref2 = config.ge_v_ref_mps * config.ge_v_ref_mps;
        const Real ge = 1.0f + (config.ge_max - 1.0f) * (v * v) / (v * v + v_ref2);
        const Real df = 0.5f * config.air_density * cl * config.frontal_area_m2 * v * v * ge;
        const Real wheel_load = (config.mass_kg * config.gravity_m_s2 + df) * 0.25f;
        const Real dfz = (wheel_load - config.tire_fz0_n) / std::max(config.tire_fz0_n, 1.0f);
        const Real mu = std::max(config.tire_mu_d1 + config.tire_mu_d2 * dfz, 0.3f)
                      * thermal * config.mu_effective;
        const Real mg = margin_at(s_pos);
        return mu * (config.mass_kg * config.gravity_m_s2 + df) / std::max(config.mass_kg, 1e-3f)
             * mg * mg;
    };

    const auto corner_speed = [&](Real kappa, Real s_pos) -> Real {
        const Real k = std::max(std::abs(kappa), 1e-5f);
        Real v = 25.0f;
        for (int it = 0; it < 12; ++it) {
            const Real v_new = std::sqrt(a_max_of(v, config.cl_downforce_z, s_pos) / k);
            v = 0.5f * (v + std::min(v_new, config.v_max_mps));
        }
        return std::min(v, config.v_max_mps);
    };

    const Real a_max_now = a_max_of(v_long, cl_now, vehicle_state.s_arc_m);

    constexpr Real kSeg_m = 12.0f;
    constexpr int kMaxSeg = 64;
    int n_seg = static_cast<int>(config.speed_lookahead_m / kSeg_m);
    if (n_seg < 2) n_seg = 2;
    if (n_seg > kMaxSeg) n_seg = kMaxSeg;

    Real kappa_seg[kMaxSeg];
    for (int i = 0; i < n_seg; ++i) {
        kappa_seg[i] = track.max_curvature_in_range(
            vehicle_state.s_arc_m + static_cast<Real>(i) * kSeg_m, kSeg_m);
    }

    Real v_allow_seg[kMaxSeg];
    Real v_allow = corner_speed(kappa_seg[n_seg - 1],
                                vehicle_state.s_arc_m + static_cast<Real>(n_seg - 1) * kSeg_m);
    v_allow_seg[n_seg - 1] = v_allow;
    for (int i = n_seg - 2; i >= 0; --i) {
        const Real s_next = vehicle_state.s_arc_m + static_cast<Real>(i + 1) * kSeg_m;
        const Real a_max = a_max_of(v_allow, cl_now, s_next);
        const Real a_lat = v_allow * v_allow * std::abs(kappa_seg[i + 1]);
        const Real r = std::min(1.0f, a_lat / std::max(a_max, 1e-3f));
        const Real a_long = a_max * std::sqrt(std::max(0.0f, 1.0f - r * r));
        const Real v_braked = std::sqrt(v_allow * v_allow + 2.0f * a_long * kSeg_m);
        v_allow = std::min(corner_speed(kappa_seg[i],
                                        vehicle_state.s_arc_m + static_cast<Real>(i) * kSeg_m),
                           v_braked);
        v_allow_seg[i] = v_allow;
    }

    Real v_target = std::clamp(v_allow_seg[0], config.v_min_mps, config.v_max_mps);

    const Real cd_now = (vehicle_state.current_aero_mode == physics::AeroMode::X_MODE)
        ? config.cd_x
        : config.cd_z;
    const Real drag_n = 0.5f * config.air_density * cd_now * config.frontal_area_m2
                      * v_long * v_long;
    const Real f_drive_cap = (vehicle_state.drive_force_capacity_n > 1.0f)
        ? vehicle_state.drive_force_capacity_n
        : config.drive_force_n;
    const Real thr_hold = drag_n / std::max(f_drive_cap, 1.0f);

    const Real error = v_target - v_long;
    if (v_long < config.v_min_mps){
        inputs.brake = 0.0f;
        inputs.throttle = std::clamp(
            config.kp_accel * (std::max(v_target, config.v_min_mps) - v_long), 0.0f, 1.0f);
    } else if (error > 0.0f){
        inputs.throttle = std::clamp(
            std::max(config.kp_accel * error, std::min(thr_hold, 1.0f)), 0.0f, 1.0f);
        inputs.brake = 0.0f;
    } else {
        inputs.throttle = 0.0f;
        const Real v_lim_next = std::min(v_allow_seg[1], config.v_max_mps);
        Real brake_cmd = 0.0f;
        if (v_long > v_lim_next) {
            Real a_req = 0.0f;
            for (int i = 1; i < n_seg; ++i) {
                const Real v_gate = std::min(v_allow_seg[i], config.v_max_mps);
                if (v_long > v_gate) {
                    const Real need = (v_long * v_long - v_gate * v_gate)
                                    / (2.0f * static_cast<Real>(i) * kSeg_m);
                    a_req = std::max(a_req, need);
                }
            }
            brake_cmd = a_req * config.mass_kg / std::max(config.max_brake_force_n, 1.0f);
        }
        brake_cmd += config.kp_brake * 0.1f * (-error);
        constexpr Real fade_band_mps = 8.0f;
        if (v_long < config.v_min_mps + fade_band_mps) {
            const Real t = (v_long - config.v_min_mps) / fade_band_mps;
            brake_cmd *= std::clamp(t, 0.0f, 1.0f);
        }
        inputs.brake = std::clamp(brake_cmd, 0.0f, 1.0f);
    }

    if (inputs.brake > 0.0f) {
        const Real a_lat_now = std::abs(v_long * vehicle_state.yaw_rate_rps);
        const Real lat_r = std::min(1.0f, a_lat_now / std::max(a_max_now, 1.0f));
        inputs.brake *= std::sqrt(std::max(0.0f, 1.0f - lat_r * lat_r));
        const Real min_slip = std::min(
            std::min(vehicle_state.wheel_slip_ratio[0], vehicle_state.wheel_slip_ratio[1]),
            std::min(vehicle_state.wheel_slip_ratio[2], vehicle_state.wheel_slip_ratio[3]));
        if (min_slip < -0.10f) {
            const Real cut = std::clamp(1.0f - (-min_slip - 0.10f) * 8.0f, 0.10f, 1.0f);
            inputs.brake *= cut;
        }
    }

    const Real rear_slip = std::max(vehicle_state.wheel_slip_ratio[2],
                                    vehicle_state.wheel_slip_ratio[3]);
    if (rear_slip > 0.20f && inputs.throttle > 0.0f) {
        const Real cut = std::clamp(1.0f - (rear_slip - 0.20f) * 5.0f, 0.3f, 1.0f);
        inputs.throttle *= cut;
    }

    if (inputs.throttle > 0.0f) {
        const Real a_lat_now = std::abs(v_long * vehicle_state.yaw_rate_rps);
        const Real a_budget = a_max_of(v_long, config.cl_downforce_z, vehicle_state.s_arc_m);
        const Real r_lat = std::min(1.0f, a_lat_now / std::max(a_budget, 1.0f));
        const Real a_long_avail = a_budget * std::sqrt(std::max(0.0f, 1.0f - r_lat * r_lat));
        const Real thr_ceiling = (config.mass_kg * a_long_avail + drag_n)
                               / std::max(f_drive_cap, 1.0f);
        inputs.throttle = std::min(inputs.throttle,
                                   std::clamp(thr_ceiling, 0.15f, 1.0f));
    }

    const Real beta = std::atan2(std::abs(vehicle_state.v_lat_mps),
                                 std::max(std::abs(v_long), 1.0f));
    if (beta > 0.13f) {
        const Real hold = std::clamp(1.0f - (beta - 0.13f) * 10.0f, 0.0f, 1.0f);
        inputs.throttle *= hold;
        inputs.brake *= hold;
    }

    state.last_throttle = inputs.throttle;

    inputs.ers_override = (inputs.throttle > 0.5f && v_long > 25.0f
                           && rear_slip < 0.18f
                           && vehicle_state.battery_soc > 0.05f);

    return inputs;
}

}
}
