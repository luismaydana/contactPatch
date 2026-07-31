# Anchoring the manifest in time

[VERIFY.md](VERIFY.md) is blunt about the weakest joint in this registry. The hashes prove integrity. Nothing in a repository proves *ordering*, because git commit dates are settable by whoever makes the commit, and a push to GitHub asks a reader to trust one company's records.

That dependency was removed on 2026-07-30, before this repository was first pushed. This file records what was done and how to check it.

## What got anchored

One file: [season-2026-manifest.txt](season-2026-manifest.txt), which binds all nine sealed calls. Anchoring it anchors the set, because removing or altering any call changes the manifest digest:

```
caaf244f05cd25bad4ef3eb3afb3da8c8033948a78961b0be16beb1afa56912c
```

## What left the machine, exactly

A 32-byte hash. Not the manifest, not the predictions, not even a filename. OpenTimestamps sent that digest to public calendar servers, which aggregate many digests into a Merkle tree and commit the root to the Bitcoin blockchain. None of the predictions was disclosed; SHA-256 is not invertible and the calendars never see the input. Nothing was paid, either. The calendars fund one transaction that covers thousands of stamps.

## The record

`ots stamp` ran on 2026-07-30. The calendars carried the digest into the chain within hours, and the upgraded receipt ships next to the manifest as [season-2026-manifest.txt.ots](season-2026-manifest.txt.ots). It holds two independent attestations:

| Bitcoin block | Block merkle root |
|---|---|
| 960327 | `d20f453049c7ec60772580843e88b3a18c03bdb38029b06fbd36e557c4e7ef15` |
| 960330 | `63d7f9792ed0a48cd8e6e62cda723582e98adeeb1fc299b227e18dec3ddcb4aa` |

Two paths through two calendars, so the proof survives either of them disappearing.

Zandvoort qualifying runs on 22 August. The anchor precedes it by 23 days, and precedes every other sealed session by more than that.

## Check it yourself

```
ots info predictions/season-2026-manifest.txt.ots
```

prints the proof tree, ending in the two block attestations above. A full `ots verify` wants a local Bitcoin node, which most readers do not run. Without one the check is still short: compare the merkle roots printed by `ots info` against blocks 960327 and 960330 in any block explorer. If they match, the digest was in the chain when those blocks were mined, and the receipt proves the manifest hashes to that digest.

A second, independent authority would guard against the OpenTimestamps calendars themselves going away. Any RFC-3161 service works and freetsa.org is free. That remains undone, and it is worth doing.

## What it still will not prove

A timestamp proves the manifest existed at a time. It says nothing about whether the sealed strings are what the model produced or numbers chosen by hand. Only reproduction settles that, which is what `predict_v2.py <Circuit>` and the pinned inputs in [inputs-2026/](inputs-2026/) are for. Ordering and provenance need separate mechanisms, and this file supplies one of them.
