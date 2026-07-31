# Track data

Each `<track>/centerline.csv` holds the circuit centerline in the project schema. The format, units, and regeneration steps are documented in [suzuka/README.md](suzuka/README.md); every circuit follows the same schema.

All centerlines are converted from the [TUMFTM/racetrack-database](https://github.com/TUMFTM/racetrack-database) (LGPL v3.0), which builds them from public GPS traces. `scripts/convert_tumftm_to_centerline.py` performs the conversion and `scripts/ingest_2026_tracks.py` automates the batch download. The database is cited in [docs/references.md](../../docs/references.md).

Because they derive from that database, the centerline files in this directory are distributed under **LGPL v3.0** (full text in [licenses/](../../licenses/)), not under the project's MIT license.

## One file here is not a centerline

`suzuka/raceline_ver.csv` shares the schema but not the origin, and the paragraph above does not cover it. It is a real qualifying lap's GPS trace, smoothed and resampled onto the same 5 m spacing by `scripts/make_expert_line.py`, which exists so the closed-loop simulator can drive the line a driver actually took instead of the geometric middle of the road. Corner radius is what sets corner speed, and a driven line opens radii that a centerline never does, so the two files produce visibly different laps from identical physics.

Its provenance is official timing data by way of FastF1, so neither the LGPL notice above nor the project's MIT license applies to it. Treat it the way the repository treats every other timing-derived file and regenerate it rather than depending on the copy checked in here:

```
python scripts/make_expert_line.py \
    --telemetry data/telemetry/2026_Japan_VER_Q.csv \
    --output data/tracks/suzuka/raceline_ver.csv
```

The input telemetry that command reads is itself generated rather than stored, for the same reason.
