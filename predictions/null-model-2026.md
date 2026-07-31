# The null model, and what the physics has to beat

A vehicle model that predicts pole times has an obligation nobody imposed on it from outside: it has to be better than the stupid thing. The stupid thing here is one line long.

```
2026 pole = 2025 pole at the same circuit x k
```

This document runs that baseline under exactly the protocol the physics is held to, publishes the result, and then seals the baseline's own calls for the remaining ten rounds so the season scores both. The headline first, because burying it would be worse than the finding:

**On the seven evidence circuits, out of fold, the one-line baseline scores σ 0.99% against the physics model's σ 1.414%.** The stupid thing is currently ahead, and the gap widened at the v3 re-freeze rather than closing.

## The rule, stated precisely enough to attack

`k` is the mean 2026/2025 pole ratio over the seven evidence circuits of the summer re-freeze. Its value as sealed is **1.032297**, so 2026 poles run about 3.23% slower than 2025 poles at the same venue. The unrounded mean is 1.0322977; the sealed strings carry the six-decimal value and every number below is generated from them rather than recomputed, because a table in prose that disagrees with the artifact it describes is how a rounding note turns into a credibility problem on some later call where the digit matters. Poles are the fastest non-deleted qualifying lap, which is the same rule `predict_v2.py --score` applies, because a baseline scored under looser rules than the model would be a rigged comparison.

Scoring is symmetric seven-fold leave-one-out, the same protocol and the same folds as the calibration: for each circuit, `k` is recomputed from the other six and the held-out circuit is predicted with a constant it never contributed to. Nothing else about the baseline is fitted, which is the point of it.

| Circuit | 2025 pole | 2026 pole | ratio | k from the other six | predicted | error |
|---|---|---|---|---|---|---|
| Miami | 1:26.204 | 1:27.798 | 1.01849 | 1.03460 | 1:29.187 | +1.58% |
| Barcelona | 1:11.546 | 1:14.679 | 1.04379 | 1.03038 | 1:13.720 | −1.28% |
| Montreal | 1:10.899 | 1:12.578 | 1.02368 | 1.03373 | 1:13.291 | +0.98% |
| Spielberg | 1:03.971 | 1:06.113 | 1.03348 | 1.03210 | 1:06.024 | −0.13% |
| Silverstone | 1:24.892 | 1:28.111 | 1.03792 | 1.03136 | 1:27.554 | −0.63% |
| Spa | 1:40.562 | 1:44.361 | 1.03778 | 1.03138 | 1:43.718 | −0.62% |
| Budapest | 1:14.890 | 1:17.207 | 1.03094 | 1.03252 | 1:17.326 | +0.15% |

Out of fold: **μ +0.01%, σ 0.99%, RMS 0.92%, worst call 1.58%.** The physics model on the same seven, same folds: μ +0.102%, σ 1.414%.

That second figure used to read 1.32%. Five defects were corrected at the [v3 re-freeze](refreeze-2026-v3.md) and σ went up, because one of them had been cancelling against another. The corrected number is the honest one and it is further from the baseline, which is worth saying in the document whose job is to be unflattering.

## What this establishes, and what it does not

It is worth being careful here, because the temptation to over-read a result that hurts is the same temptation as over-reading one that flatters, and the second is the one this project has already been caught at once.

The comparison does **not** establish that the baseline is more accurate. With seven points, σ carries a 95% interval of **[0.64, 2.18]** for the baseline and **[0.911, 3.113]** for the model, and those intervals overlap across almost their whole length. Seven circuits cannot separate 0.99 from 1.414. Anyone reading this as "the trivial rule wins" is making the small-sample error the re-freeze document spends two pages warning about.

What it does establish is sharper and harder to argue with: **the physics has not yet earned its complexity.** A model with a tyre fit, a friction ellipse, an energy ledger, an active-aero mode switch and a two-pass QSS envelope is currently not measurably better than multiplying last year's time by a constant. That is a real finding about this project, it is the first thing a competent reader will ask for, and it should not have taken an outside reading to produce it.

## Why the baseline is so strong, which is itself the finding

The reason is visible in the ratio column and it is a fact about 2026 rather than a fact about statistics. Across the seven circuits the 2026/2025 ratio runs from 1.0185 to 1.0438, a spread of 2.53 percentage points, with a standard deviation of **0.88%**.

That near-constancy is the whole game. The 2026 regulations changed mass, tyre width, aerodynamics and power unit all at once, and the net effect on a flying lap turned out to be close to a single multiplicative constant across circuits as different as Spielberg and Spa. When a regulation change scales every circuit by nearly the same factor, a constant captures nearly all of the signal, and there is very little left over for physics to explain. The baseline's σ of 0.99% is essentially that 0.88% ratio spread, plus the noise in reading two pole laps.

So the honest framing of the model's task is not "beat 3.23%". It is "explain the 0.88% that the constant leaves on the table". That is a much harder problem than the headline suggests, and stating it this way makes the target legible for the first time.

## The information the model throws away

There is an asymmetry in the comparison that runs against the model, and it is the model's own doing.

The baseline's single input is the **2025 pole time**. The physics model loads that number, hashes it into the input pin at `predict_v2.py `session_2025()``, and then never uses it again: the prediction is built from the 2025 lap's GPS geometry and its top speed, and the lap time is computed from grip and curvature. The most directly predictive quantity available about a 2026 pole time is sitting in the same data structure, sealed into the commitment, and discarded.

That is defensible as a design choice, because a model that consumes last year's lap time is measuring last year's car and not this year's regulations, and it can never say why a circuit changed. It is not defensible as an unexamined one. The two predictors use different information, and until now only one of them had been scored.

## Where the baseline breaks, and what it exposed in the model

The baseline assumes its 2025 reference is a comparable dry lap, and nothing in the rule checks that. Testing the assumption against the ten remaining rounds turned up something worse than a flaw in the baseline.

```
2025 Las Vegas Q:  1:47.934  INTERMEDIATE  rainfall  top 331 km/h
2024 Las Vegas Q:  1:32.312  SOFT          dry       top 347 km/h
```

**The 2025 Las Vegas qualifying session was wet.** Pole was set on intermediates, fifteen seconds off a dry lap. The baseline applied to that reference predicts **1:51.420** for a session that will run somewhere near 1:35. That misses by roughly sixteen seconds with a known cause, and it sits in the published set on purpose.

The temptation was to let the baseline skip that round, and it is worth naming why that would have been cheating. The null model's whole value is that it applies no judgment: the moment it is allowed to abstain exactly where it would embarrass itself, it stops being a mechanical rule and becomes a rule plus a human who saw the answer coming. That is the cherry-picking this registry exists to make impossible, and it does not become acceptable when the beneficiary is the opponent. So the baseline calls all ten, Las Vegas included, and takes the consequence.

Because that single round would otherwise decide a ten-round comparison on its own, both scorings are declared now, before anything runs, so neither can be chosen afterwards:

- **Primary: all ten rounds, mechanical.** This is the honest score of the rule as stated.
- **Secondary: the nine dry-referenced rounds.** This is the score a reader gets if they grant the baseline the same input hygiene the model also lacks, and it is the fairer test of the underlying idea.

Both get published. If they disagree, that disagreement is the finding.

The rest of the ten check out. Baku's 2025 session recorded rainfall but its pole lap was dry and on softs, 1:41.117 against 1:41.365 in 2024 with an identical 339 km/h top speed, so it stays in. All seven evidence circuits are dry-referenced, which matters more than the rest of this section: the calibration itself is not contaminated.

Now the part that is not about the baseline. **The physics model called Las Vegas from that same wet session, and nothing in the pipeline noticed.** `session_2025()` takes the fastest lap of the 2025 qualifying session with no compound check and no rainfall check. The declared wet rule voids a call when the *2026* session is wet; it was never written to cover a wet *2025 reference*. So the sealed Las Vegas call is built on a wet racing line and a top speed 16 km/h below the dry figure, which sets `V_CAP` low.

The call stands. It is sealed, its hash is published, and editing it after noticing a problem is exactly the move this registry exists to make impossible. What can be done is to say so now, before the session, which is strictly stronger than explaining it afterwards: **Las Vegas is the call in this set most likely to miss, the input is named, and the direction is predictable.** If it misses, that is a miss with a diagnosis written in July, and no credit is claimed for the diagnosis after the fact.

The gap goes on the January list as an input gate: a reference session that ran wet should refuse to produce a call, the same way Madrid refuses for want of any session at all.

One thing the episode does show, and it is the only comfort available. Given the identical wet input, the baseline lands at 1:51.420 while the physics produces a call in the range a dry Las Vegas lap actually occupies. The model's number stays sealed until the session like every other, so take the claim as bounded rather than exact: it is inside its own published bands, and those bands do not come within fifteen seconds of 1:51. Working from the shape of the line and the physics of the car, rather than from last year's time, is what keeps a wet reference from turning into a sixteen-second error. That property is invisible in a σ computed over seven dry circuits, which is worth remembering before reading too much into 0.99 against 1.414.

## The baseline's own ten calls

A rival that only scores well in hindsight on the fitting set is not a rival. So the baseline makes its own falsifiable calls on the same rounds, published here in full.

These are published in the open rather than held back, and the difference from the model's calls is deliberate. There is nothing to hide: the rule is public, `k = 1.032298` is public, and the 2025 poles are public, so anyone can recompute every number below and see that no other value was substituted later. Concealing a number that a reader could derive in one line would be ceremony rather than protocol. The hashes still do one job, which is binding the set so no circuit can be dropped once results start arriving, and that is what the manifest is for.

| Round | Circuit | 2025 pole | baseline call | 68% band |
|---|---|---|---|---|
| R12 | Zandvoort | 1:08.662 | 1:10.880 | [1:10.066, 1:11.693] |
| R13 | Monza | 1:18.792 | 1:21.337 | [1:20.403, 1:22.270] |
| R15 | Baku | 1:41.117 | 1:44.383 | [1:43.185, 1:45.580] |
| R17 | Singapore | 1:29.158 | 1:32.038 | [1:30.981, 1:33.094] |
| R18 | Austin | 1:32.510 | 1:35.498 | [1:34.402, 1:36.594] |
| R19 | Mexico City | 1:15.586 | 1:18.027 | [1:17.132, 1:18.922] |
| R20 | São Paulo | 1:09.511 | 1:11.756 | [1:10.933, 1:12.579] |
| R21 | Las Vegas | 1:47.934 (wet) | 1:51.420 | [1:50.142, 1:52.698] |
| R22 | Lusail | 1:19.387 | 1:21.951 | [1:21.011, 1:22.891] |
| R23 | Abu Dhabi | 1:22.207 | 1:24.862 | [1:23.888, 1:25.836] |

Bands are σ_naive 0.99% scaled by the same Student-t factors the model uses, T68 = 1.159 at ν = 6. A hit is inside ±0.99%, which is a tighter target than the model's ±1.414%, and deliberately so: a challenger that grades itself on wider bands than the champion has not challenged anything.

**Baseline manifest:** `e0c91cdba99acc94046cadcf307e54258112dfc3f57347198204868cdb7679f2`

The baseline still calls all ten rounds, including Las Vegas. The physics model no longer does: the v3 dry-reference gate abstains there, so **the paired comparison runs over nine rounds** and Las Vegas is scored for the baseline alone, as a standing record of what the rule does with a wet reference when nothing stops it.

Everything needed to check that is in the repository, since a hash nobody can verify is decoration. The ten commitment strings ship in full as [null-model-commitments.txt](null-model-commitments.txt), one per line, and the `<Circuit> <hash>` index is [null-model-manifest.txt](null-model-manifest.txt).

```
sha256sum predictions/null-model-manifest.txt
```

must return the value above. Each individual call is the SHA-256 of its own line in the commitments file taken without the trailing newline, the same byte discipline the model's preimages use.

Las Vegas appears in the set as a full commitment rather than as a blank, so the abstention is on the record as a decision that was made rather than as a circuit that quietly went missing. It is scored as an abstention.

## How this gets settled

Not by argument. Both predictors have calls made in advance and published, and they overlap on nine rounds; the tenth, Las Vegas, is the baseline's alone because the model now refuses a wet reference. At the end of the season there are nine paired errors and the question becomes a test rather than a debate.

The rules are fixed now, before any of it runs, because fixing them afterwards is how this kind of comparison usually gets rigged:

1. The paired test runs on the nine rounds both call. Las Vegas is published for the baseline unpaired, so the rule's worst case stays visible rather than disappearing with the pairing.
2. A wet 2026 session voids that round for both, on the same declared trigger, since neither predictor models rain.
3. The statistic is the paired difference in absolute percentage error, and the test is a sign test over the paired rounds. Chosen now, and named now, because it assumes nothing about the error distribution and because a test picked after seeing the errors is not a test.
4. Nine paired rounds on top of seven evidence circuits still will not settle this. Stated in advance so that a narrow win in either direction does not get read as a verdict by either of us.

If the baseline wins, the honest conclusion is that this vehicle model does not currently justify itself as a forecasting instrument, and that conclusion gets published in the same place as everything else. The physics would still be the only one of the two that can say *why* a lap time is what it is, decompose a miss into corner and straight, survive a wet reference, or call a circuit at all when the regulations change again. None of that shows up in σ, and none of it is worth anything if the number is not competitive.

The January program has a target that is specific rather than aspirational: **beat 0.99%.** It is further away than it was this morning, which is what happens when you stop measuring a coincidence.
