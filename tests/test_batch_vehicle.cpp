#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "contactpatch/physics/batch_vehicle.hpp"

using namespace contactpatch;
using namespace contactpatch::physics;

TEST_CASE("batch vehicle accelerates with throttle", "[batch_vehicle]") {
    BatchVehicleConfig cfg{};
    BatchVehicleState st{};
    BatchInputs in{};
    in.throttle = 1.0f;

    for (int i = 0; i < 100; ++i) {
        step_batch_vehicle(cfg, st, in, 0.001f);
    }
    REQUIRE(st.v_long_mps > 0.0f);
}

TEST_CASE("batch vehicle braking produces negative longitudinal force", "[batch_vehicle]") {
    BatchVehicleConfig cfg{};
    BatchVehicleState st{};
    st.v_long_mps = 20.0f;
    st.wheel_omega_rad_s[BATCH_WHEEL_FL] = 20.0f / cfg.wheel_radius_m;
    st.wheel_omega_rad_s[BATCH_WHEEL_FR] = 20.0f / cfg.wheel_radius_m;
    st.wheel_omega_rad_s[BATCH_WHEEL_RL] = 20.0f / cfg.wheel_radius_m;
    st.wheel_omega_rad_s[BATCH_WHEEL_RR] = 20.0f / cfg.wheel_radius_m;
    BatchInputs in{};
    in.brake = 1.0f;

    for (int i = 0; i < 200; ++i) {
        step_batch_vehicle(cfg, st, in, 0.001f);
    }
    REQUIRE(st.v_long_mps < 20.0f);
}

TEST_CASE("wheel contact velocity matches chassis when not yawing", "[batch_vehicle][kinematics]") {
    BatchVehicleConfig cfg{};
    BatchVehicleState st{};
    st.v_long_mps = 30.0f;
    st.v_lat_mps = 2.0f;
    BatchInputs in{};

    evaluate_batch_forces(cfg, st, in, 0.001f);

    for (int i = 0; i < 4; ++i) {
        REQUIRE(st.wheel_v_local_x[i] == Catch::Approx(st.v_long_mps));
        REQUIRE(st.wheel_v_local_y[i] == Catch::Approx(st.v_lat_mps));
    }
}

TEST_CASE("front wheels rotate velocity with steering", "[batch_vehicle][kinematics]") {
    BatchVehicleConfig cfg{};
    BatchVehicleState st{};
    st.v_long_mps = 20.0f;
    BatchInputs in{};
    in.steering_rad = 0.1f;

    evaluate_batch_forces(cfg, st, in, 0.001f);

    REQUIRE(st.wheel_v_local_x[BATCH_WHEEL_FL] != Catch::Approx(st.v_long_mps));
    REQUIRE(st.wheel_v_local_x[BATCH_WHEEL_RL] == Catch::Approx(st.v_long_mps));
}

TEST_CASE("batch vehicle accelerates from standstill with Pacejka loop", "[batch_vehicle][accel]") {
    BatchVehicleConfig cfg{};
    BatchVehicleState st{};
    BatchInputs in{};
    in.throttle = 1.0f;

    for (int i = 0; i < 1000; ++i) {
        step_batch_vehicle(cfg, st, in, 0.001f);
    }

    REQUIRE(st.v_long_mps > 4.0f);
    REQUIRE(st.v_long_mps < 50.0f);
    REQUIRE(st.wheel_omega_rad_s[BATCH_WHEEL_RL] > 0.0f);
    REQUIRE(st.wheel_omega_rad_s[BATCH_WHEEL_FL] > 0.0f);
}

TEST_CASE("identical inputs produce identical state", "[batch_vehicle][determinism]") {
    BatchVehicleConfig cfg{};
    BatchVehicleState a{};
    BatchVehicleState b{};
    a.v_long_mps = 25.0f;
    b.v_long_mps = 25.0f;
    for (int w = 0; w < 4; ++w) {
        a.wheel_omega_rad_s[w] = 25.0f / cfg.wheel_radius_m;
        b.wheel_omega_rad_s[w] = 25.0f / cfg.wheel_radius_m;
    }

    for (int i = 0; i < 500; ++i) {
        BatchInputs in{};
        in.throttle = (i % 100 < 60) ? 0.8f : 0.0f;
        in.brake = (i % 100 >= 80) ? 0.6f : 0.0f;
        in.steering_rad = 0.2f * std::sin(0.01f * static_cast<Real>(i));
        step_batch_vehicle(cfg, a, in, 0.001f);
        step_batch_vehicle(cfg, b, in, 0.001f);
    }

    REQUIRE(a.x_m == b.x_m);
    REQUIRE(a.y_m == b.y_m);
    REQUIRE(a.yaw_rad == b.yaw_rad);
    REQUIRE(a.v_long_mps == b.v_long_mps);
    REQUIRE(a.v_lat_mps == b.v_lat_mps);
    for (int w = 0; w < 4; ++w) {
        REQUIRE(a.wheel_omega_rad_s[w] == b.wheel_omega_rad_s[w]);
        REQUIRE(a.tire_temp_c[w] == b.tire_temp_c[w]);
    }
    REQUIRE(a.battery_soc == b.battery_soc);
}
