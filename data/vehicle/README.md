# Vehicle data

The 2026 baseline car lives in code, not in a data file. The `BatchVehicleConfig` defaults in [`include/contactpatch/physics/batch_vehicle.hpp`](../../include/contactpatch/physics/batch_vehicle.hpp) are the single source of truth: 768 kg, 45.5 % front weight, a 400 kW combustion cap plus a 350 kW MGU-K on a 4 MJ store, and an eight-speed box. The full parameter table is in [ARCHITECTURE.md](../../ARCHITECTURE.md#parameters).

The values follow the public 2026 regulations and representative estimates, listed in [docs/regulations_2026.md](../../docs/regulations_2026.md). None of the numbers come from a specific team.
