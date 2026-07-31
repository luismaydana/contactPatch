# References

Sources the model actually draws on, with enough detail to find them.

## Tire model

- Pacejka, H. B. (2012). *Tire and Vehicle Dynamics*, 3rd ed. Butterworth-Heinemann. ISBN 978-0-08-097016-5. The Magic Formula pure-slip equations in `physics/tire_pacejka` follow Chapter 4. Combined slip here is a friction-ellipse approximation rather than Pacejka's similarity method.
- Bakker, E.; Nyborg, L.; Pacejka, H. B. (1987). "Tyre modelling for use in vehicle dynamics studies." SAE 870421. The original Magic Formula paper.

## Vehicle dynamics

- Milliken, W. F. & Milliken, D. L. (1995). *Race Car Vehicle Dynamics*. SAE International. ISBN 978-1-56091-526-3. Used for the quasi-static weight transfer model.

## Track data

- TUMFTM racetrack-database. https://github.com/TUMFTM/racetrack-database. Center lines for a set of race circuits, built from public GPS traces and a minimum-curvature optimization. License LGPL v3.0. Source of every `data/tracks/*/centerline.csv`, converted by `scripts/convert_tumftm_to_centerline.py`; `scripts/ingest_2026_tracks.py` automates the batch.

## Telemetry

- FastF1. https://github.com/theOehrly/Fast-F1. Session and timing data used as the validation reference and to build the simulator inputs.

The 2026 rule values used in the model are listed in `regulations_2026.md`.
