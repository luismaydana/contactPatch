#include "contactpatch/track/centerline_track.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <sstream>

namespace contactpatch {
namespace track {

namespace{

Real cross_2d(Real ax, Real ay, Real bx, Real by){return ax * by - ay * bx;}

void compute_curvature_from_geometry(std::vector<CenterlinePoint>& pts){
    const usize n = pts.size();
    if (n < 3) {
        for (auto& p : pts) p.curvature = 0.0f;
        return;
    }
    pts.front().curvature = 0.0f;
    pts.back().curvature = 0.0f;
    for (usize i = 1; i + 1 < n; ++i) {
        const Real ax = pts[i - 1].x_m, ay = pts[i - 1].y_m;
        const Real bx = pts[i].x_m, by = pts[i].y_m;
        const Real cx = pts[i + 1].x_m, cy = pts[i + 1].y_m;
        const Real abx = bx - ax, aby = by - ay;
        const Real acx = cx - ax, acy = cy - ay;
        const Real bcx = cx - bx, bcy = cy - by;
        const Real ab = std::sqrt(abx * abx + aby * aby);
        const Real bc = std::sqrt(bcx * bcx + bcy * bcy);
        const Real ca = std::sqrt(acx * acx + acy * acy);
        const Real denom = ab * bc * ca;
        if (denom < 1e-6f) {
            pts[i].curvature = 0.0f;
            continue;
        }
        const Real cross = abx * acy - aby * acx;
        pts[i].curvature = 2.0f * cross / denom;
    }
}

void compute_x_zones(std::vector<CenterlinePoint>& pts){
    const usize n = pts.size();
    for (auto& p : pts) p.in_x_zone = false;
    if (n < 2) return;
    constexpr Real kKappaStraight = 0.003f;
    constexpr Real kMinStraightLen = 250.0f;
    const Real total = pts.back().s_arc_m;
    if (total < kMinStraightLen) return;

    std::vector<char> straight(n);
    bool all_straight = true;
    for (usize i = 0; i < n; ++i) {
        straight[i] = (std::abs(pts[i].curvature) < kKappaStraight) ? 1 : 0;
        if (!straight[i]) all_straight = false;
    }
    if (all_straight) {
        for (auto& p : pts) p.in_x_zone = true;
        return;
    }

    usize anchor = 0;
    while (anchor < n && straight[anchor]) ++anchor;

    usize i = anchor;
    do {
        if (straight[i]) {
            std::vector<usize> run;
            while (straight[i]) {
                run.push_back(i);
                i = (i + 1) % n;
                if (i == anchor) break;
            }
            Real len = 0.0f;
            for (usize k = 0; k + 1 < run.size(); ++k) {
                Real d = pts[run[k + 1]].s_arc_m - pts[run[k]].s_arc_m;
                if (d < 0.0f) d += total;
                len += d;
            }
            if (len >= kMinStraightLen) {
                for (usize j : run) pts[j].in_x_zone = true;
            }
        } else {
            i = (i + 1) % n;
        }
    } while (i != anchor);
}

Real wrap_s_arc(Real s_arc_m, Real track_length_m){
    if (track_length_m < 1e-6f) {
        return 0.0f;
    }
    s_arc_m = std::fmod(s_arc_m, track_length_m);
    if (s_arc_m < 0.0f) {
        s_arc_m += track_length_m;
    }
    return s_arc_m;
}

bool in_forward_arc_span(Real s_start, Real span_m, Real s_point, Real track_length_m){
    if (span_m <= 0.0f || track_length_m < 1e-6f) {
        return false;
    }
    Real delta = s_point - s_start;
    if (delta < 0.0f) {
        delta += track_length_m;
    }
    return delta <= span_m + 1e-4f;
}

struct SegmentCandidate {
    Real dist_sq = 0.0f;
    Real s_arc_m = 0.0f;
    Real lateral_offset_m = 0.0f;
    Real heading_track_rad = 0.0f;
    int segment_idx = -1;
};

bool project_onto_segment(Real x_m,Real y_m,const CenterlinePoint& a,const CenterlinePoint& b,int segment_idx,SegmentCandidate& out){
    const Real dx = b.x_m - a.x_m;
    const Real dy = b.y_m - a.y_m;
    const Real len_sq = dx * dx + dy * dy;
    if (len_sq < 1e-12f) {
        return false;
    }
    const Real ax = x_m - a.x_m;
    const Real ay = y_m - a.y_m;
    const Real t = std::clamp((ax * dx + ay * dy) / len_sq, 0.0f, 1.0f);

    const Real px = a.x_m + t * dx;
    const Real py = a.y_m + t * dy;
    const Real vx = x_m - px;
    const Real vy = y_m - py;

    const Real inv_len = 1.0f / std::sqrt(len_sq);
    const Real tx = dx * inv_len;
    const Real ty = dy * inv_len;

    out.dist_sq = vx * vx + vy * vy;
    out.s_arc_m = a.s_arc_m + t * (b.s_arc_m - a.s_arc_m);
    out.lateral_offset_m = cross_2d(tx, ty, vx, vy);
    out.heading_track_rad = std::atan2(ty, tx);
    out.segment_idx = segment_idx;
    return true;
}

}

bool CenterlineTrack::load_from_csv(const std::string& path){
    points_.clear();

    std::ifstream file(path);
    if (!file.is_open()) return false;

    std::string line;
    bool first = true;
    while (std::getline(file, line)) {
        if (line.empty()) continue;
        if (first) {
            first = false;
            continue;
        }

        std::stringstream ss(line);
        std::string token;
        CenterlinePoint p{};

        if (!std::getline(ss, token, ',')) continue;
        p.s_arc_m = static_cast<Real>(std::stof(token));
        if (!std::getline(ss, token, ',')) continue;
        p.x_m = static_cast<Real>(std::stof(token));
        if (!std::getline(ss, token, ',')) continue;
        p.y_m = static_cast<Real>(std::stof(token));
        if (!std::getline(ss, token, ',')) continue;
        p.curvature = 0.0f;
        if (std::getline(ss, token, ',')) {
            if (std::getline(ss, token, ',')) {
                if (std::getline(ss, token, ',')) {
                    int s = std::atoi(token.c_str()) - 1;
                    if (s < 0) s = 0;
                    if (s > 2) s = 2;
                    p.sector = s;
                }
            }
        }

        points_.push_back(p);
    }

    compute_curvature_from_geometry(points_);
    compute_x_zones(points_);
    return !points_.empty();
}

Real CenterlineTrack::get_curvature_at(Real s_arc_m)const{
    if (points_.empty()) return 0.0f;
    if (s_arc_m <= points_.front().s_arc_m) return points_.front().curvature;
    if (s_arc_m >= points_.back().s_arc_m) return points_.back().curvature;

    for (usize i = 1; i < points_.size(); ++i) {
        if (s_arc_m <= points_[i].s_arc_m) {
            return points_[i - 1].curvature;
        }
    }
    return points_.back().curvature;
}

int CenterlineTrack::get_sector_at(Real s_arc_m)const{
    if (points_.empty()) return 0;
    const Real track_length = get_total_length();
    if (track_length < 1e-6f) return 0;
    Real s = std::fmod(s_arc_m, track_length);
    if (s < 0.0f) s += track_length;
    for (usize i = 0; i < points_.size(); ++i) {
        if (points_[i].s_arc_m >= s) return points_[i].sector;
    }
    return points_.back().sector;
}

Real CenterlineTrack::get_total_length() const {
    if (points_.empty()) return 0.0f;
    return points_.back().s_arc_m;
}

CenterlinePoint CenterlineTrack::sample_at_s(Real s_arc_m) const {
    if(points_.empty()) {
        return {};
    }
    const Real track_length = get_total_length();
    if(track_length < 1e-6f) {
        return points_.front();
    }
    s_arc_m = wrap_s_arc(s_arc_m, track_length);
    if (s_arc_m <= points_.front().s_arc_m) {
        return points_.front();
    }
    if (s_arc_m >= points_.back().s_arc_m) {
        return points_.back();
    }

    for (usize i = 1; i < points_.size(); ++i){
        if (s_arc_m <= points_[i].s_arc_m) {
            const CenterlinePoint& a = points_[i - 1];
            const CenterlinePoint& b = points_[i];
            const Real ds = b.s_arc_m - a.s_arc_m;
            const Real t = (ds > 1e-6f) ? ((s_arc_m - a.s_arc_m) / ds) : 0.0f;

            CenterlinePoint out{};
            out.s_arc_m = s_arc_m;
            out.x_m = a.x_m + t * (b.x_m - a.x_m);
            out.y_m = a.y_m + t * (b.y_m - a.y_m);
            out.curvature = a.curvature + t * (b.curvature - a.curvature);
            return out;
        }
    }

    return points_.back();
}

bool CenterlineTrack::is_x_zone_at(Real s_arc_m) const{
    if (points_.empty()) return false;
    const Real total = get_total_length();
    if (total < 1e-6f) return false;
    Real s = std::fmod(s_arc_m, total);
    if (s < 0.0f) s += total;
    for (usize i = 1; i < points_.size(); ++i) {
        if (s <= points_[i].s_arc_m) return points_[i - 1].in_x_zone;
    }
    return points_.back().in_x_zone;
}

Real CenterlineTrack::max_curvature_in_range(Real s_start, Real span_m) const{
    if (points_.empty()) {
        return 0.0f;
    }
    const Real track_length = get_total_length();
    if (track_length < 1e-6f || span_m <= 0.0f) {
        return 0.0f;
    }

    s_start = wrap_s_arc(s_start, track_length);

    Real max_kappa = 0.0f;
    for (const CenterlinePoint& p : points_) {
        if (in_forward_arc_span(s_start, span_m, p.s_arc_m, track_length)) {
            max_kappa = std::max(max_kappa, std::abs(p.curvature));
        }
    }
    return max_kappa;
}

TrackProjection CenterlineTrack::project_to_track(Real x_m, Real y_m, Real s_hint_m, Real window_m) const{
    TrackProjection out{};
    if (points_.size() < 2) {
        return out;
    }
    const Real track_length = get_total_length();
    const bool use_window = (s_hint_m >= 0.0f) && (track_length > 1e-6f) && (window_m > 0.0f);

    const auto arc_dist = [track_length](Real a, Real b)-> Real{
        const Real d = std::abs(a - b);
        return std::min(d, track_length - d);
    };

    usize closest = 0;
    Real min_vertex_sq = -1.0f;
    for (usize i = 0; i < points_.size(); ++i) {
        if (use_window && arc_dist(points_[i].s_arc_m, s_hint_m) > window_m) {
            continue;
        }
        const Real dist_sq = (points_[i].x_m - x_m) * (points_[i].x_m - x_m)
                           + (points_[i].y_m - y_m) * (points_[i].y_m - y_m);
        if (min_vertex_sq < 0.0f || dist_sq < min_vertex_sq) {
            min_vertex_sq = dist_sq;
            closest = i;
        }
    }
    if (min_vertex_sq < 0.0f){
        return project_to_track(x_m, y_m);
    }

    SegmentCandidate best{};
    best.dist_sq = min_vertex_sq;
    best.s_arc_m = points_[closest].s_arc_m;
    best.segment_idx = static_cast<int>(closest);

    if (closest + 1 < points_.size()) {
        const Real dx = points_[closest + 1].x_m - points_[closest].x_m;
        const Real dy = points_[closest + 1].y_m - points_[closest].y_m;
        const Real len = std::sqrt(dx * dx + dy * dy);
        if (len > 1e-6f) {
            const Real tx = dx / len;
            const Real ty = dy / len;
            const Real vx = x_m - points_[closest].x_m;
            const Real vy = y_m - points_[closest].y_m;
            best.lateral_offset_m = cross_2d(tx, ty, vx, vy);
            best.heading_track_rad = std::atan2(ty, tx);
        }
    } else if (closest > 0) {
        const Real dx = points_[closest].x_m - points_[closest - 1].x_m;
        const Real dy = points_[closest].y_m - points_[closest - 1].y_m;
        const Real len = std::sqrt(dx * dx + dy * dy);
        if (len > 1e-6f) {
            const Real tx = dx / len;
            const Real ty = dy / len;
            const Real vx = x_m - points_[closest].x_m;
            const Real vy = y_m - points_[closest].y_m;
            best.lateral_offset_m = cross_2d(tx, ty, vx, vy);
            best.heading_track_rad = std::atan2(ty, tx);
        }
    }

    if (closest > 0) {
        SegmentCandidate candidate{};
        if (project_onto_segment(x_m,y_m,points_[closest - 1],points_[closest],static_cast<int>(closest - 1),candidate)&& candidate.dist_sq < best.dist_sq){
            best = candidate;
        }
    }

    if (closest + 1 < points_.size()){
        SegmentCandidate candidate{};
        if (project_onto_segment(x_m,y_m,points_[closest],points_[closest + 1],static_cast<int>(closest),candidate)&& candidate.dist_sq < best.dist_sq){
            best = candidate;
        }
    }

    out.s_arc_m = best.s_arc_m;
    out.lateral_offset_m = best.lateral_offset_m;
    out.heading_track_rad = best.heading_track_rad;
    out.segment_idx = best.segment_idx;
    return out;
}
}
}
