#pragma once
#include "contactpatch/core/types.hpp"
namespace contactpatch{
namespace physics{

struct PacejkaConfig{
    Real Fz0   = 2000.0f;
    Real p_cx1 = 1.65f;
    Real p_dx1 = 1.9f;
    Real p_dx2 = -0.17f;
    Real p_ex1 = 0.0f;
    Real p_kx1 = 15.0f;
    Real p_hx1 = 0.0f;
    Real p_vx1 = 0.0f;
    Real p_cy1 = 1.3f;
    Real p_dy1 = 1.8f;
    Real p_dy2 = -0.17f;
    Real p_ey1 = 0.0f;
    Real p_ky1 = 17.0f;
    Real p_hy1 = 0.0f;
    Real p_vy1 = 0.0f;
};

struct TireKinematics{
    Real kappa;
    Real alpha;
    Real gamma;
    Real Fz;
};

struct TireForces{
    Real Fx;
    Real Fy;
    Real Mz;
};

Real evaluate_pacejka_fx(const PacejkaConfig& config, const TireKinematics& kin);

Real evaluate_pacejka_fy(const PacejkaConfig& config, const TireKinematics& kin);

TireForces compute_tire_forces(const PacejkaConfig& config, const TireKinematics& kin);

}
}
