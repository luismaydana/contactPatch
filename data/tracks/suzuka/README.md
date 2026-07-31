# Suzuka track data

## Files

- `centerline.csv`: 1161 points at about 5 m spacing, total length 5798 m; real Suzuka is 5807 m, so the reconstruction error is (5807 − 5798)/5807 = 0.155%. Sourced from [TUMFTM/racetrack-database](https://github.com/TUMFTM/racetrack-database) via `scripts/convert_tumftm_to_centerline.py`. LGPL v3.0, cited in `docs/references.md`.

## Schema (centerline.csv)

```
s_arc,x,y,z,width_left,width_right,sector
0.000, 0.0, 0.0, 0.0, 7.5, 7.5, 1
1.234, 1.230, 0.085, 0.0, 7.5, 7.5, 1
```

All units are SI meters and `s_arc` increases monotonically. The `sector` column labels each point 1, 2, or 3. The simulator reads arc length, position, and sector, and recomputes curvature from the geometry. The `z` and width columns are not used.

## Regenerating the file

From a fresh TUMFTM snapshot:

```
curl -O https://raw.githubusercontent.com/TUMFTM/racetrack-database/master/tracks/Suzuka.csv
python scripts/convert_tumftm_to_centerline.py Suzuka.csv data/tracks/suzuka/centerline.csv
```

From a different source such as a GPS trace or telemetry:

1. Sample at 1 to 5 m arc-length intervals.
2. Center on (0, 0) at the start line with x pointing forward.
3. Smooth lightly for jitter, but do not smooth toward a racing line.
4. Write `centerline.csv` matching the schema above.
