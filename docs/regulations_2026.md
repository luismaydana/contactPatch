# Modeled 2026 regulations

The 2026 rule changes the simulator actually represents, and where each one lives in the code. Values are the defaults in `BatchVehicleConfig` and the constants in the QSS predictor. Anything not listed here is either modeled with a generic value or left out, and the out-of-scope items are at the bottom.

## What is modeled

| 2026 rule | how it shows up | location | value |
|---|---|---|---|
| Minimum mass reduced to 768 kg | chassis mass | `BatchVehicleConfig::mass_kg` | 768 kg |
| Active aerodynamics in place of DRS | two aero modes, low-drag X and high-downforce Z; X engages only on sustained straights (a continuous low-curvature run of at least 250 m, about three seconds at racing speed), matching the approved-zone rule rather than every short low-curvature window | `track/centerline_track` (zone detection), `physics/aero`, `sim/batch_simulator` | straight run >= 250 m at curvature < 0.003 1/m |
| MGU-K up to 350 kW, deployment tapering with speed | electric boost torque on the rear axle, full power below 290 km/h and tapering linearly to zero by 355 km/h | `physics/batch_vehicle`, `scripts/ers_dp.py`, `BatchVehicleConfig::mguk_max_power_w`, `mguk_taper_start_mps`, `mguk_taper_end_mps` | 350 kW, taper 290 to 355 km/h |
| No MGU-H | only the MGU-K is modeled | by omission | n/a |
| Combustion and electric power of similar magnitude | the QSS predictor budgets 400 kW combustion plus 350 kW electric; the forward sim drives an engine torque curve capped at the same power through an eight-speed gearbox, plus the optional boost | `scripts/qss_laptime.py`, `physics/batch_vehicle` | 400 kW + 350 kW |
| Energy store near 4 MJ | battery state of charge, recharged under braking through the MGU-K and drained by deployment | `BatchVehicleConfig::battery_capacity_j`, `scripts/ers_dp.py` | 4 MJ capacity |
| Smaller car footprint | wheelbase | `BatchVehicleConfig::wheelbase_m` | 3.40 m |
| Narrower tyres | carried in the Pacejka baseline rather than as an explicit width | `data/tires`, `physics/tire_pacejka` | baseline coefficients |

Deploy efficiency from electrical to mechanical is 0.92 and regen efficiency under braking is 0.70, both in `BatchVehicleConfig` and mirrored by the Python ERS optimizer. The 2026 rule capping recovery at 8.5 MJ per lap is not modeled; physical recovery at Suzuka stays near 2 MJ, well inside it.

## What is not modeled

- The Manual Override ("Overtake") mode, which extends full MGU-K deployment up to 337 km/h when a car is within one second of the car ahead. It only applies in wheel-to-wheel running, so it has no effect on a single qualifying lap and is left out deliberately.
- The exact FIA-defined X-mode activation zones per circuit. The model derives them from sustained straights instead, which matches the intent for a known layout like Suzuka.
- Procedural and sporting rules: how often the active aero may be used, penalties, session formats.
- Fuel chemistry and the sustainable-fuel torque map. The engine is a force cap, not a combustion model.
- The MGU-H, which 2026 removes in any case.
- Exact tyre compound widths and constructions. The tyre is a single Pacejka set, not a per-compound library.

## On the numbers

The values above follow the published 2026 technical regulations as they stood when the baseline was set. They describe a representative car rather than any specific team, and the project is not affiliated with the FIA or any constructor.
