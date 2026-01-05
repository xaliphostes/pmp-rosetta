# pmp-rosetta

A port of the [PMP library](https://github.com/pmp-library/pmp-library) in Python using [rosetta](https://github.com/xaliphostes/rosetta).

Soon (still using [rosetta](https://github.com/xaliphostes/rosetta)), binding in
- **JavaScript**
- **TypeScript**
- **Wasm**
- **REST-API**

without any changes and with the same [*shared rosetta API*](bindings/pmp_registration.h).

## Compile

### 1. Make the generator executable
From the root project
```sh
mkdir build && cd build
cmake ..
make
```

### 2. Generate the binding(s)
From the root project
```sh
./pmp_generator project.json
```

### 3. Compile each binding

#### For Python:
```sh
cd generated
mkdir build && cd build
cmake ..
make
```
or (after creating a venv with activation)
```sh
pip install .
```

### 4. Testing the Python binding

#### From the build directory
```sh
cp ../../../example.py .
python3.14 example.py # because I used Python version 3.14 to generate the lib
```

#### Or from anywhere if using `pip install .`
From the root project
```sh
python3.14 example.py
```

## 📜 License

[MIT](LICENSE) License

## 💡 Credits

[Xaliphostes](https://github.com/xaliphostes) (fmaerten@gmail.com)
