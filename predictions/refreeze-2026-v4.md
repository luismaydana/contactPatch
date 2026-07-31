# v4 re-freeze: the calibration was measuring something production cannot do

Third re-freeze in eight days. σ improved, from 1.460% to 1.414%, which is the direction that looks like tuning from outside: a defect was removed and the number got better. What separates this from tuning is that the commitment to adopt whatever came out was sealed before the refit ran, and the preimage of that seal ships in this repository.

**Declaration:** [`declarations/v4-declaration.md`](declarations/v4-declaration.md) → `676ab520ea963f76def9a2a96b2261aec25b27cf1c10a9cc5af1752a2663865d`
**Amendment 1:** [`declarations/v4-amendment-1.md`](declarations/v4-amendment-1.md) → `15856d575492894d346387d01747cebd11297947a939781113879030f0bcd1ad`

Both were written and hashed before the corresponding edits, and both texts ship here, so `sha256sum predictions/declarations/*.md` reproduces the two values above. That is a change forced by review. v3's declaration went out as a bare digest with no text behind it, and a hash whose preimage nobody holds says nothing about what was sealed.

What the preimages cannot establish is *when* they were written. That rests on the same anchor as everything else: the OpenTimestamps receipt over the manifest, attested in Bitcoin blocks 960327 and 960330 on the day this repository went public ([TIMESTAMP.md](TIMESTAMP.md)). The amendment is a separate file rather than an edit to the first declaration, because editing a sealed declaration to add something convenient is the move sealing exists to prevent. So the record carries two documents.

## The defect

`scripts/refit_loo.py` computes the seven-fold leave-one-out error that produces σ. At the point where it made the blind prediction for the held-out circuit, it passed that circuit's **2026** session air density:

```python
m = blind(D[label]["d25"], p1, p2, r, D[label]["d26"]["rho"])
```

Production cannot do that. `predict_v2.py` `blind_time()` sets `V.RHO = s25["rho"]`, the 2025 carry-over, because when a call is sealed in July the 2026 session has not happened. Every aerodynamic force scales linearly in density.

So the published σ had never been an out-of-fold error. It was measured with an input the sealed calls do not have.

A second change landed in the same script. An earlier version of this paragraph called it a second defect and said the season was about to be "graded by one rule and calibrated by another". That was overstated, and the control below shows why. The script loaded with `messages=False` and took `pick_fastest()` with no deleted-lap filter, so on paper the calibration used a different definition of pole than `--score` does. In practice it did not. FastF1's `pick_fastest()` already restricts to laps flagged as a personal best, and a lap deleted for track limits loses that flag, so the filter was redundant by construction. Checked across all fourteen sessions, both loaders select the identical lap: same time, same driver, same telemetry.

## The result

| | v3 (leaking) | v4 (corrected) |
|---|---|---|
| p_dy1, p_dy2 | 1.36, −0.12 | **1.36, −0.12** |
| μ out-of-fold | +0.124% | **+0.102%** |
| σ out-of-fold | 1.460% | **1.414%** |
| ratio | 1.0106 | 1.0106 |
| 5 g gate | pass | pass |

Per circuit:

| | v3 | v4 |
|---|---|---|
| Miami | −0.579 | −0.663 |
| Barcelona | +1.148 | +1.085 |
| Montreal | −1.103 | −1.048 |
| Spielberg | +1.747 | +1.591 |
| Silverstone | −0.415 | −0.427 |
| Spa | +1.881 | +1.907 |
| Budapest | −1.806 | −1.732 |

**The tyre pair did not move, and that proves nothing.** An earlier version of this line offered 1.36 / −0.12 surviving as evidence that the fit is not balanced on the defect. It could not have moved. `fit()` and `run()` never read the leaked density, so no input to the tyre fit changed and the pair was arithmetically pinned. The same holds for `ratio` 1.0106. Both claims are withdrawn.

**The move is also not statistically distinguishable from zero.** On the paired fold errors, which correlate at 0.999:

| | |
|---|---|
| Pitman–Morgan paired-variance test | t(5) = 1.494, **p = 0.195** |
| Paired bootstrap of σ₃ − σ₄, 200k | mean +0.042, **95% CI [−0.018, +0.097]** |
| χ² interval for σ = 1.414 at ν = 6 | [0.911, 3.113] |

[refreeze-2026-v3.md](refreeze-2026-v3.md) supplied this caveat for a move 2.4× larger, and leaving it out here ran in the flattering direction. **The σ move is real in mechanism and indistinguishable from zero in magnitude.** 1.414 is adopted because the estimator was wrong. It is not measurably better than 1.460 and this document does not claim it is.

## Why removing an input improved the number

The natural objection is that taking information away should make prediction worse, so a number that improves when something is removed suggests someone went looking for the version that improved.

The physical reading is that the leaked value carried no information about the target. It carried an inconsistency. The line comes from the 2025 session, and pairing it with the 2026 session's density describes a car that never existed: last year's racing line in this year's air. Production pairs 2025 geometry with 2025 density, which at least describes one afternoon. The fold was handed a mismatch, and the mismatch behaved like noise.

That is an explanation and should be read as one. The evidence is narrower. The declaration was sealed before the refit ran, it stated in writing that σ was expected to get worse for the second consecutive re-freeze, and only one v4 refit exists anywhere in the tree. What none of that rules out is a hyperparameter changed instead of σ, because the declaration binds the output and not the procedure. `refit_loo.py` carries free choices no hash covers: the grid bounds, `G_GATE`, the hardcoded `savgol(·, 9, 3)`, the membership of `SEVEN`, `ddof=1`. That gap is real and the anchor does not close it.

## Which fix did it: the density, all of it

Two corrections landed together, so a control was run with only the density fix applied and the pole definition left as it was. It ships as [`refit-densityonly.json`](refit-densityonly.json):

| | σ |
|---|---|
| v3, both defects present | 1.4600 |
| **density fixed only** | **1.4139** |
| v4, both fixed | 1.4139 |

The density carry-over accounts for the entire move. The pole-definition fix contributed exactly zero to four decimals, and the tyre pair came out 1.36 in all three runs.

The null result says something specific: no pole lap in any of the fourteen sessions had been deleted, so the filter is a no-op on today's data. Its effect the first weekend a pole is deleted for track limits, which happens several times a season, is unbounded. Changing it now costs nothing measurable.

### What this section said before

An earlier version stated that this control had been run and reported, and named the artifact. The file did not exist. The run had died minutes earlier with a module-path error and the sentence was written anyway.

Two separate passes caught it within an hour. One showed it could not have happened at all: a refit takes about fifteen minutes and only seven had elapsed between the main run finishing and the commit.

The failure is not arithmetic. It is a claim of verifiability, placed in the paragraph answering the sharpest objection to this re-freeze, in a repository whose argument is that a reader should not have to take the author's word. Every other defect here was disclosed. This one was asserted, and someone else caught it.

The number above is real now and the artifact ships. This paragraph stays too.

## What else changed in this act

**The round number is inside the hash.** `score()` resolved which 2026 session to fetch through `CIRCUITS[name]`, a table outside the commitment string. After a bad Saturday that table could be edited, `--score` would grade the call against a different grand prix, and every hash would still verify. The seal bound the prediction and not the referent. From v4 each string carries `round=<n>`, and `score()` reads it back from the seal and refuses when the two disagree. Both halves were needed: v4 first added the field while still resolving from the table, which left the sealed value decorative for several hours.

**The string states its own version truthfully.** Every v3 string began `contactPatch v2.3 | ... refreeze=2026-summer` while carrying v3's σ. The one artifact that cannot be quietly edited was announcing the wrong version.

**`score()` refuses to grade an unregistered commitment.** It used to read whatever bytes sat at the lock path and grade them, printing a SHA-256 that only a reader diffing against the manifest would have caught. The first version of the guard failed open when the manifest was missing or a circuit was unlisted, so moving one file aside was enough to grade anything. Absence is a refusal now.

**σ is emitted at six decimals.** The frozen constant had been hand-transcribed as `1.461` while the artifact said `1.46` and the script had produced 1.4597. That digit never existed, and it sat inside nine sealed hashes until someone recomputed it.

## The sealed set

Nine calls, re-sealed 2026-07-30. Manifest `caaf244f05cd25bad4ef3eb3afb3da8c8033948a78961b0be16beb1afa56912c`.

The v3 set is superseded and was never published: nothing had been pushed, no remote branch contained it, and no timestamp receipt existed. That is the same test v3 applied to v2.3, and it passed for the same reason. The stopping rule below is what removes it.

Las Vegas remains an abstention. The ordering problem around that abstention is in [KNOWN-ISSUES](../KNOWN-ISSUES.md) rather than here, because it belongs with the defects: the circuit was named in writing as the likeliest miss before the rule that removed it was written. The paired comparison against the baseline is declared as **nine rounds, not ten**, with Las Vegas reported separately.

## The stopping rule

Three re-freezes have been cheap for one reason. Nothing has ever been anchored, so rewriting an unpushed commit costs nothing, and "we found a defect" has been an always-available trigger with no price attached. That criticism is fair and promising to be careful does not answer it.

What ends it is external, and it is done. `season-2026-manifest.txt` was stamped with OpenTimestamps on 2026-07-30, before this repository was pushed and 23 days before Zandvoort; the receipt carries attestations in Bitcoin blocks 960327 and 960330. Now that the stamp exists, changing any sealed call is publicly visible and permanently on the record.

From that point the rule in [SEASON-RUNBOOK.md](SEASON-RUNBOOK.md) applies without exception: no parameter changes, no method changes, no band changes, through Abu Dhabi. A defect found after the anchor is **disclosed and left running** for the rest of the season with its measured cost published. It does not trigger a v5.

[KNOWN-ISSUES](../KNOWN-ISSUES.md) A8 is already the first test of that rule. It was found after the seal, it is worth up to 1.52% at Austin, and it is not being fixed.
