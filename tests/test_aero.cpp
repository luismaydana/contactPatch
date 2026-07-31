#include <catch2/catch_test_macros.hpp>
#include "contactpatch/physics/aero.hpp"
#include <cmath>

using namespace contactpatch::physics;
using namespace contactpatch;

TEST_CASE("F1 2026 Aero Logic", "[aero]"){
    AeroConfig config;
    config.air_density = 1.225f;
    config.frontal_area = 1.5f;

    config.cd_z = 1.1f;
    config.cl_z = -3.5f;
    config.cop_offset_z = Vec3(0.0f, 0.0f, 0.0f);

    config.cd_x = 0.6f;
    config.cl_x = -1.0f;
    config.cop_offset_x = Vec3(0.0f, 0.0f, 0.0f);

    Vec3 velocity(80.0f, 0.0f, 0.0f);

    Vec3 force_z, torque_z;
    Vec3 force_x, torque_x;

    SECTION("Z-Mode generates more drag and downforce than X-Mode"){
        AeroState state_z{AeroMode::Z_MODE};
        compute_aero_forces(config, state_z, velocity, 1.0f, force_z, torque_z);
        AeroState state_x{AeroMode::X_MODE};
        compute_aero_forces(config, state_x, velocity, 1.0f, force_x, torque_x);

        REQUIRE(force_z.GetX() < 0.0f);
        REQUIRE(force_x.GetX() < 0.0f);
        REQUIRE(force_z.GetZ() < 0.0f);
        REQUIRE(force_x.GetZ() < 0.0f);
        REQUIRE(std::abs(force_z.GetX()) > std::abs(force_x.GetX()));
        REQUIRE(std::abs(force_z.GetZ()) > std::abs(force_x.GetZ()));
    }

    SECTION("Zero velocity generates zero forces"){
        AeroState state_z{AeroMode::Z_MODE};
        Vec3 zero_vel(0.0f, 0.0f, 0.0f);
        compute_aero_forces(config, state_z, zero_vel, 1.0f, force_z, torque_z);
        REQUIRE(force_z.GetX() == 0.0f);
        REQUIRE(force_z.GetY() == 0.0f);
        REQUIRE(force_z.GetZ() == 0.0f);
    }
}
