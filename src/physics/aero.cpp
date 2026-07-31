#include "contactpatch/physics/aero.hpp"
#include <cmath>
namespace contactpatch{
namespace physics{
void compute_aero_forces(const AeroConfig& config, const AeroState& state, const Vec3& v_body, Real ride_height_mult, Vec3& out_force_body, Vec3& out_torque_body){
    Real v_sq = v_body.LengthSq();
    if(v_sq < 0.001f){
        out_force_body = Vec3(0.0f, 0.0f, 0.0f);
        out_torque_body = Vec3(0.0f, 0.0f, 0.0f);
        return;
    }
    Real q = (config.air_density * v_sq) / 2.0f;
    Real cd, cl;
    Vec3 cop_offset;
    if(state.current_mode == AeroMode::X_MODE){
        cd = config.cd_x;
        cl = config.cl_x;
        cop_offset = config.cop_offset_x;
    }else{
        cd = config.cd_z;
        cl = config.cl_z;
        cop_offset = config.cop_offset_z;
    }
    Real drag_force = q * config.frontal_area * cd;
    Real downforce = q * config.frontal_area * cl * ride_height_mult;
    Vec3 v_dir = v_body.Normalized();
    Vec3 force_drag = -v_dir * drag_force;
    Vec3 force_down = Vec3(0.0f, 0.0f, downforce);
    out_force_body = force_drag + force_down;
    out_torque_body = cop_offset.Cross(out_force_body);
}
}
}
