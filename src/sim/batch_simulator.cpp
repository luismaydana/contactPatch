#include "contactpatch/sim/batch_simulator.hpp"

#include <cmath>

namespace contactpatch {
namespace sim {

namespace {

bool is_forward_sector_cross(int prev_sector, int new_sector){
    return (new_sector == prev_sector + 1) || (prev_sector == 2 && new_sector == 0);
}
}

void BatchSimulator::initialize(const physics::BatchVehicleConfig& config,const physics::BatchVehicleState& initial_state){
    config_ = config;
    state_ = initial_state;
    lap_state_ = LapState{};
    initialized_ = true;
}

bool BatchSimulator::load_track(const std::string& csv_path){
    has_track_ = track_.load_from_csv(csv_path);
    lap_state_ = LapState{};
    if (has_track_) {
        apply_track_projection(false);
        lap_state_.prev_s_arc_m = state_.s_arc_m;
    }
    return has_track_;
}

void BatchSimulator::set_track_points_for_testing(const std::vector<track::CenterlinePoint>& points) {
    track_.set_points_for_testing(points);
    has_track_ = points.size() >= 2;
    lap_state_ = LapState{};
    if (has_track_) {
        lap_state_.prev_s_arc_m = 0.0f;
    }
}

void BatchSimulator::apply_track_projection(bool use_hint) {
    const Real hint = use_hint ? state_.s_arc_m : -1.0f;
    const track::TrackProjection proj = track_.project_to_track(state_.x_m, state_.y_m, hint);
    if(proj.segment_idx <0){return;}
    state_.s_arc_m = proj.s_arc_m;
    state_.lateral_offset_m = proj.lateral_offset_m;
    state_.track_heading_rad = proj.heading_track_rad;
}

void BatchSimulator::record_sector_time(int sector_idx){
    if(sector_idx < 0 ||sector_idx > 2){return;}
    const Real sector_time = lap_state_.sim_time_s - lap_state_.sector_start_time_s;
    lap_state_.last_sector_times_s[sector_idx] = sector_time;
    if (lap_state_.best_sector_times_s[sector_idx] < 0.0f
        || sector_time < lap_state_.best_sector_times_s[sector_idx]) {
        lap_state_.best_sector_times_s[sector_idx] = sector_time;
    }
}

void BatchSimulator::update_lap_timing(Real dt){
    (void)dt;if (!has_track_){return;}

    const Real track_length = track_.get_total_length();
    if (track_length < 1e-3f) {
        return;
    }

    const Real delta_s = state_.s_arc_m - lap_state_.prev_s_arc_m;

    if (state_.v_long_mps > 1.0f && delta_s < -track_length * 0.5f){
        record_sector_time(lap_state_.current_sector_idx);

        lap_state_.last_lap_time_s = lap_state_.current_lap_time_s;
        if (lap_state_.best_lap_time_s < 0.0f
            || lap_state_.current_lap_time_s < lap_state_.best_lap_time_s) {
            lap_state_.best_lap_time_s = lap_state_.current_lap_time_s;
        }

        lap_state_.lap_count += 1;
        lap_state_.current_lap_time_s = 0.0f;
        lap_state_.current_sector_idx = 0;
        lap_state_.sector_start_time_s = lap_state_.sim_time_s;
    } else {
        const int new_sector = track_.get_sector_at(state_.s_arc_m);
        const int prev_sector = lap_state_.current_sector_idx;
        if (new_sector != prev_sector) {
            if (is_forward_sector_cross(prev_sector, new_sector)) {
                record_sector_time(prev_sector);
                lap_state_.sector_start_time_s = lap_state_.sim_time_s;
            }
            lap_state_.current_sector_idx = new_sector;
        }
    }

    lap_state_.prev_s_arc_m = state_.s_arc_m;
}

void BatchSimulator::simulate_s_arc_for_testing(Real s_arc_m, Real dt, Real v_long_mps){
    if (!has_track_) {
        return;
    }
    lap_state_.sim_time_s += dt;
    lap_state_.current_lap_time_s += dt;

    state_.s_arc_m = s_arc_m;
    state_.v_long_mps = v_long_mps;

    update_lap_timing(dt);
}

physics::BatchOutputs BatchSimulator::step(const physics::BatchInputs& inputs, Real dt){
    if (!initialized_){
        initialize(physics::BatchVehicleConfig{}, physics::BatchVehicleState{});
    }

    if (has_track_){
        state_.current_aero_mode = track_.is_x_zone_at(state_.s_arc_m)
            ? physics::AeroMode::X_MODE
            : physics::AeroMode::Z_MODE;
    }

    constexpr Real kMaxSubstep = 0.001f;
    int n_sub = static_cast<int>(std::ceil(dt / kMaxSubstep));
    if(n_sub< 1){
        n_sub = 1;
    }
    const Real sub_dt = dt / static_cast<Real>(n_sub);

    physics::BatchOutputs out{};
    for (int i = 0; i < n_sub; ++i) {
        out = physics::step_batch_vehicle(config_, state_, inputs, sub_dt);
    }
    if (has_track_) {
        apply_track_projection();
        lap_state_.sim_time_s += dt;
        lap_state_.current_lap_time_s += dt;
        update_lap_timing(dt);
    }

    return out;
}
}
}
