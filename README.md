# lenet
5LIM0 - Lab assignment

## Folder structure
* `lenet.c` - LeNet C code
* `weights.npy` - Network weights in numpy format
* `test_data` - Input data to the network (`png` images)
* `generate_header.py` - Script to convert numpy weights and input image to header file `weights.h`. 
    * Useful, if you like to contorl the memory layout of input and weights.
* `base_tta.adf` - TTA reference design
* `Makefile` - Build system
    * `make header` - Builds `weights.h` header using `generate_header.py` script
    * `make host` - Builds binary for your host. Useful for testing.
    * `make tce` - Compiles C-code to TTA program (`tpef` format)
    * `make tcesim` - Compiles and run the program on TCE simulator (`tcesim`) and returns runtime.
    * `make vhdl` - Generates program and data memory image for the TTA processor. (Note: You should select implementation for the processor before using this command)
    
## Example flow

```bash
git clone https://github.com/kanishkan/lenet.git
cd lenet

# Compile and run the code on TCE simulator
make tcesim

$ Runtime: xxx cycles
```
