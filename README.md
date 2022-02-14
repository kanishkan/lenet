# LeNet Implementation on Embedded ASIP
5LIM0 - Lab3 assignment

## Folder structure
* `lenet.c` - LeNet C code
* `base_tta.adf` - TTA reference design
* `weights.npy` - Network weights in numpy format
* `test_data` - Input data to the network (`png` images)
* `Makefile` - Build system
    * `make header` - Builds `weights.h` header using `generate_header.py` script
    * `make host` - Builds binary for your host. Useful for testing.
    * `make tce` - Compiles C-code to TTA program (`tpef` format)
    * `make tcesim` - Compiles and run the program on TCE simulator (`ttasim`) and returns runtime.
    * `make energy` - Reports energy numbers for the design (energy per FU and instructions)
    * `make vhdl` - Generates program and data memory image for the TTA processor. (Note: You should select implementation for the processor before using this command)
* `scripts\`
    * `generate_header.py` - Script to convert numpy weights and input image to header file `weights.h`. 
        * Useful, if you like to contorl the memory layout of input and weights.
    * `tce_energy_model.py` - Script for analytical energy model
    * `setup.sh` - Shell script to update the TCE tools
    * `scripts/compare_results.sh` - Regression test that compares the simulator result to expected results
* `examples` - Some TTA design examples for your reference
* `examples/fpga/pynq_notebook.ipynb` - Notebook for programming and testing your design on Pynq

## Example flow

```bash
git clone https://github.com/kanishkan/lenet.git
cd lenet

# Compile and run the code on TCE simulator
make tcesim

$ Runtime: xxx cycles
```
