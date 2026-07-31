import numpy as np
import qss_laptime as q

ETA_REGEN = 0.70
REAR_BRAKE_SHARE = 0.42
P_CLIP = 350e3
RECOVERY_CAP_J = 7e6
RECOVERY_CAP_BY_TRACK = {"Monza": 5.5e6, "Jeddah": 6.5e6, "Melbourne": 6.5e6,
                         "Spielberg": 6.5e6}


def step_speed(v, kappa_i, straight_i, ds_i, tire, p_extra, decel=False):
    a_lat = v * v * abs(kappa_i)
    ay = q.grip_accel_lat(v, tire)
    ax = q.grip_accel_long(v, tire)
    r = np.minimum(1.0, a_lat / np.maximum(ay, 1e-9))
    a_long = ax * np.sqrt(np.maximum(0.0, 1.0 - r * r))
    p_wheels = q.P_ICE + p_extra
    a_drive = np.minimum(q.F_DRIVE, p_wheels / np.maximum(v, 1.0)) / q.M
    a_tire = np.minimum(a_long, a_drive)
    a_accel = a_tire - q.drag(v, straight_i) / q.M
    if not decel:
        a_accel = np.maximum(0.0, a_accel)
    return np.sqrt(np.maximum(0.0, v * v + 2.0 * a_accel * ds_i))


def brake_harvest(v_entry, v_exit, ds_i, straight_i, dt):
    v_mid = 0.5 * (v_entry + v_exit)
    a_dec = np.maximum(0.0, (v_entry * v_entry - v_exit * v_exit) / (2.0 * ds_i))
    a_brk = np.maximum(0.0, a_dec - q.drag(v_mid, straight_i) / q.M)
    p_rear = REAR_BRAKE_SHARE * q.M * a_brk * v_mid
    return np.minimum(p_rear, q.P_ERS) * ETA_REGEN * dt
