#pragma once

#include "contactpatch/core/types.hpp"
#include "contactpatch/physics/aero.hpp"
#include "contactpatch/physics/tire_pacejka.hpp"

namespace contactpatch{
namespace physics{
enum BatchWheelIndex{BATCH_WHEEL_FL = 0, BATCH_WHEEL_FR = 1, BATCH_WHEEL_RL = 2, BATCH_WHEEL_RR = 3 };

struct BatchInputs{
    Real throttle = 0.0f;
    Real brake =0.0f;
    Real steering_rad = 0.0f;
    bool ers_override = false;
};

struct BatchVehicleConfig{
    Real mass_kg = 768.0f;
    Real izz_kg_m2 = 800.0f;
    Real wheelbase_m = 3.40f;
    Real wheel_radius_m = 0.35f;
    Real wheel_inertia_kg_m2 = 1.5f;
    Real max_brake_force_n = 38000.0f;
    Real max_steer_rad = 0.40f;
    Real brake_bias_front = 0.58f;

    Real engine_max_torque_nm = 380.0f;
    Real engine_max_power_w = 400000.0f;
    Real engine_rev_limit_rpm = 12000.0f;
    Real shift_up_rpm = 11400.0f;
    Real shift_down_rpm = 8200.0f;
    Real gear_ratios[8] = {13.8f, 11.7f, 9.95f, 8.45f, 7.18f, 6.10f, 5.18f, 4.40f};

    Real lsd_preload_nm = 50.0f;
    Real lsd_locking_coeff = 0.5f;
    Real tire_temp_opt_c = 95.0f;
    Real tire_temp_sigma = 30.0f;
    Real heat_coeff_slip = 4.75e-5f;
    Real cool_coeff = 0.01f;
    Real ambient_temp_c = 30.0f;
    Real ride_height_opt_m = 0.040f;
    Real mguk_max_power_w = 350000.0f;
    Real mguk_deploy_efficiency = 0.92f;
    Real regen_efficiency = 0.7f;
    Real battery_capacity_j = 4000000.0f;
    Real mguk_taper_start_mps = 80.56f;
    Real mguk_taper_end_mps = 98.61f;

    Real cog_height_m = 0.30f;
    Real weight_dist_front = 0.455f;
    Real track_front_m = 1.55f;
    Real track_rear_m = 1.50f;
    Real gravity_m_s2 = 9.81f;

    PacejkaConfig front_tires{};
    PacejkaConfig rear_tires{};

    Vec3 wheel_pos[4] ={
        Vec3(1.70f, 0.775f, -0.15f),
        Vec3(1.70f, -0.775f, -0.15f),
        Vec3(-1.70f, 0.75f, -0.15f),
        Vec3(-1.70f, -0.75f, -0.15f),
    };

    AeroConfig aero{
        1.5f,
        1.225f,
        1.0f,
        -5.0f,
        0.6f,
        -1.0f,
        Vec3(-0.05f, 0.0f, 0.0f),
        Vec3(0.0f, 0.0f, 0.0f),
    };
};

struct BatchVehicleState{
    Real s_arc_m = 0.0f;
    Real lateral_offset_m = 0.0f;
    Real track_heading_rad = 0.0f;
    Real x_m = 0.0f;
    Real y_m = 0.0f;
    Real yaw_rad = 0.0f;
    Real v_long_mps = 0.0f;
    Real v_lat_mps = 0.0f;
    Real yaw_rate_rps = 0.0f;

    Real wheel_omega_rad_s[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    Real wheel_v_local_x[4] = {};
    Real wheel_v_local_y[4] = {};
    Real wheel_slip_ratio[4] = {};
    Real wheel_slip_angle_rad[4] = {};
    Real wheel_fz_n[4] = {};
    Real wheel_fx_local[4] = {};
    Real wheel_fy_local[4] = {};
    Real last_a_long_mps2 = 0.0f;
    Real last_a_lat_mps2 = 0.0f;
    Real engine_rpm = 4000.0f;
    Real battery_soc = 1.0f;
    Real tire_temp_c[4] = {80.0f, 80.0f, 80.0f, 80.0f};
    Real ride_height_m = 0.060f;
    int current_gear = 1;
    AeroMode current_aero_mode = AeroMode::Z_MODE;
    Real ers_boost_torque_per_rear_n_m = 0.0f;
    Real drive_force_capacity_n = 0.0f;
};

struct BatchForces{
    Real f_long_n = 0.0f;
    Real f_lat_n = 0.0f;
    Real t_z_n_m = 0.0f;
};

struct BatchOutputs{
    Real speed_mps = 0.0f;
    Real engine_rpm = 0.0f;
    Real battery_soc = 0.0f;
    int current_gear = 1;
    BatchForces forces;
};

BatchForces evaluate_batch_forces(const BatchVehicleConfig& config,BatchVehicleState& state,const BatchInputs& inputs,Real dt);

void update_batch_state(const BatchVehicleConfig& config,BatchVehicleState& state,const BatchForces& forces,const BatchInputs& inputs,Real dt);

BatchOutputs step_batch_vehicle(const BatchVehicleConfig& config,BatchVehicleState& state,const BatchInputs& inputs,Real dt);

}
}