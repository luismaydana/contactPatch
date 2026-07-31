# Anchoring the manifest in time

[VERIFY.md](VERIFY.md) is blunt about the weakest joint in this registry. The hashes prove integrity. Nothing here proves *ordering* except a third party's log, and git commit dates are settable by whoever makes the commit, so on their own they establish nothing at all. A push to GitHub is better, since the timestamp belongs to the server rather than to me, but it still asks a reader to trust one company's records.

There is a way to remove that dependency. It costs about ten minutes. This file exists so it gets done as one deliberate act instead of buried inside a script.

## What gets anchored

One file: [season-2026-manifest.txt](season-2026-manifest.txt), which binds all nine sealed calls. Anchoring it anchors the set, because removing or altering any call changes the manifest digest:

```
caaf244f05cd25bad4ef3eb3afb3da8c8033948a78961b0be16beb1afa56912c
```

## What leaves the machine, exactly

A 32-byte hash. Not the manifest, not the predictions, not even a filename. OpenTimestamps sends that digest to public calendar servers, which aggregate many digests into a Merkle tree and commit the root to the Bitcoin blockchain, and the receipt that comes back proves the digest existed before the block carrying it.

None of the predictions is disclosed. SHA-256 is not invertible and the calendars never see the input.

It is still an irreversible outward action. Once a digest is in a public calendar it cannot be withdrawn, which is why this is written down for a person to run rather than performed by a script.

## The commands

```bash
pip install opentimestamps-client
ots stamp predictions/season-2026-manifest.txt
```

That writes `season-2026-manifest.txt.ots` next to the file. Commit it. The receipt is incomplete for the first few hours, until the calendar's aggregation makes it into a block:

```bash
ots upgrade predictions/season-2026-manifest.txt.ots
ots verify predictions/season-2026-manifest.txt.ots
```

`verify` prints the block time the manifest is proven to predate.

A second, independent authority costs nothing and guards against one calendar disappearing. Any RFC-3161 service works. freetsa.org is free, and its receipt is a signed file that gets committed alongside the `.ots`.

## Why before 22 August rather than in January

The deadline is not administrative. Every day the manifest goes unanchored is a day of season that can never be anchored retroactively, because the only thing worth proving is that the calls existed *before* the sessions they speak about.

Zandvoort runs on 22 August. From that moment an anchor covers eight remaining rounds instead of nine, then seven, and eventually none.

If the tooling turns out to be a problem, the cheapest partial substitute is a snapshot of the published manifest at `web.archive.org`. Thirty seconds, a third party's dated and immutable copy, and better than nothing. It is worse than a receipt because it depends on that organisation continuing to exist, where an `.ots` file verifies offline against the Bitcoin chain for as long as the chain does.

## What it still will not prove

Saying this plainly so the anchor does not get oversold the way the git-history claim was.

A timestamp proves the manifest existed at a time. It says nothing about whether the sealed strings are what the model produced or numbers chosen by hand. Only reproduction settles that, which is what `predict_v2.py <Circuit>` and the pinned inputs in [inputs-2026/](inputs-2026/) are for. Ordering and provenance need separate mechanisms and this file only supplies one of them.
