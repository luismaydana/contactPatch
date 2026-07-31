#pragma once
#include "contactpatch/core/types.hpp"
namespace contactpatch{
namespace physics{

    enum class AeroMode{
        Z_MODE,
        X_MODE
    };

    struct AeroConfig{
        Real frontal_area;
        Real air_density;
        Real cd_z;
        Real cl_z;
        Real cd_x;
        Real cl_x;
        Vec3 cop_offset_z;
        Vec3 cop_offset_x;
    };

    struct AeroState{AeroMode current_mode = AeroMode::Z_MODE;};

    void compute_aero_forces(const AeroConfig& config, const AeroState& state, const Vec3& v_body, Real ride_height_mult, Vec3& out_force_body, Vec3& out_torque_body);

}
}
