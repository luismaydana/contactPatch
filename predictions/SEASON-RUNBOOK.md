# Season run-book: eleven rounds, no pauses

The model is in parc fermé through Abu Dhabi: the season gets driven with the
car we have. From here the work is operational: lock before each qualifying,
publish the hash, score after, own the result. This file is the checklist so
none of that depends on memory or mood.

## The remaining calendar (GP qualifying start, UTC)

| Rnd | Venue | Quali (UTC) | Format | Call |
|---|---|---|---|---|
| R12 | Zandvoort | Sat 2026-08-22 14:00 | sprint | yes, planar (banking measured ~0.3 s, declared) |
| R13 | Monza | Sat 2026-09-05 14:00 | conventional | yes |
| R14 | Madrid | Sat 2026-09-12 14:00 | conventional | no call: no prior session (see the re-freeze doc) |
| R15 | Baku | Fri 2026-09-25 12:00 | conventional | yes |
| R16 | Kuala Lumpur | Sat 2026-10-03 06:00 | conventional | no call: no prior session, same rule as Madrid |
| R17 | Singapore | Sat 2026-10-10 13:00 | sprint | yes |
| R18 | Austin | Sat 2026-10-24 21:00 | conventional | yes |
| R19 | Mexico City | Sat 2026-10-31 21:00 | conventional | yes |
| R20 | São Paulo | Sat 2026-11-07 18:00 | conventional | yes |
| R21 | Las Vegas | Sat 2026-11-21 04:00 | conventional | no call: 2025 reference ran wet (v3 gate) |
| R22 | Lusail | Sat 2026-11-28 18:00 | conventional | yes |
| R23 | Abu Dhabi | Sat 2026-12-05 14:00 | conventional | yes |

Note Baku: qualifying is a FRIDAY. Note Las Vegas: the UTC date is the 21st
(Friday night local). The lock deadline is the session start above, always.

Three rounds get no call. Madrid and Kuala Lumpur are new venues with no 2025
qualifying session, so the v2.2 line has nothing to
build from. Las Vegas has a session but a wet one, and from v3 a reference that ran on
intermediates refuses to produce a call rather than building a dry-line
prediction from a wet lap. All three abstentions are declared here rather than
left as gaps.
Round numbers matter operationally, because `--score` resolves the 2026
session through them, and the two new venues shift everything behind them.
The table above is checked against the published schedule; the correction and
its proof of harmlessness are in [season-2026-locks.md](season-2026-locks.md).

The calendar also stresses the frozen rules one at a time, which makes the
back half of the season its own experiment: Monza, the fastest lap of the
year, leans hardest on the top-speed ratio; Mexico City at 2,240 m is the
density rule's sternest test; Las Vegas runs at night on the coldest tarmac
of the season, at the far edge of what a dry-only model has seen.

## Before qualifying: already done

All nine calls were locked in one act under v4, and their hashes are
published in [season-2026-locks.md](season-2026-locks.md) under a manifest hash
that binds the set. There is no weekly lock step any more, and that is the
point: a schedule that locks race by race can never demonstrate how many races
were considered and skipped, while a sealed manifest cannot lose a circuit
without changing its own hash. The document explains the trade in full, in
particular what committing early gives up.

So nothing needs to be predicted during a race week. The preimages sit in
`locks/`, which is gitignored, and they stay there until their race is scored.
On sprint weekends nothing from Friday enters anything; the inputs were frozen
in July and the sprint had not happened yet.

If a circuit somehow needs a call that is not in the manifest, the command
still exists:

```
python scripts/predict_v2.py --lock <Circuit>
```

Using it during the season would be a departure from the sealed set and would
have to be declared as one, with its own reason, in the open.

## After qualifying (same day)

```
python scripts/predict_v2.py --score <Circuit>
```

The wet rule is automatic and was fixed in advance: pole lap on INTERMEDIATE
or WET compound, or any rainfall in the session weather record, means VOID,
no discretion. Otherwise the verdict is HIT (inside σ), MISS (inside the 95%
band) or STRONG MISS (outside it, which triggers the next declared re-freeze).

Then, win or lose: move `commitment_v4.txt` and `input_2025_lap.npz` from
`locks/<circuit>-2026/` into `predictions/<circuit>-2026/` (that releases the
preimage), update the track record on the site (races.js state + result), and
if it missed, the debrief gets written with the decomposition, same as Spa
and Budapest.

## What never happens during the season

No parameter changes, no line-method changes, no band changes, no "just this
once". The January 2027 research program exists precisely so that everything
learned this season has somewhere to go that is not a mid-season tweak.

Sealing all nine calls in July makes that rule enforceable rather than merely
promised. A retune in October would not quietly improve the remaining
predictions; it would orphan them, because they were produced by a
configuration that no longer exists and their hashes are already public. There
is no version of a mid-season change that leaves the record coherent, which is
the strongest reason to have committed the season this way.

One escape valve exists and was declared before any of this: a strong miss,
meaning a call landing outside its own 95% band, triggers a documented
re-freeze. That is how Budapest was handled. It fires on evidence rather than
on mood, and it is written down in advance so that using it is not a decision
anyone gets to make after seeing a result they dislike.

## Alternative configurations, if any are ever published

A better-calibrated variant is a legitimate thing to want, and the way to have
one without damaging the record is to run it as a declared challenger rather
than as a replacement. Any such variant is bound by the same rules as the
frozen model: sealed before the season it is scored on, its full record
published, and never substituted into a call that v2.3 already made. The
frozen configuration keeps the headline, and a variant is reported next to it,
not in place of it.

The multiple-comparisons trap has to be named because it is what makes this
tempting and dangerous at once. Run k variants over ten races and the best of
them will look good by chance alone; picking that one afterwards and
presenting it as the model is cherry-picking with extra steps, and it is
indistinguishable from skill unless every variant's record is published. So
the rule is all of them or none of them, declared in advance, with k stated.
