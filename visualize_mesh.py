import sys
import pyvista as pv

if len(sys.argv) != 2:
    print(f"Usage: python {sys.argv[0]} <mesh.obj>")
    sys.exit(1)

mesh = pv.read(sys.argv[1])
mesh.plot(show_edges=True, color="white")