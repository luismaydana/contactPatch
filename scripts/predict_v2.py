"""contactPatch race predictor, v4 (2026-07-30 re-freeze).

PREDICTION:  python scripts/predict_v2.py <Circuit>     (downloads that venue's
             2025 pole lap once, then works from cache)
LOCK:        python scripts/predict_v2.py --lock <Circuit>
             (same prediction, plus the commitment file and the pinned input
             lap staged under locks/<circuit>-2026/, gitignored; both move to
             predictions/<circuit>-2026/ when the call is scored)
SCORING:     python scripts/predict_v2.py --score <Circuit>
             (auto-VOID if the pole lap ran INTERMEDIATE/WET compound or the
             session weather recorded rainfall; no judgment calls after the fact)

The v1 predictor (predict_race.py) stays untouched: it is what reproduces the
Spa and Budapest commitments. New calls run through THIS file. Everything
frozen below comes from the documented v4 re-freeze
(predictions/refreeze-2026-v4.md); nothing is tuned per call. The summer and v3
re-freezes it supersedes are kept beside it rather than deleted.

The v2.2 line is the venue's 2025 pole lap itself: resampled at 5 m and
Savitzky-Golay filtered, no survey centerline, no external track data. Any
venue with one qualifying session on record is callable. Madrid is not (new
circuit, no 2025 session) and we say so instead of improvising. On sprint
weekends (Zandvoort, Singapore) the Friday sprint sessions are not inputs;
the lock lands before the GP qualifying start.

Two kinds of number sit in the frozen block below and they do not do the same
job. The tyre pair was fitted on all seven evidence circuits, so it describes
laps it has already seen. MU and SIGMA come out of the leave-one-out, where
every error was measured on the circuit its own fold trained without, so they
estimate the lap that has not been driven yet. Only the second kind is allowed
to set a band. Quoting an in-sample residual as accuracy is the easiest way a
model like this flatters itself, and the calibration is arranged so that it
cannot happen here by accident.
"""
import os, sys, hashlib, warnings
warnings.filterwarnings("ignore")
from cp import config as C
sys.path.insert(0, C.SCRIPTS)
import numpy as np
from scipy.signal import savgol_filter
from cp import v2physics as V

# ---- FROZEN v4 calibration (2026-07-30, declaration 676ab520 sealed first) ----
# Regenerate with scripts/refit_loo.py; it writes predictions/refit-v4.json.
#
# Sigma went DOWN, 1.460 -> 1.414, and that is the awkward direction to move in.
# v4 removed a leak: the leave-one-out fold had been handing each held-out
# circuit its own 2026 session air density, which production cannot have. Taking
# information away and getting a better number looks exactly like tuning, so the
# only thing separating this from tuning is that the declaration committing to
# adopt whatever came out was sealed before the refit ran (676ab520, with the
# commitment-string change declared as 15856d57).
#
# The physical reading is that the leaked value was not information, it was an
# inconsistency: 2025 geometry paired with 2026 density. Production pairs 2025
# with 2025. Two fixes landed together, the density and the pole definition, so
# the improvement is not attributable to one of them without a decomposition;
# that is reported in predictions/refreeze-2026-v4.md rather than assumed.
#
# The tyre pair did not move at all, which is the reassuring part: 1.36/-0.12
# survives a change in how the error is measured.
P_DY1, P_DY2 = 1.36, -0.12     # fitted, in-sample: 7 circuits, 5 g gate passed
MU = 0.102                     # offset %, out-of-fold (symmetric 7-fold LOO)
SIGMA = 1.414                  # scatter %, out-of-fold; also the hit threshold
RATIO = 1.0106                 # measured, 7 post-change top-speed pairs
T68, T95 = 1.159, 2.616        # Student-t (nu=6) x sqrt(1+1/7)
SG_WINDOW = 9                  # chosen; spread vs 7 and 11 declared per call
K_SMOOTH = 3                   # curvature box half-width; swept in s1 from v3 on

# circuit -> (2025 event name, 2026 quali round, banked corners)
#
# From v4 the round IS in the commitment string, so this table is inside the
# hash and correcting it breaks the call it belongs to, by design. Through v3 it
# was outside: the note here used to say that as a safety property, that no hash
# could depend on a round, so correcting seven of them was free. It was the
# opposite. The round decides which grand prix score() grades the call against,
# and leaving the referent uncommitted is the one thing a reader could not check.
# They were off by one from Singapore on, because R16 is the Kuala Lumpur
# round, a venue with no 2025 session and therefore no call, and it was
# missing from this table. Left uncorrected, --score Singapore would have
# graded the registered call against the wrong grand prix.
CIRCUITS = {
    # Zandvoort's banking stays unmodeled: worth ~0.3 s, inside the 68% band,
    # and the banked solver broke the 5 g gate. Rejected sealed, see the
    # re-freeze doc. The call is planar and says so.
    "Zandvoort": ("Dutch", 12, None),
    "Monza":     ("Italian", 13, None),
    "Baku":      ("Azerbaijan", 15, None),
    "Singapore": ("Singapore", 17, None),
    "Austin":    ("United States", 18, None),
    "Mexico":    ("Mexico City", 19, None),
    "SaoPaulo":  ("Sao Paulo", 20, None),
        # Las Vegas is absent by rule, not by choice: its 2025 reference ran on
    # intermediates, and session_2025 refuses a wet reference. Nine calls.
    "Lusail":    ("Qatar", 22, None),
    "AbuDhabi":  ("Abu Dhabi", 23, None),
}


def fmt(t):
    m = int(t // 60)
    s = t - 60.0 * m
    if round(s, 3) >= 60.0:   # rounding carried the seconds into the next minute
        m += 1
        s = 0.0
    return f"{m}:{s:06.3f}"


class WetReference(Exception):
    """The 2025 reference session was not dry, so the venue is not callable."""


def session_2025(event):
    import fastf1, logging
    logging.getLogger("fastf1").setLevel(logging.CRITICAL)
    fastf1.Cache.enable_cache(C.CACHE)
    s = fastf1.get_session(2025, event, "Q")
    s.load(telemetry=True, weather=True, messages=False)
    lap = s.laps.pick_fastest()
    # The declared wet rule covers the 2026 session. It never covered the 2025
    # REFERENCE, and Las Vegas 2025 ran on intermediates, so that call was built
    # from a wet line and a low top-speed anchor. A venue whose reference was wet
    # is not callable, the same way a venue with no session at all is not.
    compound = str(lap.get("Compound", "?")).upper()
    if compound in ("INTERMEDIATE", "WET"):
        raise WetReference(f"{event} 2025 pole ran on {compound}: no dry reference, no call")
    tel = lap.get_telemetry()
    w = s.weather_data
    rho = (float(w["Pressure"].median()) * 100.0) / (287.05 * (float(w["AirTemp"].median()) + 273.15))
    d = {"x": tel["X"].values / 10.0, "y": tel["Y"].values / 10.0,
         "top_kmh": float(tel["Speed"].max()), "rho": rho,
         "lap_s": float(lap["LapTime"].total_seconds())}
    # input pin: anchored to THIS data, not whatever the API serves later
    h = hashlib.sha256()
    h.update(np.asarray(d["x"], dtype="<f8").tobytes())
    h.update(np.asarray(d["y"], dtype="<f8").tobytes())
    h.update(np.float64(d["top_kmh"]).tobytes())
    h.update(np.float64(d["lap_s"]).tobytes())
    d["data_sha"] = h.hexdigest()[:16]
    return d


def build_line(gx, gy, window=SG_WINDOW):
    x, y = V._resample(gx, gy, 5.0)
    return V.line_to_arrays(savgol_filter(x, window, 3), savgol_filter(y, window, 3))


def blind_time(name):
    ev25, _, bank_spec = CIRCUITS[name]
    s25 = session_2025(ev25)
    V.RHO = s25["rho"]                       # carry-over: same venue, 2025 session
    cap = V.vcap_from_top(s25["top_kmh"] * RATIO / 3.6)
    # Both smoothing stages, not just the visible one. Sweeping the SG window while
    # a second box filter stayed pinned reported a spread six times smaller than the
    # method's real sensitivity.
    ts = {}
    for w, kk in ((7, K_SMOOTH), (SG_WINDOW, K_SMOOTH), (11, K_SMOOTH),
                  (SG_WINDOW, K_SMOOTH - 1), (SG_WINDOW, K_SMOOTH + 1)):
        dist, rx, ry = build_line(s25["x"], s25["y"], w)
        bank = None
        if bank_spec:
            kappa = V.calculate_curvature(rx, ry, kk)
            bank = V.bank_profile_by_distance(dist, kappa, bank_spec)
        m = V.lap_metrics(dist, rx, ry, P_DY1, P_DY2, cap, bank, k_smooth=kk)
        ts[(w, kk)] = m["t_sim"]
        if w == SG_WINDOW and kk == K_SMOOTH:
            main = m
    base = ts[(SG_WINDOW, K_SMOOTH)]
    s1 = max(abs(v - base) for v in ts.values()) / base * 100.0
    if s1 > 0.8:
        print(f"  [stability gate] filter spread {s1:.2f}% > 0.8%, declare in the call")
    return main, cap, s25["top_kmh"], s25["rho"], s1


def predict(name, lock=False):
    ev25, rnd, bank_spec = CIRCUITS[name]
    s25 = session_2025(ev25)
    m, cap, top25, rho, s1 = blind_time(name)
    t = m["t_sim"]
    pole = t / (1 + MU / 100.0)
    b68 = SIGMA * T68 / 100.0
    b95 = SIGMA * T95 / 100.0
    lo68, hi68 = pole * (1 - b68), pole * (1 + b68)
    lo95, hi95 = pole * (1 - b95), pole * (1 + b95)
    top_pred = top25 * RATIO
    # round= is inside the hash from v4 on. It was outside it through v3, and an
    # adversarial review named the consequence: the round selects which 2026
    # session --score fetches, so an author who disliked a Saturday could edit
    # the table, grade the call against a different grand prix, and every hash
    # would still verify. The seal bound the prediction and not the referent.
    # Editing the table now breaks the hash that depends on it, which is what a
    # reader was entitled to assume in the first place.
    commit = (f"contactPatch v4 | {name} 2026 quali POLE (dry) | round={rnd} | frozen pre-quali | "
              f"refreeze=2026-v4 p=({P_DY1},{P_DY2}) mu={MU}% sigma={SIGMA}%oof "
              f"ratio={RATIO} rho={rho:.4f}(2025 carry-over) | line=2025-pole-gps sg{SG_WINDOW} "
              f"s1={s1:.2f}% | data={s25['data_sha']} | V_CAP={cap:.1f} | "
              f"POINT={fmt(pole)} | 68pct=[{fmt(lo68)},{fmt(hi68)}] | "
              f"95pct=[{fmt(lo95)},{fmt(hi95)}] | top~{top_pred:.0f}kmh | "
              f"wet=VOID(inter-wet-compound-or-rainfall) | "
              f"hit=inside {SIGMA}% | strong-miss=outside 95pct band")
    h = hashlib.sha256(commit.encode()).hexdigest()
    print(f"=== {name} 2026 pole, v4 (dry) ===")
    print(f"POINT  {fmt(pole)}   68% [{fmt(lo68)}, {fmt(hi68)}]   95% [{fmt(lo95)}, {fmt(hi95)}]")
    print(f"model {t:.3f}s   V_CAP {cap:.1f} m/s   rho {rho:.4f}   top ~{top_pred:.0f} km/h   "
          f"G peak {m['g_peak']:.2f}   filter spread {s1:.2f}%   data pin {s25['data_sha']}")
    print(f"SHA-256  {h}")
    if lock:
        # locks/ is gitignored, so the preimage cannot reach the public repo
        # before scoring. Exact bytes, no trailing newline: the file's sha256
        # IS the registered hash (VERIFY.md).
        d = os.path.join(C.ROOT, "locks", f"{name.lower()}-2026")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "commitment_v4.txt"), "wb") as f:
            f.write(commit.encode("utf-8"))
        np.savez(os.path.join(d, "input_2025_lap.npz"), x=s25["x"], y=s25["y"],
                 top_kmh=s25["top_kmh"], lap_s=s25["lap_s"])
        print(f"LOCKED to locks/{name.lower()}-2026/ (gitignored staging).")
        print("Publish ONLY the SHA-256 before quali. After scoring, move both files")
        print(f"into predictions/{name.lower()}-2026/ to release the preimage.")
    return commit, h


def parse_secs(s):
    m, sec = s.split(":")
    return int(m) * 60 + float(sec)


def registered_sha(name):
    """The hash this circuit's call was sealed under, read from the public
    manifest. None if the circuit is not in the sealed set."""
    p = os.path.join(C.ROOT, "predictions", "season-2026-manifest.txt")
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        for ln in f:
            parts = ln.split()
            if len(parts) == 2 and parts[0].lower() == name.lower():
                return parts[1]
    return None


def load_commitment(name):
    """The call as it was registered. Staged in locks/ before scoring, moved to
    predictions/ when the preimage is released.

    The file is checked against season-2026-manifest.txt before it is returned.
    It used to be returned unchecked, which meant score() would grade whatever
    bytes sat at that path: hand-place a different string on race day and the
    verdict comes out of it, with only a printed SHA-256 that a reader would have
    had to diff against the manifest themselves to catch. The manifest is public
    and the check is free, so there is no reason the tool should not do it."""
    leaf = f"{name.lower()}-2026"
    want = registered_sha(name)
    for base in ("locks", "predictions"):
        for stem in ("commitment_v4.txt", "commitment_v23.txt"):
            p = os.path.join(C.ROOT, base, leaf, stem)
            if not os.path.exists(p):
                continue
            with open(p, "rb") as f:
                text = f.read().decode("utf-8")
            got = hashlib.sha256(text.encode()).hexdigest()
            # `if want and ...` failed OPEN: registered_sha returns None when the
            # manifest is missing, when the circuit is not listed, or when a line
            # is malformed, and each of those returned the file unchecked and
            # silently. Moving the manifest aside was enough to grade any bytes
            # at all. A guard that disappears when its reference is removed is
            # not a guard, so absence is now a refusal.
            if want is None:
                print(f"REFUSING TO SCORE {name}: no registered hash. Either "
                      f"predictions/season-2026-manifest.txt is missing or "
                      f"malformed, or {name} is not in the sealed set. A call "
                      f"that is not in the manifest was never committed.")
                return None, None
            if got != want:
                print(f"REFUSING TO SCORE {name}: {p} hashes to {got[:16]}, "
                      f"but the manifest registers {want[:16]}. This file is not "
                      f"the sealed call.")
                return None, None
            return text, p
    return None, None


def field(commit, key):
    for tok in commit.replace(" | ", " ").split():
        if tok.startswith(key + "="):
            return tok[len(key) + 1:]
    return None


def registered_thresholds(commit, pred):
    """The verdict rules as SEALED, not as currently configured.

    Reading SIGMA off the module would let a later recalibration regrade a
    season that is already committed, with every published hash still checking
    out, and that is not a hypothetical: the harvest fix on the January list
    moves sigma by construction. So sigma comes out of the string, and T95 is
    recovered from the 95% band the same string carries, which pins it without
    needing a field the sealed set does not have.
    """
    sig = float(field(commit, "sigma").rstrip("%oof"))
    hi95 = parse_secs(field(commit, "95pct").split(",")[1].rstrip("]"))
    t95 = (hi95 / pred - 1.0) * 100.0 / sig
    return sig, t95


def score(name):
    import fastf1, logging
    logging.getLogger("fastf1").setLevel(logging.CRITICAL)
    fastf1.Cache.enable_cache(C.CACHE)

    # The committed string is the authority: re-deriving at scoring time would
    # grade a number nobody registered, which is what the protocol exists to stop.
    commit, path = load_commitment(name)
    if commit is None:
        print(f"{name}: no commitment found under locks/ or predictions/. "
              f"A call that was never locked cannot be scored; run --lock before the session.")
        return
    pred = parse_secs(field(commit, "POINT"))
    pinned = field(commit, "data")
    sigma_c, t95_c = registered_thresholds(commit, pred)
    print(f"commitment {path}")
    print(f"  sha256 {hashlib.sha256(commit.encode()).hexdigest()}")
    print(f"  registered POINT {fmt(pred)}   data pin {pinned}")
    print(f"  registered bands sigma {sigma_c:.2f}%  t95 {t95_c:.3f}  "
          f"(module today: {SIGMA:.2f}% / {T95:.3f})")
    if abs(sigma_c - SIGMA) > 5e-3 or abs(t95_c - T95) > 5e-3:
        print(f"  NOTE: the model has been recalibrated since this call was sealed. "
              f"Scoring against the REGISTERED bands, which is the only honest choice: "
              f"grading an old call by new thresholds would rewrite a result the "
              f"commitment already fixed.")

    # The SEALED round is the authority, not the table. v4 put round= inside the
    # commitment string and then still resolved the session from CIRCUITS, which
    # made the sealed field decorative: edit the table after a bad Saturday and
    # score() fetches a different grand prix while every hash still verifies.
    # Adding a field to the string protects nothing until the code reads it back.
    rnd_sealed = field(commit, "round")
    _, rnd_table, _ = CIRCUITS[name]
    if rnd_sealed is None:
        print(f"REFUSING TO SCORE {name}: the commitment carries no round= field. "
              f"Pre-v4 strings did not bind their referent and cannot be scored "
              f"by this path.")
        return
    rnd = int(rnd_sealed)
    if rnd != rnd_table:
        print(f"REFUSING TO SCORE {name}: the sealed call names round {rnd}, the "
              f"circuit table says {rnd_table}. The table was edited after the "
              f"call was sealed; the sealed value is the one that counts.")
        return
    s = fastf1.get_session(2026, rnd, "Q")
    # messages=True or FastF1 never populates Deleted, and the track-limits
    # filter below silently becomes a no-op.
    s.load(telemetry=False, weather=True, messages=True)
    # A lap deleted for track limits was never pole, and the commitment says POLE.
    laps = s.laps
    if "Deleted" in laps.columns:
        kept = laps[~laps["Deleted"].fillna(False).astype(bool)]
        n_del = len(laps) - len(kept)
        if n_del:
            print(f"  {n_del} deleted lap(s) excluded before picking pole")
        if len(kept):
            laps = kept
    pole_lap = laps.pick_fastest()
    real = float(pole_lap["LapTime"].total_seconds())
    compound = str(pole_lap.get("Compound", "?")).upper()
    rained = bool(s.weather_data["Rainfall"].any()) if "Rainfall" in s.weather_data else False
    if compound in ("INTERMEDIATE", "WET") or rained:
        print(f"{name}: VOID (declared wet rule: compound={compound}, rainfall={rained}). "
              f"Real fastest lap {fmt(real)} goes on the record, unscored.")
        return

    # A drift here does not move the verdict; the registered POINT stands. It
    # says the upstream data changed, which is the whole point of pinning it.
    m, cap, top25, rho, s1 = blind_time(name)
    live_pred = m["t_sim"] / (1 + MU / 100.0)
    live_pin = session_2025(CIRCUITS[name][0])["data_sha"]
    if live_pin == pinned:
        print(f"  pin OK: input telemetry unchanged since the lock")
    else:
        print(f"  PIN MISMATCH: registered {pinned}, upstream now {live_pin}. "
              f"The 2025 telemetry was revised after the lock. Scoring the registered "
              f"call, as declared; today's re-run would give {fmt(live_pred)}.")

    err = 100 * (pred - real) / real
    if abs(err) <= sigma_c:
        verdict = "HIT"
    elif abs(err) <= sigma_c * t95_c:
        verdict = "MISS (inside stated scatter)"
    else:
        verdict = "STRONG MISS (re-freeze trigger)"
    print(f"{name}: pred {fmt(pred)}  real {fmt(real)}  err {err:+.2f}%  {verdict}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__)
    elif a[0] == "--score":
        score(a[1])
    elif a[0] == "--lock":
        predict(a[1], lock=True)
    else:
        predict(a[0])
