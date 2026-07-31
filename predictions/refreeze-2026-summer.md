# The 2026 summer re-freeze (v2.3)

Two calls, two misses, and the Budapest debrief pre-declared this document: a
recalibration at the summer break, done in the open, with Spa and Budapest as
data points. Here is what changed, what was found, and every number that came
out of it, including the ones that went against us.

The whole process ran under seven declarations, each written and hashed BEFORE
the runs it governs: `c0c1cc53…` (scope, data, acceptance gates), `03f833fc…`
(one amendment, zero new fitted parameters), `db5cce96…` (an attempt to remove
the external track-data dependency, which failed its own gate and got
diagnosed), `77d67ccf…` (the revised line method that came out of that
diagnosis), `34b486e0…` (the banked-corner check, which rejected its own
solver), `c6da0502…` (the seven-circuit final fit and its symmetric
leave-one-out), and `8429a398…` (the energy ledger). Sealing them first is not
ceremony. Mid-analysis, when a gate turns out to be inconvenient, the person
who wrote it will want to move it; the seal is there so that wanting is as far
as it goes. No gate was moved after seeing a result.

## What the diagnosis found

1. **v1's σ = 1.11% was an artifact.** The generated minimum-curvature line is
   uniformly optimistic and the old grip envelope was optimistic too; on the
   calibration circuits the two errors partially cancelled. Cancellation is
   the most dangerous failure a calibration can have, worse than being
   plainly wrong, because two opposing biases that happen to average out on
   the circuits you fitted have no obligation to keep averaging out on the
   circuits you have not seen; the pair decouples the moment the balance of
   corner types changes, which is precisely what a new venue does. Real
   driven lines plus a physical envelope expose the true circuit-to-circuit
   scatter, which is about 3%. That scatter was present under v1 too; the two
   cancelling biases were hiding it.
2. **The frozen car was physically impossible.** At Budapest it pulled 5.97 g
   lateral at 233 km/h, with 238 m of the lap above 5 g. A 768 kg car on 2026
   downforce does not do that.
3. **The rules changed mid-season and the model had not.** From Miami the FIA
   limited MGU-K deployment to 350 kW in key acceleration zones and 250 kW
   elsewhere. The v1 tyre was identified at Suzuka, round 3, a pre-change car.
4. **Air density was treated as a constant.** The five calibration sessions
   actually ran between ρ = 1.072 (Spielberg, 677 m altitude, 33 °C air) and
   1.217 (Montreal). Every aero force scales linearly with ρ, and it cuts
   both ways at once: thin air steals downforce in the corners and drag on
   the straights, which is why Mexico City produces the strange sight of
   cars in their biggest wings setting the year's highest top speeds. A
   fixed-density model would have wrecked that call (2,240 m, roughly −20%)
   in both directions at the same time.

## What v2.1 is

| | v1 (frozen) | v2.1 (frozen at this re-freeze) |
|---|---|---|
| Tyre pair | 1.80 / −0.17 | 1.58 / −0.17, re-fit on 5 post-change circuits |
| Peak lateral G | 5.97 | 4.78, under a declared 5.0 gate |
| Power model | pre-Miami spec | post-Miami: 350 kW key zones, 250 kW rest |
| Racing line | generated min-curvature | real pole lap, projected on the centerline |
| Line for a future circuit | generated | that venue's 2025 pole lap |
| Air density | 1.225 fixed | measured per session; 2025 same-venue carry-over pre-session |
| Top-speed ratio | 1.0037, mixed-era | 1.0106 ± 0.0235, 7 post-change pairs |
| μ / σ | −0.39% / 1.11% in-sample | +0.72% / 3.19% **out-of-fold** |

Calibration is leave-one-out through the full production path, fit on four and
predict the fifth, no partial credit: each held-out circuit predicted from its
2025 line, carry-over density and anchored cap, with the tyre fit on the other
four. The five out-of-fold errors: Montreal +1.21, Spielberg +4.57,
Silverstone +1.88, Spa +0.13, Budapest −4.18 (%).

## What the gates said

- Line gate (rebuilt line within 2 m RMS of the GPS lap, length within 2%):
  10 of 10 lines pass.
- G gate (5.0 g): pass at 4.78. It earned its keep: one configuration fit the
  lap times better and was rejected at 8.76 g.
- Reproduction gate (each 2026 session within 1%): **2 of 5 pass** (Spa +0.01,
  Montreal +0.40; Silverstone +1.74, Spielberg +2.81, Budapest −3.36 fail).
  Published as failed, per the declaration.
- Honesty gate: σ came out larger than v1 claimed, so the larger number is the
  one on every future call.

## Dead ends, kept on the record

- Track temperature does not explain the residuals: correlation 0.011, and the
  hottest session (Spielberg, 53 °C track) errs in the wrong direction for that
  theory.
- A first attempt to measure the 2026 lateral envelope directly from telemetry
  headings produced a physically meaningless fit (negative lift coefficient)
  and was discarded; the idea survives, the extraction needs per-apex work.
- An FP3-to-pole gap feature showed no obvious correlation with the residuals
  on the circuits where both exist. Per-event grip from practice stays on the
  research list, unproven.

## The line was biased too (v2.2)

v2.1 was not the end of it. The next limit in line was n = 5: with five
evidence circuits, the 95% confidence interval on σ itself runs [1.9, 9.2],
a factor of almost five of uncertainty about our own uncertainty. Two
post-change venues, Miami and Barcelona, were sitting out of the fit for one
reason only: no survey centerline. So we tried to build a reference line from
the telemetry itself, the median of all twenty drivers' fastest laps, behind a
sealed equivalence gate (`db5cce96…`): swap the reference, keep everything else
fixed, and the predictions must agree within 0.5%.

They did not. All five circuits failed, by 0.5% to 4.6%, always in the same
direction. Chasing that down produced the most useful table of the summer:
five constructions of the same pole lap, and the survey-centerline rebuild,
the one under every v2.1 number, is the outlier. The geometry deserves a
paragraph, because the whole summer turned on it. A driver spends the width of the
road buying radius, and the exchange rate is worth doing out loud rather than
waving at. Corner speed goes with the square root of radius, and the formula
is one balance, not a reference to look up: the corner demands centripetal
force `m·v²·κ`, the tyre supplies at most `μN`, and a car at the limit is the
case where the two are equal. Solve for v and `v = √(μN/mκ)` falls out,
so a driven arc that opens the radius by a fifth carries √1.2 ≈ 9.5% more speed
through the corner, and one that opens it by half carries 22% more. Those
are not rounding errors on a lap made mostly of corners. A
survey centerline, by definition, runs down the middle, which is nowhere a
driver puts a car; its curvature is the road's curvature, tighter than the
driven arc's, and a lap rebuilt on top of it inherits corners sharper than
the ones the car actually took. Feed those sharper corners to a fit and the
optimizer has exactly one lever left to make the lap times come out right:
more grip. So the tyre absorbed the difference, silently, on every circuit
at once, and the fit had been quietly compensating for the whole of v2.1.
The other four constructions, including simply filtering the pole lap's own
GPS, agree with each other to about ±0.5%.

So the line method changed, under its own sealed declaration (`77d67ccf…`)
with the adoption rule fixed in advance: smaller out-of-fold σ on the same
five folds wins, ties go to the incumbent. The v2.2 line is the venue's 2025
pole lap itself, resampled at 5 m and Savitzky-Golay filtered. No survey data,
no reference, no width table. Any circuit with one qualifying session on
record is now callable, which is the capability the factory attempt was after
in the first place.

| | v2.1 | v2.2 (frozen for the run-in) |
|---|---|---|
| Line | 2025 pole projected on survey centerline | 2025 pole GPS, filtered, direct |
| External track data | required (blocked Miami, Barcelona) | none |
| Tyre pair | 1.58 / −0.17 | 1.42 / −0.13, re-fit on the unbiased lines |
| Peak lateral G | 4.78 | 4.91, same 5.0 gate |
| μ / σ, same 5 folds | +0.72% / 3.19% | +0.03% / 2.02% |

Then the two venues the old method could not touch, called blind with the
five-circuit fit, lines from 2025, scored against the real 2026 poles they
never saw: Miami −0.29%, Barcelona −0.24%. That validation event is on the
record and stays there.

One last sealed step closed the campaign (`c6da0502…`): with seven evidence
circuits in hand, the final fit uses all seven, and σ comes from a symmetric
seven-fold leave-one-out, every fold refit from scratch. Leave-one-out rather
than a held-out split because seven circuits cannot spare one: this way every
circuit plays the unseen test exactly once, and no error in the average was
ever computed on a lap its fold had trained on. The fit landed on
exactly the same parameters the five-circuit fit chose, 1.42 / −0.13, which
is what you want to see from numbers about to run eleven rounds untouched.
The seven out-of-fold errors: Montreal −0.68, Spielberg +1.93, Silverstone
−0.04, Spa +1.99, Budapest −2.02, Miami −0.29, Barcelona −0.24 (%). Final:
μ +0.09%, σ 1.43%, CI on σ [0.9, 3.2], against a measured teammate noise
floor of 0.37%.

One number for scale, from the timing data: teammates in the same car split by
a median 0.37% across 147 qualifying pairs. Teammates are the cleanest control
the sport offers. Whatever separates two drivers in the same machinery is form
on the day, how much the track came to them, and what traffic they found on the
lap. All three are precisely the part of qualifying no car model can see. Their spread is the irreducible noise under every prediction, which
makes 0.37% the floor any car model can hope for. And from the same timing
data, the other end of the scale: the median margin between pole and second
is 0.15%. A model at σ 1.32% calls the pole time, honestly banded; calling
which name goes on it is an order of magnitude away, and this project does
not pretend otherwise. The final configuration stands at 1.32% against that
floor, with the gap now made of transient dynamics, axle balance and surface
state rather than line reconstruction or missing energy.

Those two numbers compose into a ceiling, and it is better to do the arithmetic
than to leave it as an impression. Treat the teammate spread as noise the model
cannot see and take the model's own error as independent of it; then what even
a perfect car model would still measure is √(σ_model² + 0.37²). Running that
backwards from 1.32% leaves √(1.32² − 0.37²) = 1.27% that belongs to the model
rather than to the sport. So of the current scatter, the overwhelming majority
is still ours to win, and the noise floor is nowhere near binding yet. The
independence assumption is doing work there and is probably generous, since a
driver having a poor day and a model mispredicting that day's grip are not
obviously uncorrelated; read 1.27% as a lower bound on what is left to take,
not as a target.

## Zandvoort's banking, measured and kept out

Zandvoort's banked corners, the Hugenholtz bowl and the banked final sweep
that slings the car onto the main straight, got one last look before the
call, under their own sealed gates (`34b486e0…`). Banking helps a car twice:
part of the corner's centripetal demand gets carried by the track surface
itself instead of the rubber, and the same tilt presses the car harder into
the road, so the tyre is asked for less while being given more. A planar
model sees neither effect, which is why the corner deserved its own solver
and its own gates. With v2.2 lines anchored at the timing line, the
banked-solver windows could finally be placed correctly, and the 2025 lap's
own speed trace was there to check against. The check went against the solver.
The banked-corner deficit does not stand out from the ordinary era gap between
a 2025 trace and a 2026 car, the lever overshoots what the real car measurably
carried, and it pushes tyre G to 6.1 through the 5.0 physical gate. Its whole
effect on the unbiased line is about 0.3 s; the old 2 s figure turns out to
have been an artifact of the biased line and its misplaced windows. So it stays
out, and the number that mattered comes with it: the
un-modeled banking is worth roughly 0.4% of lap time, inside the 68% band.
Zandvoort gets called planar, limitation named, size measured.

## The energy the car actually has (v2.3)

One omission survived everything above, and the question that finally exposed
it was almost embarrassing: where does this model lift and coast? Nowhere. It
deployed from a fixed 4 MJ tank and recovered nothing during the lap. The 2026
formula's defining mechanic is the opposite. The MGU-K harvests at up to
350 kW in every braking zone, energy management is the sport's new central
axis, and a qualifying lap carries enough braking time to recover several
megajoules. The residuals were pointing at it too: the two power circuits read
slow (Spielberg +1.93, Spa +1.99) while the grip circuit read fast (Budapest
−2.02).

So, under one more sealed declaration (`8429a398…`), the flat tank became a
state-of-charge ledger walked in track order: the 4 MJ store drains under
deployment and refills under braking, all constants from the public spec,
zero fitted parameters. Walking in track order is the entire point. Energy
recovered braking for a chicane exists for the corners after that chicane,
never before it. A budget would let megajoules from anywhere pay for
anything; a path insists on order, and a lap is a path. The ledger enforces that
causality meter by meter: the charge at any point is the charge at the
previous point, plus what this braking zone just gave back, minus what this
straight just spent, never above what the battery physically holds. The numbers
the ledger runs under are the regulated ones: 350 kW of recovery under braking,
the 4 MJ store it refills, and a 7 MJ per-lap harvest limit that stops a circuit
with many braking zones from inventing energy. Under those rules deployment per
lap went from 4 MJ to 7-9 MJ, which is the world the technical directive's own
superclipping figures describe. Deployment exceeding the store is not a
contradiction: the store is a tank size, the deployment figure is throughput,
and the whole point of harvesting mid-lap is that the tank gets filled more than
once. Treating those two as the same number is exactly what the old fixed-tank
model did wrong. The
tyre re-fit landed at 1.34 / −0.12: for the third time in this document,
removing a bias moved the grip DOWN, because the tyre had been quietly
covering for missing power.

Seven-fold leave-one-out, re-run from scratch: μ +0.07%, **σ 1.32%**, CI
[0.85, 2.90]. Adopted by the pre-declared rule (beat 1.43 with every gate
passing). The spread also changed shape: Spielberg fell from +1.93 to +0.85
and Budapest from −2.02 to −1.58, while Spa moved against us, +1.99 to +2.48,
and is now the model's named outlier, first on the January list. Lift-and-coast
itself is declared not separately modeled: at quasi-steady-state level its
lap-time content IS the ledger.

One caveat for anyone recomputing these statistics by hand, because the
arithmetic is the first thing a careful reader will try. Every fold was refit
from scratch under the ledger, so this is a new set of seven errors, not the
previous set with three entries edited. The three quoted above are the movers
worth naming; the other four are not restated, and μ and σ are computed over
all seven. Substituting the three new values into the four old ones does not
reproduce 1.32% and is not meant to: the earlier list belongs to the
superseded fit. The stage that governs 2026 is the one immediately above, and
the seven errors behind it live with the sealed run `c6da0502…` rather than in
this paragraph.

## What a v2.3 call looks like

Bands are Student-t predictive intervals for n = 7, not naive ±σ, and the
distinction is exactly the kind that gets skipped when a σ needs to look
good. With seven points, σ = 1.32 is itself an estimate, so the bands have
to pay for two uncertainties at once: where the next error will land, and
how well we even know the scatter it will land within. The t distribution
with ν = 6 charges for the second, its tails heavier than a normal's
precisely because the sample was small, and the extra factor of √(1+1/7)
charges for predicting a new point rather than describing the old ones. The
two factors multiply out in the open: `t(0.84, ν=6) = 1.084` and
`√(1+1/7) = 1.069`, so `T68 = 1.084 × 1.069 = 1.159`; likewise
`t(0.975, 6) = 2.447` gives `T95 = 2.447 × 1.069 = 2.616`. Set ν = ∞ and
drop the predictive factor and those collapse to the familiar 1.00 and 1.96,
which is exactly the check that the multipliers are the normal ones plus two
named corrections and nothing else. The result: 68% is about ±1.5% and 95%
about ±3.5% of lap time, wider than ±σ and ±2σ, and honestly so. The CI on σ
itself comes from the χ² pivot with n−1 = 6 degrees of freedom,
`σ·√(6/χ²)` at the two quantiles (14.45 and 1.24); recomputing from the
rounded 1.32 lands the upper end at 2.91 where the frozen doc says 2.90,
which is the rounding of σ, not a different interval. A hit is a call inside ±1.32%; outside the 95%
band is a strong miss and triggers the next declared re-freeze.
Everything a call depends on rides inside its committed string: the tyre pair,
the offsets, the line settings, the session density, and the pin over the raw
input lap. There is nothing to take on faith that is not also under the hash.

## Hardened for a season that does not pause

Eleven rounds in nineteen weeks, so the protocol got the same treatment as the
physics before the freeze:

- Every commitment now carries an input pin, a hash over the raw 2025 lap the
  line was built from, and that lap ships with the preimage at scoring. If the
  upstream telemetry API revises its data, the call still reproduces.
- Wet is an objective rule fixed in advance: pole lap on intermediates or wets,
  or any rainfall in the session record, voids the call automatically.
- Sprint weekends (Zandvoort, Singapore): Friday sessions are not inputs, and
  the lock lands before GP qualifying starts.
- The discretization (5 m resample, SG(9,3) filter) is declared part of the
  model: absolute lap time shifts by about 5% across alternative settings, the
  calibration absorbs the common-mode part at the frozen setting, and the
  per-call stability gate only checks per-venue anomalies there. Two knobs
  measured insensitive, also on the record: the cap factor (0.1% across its
  plausible range) and the top-speed ratio's standard error (0.05%).
- All ten callable venues went through the full production path before the
  freeze: 10 of 10 pass every gate, with the density rule spanning Mexico City
  at ρ = 0.908 to Lusail at 1.206.
- Madrid stays a no-call for now, with its door ajar on a measurement: on the
  four conventional weekends of the evidence set, the FP3-to-pole ratio
  scattered just 0.27%, under the 0.8% threshold declared for even considering
  a practice-based line. If a Madrid protocol happens, it gets its own seal
  before the weekend.

The operational checklist for the rest of the season is
[SEASON-RUNBOOK.md](SEASON-RUNBOOK.md).

The frozen v1 path is untouched: `predict_race.py` still reproduces the Spa and
Budapest commitments bit for bit. New calls run through `scripts/predict_v2.py`.
