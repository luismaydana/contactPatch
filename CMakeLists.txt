cmake_minimum_required(VERSION 3.25)

project(contactpatch
    VERSION 0.3.0
    DESCRIPTION "Deterministic F1 batch vehicle dynamics simulator"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

if(MSVC)
    string(APPEND CMAKE_CXX_FLAGS " /EHsc")
endif()

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
    set(CMAKE_BUILD_TYPE RelWithDebInfo)
endif()

add_library(contactpatch_warnings INTERFACE)
if(MSVC)
    target_compile_options(contactpatch_warnings INTERFACE
        /W4 /permissive- /EHsc /Zc:__cplusplus /Zc:preprocessor /utf-8 /fp:precise
    )
    target_compile_definitions(contactpatch_warnings INTERFACE
        _CRT_SECURE_NO_WARNINGS NOMINMAX
    )
else()
    target_compile_options(contactpatch_warnings INTERFACE
        -Wall -Wextra -Wpedantic -Wshadow -Wcast-align
        -Wdouble-promotion -ffp-contract=off
    )
endif()

include(FetchContent)
set(FETCHCONTENT_QUIET OFF)

FetchContent_Declare(Catch2
    GIT_REPOSITORY https://github.com/catchorg/Catch2.git
    GIT_TAG        v3.5.4
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(Catch2)
list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)

add_library(contactpatch_core STATIC
    src/physics/tire_pacejka.cpp
    src/physics/aero.cpp
    src/physics/batch_vehicle.cpp
    src/control/pure_pursuit.cpp
    src/track/centerline_track.cpp
    src/sim/batch_simulator.cpp
)
target_include_directories(contactpatch_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
target_link_libraries(contactpatch_core
    PUBLIC contactpatch_warnings
)

add_executable(telemetry_runner apps/telemetry_runner.cpp)
target_link_libraries(telemetry_runner PRIVATE contactpatch_core)
target_compile_definitions(telemetry_runner PRIVATE
    CONTACTPATCH_DATA_DIR="${CMAKE_SOURCE_DIR}/data"
)

add_executable(lap_optimizer apps/lap_optimizer.cpp)
target_link_libraries(lap_optimizer PRIVATE contactpatch_core)
target_compile_definitions(lap_optimizer PRIVATE
    CONTACTPATCH_DATA_DIR="${CMAKE_SOURCE_DIR}/data"
)

enable_testing()
add_subdirectory(tests)
