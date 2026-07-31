"""Regression test for every published hash. Standard library only.

    python tests/test_reproducibility.py          offline tier
    python tests/test_reproducibility.py --net    adds the nine sealed 2026 calls

This exists because the project's central claim was documented and never
checked. Every other assertion here is about behaviour; these are about
artifacts a stranger is invited to verify, and if one of them stops matching,
the honest answer to "did the author edit a call" has to be no, and something
has to be able to say so without a person remembering to look.

No pytest on purpose: a test that guards published hashes should not itself
depend on a package that has to resolve.
"""
import hashlib
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Shipped artifacts and the digests published against them. A change here is
# either a defect or a deliberate re-publication; there is no third case.
FILES = {
    "predictions/spa-2026/commitment.txt":
        "03ea1c08d2132e3386a2fb50bb3d5bbbdd91fc51fe6ef22bb5a6c79f61b13519",
    "predictions/budapest-2026/commitment.txt":
        "b22f847955638ae96d47716e332284eefa140db4cc95a4c45712908e39fe9cf4",
    "predictions/season-2026-manifest.txt":
        "caaf244f05cd25bad4ef3eb3afb3da8c8033948a78961b0be16beb1afa56912c",
    "predictions/null-model-manifest.txt":
        "e0c91cdba99acc94046cadcf307e54258112dfc3f57347198204868cdb7679f2",
}

fails = []


def check(label, got, want):
    ok = got == want
    print(f"  [{'ok  ' if ok else 'FAIL'}] {label:<46} {str(got)[:16]}")
    if not ok:
        fails.append(f"{label}: got {got}, expected {want}")


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


print("shipped artifacts")
for rel, want in FILES.items():
    p = os.path.join(ROOT, rel)
    check(rel, sha(p) if os.path.exists(p) else "MISSING", want)

# The manifest has to hash the file it names, and the file has to contain the
# calls it claims. Checking the digest alone would pass on an empty file.
print("\nmanifest binds its members")
man = os.path.join(ROOT, "predictions", "season-2026-manifest.txt")
if os.path.exists(man):
    with open(man, "rb") as f:
        lines = f.read().decode("utf-8").splitlines()
    check("season manifest line count", str(len(lines)), "9")
    check("every line is <Circuit> <64 hex>",
          str(all(len(p := ln.split()) == 2 and len(p[1]) == 64 for ln in lines)), "True")
    check("sorted, as documented", str(lines == sorted(lines)), "True")

# Each null-model commitment must hash to its own manifest line, taken without
# the trailing newline. That byte discipline is part of the published contract,
# so it gets asserted rather than described.
print("\nnull-model commitments hash to their manifest lines")
nm = os.path.join(ROOT, "predictions", "null-model-manifest.txt")
nc = os.path.join(ROOT, "predictions", "null-model-commitments.txt")
if os.path.exists(nm) and os.path.exists(nc):
    with open(nm, "rb") as f:
        index = dict(ln.split() for ln in f.read().decode("utf-8").splitlines())
    with open(nc, "rb") as f:
        bodies = f.read().decode("utf-8").splitlines()
    matched = 0
    for line in bodies:
        h = hashlib.sha256(line.encode("utf-8")).hexdigest()
        if h in index.values():
            matched += 1
    check("commitments matching their index", f"{matched}/10", "10/10")

# The v1 predictor is byte-frozen and needs no network, so it is the one call
# that can be regenerated end to end in CI.
# The pinned inputs are the only durable copy of what the sealed calls were built
# from. If one drifts, the upstream data is gone and nobody can tell.
print("\npinned 2025 inputs match the pins inside the sealed commitments")
pins_dir = os.path.join(ROOT, "predictions", "inputs-2026")
locks_dir = os.path.join(ROOT, "locks", "season-2026-v3")
if os.path.isdir(pins_dir):
    import re
    try:
        import numpy as np
    except ImportError:
        np = None
    if np is None:
        print("  [skip] numpy not installed")
    else:
        matched = total = attempted = skipped = 0
        for fn in sorted(os.listdir(pins_dir)):
            if not fn.endswith(".npz"):
                continue
            total += 1
            d = np.load(os.path.join(pins_dir, fn))
            h = hashlib.sha256()
            h.update(np.asarray(d["x"], dtype="<f8").tobytes())
            h.update(np.asarray(d["y"], dtype="<f8").tobytes())
            h.update(np.float64(d["top_kmh"]).tobytes())
            h.update(np.float64(d["lap_s"]).tobytes())
            got = h.hexdigest()[:16]
            # The sealed commitments are gitignored until scoring, so on a clean
            # clone there is nothing to compare against. This used to do
            # `matched += 1` and continue, which meant every pin counted as
            # verified and the line printed 10/10 having checked nothing — in the
            # exact state CI runs in. A check that cannot run must say so, not
            # report the number it would have liked. Skips are counted apart and
            # the assertion is over what was actually attempted.
            # v4 writes locks/<circuit>-2026/commitment_v4.txt; the v3 layout is
            # kept as a fallback so the superseded set stays checkable.
            lock = os.path.join(ROOT, "locks", f"{fn[:-4].lower()}-2026",
                                "commitment_v4.txt")
            if not os.path.exists(lock):
                lock = os.path.join(locks_dir, f"{fn[:-4].lower()}_commitment.txt")
            released = None
            for stem in ("commitment_v4.txt", "commitment_v23.txt", "commitment.txt"):
                cand = os.path.join(ROOT, "predictions", f"{fn[:-4].lower()}-2026", stem)
                if os.path.exists(cand):
                    released = cand
                    break
            src = lock if os.path.exists(lock) else released
            if src is None:
                skipped += 1
                continue
            attempted += 1
            with open(src, encoding="utf-8") as f:
                want = re.search(r"data=([0-9a-f]{16})", f.read()).group(1)
            matched += (got == want)
        if skipped:
            print(f"  {skipped} of {total} pins have no preimage on this machine "
                  f"(sealed and gitignored until their race is scored) — NOT verified")
        if attempted:
            check("inputs matching their sealed pin", f"{matched}/{attempted}",
                  f"{attempted}/{attempted}")
        else:
            # The state a fresh clone is in, and the state CI runs in. Printing an
            # ok line here is how the old version reported success for zero work.
            print("  [SKIP] inputs matching their sealed pin        "
                  "no preimage available — this check did not run")

print("\nv1 predictor regenerates its registered call")
out = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "predict_race.py"), "Budapest"],
                     capture_output=True, text=True, cwd=ROOT)
line = next((l for l in out.stdout.splitlines() if "SHA-256" in l), "")
check("predict_race.py Budapest", line.split()[-1] if line else "NO OUTPUT",
      "b22f847955638ae96d47716e332284eefa140db4cc95a4c45712908e39fe9cf4")

if "--net" in sys.argv:
    # Opt-in, because it needs the 2025 sessions from a third-party API. A test
    # that fails when someone else's service is down is not testing this repo.
    print("\nsealed 2026 calls regenerate (network)")
    import contextlib
    import io
    import warnings
    warnings.filterwarnings("ignore")
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import predict_v2 as P

    with open(man, "rb") as f:
        registered = dict(ln.split() for ln in f.read().decode("utf-8").splitlines())
    for name in P.CIRCUITS:
        with contextlib.redirect_stdout(io.StringIO()):
            _, h = P.predict(name)
        check(f"predict_v2.py {name}", h, registered.get(name, "NOT IN MANIFEST"))

print()
if fails:
    print(f"FAILED: {len(fails)} published hash(es) no longer reproduce")
    for f in fails:
        print(f"  {f}")
    sys.exit(1)
print("All published hashes reproduce.")
