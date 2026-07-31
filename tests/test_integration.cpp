#include <cmath>
#include <fstream>
#include <string>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "contactpatch/control/pure_pursuit.hpp"
#include "contactpatch/sim/batch_simulator.hpp"

using namespace contactpatch;
using namespace contactpatch::control;
using namespace contactpatch::sim;
using namespace contactpatch::track;

TEST_CASE("Integration - Pure Pursuit drives Suzuka stably across the figure-8", "[integration]") {
    const std::string csv_path = std::string(CONTACTPATCH_DATA_DIR) + "/tracks/suzuka/centerline.csv";

    BatchSimulator sim{};
    if (!sim.load_track(csv_path)) {
        SUCCEED("Suzuka CSV not available from test cwd. Skipping integration test.");
        return;
    }

    const auto& pts = sim.get_track().points();
    REQUIRE(pts.size() > 2);

    physics::BatchVehicleState st{};
    st.x_m = pts.front().x_m;
    st.y_m = pts.front().y_m;
    const Real dx = pts[1].x_m - pts[0].x_m;
    const Real dy = pts[1].y_m - pts[0].y_m;
    st.yaw_rad = std::atan2(dy, dx);
    st.v_long_mps = 30.0f;

    physics::BatchVehicleConfig vehicle_cfg{};
    for (int w = 0; w < 4; ++w) {
        st.wheel_omega_rad_s[w] = st.v_long_mps / vehicle_cfg.wheel_radius_m;
    }
    sim.initialize(vehicle_cfg, st);

    sim.step(physics::BatchInputs{}, 0.001f);

    PurePursuitConfig pp_cfg{};
    pp_cfg.lookahead_min_m = 15.0f;
    pp_cfg.lookahead_gain_s = 0.6f;
    pp_cfg.mu_effective = 0.6f;
    pp_cfg.v_max_mps = 70.0f;
    pp_cfg.speed_lookahead_m = 90.0f;
    pp_cfg.kp_brake = 0.5f;
    PurePursuitState pp_state{};

    constexpr Real dt = 0.01f;

    constexpr Real kCrossoverArc = 2544.0f;
    Real max_s_arc = 0.0f;

    for (int i = 0; i < 12000; ++i) {
        const physics::BatchInputs inputs = compute_pure_pursuit_inputs(
            pp_cfg, pp_state, sim.get_state(), sim.get_track(), dt);

        sim.step(inputs, dt);
        const auto& s = sim.get_state();

        REQUIRE(std::isfinite(s.x_m));
        REQUIRE(std::isfinite(s.y_m));
        REQUIRE(std::isfinite(s.v_long_mps));
        REQUIRE(std::abs(s.lateral_offset_m) < 30.0f);

        max_s_arc = std::max(max_s_arc, s.s_arc_m);
        if (max_s_arc > kCrossoverArc + 150.0f) {
            break;
        }
        if (sim.lap_state().lap_count >= 1) {
            break;
        }
    }

    REQUIRE(max_s_arc > kCrossoverArc + 100.0f);
    REQUIRE(sim.lap_state().lap_count <= 1);
    REQUIRE(sim.get_state().v_long_mps > 5.0f);
}
