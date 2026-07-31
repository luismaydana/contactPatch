# Prediction registry

contactPatch makes pole-time calls for selected 2026 qualifying sessions and pre-registers each one. Pole time, and not race results, because qualifying is the cleanest experiment the sport runs: one car at a time on a clear track, minimum fuel, maximum power, no strategy, no traffic, no luck worth modeling. A race result needs a model of chaos; a pole time needs a model of a car. The mechanism is a hash commitment:

1. Before qualifying, the model is run once and the full prediction (point estimate, uncertainty bands, conditions, frozen configuration) is serialized into a single commitment string.
2. The SHA-256 of that string is published before the session runs.
3. After qualifying, the call is scored against the real pole time under rules declared inside the commitment itself, and the preimage is released.

Because the hash goes out first, a call cannot be edited, re-run, or quietly withdrawn after the result is known. Hits and misses both get published. Verification steps are in [VERIFY.md](VERIFY.md).

## Calls

| Session | Committed | Status | SHA-256 |
|---|---|---|---|
| Silverstone 2026 quali (Jul 4) | — | **Abstention**, declared Jul 2: the pipeline was not frozen yet, and predicting before freezing would break the backtest → freeze → deploy discipline this registry depends on. Silverstone became a backtest point instead. | — |
| Spa-Francorchamps 2026 quali (Jul 18) | Jul 13 | **Scored: MISS.** Real dry pole 1:44.361 vs called 1:41.999 (−2.26 %, outside the pre-declared 2σ band). Secondary top-speed call ~340 km/h ± 2 %: real 336.0 km/h, within band. Scored exactly as the pre-declared rules require. | `03ea1c08d2132e3386a2fb50bb3d5bbbdd91fc51fe6ef22bb5a6c79f61b13519`. Preimage released: [spa-2026/commitment.txt](spa-2026/commitment.txt) |
| Budapest 2026 quali (Jul 25) | Jul 24 | **Scored: MISS.** Real dry pole 1:17.207 (Norris) vs called 1:13.613 (−4.65 %, 4.19 σ, outside 2σ). Secondary top speed also missed (331.0 real vs ~319 ± 2 %). Pre-registered as the test of the Spa hypothesis, and the outcome, a global 2026 cornering-envelope bias, triggers a documented re-freeze at the summer break. | `b22f847955638ae96d47716e332284eefa140db4cc95a4c45712908e39fe9cf4`. Preimage released: [budapest-2026/commitment.txt](budapest-2026/commitment.txt) |

**The model has a rival it does not currently beat.** Multiplying a circuit's 2025 pole time by one constant scores σ 0.99% out of fold against the model's 1.414%, on the same seven circuits under the same folds. That comparison, what it does and does not establish at n = 7, and the paired season-long test now running between the two are in [null-model-2026.md](null-model-2026.md). It also documents the one round where the trivial rule collapses and the physics does not.

**The rest of the season is already sealed.** Nine calls, one per remaining callable round, committed under the frozen v4 configuration and published together under a manifest hash: [season-2026-locks.md](season-2026-locks.md). That document states, in advance, what the season is expected to produce: 3 to 8 hits out of 9, centred on 5.5, with a 37% chance of at least one strong miss. Nine out of nine would be evidence the bands were too wide, not evidence of skill.

Las Vegas is not among them. Its 2025 reference session ran on intermediates, and from v3 a wet reference refuses to produce a call at all.

One label on those two rows is wrong and is corrected here rather than quietly dropped. The "secondary top-speed call" in every commitment string is not a model output. `predict_v2.py` `predict()` computes it as `top_pred = top25 × RATIO`, last year's measured top speed scaled by a constant, and the v1 predictor does the same. It belongs in the commitment because the pole-time prediction is anchored to it and a reader should be able to see the anchor, but scoring it as though the physics produced it credits and blames the model for a number it never computed. From here it is reported as what it is: a scaled carry-over, published alongside the call rather than as part of it.

The bands and the dry-session condition live inside each commitment string. The classification rules are declared here, and their logic is self-referential on purpose: the model grades itself against its own published uncertainty, so it cannot claim precision before the session and hide behind vagueness after it. For the two v1 calls above, a result inside the 1σ band is a hit, between 1σ and 2σ is a miss within the model's own stated scatter, and outside the 2σ band is a strong miss that forces an error decomposition. From Zandvoort onward the thresholds are the ones written into each v4 string and they are not the same numbers: a hit is a call landing inside ±σ (currently ±1.414%), and a strong miss is one outside the 95% predictive band, which at n = 7 sits at 2.616σ rather than 2σ because the bands are Student-t intervals for a small sample. Either way the tighter the bands the model dares to publish, the easier it is to convict of a miss, which is the correct incentive. A wet session voids the call, since the model is dry-only. Between calls the configuration sits in parc fermé: sealed before the session, untouchable after, exactly like the cars it predicts. Any recalibration has to be a pre-declared, documented re-freeze, like the one the Budapest result triggered for the summer break.

**Superseded twice, and both are kept.** The [v3 re-freeze](refreeze-2026-v3.md), 2026-07-29, corrected five physics defects found by audit and moved σ from 1.32% to 1.460%. The [v4 re-freeze](refreeze-2026-v4.md), 2026-07-30, corrected the calibration script itself. It had been handing each held-out circuit the air density of the 2026 session it was predicting, which production cannot have. σ landed at 1.414%. The summer re-freeze below is the history both replaced, kept because the v2.2 line method and the seven-circuit evidence set came out of it.

**Summer re-freeze (2026-07-28).** The Budapest debrief pre-declared a documented
recalibration at the summer break. It is done: [refreeze-2026-summer.md](refreeze-2026-summer.md)
has the declarations (hashed before fitting), every gate result including the failed
ones, and the new frozen configuration. Calls from Zandvoort onward run under v2.3
through `scripts/predict_v2.py`; the season's operational checklist lives in
[SEASON-RUNBOOK.md](SEASON-RUNBOOK.md). The v1 path stays untouched, so Budapest
still reproduces from it bit-for-bit; Spa is verified through its released
preimage, for the lock-hygiene reason its own [README](spa-2026/README.md)
states in full.

One wording note for anyone cross-checking the frozen strings. The Spa commitment calls the four-circuit set a "blind backtest", meaning blind in the sense that the model had never seen those circuits: the tyre was fitted at Suzuka and every line is generated from geometry. The μ and σ derived from their errors are still in-sample statistics of that same set, which is how the project's validation page describes them. The frozen string can't be edited, so this note is the bridge.
