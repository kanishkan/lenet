# Makefile for host and TCE build
# Optionally, you can test the code on host with `make test`

# Host dependency
HOST_CC = gcc

# TCE flags
TCE_CC = tcecc
TCC_FLAGS = -O3 --bubblefish2-scheduler

ADF_FILE=base_tta.adf
SYMBOL_NAMES=predicted_number,ecc,lcc

HDB_FILES="generate_base32.hdb,generate_rf_iu.hdb,almaif.hdb,asic_130nm_1.5V.hdb"

# Benchmark source
SRC = lenet.c

.PHONY : clean all host tce header test tcesim vhdl

weights.h: ./scripts/generate_header.py weights.npy
	./scripts/generate_header.py

header: weights.h

host: weights.h $(SRC)
	$(HOST_CC) $(SRC) -o lenet -DHOST_DEBUG

lenet.tpef: weights.h $(SRC) $(ADF_FILE)
	$(TCE_CC) $(TCC_FLAGS) -a $(ADF_FILE) \
		-o lenet.tpef $(SRC) -k $(SYMBOL_NAMES)

tce: lenet.tpef

tcesim: lenet.tpef
	@tput setaf 5; echo "Runtime: $$(echo quit | ttasim -a $(ADF_FILE) -p lenet.tpef -e 'run; info proc cycles;' | sed -n 2p) cycles"
	@tput setaf 5; echo "Predicted Number: $$(echo quit | ttasim -a $(ADF_FILE) -p lenet.tpef -e 'run; x /u w predicted_number;' | sed -n 2p)"

energy: lenet.tpef ./scripts/tce_energy_model.py
	echo "$$(echo quit | ttasim -a $(ADF_FILE) -p lenet.tpef -e 'run; info proc stats;')\n" > log.txt
	python3 ./scripts/tce_energy_model.py --adf $(ADF_FILE) --log log.txt

asm: lenet.tpef
	tcedisasm -o lenet.asm $(ADF_FILE) lenet.tpef

vhdl: lenet.tpef
	rm -rf proge-out *.img
	generateprocessor -d onchip -f onchip -e tta_core \
		-g AlmaIFIntegrator -o proge-out \
		--hdb-list $(HDB_FILES) \
		--icd-arg-list="debugger:external" \
		-p lenet.tpef $(ADF_FILE)
	generatebits --verbose -d -w 4 -e tta_core \
		-p lenet.tpef -x proge-out $(ADF_FILE)

all: host tce

clean:
	rm -rf *.tpef lenet weights.h proge-out *.asm *.img *.dot log.txt *.trace* *.S

