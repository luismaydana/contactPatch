# v4 re-freeze: scope, fixes, stopping rule. Declared before any code was touched.

Sealed before the first edit, for the same reason as v3 and with one more
reason on top. The v3 declaration existed because the person correcting the
defects already knew which way he wanted the answer to move. That still holds.
What is new is that this is the third re-freeze in eight days, and a project
that re-freezes whenever it finds a defect has replaced a commitment with a
habit. So this file also has to say what closes the door, not only what opens
it.

## Why this is a re-freeze and not a violation of parc fermé

Same test as v3, applied honestly and passed for the same reason. The nine v3
calls were sealed locally on 2026-07-29. Verified 2026-07-30: nothing has been
pushed since 2026-07-26, the local branch is 38 commits ahead of `origin/main`,
and `origin/main` contains no `season-2026-locks.md`, no `season-2026-manifest.txt`
and no `predict_v2.py`. No `.ots` receipt exists. The nine hashes have never
been public in any form.

No 2026 session has been run under v3. Zandvoort is 23 days away. There is no
result to launder, and nothing anyone has seen to break.

Spa and Budapest are untouched, as in v3. Those two were published externally
before their sessions, the `predict_race.py` path stays byte-frozen, and the v1
record stands exactly as it is.

## The defect that forces this

`scripts/refit_loo.py` computes the seven-fold leave-one-out error that produces
the published sigma. At the point where it makes the blind prediction for the
held-out circuit it passes that circuit's **2026** session air density:

```python
m = blind(D[label]["d25"], p1, p2, r, D[label]["d26"]["rho"])
```

The production path cannot do this. `predict_v2.py:135` sets `V.RHO = s25["rho"]`,
the 2025 carry-over, because when a call is sealed in July the 2026 session has
not happened. Every aerodynamic force scales linearly in density.

So the published sigma was measured with an input the sealed calls do not have.
It is not an out-of-fold estimate of anything the model will be asked to do. The
number is optimistic by an amount that cannot be known without recomputing it,
which is the whole reason this cannot be handled by disclosure alone: a declared
limitation whose size is unknown is not a limitation, it is a hole.

Publishing a sigma known to be measured this way, in a project whose entire
argument is that the reader should not have to trust the author, would be the
first genuinely dishonest act in the record. That is the bar this clears, and it
is why the cost of a third re-freeze is worth paying.

## The three corrections, fixed now, with no discretion left for later

**1. The density carry-over.** `refit_loo.py` passes the held-out circuit's 2025
session density into the blind prediction, matching `predict_v2.py:135` exactly.
The calibration then measures what production can actually do.

**2. The pole definition.** `refit_loo.py:54` loads with `messages=False` and
line 60 takes `pick_fastest()` with no deleted-lap filter. `predict_v2.py:268-274`
documents that without `messages=True` FastF1 never populates the `Deleted`
column, so a track-limits filter is a silent no-op. The calibration is therefore
fitted against a different definition of "pole" than the one the season will be
scored under. It loads with `messages=True` and applies the same non-deleted rule
as `--score`.

**3. The sigma transcription.** `SIGMA = 1.461` in `predict_v2.py` was written by
hand. `refit_loo.py:149` writes `round(SIGMA, 3)` and the artifact says `1.46`, so
the script never produced 1.461. Recomputation from the published fold errors gives
1.4597. The script will emit sigma at a precision that makes transcription
checkable rather than approximate, and the frozen constant will be whatever it
emits, copied exactly.

## What is committed in advance

**The new sigma is adopted whichever way it moves.** The density fix removes
information from the calibration, so the honest expectation is that sigma gets
worse for the second consecutive re-freeze. It is adopted regardless. No
threshold, no second look, no "unless it is unreasonable". If it improves, that
is adopted too and the improvement is reported as what it is: the removal of a
leak, not a better model.

**No parameter is re-fitted by hand.** The tyre pair and the ratio come out of
the corrected script. The grid, the bounds, the 5 g gate, `SG_WINDOW = 9`,
`K_SMOOTH = 3`, the 5 m resample and the identity of the seven evidence circuits
are unchanged from v3. This re-freeze fixes how the error is measured, not what
the model is.

**The nine circuits stay nine.** Las Vegas remains an abstention under the
existing wet-reference rule. No circuit enters or leaves this set. If a circuit
looked likely to miss it stays in, and the manifest binds the set exactly as
before.

**The known-defect list is corrected in the same act**, not deferred: the section A
entries that say "It stands" for defects v3 already fixed, the `MU_MIN` crossover
recomputed against `RATIO` and per-session density rather than module defaults,
the season-forecast arithmetic that used `1/T68` where the predictive scale
factor belongs, and the ten-versus-nine count. These are documentation defects
found in the same audit and they are fixed now rather than surviving into a
fourth re-freeze.

## The stopping rule

Three re-freezes have been cheap for one reason: nothing has ever been anchored.
Rewriting an unpushed git commit costs nothing, so "we found a defect" has been
an always-available trigger with no price attached. That is a real structural
criticism and it does not go away by promising to be careful.

What ends it is an external anchor.

**`predictions/season-2026-manifest.txt` is stamped with OpenTimestamps and the
receipt committed before the repository is pushed, and before Zandvoort on
2026-08-22.** After that stamp exists, changing any sealed call is publicly
visible and permanently on the record. The declared rule from that point is the
one already written in `SEASON-RUNBOOK.md`: no parameter changes, no method
changes, no band changes, through Abu Dhabi, and the only escape valve is a
strong miss, which fires on evidence rather than on discovery.

If a further defect is found after the anchor, it is **disclosed and left
running** for the rest of the season, with its measured cost published, exactly
as `KNOWN-ISSUES.md` section A was supposed to work. It does not trigger a v5.
The anchor is the point where the model stops being editable and starts being
accountable, and putting that in writing before the refit is run is the only way
the commitment means anything.

## Pre-edit state

Digests of the files about to be modified, taken before the first edit:

```
scripts/refit_loo.py        d7574d5fc9a32e54
scripts/predict_v2.py       6b8221d6ff64f5fb
scripts/cp/v2physics.py     1959a54a1493a708
```

`v2physics.py` is listed because it is the physics module the refit runs against.
No change to it is planned or authorised by this declaration; its digest is
recorded so that any change to it would be visible.

Superseded set: the nine v3 hashes under manifest
`c8fe88c49b1320f9...`, sealed 2026-07-29, never published.

Declared 2026-07-30, before any edit.
