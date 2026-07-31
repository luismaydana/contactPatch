#include <algorithm>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

#include "contactpatch/control/pure_pursuit.hpp"
#include "contactpatch/sim/batch_simulator.hpp"
#include "lap_common.hpp"

using namespace contactpatch;
using namespace contactpatch::physics;
using namespace contactpatch::sim;
using namespace contactpatch::control;

struct RolloutResult {
    Real lap_time = 1e9f;
    bool clean = false;
    Real max_beta = 0.0f;
    Real min_v = 1e9f;
};

int main() {
    BatchSimulator sim;
    const std::string data_dir = CONTACTPATCH_DATA_DIR;
    if (!sim.load_track(data_dir + "/tracks/suzuka/raceline_ver.csv")) {
        std::printf("Cannot load track.\n");
        return 1;
    }
    const Real track_len = sim.get_track().get_total_length();
    const Real v0 = lap::load_initial_speed(
        data_dir + "/telemetry/2026_Japan_VER_Q_inputs.csv");
    BatchVehicleConfig cfg{};
    const BatchVehicleState st0 = lap::make_flying_start(cfg, sim.get_track(), v0);
    const auto ers_windows = lap::load_ers_windows(
        data_dir + "/sim_results/ers_schedule.csv", track_len);
    std::printf("track %.1f m, v0 %.1f m/s, %zu ERS windows\n",
                track_len, v0, ers_windows.size());

    constexpr Real kSpacing = 25.0f;
    const int M = static_cast<int>(track_len / kSpacing) + 1;
    std::vector<Real> knot_s(M);
    for (int i = 0; i < M; ++i) {
        knot_s[i] = static_cast<Real>(i) * kSpacing;
    }

    PurePursuitConfig pp = lap::make_pp_config(cfg);
    pp.margin_s_m = knot_s.data();
    pp.margin_count = M;

    const auto rollout = [&](const std::vector<Real>& m, Real t_bound) -> RolloutResult {
        RolloutResult r{};
        pp.margin_value = m.data();
        sim.initialize(cfg, st0);
        PurePursuitState pps{};
        const Real dt = 0.01f;
        const int max_steps = 16000;
        Real s_prev = 0.0f;
        Real beta_max = 0.0f;
        Real v_min = 1e9f;
        for (int k = 0; k < max_steps; ++k) {
            if (static_cast<Real>(k) * dt > t_bound) {
                return r;
            }
            BatchInputs in = compute_pure_pursuit_inputs(pp, pps, sim.get_state(),
                                                         sim.get_track(), dt);
            if (!ers_windows.empty()) {
                in.ers_override = in.ers_override
                    && lap::ers_scheduled(ers_windows, sim.get_state().s_arc_m);
            }
            sim.step(in, dt);
            const auto& s = sim.get_state();
            const Real beta = std::atan2(std::abs(s.v_lat_mps),
                                         std::max(std::abs(s.v_long_mps), 1.0f));
            if (beta > beta_max) beta_max = beta;
            if (k > 200) {
                if (s.v_long_mps < v_min) v_min = s.v_long_mps;
                if (s.v_long_mps < 3.0f) {
                    r.max_beta = beta_max;
                    r.min_v = v_min;
                    return r;
                }
            }
            if (sim.lap_state().lap_count >= 1) {
                const Real ds_wrap = (track_len - s_prev) + s.s_arc_m;
                const Real frac = (ds_wrap > 1e-3f)
                    ? (track_len - s_prev) / ds_wrap
                    : 1.0f;
                r.lap_time = (static_cast<Real>(k) + frac) * dt;
                r.max_beta = beta_max;
                r.min_v = v_min;
                r.clean = (beta_max <= 0.152f) && (v_min >= 5.0f);
                return r;
            }
            if (std::abs(s.s_arc_m - s_prev) > 30.0f) {
                r.max_beta = beta_max;
                r.min_v = v_min;
                return r;
            }
            s_prev = s.s_arc_m;
        }
        r.max_beta = beta_max;
        r.min_v = v_min;
        return r;
    };

    Real m0 = 0.88f;
    std::vector<Real> m(M, m0);
    {
        std::vector<Real> ws_s;
        std::vector<Real> ws_m;
        lap::load_margin_schedule(data_dir + "/sim_results/margin_schedule.csv", ws_s, ws_m);
        if (static_cast<int>(ws_m.size()) == M) {
            m = ws_m;
            std::printf("warm start from existing margin_schedule.csv\n");
        }
    }
    RolloutResult base = rollout(m, 1e9f);
    while (!base.clean && m0 > 0.775f) {
        m0 -= 0.02f;
        std::fill(m.begin(), m.end(), m0);
        base = rollout(m, 1e9f);
        std::printf("feasibility phase: m0 %.2f -> %.3f s clean=%d beta=%.3f\n",
                    m0, base.lap_time, base.clean ? 1 : 0, base.max_beta);
    }
    std::printf("baseline (m0 %.2f): %.3f s  clean=%d  max_beta=%.3f  min_v=%.1f\n",
                m0, base.lap_time, base.clean ? 1 : 0, base.max_beta, base.min_v);
    if (!base.clean) {
        std::printf("no clean starting point found, aborting\n");
        return 1;
    }

    Real best = base.lap_time;
    long long evals = 1;
    const Real deltas[4] = {0.04f, 0.02f, 0.01f, 0.005f};
    constexpr Real kLo = 0.78f;
    constexpr Real kHi = 1.00f;

    std::ofstream log(data_dir + "/sim_results/lap_optimizer_log.csv");
    log << "eval,delta,knot,sign,lap_time_s,clean,accepted\n";

    const std::string sched_path = data_dir + "/sim_results/margin_schedule.csv";
    const auto write_schedule = [&]() {
        std::ofstream out(sched_path);
        out << "s_m,margin\n";
        for (int k = 0; k < M; ++k) {
            out << knot_s[k] << ',' << m[k] << '\n';
        }
    };

    for (int dpass = 0; dpass < 4; ++dpass) {
        const Real delta = deltas[dpass];
        bool improved = true;
        int sweep = 0;
        while (improved && sweep < 6) {
            improved = false;
            ++sweep;
            for (int i = 0; i < M; ++i) {
                for (int sgn = 1; sgn >= -1; sgn -= 2) {
                    std::vector<Real> cand = m;
                    const Real step = delta * static_cast<Real>(sgn);
                    const int il = (i + M - 1) % M;
                    const int ir = (i + 1) % M;
                    cand[i] = std::clamp(cand[i] + step, kLo, kHi);
                    cand[il] = std::clamp(cand[il] + 0.5f * step, kLo, kHi);
                    cand[ir] = std::clamp(cand[ir] + 0.5f * step, kLo, kHi);
                    if (cand == m) {
                        continue;
                    }
                    const RolloutResult r = rollout(cand, best + 0.5f);
                    ++evals;
                    const bool accept = r.clean && r.lap_time < best - 0.002f;
                    log << evals << ',' << delta << ',' << i << ',' << sgn << ','
                        << r.lap_time << ',' << (r.clean ? 1 : 0) << ','
                        << (accept ? 1 : 0) << '\n';
                    if (accept) {
                        m = cand;
                        best = r.lap_time;
                        improved = true;
                        write_schedule();
                        break;
                    }
                }
            }
            std::printf("delta %.3f sweep %d: best %.3f s (%lld evals)\n",
                        delta, sweep, best, evals);
            std::fflush(stdout);
            log.flush();
        }
    }

    write_schedule();
    std::printf("final: %.3f s after %lld evals; margin_schedule.csv written\n",
                best, evals);
    return 0;
}
