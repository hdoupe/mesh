# c-mesh

How to build `kernel.c`
----------------------------

1. Install `czmq` and `cJSON`
  - Install `czmq` using the [zeromq instructions][].
    - Mac users can use `brew install czmq`
  - Install `cJSON` from source using the [cJSON instructions][].
    - `cmake` is required. `cmake` instructions can be found at the [cmake install page][].
      - Mac users can use `brew install cmake`
    - ```bash
      # brew install cmake
      git clone https://github.com/DaveGamble/cJSON
      cd cJSON
      mkdir build
      cd build
      cmake ..
      make install
      ```
2. Go to the `cmesh` directory and compile `kernel.c`:
    ```
    gcc -c kernel.c -o kernel.o -g
    ```
3. Move that to the directory containing the Fortran or C file that needs to be linked to the `kernel.o` object and run:
    ```
    gfortran kernel.o taxsim9.for -o cmeshkernel -lczmq -lzmq -lcjson -g
    ```
4. Start the server:
    ```
    ./cmeshkernel
    ```

Concrete examples coming soon...
--------------------------------


[zeromq instructions]: http://zeromq.org/area:download
[cJSON instructions]: https://github.com/DaveGamble/cJSON#building
[cmake install page]: https://cmake.org/install/