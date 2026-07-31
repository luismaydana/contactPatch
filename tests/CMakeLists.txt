include(Catch)

set(TEST_SOURCES
    test_pacejka.cpp
    test_aero.cpp
    test_batch_vehicle.cpp
    test_batch_simulator.cpp
    test_batch_track_projection.cpp
    test_batch_lap_timing.cpp
    test_pure_pursuit.cpp
    test_advanced_physics.cpp
    test_integration.cpp
)

add_executable(contactpatch_tests ${TEST_SOURCES})
target_link_libraries(contactpatch_tests
    PRIVATE
        contactpatch_core
        Catch2::Catch2WithMain
)
target_compile_definitions(contactpatch_tests PRIVATE
    CONTACTPATCH_DATA_DIR="${CMAKE_SOURCE_DIR}/data"
)

catch_discover_tests(contactpatch_tests)
