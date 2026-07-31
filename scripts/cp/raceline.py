import numpy as np


def _normals(x, y):
    tx = np.roll(x, -1) - np.roll(x, 1)
    ty = np.roll(y, -1) - np.roll(y, 1)
    tn = np.hypot(tx, ty)
    tn[tn < 1e-9] = 1.0
    tx /= tn; ty /= tn
    return -ty, tx


def minimum_curvature(x, y, width_left, width_right, margin=0.6, ridge=0.02):
    if abs(x[0] - x[-1]) < 1e-6 and abs(y[0] - y[-1]) < 1e-6:
        x, y = x[:-1], y[:-1]
        width_left, width_right = width_left[:-1], width_right[:-1]
    n = len(x)
    nx, ny = _normals(x, y)
    I = np.eye(n)
    D2 = -2.0 * I + np.roll(I, 1, axis=1) + np.roll(I, -1, axis=1)
    A = D2 * nx
    B = D2 * ny
    bx = D2 @ x
    by = D2 @ y
    H = A.T @ A + B.T @ B + ridge * I
    g = A.T @ bx + B.T @ by
    alpha = np.linalg.solve(H, -g)
    lo = -(width_right - margin)
    hi = width_left - margin
    alpha = np.minimum(np.maximum(alpha, lo), hi)
    rx = x + alpha * nx
    ry = y + alpha * ny
    return rx, ry, alpha


def minimum_time(x, y, width_left, width_right, lap_time_fn, knots=25,
                 steps=(0.4, 0.2, 0.1), margin=0.6):
    if abs(x[0] - x[-1]) < 1e-6 and abs(y[0] - y[-1]) < 1e-6:
        x, y, width_left, width_right = x[:-1], y[:-1], width_left[:-1], width_right[:-1]
    n = len(x)
    nx, ny = _normals(x, y)
    lo = -(width_right - margin)
    hi = width_left - margin
    _, _, alpha0 = minimum_curvature(x, y, width_left, width_right, margin=margin)
    if len(alpha0) != n:
        alpha0 = alpha0[:n]
    knot_idx = np.linspace(0, n - 1, knots).astype(int)
    delta = np.zeros(knots)

    def t_of(d):
        a = np.minimum(np.maximum(alpha0 + np.interp(np.arange(n), knot_idx, d), lo), hi)
        return lap_time_fn(x + a * nx, y + a * ny), a

    best_t, _ = t_of(delta)
    for step in steps:
        for k in range(knots):
            for s in (step, -step):
                trial = delta.copy(); trial[k] += s
                t, _ = t_of(trial)
                if t < best_t - 1e-4:
                    best_t = t; delta = trial
    _, a = t_of(delta)
    return x + a * nx, y + a * ny, a


def arc_length(x, y):
    dx = np.diff(x); dy = np.diff(y)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(dx, dy))])
    return s


def to_telemetry_frame(x, y):
    import pandas as pd
    s = arc_length(x, y)
    return pd.DataFrame({"X": x * 10.0, "Y": y * 10.0, "Distance": s,
                         "Speed": np.full(len(x), 200.0)})
