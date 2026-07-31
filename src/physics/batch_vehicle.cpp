#include "contactpatch/physics/batch_vehicle.hpp"
#include <algorithm>
#include <cmath>

namespace contactpatch{
namespace physics{
namespace{

Vec3 compute_wheel_velocity_body(const BatchVehicleState& state,const BatchVehicleConfig& config,int wheel_idx){
    const Vec3& r = config.wheel_pos[wheel_idx];
    const Real v_x = state.v_long_mps - state.yaw_rate_rps * r.GetY();
    const Real v_y = state.v_lat_mps + state.yaw_rate_rps * r.GetX();
    return Vec3(v_x, v_y, 0.0f);
}
void rotate_wheel_to_body_forces(Real fx_wheel, Real fy_wheel, Real steer_rad, Real& fx_body, Real& fy_body){
    const Real c = std::cos(steer_rad);
    const Real s = std::sin(steer_rad);
    fx_body = fx_wheel * c - fy_wheel * s;
    fy_body = fx_wheel * s + fy_wheel * c;
}
Vec3 rotate_body_to_wheel_frame(const Vec3& v_body, Real steer_rad){
    const Real c = std::cos(steer_rad);
    const Real s = std::sin(steer_rad);
    const Real vx = v_body.GetX() * c + v_body.GetY() * s;
    const Real vy = -v_body.GetX() * s + v_body.GetY() * c;
    return Vec3(vx, vy, 0.0f);
}

void update_wheel_slips(BatchVehicleState& state, const BatchVehicleConfig& config) {
    static constexpr Real kSlipDenomEps = 1.0f;

    for (int i = 0; i < 4; ++i) {
        const Real v_local_x = state.wheel_v_local_x[i];
        const Real v_local_y = state.wheel_v_local_y[i];
        const Real denom = std::max(std::abs(v_local_x), kSlipDenomEps);

        const Real wheel_surface_speed = state.wheel_omega_rad_s[i] * config.wheel_radius_m;
        state.wheel_slip_ratio[i] = (wheel_surface_speed - v_local_x) / denom;
        state.wheel_slip_angle_rad[i] = std::atan2(-v_local_y, denom);
    }
}

void update_wheel_normal_loads(BatchVehicleState& state,const BatchVehicleConfig& config,Real aero_force_z,Real aero_pitch_torque_y){
    const Real f_total = config.mass_kg * config.gravity_m_s2 - aero_force_z;

    const Real fz_front_total = f_total * config.weight_dist_front;
    const Real fz_rear_total = f_total * (1.0f - config.weight_dist_front);

    Real fz[4];
    fz[BATCH_WHEEL_FL] = fz_front_total * 0.5f;
    fz[BATCH_WHEEL_FR] = fz_front_total * 0.5f;
    fz[BATCH_WHEEL_RL] = fz_rear_total * 0.5f;
    fz[BATCH_WHEEL_RR] = fz_rear_total * 0.5f;

    const Real safe_wheelbase = std::max(config.wheelbase_m, 1e-6f);
    const Real safe_track_front = std::max(config.track_front_m, 1e-6f);
    const Real safe_track_rear = std::max(config.track_rear_m, 1e-6f);

    const Real d_fz_aero = aero_pitch_torque_y / safe_wheelbase;
    const Real d_fz_long =
        config.mass_kg * state.last_a_long_mps2 * config.cog_height_m / safe_wheelbase
        + d_fz_aero;
    const Real d_fz_lat_front = config.mass_kg * state.last_a_lat_mps2 * config.cog_height_m
                              * config.weight_dist_front / safe_track_front;
    const Real d_fz_lat_rear = config.mass_kg * state.last_a_lat_mps2 * config.cog_height_m
                             * (1.0f - config.weight_dist_front) / safe_track_rear;

    fz[BATCH_WHEEL_FL] -= d_fz_long * 0.5f + d_fz_lat_front * 0.5f;
    fz[BATCH_WHEEL_FR] -= d_fz_long * 0.5f - d_fz_lat_front * 0.5f;
    fz[BATCH_WHEEL_RL] += d_fz_long * 0.5f + d_fz_lat_rear * 0.5f;
    fz[BATCH_WHEEL_RR] += d_fz_long * 0.5f - d_fz_lat_rear * 0.5f;

    for (int i = 0; i < 4; ++i) {
        state.wheel_fz_n[i] = std::max(fz[i], 0.0f);
    }
}

void integrate_wheel_omegas(BatchVehicleState& state,const BatchVehicleConfig& config,const BatchInputs& inputs,Real dt){
    const Real throttle = std::clamp(inputs.throttle, 0.0f, 1.0f);
    const Real brake = std::clamp(inputs.brake, 0.0f, 1.0f);
    const Real safe_inertia = std::max(config.wheel_inertia_kg_m2, 1e-6f);
    const Real radius = config.wheel_radius_m;

    constexpr Real kRadSToRpm = 60.0f / (2.0f * 3.1415926535f);
    if (state.current_gear < 1) state.current_gear = 1;
    if (state.current_gear > 8) state.current_gear = 8;
    const Real avg_rear_omega =
        0.5f * (state.wheel_omega_rad_s[BATCH_WHEEL_RL] + state.wheel_omega_rad_s[BATCH_WHEEL_RR]);
    Real rpm = std::max(avg_rear_omega, 0.0f)
             * config.gear_ratios[state.current_gear - 1] * kRadSToRpm;
    if (rpm > config.shift_up_rpm && state.current_gear < 8) {
        state.current_gear += 1;
    } else if (rpm < config.shift_down_rpm && state.current_gear > 1) {
        state.current_gear -= 1;
    }
    const Real ratio = config.gear_ratios[state.current_gear - 1];
    rpm = std::max(avg_rear_omega, 0.0f) * ratio * kRadSToRpm;
    state.engine_rpm = std::max(rpm, 2000.0f);

    const Real omega_engine = state.engine_rpm / kRadSToRpm;
    Real t_engine_cap = std::min(config.engine_max_torque_nm,
                                 config.engine_max_power_w / std::max(omega_engine, 100.0f));
    if (state.engine_rpm >= config.engine_rev_limit_rpm) {
        t_engine_cap = 0.0f;
    }
    state.drive_force_capacity_n = t_engine_cap * ratio / std::max(radius, 1e-3f);

    const Real rear_drive_torque = (t_engine_cap * throttle * ratio) * 0.5f;
    const Real brake_torque_total = config.max_brake_force_n * brake * radius;
    const Real brake_front_each = brake_torque_total * config.brake_bias_front * 0.5f;
    const Real brake_rear_each =
        brake_torque_total * (1.0f - config.brake_bias_front) * 0.5f;

    const Real omega_diff = state.wheel_omega_rad_s[BATCH_WHEEL_RR] - state.wheel_omega_rad_s[BATCH_WHEEL_RL];
    const Real tau_lsd_viscous = config.lsd_locking_coeff * omega_diff;
    const Real tau_lsd_coulomb = config.lsd_preload_nm * std::clamp(omega_diff * 2.0f, -1.0f, 1.0f);
    const Real tau_lsd = tau_lsd_viscous + tau_lsd_coulomb;

    for (int i = 0; i < 4; ++i) {
        Real tau_drive = 0.0f;
        if (i == BATCH_WHEEL_RL || i == BATCH_WHEEL_RR) {
            tau_drive = rear_drive_torque + state.ers_boost_torque_per_rear_n_m;
            if (i == BATCH_WHEEL_RL) {
                tau_drive += tau_lsd;
            } else {
                tau_drive -= tau_lsd;
            }
        }

        const Real tau_brake = (i < 2) ? brake_front_each : brake_rear_each;
        const Real omega = state.wheel_omega_rad_s[i];
        Real brake_sign = 0.0f;
        if (omega > 0.0f) {
            brake_sign = 1.0f;
        } else if (omega < 0.0f) {
            brake_sign = -1.0f;
        }

        const Real tau_react = state.wheel_fx_local[i] * radius;
        const Real tau_net = tau_drive - tau_brake * brake_sign - tau_react;
        state.wheel_omega_rad_s[i] += (tau_net / safe_inertia) * dt;

        if (state.wheel_omega_rad_s[i] < 0.0f && tau_drive == 0.0f) {
            state.wheel_omega_rad_s[i] = 0.0f;
        }
    }

}

void compute_tire_forces_per_wheel(const BatchVehicleConfig& config,BatchVehicleState& state,Real steer_rad,Real& out_fx,Real& out_fy,Real& out_tz){
    out_fx = 0.0f;
    out_fy = 0.0f;
    out_tz = 0.0f;

    for (int i = 0; i < 4; ++i) {
        state.wheel_fx_local[i] = 0.0f;
        state.wheel_fy_local[i] = 0.0f;
    }

    for (int i = 0; i < 4; ++i) {
        TireKinematics kin{};
        kin.kappa = state.wheel_slip_ratio[i];
        kin.alpha = state.wheel_slip_angle_rad[i];
        kin.gamma = 0.0f;
        kin.Fz = state.wheel_fz_n[i];

        if (kin.Fz <= 0.0f) continue;

        const PacejkaConfig& tire_cfg = (i < 2) ? config.front_tires : config.rear_tires;
        TireForces tf = compute_tire_forces(tire_cfg, kin);

        const Real t_diff = (state.tire_temp_c[i] - config.tire_temp_opt_c) / std::max(config.tire_temp_sigma, 1e-3f);
        const Real mu_thermal_raw = std::exp(-(t_diff * t_diff));
        const Real mu_thermal = std::max(0.5f, mu_thermal_raw);
        const Real fx_max = tire_cfg.p_dx1 * mu_thermal * kin.Fz;
        const Real fy_max = tire_cfg.p_dy1 * mu_thermal * kin.Fz;
        const Real ex = tf.Fx / std::max(fx_max, 1e-6f);
        const Real ey = tf.Fy / std::max(fy_max, 1e-6f);
        const Real e_mag = std::sqrt(ex * ex + ey * ey);
        if (e_mag > 1.0f) {
            const Real scale = 1.0f / e_mag;
            tf.Fx *= scale;
            tf.Fy *= scale;
        }

        state.wheel_fx_local[i] = tf.Fx;
        state.wheel_fy_local[i] = tf.Fy;

        const Real delta = (i < 2) ? steer_rad : 0.0f;
        Real fx_body = 0.0f;
        Real fy_body = 0.0f;
        rotate_wheel_to_body_forces(tf.Fx, tf.Fy, delta, fx_body, fy_body);

        out_fx += fx_body;
        out_fy += fy_body;

        const Vec3& r = config.wheel_pos[i];
        out_tz += r.GetX() * fy_body - r.GetY() * fx_body;
    }
}

void update_wheel_contact_velocities(
    BatchVehicleState& state,
    const BatchVehicleConfig& config,
    Real steer_rad) {
    for (int i = 0; i < 4; ++i) {
        const Vec3 v_wheel_body = compute_wheel_velocity_body(state, config, i);
        const Real delta = (i < 2) ? steer_rad : 0.0f;
        const Vec3 v_wheel_local = rotate_body_to_wheel_frame(v_wheel_body, delta);
        state.wheel_v_local_x[i] = v_wheel_local.GetX();
        state.wheel_v_local_y[i] = v_wheel_local.GetY();
    }
}

void update_tire_temperatures(BatchVehicleState& state, const BatchVehicleConfig& config, Real dt) {
    const Real T_ambient = config.ambient_temp_c;
    for (int i = 0; i < 4; ++i) {
        const Real slip_x = state.wheel_slip_ratio[i] * state.wheel_v_local_x[i];
        const Real slip_y = state.wheel_v_local_y[i];
        const Real P = std::abs(state.wheel_fx_local[i]) * std::abs(slip_x) + std::abs(state.wheel_fy_local[i]) * std::abs(slip_y);
        const Real dT = config.heat_coeff_slip * P - config.cool_coeff * (state.tire_temp_c[i] - T_ambient);
        state.tire_temp_c[i] += dT * dt;
        state.tire_temp_c[i] = std::min(state.tire_temp_c[i], 150.0f);
    }
}

Real compute_ride_height_multiplier(Real ride_height, const BatchVehicleConfig& config) {
    if (ride_height > 0.10f) return 1.0f;
    if (ride_height >= config.ride_height_opt_m) {
        const Real t = (0.10f - ride_height) / (0.10f - config.ride_height_opt_m);
        return 1.0f + 2.0f * t;
    }
    const Real stall_ratio = ride_height / std::max(config.ride_height_opt_m, 1e-6f);
    return std::max(0.5f, 3.0f * stall_ratio);
}

void update_ers(BatchVehicleState& state, const BatchVehicleConfig& config, const BatchInputs& inputs, Real f_brake, Real dt) {
    state.ers_boost_torque_per_rear_n_m = 0.0f;
    const Real energy_max = std::max(config.battery_capacity_j, 1.0f);

    if (inputs.brake > 0.0f) {
        const Real f_rear_actual = std::max(0.0f, -(state.wheel_fx_local[BATCH_WHEEL_RL] + state.wheel_fx_local[BATCH_WHEEL_RR]));
        const Real f_brake_rear = std::min(f_brake * (1.0f - config.brake_bias_front), f_rear_actual);
        const Real p_regen = std::min(f_brake_rear * state.v_long_mps, config.mguk_max_power_w) * config.regen_efficiency;
        state.battery_soc += (p_regen * dt) / energy_max;
        state.battery_soc = std::min(state.battery_soc, 1.0f);
    } else if (inputs.ers_override && state.battery_soc > 0.0f) {
        const Real taper_span = std::max(
            config.mguk_taper_end_mps - config.mguk_taper_start_mps, 1e-3f);
        const Real taper = std::clamp(
            (config.mguk_taper_end_mps - state.v_long_mps) / taper_span, 0.0f, 1.0f);
        const Real p_boost = config.mguk_max_power_w * taper;
        const Real energy_used = p_boost * dt;
        if (energy_used > 0.0f && state.battery_soc * energy_max >= energy_used) {
            state.battery_soc -= energy_used / energy_max;
            if (state.v_long_mps > 5.0f) {
                const Real p_mech = p_boost * config.mguk_deploy_efficiency;
                const Real f_boost_at_wheels = p_mech / state.v_long_mps;
                const Real boost_torque_total = f_boost_at_wheels * config.wheel_radius_m;
                state.ers_boost_torque_per_rear_n_m = boost_torque_total * 0.5f;
            }
        }
    }
}

}

BatchForces evaluate_batch_forces(const BatchVehicleConfig& config,BatchVehicleState& state,const BatchInputs& inputs,Real dt){
    const Real steer_rad = std::clamp(inputs.steering_rad, -config.max_steer_rad, config.max_steer_rad);

    update_wheel_contact_velocities(state, config, steer_rad);
    update_wheel_slips(state, config);
    BatchForces out{};
    out.f_long_n = 0.0f;
    out.f_lat_n = 0.0f;
    out.t_z_n_m = 0.0f;

    const Vec3 v_body(state.v_long_mps, state.v_lat_mps, 0.0f);
    AeroState aero_state{state.current_aero_mode};
    Vec3 aero_force;
    Vec3 aero_torque;
    compute_aero_forces(config.aero, aero_state, v_body, 1.0f, aero_force, aero_torque);

    out.f_long_n += aero_force.GetX();
    out.f_lat_n += aero_force.GetY();
    out.t_z_n_m += aero_torque.GetZ();

    state.ride_height_m = std::max(0.010f,
        0.060f - std::max(-aero_force.GetZ(), 0.0f) / 200000.0f);
    const Real df_mult = compute_ride_height_multiplier(state.ride_height_m, config);
    aero_force = Vec3(aero_force.GetX(), aero_force.GetY(), aero_force.GetZ() * df_mult);

    update_wheel_normal_loads(state, config, aero_force.GetZ(), aero_torque.GetY());

    Real tire_fx = 0.0f;
    Real tire_fy = 0.0f;
    Real tire_tz = 0.0f;
    compute_tire_forces_per_wheel(config, state, steer_rad, tire_fx, tire_fy, tire_tz);

    update_tire_temperatures(state, config, dt);

    const Real f_brake_total = inputs.brake * config.max_brake_force_n;
    update_ers(state, config, inputs, f_brake_total, dt);

    out.f_long_n += tire_fx;
    out.f_lat_n += tire_fy;
    out.t_z_n_m += tire_tz;

    return out;
}

void update_batch_state(const BatchVehicleConfig& config,BatchVehicleState& state,const BatchForces& forces,const BatchInputs& inputs,Real dt) {
    const Real safe_mass = (config.mass_kg > 1e-6f) ? config.mass_kg : 1.0f;
    const Real safe_izz = (config.izz_kg_m2 > 1e-6f) ? config.izz_kg_m2 : 1.0f;

    const Real a_long = forces.f_long_n / safe_mass + state.v_lat_mps * state.yaw_rate_rps;
    const Real a_lat = forces.f_lat_n / safe_mass - state.v_long_mps * state.yaw_rate_rps;
    const Real yaw_acc = forces.t_z_n_m / safe_izz;

    state.v_long_mps += a_long * dt;
    state.v_lat_mps += a_lat * dt;
    state.yaw_rate_rps += yaw_acc * dt;

    state.yaw_rad += state.yaw_rate_rps * dt;

    const Real cy = std::cos(state.yaw_rad);
    const Real sy = std::sin(state.yaw_rad);
    state.x_m += (state.v_long_mps * cy - state.v_lat_mps * sy) * dt;
    state.y_m += (state.v_long_mps * sy + state.v_lat_mps * cy) * dt;

    integrate_wheel_omegas(state, config, inputs, dt);

    state.last_a_long_mps2 = a_long;
    state.last_a_lat_mps2 = a_lat;
}

BatchOutputs step_batch_vehicle(const BatchVehicleConfig& config,BatchVehicleState& state,const BatchInputs& inputs,Real dt){
    const BatchForces forces = evaluate_batch_forces(config, state, inputs, dt);
    update_batch_state(config, state, forces, inputs, dt);

    BatchOutputs out{};
    out.speed_mps = std::sqrt(state.v_long_mps * state.v_long_mps + state.v_lat_mps * state.v_lat_mps);
    out.engine_rpm = state.engine_rpm;
    out.battery_soc = state.battery_soc;
    out.current_gear = state.current_gear;
    out.forces = forces;
    return out;
}

}
}
