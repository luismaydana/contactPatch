# v4 declaration, amendment 1: what the commitment string binds

Amends the v4 declaration sealed 2026-07-30 as
`676ab520ea963f76def9a2a96b2261aec25b27cf1c10a9cc5af1752a2663865d`.

That file is not edited. It is sealed, and editing a sealed declaration to add
something convenient is the exact move the sealing exists to prevent. So this is
a separate document with its own date and its own hash, and the record shows two
declarations rather than one tidy one. That is the honest shape of what happened.

## What is being added, and why it was not in the first declaration

The first declaration was written to cover three defects found by a statistical
audit. While it was being executed, an adversarial review of the protocol
returned a finding that is not about the model at all:

> The round number is a post-seal, author-mutable input that selects **which
> real-world result the sealed number is compared against**. `predict_v2.py:266`
> resolves the 2026 session through `CIRCUITS[name]`, and the commitment string
> contains no round. After a bad Saturday the table can be edited, `--score`
> fetches a different grand prix, and every hash still verifies.

The seal binds the prediction and not the referent. `season-2026-locks.md`
presents the round's absence from the string as a safety property — no hash can
depend on it, so correcting the table was harmless. Read adversarially it is the
opposite: the one input that decides what the prediction is graded against is
the one input nobody committed to. The table has already been wrong once, for
seven of ten circuits.

This matters now and not in January because of the stopping rule in the first
declaration. The OpenTimestamps anchor is meant to end the re-freeze sequence,
and after it no sealed call can change. A hole left open at the moment of
anchoring is a hole for the whole season.

## The two additions

**1. The 2026 round number enters the commitment string.** Each sealed call
carries the round it will be scored against, so the referent is inside the hash.
Changing the table afterwards then breaks the hash it belongs to, which is what
the reader was entitled to assume all along.

**2. The string states its own version truthfully.** Every v3 string begins
`contactPatch v2.3 | ... refreeze=2026-summer` while carrying v3's `sigma=1.461%`.
The hashed artifact — the one object that cannot be quietly edited — announces
the wrong version and the wrong re-freeze. Under v4 it says v4.

Neither addition changes a parameter, a method, or a predicted time. They change
what the hash covers and what the string admits about itself.

## What is unchanged from the first declaration

Everything else, explicitly and without exception:

- The new sigma is adopted whichever way it moves, with no threshold and no
  second look. The expectation remains that it gets worse.
- No parameter is re-fitted by hand. Tyre pair, ratio, grid, bounds, the 5 g
  gate, `SG_WINDOW`, `K_SMOOTH`, the 5 m resample and the seven evidence
  circuits are as they were.
- The nine circuits stay nine. Las Vegas remains an abstention. No circuit
  enters or leaves.
- The OpenTimestamps anchor over the manifest, before the push and before
  Zandvoort, is the stopping rule. A defect found after the anchor is disclosed
  and left running for the season; it does not trigger a v5.

## Pre-edit state

`predict_v2.py` is unmodified since the first declaration and still hashes to
`6b8221d6ff64f5fb`, which is the digest recorded there. `refit_loo.py` has been
modified under the first declaration's three corrections and now hashes to
`5536ea9eeddd644a`; its corrected form is running the refit as this is written,
and nothing in this amendment touches it.

Declared 2026-07-30, before the commitment-string format was changed.
