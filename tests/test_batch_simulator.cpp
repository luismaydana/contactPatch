#include <catch2/catch_test_macros.hpp>

#include "contactpatch/sim/batch_simulator.hpp"

using namespace contactpatch;

TEST_CASE("batch simulator steps deterministically", "[batch_simulator]") {
    sim::BatchSimulator a;
    sim::BatchSimulator b;

    physics::BatchVehicleConfig cfg{};
    physics::BatchVehicleState st{};
    a.initialize(cfg, st);
    b.initialize(cfg, st);

    physics::BatchInputs in{};
    in.throttle = 0.4f;

    for (int i = 0; i < 200; ++i) {
        a.step(in);
        b.step(in);
    }

    REQUIRE(a.get_state().x_m == b.get_state().x_m);
    REQUIRE(a.get_state().y_m == b.get_state().y_m);
    REQUIRE(a.get_state().v_long_mps == b.get_state().v_long_mps);
}
