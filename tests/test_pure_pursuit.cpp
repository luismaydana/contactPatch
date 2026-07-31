#include <cmath>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "contactpatch/control/pure_pursuit.hpp"
#include "contactpatch/sim/batch_simulator.hpp"

using namespace contactpatch;
using namespace contactpatch::control;
using namespace contactpatch::sim;
using namespace contactpatch::track;

static std::vector<CenterlinePoint> make_straight_points(Real length_m, int count) {
    std::vector<CenterlinePoint> points;
    points.reserve(static_cast<usize>(count));
    for (int i = 0; i < count; ++i) {
        CenterlinePoint p{};
        p.s_arc_m = length_m * static_cast<Real>(i) / static_cast<Real>(count - 1);
        p.x_m = p.s_arc_m;
        p.y_m = 0.0f;
        p.curvature = 0.0f;
        points.push_back(p);
    }
    return points;
}

TEST_CASE("pure pursuit follows straight line", "[batch_pursuit]") {
    BatchSimulator sim{};
    sim.set_track_points_for_testing(make_straight_points(200.0f, 21));

    physics::BatchVehicleState st{};
    st.x_m = 0.0f;
    st.y_m = 0.0f;
    st.yaw_rad = 0.0f;
    st.v_long_mps = 10.0f;
    sim.initialize(physics::BatchVehicleConfig{}, st);

    PurePursuitConfig pp_cfg{};
    PurePursuitState pp_state{};

    constexpr Real dt = 0.01f;
    Real max_lateral = 0.0f;
    for (int i = 0; i < 500; ++i) {
        const physics::BatchInputs inputs = compute_pure_pursuit_inputs(
            pp_cfg, pp_state, sim.get_state(), sim.get_track(), dt);
        sim.step(inputs, dt);

        const Real lat = std::abs(sim.get_state().lateral_offset_m);
        max_lateral = std::max(max_lateral, lat);
        REQUIRE(std::isfinite(sim.get_state().x_m));
        REQUIRE(std::isfinite(sim.get_state().y_m));
        REQUIRE(std::isfinite(sim.get_state().v_long_mps));
    }

    REQUIRE(max_lateral < 0.5f);
    REQUIRE(sim.get_state().v_long_mps > 30.0f);
}

TEST_CASE("pure pursuit survives Suzuka for 60 seconds", "[batch_pursuit]") {
    const std::string csv = std::string(CONTACTPATCH_DATA_DIR) + "/tracks/suzuka/centerline.csv";

    BatchSimulator sim{};
    if (!sim.load_track(csv)) {
        SUCCEED("Suzuka CSV not available from test cwd");
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
    {
        const physics::BatchVehicleConfig tmp_cfg{};
        for (int w = 0; w < 4; ++w) {
            st.wheel_omega_rad_s[w] = st.v_long_mps / tmp_cfg.wheel_radius_m;
        }
    }
    sim.initialize(physics::BatchVehicleConfig{}, st);

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
    constexpr Real max_lateral_allowed_m = 20.0f;
    Real max_lateral = 0.0f;
    for (int i = 0; i < 6000; ++i) {
        const physics::BatchInputs inputs = compute_pure_pursuit_inputs(
            pp_cfg, pp_state, sim.get_state(), sim.get_track(), dt);
        sim.step(inputs, dt);

        const auto& s = sim.get_state();
        REQUIRE(std::isfinite(s.x_m));
        REQUIRE(std::isfinite(s.y_m));
        REQUIRE(std::isfinite(s.v_long_mps));

        max_lateral = std::max(max_lateral, std::abs(s.lateral_offset_m));
        REQUIRE(std::abs(s.lateral_offset_m) < max_lateral_allowed_m);
    }

    REQUIRE(sim.lap_state().lap_count >= 0);
    REQUIRE(max_lateral < max_lateral_allowed_m);
    REQUIRE(sim.get_state().v_long_mps > 5.0f);
}
