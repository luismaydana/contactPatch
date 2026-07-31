# Verifying a call

The threat this page defends against is me: someone who made a call, watched it miss, and would like to rewrite it after the fact. The scheme makes that require finding a second preimage for a published SHA-256, so the question a reader has to settle is whether the hash checks out, and that one has an answer you can compute without me. Here is how to run it.

Each scored call ships its commitment preimage as a text file, named `commitment.txt` for the two v1 calls and `commitment_v4.txt` for the nine sealed ones. It holds the exact byte sequence that was hashed, UTF-8, single line, no trailing newline. Recomputing its SHA-256 must reproduce the registered hash exactly.

Two properties of the hash carry the whole scheme, and they are worth naming. Avalanche: change any single byte of the input, a trailing newline is enough, and the output becomes unrecognizable, which is why the byte discipline above is part of the contract rather than pedantry. Preimage resistance: given a published hash, nobody can construct a second plausible prediction string that matches it, so the only string that will ever check out is the one that existed before the session. That "nobody" has a size, and it is worth computing once instead of gesturing at: a second preimage on SHA-256 costs on the order of 2²⁵⁶ ≈ 1.2×10⁷⁷ attempts, and even at 10²¹ hashes per second, roughly the entire Bitcoin network turned to this one string, the expected time exceeds the age of the universe by about 38 orders of magnitude. The attack this scheme has to survive is not that one; it is the author quietly editing a file and hoping nobody checks, which is why the check is one command. Neither property asks you to trust this project; they are the same assumptions the rest of your digital life already rests on.

PowerShell:

```
Get-FileHash predictions/spa-2026/commitment.txt -Algorithm SHA256
```

Linux / macOS / Git Bash:

```
sha256sum predictions/spa-2026/commitment.txt
```

Expected for Spa-Francorchamps 2026:

```
03ea1c08d2132e3386a2fb50bb3d5bbbdd91fc51fe6ef22bb5a6c79f61b13519
```

Expected for Budapest 2026 (`predictions/budapest-2026/commitment.txt`):

```
b22f847955638ae96d47716e332284eefa140db4cc95a4c45712908e39fe9cf4
```

If the file's hash matches, the prediction text you are reading is byte-for-byte the one committed before the session, so nothing was edited once the result came in. If it does not match, don't trust the call. Open an issue.

## What the hash does not prove, and where this registry is weakest

The check above proves the text was not altered after the hash existed. Whether the hash existed *before* qualifying is a second, independent claim, and it needs its own evidence. This section is here because an earlier version of this file pointed at the git history for that evidence, and the git history does not support it.

Take the ordering claim apart. A commit carries an author date and a committer date, and both are settable from the environment: `GIT_COMMITTER_DATE` will put any commit at any moment its author likes. So a commit dated before a session is worth exactly what its author's honesty is worth, which is the thing under test. Git dates alone cannot anchor ordering, and it was a mistake to say they could.

What does anchor ordering is a timestamp somebody else controls. A push to GitHub is recorded server-side with the server's clock, and that record is not the author's to edit. So the sequence that carries weight is: hash committed, hash pushed, session runs, preimage released.

Applying that standard honestly to this registry gives two different answers.

**Spa and Budapest are anchored outside this repository, and that is where to check them.** Both entered the repo after their sessions had run, so the git history dates nothing. What dates them is that each call was posted publicly before its session:

- Spa-Francorchamps, posted before the 18 July session: [instagram.com/p/Da3e1CcD5uv](https://www.instagram.com/p/Da3e1CcD5uv/)
- Budapest, posted before the 25 July session: [instagram.com/p/DbOFjKsgD1f](https://www.instagram.com/p/DbOFjKsgD1f/)

Those posts carry the pole-time call itself in plain text rather than a hash, which is a stronger form of evidence and worth saying so rather than dressing it down. A hash commitment needs a reveal before anyone learns what was claimed; a number posted in the open needs nothing. The prediction was legible to anyone who saw the post, on a date that is not the author's to set, before the car ran.

Be precise about the limits, because this is the same category of evidence as a GitHub push and not better than one. The date comes from a platform's records, so it cannot be back-dated, and it also cannot be verified cryptographically or checked offline. It rests on that company continuing to display the post honestly. It is real evidence and it is not an anchor in the sense [TIMESTAMP.md](TIMESTAMP.md) describes, which is exactly why the timestamp receipt is worth doing for what comes next instead of relying on this again.

One thing this document will not do is vouch for those posts on your behalf. Open them and read the date. That is the whole design here: the check belongs to the reader, and a page that told you to trust its author about the evidence for trusting its author would be worth nothing.

**The sealed 2026 calls are the real test, and their ordering rests on the timestamp receipt rather than on this repository's history.** An earlier version of this paragraph said the hashes "were committed and pushed before any of the ten sessions ran". That was false when it was written. Nothing had been pushed: the working branch was 38 commits ahead of a remote that contained no `season-2026-locks.md`, no manifest and no `predict_v2.py`, and the sentence sat one heading below a long correction of a *weaker* ordering claim. It is worth stating plainly what that means, because it is the same defect twice. The hashes were never public, the same audit finding that forced the v3 re-freeze applied to the paragraph announcing it, and this document, whose entire job is to let you check the author rather than believe him, was the last place it survived.

So the honest description of the ordering evidence is this. The commitment strings and the manifest that binds them are in this repository, and their contents can be checked against the model by anyone, offline, in seconds. What that proves is integrity: the set has not been edited. What it does not prove by itself is *when*, because a git commit date is set by whoever makes the commit and a push date proves only that the push happened. The ordering claim is carried by the OpenTimestamps receipt over `season-2026-manifest.txt`, which puts the set in the Bitcoin chain and removes both GitHub and the author from the trusted set. [TIMESTAMP.md](TIMESTAMP.md) describes the procedure and why it expires round by round rather than at the end of the season. Until you have verified that receipt, treat the ordering as unproven and the integrity as proven, which is exactly the split this document should have described in the first place.

For the nine sealed calls, the stronger anchor exists. The manifest digest was stamped with OpenTimestamps on 2026-07-30, before this repository was first pushed, and the receipt in [season-2026-manifest.txt.ots](season-2026-manifest.txt.ots) carries attestations in Bitcoin blocks 960327 and 960330. What was done, what left the machine, and how to check it without trusting anyone here are in [TIMESTAMP.md](TIMESTAMP.md). That removes GitHub from the trusted set for everything from Zandvoort on; Spa and Budapest keep the public-post anchors above.

Sealed calls (hash published, session not yet scored) have no `commitment.txt` yet, and the reason usually given for that is wrong, so here is the real one. The preimage is not secret in any meaningful sense: the model is deterministic, the frozen configuration ships in this repository, the 2025 inputs are now published in [inputs-2026/](inputs-2026/), and this document tells you to run `predict_v2.py <Circuit>` and watch the registered hash come back. Anyone willing to spend ten seconds already has the number. What withholding the file actually buys is a clean sequence in the record, hash first and text second, so that the order is legible to someone reading later rather than reconstructed. That is a presentational property, not a cryptographic one, and calling it secrecy would be overselling it.

## v4 calls (Zandvoort onward)

Same idea, two additions. The preimage file is `commitment_v4.txt`, written as exact bytes with no trailing newline, so the same `sha256sum` check applies. And the commitment now carries an input pin: `data=<16 hex>` inside the string is a SHA-256 prefix over the raw 2025 pole-lap arrays the line was built from. When the call is scored, the pinned input ships next to the preimage as `input_2025_lap.npz`; recomputing the pin from it proves the line came from that exact telemetry, even if the upstream API later revises its data. To re-run the whole call:

```
python scripts/predict_v2.py <Circuit>
```

which must print the registered SHA-256 bit for bit while the pinned input matches.

The pinned inputs no longer wait for scoring. All ten ship in [inputs-2026/](inputs-2026/), and what they buy needs stating precisely, because an earlier version of this paragraph overclaimed it. They let you verify that the geometry a sealed call was built from is the geometry shipped here: hash the arrays, compare against the `data=` field inside the commitment, done. What they do **not** yet do is let you regenerate a lap time offline. No code path reads them. `predict_v2.py` takes its geometry from FastF1 and nothing else, and the air density that enters both the physics and the commitment string is not in these files at all. So "reproducible without the network" was wrong as written: the *pin* is checkable offline, the *prediction* is not. Wiring `--from-pin` is on the list and is not done. Nine of the ten were checked against the `data=` field of their own sealed commitment before being published; Las Vegas ships without one, because its call was withdrawn and there is no v3 or v4 commitment for it to be checked against. That step needs Python and one download; the hash check above needs neither. [HOW_TO_USE.md](../HOW_TO_USE.md) has the setup for both, and for the case where your hash comes out different.
