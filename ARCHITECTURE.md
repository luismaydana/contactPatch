# Architecture

This document describes how contactPatch is put together: the simulation loop, the modules, the data formats, and the simplifications I made along the way. It tracks the code as it actually runs, not an idealized version of it.

## Design goals

A few decisions shaped everything else.

- Determinism. The core is plain C++ with no threads, no random numbers, and fixed-point time stepping. A given set of inputs produces the same trajectory byte for byte. That makes regressions easy to catch, lap times easy to compare, and it is the property every hash in [predictions/](predictions/) leans on.
- Planar physics. The car is a flat rigid body with three degrees of freedom plus four spinning wheels. Yaw is what lets a car be loose or tight, so it stays; springs and dampers price ride motions this project never asks about, so they go. That split leaves enough state for the car to misbehave like a car, and little enough to stay debuggable.
- One car, one lap. There is no traffic and no race state machine. The unit of work is a single flying lap on a single track.
- Configuration lives in plain structs. Vehicle, tyre, and aero parameters are fields on `BatchVehicleConfig` and its sub-structs, with defaults set to a 2026 baseline. There is no config file parser in the hot path.

## Frames and conventions

Two frames, both right-handed with z pointing up.

- World frame. Fixed to the track origin. The car's position `(x_m, y_m)` and heading `yaw_rad` live here.
- Body frame. Fixed to the chassis center of mass. x points forward, y points left, z points up. Velocities (`v_long_mps`, `v_lat_mps`), yaw rate, and all force accumulation happen here.

Wheel order is fixed everywhere: `FL=0, FR=1, RL=2, RR=3`. The front wheels steer, the rear wheels drive.

## The simulation step

The entry point is `BatchSimulator::step(inputs, dt)`. One call advances the world by `dt` and does four things in order.

```
BatchSimulator::step(inputs, dt)
  1. pick aero mode      max curvature over the next 50 m -> X_MODE or Z_MODE
  2. substep loop        split dt into chunks of at most 1 ms
       step_batch_vehicle(config, state, inputs, sub_dt)
         evaluate_batch_forces   aero, loads, slips, tyre forces, thermal, ERS
         update_batch_state      integrate chassis and wheels
  3. project to track    map (x, y) back to arc length, lateral offset, heading
  4. lap and sector timing
```

The integration is semi-implicit (symplectic) Euler, and the choice has a reason. Plain explicit Euler quietly pumps energy into anything that oscillates, and a car model is full of things that oscillate; a fully implicit scheme buys stability at the cost of a solve per substep. Advancing the velocities first and then moving the position with the velocities you just computed costs nothing extra over explicit Euler and keeps the energy bounded, which is why so much of game physics and molecular dynamics runs on this same scheme. Inside `update_batch_state`, the body velocities are advanced first using the forces evaluated at the current state, then the world position is advanced using the velocities that were just updated. Wheel angular speeds advance with explicit Euler in the same substep. The fixed substep is 1 ms; if `step` is called with a larger `dt`, it is divided into equal chunks so the physics never sees a step bigger than that.

Cost per call is O(dt / 1 ms) substeps, and each substep is O(1): four wheels, a fixed force chain, no allocation and no search that grows with the track. A 90 s lap is therefore about 90,000 substeps, and the whole run is linear in lap time with a constant that a profiler, not an asymptotic argument, is the right tool for. The energy claim above is worth stating as a bound rather than a slogan: a symplectic integrator does not conserve the true energy either, it conserves a nearby shadow quantity, so its energy error stays bounded and oscillating instead of growing without limit the way explicit Euler's does. Over one lap the distinction rarely matters. Over the tens of millions of substeps `lap_optimizer` runs, a scheme that drifts monotonically would make late candidates incomparable with early ones, and the search would be optimising the drift.

One detail worth knowing: load transfer uses the previous substep's accelerations (`last_a_long_mps2`, `last_a_lat_mps2`). The normal loads are therefore lagged by one substep. At 1 ms this lag is small, and it avoids an algebraic loop between forces and loads.

## Modules

### core/types.hpp

`Real` is a `float`. There is a small `Vec3`, a `Wheel` enum, and a `PerWheel<T>` array alias. Single precision is a deliberate choice: it halves memory traffic and the determinism guarantees hold as long as the build keeps `/fp:precise` and contraction off. Being exact about what is enforced and what is merely relied on: `CMakeLists.txt` passes `/fp:precise` on MSVC and `-ffp-contract=off` on GCC and Clang, so on the primary MSVC build contraction is left to the compiler's default under `/fp:precise` rather than pinned by a flag. Determinism also has no regression test behind it. Both existing determinism tests run the same binary twice in one process, which demonstrates purity and says nothing about reproducibility across compilers or standard-library versions. A pinned golden lap time would, and it is on the January list.

### track/centerline_track.hpp

A track is a list of `CenterlinePoint`s, each with arc length, position, curvature, and a sector index. The class loads them from CSV, then offers the queries the rest of the engine needs.

- Curvature is recomputed from geometry on load using the Menger formula (signed, from the triangle area of three consecutive points). Any curvature column in the file is ignored, on principle: curvature is derivable from the positions, and a derived quantity stored next to its source will eventually disagree with it.
- `project_to_track(x, y, hint)` finds where the car is along the line. It does a windowed nearest-vertex search around the arc-length hint, then refines onto the two adjacent segments. The result is arc length, signed lateral offset, and track heading. The window is there for correctness, and Suzuka is the track that forces the point: the circuit is a figure eight, the only one on the calendar, and near the crossover the early part of the lap passes within a few meters of a section that is thousands of meters away in arc length. An unwindowed nearest-point search there sees two candidate points at nearly the same distance and will happily snap to the wrong arm, teleporting the car most of a lap forward or backward in one substep, at which point the lap timer, the sector logic and the speed planner all inherit the lie at once. Constraining the search to a window around where the car was last seen removes the failure, and the window size is not a guess.

An earlier version of this section argued the point badly enough to be worth replacing in the open rather than editing quietly. It set out to show that *the true nearest point never escapes the window*, which is not only unprovable but is the negation of the paragraph above: at the crossover the globally nearest point **is** on the wrong arm, thousands of metres away in arc length. If that theorem held, the window would have nothing to do. The argument also assumed a projection every millisecond, when `project_to_track` runs once per `step()` and both apps step at 10 ms.

The provable statement is different and is the one that matters. What must never escape is the **tracked** point, the one continuous in the car's motion, and it cannot, because it moves at the car's own speed. Displacement between projections is at most `v_max · dt` = 100 × 0.01 = **0.92 m** at the model's top speed, against a 60 m half-width, so the safety factor is **65×**. The window must therefore be wide enough for one step of motion plus the widest lateral excursion, and narrow enough to **exclude** the global optimum on the other arm. Both conditions hold at 60 m, and the second is the one doing the work.

Two honest caveats. At a one-second step the displacement would be 92 m and the bound would fail, so the earlier claim that it survives two orders of magnitude of step growth is false. And `tests/test_batch_track_projection.cpp` calls the function only with the default hint, so the windowed branch this paragraph is about has no test at all.

The window is worth being precise about in the other direction too, because it is not an asymptotic win. The loop still walks all 1,161 vertices and rejects the far ones with a single arc-distance comparison, so the pass stays O(n); what the window strips is the expensive half, leaving roughly 24 candidates at 5 m spacing to measure and refine against. Neither version is slow enough here to be worth timing. The window earns its place on correctness alone, and the arithmetic it saves is a side effect.
- `max_curvature_in_range(s, span)` returns the sharpest curvature over a forward arc span. The speed planner and the aero switch both use it to look ahead.
- `sample_at_s` and `get_sector_at` interpolate position and read the sector label at a given arc length, wrapping around the lap.

Costs, since a track query sits inside the hottest loop in the program. Loading is O(n) for the Menger pass over n = 1,161 points at Suzuka and happens once. `max_curvature_in_range(s, span)` looks like it should cost O(span / spacing), twelve points for the 60 m aero lookahead, and it does not: the implementation walks all 1,161 points and filters each one with `in_forward_arc_span`, so it is O(n) like the rest. It is also the worst of them, because the speed planner calls it once per lookahead segment rather than once per step. `get_sector_at` and `get_curvature_at` are O(n) linear scans for the same reason, which deserves stating plainly because the array they scan is sorted: `s_arc` increases monotonically by the schema's own guarantee, so `std::lower_bound` would answer the same question in O(log n). At one `get_sector_at` per step over a 90 s lap that is about 104 million float comparisons where roughly one million would do, a factor of 106.

It has not been changed, and the reason is the freeze rather than the arithmetic. This file is upstream of every lap the C++ side has ever produced, the calls in [predictions/](predictions/) were made against it, and a 106x speedup on a loop that already runs a lap in well under a second buys nothing that justifies touching the frozen path before a season. It is written down here so that a reader who spots it knows it was measured rather than missed, and it belongs on the January list with the rest of the work the freeze is holding back.

### physics/aero.hpp

Two aero modes, picked by the simulator and stored on the state. `Z_MODE` is the high-downforce corner setting, `X_MODE` is the low-drag straight-line setting that replaces DRS for 2026.

`compute_aero_forces` builds dynamic pressure `q = 0.5 * rho * v^2`, then drag along the reverse velocity direction and downforce along body z. The lift coefficients are negative, so downforce points down. The center of pressure sits slightly ahead of the center of mass (`cop_offset_z = (-0.05, 0, 0)`), and the moment is the cross product of that offset with the aero force. That offset is what lets aero balance be tuned without touching the static weight distribution, and the distinction matters because the two balances rule different speeds: weight distribution decides how the car behaves in the slow corners, where downforce is a rounding error, while the center of pressure decides the fast ones, where the wings carry more load than the mass does. The crossover between those regimes is computable rather than folklore. Downforce is `0.5·ρ·v²·C_L·A`, weight is `m·g = 768 · 9.81 ≈ 7.5 kN`, and setting them equal with the frozen coefficients (`C_L = 5.0`, `A = 1.5`, `ρ ≈ 1.2`) would give `v = √(7534/4.5) ≈ 41 m/s`, about 147 km/h, if downforce were simply quadratic in speed. It is not: `downforce_z` always multiplies by the ground-effect term `ge(v)`, which runs from 1 to 2, and dropping it is an error this document made twice. Solving `4.59·v²·ge(v) = 7534` properly puts the crossover at **34 m/s, about 122 km/h**. Below that, the car is a mass on springs of rubber; above it, an inverted wing that happens to have wheels, and by 280 km/h `ge` has reached 1.79 and the aero load is **49.8 kN, about 6.6 times the weight** rather than the 27 kN and 3.6× stated here before. Any corner taken above ~150 km/h is therefore argued with the center of pressure, not with the static distribution, which is why the two balances get separate dials. A car can be stable in one regime and treacherous in the other, and this offset is the model's dial for that second regime.

### physics/tire_pacejka.hpp

Pure-slip longitudinal and lateral forces from the Pacejka Magic Formula. For each axis the peak `D = mu * Fz`, with `mu = p_d1 + p_d2 * dfz` and `dfz = (Fz - Fz0) / Fz0`. That `p_d2` term is the load sensitivity: grip per newton drops as the tyre is pushed harder, and one worked case shows why a heavier car does not corner proportionally faster. Take the baseline pair 1.8 / −0.17 and double the load from the reference: `dfz` goes from 0 to 1, so `mu` falls from 1.80 to 1.63, and the peak force goes from `1.80·Fz0` to `1.63·2·Fz0 = 3.26·Fz0`. Proportional scaling would have given 3.60. The second half of the load buys about 81% of what the first half bought, and since cornering capability is force over mass, a car whose extra load comes from its own weight ends up with less lateral g than it started with. Every downstream behaviour that looks like strategy, protecting the loaded tyre, wanting load transfer small, the whole logic of running a car light, is this one line compounding. Stiffness `B`, shape `C`, and curvature `E` follow the standard form. Self-aligning moment is a simple pneumatic-trail times `Fy`. The two lateral peak parameters are calibrated against real telemetry; the README's validation section describes the fit and its holdout.

Combined slip is not handled inside this file. The pure-slip `Fx` and `Fy` come out independently and are reconciled by the friction ellipse in the vehicle module.

### physics/batch_vehicle.hpp

This is the core. `evaluate_batch_forces` runs the whole force chain for one substep, then `update_batch_state` integrates. The chain:

1. Contact velocities and slips. Each wheel's velocity is the chassis velocity plus the yaw-rate cross term at the wheel position. Front-wheel velocities are rotated into the steered frame. Slip ratio and slip angle come from the contact velocity and the wheel's surface speed. Slip is the part of tyre behavior that surprises everyone the first time: a tyre makes no force by rolling faithfully, it makes force by sliding a controlled amount. The two quantities measure the two kinds of controlled sliding. Slip ratio is the mismatch between how fast the wheel surface moves and how fast the ground passes under it, a few percent under drive or braking; slip angle is the mismatch between where the wheel points and where it actually travels, a few degrees under cornering. Force rises with each of them up to a peak and then falls away, and that falling side is what a lockup and a slide actually are: the tyre pushed past its peak, giving less back for more slip. The Magic Formula's B, C and E coefficients exist to draw exactly that rise-peak-fall curve, which is why the whole force model downstream starts from these two numbers.
2. Aero and ride height. Aero forces are computed once, then ride height is derived from the downforce (more downforce pushes the car closer to the floor), and a ground-effect multiplier scales the downforce based on that ride height. This is a feedback loop by construction, more downforce, lower ride, more downforce again, and it is the loop that makes ground-effect cars interesting; below the optimal height the multiplier falls off to model floor stall, and a 10 mm clamp keeps the whole thing from running away.
3. Normal loads. Start from the static front/rear split, add the aero load, then add quasi-static longitudinal and lateral transfer from the lagged accelerations plus the aero pitch moment. Loads are floored at zero so a lifted wheel makes no force.
4. Tyre forces and the friction ellipse. Each tyre's pure-slip `Fx` and `Fy` are scaled by a thermal grip factor, then clamped to an ellipse: `(Fx/Fx_max)^2 + (Fy/Fy_max)^2 <= 1`. Because the longitudinal and lateral peaks differ (`p_dx1 = 1.9`, `p_dy1 = 1.8`), the limit is a genuine ellipse, not a circle. The physical content deserves spelling out. A contact patch makes force through one mechanism, rubber gripping road, and that mechanism does not care which way the force points: ask for pure braking and you can have all of it, ask for pure cornering and you can have all of it, ask for both at once and it is the vector sum that hits the cap. This is why trail braking works at all. As the driver bleeds off the brake toward the apex, longitudinal demand falls, and precisely that much lateral capacity comes free to rotate the car; the trail-braking reflex in the controller below is this ellipse read in reverse. Forces are rotated into the body frame and summed into a longitudinal force, a lateral force, and a yaw moment.
5. Tyre temperatures. One lumped state per tyre. Frictional power heats it, convection cools it toward ambient, and a 150 C ceiling clamp protects against runaway. Temperature feeds back into grip through the thermal factor, a Gaussian centered on the optimal temperature and floored at half grip. The window that Gaussian draws is the same one an entire qualifying out-lap is choreographed around: the fronts heat mostly from braking and steering work, the rears from traction, so they warm at different rates, and the driver's job on that lap is to have all four arrive inside the window at the exact moment the flying lap starts, without pushing any of them through the top of it first. Miss low and the tyre is numb, sliding before it grips; miss high and the surface goes greasy and the lap is dead before sector one ends. In the model the same trade runs continuously: every demand the controller makes feeds heat into the state, the state feeds grip back, and a lap that overworks its tyres early pays for it with less grip late. That trade is why a fast out-lap can cost the flying lap that follows it, and why the temperature window is managed for a whole session rather than a corner.
6. ERS. Under braking, energy is harvested from the braking force the rear tyres actually transmit, at a fixed efficiency, so a locked or unloaded wheel regenerates nothing. When deploy is requested, stored energy is converted to a boost torque on the rear wheels at the deploy efficiency, capped by the MGU-K power limit and the remaining charge. The deploy power follows the 2026 speed taper: full below 290 km/h, falling linearly to zero by 355 km/h, so high-speed deployment is limited the way the rules require.

Drive torque comes from an engine torque curve, flat torque capped by power, multiplied by the current gear ratio. An eight-speed box shifts on rpm thresholds with hysteresis, and the hysteresis is there for a failure you can picture: a car holding nearly constant speed through a long corner sits with its rpm right at a shift threshold, and without a dead band the box upshifts, the rpm drops below the downshift point, the box downshifts, the rpm rises again, and the driveline hunts back and forth every few substeps, jolting the rear tyres with each swap exactly when they are already at their cornering limit. Separating the up and down thresholds costs nothing and makes the state machine boring, which is what a gearbox should be. A rev limiter cuts torque at the top, and the current gear's tractive capacity is exposed on the state so the controller can modulate against the force actually available.

The rear axle has a limited-slip differential: a viscous term proportional to the left-right speed difference plus a Coulomb preload that saturates linearly inside a small speed-difference band, which keeps the torque from chattering sign at every substep when the axle is locked. Engine torque through the gear, ERS boost, brake torque (front/rear biased), and the reaction torque from longitudinal tyre force all sum onto each wheel before the explicit Euler update.

`update_batch_state` turns the summed body forces into accelerations, including the `v x yaw_rate` coupling terms that make the planar model behave correctly in a corner, integrates the velocities and yaw rate, then advances world position.

One honest note on ERS. The vehicle model applies a deploy boost only when the input asks for it (`ers_override`). The controller requests it when traction is healthy and charge remains, and the runner narrows those requests to the deploy windows computed by the Python optimizer when a schedule file is present, so the closed-loop lap executes the planned deployment. The allocation strategy itself, the one that decides where the battery buys the most lap time, lives in the QSS predictor on the Python side, described below.

### control/pure_pursuit.hpp

The controller that drives the closed-loop lap. Steering is textbook pure pursuit: pick a lookahead point ahead on the centerline, find the angle to it in the body frame, and steer by `atan2(2 * L * sin(alpha), Ld)`. The command is clamped and rate limited. Pure pursuit over anything smarter is a debuggability decision: when the car misses an apex there is one lookahead point and one angle to look at, and the failure shows up in a plot. A predictive controller would lap faster and explain less, and this loop exists to be understood. The lookahead distance is the controller's entire personality. Too short and the steering chases every kink of the centerline, sawing at the wheel the way a driver does when staring just past the front wing; too long and the controller smooths the path into a chord, clipping apexes it should be driving around. Between those two failure modes sits the tuning, and both of them are visible the moment you plot the driven line over the centerline.

The lookahead grows linearly with speed (`lookahead_min_m + lookahead_gain_s · v`), and linear is not a style choice; it falls out of the geometry if you ask what keeps the correction bounded. The pursuit arc through a target offset `e` at distance `L` has curvature `κ = 2e/L²`, so the lateral acceleration the controller demands to chase that target is `a = v²κ = 2e·v²/L²`. Hold `L` fixed and the demand grows with the square of speed: the same 20 cm error that goes unnoticed at 80 km/h becomes a violent input at 300, which is exactly the sawing failure above. Now substitute `L = k·v` and the v² cancels: `a = 2e/k²`, constant in speed. The linear schedule is the unique power of `v` that makes the controller equally gentle everywhere, and the `min` term exists because at walking pace `k·v` collapses to nothing and the arc degenerates.

Speed comes from a short backward pass over the next 300 m. Segment curvatures set corner-speed ceilings from the grip budget including downforce:

```
m * v^2 * kappa  =  mu * (m * g + 0.5 * rho * Cl * A * v^2 * ge(v))
```

with `mu` taken from the same calibrated load-sensitive tyre model the QSS uses and `ge(v)` the same speed-based ground-effect sigmoid the QSS uses. The planner and the QSS agree; the plant does not, and that is a defect rather than a design. `batch_vehicle.cpp` derives its downforce multiplier from ride height instead, which makes it non-monotonic in speed and pins it at 0.75 above roughly 48 m/s, so at 90 m/s the planner is steering to a grip level 2.4 times what the physics delivers. It is written up in [KNOWN-ISSUES.md](KNOWN-ISSUES.md) with the numbers, and the closed-loop deficit discussed later in this document should not be read as a controller result until the two are unified. Braking limits then propagate backward through the segments with a friction-ellipse reduction wherever braking overlaps cornering, and braking capacity follows the active aero mode the car is currently in. A grip margin keeps targets off the absolute limit, because the absolute limit is not a lap anybody finishes. Ask for every last percent in one corner and the car arrives at the next one unsettled, so the tenth gained on entry comes back with interest over the two corners it takes to recover; a lap at 98% everywhere beats a lap at 101% somewhere, and the margin is that arithmetic written down. Which corners will tolerate less of it depends on what follows them, which is not something worth guessing, so it is a per-position table optimized offline by `lap_optimizer`, which runs a pattern search on the margin knots against the full simulator, no surrogate model and no gradients, the physics itself scoring every candidate. Pattern search rather than coordinate descent, and the distinction is not pedantry: each move perturbs three adjacent knots as a triangular hat rather than one axis at a time, so the search directions are a fixed basis that is not the coordinate axes, the mesh never refines, and the acceptance test is a hard clean-lap predicate. None of the convergence theory that attaches to coordinate descent applies here. What it is, accurately, is a budget-limited direct search with no guarantee, and only accepts laps that are both faster and clean, with a global scalar as fallback when no schedule file is present. On top of the proportional throttle and brake tracking sit driver reflexes, each one a correction a driver makes without thinking, written here as a control law:

- a yaw-rate damper that countersteers when the car rotates more than the commanded steering should produce,
- a sideslip guard that lifts both pedals in a slide (a stiff, high-downforce single-seater does not break away progressively the way a heavy GT car does; it snaps, and the window to catch it is small),
- a slip-based traction cut and a slip-based brake release,
- trail braking shaped by the remaining friction-ellipse capacity,
- a grip budget that follows tyre temperature,
- and a throttle ceiling set by what the friction ellipse leaves over, converted through the current gear's tractive capacity.

### sim/batch_simulator.hpp

The conductor. It owns the config, the state, the track, and the lap timer. Before each step it sets the aero mode from the precomputed X-mode zones (the sustained straights found at track load), so low-drag mode engages only on real straights, not on every short low-curvature window. After stepping the vehicle it projects the new position back onto the track and updates timing.

Lap detection watches the arc length. When it jumps backward by more than half the track length while the car is moving, that is a lap boundary (the standard wrap-around test), so the lap counter ticks and the best lap updates. Sectors come from the labels in the track file, with forward-cross detection so a car wiggling across a boundary does not log a false split; a split that fires twice is the kind of off-by-one that poisons every downstream comparison, so it gets its own guard. There is also a small testing-only path that drives arc length directly so the timing logic can be unit tested without running the full physics.

## Two lap-time paths

There are two different ways the project produces a lap time, and they answer different questions.

- Closed-loop forward simulation (C++). `telemetry_runner` puts the pure pursuit controller in the loop and integrates the full vehicle model around the lap. This is the honest dynamic path: it has to actually balance the car. Out of the box, with the default global grip margin, it completes clean flying laps roughly 20% off the real lap; the offline per-corner margin search narrows that. Closing the rest is controller work, not physics work.
- Quasi-steady-state prediction (Python, `scripts/qss_laptime.py`). This treats the lap as a sequence of points, builds a speed envelope from the grip limit, then runs a forward pass for power-limited acceleration and a backward pass for braking; every point ends up capped by the tightest constraint reachable from it in either direction, the same shape as any two-pass prefix/suffix sweep.

  It is worth walking that argument rather than asserting the result, because the reason two passes are enough is the whole trick. Take the braking direction first. The claim is that after one backward sweep, every point carries a speed the car can still shed in time for everything ahead of it. Induct from the end of the lap backwards. The last point is capped by its own grip limit and there is nothing after it to brake for, which is the base case. Now suppose point i+1 already carries a speed that is safe for the whole remainder. Point i is then bounded by two things at once: its own grip ceiling, and whatever speed can decelerate to `v[i+1]` across the segment, which from `v² = u² + 2as` is `sqrt(v[i+1]² + 2·a_brake·ds)`. Taking the smaller of the two gives a point that is safe for the remainder, which is the inductive step, and the induction closes. With `a_brake = F_BRAKE/M = 38,000/768 = 49.5 m/s²` over a 5 m segment, that second term allows one point to sit at most 22.2 m/s above the next, which is the concrete shape of the constraint.
  
  Note what the induction does not give. It only ever looks one segment ahead, so a single sweep suffices and there is no fixpoint to iterate toward: the pass is O(n) and exactly O(n), not O(n) per iteration. It also says nothing about whether the car can *reach* those speeds, because braking capacity and engine capacity are different constraints. That is what the forward pass supplies, by the mirror-image induction from the start line using drive force instead of brake force. The final envelope is the pointwise minimum of the two, and the minimum is the right combiner rather than an approximation: each pass produces an upper bound on a feasible set, a speed is achievable only if it satisfies both bounds, and the intersection of two upper-bounded sets is bounded by the smaller bound at every point. A dynamic-programming pass (`scripts/ers_dp.py`) then manages the battery over position, speed and stored energy, recharging under braking with the same rear-axle MGU-K model the C++ side uses and deploying where it buys the most time, with the older fixed-budget longest-zones heuristic kept as its baseline. It is fast and it is where the energy strategy lives, but it assumes the car is always exactly on the limit.

  The cost of that DP is worth writing down, because it is what fixes the grid. The table is O(n · n_v · n_e) with two actions evaluated at every cell. The figures this section used to quote were taken from the resampled 5 m line, but `ers_dp.py` reads the raw telemetry, which at Suzuka is **n = 699** points and not 1,159. With speeds from 4 m/s to V_CAP in 0.5 m/s steps (n_v = 177) and charge in 50 kJ steps across a 4 MJ store (n_e = 81), the real cost is **20.0 million transitions and a policy table of 10.0 MB**. Comfortable on a laptop either way, which is the only reason the state gets to stay three-dimensional.

The justification for the grid resolution was wrong, and in the interesting direction, so it is worth correcting rather than restating. The claim was that 0.5 m/s sits well below the speed difference one segment of deployment makes and 50 kJ below what one 5 m segment draws at full power. Both reverse in the regime where deployment actually happens. One segment of full deploy moves the speed by 0.57 m/s at 60 m/s but only **0.12 m/s at 90 m/s**, a quarter of a cell; and a 5 m segment at 350 kW draws 1.75 MJ divided by speed, which is **19 kJ at 90 m/s**, under half a cell. Both axes are therefore *coarser* than one decision, not finer, which is the opposite of what was claimed. The grid is defensible on cost grounds; it was not defensible on the grounds given.

There is a larger point behind that. Energy here is a single scalar resource constraint, which is exactly the shape that Lagrangian relaxation dissolves: price the energy at λ, solve a two-dimensional DP over position and speed, and bisect λ until the terminal charge comes out right. The whole 81-deep energy axis disappears. That is worth doing and it is on the January list, because it removes a dimension rather than tuning one.

  The two envelope passes are cheap by comparison, O(n) each on the same n, and the corner-speed fixed point inside them is 40 damped iterations at a blend of 0.5, converging linearly. That is a constant factor on a small number and it vanishes next to the telemetry download that feeds it, which is the honest reason none of this needed optimising.

The QSS number is the lap-time tool. The closed-loop run is a stability demonstrator for the dynamic model, and the distance between what it achieves and the QSS prediction measures the controller, not the physics.

## Data flow

```
fastf1_loader.py        pull a session from FastF1        -> data/telemetry/<race>.csv
telemetry_to_inputs.py  resample to throttle/brake/steer  -> data/telemetry/<race>_inputs.csv
centerline.csv          track geometry with sectors

         inputs + track
                |
                v
        telemetry_runner (C++)   closed-loop lap
                |
                v
        data/sim_results/<race>_sim.csv     per-step state trace

qss_laptime.py          QSS prediction + ERS allocation   -> lap time, envelope plot
ers_dp.py               optimal ERS placement by DP       -> deploy schedule, comparison
calibrate_tire.py       two-parameter tyre fit, holdout   -> calibrated peak parameters
lap_optimizer (C++)     per-corner margin search in-sim   -> margin schedule for the runner
visualize_ghost.py      real vs simulated, side by side   -> ghost animation, plots
make_poster.py          composite summary image           -> contactpatch_poster.png
```

## File formats

All CSV, comma separated, one header row.

`data/tracks/<track>/centerline.csv`

| column | meaning |
|---|---|
| s_arc | arc length from the start line, meters |
| x, y | centerline position, meters |
| z | unused by the simulator |
| width_left, width_right | track width, unused by the simulator |
| sector | 1, 2, or 3 |

The loader reads arc length, position, and sector. Curvature is always recomputed from the geometry.

`data/telemetry/<race>_inputs.csv`: `time_s, throttle, brake, steering_rad, distance_m, speed_ref_mps`. This is what the C++ runner replays, interpolated in time.

`data/sim_results/<race>_sim.csv`: `time_s, s_arc_m, v_long_mps, x_m, y_m, yaw_rad`, the four tyre temperatures, `battery_soc`, and the four vertical loads. One row per output step.

## Parameters

The defaults in `BatchVehicleConfig` target a 2026 car.

| group | values |
|---|---|
| mass and inertia | 768 kg, yaw inertia 800 kg m^2, wheelbase 3.40 m |
| weight | 45.5% front, CoG height 0.30 m, track 1.55 / 1.50 m |
| wheels | radius 0.35 m, inertia 1.5 kg m^2 |
| drive and brake | 380 N m engine torque to a 400 kW cap, 38 kN brake, 58% front bias |
| gearbox | 8 speeds, overall ratios 13.8 to 4.40, shifts at 11400 / 8200 rpm, limiter 12000 |
| steering | limit 0.40 rad, rate limit 2.5 rad/s |
| differential | viscous 0.5 N m s/rad, Coulomb preload 50 N m |
| tyres | peak long. 1.9, peak lat. 1.8, load sensitivity -0.17, optimal temp 95 C |
| ERS | MGU-K 350 kW, deploy efficiency 0.92, regen efficiency 0.70, battery 4 MJ |

## Testing

The Catch2 suite is split by area: Pacejka forces, aero, the batch vehicle, track projection, lap and sector timing, pure pursuit, integration, and a set of combined-physics checks. The timing tests use the direct arc-length path so they stay fast and deterministic. Tests run through CTest with the same presets as the build.

## Known simplifications

Stated plainly so nobody mistakes the model for more than it is.

- No suspension states. Load transfer is quasi-static, computed from the accelerations and the aero pitch term. There are no springs or dampers, so pitch, heave, and roll do not have their own dynamics.
- Simplified powertrain. The engine is a flat torque curve into a power cap, driven through an eight-speed gearbox with rpm-hysteresis shifts. Shifts are instantaneous; there is no clutch or shift-cut model.
- One-state tyre thermal model, not a multi-layer carcass model.
- Closed-loop ERS deployment follows the precomputed DP schedule, gated by traction and charge safety. Without a schedule file it falls back to a heuristic gate.
- The controller follows a geometric line with a grip margin, so the line is not a true minimum-time trajectory.
- Dry track, single car, no tyre wear over a stint.
