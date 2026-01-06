# pmp-rosetta

<p align="center">
  <img src="media/bunny.png"width="700">
</p>

A port of the [**PMP library**](https://github.com/pmp-library/pmp-library) in Python using [**rosetta**](https://github.com/xaliphostes/rosetta).

✨ The **Polygon Mesh Processing** (PMP) Library is a modern C++ open-source library for processing and visualizing polygon surface meshes. It has an efficient and easy-to-use mesh data structure, as well as standard algorithms such as decimation, remeshing, subdivision, or smoothing.

✨ **Rosetta** is a **non-intrusive C++ header-only introspection library** that is used to automatically generates consistent bindings for Python, JavaScript, Lua, Ruby, Julia and more — without modifying your C++ code.
Describe your introspection once, and export them everywhere. You do not need to know anything about the underlaying libs that are used for the bindings (NAPI, Pybind11, Rice...)

Soon (and still using [rosetta](https://github.com/xaliphostes/rosetta)), new bindings will be available in
- **JavaScript**
- **TypeScript**
- **Wasm**
- **REST-API**

without any changes and with the same [*shared rosetta API*](bindings/pmp_registration.h).

## Compile

### 1. Make the custom generator
The standard `binding_generator` executable from `rosetta`  doesn't know about the project's classes. It queries `rosetta::Registry::instance()` at generation time, but the registry is empty because the `register_rosetta_classes()` function is never called.

This custom generator solves the problem by:
1. Including the `pmp_registration.h` (i.e., pmp rosetta registration of the given C++ lib)
2. Calling `pmp_rosetta::register_all()` **before** generating
3. Now the generator finds all the classes and free functions.
   
From the root project
```sh
mkdir build && cd build
cmake ..
make
```

### 2. Generate the binding(s) using the generator
From the root project
```sh
./pmp_generator project.json
```

### 3. Compile each binding

#### a. For Python:

##### Setup venv and install modules
Go toi the `generated/python` folder.

Then create a virtual env:
```sh
python2.14 -m venv venv214
source ./venv214/bin/activate

# Install the necessary python modules for the GUI later one
pip install pyvista pyvistaqt pyqt5 numpy
```

##### Compile the python PMP lib
Still from the python folder,
```sh
pip install .
```

### 4. Testing
Still from the python folder,
```sh
python ../../remesh_viewer.py
```

## 📜 License

[MIT](LICENSE) License

## 💡 Credits

[Xaliphostes](https://github.com/xaliphostes) (fmaerten@gmail.com)
