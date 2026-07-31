# The v3 re-freeze: five corrections, and a σ that got worse

Five defects were found in the physics by audit, verified against source, measured, and corrected. The out-of-fold scatter went from **1.351% to 1.461%**. The corrected model is adopted anyway, and this document is mostly about why that is the right call and what the number is telling us.

## Why this happened at all, and why it is not a broken seal

Ten calls for the rest of 2026 were sealed on 2026-07-28. An earlier version of `KNOWN-ISSUES.md` said their hashes were public and used that to justify leaving five measured defects running inside them.

They were never public. Checked on 2026-07-29: no remote branch contained the commit that created them, and the public remote had no knowledge of `season-2026-locks.md`. Parc fermé was being applied to something that had never entered parc fermé, and a commitment nobody has seen is not a commitment. The whole force of commit-reveal is the public timestamp; there was none.

So the ten seals are **superseded before publication**, not broken after it. Spa and Budapest are a different matter entirely and are untouched: both were posted publicly before their sessions, `predict_race.py` stays byte-frozen, and the v1 path was never in scope here.

## The declaration came first, and that is the load-bearing part

Correcting physics after watching two calls miss is precisely the situation where an author's judgement should not be trusted unsupervised. Five knobs are about to move in a model whose owner already knows which direction he would like the answer to go.

So the scope, the five fixes, the gates, and the expected outcome were written down and hashed before the first line changed:

```
declaration       f347fd09e41555962969135cd4846507de2c61c5a4cf46f94f663b232c62d724
v2physics.py      f88983d96f4a74eb09b8733336c708cda50c4ea60d629f9a5e8d45bff194f007
predict_v2.py     223c23559a295fbb2ae920122e2b32c2327ac4afe568d64ff0b46fbb8a5732f1
```

The two file digests are there so the order is checkable rather than asserted: they are the state the declaration governed, and the pre-fix module can be recovered from git and re-hashed to that value by anyone.

Four of the five corrections have no free parameter. A lap that closes, energy that is conserved, a dry reference, a threshold at the physically correct speed: there is one right answer and nothing to choose. The fifth has one, so `ETA_REGEN = 0.70` was fixed **in the declaration**, taken from a value already written in `scripts/ers_dp.py` long before this decision, with no sweep run over it. A free parameter tuned after seeing a result is the thing the declaration exists to prevent.

The declaration also committed, in advance, to publishing whatever came out: *"if σ gets worse, that is the result, and the v3 configuration is still adopted, because these are corrections to defects rather than a search for a smaller number."* That sentence is why this document exists in this form.

## The five corrections

1. **The lap now closes.** A flying lap is a loop, and the forward pass was seeding itself from the braking envelope without requiring the end of the lap to reach that speed. The car was handed 16 to 27 m/s at the timing line, on every circuit, always in the same direction. The seed now iterates to the periodic fixpoint.
2. **Recovered energy is credited at the recovery efficiency**, 0.70, not the deployment figure of 0.92. One constant had been serving two physically different jobs, which is how the harvest side spent two configurations charging the battery at the wrong rate.
3. **The deployment threshold uses total power.** Below the speed where the drive-force cap stops binding, electrical power reaches the road as nothing. The boundary was computed from combustion alone, putting it at 33.3 m/s instead of 52.5, which mis-ranked which zones got full power.
4. **A wet 2025 reference refuses to produce a call.** The declared wet rule covered the 2026 session and never covered the reference. Las Vegas 2025 ran on intermediates, so **Las Vegas is now an abstention and the season is nine calls, not ten.** That consequence was accepted in the declaration, before the refit, so that losing a circuit could not become negotiable afterwards.
5. **The curvature filter's half-width is swept.** The published stability figure varied the Savitzky-Golay window while a second box filter stayed pinned, and the pinned one was worth a median 4.3 times more, up to 6.5 at the worst venue. Both are swept now.

## The control, which had to come before any claim about σ

The old σ of 1.32% was produced by a private pipeline. The new one comes from `scripts/refit_loo.py`, which lives in this repository. Comparing them directly would be worthless if those two programs differ in anything beyond the five corrections, because then the difference would measure the scripts rather than the physics.

So the pre-fix module was recovered from git, its digest checked against the one sealed in the declaration, and the **new** script was run against the **old** physics:

| | tyre pair | μ | σ |
|---|---|---|---|
| Published v2.3 | 1.34 / −0.12 | +0.07% | 1.32% |
| Control: new script, old physics | **1.34 / −0.12** | +0.085% | **1.351%** |
| v3: new script, corrected physics | 1.36 / −0.12 | +0.124% | **1.461%** |

The tyre pair reproduces exactly and the two statistics land within 0.02 and 0.03 percentage points, which is the resolution the grid and the ratio bookkeeping can be expected to agree to. The pipelines are the same program. The comparison is therefore about physics, and σ genuinely got worse.

A side effect worth recording: this retires a finding from the audit. σ used to be the least verifiable number in a project built on verifiability, quotable but not regenerable from the public tree. It is regenerable now, by one command, and the control is the evidence that the command is the right one.

## Why removing a defect made the scatter worse

This is the interesting result and it deserves the space.

The closure defect was not a constant offset. It handed back between 16 and 27 m/s depending on the circuit, so the naive expectation is that removing it should have *reduced* circuit-to-circuit spread. It did the opposite. The per-circuit errors, out of fold, before and after:

| Circuit | with the defect | corrected | change | closure gap it had |
|---|---|---|---|---|
| Miami | −0.44% | −0.58% | −0.14 | 23.1 m/s |
| Barcelona | +0.35% | +1.15% | **+0.80** | 16.2 m/s |
| Montreal | −0.89% | −1.10% | −0.21 | 18.0 m/s |
| Spielberg | +1.05% | +1.75% | **+0.70** | 19.6 m/s |
| Silverstone | −0.25% | −0.42% | −0.17 | 23.1 m/s |
| Spa | +2.44% | +1.88% | **−0.56** | 27.4 m/s |
| Budapest | −1.66% | −1.81% | −0.15 | 18.7 m/s |

Correlation between the size of the closure gap and the change in error: **r = −0.686**. The bigger the defect was at a circuit, the more removing it helped that circuit. Spa had the largest gap at 27.4 m/s and its error improved most; Barcelona had the smallest at 16.2 and got worse.

That is the signature of **cancellation**. The free speed at the timing line was partly compensating for a different error running the other way, and the two happened to offset most at the circuits where the gap was largest. Remove one and the other is exposed with nothing standing in front of it.

The re-freeze that produced v2.2 identified exactly this failure mode and named it the most dangerous a calibration can have, because two opposing biases that average out on the circuits you fitted have no obligation to keep averaging out on the ones you have not seen. That was written about a generated racing line and an optimistic grip envelope. It turns out to describe this model's own energy and closure terms just as well, and the project has now demonstrated it on itself rather than only warning about it.

So **1.461% is a more honest number than 1.351% was**, and that is the whole argument for adopting it. The smaller figure was smaller partly because two mistakes were holding hands. A model that is right for better reasons and scores slightly worse is the correct trade, and keeping known-wrong physics because it flatters is the alternative this project exists to refuse.

With n = 7 the two values are not separable anyway: σ = 1.461% carries a 95% interval of roughly [0.94, 3.22], and 1.351% sits inside it. The claim here is not that the model got worse. It is that the number is now measuring the model instead of measuring a coincidence.

## The expectation was recorded, and it was wrong

The declaration predicted σ would land between 1.0% and 1.3%, with the reasoning that removing a circuit-varying defect should tighten the spread. It came out at 1.461%, above the range.

That is published because writing an expectation down and then quietly not mentioning it is worse than not writing one. The prediction failed, the reason it failed is the cancellation above, and the failure is more informative than a hit would have been: it is what forced the correlation to be computed at all.

The declaration's escape clause, that σ above 1.5% would mean something was wrong with the corrections rather than with the model, did not trigger. 1.461% is below it, the gates all pass, and closure is exact.

## What is now frozen

| | v3 |
|---|---|
| tyre, in-sample on seven circuits | p_dy1 **1.36**, p_dy2 **−0.12** |
| μ, out of fold | **+0.124%** |
| σ, out of fold | **1.461%** |
| top-speed ratio, seven pairs | 1.0106 |
| callable rounds | **9** (Las Vegas abstains) |
| lap closure, all seven folds | **0.000 m/s** |
| peak lateral, worst circuit | 4.84 g, gate 5.0 |

Gates G1 through G4 all pass. Every fold refit from scratch; no error in that average was measured on a lap its own fold had trained on.

## The comparison that has not changed

The naive baseline, last year's pole time multiplied by one constant, is untouched by any of this. It still scores σ 0.99% out of fold on the same seven circuits, and the corrected model at 1.461% is now further behind it than the uncorrected one was.

That is not a reason to un-correct the physics, and it is a reason to be blunt about where this project stands: **the physics still has not earned its complexity.** The season-long paired test in [null-model-2026.md](null-model-2026.md) runs unchanged and will settle it on nine rounds instead of ten. The January target moves from "beat 0.99%" to the same target from further away.
