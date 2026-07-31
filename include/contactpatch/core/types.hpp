#pragma once

#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>

namespace contactpatch{

using Real = float;
using usize = std::size_t;
using u32 = std::uint32_t;
using u64 = std::uint64_t;
using i32 = std::int32_t;
using i64 = std::int64_t;

class Vec3 {
public:
    Vec3() : x_(0.0f), y_(0.0f), z_(0.0f) {}
    Vec3(Real x, Real y, Real z) : x_(x), y_(y), z_(z) {}

    Real GetX() const{return x_;}
    Real GetY() const{return y_;}
    Real GetZ() const{return z_;}

    void SetX(Real x){ x_ = x; }
    void SetY(Real y){y_ = y; }
    void SetZ(Real z){z_ = z; }

    Real LengthSq()const { return x_ * x_ + y_ * y_ + z_ * z_;}
    Real Length()const { return std::sqrt(LengthSq());}

    Real Dot(const Vec3& o) const { return x_ * o.x_ + y_ * o.y_ + z_ * o.z_; }

    Vec3 Cross(const Vec3& o)const{
        return Vec3(y_ * o.z_ - z_ * o.y_,z_ * o.x_ - x_ * o.z_,x_ * o.y_ - y_ * o.x_);
    }

    Vec3 Normalized() const {
        const Real len = Length();
        if (len < 1e-12f) return Vec3(0.0f, 0.0f, 0.0f);
        const Real inv = 1.0f / len;
        return Vec3(x_ * inv, y_ * inv, z_ * inv);
    }

    Vec3 operator+(const Vec3& o) const { return Vec3(x_ + o.x_, y_ + o.y_, z_ + o.z_); }
    Vec3 operator-(const Vec3& o) const { return Vec3(x_ - o.x_, y_ - o.y_, z_ - o.z_); }
    Vec3 operator-() const { return Vec3(-x_, -y_, -z_); }
    Vec3 operator*(Real s) const { return Vec3(x_ * s, y_ * s, z_ * s); }

    Vec3& operator+=(const Vec3& o) { x_ += o.x_; y_ += o.y_; z_ += o.z_; return *this; }
    Vec3& operator-=(const Vec3& o) { x_ -= o.x_; y_ -= o.y_; z_ -= o.z_; return *this; }

private:
    Real x_;
    Real y_;
    Real z_;
};

inline Vec3 operator*(Real s, const Vec3& v) { return v * s; }

enum class Wheel : u32 { FL = 0, FR = 1, RL = 2, RR = 3, COUNT = 4 };

template <class T>
using PerWheel = std::array<T, static_cast<usize>(Wheel::COUNT)>;

}
