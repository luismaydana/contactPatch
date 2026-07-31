import numpy as np
import qss_laptime as q

CL_Z = 5.0
CL_X = 3.0
CD_Z = 1.0
CD_X = 0.6
DF_SCALE = 1.0


def ground_effect_mult(v):
    return 1.0 + (q.GE_MAX - 1.0) * (v * v / (v * v + q.V_REF * q.V_REF))


def cl(straight):
    return CL_X if straight else CL_Z


def cd(straight):
    return CD_X if straight else CD_Z


def downforce(v, straight):
    return DF_SCALE * 0.5 * q.RHO * cl(straight) * q.A * v * v * ground_effect_mult(v)


def drag(v, straight):
    return 0.5 * q.RHO * cd(straight) * q.A * v * v


def wheel_load(v, straight):
    return (q.M * q.G + downforce(v, straight)) / 4.0


def mu_peak(v, d1, d2, straight):
    dfz = (wheel_load(v, straight) - q.FZ0) / q.FZ0
    return np.maximum(d1 + d2 * dfz, q.MU_MIN)


def mu_lat(v, tire, straight):
    return q.MU if tire == "flat" else mu_peak(v, q.P_DY1, q.P_DY2, straight)


def mu_long(v, tire, straight):
    return q.MU if tire == "flat" else mu_peak(v, q.P_DX1, q.P_DX2, straight)


def grip_lat(v, tire, straight):
    return mu_lat(v, tire, straight) * (q.M * q.G + downforce(v, straight)) / q.M


def grip_long(v, tire, straight):
    return mu_long(v, tire, straight) * (q.M * q.G + downforce(v, straight)) / q.M
