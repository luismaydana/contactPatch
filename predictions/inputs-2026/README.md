# The pinned 2025 inputs

Ten files, seventy kilobytes, and they exist because of a failure mode the rest of the registry could not survive.

Every v2.3 call is built from one venue's 2025 pole lap: its GPS geometry, its top speed, its lap time. That data lives on a third-party API. If it is revised, or the API changes how it merges telemetry, or the service goes away, then every sealed call becomes unreproducible from scratch and the invitation in [VERIFY.md](../VERIFY.md) to re-run the model and watch the hash come back stops meaning anything. The commitment strings would still verify against their own bytes, but the stronger claim, that the number came from the model rather than from somewhere else, would be unavailable to anyone forever.

So the inputs ship here instead of being trusted to stay put.

Each `<Circuit>.npz` holds the four arrays the pin is computed over: `x`, `y` in metres, `top_kmh`, and `lap_s`. Recomputing the SHA-256 over them in that order, little-endian float64, and taking the first sixteen hex characters must reproduce the `data=` field inside that circuit's commitment string. All ten were verified that way before being committed.

```
python tests/test_reproducibility.py
```

checks them along with everything else.

Two notes on what this does and does not do. It **does** pin the geometry against a later upstream revision, which is the point, and it lets anyone check offline that the arrays here are the arrays a sealed call was built from. It does **not** make a call reproducible without the network, which this file used to claim: nothing in `scripts/` reads an `.npz`, `predict_v2.py` sources its geometry from FastF1 only, and the session air density that enters both the physics and the commitment string is not stored here. Reproducing a lap time still needs one download. It does **not** prove the arrays came from any particular session: the pin is self-certifying, so it binds the file to the commitment and nothing binds either to reality except the fact that anyone can pull the same session today and compare. That gap is named in [KNOWN-ISSUES.md](../../KNOWN-ISSUES.md) rather than papered over.

One thing the pin misses, worth stating here because this directory is where a reader would look for it. Air density is computed from the same session's weather record and feeds the physics directly, but it is **not** part of the hashed material, and the weather rows are not in these files. A weather revision would change a prediction while the pin still reported a match. Extending the pin cannot be retrofitted to a sealed call, so it is a v3 change; for now the density appears in the commitment string to four decimals, which is at least visible.

The archives are written with fixed timestamps so the files themselves are byte-stable. Nothing in the protocol depends on that, since the pin is over the arrays rather than the container, but a file that changes its own hash every time it is written is an unhelpful thing to publish.
