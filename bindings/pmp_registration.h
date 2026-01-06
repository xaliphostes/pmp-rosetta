// ============================================================================
// PMP Library Rosetta Registration
// ============================================================================
// This file registers PMP classes with Rosetta for introspection.
//
// IMPORTANT: For overloaded functions, use FULLY QUALIFIED type names (pmp::)
// because the macro stringifies the type and it must be valid C++ in the
// generated binding file.
// ============================================================================
#pragma once

#include <rosetta/rosetta.h>

// PMP headers - Core
#include <pmp/bounding_box.h>
#include <pmp/surface_mesh.h>
#include <pmp/types.h>

// PMP headers - Algorithms
#include <pmp/algorithms/curvature.h>
#include <pmp/algorithms/decimation.h>
#include <pmp/algorithms/differential_geometry.h>
#include <pmp/algorithms/distance_point_triangle.h>
#include <pmp/algorithms/features.h>
#include <pmp/algorithms/geodesics.h>
#include <pmp/algorithms/hole_filling.h>
#include <pmp/algorithms/normals.h>
#include <pmp/algorithms/parameterization.h>
#include <pmp/algorithms/remeshing.h>
#include <pmp/algorithms/shapes.h>
#include <pmp/algorithms/smoothing.h>
#include <pmp/algorithms/subdivision.h>
#include <pmp/algorithms/triangulation.h>
#include <pmp/algorithms/utilities.h>

// PMP headers - IO
#include <pmp/io/io.h>

// NOTE: Do NOT use "using namespace pmp;" here - we need fully qualified names
// for the overload macros to generate correct code.

// Copy a mesh in C++
inline pmp::SurfaceMesh copy_mesh(const pmp::SurfaceMesh &src) {
    return pmp::SurfaceMesh(src);
}

// Load mesh entirely in C++ (workaround for Python-created mesh issues)
inline void load_mesh(pmp::SurfaceMesh &mesh, const std::filesystem::path &filepath) {
    pmp::read(mesh, filepath);
}

namespace pmp_rosetta {

    inline void register_all() {
        using namespace rosetta::core;
        auto &registry      = Registry::instance();
        auto &func_registry = FunctionRegistry::instance();

        // ========================================================================
        // Handle Types - MUST be registered for methods that return them
        // These are lightweight index wrappers used by SurfaceMesh
        // ========================================================================

        ROSETTA_REGISTER_CLASS(pmp::Vertex).constructor<>();
        ROSETTA_REGISTER_CLASS(pmp::Face).constructor<>();
        ROSETTA_REGISTER_CLASS(pmp::Edge).constructor<>();
        ROSETTA_REGISTER_CLASS(pmp::Halfedge).constructor<>();

        // ========================================================================
        // IO Flags - Used by read/write functions
        // ========================================================================

        ROSETTA_REGISTER_CLASS(pmp::IOFlags)
            .constructor<>()
            .field("use_binary", &pmp::IOFlags::use_binary)
            .field("use_vertex_normals", &pmp::IOFlags::use_vertex_normals)
            .field("use_vertex_colors", &pmp::IOFlags::use_vertex_colors)
            .field("use_vertex_texcoords", &pmp::IOFlags::use_vertex_texcoords)
            .field("use_face_normals", &pmp::IOFlags::use_face_normals)
            .field("use_face_colors", &pmp::IOFlags::use_face_colors);

        // ========================================================================
        // Core Types
        // ========================================================================

        // Point is actually pmp::Matrix<float, 3, 1> - register with alias
        ROSETTA_REGISTER_CLASS(pmp::Point).constructor<>().constructor<float, float, float>();

        // BoundingBox
        ROSETTA_REGISTER_CLASS(pmp::BoundingBox)
            .constructor<>()
            .method("min", &pmp::BoundingBox::min)
            .method("max", &pmp::BoundingBox::max)
            .method("center", &pmp::BoundingBox::center)
            .method("size", &pmp::BoundingBox::size)
            .method("is_empty", &pmp::BoundingBox::is_empty);

        // SurfaceMesh - the main mesh class
        ROSETTA_REGISTER_CLASS(pmp::SurfaceMesh)
            .constructor<>()
            // Topology modification - return handle types
            .method("add_vertex", &pmp::SurfaceMesh::add_vertex)
            .method("add_triangle", &pmp::SurfaceMesh::add_triangle)
            .method("add_quad", &pmp::SurfaceMesh::add_quad)
            // Counts
            .method("n_vertices", &pmp::SurfaceMesh::n_vertices)
            .method("n_edges", &pmp::SurfaceMesh::n_edges)
            .method("n_faces", &pmp::SurfaceMesh::n_faces)
            .method("n_halfedges", &pmp::SurfaceMesh::n_halfedges)
            // Queries
            .method("is_empty", &pmp::SurfaceMesh::is_empty)
            .method("is_triangle_mesh", &pmp::SurfaceMesh::is_triangle_mesh)
            .method("is_quad_mesh", &pmp::SurfaceMesh::is_quad_mesh)
            // Memory management
            .method("clear", &pmp::SurfaceMesh::clear)
            .method("reserve", &pmp::SurfaceMesh::reserve)
            .method("garbage_collection", &pmp::SurfaceMesh::garbage_collection)
            .lambda_method_const<std::vector<pmp::Scalar>>("vertices",
                                                           [](const pmp::SurfaceMesh &self) {
                                                               std::vector<pmp::Scalar> pos;
                                                               pos.reserve(self.n_vertices() * 3);
                                                               for (auto v : self.vertices()) {
                                                                   const pmp::Point &p =
                                                                       self.position(v);
                                                                   pos.push_back(p[0]);
                                                                   pos.push_back(p[1]);
                                                                   pos.push_back(p[2]);
                                                               }
                                                               return pos;
                                                           })
            .lambda_method<std::vector<pmp::IndexType>>("indices",
                                                        [](const pmp::SurfaceMesh &self) {
                                                            std::vector<pmp::IndexType> indices;
                                                            indices.reserve(self.n_faces() * 3);
                                                            for (auto f : self.faces()) {
                                                                for (auto v : self.vertices(f)) {
                                                                    indices.push_back(v.idx());
                                                                }
                                                            }
                                                            return indices;
                                                        });

        // ========================================================================
        // Algorithms - Non-overloaded functions (simple registration)
        // ========================================================================

        // Decimation
        ROSETTA_REGISTER_FUNCTION(pmp::decimate);

        // Smoothing
        ROSETTA_REGISTER_FUNCTION(pmp::explicit_smoothing);
        ROSETTA_REGISTER_FUNCTION(pmp::implicit_smoothing);

        // Remeshing
        ROSETTA_REGISTER_FUNCTION(pmp::uniform_remeshing);
        ROSETTA_REGISTER_FUNCTION(pmp::adaptive_remeshing);

        // Subdivision
        ROSETTA_REGISTER_FUNCTION(pmp::loop_subdivision);
        ROSETTA_REGISTER_FUNCTION(pmp::catmull_clark_subdivision);
        ROSETTA_REGISTER_FUNCTION(pmp::quad_tri_subdivision);

        // Normals
        ROSETTA_REGISTER_FUNCTION(pmp::vertex_normals);
        ROSETTA_REGISTER_FUNCTION(pmp::face_normals);

        // Features
        ROSETTA_REGISTER_FUNCTION(pmp::detect_features);
        ROSETTA_REGISTER_FUNCTION(pmp::clear_features);

        // Hole Filling
        ROSETTA_REGISTER_FUNCTION(pmp::fill_hole);

        // Curvature
        ROSETTA_REGISTER_FUNCTION(pmp::curvature);

        // Shapes (Primitives)
        ROSETTA_REGISTER_FUNCTION(pmp::tetrahedron);
        ROSETTA_REGISTER_FUNCTION(pmp::hexahedron);
        ROSETTA_REGISTER_FUNCTION(pmp::octahedron);
        ROSETTA_REGISTER_FUNCTION(pmp::dodecahedron);
        ROSETTA_REGISTER_FUNCTION(pmp::icosahedron);
        ROSETTA_REGISTER_FUNCTION(pmp::uv_sphere);
        ROSETTA_REGISTER_FUNCTION(pmp::plane);
        ROSETTA_REGISTER_FUNCTION(pmp::cone);
        ROSETTA_REGISTER_FUNCTION(pmp::cylinder);
        ROSETTA_REGISTER_FUNCTION(pmp::torus);

        // Parameterization
        ROSETTA_REGISTER_FUNCTION(pmp::harmonic_parameterization);
        ROSETTA_REGISTER_FUNCTION(pmp::lscm_parameterization);

        // Utilities (non-overloaded)
        ROSETTA_REGISTER_FUNCTION(pmp::bounds);
        ROSETTA_REGISTER_FUNCTION(pmp::surface_area);
        ROSETTA_REGISTER_FUNCTION(pmp::volume);
        ROSETTA_REGISTER_FUNCTION(pmp::flip_faces);

        // ========================================================================
        // Algorithms - OVERLOADED functions
        // IMPORTANT: Use FULLY QUALIFIED types (pmp::) in the function pointer!
        // ========================================================================

        // Triangulation has two overloads:
        //   void triangulate(SurfaceMesh& mesh)
        //   void triangulate(SurfaceMesh& mesh, Face f)
        ROSETTA_REGISTER_OVERLOADED_FUNCTION(pmp::triangulate, void (*)(pmp::SurfaceMesh &));
        ROSETTA_REGISTER_OVERLOADED_FUNCTION_AS(pmp::triangulate, "triangulate_face",
                                                void (*)(pmp::SurfaceMesh &, pmp::Face));

        // Centroid has overloads - register mesh version
        ROSETTA_REGISTER_OVERLOADED_FUNCTION(pmp::centroid,
                                             pmp::Point (*)(const pmp::SurfaceMesh &));

        // ========================================================================
        // IO Functions - OVERLOADED
        // ========================================================================

        // void read(SurfaceMesh& mesh, const std::filesystem::path& file)
        ROSETTA_REGISTER_OVERLOADED_FUNCTION(
            pmp::read, void (*)(pmp::SurfaceMesh &, const std::filesystem::path &));

        // Load mesh entirely in C++ and return it
        ROSETTA_REGISTER_FUNCTION(load_mesh);

        // Copy mesh in C++
        ROSETTA_REGISTER_FUNCTION(copy_mesh);

        // void write(const SurfaceMesh& mesh, const std::filesystem::path& file, const IOFlags&
        // flags)
        ROSETTA_REGISTER_OVERLOADED_FUNCTION(pmp::write, void (*)(const pmp::SurfaceMesh &,
                                                                  const std::filesystem::path &,
                                                                  const pmp::IOFlags &));
    }

} // namespace pmp_rosetta
