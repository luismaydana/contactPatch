# How to use contactPatch

Three different people open this repository and they do not need the same things from it. One wants to check whether a published prediction is what it claims to be. One wants to re-run a prediction and see the registered hash come back. One wants to build the simulator and watch a lap. The first needs nothing installed at all, the second needs Python, and only the third needs a C++ toolchain.

The tracks below are ordered by what they cost, cheapest first, and the ordering is the argument. A registry whose audit required a working MSVC installation would have its incentives backwards: the claim the project stakes the most on should be the one a stranger can check fastest. Verifying a call takes one command and no dependencies. Building the simulator takes an afternoon. Those are deliberately different numbers.

| Track | What you need | What you get | Measured cost |
|---|---|---|---|
| [1. Verify a call](#track-1-verify-a-published-call) | nothing | proof a published call was not edited after the session | seconds |
| [2. Reproduce a prediction](#track-2-reproduce-a-prediction) | Python 3.11+, and one download for v4 | the registered SHA-256, regenerated on your machine | 3 s (v1) to 16 s (v4) |
| [3. Run the simulator](#track-3-build-and-run-the-simulator) | C++20 toolchain, CMake, Ninja, Python | a closed-loop lap, a ghost animation, the test suite | one build |

Timings are wall-clock on the machine this was written on, warm cache, and they are here to set expectations about orders of magnitude rather than to be benchmarks.

## What a fresh clone does not contain

Worth handling first, because it is the source of every "file not found" the commands below can produce, and one rule explains all of them at once.

Four directories that the pipeline writes to are absent from a clean checkout: `data/telemetry/`, `data/sim_results/`, `data/fastf1_cache/`, and `locks/`. They are absent for two different reasons, and the difference matters.

The first three fall under one clause: anything derived from session timing data is regenerable from the pipeline and is not redistributed here. FastF1 serves the raw sessions, the loader turns them into simulator inputs, and the runner and plotting scripts write the rest. Shipping a copy would mean redistributing timing data this project has no standing to redistribute, and it would mean shipping a 1.9 GB cache to save a download the user can perform in a minute. The commands that need these files also create them, so the fix is always to run the step before, never to hunt for a missing asset.

`locks/` is excluded for a reason that is not about size or licensing at all. It holds the commitment preimages for calls that have been sealed but not yet scored, and a preimage published early is a prediction leaked early. The hash goes out first and the text stays sealed until the session has run; putting that directory in the repository would break the protocol it exists to serve. Each preimage moves into `predictions/<circuit>-2026/` at scoring time, which is exactly the moment it stops being secret.

That clause has one acknowledged exception, named here rather than left as a quiet counterexample. `data/tracks/suzuka/raceline_ver.csv` is a driven line derived from timing data and it is checked in, which its own [README](data/tracks/README.md) both explains and advises against relying on. It stays because the runner needs something to drive out of the box.

Those two clauses cover the whole surface, and the check is mechanical rather than a matter of trust: `git ls-files data/` returns eighteen files, being twelve circuit centerlines, the Suzuka raceline the runner drives, and five provenance READMEs. Nothing else under `data/` is expected to exist before you run something that writes it.

## Track 1: verify a published call

This track needs no installation, no Python, and no build. Both commands ship with the operating system.

Every scored prediction publishes the exact byte sequence that was hashed before the session. Recomputing its SHA-256 must reproduce the registered value.

```bash
git clone https://github.com/luismaydana/contactPatch.git
cd contactPatch
```

Then, on Linux, macOS, or Git Bash:

```bash
sha256sum predictions/budapest-2026/commitment.txt
```

Or in PowerShell:

```powershell
Get-FileHash predictions/budapest-2026/commitment.txt -Algorithm SHA256
```

The output must be, character for character:

```
b22f847955638ae96d47716e332284eefa140db4cc95a4c45712908e39fe9cf4
```

which is the hash published for Budapest in [predictions/README.md](predictions/README.md). If it matches, the text you are reading is byte-for-byte the text that hash was computed over, so nothing was edited after the hash existed. If it does not match, do not trust the call, and open an issue.

The sealed season works the same way at the level of the set. Nine calls were committed in one act and bound under a manifest hash, so the set cannot lose a circuit without the binding changing:

```bash
sha256sum predictions/season-2026-manifest.txt
```

must return `caaf244f05cd25bad4ef3eb3afb3da8c8033948a78961b0be16beb1afa56912c`. The reasoning behind sealing the season this way, including what it gives up, is in [predictions/season-2026-locks.md](predictions/season-2026-locks.md).

Two things this check does not prove, stated here rather than left to be discovered. First, it establishes integrity and not ordering: the text was not altered after the hash existed, but *when* the hash existed is a separate claim needing separate evidence, and git commit dates are settable by whoever makes the commit. [predictions/VERIFY.md](predictions/VERIFY.md) works through what actually anchors each call and is blunt about which ones this repository cannot anchor. Second, an unscored call has no preimage on purpose, so for the nine sealed 2026 rounds there is nothing to hash yet.

## Track 2: reproduce a prediction

Verifying a hash proves a text was not edited. Reproducing the prediction proves the text came from the model rather than from a spreadsheet, which is the stronger claim and costs a little more.

One thing to settle before installing anything: **the C++ core is not on this path.** Pole-time calls come from the quasi-steady-state predictor, which is Python, and the C++ simulator answers a different question, namely whether the dynamic model stays stable when a controller drives it closed-loop. [ARCHITECTURE.md](ARCHITECTURE.md) draws the line in full. If your goal is to re-run a call, you can skip Track 3 entirely.

### Install

```bash
pip install -r requirements.txt
```

That pulls fastf1, pandas, numpy, scipy and matplotlib, pinned to exact versions. **Python 3.11 or newer**, and the floor comes from the pins rather than from the code: the scripts themselves are 3.8-clean, which is the trap, because on 3.8 pip quietly resolves backwards to a numpy 1.x and a years-old FastF1 and the hashes then fail with nothing to explain why. 3.14 is what produced the sealed calls. A virtual environment is the usual courtesy:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

`imageio-ffmpeg` sits in the same file and is optional. It only decides whether the ghost animation writes MP4 or falls back to GIF.

### The two predictors, and which call belongs to which

The repository carries two predictors on purpose, and picking the wrong one produces a hash mismatch that looks alarming and is not.

`scripts/predict_race.py` is the archived v1 path, byte-frozen. It is what reproduces the Spa and Budapest commitments, and it must never be edited, because editing it would break the only thing it is still for. It computes locally from the circuit centerlines shipped in `data/tracks/`, so it needs no network at all:

```bash
python scripts/predict_race.py Budapest
```

That prints `b22f847955638ae96d47716e332284eefa140db4cc95a4c45712908e39fe9cf4` in under three seconds, matching the registered hash exactly.

Spa is the one exception and its own [README](predictions/spa-2026/README.md) explains why in full: that call predates the single-run lock discipline and its committed string carries about a millisecond of internal drift, so re-running the frozen model today lands a millisecond away and regenerates a different string. Spa is verified through its released preimage instead, Track 1 style, and that preimage hashes to the registered value exactly.

`scripts/predict_v2.py` runs every call from Zandvoort onward under the v2.3 configuration set at the summer re-freeze. This one does need network the first time, because the v2.2 line is built from the venue's own 2025 pole lap rather than from a survey centerline, and that lap comes from FastF1:

```bash
python scripts/predict_v2.py Monza
```

First run for a given venue downloads and caches that session, roughly 40 to 70 MB per event, into `data/fastf1_cache/`. After that the command is offline and deterministic, about ten to sixteen seconds, depending on the circuit, and prints:

```
SHA-256  a53f99f01aef5dd0...
```

which is the hash published for Monza in the season table. Every one of the nine sealed calls regenerates this way and all nine were checked before their hashes were published.

`tests/test_reproducibility.py --net` checks them again, but read that as a tool you have to remember to run rather than a guarantee: CI runs the offline tier only, so the nine sealed calls are **not** regenerated automatically on every push. What CI does check is the digest of the manifest file, which proves the file was not edited and does not prove the predictor still produces those hashes. Those are different claims and only the weaker one is automated.

Run it with no arguments and it prints its own usage, including the lock and score subcommands, which belong to the operator rather than to a reader. The season's operational checklist is [predictions/SEASON-RUNBOOK.md](predictions/SEASON-RUNBOOK.md).

### If your hash differs

Assume the pipeline before you assume the model. The likely causes, in the order they actually occur: the wrong predictor for that circuit's era, a venue not in the frozen circuit table, or upstream telemetry that has been revised since the lock. The third one is handled rather than hoped about, which is what the `data=<16 hex>` field inside each v2.3 commitment string is for: it pins a SHA-256 prefix over the raw 2025 arrays the line was built from, so a scoring run reports a pin mismatch instead of silently grading a different input. The registered call still stands in that case, because the alternative, re-deriving at scoring time, would grade a number nobody ever registered.

## Track 3: build and run the simulator

### Requirements

- A C++20 compiler. The presets use MSVC from the Visual Studio Build Tools.
- CMake 3.25 or newer, with Ninja.
- Network access at configure time. CMake fetches Catch2 v3.5.4 through `FetchContent`, so there is nothing to install by hand, but the first configure does reach the internet.
- Python 3.11+ and the requirements above, to generate the runner's input trace.

### Build and test

From the project root:

```bash
cmake --preset msvc-release
cmake --build --preset msvc-release
ctest --preset msvc-release
```

`ctest` should report 23 of 23 passing. There is an `msvc-debug` preset too, with assertions and debug info, when a test fails and you want to know why.

Every push to `main` and every pull request runs exactly these three commands on a clean Windows runner in CI, which is the reason they can be quoted as working from a fresh clone rather than only on the machine that wrote them.

A platform note, since the presets say so themselves: both configure presets carry a `hostSystemName equals Windows` condition, so on Linux or macOS `cmake --preset msvc-release` refuses rather than misbehaving. `CMakeLists.txt` does carry a GCC and Clang warning branch, so a manual configure is plausible, but it is untested and CI does not cover it. Treat a non-Windows build as unverified, and if you get one working, an issue saying so would be genuinely useful.

### Run a lap

The build produces two executables. Run both from the project root so they resolve the data folder:

```bash
.\build\msvc-release\telemetry_runner.exe
```

It loads the Suzuka raceline and the Verstappen input trace, runs the closed-loop simulation, writes `data/sim_results/2026_Japan_VER_Q_sim.csv`, and prints the lap time.

That input trace is generated rather than stored, per the rule above, so on a fresh clone it does not exist yet and the runner will not find it. Two commands create it:

```bash
python scripts/fastf1_loader.py --year 2026 --gp Japan --session Q --driver VER
python scripts/telemetry_to_inputs.py --input data/telemetry/2026_Japan_VER_Q.csv --output data/telemetry/2026_Japan_VER_Q_inputs.csv
```

The second executable, `lap_optimizer`, searches the per-corner grip margins against the full simulator by coordinate descent and writes a schedule the runner picks up automatically on its next run. Both that schedule and the DP deploy windows are optional inputs. Without them the runner falls back to a single global grip margin and a heuristic ERS gate, which costs lap time and still produces a clean lap.

### The full pipeline

Session to ghost animation, in order:

```bash
python scripts/fastf1_loader.py --year 2026 --gp Japan --session Q --driver VER
python scripts/telemetry_to_inputs.py --input data/telemetry/2026_Japan_VER_Q.csv --output data/telemetry/2026_Japan_VER_Q_inputs.csv
python scripts/qss_laptime.py --telemetry data/telemetry/2026_Japan_VER_Q.csv
python scripts/ers_dp.py --telemetry data/telemetry/2026_Japan_VER_Q.csv
python scripts/visualize_ghost.py --track data/tracks/suzuka/centerline.csv --real data/telemetry/2026_Japan_VER_Q.csv --sim data/sim_results/2026_Japan_VER_Q_sim.csv
```

`qss_laptime.py` prints the greedy-ERS prediction. `ers_dp.py` prints the dynamic-programming one, the −1.7% figure the README quotes, and writes the deploy schedule the runner can then use.

Do not expect the closed-loop lap time and the QSS lap time to agree, and do not read the gap as an error. They answer different questions. The QSS number is the lap-time tool, computed from grip and curvature with a two-pass envelope; the closed-loop run is a stability demonstrator for the dynamic model, driven by a geometric controller that is not solving for the minimum-time trajectory. The distance between them measures the controller, not the physics.

## When the model does not apply

Constraints the model declares about itself, so that a result outside them is read as out of scope rather than as a failure.

- **Dry sessions only.** No weather model, no evolving grip, no track temperature. A wet qualifying session voids the call automatically, decided by compound and by the session rainfall record rather than by anyone's judgment after the fact.
- **One car, alone.** No traffic, no wheel-to-wheel racing, no dirty air.
- **Smooth asphalt.** Load transfer is quasi-static, so there is no suspension and no curb-riding. A lap that gains its time over the curbs is a lap the model cannot see.
- **Circuits with a prior session.** The v2.2 line is built from a venue's own 2025 pole lap, so a new circuit has nothing to build from. Madrid is the live case, and the honest entry there is an abstention rather than an improvised line.
- **No tyre wear.** Single flying lap, no degradation across a stint.

## Where to go next

- [README.md](README.md) for what the model is and how it was validated.
- [ARCHITECTURE.md](ARCHITECTURE.md) for the module reference, the simulation loop, the data formats, and the algorithm analysis.
- [predictions/](predictions/) for the registry: hashes, released preimages, verification steps, and the debriefs for the calls that missed.
- [docs/regulations_2026.md](docs/regulations_2026.md) for which 2026 rules are modeled and which are not.
- [KNOWN-ISSUES.md](KNOWN-ISSUES.md) for the defects found by audit, what each one costs, and why the ones inside sealed calls are being left to run.
- [tests/test_reproducibility.py](tests/test_reproducibility.py) if you would rather have a machine check every published hash than take this document's word for it. It needs no network and no test framework; `--net` adds the nine sealed calls.

If something here does not reproduce, that is worth an issue. A set of instructions that works only on the machine it was written on is a bug in the instructions.
