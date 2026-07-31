#include <cmath>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "contactpatch/physics/batch_vehicle.hpp"

using namespace contactpatch;
using namespace contactpatch::physics;

TEST_CASE("LSD transfers torque toward the slower wheel", "[physics][lsd]") {
    BatchVehicleConfig config{};
    config.lsd_preload_nm = 50.0f;
    config.lsd_locking_coeff = 2.0f;
    config.gravity_m_s2 = 0.0f;

    BatchVehicleState state{};
    state.v_long_mps = 1.0f;

    state.wheel_omega_rad_s[BATCH_WHEEL_RR] = 50.0f;
    state.wheel_omega_rad_s[BATCH_WHEEL_RL] = 5.0f;

    BatchInputs inputs{};
    inputs.throttle = 1.0f;

    const Real dt = 0.01f;
    const Real omega_diff_before = state.wheel_omega_rad_s[BATCH_WHEEL_RR] - state.wheel_omega_rad_s[BATCH_WHEEL_RL];

    BatchOutputs out = step_batch_vehicle(config, state, inputs, dt);

    const Real omega_diff_after = state.wheel_omega_rad_s[BATCH_WHEEL_RR] - state.wheel_omega_rad_s[BATCH_WHEEL_RL];
    REQUIRE(omega_diff_after < omega_diff_before);
}

TEST_CASE("Thermal tire model heats up", "[physics][thermal]") {
    BatchVehicleConfig config{};
    BatchVehicleState state{};
    state.v_long_mps = 30.0f;
    state.tire_temp_c[0] = 25.0f;

    BatchInputs inputs{};
    inputs.throttle = 1.0f;

    for (int i = 0; i < 100; ++i) {
        step_batch_vehicle(config, state, inputs, 0.01f);
    }

    REQUIRE(state.tire_temp_c[0] > 25.0f);
}

TEST_CASE("Ground effect increases downforce at high speed", "[physics][aero]") {
    BatchVehicleConfig config{};
    BatchVehicleState state{};
    state.v_long_mps = 80.0f;

    BatchInputs inputs{};
    BatchOutputs out = step_batch_vehicle(config, state, inputs, 0.01f);

    REQUIRE(state.ride_height_m < 0.060f);
}

TEST_CASE("ERS strategy regenerates and boosts", "[physics][ers]") {
    BatchVehicleConfig config{};
    BatchVehicleState state{};
    state.v_long_mps = 50.0f;
    state.battery_soc = 0.5f;
    for (int i = 0; i < 4; ++i) {
        state.wheel_omega_rad_s[i] = state.v_long_mps / config.wheel_radius_m;
    }

    BatchInputs inputs{};
    inputs.brake = 1.0f;
    for (int i = 0; i < 100; ++i) {
        step_batch_vehicle(config, state, inputs, 0.001f);
    }
    REQUIRE(state.battery_soc > 0.5f);

    const Real prev_soc = state.battery_soc;

    BatchVehicleState state_boost = state;
    BatchVehicleState state_noboost = state;

    BatchInputs in_boost{};
    in_boost.throttle = 0.3f;
    in_boost.ers_override = true;
    BatchInputs in_noboost = in_boost;
    in_noboost.ers_override = false;

    step_batch_vehicle(config, state_boost, in_boost, 0.1f);
    step_batch_vehicle(config, state_noboost, in_noboost, 0.1f);

    REQUIRE(state_boost.battery_soc < prev_soc);
    const Real rear_omega_boost =
        0.5f * (state_boost.wheel_omega_rad_s[2] + state_boost.wheel_omega_rad_s[3]);
    const Real rear_omega_noboost =
        0.5f * (state_noboost.wheel_omega_rad_s[2] + state_noboost.wheel_omega_rad_s[3]);
    REQUIRE(rear_omega_boost > rear_omega_noboost);
}
