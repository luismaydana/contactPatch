#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "contactpatch/sim/batch_simulator.hpp"

using namespace contactpatch;
using namespace contactpatch::track;
using namespace contactpatch::sim;

static void set_straight_track(BatchSimulator& sim, Real length_m, int point_count) {
    std::vector<CenterlinePoint> points;
    points.reserve(static_cast<usize>(point_count));
    for (int i = 0; i < point_count; ++i) {
        CenterlinePoint p{};
        p.s_arc_m = length_m * static_cast<Real>(i) / static_cast<Real>(point_count - 1);
        p.x_m = p.s_arc_m;
        p.y_m = 0.0f;
        const Real frac = p.s_arc_m / length_m;
        p.sector = (frac < 1.0f / 3.0f) ? 0 : (frac < 2.0f / 3.0f ? 1 : 2);
        points.push_back(p);
    }
    sim.set_track_points_for_testing(points);
}

TEST_CASE("lap crossing detected on forward s_arc wrap", "[batch_lap]") {
    BatchSimulator sim{};
    sim.initialize(physics::BatchVehicleConfig{}, physics::BatchVehicleState{});
    set_straight_track(sim, 100.0f, 11);

    sim.simulate_s_arc_for_testing(90.0f, 0.001f);
    sim.simulate_s_arc_for_testing(5.0f, 0.001f);

    REQUIRE(sim.lap_state().lap_count == 1);
    REQUIRE(sim.lap_state().last_lap_time_s == Catch::Approx(0.002f).margin(0.0005f));
}

TEST_CASE("sector crossing records sector times", "[batch_lap]") {
    BatchSimulator sim{};
    sim.initialize(physics::BatchVehicleConfig{}, physics::BatchVehicleState{});
    set_straight_track(sim, 300.0f, 31);

    sim.simulate_s_arc_for_testing(50.0f, 0.001f);
    sim.simulate_s_arc_for_testing(150.0f, 0.001f);
    REQUIRE(sim.lap_state().last_sector_times_s[0] == Catch::Approx(0.002f).margin(0.0005f));

    sim.simulate_s_arc_for_testing(250.0f, 0.001f);
    REQUIRE(sim.lap_state().last_sector_times_s[1] == Catch::Approx(0.001f).margin(0.0005f));

    sim.simulate_s_arc_for_testing(10.0f, 0.001f);
    REQUIRE(sim.lap_state().lap_count == 1);
    REQUIRE(sim.lap_state().last_sector_times_s[2] == Catch::Approx(0.001f).margin(0.0005f));
}

TEST_CASE("low speed s_arc wrap does not count spurious lap", "[batch_lap]") {
    BatchSimulator sim{};
    sim.initialize(physics::BatchVehicleConfig{}, physics::BatchVehicleState{});
    set_straight_track(sim, 100.0f, 11);

    sim.simulate_s_arc_for_testing(90.0f, 0.001f, 0.5f);
    sim.simulate_s_arc_for_testing(5.0f, 0.001f, 0.5f);

    REQUIRE(sim.lap_state().lap_count == 0);
}

TEST_CASE("pacejka launch does not false-trigger lap on Suzuka", "[batch_lap]") {
    BatchSimulator sim{};
    sim.initialize(physics::BatchVehicleConfig{}, physics::BatchVehicleState{});
    const std::string csv = std::string(CONTACTPATCH_DATA_DIR) + "/tracks/suzuka/centerline.csv";
    if (!sim.load_track(csv)) {
        SUCCEED("Suzuka CSV not available from test cwd");
        return;
    }

    physics::BatchInputs in{};
    in.throttle = 1.0f;
    for (int i = 0; i < 1000; ++i) {
        sim.step(in);
    }

    REQUIRE(sim.lap_state().lap_count == 0);
    REQUIRE(sim.lap_state().current_lap_time_s == Catch::Approx(1.0f).margin(0.05f));
}
