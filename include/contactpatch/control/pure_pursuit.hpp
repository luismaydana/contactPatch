#pragma once

#include "contactpatch/core/types.hpp"
#include "contactpatch/physics/batch_vehicle.hpp"
#include "contactpatch/track/centerline_track.hpp"

namespace contactpatch{
namespace control {

struct PurePursuitConfig {
    Real wheelbase_m = 3.40f;
    Real lookahead_min_m = 5.0f;
    Real lookahead_gain_s = 0.5f;
    Real mu_effective = 1.0f;
    Real tire_mu_d1 = 1.8f;
    Real tire_mu_d2 = -0.17f;
    Real tire_fz0_n = 2000.0f;
    Real gravity_m_s2 = 9.81f;
    Real v_min_mps = 8.0f;
    Real v_max_mps = 100.0f;
    Real kp_accel = 0.3f;
    Real kp_brake = 0.35f;
    Real speed_lookahead_m = 50.0f;
    Real max_steer_rad = 0.40f;
    Real max_steer_rate_rad_s = 2.5f;
    Real cl_downforce_z = 5.0f;
    Real cl_downforce_x = 1.0f;
    Real air_density = 1.225f;
    Real frontal_area_m2 = 1.5f;
    Real mass_kg = 768.0f;
    Real grip_safety_factor = 0.85f;
    Real k_yaw_damp = 0.25f;
    Real max_brake_force_n = 38000.0f;
    Real tire_temp_opt_c = 95.0f;
    Real tire_temp_sigma = 30.0f;
    Real drive_force_n = 12000.0f;
    Real cd_z = 1.0f;
    Real cd_x = 0.6f;
    Real ge_max = 2.0f;
    Real ge_v_ref_mps = 40.0f;
    const Real* margin_s_m = nullptr;
    const Real* margin_value = nullptr;
    int margin_count = 0;
};

struct PurePursuitState {
    Real last_steering_rad = 0.0f;
    Real last_throttle = 0.0f;
    bool initialized = false;
};
physics::BatchInputs compute_pure_pursuit_inputs(const PurePursuitConfig& config,PurePursuitState& state,const physics::BatchVehicleState& vehicle_state,const track::CenterlineTrack& track,Real dt);
}
}
