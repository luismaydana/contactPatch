# The rest of the season, sealed in one act

Nine calls, one per remaining callable round, committed on 2026-07-30 under the frozen v4 configuration. The hashes are below. The preimages stay unpublished until each race is scored, at which point that race's string is released and anyone can check it against the hash printed here.

## The commitments

| Round | Circuit | SHA-256 prefix (full values in [season-2026-manifest.txt](season-2026-manifest.txt)) |
|---|---|---|
| R12 | Zandvoort | `c22410aed9278092` |
| R13 | Monza | `a53f99f01aef5dd0` |
| R15 | Baku | `93a5e00a835cd1fc` |
| R17 | Singapore | `9d7a2441acd55d92` |
| R18 | Austin | `23b6aac17970cc7d` |
| R19 | Mexico City | `65696ac7e40821d5` |
| R20 | São Paulo | `e74b1d0a0741e914` |
| R22 | Lusail | `f2819e828de74376` |
| R23 | Abu Dhabi | `9af74c916be4a4b8` |

R21 Las Vegas is absent by rule rather than by choice: its 2025 reference session ran on intermediates, and a wet reference now refuses to produce a call. That consequence was written into the [v3 declaration](refreeze-2026-v3.md) before the refit ran, so losing a circuit could not become negotiable once the numbers existed. R14 Madrid and R16 Kuala Lumpur are absent for the older reason. They are new circuits with no 2025 qualifying session, the v2.2 line method has nothing to build from, and inventing one for the sake of a full card is the kind of improvisation this registry exists to prevent.

**Manifest hash:** `caaf244f05cd25bad4ef3eb3afb3da8c8033948a78961b0be16beb1afa56912c`

That is the SHA-256 of [season-2026-manifest.txt](season-2026-manifest.txt): nine `<Circuit> <hash>` lines, sorted by circuit, UTF-8, newline-separated, with no trailing newline. It exists so the set is as sealed as its members.

Hash the file rather than retyping the table above, because the two are not byte-identical and the file is the artifact. The table renders circuits the way a reader says them, so it has "Mexico City", "São Paulo" and "Abu Dhabi"; the manifest uses the single-token keys the code uses, `Mexico`, `SaoPaulo`, `AbuDhabi`. Reconstructing the manifest from the table gives a different digest, and that is a defect in how this was originally described rather than a subtlety worth preserving. A future revision should carry the identifier and the display name as separate fields so no reader has to know the difference.

## Why one act instead of weekly locks

The original plan was a lock each race week, and it would have been sound. Committing the whole season at once is strictly stronger, and the reason is a hole that weekly locking leaves open.

Suppose the calls arrive one at a time. Every hash is honest, every preimage checks out, and the record is still open to one objection that nothing in the scheme can answer: nobody can tell how many races were *considered* and skipped. A model that quietly declines the circuits it feels shaky about and calls only the ones it likes would produce exactly the same evidence as one that calls everything, and it would score better. The commit-reveal protocol proves each individual call was not edited after the fact; it says nothing about which calls were never made.

Sealing them all at once closes that hole, and the manifest hash is what closes it. Removing a circuit from the set changes the manifest, so there is no longer any way to drop a race quietly. What was a promise about the author's future behaviour becomes a property of a published number.

The price is that nine calls made in July on the same 2025 data cannot benefit from anything the season teaches. A weekly schedule could have folded each result into the next prediction, and that option is given up on purpose, because a model that adjusts after seeing results has stopped predicting.

## Verify

Once a race has been scored, its preimage ships as `<circuit>-2026/commitment_v4.txt` and the check is one command:

```
sha256sum predictions/zandvoort-2026/commitment_v4.txt
```

The output must equal the hash in the table, byte for byte. To confirm the nine hashes above are the ones the manifest binds:

```
sha256sum predictions/season-2026-manifest.txt
```

Before any of that, the model itself can be re-run without waiting for a session. Every call in the table regenerates from the frozen configuration and public telemetry:

```
python scripts/predict_v2.py Monza
```

which prints the same SHA-256 that appears in this table. All nine were checked this way before publication and all nine reproduce; none is a hash of something that cannot be recomputed. The check is also part of `tests/test_reproducibility.py --net`, though CI runs the offline tier only, so that check still depends on someone remembering.

## One correction after sealing, and why it changes nothing

Sealing a set of calls raises an obvious question about anything touched afterwards, so this is on the record with the evidence rather than as an assurance.

A pre-publication audit found that seven of the ten circuits carried the wrong 2026 round number in `predict_v2.py`. The 2026 calendar adds two venues without a 2025 session, Madrid and Kuala Lumpur, and only Madrid had been accounted for. Everything from Singapore onward was therefore off by one: `--score Singapore` would have loaded round 16, which is the Kuala Lumpur grand prix, and graded the registered call against the wrong session entirely. Zandvoort, Monza and Baku sit ahead of the gap and were never affected.

That fix was argued to be safe on structural grounds, and the argument was exactly backwards. It ran: a round number is used in one place, `score()`, and it never appears in the commitment string, so no hash can depend on it and correcting the table is free. Read adversarially, the absence is the defect. The round decides **which grand prix a sealed call is graded against**, so leaving it out of the hash meant the seal bound the prediction and not the referent. After a bad Saturday the table could be edited, a different session fetched, and every published hash would still verify.

From v4 the round is inside the commitment string as `round=<n>`, and `score()` reads it back from the seal and refuses to grade a call whose sealed round disagrees with the table. Both halves were needed, and only the first landed at first: v4 added the field while still resolving the session from the table, which left the sealed value decorative for several hours until a review pointed out that adding a field protects nothing until the code reads it back. The nine v4 calls carry the round they will be scored against, and all nine were regenerated and re-verified against the manifest after the change.

The failure would have surfaced on 10 October as a nonsensical result, and a correction made then would have been indistinguishable from tampering.

## The stability gate fires on all nine

Every call carries `s1`, the spread of its lap time across the smoothing settings. Under v2.3 that figure swept the Savitzky-Golay window only, landed near 0.4%, and sat comfortably inside the 0.8% gate. It was measuring the wrong filter. A second box filter sat downstream with its half-width hard-coded, unvaried and unmentioned, and on the nine shared circuits it moves the answer a median 4.3 times more than the one being swept, up to 6.5 times at the worst venue. An earlier version of this sentence quoted the worst circuit as though it were typical.

v3 sweeps both. The result:

| Circuit | s1 | | Circuit | s1 |
|---|---|---|---|---|
| São Paulo | 0.86% | | Austin | 1.96% |
| Mexico City | 1.20% | | Monza | 2.01% |
| Singapore | 1.46% | | Lusail | 2.57% |
| Baku | 1.69% | | | |
| Zandvoort | 1.73% | | Abu Dhabi | 1.91% |

**Nine out of nine exceed the 0.8% gate.** The declaration said what would happen in that case, before the numbers existed: the gate fires, the spread is declared in every affected call, and the gate is not widened to accommodate the result. So every commitment string carries its own `s1` and every call goes out with the gate tripped.

Read what that means plainly, because it is the least comfortable number in this document. At Lusail the answer moves 2.57% depending on a smoothing choice, against a σ of 1.414%. **The sensitivity to how the line is filtered is larger than the model's own stated uncertainty on most of this set.** A reader is entitled to weigh that against every band published here, and the only reason it can be weighed at all is that the figure is no longer measuring the wrong thing.

It also reframes what the January program is for. The obvious target was to beat the naive baseline's 0.99%. The prior question is now whether a method whose answer moves 2.57% under a defensible change of filter can be said to have a 1.414% uncertainty at all, and that is a question about the line method rather than about the physics.

## What the season is expected to look like

The verdict scale lives in each commitment string. A **hit** is a call landing inside ±σ, now ±1.414%. A **miss** is outside σ but inside the 95% predictive band, ±3.699%, so a call that failed while staying inside the uncertainty it published. A **strong miss** is outside that band, and it triggers the next declared re-freeze.

Those thresholds fix what the season should produce, and the arithmetic is worth doing in advance rather than after the fact. If the model is calibrated, the error on a fresh circuit divided by σ behaves like a t distribution with ν = 6 scaled by √(1+1/7) = 1.069, so the chance of any one call landing inside ±σ is P(|t₆| ≤ 1/1.069) = P(|t₆| ≤ 0.9354) = **61.4%**. Over nine calls that gives **5.5 hits and 0.45 strong misses**, and the binomial spread puts the honest range at **3 to 8 hits out of 9**, with 3 to 7 covering 89.7% of outcomes. The probability of at least one strong miss is 1 − 0.95⁹ = **37.0%**, so a season without one is more likely than not and would not by itself be vindication.

Note that none of those figures depends on σ. The scale factor cancels: a hit is defined as landing inside ±σ, so widening σ widens the target and the band together and the hit probability is a property of the t distribution alone. That is worth stating because an earlier version of this paragraph got it wrong in a way that looked like it depended on σ. It used 1/T68 = 0.863 as the bound where the scale factor 1/1.069 belongs, applying √(1+1/7) twice, and reported 57.9%, 5.2 hits, 0.6 strong misses and a 45% chance of at least one. The last of those was the expected *count* 0.45 relabelled as a probability. The v2.3 version of this same paragraph had all four right, so this was a regression introduced while rewriting for nine calls, and every one of the four errors made the model look worse than its own declared calibration implies. Correcting them raises the expected hits and lowers the expected strong misses, which is the uncomfortable direction to be corrected in: the arithmetic that was wrong was the arithmetic being harder on itself, and nobody checks that kind.

σ has moved twice since v2.3 and the two moves have different causes. It rose from 1.351% to 1.460% at the [v3 re-freeze](refreeze-2026-v3.md), when five defects were corrected and one of them turned out to have been cancelling against another. It then fell to 1.414% at the [v4 re-freeze](refreeze-2026-v4.md), which removed a leak in the calibration itself rather than changing the model. Substituting 1.414 for 1.461 mechanically across this file made this sentence say the five v3 fixes produced 1.414%, which they did not; that is corrected here. Wider bands mean each individual call is easier to hit and the whole set is less informative, which is the trade a bigger σ always makes. It is the honest trade, and pretending to the smaller number would have been the alternative.

This forecast carries no separate seal, and that is not an oversight. It is arithmetic on σ, which is already sealed inside all nine strings. There was no freedom to choose a flattering version of it: a larger σ would have made every individual call easier to hit while widening the published bands until they said nothing, and a smaller one would have narrowed the bands into a season of strong misses. The trade was made when σ was frozen, and this is what the frozen value implies.

The consequence is a scoring rule that runs in both directions, which is the part most likely to be misread. **Nine hits out of nine would be a failure of calibration, not a triumph.** Its probability under a correct model is 0.614⁹ = 1.25%, so a clean sweep is evidence that the bands were declared too wide to be wrong. A model claiming an uncertainty it never exceeds has not made a prediction; it has made an unfalsifiable statement wearing the costume of one. Somewhere between three and seven is what a working instrument looks like, and the misses are load-bearing.

So the season has three publishable outcomes and none of them needs dressing up. Land inside 3–7 and the calibration held. Land at 8 or 9 and σ was overstated, which is a finding about the bands. Land at 0–2 and σ was understated, which is a finding about the physics and sends the January program somewhere specific. The record cannot come out uninformative, which is the only property worth engineering for.
