# -*- coding: utf-8 -*-
"""contactPatch v2 physics (frozen at the 2026 summer re-freeze; v2.3 calls
use it through scripts/predict_v2.py).
Self-contained on purpose: the v1 path (qss_laptime.py + cp/qss.py) is untouched
so the Spa and Budapest commitments keep reproducing bit-for-bit. Differences
from v1 are marked V2.

V2 changes vs the frozen model:
  - post-Miami TD power: MGU-K deploy 350 kW only in the KEY acceleration zones
    (approximated as the two longest zones of the lap), 250 kW elsewhere.
  - tyre pair (P_DY1, P_DY2) is a run-time argument (re-identified, not 1.8/-0.17).
  - V2.2: the racing line is the venue's real pole lap directly (resampled and
    filtered); the survey-centerline rebuild is retired.
  - V2.3: deployment draws from a state-of-charge ledger that harvests under
    braking (350 kW into the 4 MJ store, 7 MJ/lap cap), instead of a fixed tank.
Everything else (integrator structure, ellipse, taper, drag/aero constants,
curvature estimator) is byte-identical in intent to v1 so that any difference
in output is attributable to the declared changes.

What the solver may assume: dry session, planar track, one car alone on a clear
lap, quasi-steady state at every sample. The last one carries the weight. It
says the car is always already at the limit the tyre allows for the curvature
under it, which is wrong for the few tenths spent rotating between phases and
right for the seconds spent committed inside them. A qualifying lap is mostly
the second kind of time, so the approximation holds and its residual is carried
in sigma rather than argued away. It breaks where you would expect: banking
(that load is not in a planar force balance), wet (different tyre, call voids),
and turn-in, where the car is still rotating and the model has it settled.
"""
import numpy as np

# ---- constants identical to frozen v1 (RHO became per-session in v2.1) ----
M = 768.0; A = 1.5; G = 9.81
RHO = 1.225   # v2.1: set per run from measured session weather (P/(R*T))
CL_Z = 5.0; CD_Z = 1.0; CD_X = 0.6
F_DRIVE = 12000.0; F_BRAKE = 38000.0
P_ICE = 400_000.0
ETA_ERS = 0.92            # deployment: stored joules -> joules at the wheels
ETA_REGEN = 0.70          # recovery: joules at the wheels -> stored joules. One name
                          # used to serve both, which is how the harvest side spent two
                          # seasons crediting the battery at the deploy figure.
WRAP_TOL = 0.5            # m/s; closure gate G3
ENERGY_ERS_PER_LAP = 4_000_000.0
KAPPA_STRAIGHT = 0.003
MGUK_TAPER_START = 80.56; MGUK_TAPER_END = 98.61
GE_MAX = 2.0; V_REF = 40.0
P_DX1 = 1.9; P_DX2 = -0.17
FZ0 = 2000.0; MU_MIN = 0.3

# ---- V2: post-Miami TD deployment powers ----
P_ERS_KEY = 350_000.0   # key acceleration zones (approx: 2 longest zones)
P_ERS_SEC = 250_000.0   # everywhere else on the lap

# ---- V2.3 energy ledger: harvest during the lap (all public spec, no fits) ----
E_STORE = 4_000_000.0     # ES capacity, full at the start of the flying lap
P_HARVEST = 350_000.0     # MGU-K recovery power in braking zones
HARVEST_CAP = 7_000_000.0 # per-lap harvest limit (TD figure)
N_KEY_ZONES = 2


def calculate_curvature(x, y, k=3):
    w = 2 * k + 1
    kernel = np.ones(w) / w
    xp = np.pad(x, k, mode="edge"); yp = np.pad(y, k, mode="edge")
    x = np.convolve(xp, kernel, mode="valid"); y = np.convolve(yp, kernel, mode="valid")
    dx = np.gradient(x); dy = np.gradient(y)
    ddx = np.gradient(dx); ddy = np.gradient(dy)
    return np.abs(dx * ddy - dy * ddx) / np.power(dx ** 2 + dy ** 2, 1.5)


def ground_effect_mult(v):
    return 1.0 + (GE_MAX - 1.0) * (v * v / (v * v + V_REF * V_REF))


def downforce_z(v):
    return 0.5 * RHO * CL_Z * A * v * v * ground_effect_mult(v)


def drag(v, straight):
    cd = CD_X if straight else CD_Z
    return 0.5 * RHO * cd * A * v * v


def mguk_taper(v):
    span = MGUK_TAPER_END - MGUK_TAPER_START
    return min(1.0, max(0.0, (MGUK_TAPER_END - v) / span))


def wheel_load(v):
    return (M * G + downforce_z(v)) / 4.0


def mu_peak(v, d1, d2):
    dfz = (wheel_load(v) - FZ0) / FZ0
    return np.maximum(d1 + d2 * dfz, MU_MIN)


def grip_accel_lat(v, p_dy1, p_dy2):
    return mu_peak(v, p_dy1, p_dy2) * (M * G + downforce_z(v)) / M


def grip_accel_long(v):
    return mu_peak(v, P_DX1, P_DX2) * (M * G + downforce_z(v)) / M


def corner_speed(kappa, p_dy1, p_dy2, v_cap, bank=None):
    """Banked corner balance: v^2 k (cos t - mu sin t) <= mu (g cos t + DF/M) + g sin t.
    bank=None reproduces the flat formula exactly (cos=1, sin=0)."""
    v = np.full_like(kappa, 25.0)
    if bank is None:
        ct, st = 1.0, 0.0
    else:
        ct, st = np.cos(bank), np.sin(bank)
    for _ in range(40):
        mu = mu_peak(v, p_dy1, p_dy2)
        num = mu * (G * ct + downforce_z(v) / M) + G * st
        den = np.maximum(kappa, 1e-9) * np.maximum(ct - mu * st, 0.05)
        v_new = np.sqrt(num / den)
        v = 0.5 * v + 0.5 * np.minimum(v_new, v_cap)
    return np.minimum(v, v_cap)


def lap_metrics(dist, x, y, p_dy1, p_dy2, v_cap, bank=None, k_smooth=3):
    """QSS with V2 deployment. x/y in meters, dist arc-length in meters.

    k_smooth is the curvature box-filter half-width. It was hard-coded, which
    made it invisible to the published stability figure while being worth more
    than sigma across its plausible range. It is an argument now so the sweep
    can reach it.
    """
    kappa = calculate_curvature(x, y, k_smooth)
    straight = np.abs(kappa) < KAPPA_STRAIGHT
    n = len(dist); ds = np.diff(dist)
    v_env = corner_speed(kappa, p_dy1, p_dy2, v_cap, bank)

    if bank is None:
        bct = np.ones(n); bst = np.zeros(n)
    else:
        bct, bst = np.cos(bank), np.sin(bank)
    v_back = v_env.copy()
    for i in range(n - 2, -1, -1):
        v = v_back[i + 1]
        a_lat = max(0.0, v * v * kappa[i + 1] * bct[i + 1] - G * bst[i + 1])
        ay = grip_accel_lat(v, p_dy1, p_dy2); ax = grip_accel_long(v)
        r = min(1.0, a_lat / max(ay, 1e-9))
        a_long = ax * np.sqrt(max(0.0, 1.0 - r * r))
        a_tire = min(a_long, F_BRAKE / M)
        a_brake = a_tire + drag(v, straight[i + 1]) / M
        v_back[i] = min(v_env[i], np.sqrt(v * v + 2.0 * a_brake * ds[i]))

    def forward(deploy_power=None, deploy_notaper=None, v_start=None):
        v = v_back.copy()
        if v_start is not None:
            v[0] = min(v_back[0], v_start)
        for i in range(1, n):
            vp = v[i - 1]
            a_lat = max(0.0, vp * vp * kappa[i - 1] * bct[i - 1] - G * bst[i - 1])
            ay = grip_accel_lat(vp, p_dy1, p_dy2); ax = grip_accel_long(vp)
            r = min(1.0, a_lat / max(ay, 1e-9))
            a_long = ax * np.sqrt(max(0.0, 1.0 - r * r))
            p_ers = 0.0
            if deploy_power is not None and deploy_power[i - 1] > 0.0:
                tap = 1.0 if (deploy_notaper is not None and deploy_notaper[i - 1]) \
                    else mguk_taper(vp)
                p_ers = deploy_power[i - 1] * ETA_ERS * tap
            a_drive = min(F_DRIVE, (P_ICE + p_ers) / max(vp, 1.0)) / M
            a_tire = min(a_long, a_drive)
            a_accel = max(0.0, a_tire - drag(vp, straight[i - 1]) / M)
            v[i] = min(v_back[i], np.sqrt(vp * vp + 2.0 * a_accel * ds[i - 1]))
        return v

    # A flying lap is a loop, so the speed the car leaves the timing line with has to
    # be the speed it arrives with. Seeding from the braking envelope alone handed it
    # 13-22 m/s it never earned. Iterate the seed to the periodic fixpoint; the map is
    # a contraction (each pass can only lower v[0]) so this converges immediately, and
    # the loop is bounded rather than trusted.
    v_no_ers = forward(None)
    for _ in range(8):
        if abs(v_no_ers[0] - v_no_ers[-1]) <= WRAP_TOL:
            break
        v_no_ers = forward(None, v_start=v_no_ers[-1])

    # Below this speed the drive-force cap binds with or without deployment, so extra
    # electrical power buys nothing. Using combustion power alone put the boundary at
    # 33.3 m/s instead of 52.5 and mis-ranked the zones.
    v_FL = (P_ICE + P_ERS_SEC * ETA_ERS) / F_DRIVE
    is_accel = np.zeros(n, dtype=bool)
    for i in range(n - 1):
        if v_no_ers[i + 1] > v_no_ers[i] and v_no_ers[i] >= v_FL:
            is_accel[i] = True
    zones = []; start = None
    for i in range(n):
        if is_accel[i]:
            if start is None: start = i
        else:
            if start is not None: zones.append((start, i - 1)); start = None
    if start is not None: zones.append((start, n - 2))
    zones.sort(key=lambda z: -(z[1] - z[0]))

    # V2: zone rank sets POWER. V2.1: key zones hold full power (no speed
    # taper: the TD maintains 350 kW there, superclipping 2-4 s); secondary
    # zones keep 250 kW with the original taper. V2.3: the budget is a state
    # of charge walked in TRACK ORDER. The 4 MJ store drains under deployment
    # and the MGU-K refills it at 350 kW in every braking zone (times the same
    # one-way efficiency the deploy side uses, capped by the store and by the
    # 7 MJ per-lap harvest limit). Same reason the 2026 cars lift-and-coast:
    # the lap's usable energy is far more than the store alone.
    deploy_power = np.zeros(n)
    deploy_notaper = np.zeros(n, dtype=bool)
    energy = 0.0
    harvested = 0.0
    zone_at = {}
    for rank, (a, b) in enumerate(zones):
        key = rank < N_KEY_ZONES
        for i in range(a, b + 1):
            zone_at[i] = key
    braking = np.zeros(n, dtype=bool)
    braking[:-1] = v_no_ers[1:] < v_no_ers[:-1] - 1e-6
    soc = E_STORE
    for i in range(n - 1):
        dt_i = ds[i] / max(v_no_ers[i], 1.0)
        if i in zone_at:
            key = zone_at[i]
            p_zone = P_ERS_KEY if key else P_ERS_SEC
            tap = 1.0 if key else mguk_taper(v_no_ers[i])
            e_i = p_zone * tap * dt_i
            if e_i > 1e-6 and soc >= e_i:
                deploy_power[i] = p_zone; deploy_notaper[i] = key
                energy += e_i; soc -= e_i
        elif braking[i] and harvested < HARVEST_CAP:
            gain = min(P_HARVEST * ETA_REGEN * dt_i,
                       HARVEST_CAP - harvested, E_STORE - soc)
            soc += gain; harvested += gain

    # Same closure condition on the deployed lap. The energy schedule was built from
    # v_no_ers, so this converges from the same seed rather than fighting it.
    v_sim = forward(deploy_power, deploy_notaper)
    for _ in range(8):
        if abs(v_sim[0] - v_sim[-1]) <= WRAP_TOL:
            break
        v_sim = forward(deploy_power, deploy_notaper, v_start=v_sim[-1])

    def lap_time(vv):
        vs = 0.5 * (vv[:-1] + vv[1:])
        return float(np.sum(ds / np.maximum(vs, 1.0)))

    glat_kin = v_sim * v_sim * np.abs(kappa) / G
    glat = np.maximum(0.0, v_sim * v_sim * np.abs(kappa) * bct - G * bst) / G
    return {"t_sim": lap_time(v_sim), "t_no_ers": lap_time(v_no_ers),
            "g_peak_kinematic": float(glat_kin.max()),
            "v_sim": v_sim, "v_env": v_env, "kappa": kappa, "dist": dist,
            "energy": energy, "g_peak": float(glat.max()),
            "g_p99": float(np.percentile(glat, 99)),
            "top_sim_kmh": float(v_sim.max() * 3.6)}


def vcap_from_top(top_mps):
    return max(92.0, top_mps * 1.04)   # identical structural rule to v1


# ================= line tools: GPS pole lap -> centerline-frame offset line =====

def _umeyama(src, dst):
    """similarity transform (R, s, t) minimizing ||s*R*src + t - dst||."""
    mu_s = src.mean(0); mu_d = dst.mean(0)
    sc = src - mu_s; dc = dst - mu_d
    cov = dc.T @ sc / len(src)
    U, D, Vt = np.linalg.svd(cov)
    S = np.eye(2)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0: S[1, 1] = -1
    R = U @ S @ Vt
    var = (sc ** 2).sum() / len(src)
    s = np.trace(np.diag(D) @ S) / var
    t = mu_d - s * R @ mu_s
    return R, s, t


def _resample(x, y, step=5.0):
    dx = np.diff(x); dy = np.diff(y)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(dx, dy))])
    si = np.arange(0.0, s[-1], step)
    return np.interp(si, s, x), np.interp(si, s, y)


def align_lap_to_centerline(gx, gy, cx, cy, iters=40):
    """ICP with similarity transform; principal-axis + reflection init sweep."""
    gx, gy = _resample(gx, gy); P = np.column_stack([gx, gy])
    C = np.column_stack([cx, cy])
    Pc = P - P.mean(0); Cc = C - C.mean(0)

    def pca_angle(X):
        u, _, _ = np.linalg.svd(X.T @ X)
        return np.arctan2(u[1, 0], u[0, 0])

    scale0 = np.sqrt((Cc ** 2).sum() / len(C)) / np.sqrt((Pc ** 2).sum() / len(P))
    best = None
    from scipy.spatial import cKDTree
    tree = cKDTree(C)
    for extra in (0.0, np.pi):
        for refl in (1.0, -1.0):
            th = pca_angle(Cc) - pca_angle(Pc) + extra
            R0 = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
            F = np.diag([1.0, refl])
            Q = (scale0 * (R0 @ F) @ Pc.T).T + C.mean(0)
            for _ in range(iters):
                d, j = tree.query(Q)
                R, s, t = _umeyama(Q, C[j])
                Q = (s * R @ Q.T).T + t
            d, j = tree.query(Q)
            rms = float(np.sqrt((d ** 2).mean()))
            if best is None or rms < best[0]:
                best = (rms, Q)
    return best[1], best[0]


def offsets_on_centerline(Q, cx, cy, wl, wr, smooth_w=5, margin=0.3):
    """signed lateral offset of aligned lap Q at each centerline node, smoothed
    and clamped to the track width. Returns rebuilt line + diagnostics."""
    tx = np.roll(cx, -1) - np.roll(cx, 1); ty = np.roll(cy, -1) - np.roll(cy, 1)
    tn = np.hypot(tx, ty); tn[tn < 1e-9] = 1.0
    nx, ny = -ty / tn, tx / tn
    from scipy.spatial import cKDTree
    tq = cKDTree(Q)
    alpha = np.zeros(len(cx))
    for i in range(len(cx)):
        _, j = tq.query([cx[i], cy[i]])
        alpha[i] = (Q[j, 0] - cx[i]) * nx[i] + (Q[j, 1] - cy[i]) * ny[i]
    k = np.ones(smooth_w) / smooth_w
    ap = np.concatenate([alpha[-smooth_w:], alpha, alpha[:smooth_w]])
    alpha_s = np.convolve(ap, k, mode="same")[smooth_w:-smooth_w]
    alpha_c = np.clip(alpha_s, -(wr - margin), wl - margin)
    rx = cx + alpha_c * nx; ry = cy + alpha_c * ny
    # declared line gate metric: rebuilt line vs the ALIGNED GPS lap (not vs centerline)
    tl = cKDTree(np.column_stack([rx, ry]))
    d_gps, _ = tl.query(Q)
    return rx, ry, {"mean_abs_off": float(np.abs(alpha_c).mean()),
                    "max_abs_off": float(np.abs(alpha_c).max()),
                    "clipped_frac": float(np.mean(np.abs(alpha_s - alpha_c) > 1e-6)),
                    "rms_line_vs_gps": float(np.sqrt((d_gps ** 2).mean()))}


def line_to_arrays(rx, ry):
    dx = np.diff(rx); dy = np.diff(ry)
    dist = np.concatenate([[0.0], np.cumsum(np.hypot(dx, dy))])
    return dist, rx, ry


def bank_profile_by_distance(dist, kappa, windows, ramp_m=25.0):
    """windows: list of (d0, d1, degrees), distances from public circuit specs.
    The angle ramps linearly over ramp_m at each edge (no hard steps: a hard
    step next to a banked apex creates a fictitious tyre-G spike)."""
    theta = np.zeros(len(dist))
    for d0, d1, deg in windows:
        th = np.deg2rad(deg)
        up = np.clip((dist - d0) / ramp_m, 0.0, 1.0)
        dn = np.clip((d1 - dist) / ramp_m, 0.0, 1.0)
        theta = np.maximum(theta, th * np.minimum(up, dn))
    return theta


def bank_profile(dist, kappa, corner_bank_deg, kappa_thr=0.006):
    """Build theta(s). corner_bank_deg: {corner_index_1based: degrees}; corners are
    contiguous kappa>thr segments in track order. Angles from public circuit specs."""
    n = len(dist); inb = kappa > kappa_thr
    theta = np.zeros(n); idx = 0; i = 0
    while i < n:
        if inb[i]:
            j = i
            while j < n and inb[j]: j += 1
            idx += 1
            if idx in corner_bank_deg:
                theta[i:j] = np.deg2rad(corner_bank_deg[idx])
            i = j
        else:
            i += 1
    return theta
