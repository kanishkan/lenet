# Makefile for host and TCE build
# Optionally, you can test the code on host with `make test`

BENCH = lenet

# Host dependency
HOST_CC = gcc

# TCE flags
TCE_CC = tcecc
TCC_FLAGS = -O3 --bubblefish2-scheduler

PROC_DESIGN=base_tta
ADF_FILE=$(PROC_DESIGN).adf
SYMBOL_NAMES=predicted_number,ecc,lcc

HDB_FILES="generate_base32.hdb,generate_rf_iu.hdb,almaif.hdb,asic_130nm_1.5V.hdb"

# Benchmark source
SRC = $(BENCH).c

.PHONY : clean all host tce header test tcesim vhdl

header: generate_header.py weights.npy
	./generate_header.py

host: header weights.h
	$(HOST_CC) $(SRC) -o lenet -DHOST_DEBUG

$(BENCH).tpef: header weights.h $(SRC) $(ADF_FILE)
	$(TCE_CC) $(TCC_FLAGS) -a $(ADF_FILE) \
		-o $(BENCH).tpef $(SRC) -k $(SYMBOL_NAMES)

tce: $(BENCH).tpef

tcesim: tce
	tput setaf 5; echo "Runtime: $$(echo quit | ttasim -a $(ADF_FILE) -p $(BENCH).tpef -e 'run; info proc cycles;' | sed -n 2p) cycles"

energy: tce
	echo "$(echo quit | ttasim -a $(ADF_FILE) -p $(BENCH).tpef -e 'run; info proc stats;')\n" >> log.txt
	python3 tce_energy_model.py --adf $(ADF_FILE) --log log.txt

asm: tce
	tcedisasm -o $(BENCH).asm $(ADF_FILE) $(BENCH).tpef

vhdl: tce
	rm -rf proge-out *.img
	generateprocessor -d onchip -f onchip -e tta_core \
		-g AlmaIFIntegrator -o proge-out \
		--hdb-list $(HDB_FILES) \
		--icd-arg-list="debugger:external" \
		-p $(BENCH).tpef $(ADF_FILE)
	generatebits --verbose -d -w 4 -e tta_core \
		-p $(BENCH).tpef -x proge-out $(ADF_FILE)

all: host tce

clean:
	rm -rf *.tpef lenet weights.h proge-out *.asm *.img *.dot

