# Makefile for host and TCE build
# Optionally, you can test the code on host with `make test`

BENCH = lenet

# Host dependency
HOST_CC = gcc

# TCE flags
TCE_CC = tcecc
TCC_FLAGS = -O3

PROC_DESIGN=base_tta
ADF_FILE=$(PROC_DESIGN).adf
SYMBOL_NAMES=predicted_number,ecc,lcc

# Benchmark source
SRC = $(BENCH).c

.PHONY : clean all host tce header test tcesim vhdl

header: generate_header.py weights.npy
	./generate_header.py

host: header weights.h
	$(HOST_CC) $(SRC) -o lenet -DHOST_DEBUG

$(BENCH).tpef: header weights.h $(SRC) $(ADF_FILE)
	$(TCE_CC) $(TCC_FLAGS) -a $(ADF_FILE) -o $(BENCH).tpef $(SRC) -k $(SYMBOL_NAMES)

tce: $(BENCH).tpef

tcesim: tce
	tput setaf 5; echo "Runtime: $$(echo quit | ttasim -a $(ADF_FILE) -p $(BENCH).tpef -e 'run; info proc cycles;' | sed -n 2p) cycles"

asm: tce
	tcedisasm -o $(BENCH).asm $(ADF_FILE) $(BENCH).tpef

vhdl: tce
	rm -rf proge-out *.img
	generateprocessor -d onchip -f onchip -e tta_core -i $(PROC_DESIGN).idf -g AlmaIFIntegrator -o proge-out -p $(BENCH).tpef $(ADF_FILE)
	generatebits --verbose -d -w 4 -e tta_core -p $(BENCH).tpef -x proge-out $(ADF_FILE)

all: host tce

clean:
	rm -rf *.tpef lenet weights.h proge-out *.asm *.img *.dot

