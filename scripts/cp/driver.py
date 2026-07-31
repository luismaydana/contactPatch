from cp import qss as cpq


def fit_margin(tel, tire="pacejka", lo=0.80, hi=1.20, iters=34):
    t_real = cpq.compute_metrics(tel, tire, 1.0)["t_real"]
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        ts = cpq.compute_metrics(tel, tire, mid)["t_sim"]
        if ts > t_real:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def simulate(tel, skill, tire="pacejka"):
    return cpq.compute_metrics(tel, tire, skill)


def skill_to_pct(margin):
    return 100.0 * (margin - 1.0)
