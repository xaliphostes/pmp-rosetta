# ============================================================================
# CMakeLists.txt for PMP Library Binding Generator using Rosetta
# ============================================================================
# This file downloads and builds the PMP library, then creates a binding
# generator executable that uses Rosetta for introspection.
#
# Usage:
#   mkdir build && cd build
#   cmake ..
#   make
#   ./pmp_generator project.json
# ============================================================================

cmake_minimum_required(VERSION 3.16)
project(pmp_binding_generator VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# ============================================================================
# Options
# ============================================================================
option(PMP_BUILD_VIS "Build PMP visualization module (requires OpenGL)" OFF)
option(PMP_BUILD_EXAMPLES "Build PMP examples" OFF)
option(PMP_BUILD_TESTS "Build PMP tests" OFF)
option(PMP_BUILD_DOCS "Build PMP documentation" OFF)

# ============================================================================
# Paths - adjust these to your structure
# ============================================================================
message("${CMAKE_CURRENT_SOURCE_DIR}")
set(ROSETTA_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../rosetta/include")
set(BINDING_GENERATOR_DIR "${CMAKE_CURRENT_SOURCE_DIR}/generator")

# ============================================================================
# FetchContent for dependencies
# ============================================================================
include(FetchContent)

# ----------------------------------------------------------------------------
# PMP Library
# ----------------------------------------------------------------------------
message(STATUS "Fetching PMP library...")
FetchContent_Declare(
    pmp
    GIT_REPOSITORY https://github.com/pmp-library/pmp-library.git
    GIT_TAG        main  # Or specify a version tag like "3.0.0"
    GIT_SHALLOW    TRUE
)

# Set PMP options before making it available
set(PMP_BUILD_VIS ${PMP_BUILD_VIS} CACHE BOOL "" FORCE)
set(PMP_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(PMP_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(PMP_BUILD_DOCS OFF CACHE BOOL "" FORCE)

FetchContent_MakeAvailable(pmp)

# Get the PMP source directory for include paths
FetchContent_GetProperties(pmp SOURCE_DIR PMP_SOURCE_DIR)
message(STATUS "PMP source directory: ${PMP_SOURCE_DIR}")

# ----------------------------------------------------------------------------
# nlohmann_json (for configuration parsing)
# ----------------------------------------------------------------------------
find_package(nlohmann_json 3.9 QUIET)
if(NOT nlohmann_json_FOUND)
    message(STATUS "Fetching nlohmann_json...")
    FetchContent_Declare(
        nlohmann_json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG        v3.11.3
        GIT_SHALLOW    TRUE
    )
    FetchContent_MakeAvailable(nlohmann_json)
endif()

# ============================================================================
# Generator executable
# ============================================================================
add_executable(pmp_generator
    main.cxx
    # Add your Rosetta registration files here:
    # bindings/pmp_registration.cxx
)

# Place the executable in a convenient location
set_target_properties(pmp_generator PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/.."
)

# Include directories
target_include_directories(pmp_generator PRIVATE
    # Rosetta
    ${ROSETTA_INCLUDE_DIR}
    
    # Binding generator
    ${BINDING_GENERATOR_DIR}
    
    # PMP library headers
    ${PMP_SOURCE_DIR}/src
    
    # Local bindings directory
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/bindings
)

# Link libraries
target_link_libraries(pmp_generator PRIVATE
    pmp                              # PMP core library
    nlohmann_json::nlohmann_json     # JSON parsing
)

# If visualization is enabled, link pmp_vis as well
if(PMP_BUILD_VIS)
    target_link_libraries(pmp_generator PRIVATE pmp_vis)
endif()

# ============================================================================
# Print configuration summary
# ============================================================================
message(STATUS "")
message(STATUS "============================================================")
message(STATUS "PMP Binding Generator Configuration")
message(STATUS "============================================================")
message(STATUS "  PMP source:           ${PMP_SOURCE_DIR}")
message(STATUS "  Rosetta include:      ${ROSETTA_INCLUDE_DIR}")
message(STATUS "  Generator dir:        ${BINDING_GENERATOR_DIR}")
message(STATUS "  Build visualization:  ${PMP_BUILD_VIS}")
message(STATUS "============================================================")
message(STATUS "")

message(STATUS "  1. Build: cmake --build .")
message(STATUS "  2. Run: ./pmp_generator project.json")