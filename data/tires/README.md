# Tyre data

The calibrated tyre model lives in code, not in a data file. The `PacejkaConfig` defaults in [`include/contactpatch/physics/tire_pacejka.hpp`](../../include/contactpatch/physics/tire_pacejka.hpp) are the single source of truth: peak longitudinal 1.9, peak lateral 1.8, load sensitivity −0.17, reference load 2000 N.

The stiffness, shape, and curvature terms follow the standard Magic Formula form from Pacejka's *Tyre and Vehicle Dynamics* (cited in [docs/references.md](../../docs/references.md)). The two peak-friction parameters are calibrated against real telemetry and judged on held-out laps, as described in the README's validation section. None of the values come from any team's data.
