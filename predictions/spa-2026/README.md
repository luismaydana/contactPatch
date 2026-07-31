# Spa-Francorchamps 2026: qualifying pole call

- **Committed:** 2026-07-13, five days before the session (quali Sat 2026-07-18).
- **SHA-256:** `03ea1c08d2132e3386a2fb50bb3d5bbbdd91fc51fe6ef22bb5a6c79f61b13519`
- **Preimage:** [commitment.txt](commitment.txt), the exact hashed bytes, released after scoring. Verify per [../VERIFY.md](../VERIFY.md).

## The call

Dry pole **1:41.999**, 1σ band [1:40.864, 1:43.134], 2σ band [1:39.729, 1:44.269]. Secondary: top speed ~340 km/h ± 2 %. Conditional on a dry session (wet → void). Config frozen: greedy ERS, μ = −0.39 %, σ = 1.11 % from the four-circuit offset calibration.

## The result: MISS

Real dry pole: **1:44.361**. Error **−2.26 %** (2.04 σ), which puts it outside the pre-declared 2σ band by 0.092 s. Same arithmetic as every scored call, so it can be re-run rather than believed: (101.999 − 104.361)/104.361 = −2.362/104.361 = −2.263 %, and 2.263/1.11 = 2.04 σ. The committed 2σ band topped out at 1:44.269, and 104.361 − 104.269 = 0.092 s over. Scored exactly as the rules written into the commitment require: a strong miss, published, with a mandatory error decomposition. The secondary top-speed call did land, at 336.0 km/h, inside the ± 2 % band.

The decomposition puts most of the gap in the sectors where the car sits at high lateral load for seconds at a time, Pouhon and the fast sweeps around it, and the reason those corners in particular expose a line assumption is worth walking through. In a slow hairpin, every sane line has nearly the same shape; the corner is short, the radius is dictated by the track, and even a bad line only costs tenths of a second of low-speed running. A corner like Pouhon is the opposite case: a long double-left where the car holds serious lateral load for several seconds, where drivers give up the first apex to open the second, and where the line a human actually commits to differs from the geometric ideal by meters, sustained over the whole arc. Corner speed follows radius, so a small radius error there compounds, integrated across seconds of the lap's fastest loaded running. That is precisely where a generated minimum-curvature line diverges most from a driven one, and the test confirms the mechanism: fed the line the real pole lap actually drove, the same frozen physics reproduces that lap to −0.36%. The physics was never the problem in those sweeps; the geometry it was given was. The full analysis is in the project's debrief.

**Lock-hygiene disclosure.** The Spa call predates the single-run lock discipline. Its committed string was assembled with roughly 1 ms of internal drift between the point estimate and the bands, because two runs got mixed together while building it, so re-running the frozen model today lands 1 ms away and does **not** regenerate this exact string. Verification goes through the released preimage file instead, which hashes to the registered value bit-for-bit. The drift is three orders of magnitude below the 2.36 s miss, so no verdict changes. Every call since Budapest is locked from a single verified run and reproduces exactly.
