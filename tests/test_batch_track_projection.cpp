#include <cmath>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "contactpatch/track/centerline_track.hpp"

using namespace contactpatch;
using namespace contactpatch::track;

static CenterlineTrack make_straight_track() {
    CenterlineTrack track{};
    std::vector<CenterlinePoint> points;
    points.reserve(11);
    for (int i = 0; i <= 10; ++i) {
        CenterlinePoint p{};
        p.s_arc_m = static_cast<Real>(i * 10.0f);
        p.x_m = static_cast<Real>(i * 10.0f);
        p.y_m = 0.0f;
        p.curvature = 0.0f;
        points.push_back(p);
    }
    track.set_points_for_testing(points);
    return track;
}

TEST_CASE("project_to_track on straight line", "[batch_track][projection]") {
    const CenterlineTrack track = make_straight_track();

    const TrackProjection left = track.project_to_track(50.0f, 0.5f);
    REQUIRE(left.segment_idx >= 0);
    REQUIRE(left.s_arc_m == Catch::Approx(50.0f).margin(0.5f));
    REQUIRE(left.lateral_offset_m == Catch::Approx(0.5f).margin(0.05f));
    REQUIRE(left.heading_track_rad == Catch::Approx(0.0f).margin(0.05f));

    const TrackProjection right = track.project_to_track(50.0f, -0.5f);
    REQUIRE(right.segment_idx >= 0);
    REQUIRE(right.s_arc_m == Catch::Approx(50.0f).margin(0.5f));
    REQUIRE(right.lateral_offset_m == Catch::Approx(-0.5f).margin(0.05f));
}

TEST_CASE("project_to_track loads Suzuka centerline", "[batch_track][projection]") {
    CenterlineTrack track{};
    const std::string csv = std::string(CONTACTPATCH_DATA_DIR) + "/tracks/suzuka/centerline.csv";
    REQUIRE(track.load_from_csv(csv));

    const auto& pts = track.points();
    REQUIRE(pts.size() > 2);

    const TrackProjection at_start = track.project_to_track(pts.front().x_m, pts.front().y_m);
    REQUIRE(at_start.segment_idx >= 0);
    REQUIRE(at_start.s_arc_m == Catch::Approx(0.0f).margin(5.0f));
    REQUIRE(at_start.lateral_offset_m == Catch::Approx(0.0f).margin(0.5f));

    const CenterlinePoint& p0 = pts.front();
    const CenterlinePoint& p1 = pts[1];
    const Real dx = p1.x_m - p0.x_m;
    const Real dy = p1.y_m - p0.y_m;
    const Real len = std::sqrt(dx * dx + dy * dy);
    const Real tx = dx / len;
    const Real ty = dy / len;
    const Real left_x = p0.x_m - ty * 1.0f;
    const Real left_y = p0.y_m + tx * 1.0f;

    const TrackProjection offset_left = track.project_to_track(left_x, left_y);
    REQUIRE(offset_left.lateral_offset_m == Catch::Approx(1.0f).margin(0.15f));
}
