# Known issues

Defects I found in this project, published before anyone asked for them. Every entry below was verified against the source or against data rather than suspected, and each one says what it costs and why it is or is not being fixed right now.

The reason this file exists is narrow. A registry that publishes its misses and hides its bugs has only moved the hiding place. If a reader is going to be asked to trust a σ, they should be able to see the list of things that could be wrong with the machine that produced it.

## An earlier version of this file was wrong about its own central rule

It said the ten 2026 calls were committed and **their hashes were public**, and used that as the reason five measured physics defects were being left to run. The hashes were never public. Verified on 2026-07-29: no remote branch contained the commit that created them, and the public remote had no knowledge of `season-2026-locks.md`. Parc fermé was being applied to something that had never entered parc fermé.

A commitment nobody has seen is not a commitment. The whole force of commit-reveal is the public timestamp, and there was none, so **section A is being corrected rather than tolerated**. The [v3 re-freeze](predictions/refreeze-2026-v3.md) fixes all five, and its declaration was sealed before the first line changed, because fixing physics after watching two calls miss is exactly the situation where a person's judgement should not be trusted unsupervised.

What that means for the entries below: **section A is history, not a live defect list.** Each one records what was wrong, what it cost, and it now also records that the fix landed. Section B is unchanged and still live.

The two rules that remain, neither a matter of taste:

**A published hash is untouchable.** Spa and Budapest were posted publicly before their sessions, so `predict_race.py` stays byte-frozen forever and the v1 defects in section A were never candidates for correction. That is what parc fermé means when it actually applies.

**Anything in the C++ core is not touched without a build.** No compiler toolchain is available, so no C++ change can be compiled or checked against the 23-case suite. Editing physics blind is worse than a known bug.

---

## A. Found by audit, fixed in the v3 re-freeze

Every entry was verified against source, its cost measured, and the correction declared in advance. They are kept in full rather than deleted, because a defect list that erases its entries once they are fixed is a marketing document.

### A0. The lap does not close, and the car is handed speed it never earned

The largest defect on this list, found last, and it sits inside all ten sealed calls.

A flying lap is a loop: the speed at the timing line on the way out has to be the speed the car arrives with on the way in. The forward pass seeds itself from the braking envelope, `v = v_back.copy()`, so the lap **starts** at whatever the grip limit allows at that point and never checks that the end of the lap could reach it. Measured across sealed circuits:

| | v at the line | v at the end | handed for free |
|---|---|---|---|
| Monza | 101.60 | 83.04 | **+18.56 m/s** |
| Zandvoort | 95.18 | 82.14 | +13.03 m/s |
| Singapore | 92.26 | 69.79 | +22.46 m/s |
| Mexico City | 102.47 | 80.50 | +21.97 m/s |

Nineteen metres per second on average, appearing from nothing at the start/finish line. It always runs one way, because the seed is an upper bound the tail of the lap cannot generally meet, so the model always starts faster than a real car could and the lap always comes out short.

**Cost, measured** by iterating the seed to the periodic fixpoint on a copy of the module and reporting only differences:

| | |
|---|---|
| mean | **+0.914%** |
| worst | **+1.667%** (Mexico City), then 1.199% (Monza), 0.505% (Singapore), 0.287% (Zandvoort) |

That is larger than A1 and larger than A3. It is 69% of σ on average and **126% of σ at Mexico City**, and because it varies by a factor of six between circuits it is scatter rather than a bias the calibration could have absorbed. A meaningful part of the 1.32% the model reports as its uncertainty is this.

There is a second sting worth naming, because it is about how the mistake survived. `ARCHITECTURE.md` argues the correctness of the two-pass envelope as an induction, and that argument is right; I checked it and one sweep really is the fixpoint. But its stated base case is "the last point is capped by its own grip limit and there is nothing after it to brake for", and on a lap that closes, *there is*. The proof is sound for a road and the code drives a circuit. Writing the induction down is what makes the defect visible in hindsight, which is an argument for writing them down.

**Fixed in v3.** `v2physics.py:177-181` and `237-241` iterate the seed until `|v[0] − v[−1]| ≤ WRAP_TOL`, so the pass now converges to the periodic fixpoint a closed circuit demands. Every sealed call from v3 on contains the fix, and the ten v2.3 strings that contained the defect were superseded rather than scored.

Read what this entry said before the correction, because it is the reason this file needed one: *"It stands. It is inside all ten commitment strings and closing it changes every one of them. It is the first item of the January re-freeze."* That was true when it was written and false a day later, and it stayed on the page through the re-freeze that fixed it. The harvest figure in A1 was measured with this bias held fixed, so it remains an estimate under those conditions rather than a clean marginal effect.

### A0b. Six of the nine run the top of the envelope inside an arbitrary clamp

With the frozen pair, the load-sensitive friction `μ = 1.36 − 0.12·dfz` falls through the `MU_MIN = 0.30` floor and stops falling. Where that happens is **not a fixed speed**, which is the part two earlier versions of this entry got wrong: `dfz` runs through the downforce, so the crossover moves with air density, and `predict_v2.py` `blind_time()` sets density per session from the 2025 reference. At the module default `RHO = 1.225` it is 91.7 m/s; at 1.20 it is 92.6; at Mexico City's sealed 0.908 it is 105.6.

Computed against each sealed call's own `rho` and `V_CAP`, **six of the nine bind and three do not**:

| | rho | V_CAP | crossover | clamped |
|---|---|---|---|---|
| Monza | 1.1606 | 101.60 | 94.07 | yes |
| Baku | 1.2013 | 99.00 | 92.57 | yes |
| Abu Dhabi | 1.1881 | 96.60 | 93.05 | yes |
| Lusail | 1.2060 | 95.50 | 92.40 | yes |
| Zandvoort | 1.1932 | 95.20 | 92.86 | yes |
| São Paulo | 1.0695 | 98.10 | 97.74 | yes, barely |
| Austin | 1.1222 | 94.60 | 95.56 | no |
| Singapore | 1.1630 | 92.30 | 93.98 | no |
| Mexico City | 0.9083 | 102.50 | 105.55 | no |

Two corrections are owed here rather than one. The first version put the crossover at 93.3 m/s and said the clamp binds on "most of the sealed set". The second, written to fix that, said 91.7 m/s and claimed it binds on **all** of them "by construction", reasoning that `vcap_from_top` floors the cap at 92.0 and 92.0 > 91.7. Both were computed against module defaults instead of the code path. The first omitted the load model. The second omitted `RATIO = 1.0106` from `V_CAP` and held density fixed at 1.225. That put the second version wrong in the opposite direction from the first, and wrong most loudly at Mexico City, which it named as the extreme case and which turns out to have the largest margin of any circuit the other way: thin air at 2,240 m means less downforce, less load, and a tyre that never reaches the floor.

What that cost me twice was the difference between importing a module and following what the prediction path does with it. I recomputed both times and believed I had checked both times.

So on six of the nine, the top of the speed envelope is governed by a hard floor rather than by the calibrated tyre. Above the clamp μ stops falling while downforce keeps growing, which means grip starts **increasing** with speed again, and the model's braking capability improves the faster it goes for no physical reason. The linear load-sensitivity term is also being extrapolated to roughly ten times its reference load from a fit that never saw that regime.

Declared rather than fixed, same reason as the rest of section A.

### A1. Recovered energy is credited at the deploy efficiency

`scripts/cp/v2physics.py:207` credits brake harvest as `P_HARVEST * ETA_ERS * dt`, where `ETA_ERS = 0.92` is the *deployment* efficiency used at line 153. The recovery path should carry its own, lower figure; the earlier `scripts/ers_dp.py:29` uses `ETA_REGEN = 0.70` and describes exactly that. Charging the battery at 92% instead of 70% puts about a third more energy into the store than the lap earned.

**Cost, measured.** Re-running all ten sealed circuits on a copy of the module with harvest credited at 0.70, and reporting only the differences so no sealed preimage leaks: lap times come out **+0.561% slower on average, +0.737% at worst** (Las Vegas), never below +0.302% (Monza). So every sealed call is biased **fast by roughly half a percent**, which is 42% of σ and larger than the entire teammate noise floor.

The circuit ordering is a sanity check on the diagnosis rather than a coincidence: the effect is smallest at Monza, which brakes least, and largest at Las Vegas and Austin, which brake most. An energy-accounting error should scale with how much energy passes through the accounting, and it does.

**Fixed in v3.** `v2physics.py:39` defines `ETA_REGEN = 0.70` and line 231 uses `P_HARVEST * ETA_REGEN * dt_i`, so recovery and deployment no longer share one efficiency. It did get its own declared re-freeze rather than a quiet patch, which is what this entry asked for. It arrived in August rather than January.

### A2. No dry check on the 2025 reference session

`predict_v2.py `session_2025()`` takes `s.laps.pick_fastest()` from the 2025 qualifying session with no compound test and no rainfall test. The declared wet rule voids a call when the **2026** session is wet; nothing was written to cover a wet **2025 reference**.

It bit once. The 2025 Las Vegas qualifying ran in rain, pole set on intermediates at 1:47.934 with a 331 km/h top speed, against 1:32.312 and 347 km/h in the dry 2024 session. The sealed Las Vegas call is therefore built on a wet racing line and a top-speed anchor 16 km/h low.

The other nine check out. Baku's 2025 session recorded rainfall but its pole lap was dry and on softs, within 0.25 s of 2024 at an identical 339 km/h. All seven calibration circuits are dry-referenced, so σ itself is not contaminated.

**The sequence that followed is the problem.** This entry declared "Las Vegas is the most likely miss of the ten" and promised I would claim no credit for the diagnosis afterwards. Six commits later the v3 re-freeze introduced a wet-reference gate that **removes Las Vegas from the scored set entirely**. The circuit I had named in writing as my likeliest failure stopped being scoreable, by a rule I wrote afterwards.

That the 2025 Las Vegas session ran on intermediates was public the whole time. Nothing was discovered between those two commits that was not already available when I wrote the first one, so the rule's effect was fully determined before the rule existed. "We could not have known" is not available to me here.

The gate is still defensible on its merits. Building a dry-line prediction from a lap set on intermediates produces a number with nothing behind it, and refusing is the right behaviour at any venue. Its net effect was also one-directional: it deleted my self-nominated worst case and nothing else.

The symmetry is the sharper problem. `null-model-2026.md` argues that letting the baseline abstain at Las Vegas would be cheating, in these words: *"the moment it is allowed to abstain exactly where it would embarrass itself, it stops being a mechanical rule and becomes a rule plus a human who saw the answer coming."* It then holds the baseline to a call there. And then the model abstains. So the baseline is on the hook at the one venue the model was excused from.

**The paired comparison is therefore declared here as nine rounds, not ten.** Las Vegas is reported separately: the baseline's sealed call is scored, the model's abstention stands, and the pair is excluded from every summary statistic comparing the two. That is fixed now, before Zandvoort, rather than settled in December. It does not undo the ordering, and the ordering stays written here so a reader can weigh it.

### A2b. A second smoothing filter, never declared, moves the answer more than the one that is

Each sealed call publishes a stability figure `s1`, the spread of the lap time across Savitzky-Golay windows 7, 9 and 11. On the sealed set that lands around 0.4 to 0.5%, comfortably inside the 0.8% gate, and it is offered as evidence that the line method is not fragile.

It measures the wrong filter. After the SG pass, `calculate_curvature` applies a **second** smoothing step, a 7-point box filter whose half-width `k = 3` is hard-coded, never varied and never mentioned. Sweeping that one instead:

| k | support | lap time |
|---|---|---|
| 0 | 5 m | +4.99% |
| 2 | 25 m | +1.70% |
| 3 | 35 m | **frozen choice** |
| 4 | 45 m | −0.83% |
| 6 | 65 m | −2.55% |

A ±1 change in an undeclared constant moves the answer by more than σ, and the full range spans 7.5%. The declared stability figure understates the real filter sensitivity by roughly six times.

The combined support is worth seeing: SG(9) plus box(7) is fifteen samples at 5 m spacing, so **75 m of arc**. A 20 m-radius hairpin turns through about 215° in that distance. The curvature the model uses at a slow corner is an average over most of the corner.

**Fixed in v3.** `k_smooth` is an argument (`v2physics.py:123`) and `predict_v2.py` `blind_time()` sweeps `K_SMOOTH ± 1` alongside the SG window, so it is inside the published `s1`. The prediction in this entry was correct and is now a measured fact rather than a forecast: **nine of nine exceed the 0.8% gate**, from 0.86% to 2.57%, and every call is published with its own figure. That is the honest outcome and it is worse than the entry expected.

### A2c. Curvature is estimated on samples that are not evenly spaced

The v1 path and the ERS optimiser compute curvature by finite differences on raw FastF1 telemetry, then smooth with a fixed 7-point box filter measured in *samples*. The telemetry is time-sampled, so at Suzuka the spacing runs from **0.197 m to 30.84 m**, a factor of 156, and the filter's physical support therefore varies from 1.4 m to 216 m along one lap.

Walking a perfect 100 m circle through that estimator returns radii from 47 m to 268 m. The per-point grip envelope on raw telemetry is close to noise; it survives because the two envelope passes act as a minimum filter and the tyre fit absorbs the mean bias, which means the two are confounded.

The v2.3 line resamples to a uniform 5 m before differentiating, so the sealed calls do not carry this. It affects the v1 lineage and the published ERS figures.

### A3. The deployment-zone threshold is set where only combustion power saturates

**This entry replaces an earlier version that was wrong, and the correction matters more than the original claim.** The first version said the defect did not touch the v2.3 predictions "which use the dynamic-programming allocator". Both halves were false: v2.3 does not use the DP allocator, and the defect reaches every sealed call. It is corrected here rather than quietly edited, since a defect list that gets its own entries wrong is worth less than no list.

The threshold is `v_FL = P_ICE / F_DRIVE`, at `scripts/cp/v2physics.py:162` and again at `scripts/qss_laptime.py:172` and `scripts/cp/qss.py:66`. It marks where *combustion power alone* stops saturating the 12 kN drive-force cap, which is 400,000/12,000 = 33.3 m/s. But the quantity that matters is where *total* power stops saturating it, because `a_drive = min(F_DRIVE, (P_ICE + p_ers)/v) / M` is pinned at the force limit either way below that point. With 250 kW of electrical power at 0.92 efficiency the correct threshold is (400,000 + 230,000)/12,000 = **52.5 m/s**. The band between 33.3 and 52.5 m/s is marked as an acceleration zone when nothing electrical can reach the road there.

**Why it reaches the sealed calls.** The threshold does not merely waste charge. It defines `is_accel`, which defines the zone boundaries, which are then sorted by length at `v2physics.py:174`, and the two longest are promoted to key zones receiving 350 kW untapered instead of 250 kW tapered. Move the threshold and the zones change length, the ranking changes, and a different pair of zones gets the extra power.

**Cost, measured** on a copy of the module with the corrected threshold, reported as differences so no sealed preimage leaks:

| | |
|---|---|
| mean shift | +0.018% |
| largest shift | **0.733%** (Mexico City), then 0.681% (Baku), −0.638% (São Paulo) |

The mean sits near zero because the sign flips from circuit to circuit. That makes it **scatter** rather than a bias the calibration could absorb, and at 0.73% it is over half of σ on a single circuit. A defect that cancels on average while moving individual circuits is exactly the cancellation failure the summer re-freeze document identifies as the most dangerous kind.

It also touches a published comparison, though not in the way first written here. Correcting the gate and re-running makes the greedy **slower**, not faster, because excluding the low-speed band re-splits and re-ranks the length-sorted zones. So "the baseline is handicapped by this defect" does not follow from the defect.

The comparison is unfair for a different and larger reason. The DP harvests during the lap and spends 6.09 MJ; the greedy has no recovery path at all and is capped at the 4.00 MJ store. Give the greedy the same budget and it goes from 91.32 s to 90.59 s, so **0.733 s of the 2.570 s gap is tank size rather than allocation**. The DP's real advantage is 1.837 s, which is substantial and worth stating precisely instead of inflating: the argument that it needs all three state axes stands on its own.

**Fixed in v3.** `v2physics.py:186` now reads `v_FL = (P_ICE + P_ERS_SEC * ETA_ERS) / F_DRIVE`, which evaluates to 52.5 m/s against the defective 33.33. The old form survives only in the frozen v1 path (`qss_laptime.py:172`, `cp/qss.py:66`), where it stays, because Spa and Budapest were published and `predict_race.py` does not change.

---

### A4. The frozen set is larger than it looks, and was under-declared

Saying "the predictors are frozen" names four files and understates the real surface. What is actually frozen is the transitive import closure, because any module reachable from a predictor can move a published number.

Following the imports: `predict_race.py` pulls in `qss_laptime`, `cp/qss.py`, `cp/track.py`, `cp/raceline.py` and `cp/ers_dp.py`; `cp/qss.py` pulls in `cp/aero.py`; `cp/ers_dp.py` pulls in `cp/energy.py`. So the frozen set for the two v1 commitments is **eight modules**, not one, and includes files whose names suggest they are general utilities safe to tidy. `predict_v2.py` is cleaner, reaching only `cp/config.py` and `cp/v2physics.py`, which is the one thing the self-contained-module decision bought.

Anyone refactoring `cp/aero.py` or `cp/energy.py` on the reasonable assumption that they are shared helpers would silently break the reproduction of Spa and Budapest. The closure belongs in a check that fails on drift rather than in a sentence.

### A5. Reproducing a sealed call means reproducing an environment that was not specified

Until this audit, `requirements.txt` pinned nothing: five bare package names. The sealed path calls `savgol_filter`, `np.gradient`, `np.convolve` and `cKDTree`, and a minor-release change to an edge case in any of them moves the lap time and breaks a published hash.

The failure mode is the one the whole protocol exists to prevent. A reader in 2027 whose `sha256sum` disagrees would have no way to distinguish "scipy changed" from "the author edited the call", and the honest author would have no way to prove which it was. A commitment scheme whose verification depends on unspecified software has a gap exactly where its guarantee should be.

There was an asymmetry that made this worse: CI pins its GitHub Action to a full commit SHA and CMake pins Catch2 to a tag, while the code that actually produces the published numbers pinned nothing.

Now pinned to the versions the season locks were produced under, with the reasoning in the file. Two things still missing, both on the January list: a lockfile covering transitive dependencies, and a recorded BLAS backend, since `numpy.linalg.svd` in the line-fitting path can differ across backends.

### A6. The commitment sealed the prediction and not the rule that grades it (fixed)

The most serious finding of the audit, and the only one where the danger came from doing the right thing rather than the wrong one.

`score()` verified the commitment, read `POINT` out of it, and then decided hit or miss using `SIGMA` and `T95` as they stood in the module **today**. The sealed string carries `sigma=1.32%oof` and `hit=inside 1.32%`, and neither was ever read. So the thresholds that convert an error into a verdict lived in mutable code while everything around them was frozen.

Follow the consequence. The harvest correction in A1 is already announced as the first January item; it is correct, it will land, and it changes σ by construction. Re-running `--score` afterwards would have regraded the entire sealed season under the new number, turning borderline misses into hits and quite possibly disarming the strong-miss trigger, **with every published hash still verifying**. `sha256sum` would pass on all ten preimages, the manifest would pass, and re-running the predictor would still print the registered hash, because the prediction path is untouched. Nothing in the scoring output would have shown it, since the registered σ was never printed. The parc-fermé rule was being applied strictly to the half of the pipeline that hashes already protect, and not at all to the half where they protect nothing.

**Fixed, and safe to fix, because `score()` produces no hashes.** The thresholds now come out of the commitment. σ is parsed from the string, and T95 is recovered from the 95% band the same string carries, which pins it without needing a field the sealed set does not have. Verified against a sealed commitment: σ 1.3200% and T95 2.6166 recovered, matching the frozen constants. If the module and the commitment ever disagree, the scorer says so and grades by the registered values.

Two related defects in the same function, also fixed:

The deleted-lap filter was a permanent no-op. FastF1 only populates `Deleted` when race-control messages are loaded, and the session was loaded with `messages=False`, so the column existed full of nulls, `fillna(False)` turned every one into "not deleted", and the count printed zero forever. Loading with `messages=True` makes it real: at the 2026 Budapest session the column comes back as proper booleans with **six deleted laps** the filter would have let through.

One defect in that function is **not** fixed and is declared instead. `laps.pick_fastest()` searches Q1, Q2 and Q3 together rather than taking the classified pole, so on any session where an earlier segment was faster than Q3 the scored "real" would be a time that was never pole. The bias is one-directional: it makes `real` smaller, which flatters a model A1 already declares is biased fast. Correcting it means changing what "real" means after the calls were sealed, so it is written down here and left for the January re-freeze rather than changed now.

### A7. The wet rule is looser than the risk it names

`score()` voids a round if any rainfall sample appears anywhere in the session record. The pole lap can be bone dry on slicks at the end of a drying session and the call still voids.

The project's own data shows how often that misfires: of the ten sealed venues' 2025 sessions, two recorded rainfall and only one had a wet pole lap. So the trigger fires on roughly a fifth of sessions and would discard a scoreable dry pole on roughly a tenth.

The bias is one-sided, which is what makes it worth declaring. Rounds get removed when conditions were bad for a dry-line model and never when they were unusually good, so the surviving sample is filtered toward the model's favour, and the outcome it most reliably deletes is the strong miss that would trigger a re-freeze. That is a free option and it should not be a silent one.

The sealed string says `wet=VOID(inter-wet-compound-or-rainfall)`, which both readings satisfy, so the interpretation is being fixed here **before any of the nine scoreable sessions has run** rather than chosen afterwards: the rule stands as implemented, and every voided round will be published with its would-be error alongside the void, so the left tail stays visible even when it does not score. Tightening the trigger to the pole lap's own conditions is a v3 change.

None of these affects any published prediction. Pole-time calls come from the Python quasi-steady-state path; the C++ simulator is a closed-loop stability demonstrator. They do affect the closed-loop lap times the README reports, and B1 affects how those numbers should be interpreted.

### A8. The lap time depends on where the telemetry array happens to start

Found 2026-07-30, after the nine v4 calls were sealed. It is declared and left running; the reason is below the table.

A flying lap is a closed loop, so nothing physical distinguishes one point on it from another. The model's input is an array, though, and FastF1 decides where that array begins. Rotate the identical closed geometry, same points in the same order with a different starting index, and the predicted lap time changes.

Measured on the nine pinned inputs, rolling the arrays by 0, 37, 150 and 400 samples:

| Circuit | spread in `t_sim` | spread with ERS disabled |
|---|---|---|
| Austin | **1.52%** | 1.02% |
| Monza | 1.23% | 0.27% |
| Abu Dhabi | 0.96% | 0.98% |
| Baku | 0.93% | 0.24% |
| São Paulo | 0.79% | 0.12% |
| Lusail | 0.72% | 0.79% |
| Zandvoort | 0.71% | 0.13% |
| Mexico City | 0.43% | 0.11% |
| Singapore | 0.20% | 0.07% |

Austin alone exceeds σ = 1.414%. The median is around 0.8%, which is over half of σ, and the geometry it comes from is identical in every run.

**Two mechanisms contribute, and the split varies by circuit.** The first suggestion was that all of it comes from the state-of-charge ledger: `soc = E_STORE` at `v2physics.py:219` starts the lap with a full battery at index 0 and never wraps, so the energy pass is not periodic even though v3 made the velocity pass periodic. That holds at Baku, Monza and São Paulo, where disabling ERS removes most of the movement. It does not generalise. At Abu Dhabi and Lusail the no-ERS column is as large as the full one, so most of the effect there is geometric: `_resample` starts its 5 m grid at index 0, the Savitzky-Golay window sits differently, and the closing segment between the last point and the first is never integrated at all. The figure I was given for ERS-disabled laps was 0.037%. Re-measured across all nine, it runs from 0.07% to 1.02%.

**Declared rather than fixed.** The v3 reason for leaving defects running was that the hashes were public, and that reason was false; it is retracted at the top of this file. This one is different. The nine v4 calls are sealed, and the OpenTimestamps anchor is the declared end of the re-freeze sequence. Fixing A8 changes all nine, which means a fifth re-freeze, which is the thing the [v4 declaration](predictions/refreeze-2026-v4.md) committed to stopping. That declaration was written before this defect was known and says a defect found after the seal gets disclosed with its measured cost and left running. A8 is the first case that rule has to cover.

It is the first item of the January program, ahead of the filter sensitivity, because it is the same class as the closure defect and the fix is understood: iterate the state of charge to a periodic fixpoint the way the velocity pass already does, close the polyline, and anchor the resample grid to something on the track rather than to an array index.

---

## B. C++ core: live, unfixed, and unbuildable here

None of these sit in the sealed path. The calls come from the Python quasi-steady-state model, and this core is a separate program. It ships in this repository, though, and its defects are real. None has been corrected, for the reason given at the top of this file: no compiler toolchain is available on the machine this audit was done from, and editing physics that cannot be compiled or run against the 23-case suite is worse than a known bug. Every entry below was verified by reading source and doing arithmetic, never by execution, and that limit is part of each finding.

This heading is new. Sections A and C had one and B did not, so B1 through B7 rendered as subsections of "A. Found by audit, fixed in the v3 re-freeze": seven live C++ defects filed, visually, under a heading that says they were fixed. The preamble has referred to "Section B" as an existing thing since the file was written.

### B1. Three different ground-effect models, one of them non-monotonic

The plant, the planner and the predictor do not agree about how downforce grows with speed.

- `src/control/pure_pursuit.cpp:88` and `scripts/cp/v2physics.py:67` use the same sigmoid, `ge(v) = 1 + (ge_max − 1)·v²/(v² + v_ref²)`, monotone from 1 to 2 with `v_ref = 40 m/s`.
- `src/physics/batch_vehicle.cpp:227` computes a multiplier from *ride height* instead, and ride height is clamped at 10 mm (`batch_vehicle.cpp:288`) against an optimum of 40 mm.

Follow the second one upward in speed. Downforce pushes ride height down, the multiplier rises to its peak as height approaches the 40 mm optimum, and then the car goes *through* the optimum into the stall branch, where `max(0.5, 3·stall_ratio)` floors at `3 × 10/40 = 0.75` and stays there. So the plant makes more downforce at 40 m/s than at 50, and every corner above roughly 48 m/s runs at 75% of nominal.

At 90 m/s the planner believes the multiplier is 1.835 and the plant delivers 0.75, a factor of 2.4 apart in downforce and therefore in grip.

**This contradicts a claim in the documentation, now corrected.** `ARCHITECTURE.md` stated that the planner uses "the same speed-based ground-effect multiplier" as the physics it drives. It does not. That sentence has been fixed rather than left standing.

It also weakens a diagnosis. The README attributes the closed-loop lap's roughly 20% deficit to the controller rather than the physics. With the plant and the planner disagreeing by 2.4× on high-speed grip, that attribution is not supported, and it should not be repeated until the aero models are unified and the run repeated.

### B2. The friction ellipse caps at the nominal peak, not the load-sensitive one

`src/physics/batch_vehicle.cpp:175-176` builds the ellipse from `p_dx1` and `p_dy1` directly, while `compute_tire_forces` on the line above produces forces from the load-sensitive `μ_y = p_dy1 + p_dy2·dfz`. At a per-wheel load of 8 kN with `Fz0 = 2 kN`, `dfz = 3` and the tyre's real peak is `1.8 − 0.17×3 = 1.29`, against an ellipse that permits 1.80.

So the combined-slip limit is about 40% too permissive exactly where the car spends its fast corners, and the ellipse mostly stops binding under load. Since the ellipse is what the README uses to explain why trail braking costs something, the mechanism is documented more strictly than it is enforced.

### B3. Linear scans on a sorted array, in the hot loop

`src/track/centerline_track.cpp` resolves arc position by walking every point: `max_curvature_in_range` at line 285 iterates all 1,161 points and filters, and `get_curvature_at`, `get_sector_at`, `is_x_zone_at` and `sample_at_s` do the same. The array is sorted by `s_arc` and the schema says so, which is the precondition for `std::lower_bound` and a drop from O(n) to O(log n).

`max_curvature_in_range` is the expensive one, because `pure_pursuit.cpp:118` calls it once per lookahead segment per control step rather than once per step.

An earlier version of `ARCHITECTURE.md` described this function as `O(span / spacing)`. It is O(n), the correction is in place, and the fix is a one-line change waiting on a build that can run the test suite.

One of the five is dead code. `get_curvature_at` is declared, defined and never called, and it is also the only accessor that does not wrap `s_arc`, so it would return zero for every query past the first lap if anyone ever did call it. Deleting it is cheaper than fixing it.

### B4. Aero force and aero moment describe different downforces

`batch_vehicle.cpp:282` computes force and torque together with the ride-height multiplier hardcoded to 1.0. Line 291 then scales the force by `df_mult` and leaves the torque untouched, and line 293 hands both into the load-transfer calculation as a matched pair. They are not a matched pair: one has been scaled by up to 3× and the other has not.

The mechanism that let them drift apart is visible in the signature. `compute_aero_forces` takes a `ride_height_mult` parameter that its only production call site passes as 1.0 and then re-applies by hand afterwards, so the parameter is dead and the scaling lives outside the function that should own it.

### B5. No error handling anywhere, against fifteen unguarded parse sites

There is not a single `try` or `catch` in `apps/`, `src/`, `include/` or `tests/`. Meanwhile `std::stof` is called at fifteen places across `centerline_track.cpp`, `lap_common.hpp` and `telemetry_runner.cpp`, and it throws on a non-numeric cell or an empty string. A single malformed row in a CSV terminates the process with no message saying which file, which line, or which column.

`lap_common.hpp:29-31` is the sharpest version: it calls `getline` six times without checking the return value, then parses the result. On a short row the string is empty and the parse throws.

`load_from_csv` is the worst offender and it is worth naming as the weakest function in the C++ code. It uses three incompatible error strategies at once: it returns `false` for a missing file, silently skips short rows without counting them, and lets a malformed cell throw. It reads the header row and discards it, binding every column by position, so a schema change upstream misparses in silence rather than failing. And it clamps an out-of-range sector value into range instead of rejecting it.

### B6. Determinism is claimed, staked on, and untested

The hash protocol rests on the model being bit-reproducible, and nothing tests that. Both determinism tests run the same binary twice inside one process, which demonstrates the code has no hidden mutable state and says nothing about reproducing across compilers, standard libraries, or machines. There is no pinned golden lap time anywhere in the suite.

The rest of the suite has the same shape. Three of the tests that touch real track geometry begin by checking whether their data file loaded and calling `SUCCEED()` if it did not, so they report success when they did not run. The release test preset, the only one CI runs, omits the setting that makes an empty test run an error. A build registering zero tests is a green CI run.

Adding one golden-value regression test is the change that would make the determinism claim mean something, and it is also the precondition for safely landing any of the other C++ fixes on this list.

### B7. The v1 tyre was fitted under one aero model and deployed under another

This is the Python twin of B1 and it affects the two scored v1 calls.

`cp/aero.py` uses two lift coefficients, 3.0 on straights and 5.0 in corners, selected by a `straight` flag. `qss_laptime.py` and `cp/v2physics.py` use 5.0 everywhere and have no straight-line variant at all. Which model runs depends purely on which module was imported.

`calibrate_tire.py` fits the tyre pair through `qss_laptime.compute_metrics`, the always-5.0 model. `predict_race.py` then makes its predictions through `cp/qss.py`, which routes to `cp/aero.py`, the 3.0-on-straights model. So the two numbers that define the v1 tyre were chosen to fit a car with more straight-line downforce than the car that used them.

v2.3 is internally consistent here, since `v2physics.py` is self-contained and uses one coefficient throughout. The defect is confined to the v1 lineage, which is frozen, so it stays as it is and Spa and Budapest keep reproducing.

---

## C. Claims corrected in this pass

Documentation that said more than the code did. Each was verified false and each is now fixed; they are listed so the correction itself is on the record.

| Where | Claimed | Actually |
|---|---|---|
| `predictions/VERIFY.md` | git history dates each hash ahead of its session | commit dates are author-settable, and neither v1 hash predates its session in this repository. The v1 calls are anchored by the dated posts that carried them before their sessions, now linked from VERIFY.md; the ordering claim moved to evidence that exists rather than being dropped |
| `ARCHITECTURE.md` | planner and plant share one `ge(v)` | three models, one non-monotonic (B1) |
| `ARCHITECTURE.md` | `max_curvature_in_range` is O(span/spacing) | O(n) over all points (B3) |
| `ARCHITECTURE.md` | the CMake flags enforce no contraction | `-ffp-contract=off` is set only on the non-MSVC branch |
| `README.md` | the tyre error surface is something you can plot and look at | `calibrate_tire.py` keeps only the best point; no surface is saved |
| `README.md` | Pacejka MF 5.2 | a Magic Formula sine model with load-sensitive peaks, `E = 0` by default and camber unused |
| `README.md`, commitments | the published top speed is a model call | `predict_v2.py` `predict()` sets `top_pred = top25 × RATIO`, last year's number scaled |
| `README.md` | "Holdout, 18 unseen drivers" | 18 laps of the same session whose lap the tyre was fitted to, and the predictions correlate with the real times at r = −0.01 (see below) |
| `predict_v2.py`, season tables | 2026 round numbers | seven were off by one; corrected, and all ten hashes re-verified to reproduce |

### The Suzuka holdout, stated properly

This one deserves more than a table row, because the number is worse than the label suggested and it was found by computing something nobody had computed.

Across the 18 clean non-fit drivers in `data/sim_results/suzuka_field_qss.csv`, the model averages −2.235% with a standard deviation of 1.846 and is faster than the real lap for 16 of 18. Those are the README's figures and they reproduce exactly. Now the statistic that was missing:

- spread of the model's 18 predicted times: 1.159 s
- spread of the 18 real times: 1.231 s
- **correlation between predicted and real: r = −0.010**
- R² after allowing a free additive offset: **−0.905**

The predictions have realistic spread and none of it points anywhere. Predicting that every driver sets the field-mean lap time would be more accurate than this model is, once the common offset is removed. The reason is not mysterious and the README half-states it already: one car model is racing a grid of twenty different cars, so nearly all of the 1.8% is car-to-car spread the model has no way to see.

The implication was never drawn, and it is the important part. **That 1.8% is not model uncertainty, and the exercise cannot validate cross-circuit accuracy.** A related tell sits in the same file: `top_sim_mps` is exactly 92.0 for all 22 drivers, the `V_CAP` clamp, against real values from 85.8 to 93.3. The straight-line part of every lap in that table is a clamp rather than a computation.

The v4 out-of-fold σ of 1.414% is a different quantity, computed on seven circuits each predicted by a fold that never saw it, and it is the only number that should ever be quoted as accuracy.

---

## What happens to this list

Section C is done. Sections A and B are the January program, in that order, and the two entries that move a published number, A1 and B1, get a declared re-freeze rather than a patch.

If you find something that belongs here, open an issue. A defect list only I contribute to is one that stops at the edge of what its author thought to check.
