#pragma once

#include "contactpatch/core/types.hpp"

#include <string>
#include <vector>

namespace contactpatch {
namespace track {

struct CenterlinePoint {
    Real s_arc_m = 0.0f;
    Real x_m = 0.0f;
    Real y_m = 0.0f;
    Real curvature = 0.0f;
    int sector = 0;
    bool in_x_zone = false;
};

struct TrackProjection {
    Real s_arc_m = 0.0f;
    Real lateral_offset_m = 0.0f;
    Real heading_track_rad = 0.0f;
    int segment_idx = -1;
};

class CenterlineTrack {
public:
    bool load_from_csv(const std::string& path);
    Real get_curvature_at(Real s_arc_m) const;
    Real get_total_length() const;
    int get_sector_at(Real s_arc_m) const;
    const std::vector<CenterlinePoint>& points() const { return points_; }

    TrackProjection project_to_track(
        Real x_m, Real y_m, Real s_hint_m = -1.0f, Real window_m = 60.0f) const;

    CenterlinePoint sample_at_s(Real s_arc_m) const;
    Real max_curvature_in_range(Real s_start, Real span_m) const;
    bool is_x_zone_at(Real s_arc_m) const;

    void set_points_for_testing(const std::vector<CenterlinePoint>& points) { points_ = points; }

private:
    std::vector<CenterlinePoint> points_;
};

}
}
