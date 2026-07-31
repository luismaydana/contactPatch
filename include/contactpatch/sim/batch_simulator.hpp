#pragma once

#include "contactpatch/core/types.hpp"
#include "contactpatch/physics/batch_vehicle.hpp"
#include "contactpatch/track/centerline_track.hpp"

namespace contactpatch {
namespace sim {

struct LapState {
    Real sim_time_s = 0.0f;
    Real current_lap_time_s = 0.0f;
    Real last_lap_time_s = 0.0f;
    Real best_lap_time_s = -1.0f;
    int lap_count = 0;
    int current_sector_idx = 0;
    Real sector_start_time_s = 0.0f;
    Real last_sector_times_s[3] = {0.0f, 0.0f, 0.0f};
    Real best_sector_times_s[3] = {-1.0f, -1.0f, -1.0f};
    Real prev_s_arc_m = 0.0f;
};

class BatchSimulator {
public:
    void initialize(const physics::BatchVehicleConfig& config, const physics::BatchVehicleState& initial_state);
    bool load_track(const std::string& csv_path);
    void set_track_points_for_testing(const std::vector<track::CenterlinePoint>& points);
    physics::BatchOutputs step(const physics::BatchInputs& inputs, Real dt = FIXED_DT);

    const physics::BatchVehicleState& get_state() const { return state_; }
    const track::CenterlineTrack& get_track() const { return track_; }
    const LapState& lap_state() const { return lap_state_; }
    bool has_track() const { return has_track_; }

    void simulate_s_arc_for_testing(Real s_arc_m, Real dt, Real v_long_mps = 15.0f);

private:
    void apply_track_projection(bool use_hint = true);
    void update_lap_timing(Real dt);
    void record_sector_time(int sector_idx);

    static constexpr Real FIXED_DT = 0.001f;
    physics::BatchVehicleConfig config_{};
    physics::BatchVehicleState state_{};
    track::CenterlineTrack track_{};
    LapState lap_state_{};
    bool initialized_ = false;
    bool has_track_ = false;
};

}
}
