#!/usr/bin/env python3
"""
PMP Remesh Viewer v2 - Uses PyVista for loading/saving, PMP only for remeshing

This version avoids PMP mesh creation issues by:
- Loading meshes with PyVista's native loader
- Converting to PMP only for remeshing operations
- Saving with PyVista's native writer
"""

import sys
import tempfile
import numpy as np

try:
    import pmp
except ImportError:
    print("Error: pmp module not found. Make sure the bindings are built and installed.")
    sys.exit(1)

try:
    import pyvista as pv
    from pyvistaqt import QtInteractor
except ImportError:
    print("Error: pyvista and pyvistaqt are required.")
    print("Install with: pip install pyvista pyvistaqt")
    sys.exit(1)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QDoubleSpinBox, QFileDialog, QGroupBox,
    QSplitter, QStatusBar, QFrame, QSlider, QMessageBox, QComboBox,
    QCheckBox
)
from PyQt5.QtCore import Qt

# Available color palettes for visualization
COLOR_PALETTES = [
    'viridis', 'plasma', 'inferno', 'magma', 'cividis',
    'coolwarm', 'bwr', 'seismic', 'rainbow', 'jet',
    'turbo', 'gnuplot', 'gnuplot2', 'ocean', 'terrain'
]

# Available attributes for visualization
ATTRIBUTES = [
    'Solid Color',
    'X Coordinate',
    'Y Coordinate',
    'Z Coordinate',
    'Gaussian Curvature',
    'Mean Curvature',
    'Min Curvature',
    'Max Curvature'
]


def pyvista_to_pmp(pv_mesh):
    """Convert a PyVista PolyData to a PMP SurfaceMesh."""
    # Get vertices and faces from PyVista
    vertices = pv_mesh.points
    faces = pv_mesh.faces

    # Create PMP mesh and add vertices
    mesh = pmp.SurfaceMesh()

    # Add all vertices
    pmp_vertices = []
    for v in vertices:
        pmp_v = mesh.add_vertex(pmp.Point(float(v[0]), float(v[1]), float(v[2])))
        pmp_vertices.append(pmp_v)

    # Parse PyVista faces format: [n, v0, v1, ..., vn, n, v0, v1, ..., vn, ...]
    i = 0
    while i < len(faces):
        n = faces[i]  # Number of vertices in this face
        if n == 3:
            mesh.add_triangle(
                pmp_vertices[faces[i + 1]],
                pmp_vertices[faces[i + 2]],
                pmp_vertices[faces[i + 3]]
            )
        elif n == 4:
            mesh.add_quad(
                pmp_vertices[faces[i + 1]],
                pmp_vertices[faces[i + 2]],
                pmp_vertices[faces[i + 3]],
                pmp_vertices[faces[i + 4]]
            )
        i += n + 1

    return mesh


def pmp_to_pyvista(mesh):
    """Convert a PMP SurfaceMesh to a PyVista PolyData."""
    # Get vertices
    verts = mesh.vertices()
    vertices = np.array(verts, dtype=np.float64).reshape(-1, 3)

    # Get faces
    indices = mesh.indices()
    indices_array = np.array(indices, dtype=np.int64).reshape(-1, 3)

    # PyVista face format: [n, v0, v1, v2, n, v0, v1, v2, ...]
    n_faces = len(indices_array)
    faces = np.column_stack([np.full(n_faces, 3), indices_array]).ravel()

    return pv.PolyData(vertices, faces)


class RemeshViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PMP Remesh Viewer v2")
        self.setGeometry(100, 100, 1400, 800)

        self.original_mesh = None  # PyVista mesh
        self.remeshed_mesh = None  # PyVista mesh
        self.current_filepath = None
        self.target_edge_length = 0.02
        self.auto_edge_length = 0.02
        self._syncing_cameras = False  # Flag to prevent recursive sync

        self.setup_ui()
        self.setup_status_bar()
        self.setup_camera_sync()

    def setup_ui(self):
        """Setup the main UI layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # Control panel at the top
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

        # Splitter for the two 3D views
        splitter = QSplitter(Qt.Horizontal)

        # Left view - Original mesh
        left_frame = self.create_view_frame("Original Mesh")
        self.plotter_original = QtInteractor(left_frame)
        left_frame.layout().addWidget(self.plotter_original.interactor)
        splitter.addWidget(left_frame)

        # Right view - Remeshed mesh
        right_frame = self.create_view_frame("Remeshed Mesh")
        self.plotter_remeshed = QtInteractor(right_frame)
        right_frame.layout().addWidget(self.plotter_remeshed.interactor)
        splitter.addWidget(right_frame)

        # Set equal sizes for both views
        splitter.setSizes([700, 700])

        main_layout.addWidget(splitter, stretch=1)

        # Setup plotters
        self.setup_plotters()

    def create_view_frame(self, title):
        """Create a frame with title for a 3D view."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(5, 5, 5, 5)

        label = QLabel(f"<b>{title}</b>")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        return frame

    def create_control_panel(self):
        """Create the control panel with buttons and sliders."""
        group = QGroupBox("Controls")
        main_layout = QVBoxLayout(group)

        # First row: Load, Method, Edge Length, Auto, Remesh, Save
        row1 = QHBoxLayout()

        # Load button
        self.load_btn = QPushButton("Load Mesh")
        self.load_btn.setMinimumWidth(100)
        self.load_btn.clicked.connect(self.load_mesh)
        row1.addWidget(self.load_btn)

        row1.addSpacing(20)

        # Remeshing method selector
        row1.addWidget(QLabel("Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Uniform", "Adaptive"])
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        row1.addWidget(self.method_combo)

        row1.addSpacing(20)

        # Edge length controls (used for uniform, and as "target" for adaptive)
        self.edge_length_label = QLabel("Edge Length:")
        row1.addWidget(self.edge_length_label)

        self.edge_length_slider = QSlider(Qt.Horizontal)
        self.edge_length_slider.setMinimum(1)
        self.edge_length_slider.setMaximum(200)
        self.edge_length_slider.setValue(100)
        self.edge_length_slider.setMinimumWidth(200)
        self.edge_length_slider.valueChanged.connect(self.on_slider_changed)
        row1.addWidget(self.edge_length_slider)

        self.edge_length_spinbox = QDoubleSpinBox()
        self.edge_length_spinbox.setDecimals(4)
        self.edge_length_spinbox.setMinimum(0.0001)
        self.edge_length_spinbox.setMaximum(100.0)
        self.edge_length_spinbox.setSingleStep(0.001)
        self.edge_length_spinbox.setValue(0.02)
        self.edge_length_spinbox.setMinimumWidth(100)
        self.edge_length_spinbox.valueChanged.connect(self.on_spinbox_changed)
        row1.addWidget(self.edge_length_spinbox)

        row1.addSpacing(20)

        # Auto edge length button
        self.auto_btn = QPushButton("Auto")
        self.auto_btn.setToolTip("Compute edge length automatically (2% of bounding box)")
        self.auto_btn.clicked.connect(self.compute_auto_edge_length)
        row1.addWidget(self.auto_btn)

        row1.addSpacing(20)

        # Remesh button
        self.remesh_btn = QPushButton("Remesh")
        self.remesh_btn.setMinimumWidth(100)
        self.remesh_btn.setEnabled(False)
        self.remesh_btn.clicked.connect(self.do_remesh)
        row1.addWidget(self.remesh_btn)

        row1.addSpacing(20)

        # Save button
        self.save_btn = QPushButton("Save Remeshed")
        self.save_btn.setMinimumWidth(100)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.save_mesh)
        row1.addWidget(self.save_btn)

        row1.addStretch()

        # Mesh info labels
        self.original_info = QLabel("Original: -")
        row1.addWidget(self.original_info)

        row1.addSpacing(20)

        self.remeshed_info = QLabel("Remeshed: -")
        row1.addWidget(self.remeshed_info)

        main_layout.addLayout(row1)

        # Second row: Adaptive remeshing parameters (hidden by default)
        self.adaptive_row = QWidget()
        row2 = QHBoxLayout(self.adaptive_row)
        row2.setContentsMargins(0, 0, 0, 0)

        row2.addWidget(QLabel("Min Edge:"))
        self.min_edge_spinbox = QDoubleSpinBox()
        self.min_edge_spinbox.setDecimals(4)
        self.min_edge_spinbox.setMinimum(0.0001)
        self.min_edge_spinbox.setMaximum(100.0)
        self.min_edge_spinbox.setSingleStep(0.001)
        self.min_edge_spinbox.setValue(0.01)
        self.min_edge_spinbox.setMinimumWidth(80)
        row2.addWidget(self.min_edge_spinbox)

        row2.addSpacing(10)

        row2.addWidget(QLabel("Max Edge:"))
        self.max_edge_spinbox = QDoubleSpinBox()
        self.max_edge_spinbox.setDecimals(4)
        self.max_edge_spinbox.setMinimum(0.0001)
        self.max_edge_spinbox.setMaximum(100.0)
        self.max_edge_spinbox.setSingleStep(0.001)
        self.max_edge_spinbox.setValue(0.05)
        self.max_edge_spinbox.setMinimumWidth(80)
        row2.addWidget(self.max_edge_spinbox)

        row2.addSpacing(10)

        row2.addWidget(QLabel("Approx Error:"))
        self.approx_error_spinbox = QDoubleSpinBox()
        self.approx_error_spinbox.setDecimals(4)
        self.approx_error_spinbox.setMinimum(0.0001)
        self.approx_error_spinbox.setMaximum(100.0)
        self.approx_error_spinbox.setSingleStep(0.001)
        self.approx_error_spinbox.setValue(0.005)
        self.approx_error_spinbox.setMinimumWidth(80)
        self.approx_error_spinbox.setToolTip("Maximum geometric deviation from original surface")
        row2.addWidget(self.approx_error_spinbox)

        row2.addStretch()

        main_layout.addWidget(self.adaptive_row)
        self.adaptive_row.setVisible(False)  # Hidden by default

        # Third row: Visualization options
        row3 = QHBoxLayout()

        row3.addWidget(QLabel("Attribute:"))
        self.attribute_combo = QComboBox()
        self.attribute_combo.addItems(ATTRIBUTES)
        self.attribute_combo.setMinimumWidth(150)
        self.attribute_combo.currentIndexChanged.connect(self.on_attribute_changed)
        row3.addWidget(self.attribute_combo)

        row3.addSpacing(20)

        row3.addWidget(QLabel("Palette:"))
        self.palette_combo = QComboBox()
        self.palette_combo.addItems(COLOR_PALETTES)
        self.palette_combo.setMinimumWidth(100)
        self.palette_combo.currentIndexChanged.connect(self.on_palette_changed)
        row3.addWidget(self.palette_combo)

        row3.addSpacing(20)

        self.show_edges_checkbox = QCheckBox("Show Edges")
        self.show_edges_checkbox.setChecked(True)
        self.show_edges_checkbox.stateChanged.connect(self.on_show_edges_changed)
        row3.addWidget(self.show_edges_checkbox)

        row3.addSpacing(20)

        self.show_colorbar_checkbox = QCheckBox("Colorbar")
        self.show_colorbar_checkbox.setChecked(True)
        self.show_colorbar_checkbox.stateChanged.connect(self.on_attribute_changed)
        row3.addWidget(self.show_colorbar_checkbox)

        row3.addStretch()

        main_layout.addLayout(row3)

        return group

    def on_method_changed(self, index):
        """Handle remeshing method change."""
        is_adaptive = index == 1
        self.adaptive_row.setVisible(is_adaptive)
        # Hide uniform controls when adaptive is selected
        self.edge_length_label.setVisible(not is_adaptive)
        self.edge_length_slider.setVisible(not is_adaptive)
        self.edge_length_spinbox.setVisible(not is_adaptive)
        if is_adaptive:
            # Update adaptive parameters based on current auto edge length
            self.min_edge_spinbox.setValue(self.auto_edge_length * 0.5)
            self.max_edge_spinbox.setValue(self.auto_edge_length * 2.0)
            self.approx_error_spinbox.setValue(self.auto_edge_length * 0.25)

    def on_attribute_changed(self, _=None):
        """Handle attribute selection change - update both views."""
        self.update_mesh_display(self.plotter_original, self.original_mesh, 'lightblue')
        self.update_mesh_display(self.plotter_remeshed, self.remeshed_mesh, 'lightgreen')

    def on_palette_changed(self, _=None):
        """Handle palette selection change - update both views."""
        self.update_mesh_display(self.plotter_original, self.original_mesh, 'lightblue')
        self.update_mesh_display(self.plotter_remeshed, self.remeshed_mesh, 'lightgreen')

    def on_show_edges_changed(self, _=None):
        """Handle show edges checkbox change - update both views."""
        self.update_mesh_display(self.plotter_original, self.original_mesh, 'lightblue')
        self.update_mesh_display(self.plotter_remeshed, self.remeshed_mesh, 'lightgreen')

    def compute_scalars(self, mesh, attribute):
        """Compute scalar values for the given attribute."""
        if mesh is None:
            return None

        if attribute == 'Solid Color':
            return None
        elif attribute == 'X Coordinate':
            return mesh.points[:, 0]
        elif attribute == 'Y Coordinate':
            return mesh.points[:, 1]
        elif attribute == 'Z Coordinate':
            return mesh.points[:, 2]
        elif attribute == 'Gaussian Curvature':
            return mesh.curvature(curv_type='gaussian')
        elif attribute == 'Mean Curvature':
            return mesh.curvature(curv_type='mean')
        elif attribute == 'Min Curvature':
            return mesh.curvature(curv_type='minimum')
        elif attribute == 'Max Curvature':
            return mesh.curvature(curv_type='maximum')
        return None

    def update_mesh_display(self, plotter, mesh, default_color):
        """Update mesh display with current visualization settings."""
        if mesh is None:
            return

        # Save camera state
        try:
            cam_pos = plotter.camera.position
            cam_focal = plotter.camera.focal_point
            cam_up = plotter.camera.up
            has_camera = True
        except:
            has_camera = False

        plotter.clear()
        plotter.add_axes()

        attribute = self.attribute_combo.currentText()
        palette = self.palette_combo.currentText()
        show_edges = self.show_edges_checkbox.isChecked()
        show_colorbar = self.show_colorbar_checkbox.isChecked()

        scalars = self.compute_scalars(mesh, attribute)

        if scalars is not None:
            # Display with scalars
            plotter.add_mesh(
                mesh,
                scalars=scalars,
                cmap=palette,
                show_edges=show_edges,
                edge_color='black',
                opacity=1.0,
                scalar_bar_args={'title': attribute} if show_colorbar else None,
                show_scalar_bar=show_colorbar
            )
        else:
            # Display with solid color
            plotter.add_mesh(
                mesh,
                show_edges=show_edges,
                edge_color='black',
                color=default_color,
                opacity=1.0
            )

        # Restore camera state
        if has_camera:
            plotter.camera.position = cam_pos
            plotter.camera.focal_point = cam_focal
            plotter.camera.up = cam_up

        plotter.render()

    def setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - Load a mesh file to begin")

    def setup_plotters(self):
        """Configure the PyVista plotters."""
        for plotter in [self.plotter_original, self.plotter_remeshed]:
            plotter.set_background('white')
            plotter.add_axes()
            plotter.enable_anti_aliasing()

    def setup_camera_sync(self):
        """Setup bidirectional camera synchronization between the two views."""
        def sync_to_remeshed(*args):
            if self._syncing_cameras:
                return
            self._syncing_cameras = True
            try:
                cam = self.plotter_original.camera
                self.plotter_remeshed.camera.position = cam.position
                self.plotter_remeshed.camera.focal_point = cam.focal_point
                self.plotter_remeshed.camera.up = cam.up
                self.plotter_remeshed.render()
            except:
                pass
            finally:
                self._syncing_cameras = False

        def sync_to_original(*args):
            if self._syncing_cameras:
                return
            self._syncing_cameras = True
            try:
                cam = self.plotter_remeshed.camera
                self.plotter_original.camera.position = cam.position
                self.plotter_original.camera.focal_point = cam.focal_point
                self.plotter_original.camera.up = cam.up
                self.plotter_original.render()
            except:
                pass
            finally:
                self._syncing_cameras = False

        # Add observers to sync cameras on interaction
        self.plotter_original.iren.add_observer('InteractionEvent', sync_to_remeshed)
        self.plotter_remeshed.iren.add_observer('InteractionEvent', sync_to_original)

    def on_slider_changed(self, value):
        """Handle slider value change."""
        ratio = value / 100.0
        self.target_edge_length = self.auto_edge_length * ratio

        self.edge_length_spinbox.blockSignals(True)
        self.edge_length_spinbox.setValue(self.target_edge_length)
        self.edge_length_spinbox.blockSignals(False)

    def on_spinbox_changed(self, value):
        """Handle spinbox value change."""
        self.target_edge_length = value

        if self.auto_edge_length > 0:
            ratio = value / self.auto_edge_length
            slider_value = int(ratio * 100)
            slider_value = max(1, min(200, slider_value))

            self.edge_length_slider.blockSignals(True)
            self.edge_length_slider.setValue(slider_value)
            self.edge_length_slider.blockSignals(False)

    def compute_auto_edge_length(self):
        """Compute automatic edge length based on mesh bounding box."""
        if self.original_mesh is None:
            return

        bounds = self.original_mesh.bounds
        diagonal = np.sqrt(
            (bounds[1] - bounds[0])**2 +
            (bounds[3] - bounds[2])**2 +
            (bounds[5] - bounds[4])**2
        )
        self.auto_edge_length = diagonal * 0.02
        self.target_edge_length = self.auto_edge_length

        # Update uniform controls
        self.edge_length_spinbox.setValue(self.auto_edge_length)
        self.edge_length_slider.setValue(100)

        # Update adaptive controls
        self.min_edge_spinbox.setValue(self.auto_edge_length * 0.5)
        self.max_edge_spinbox.setValue(self.auto_edge_length * 2.0)
        self.approx_error_spinbox.setValue(self.auto_edge_length * 0.25)

        self.status_bar.showMessage(f"Auto edge length: {self.auto_edge_length:.4f}")

    def load_mesh(self):
        """Load a mesh file using PyVista."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Mesh File",
            "",
            "Mesh Files (*.obj *.stl *.ply *.vtk *.vtp);;OBJ Files (*.obj);;STL Files (*.stl);;All Files (*)"
        )

        if not filepath:
            return

        try:
            self.status_bar.showMessage(f"Loading: {filepath}")
            QApplication.processEvents()

            # Load with PyVista
            self.original_mesh = pv.read(filepath)
            self.current_filepath = filepath

            if self.original_mesh.n_points == 0:
                raise RuntimeError("Mesh is empty")

            # Triangulate if needed
            if not self.original_mesh.is_all_triangles:
                self.original_mesh = self.original_mesh.triangulate()

            # Compute auto edge length
            self.compute_auto_edge_length()

            # Display using current visualization settings
            self.update_mesh_display(self.plotter_original, self.original_mesh, 'lightblue')
            self.plotter_original.reset_camera()

            # Clear remeshed view
            self.plotter_remeshed.clear()
            self.remeshed_mesh = None

            # Update UI
            self.remesh_btn.setEnabled(True)
            self.save_btn.setEnabled(False)

            # Update info
            self.original_info.setText(
                f"Original: V={self.original_mesh.n_points}, "
                f"F={self.original_mesh.n_faces_strict}"
            )
            self.remeshed_info.setText("Remeshed: -")

            import os
            self.status_bar.showMessage(f"Loaded: {os.path.basename(filepath)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load mesh:\n{str(e)}")
            self.status_bar.showMessage("Error loading mesh")

    def do_remesh(self):
        """Perform remeshing using PMP."""
        if self.original_mesh is None:
            return

        is_adaptive = self.method_combo.currentIndex() == 1

        try:
            if is_adaptive:
                min_edge = self.min_edge_spinbox.value()
                max_edge = self.max_edge_spinbox.value()
                approx_error = self.approx_error_spinbox.value()
                self.status_bar.showMessage(
                    f"Adaptive remeshing (min={min_edge:.4f}, max={max_edge:.4f}, err={approx_error:.4f})..."
                )
            else:
                self.status_bar.showMessage(
                    f"Uniform remeshing with edge length: {self.target_edge_length:.4f}..."
                )
            QApplication.processEvents()

            # Convert PyVista mesh to PMP
            pmp_mesh = pyvista_to_pmp(self.original_mesh)

            # Triangulate if needed
            if not pmp_mesh.is_triangle_mesh():
                pmp.triangulate(pmp_mesh)

            # Apply remeshing based on selected method
            if is_adaptive:
                pmp.adaptive_remeshing(
                    pmp_mesh,
                    self.min_edge_spinbox.value(),   # min_edge_length
                    self.max_edge_spinbox.value(),   # max_edge_length
                    self.approx_error_spinbox.value(),  # approx_error
                    10,   # iterations
                    True  # use projection
                )
            else:
                pmp.uniform_remeshing(
                    pmp_mesh,
                    self.target_edge_length,
                    10,   # iterations
                    True  # use projection
                )
            pmp_mesh.garbage_collection()

            # Convert back to PyVista
            self.remeshed_mesh = pmp_to_pyvista(pmp_mesh)

            # Display using current visualization settings
            self.update_mesh_display(self.plotter_remeshed, self.remeshed_mesh, 'lightgreen')
            self.plotter_remeshed.reset_camera()

            # Sync camera
            self.sync_cameras()

            # Update UI
            self.save_btn.setEnabled(True)

            # Update info
            method_name = "Adaptive" if is_adaptive else "Uniform"
            self.remeshed_info.setText(
                f"Remeshed ({method_name}): V={self.remeshed_mesh.n_points}, "
                f"F={self.remeshed_mesh.n_faces_strict}"
            )

            self.status_bar.showMessage(
                f"{method_name} remeshing complete - "
                f"V: {self.original_mesh.n_points} -> {self.remeshed_mesh.n_points}, "
                f"F: {self.original_mesh.n_faces_strict} -> {self.remeshed_mesh.n_faces_strict}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remesh:\n{str(e)}")
            self.status_bar.showMessage("Error during remeshing")

    def sync_cameras(self):
        """Sync the camera of the remeshed view with the original view."""
        try:
            cam = self.plotter_original.camera
            self.plotter_remeshed.camera.position = cam.position
            self.plotter_remeshed.camera.focal_point = cam.focal_point
            self.plotter_remeshed.camera.up = cam.up
            self.plotter_remeshed.render()
        except:
            pass

    def save_mesh(self):
        """Save the remeshed mesh using PyVista."""
        if self.remeshed_mesh is None:
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Remeshed Mesh",
            "remeshed.obj",
            "OBJ Files (*.obj);;STL Files (*.stl);;PLY Files (*.ply);;VTK Files (*.vtk);;All Files (*)"
        )

        if not filepath:
            return

        try:
            self.remeshed_mesh.save(filepath)
            self.status_bar.showMessage(f"Saved: {filepath}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save mesh:\n{str(e)}")
            self.status_bar.showMessage("Error saving mesh")

    def closeEvent(self, event):
        """Clean up on close."""
        self.plotter_original.close()
        self.plotter_remeshed.close()
        event.accept()


def main():
    pv.set_plot_theme('document')

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = RemeshViewer()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
