# Static recompilation of Fervour: the program (gen/runimage), its
# modules (gen/fervourmode, aehmodule, soundmaster, joystick), from gen_c.py via
# ../tools/images.py, and game.c, linked with libroger (the RISC OS runtime).
ROGER   ?= $(HOME)/stuff/libroger
CC      ?= gcc
CFLAGS  ?= -O2 -g -w -fno-strict-aliasing $(if $(TRACE),-DRECOMP_TRACE)
GEN     := $(wildcard gen/*/code*.c) $(wildcard gen/*/entries.c)
OBJ     := $(GEN:.c=.o) game.o
LIBS    := $(shell pkg-config --libs sdl3) -lm -lpthread
INC     := -I$(ROGER)/include

fervour: $(OBJ) $(ROGER)/libroger.a
	$(CC) $(CFLAGS) -o $@ $(OBJ) $(ROGER)/libroger.a $(LIBS)

$(ROGER)/libroger.a: FORCE
	$(MAKE) -C $(ROGER) libroger.a

gen/%.o: gen/%.c $(ROGER)/include/roger_cpu.h
	$(CC) $(CFLAGS) $(INC) -c -o $@ $<

game.o: game.c gen/modules.inc $(ROGER)/include/roger.h
	$(CC) $(CFLAGS) $(INC) -c -o $@ $<

# Coverage build (~/stuff/superspider/phase0): "make cov" builds fervour-cov
# from separate *.cov.o objects; it writes $$RECOMP_COV (default cov.out).
COVDIR  ?= $(HOME)/stuff/superspider/phase0/cov
COVOBJ  := $(OBJ:.o=.cov.o) cov.cov.o

cov: fervour-cov

fervour-cov: $(COVOBJ) FORCE
	$(MAKE) -C $(ROGER) cov COV=$(COVDIR)
	$(CC) $(CFLAGS) -o $@ $(COVOBJ) $(ROGER)/libroger-cov.a $(LIBS)

%.cov.o: %.c $(ROGER)/include/roger_cpu.h $(COVDIR)/cov.h
	$(CC) $(CFLAGS) -DRECOMP_COV $(INC) -I$(COVDIR) -c -o $@ $<

cov.cov.o: $(COVDIR)/cov.c $(COVDIR)/cov.h
	$(CC) $(CFLAGS) -c -o $@ $<

regen:
	python3 ../tools/images.py unpack analyse gen

# "make roots" merges the gap entries a --trace-gaps run logged
# (untranslated.log, or LOG=...) into ../analysis/<image>.roots, so the next
# "make regen" translates them.
LOG ?= untranslated.log

roots:
	python3 ../tools/images.py roots $(LOG)

clean:
	rm -f gen/*/*.o game.o fervour fervour-cov *.cov.o gen/*/*.cov.o

.PHONY: FORCE cov regen roots clean
