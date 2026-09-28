cmake_minimum_required(VERSION 3.16)
project(fedbpp_health C)

add_library(fedbpp_health STATIC fedbpp_health.c)
target_include_directories(fedbpp_health PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}")
target_compile_features(fedbpp_health PUBLIC c_std_11)

if (BUILD_TESTING)
    include(CTest)
    add_executable(fedbpp_health_smoke test_fedbpp_health.c)
    target_link_libraries(fedbpp_health_smoke PRIVATE fedbpp_health)
    add_test(NAME fedbpp_health_smoke COMMAND fedbpp_health_smoke)
endif()
