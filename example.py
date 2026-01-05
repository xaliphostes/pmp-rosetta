#!/usr/bin/env python3
"""
PMP Python Bindings - Mesh Loading and Remeshing Example

This script demonstrates:
1. Loading an OBJ or STL mesh file
2. Applying uniform remeshing
3. Saving the result

Usage:
    python test_remesh.py input.obj output.obj
    python test_remesh.py input.stl output.stl
    python test_remesh.py  # Uses a generated test mesh
"""

import sys
import os

try:
    import pmp
except ImportError:
    print("Error: pmp module not found. Make sure the bindings are built and installed.")
    print("Try: pip install . (from the build directory)")
    sys.exit(1)


def print_mesh_info(mesh, label="Mesh"):
    """Print basic mesh statistics."""
    print(f"{label}:")
    print(f"  Vertices:  {mesh.n_vertices()}")
    print(f"  Edges:     {mesh.n_edges()}")
    print(f"  Faces:     {mesh.n_faces()}")
    print(f"  Triangles: {mesh.is_triangle_mesh()}")
    
    # Compute some metrics
    # bbox = pmp.bounds(mesh)
    # area = pmp.surface_area(mesh)
    
    # print(f"  Surface area: {area:.4f}")
    # print(f"  Bounding box: {bbox.min()} to {bbox.max()}")
    print()


def create_test_mesh():
    """Create a test mesh (subdivided icosahedron) if no input file is provided."""
    print("Creating test mesh (subdivided icosahedron)...")
    mesh = pmp.icosahedron()
    
    # Subdivide a few times to get more vertices
    pmp.loop_subdivision(mesh)
    pmp.loop_subdivision(mesh)
    
    return mesh


def load_mesh(filepath):
    """Load a mesh from file (OBJ, STL, OFF, etc.)."""
    print(f"Loading mesh from: {filepath}")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    mesh = pmp.SurfaceMesh()
    pmp.read(mesh, filepath)
    
    if mesh.is_empty():
        raise RuntimeError(f"Failed to load mesh or mesh is empty: {filepath}")
    
    return mesh


def save_mesh(mesh, filepath):
    """Save a mesh to file."""
    print(f"Saving mesh to: {filepath}")
    
    flags = pmp.IOFlags()
    flags.use_binary = filepath.lower().endswith('.stl')
    
    pmp.write(mesh, filepath, flags)
    print(f"  Saved successfully!")


def remesh(mesh, target_edge_length=None):
    """
    Apply uniform remeshing to the mesh.
    
    Args:
        mesh: The input SurfaceMesh (modified in place)
        target_edge_length: Target edge length. If None, computed automatically.
    """
    # Ensure the mesh is triangulated
    if not mesh.is_triangle_mesh():
        print("Triangulating mesh...")
        pmp.triangulate(mesh)
    
    # Compute target edge length if not specified
    if target_edge_length is None:
        bbox = pmp.bounds(mesh)
        bbox_size = bbox.size()

        # print(bbox, bbox_size)

        # Use ~1% of the bounding box diagonal as target edge length
        diagonal = bbox_size
        target_edge_length = diagonal * 0.02
        print(f"  Auto-computed target edge length: {target_edge_length:.4f}")
    
    print(f"Applying uniform remeshing (target edge length: {target_edge_length:.4f})...")
    
    # Uniform remeshing parameters:
    # - target_edge_length: desired edge length
    # - n_iterations: number of remeshing iterations (default ~10)
    # - use_projection: project vertices back to original surface
    pmp.uniform_remeshing(mesh, target_edge_length, 10, True)
    
    # Clean up
    mesh.garbage_collection()


def main():
    print("=" * 60)
    print("PMP Mesh Remeshing Example")
    print("=" * 60)
    print()
    
    # Parse command line arguments
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        mesh = load_mesh(input_file)
    elif len(sys.argv) == 2:
        input_file = sys.argv[1]
        output_file = "remeshed_" + os.path.basename(input_file)
        mesh = load_mesh(input_file)
    else:
        # # No arguments - create a test mesh
        # input_file = None
        # output_file = "remeshed_test.obj"
        # mesh = create_test_mesh()
        print("no argument provided")
        exit()
    
    print()
    print_mesh_info(mesh, "Input mesh")
    
    # Apply remeshing
    remesh(mesh)
    
    print()
    print_mesh_info(mesh, "Remeshed mesh")
    
    # Save result
    save_mesh(mesh, output_file)
    
    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()