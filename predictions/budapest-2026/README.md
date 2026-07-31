# Budapest 2026: qualifying pole call

- **Committed:** 2026-07-24, ahead of the session (quali Sat 2026-07-25).
- **SHA-256:** `b22f847955638ae96d47716e332284eefa140db4cc95a4c45712908e39fe9cf4`
- **Preimage:** [commitment.txt](commitment.txt), released after scoring. Verify per [../VERIFY.md](../VERIFY.md). Re-running the frozen model (`python scripts/predict_race.py Budapest`, no network needed) reproduces the committed 1:13.613 and this exact SHA-256, so the single-run lock discipline adopted after Spa held.

## The call

Dry pole **1:13.613**, 1σ band [1:12.796, 1:14.430], 2σ band [1:11.979, 1:15.247]. Secondary: top speed ~319 km/h ± 2 %. Conditional on a dry session (wet → void). Config frozen: greedy ERS, μ = −0.39 %, σ = 1.11 %.

This call was pre-registered as an experiment. After Spa the open question was whether the model's 2026 bias grows with sustained high-speed cornering (Spa's regime) or runs through everything. Budapest is brake-turn-traction with no sustained fast corners, and the generated line there hugs the centerline (0.27 m mean offset), which structurally rules out the Spa line-failure mode. On that basis it was declared the model's strong regime. The scenario table, including this outcome, was written down before the session.

## The result: MISS

Real dry pole: **1:17.207** (Norris, McLaren; session dry, track 42–50 °C). Error **−4.65 %** (4.19 σ), which is outside the 2σ band by 1.960 s. The arithmetic, so it can be re-run rather than believed: (73.613 − 77.207)/77.207 = −3.594/77.207 = −4.655 %, and −4.655/1.11 = 4.19 σ. The committed 2σ band topped out at 1:15.247, and 77.207 − 75.247 = 1.960 s. If your own recomputation of the percentage lands at −4.66, that is the millisecond rounding in the committed string, not a different result. The secondary top-speed call missed too: 331.0 km/h real against the ~319 ± 2 % called, so −3.6 %. Both scored exactly as the pre-declared rules require.

## The decomposition

- Sectors against the 2025 pole (Norris both years): S1, which carries the main straight, is **−0.08 s**, essentially flat. S2 is **+1.23 s** and S3 **+1.17 s**. The whole 2025→2026 penalty lives where the Hungaroring never straightens, the middle-sector esses and the winding run home; the straights were modeled correctly (session cap effect −0.2 s). And the +2.32 s shift itself (+3.09%) is ordinary for 2026: across the nine other circuits run in both seasons, 2026 poles are +1.57% to +4.56% slower than 2025, and Budapest sits mid-range. The track did nothing unusual. The model did.
- Time-in-speed-band (model vs real telemetry, alignment-free): instead of overlaying two speed traces, which requires syncing them in distance and puts every conclusion at the mercy of that sync, count the seconds each lap spends in each speed range. No alignment, no sync error, and the histograms disagree loudly: the real car spends **+8.2 s more in the 120–160 km/h range** than the model, while the model spends **+5.7 s more at 200–250 km/h**. The model carries 200–250 km/h through corners the real 2026 car takes at 120–160.
- The V_CAP rule was nearly exact (session cap effect −0.2 s) and the geometry rules the line out, so unlike Spa this miss is the **cornering envelope itself**. The frozen grip-and-downforce product lets the model turn in carrying speed the real 2026 car has to shed well before the corner, and it does so in medium-speed corners on every circuit type.

**Verdict on the pre-registered hypothesis: rejected.** The bias is global rather than severity-dependent, where global means it shows up across circuit types without being uniform in size. The two misses are one mechanism at two magnitudes. At Spa the generated line hid the envelope term, and the real-line run put it at +0.37 s. At Budapest, with the line ruled out, the envelope showed in full at +3.59 s. Its size tracks how much of a lap is spent in medium-speed corners.

None of this surfaced in the four calibration circuits for the ordinary reason that in-sample fits hide things: μ = −0.39% absorbed the envelope optimism those four circuits happened to sample, and with n = 4 that average did not transfer. The σ had been declared uncertain for exactly this case. Following the scenario declared before the session, the response is a documented re-freeze of the calibration at the summer break with Spa and Budapest added as data points, rather than a quiet mid-season retune. Two calls, two misses, each one decomposed to a named cause.
