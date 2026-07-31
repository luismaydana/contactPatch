#include <catch2/catch_test_macros.hpp>
#include "contactpatch/physics/tire_pacejka.hpp"

using namespace contactpatch;
using namespace contactpatch::physics;

TEST_CASE("Magic Formula sine, load-sensitive peaks: tyre force evaluations", "[pacejka]") {
    PacejkaConfig config{};
    config.Fz0 = 4000.0f;
    config.p_cx1 = 1.6f;
    config.p_dx1 = 1.2f;
    config.p_dx2 = 0.0f;
    config.p_ex1 = 0.0f;
    config.p_kx1 = 20.0f;
    config.p_hx1 = 0.0f;
    config.p_vx1 = 0.0f;
    config.p_cy1 = 1.3f;
    config.p_dy1 = 1.2f;
    config.p_dy2 = 0.0f;
    config.p_ey1 = 0.0f;
    config.p_ky1 = 15.0f;
    config.p_hy1 = 0.0f;
    config.p_vy1 = 0.0f;

    SECTION("Zero slip generates zero force"){
        TireKinematics kin{0.0f, 0.0f, 0.0f, 4000.0f};
        TireForces forces = compute_tire_forces(config, kin);
        REQUIRE(forces.Fx == 0.0f);
        REQUIRE(forces.Fy == 0.0f);
    }

    SECTION("Positive longitudinal slip (acceleration) generates positive Fx"){
        TireKinematics kin{0.1f, 0.0f, 0.0f, 4000.0f};
        TireForces forces = compute_tire_forces(config, kin);
        REQUIRE(forces.Fx > 0.0f);
        REQUIRE(forces.Fy == 0.0f);
        REQUIRE(forces.Fx <= 4800.0f);
    }
    SECTION("Negative lateral slip angle generates opposing lateral force"){
        TireKinematics kin{0.0f, -0.1f, 0.0f, 4000.0f};
        TireForces forces = compute_tire_forces(config, kin);
        REQUIRE(forces.Fy < 0.0f);
    }

    SECTION("Zero load generates zero force regardless of slip"){
        TireKinematics kin{1.0f, 1.0f, 0.0f, 0.0f};
        TireForces forces = compute_tire_forces(config, kin);
        REQUIRE(forces.Fx == 0.0f);
        REQUIRE(forces.Fy == 0.0f);
    }
}

TEST_CASE("load sensitivity floors instead of inverting at extreme load", "[pacejka]") {
    PacejkaConfig config{};

    TireKinematics kin{0.1f, 0.0f, 0.0f, 30000.0f};
    TireForces forces = compute_tire_forces(config, kin);
    REQUIRE(forces.Fx > 0.25f * 30000.0f);

    TireKinematics kin_lat{0.0f, 0.1f, 0.0f, 30000.0f};
    TireForces lat = compute_tire_forces(config, kin_lat);
    REQUIRE(lat.Fy > 0.2f * 30000.0f);
}
