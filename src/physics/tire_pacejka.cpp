#include "contactpatch/physics/tire_pacejka.hpp"
#include <cmath>
#include <algorithm>
namespace contactpatch{
namespace physics{

Real evaluate_pacejka_fx(const PacejkaConfig& config, const TireKinematics& kin){
    if(kin.Fz <= 0.0f) return 0.0f;
    Real dfz = (kin.Fz - config.Fz0) / config.Fz0;
    Real kappa_x = kin.kappa + config.p_hx1;
    Real mu_x = std::max(config.p_dx1 + config.p_dx2 * dfz, 0.3f);
    Real D_x = mu_x * kin.Fz;
    Real C_x = config.p_cx1;
    Real K_x = kin.Fz * config.p_kx1;
    Real B_x = K_x / (C_x * D_x + 1e-6f);
    Real E_x = config.p_ex1;
    Real Fx0 = D_x * std::sin(C_x * std::atan(B_x * kappa_x - E_x * (B_x * kappa_x - std::atan(B_x * kappa_x))));
    Real V_x = kin.Fz * config.p_vx1;
    return Fx0 + V_x;
}

Real evaluate_pacejka_fy(const PacejkaConfig& config, const TireKinematics& kin){
    if(kin.Fz <= 0.0f) return 0.0f;
    Real dfz = (kin.Fz - config.Fz0) / config.Fz0;
    Real alpha_y = kin.alpha + config.p_hy1;
    Real mu_y = std::max(config.p_dy1 + config.p_dy2 * dfz, 0.3f);
    Real D_y = mu_y * kin.Fz;
    Real C_y = config.p_cy1;
    Real K_y = kin.Fz * config.p_ky1;
    Real B_y = K_y / (C_y * D_y + 1e-6f);
    Real E_y = config.p_ey1;
    Real Fy0 = D_y * std::sin(C_y * std::atan(B_y * alpha_y - E_y * (B_y * alpha_y - std::atan(B_y * alpha_y))));
    Real V_y = kin.Fz * config.p_vy1;
    return Fy0 + V_y;
}

TireForces compute_tire_forces(const PacejkaConfig& config, const TireKinematics& kin){
    TireForces forces;
    forces.Fx = 0.0f;
    forces.Fy = 0.0f;
    forces.Mz = 0.0f;
    forces.Fx = evaluate_pacejka_fx(config, kin);
    forces.Fy = evaluate_pacejka_fy(config, kin);

    Real pneumatic_trail_m = 0.05f;
    forces.Mz = forces.Fy * pneumatic_trail_m;

    return forces;
}

}
}
