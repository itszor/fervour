/* Run a self-unpacking program with libroger's ARM2 interpreter until
 * control first arrives at an address, then save memory.
 *
 *   unpack FILE --stop=ADDR --dump=FROM:TO --write=OUT [--entry=ADDR] [--limit=N]
 *
 * FILE is loaded at &8000 and entered at --entry (default &8000). The run
 * is headless and nothing is translated: every instruction is interpreted,
 * with 26-bit PC/PSR semantics (Fervour's !Loader decrypts itself with
 * `eor rX, rX, pc`, which reads the flags too). When control reaches the
 * stop address (after at least one instruction has run), [FROM, TO) is
 * written to OUT and the registers are printed.
 *
 * Used by unpack.sh: Acorn squeeze stubs end with `mov pc, r8` into the
 * decoded image at &8000. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <roger.h>

static uint8_t nocode[0x80000 / 32];
static struct roger_image image = {0x8000, 0x8000 + 0x80000, NULL, 0, nocode, 'P'};

static uint32_t stop = ~0u, from, to;
static const char *out;

static int arg(const char *a)
{
    if (!strncmp(a, "--stop=", 7)) { stop = strtoul(a + 7, 0, 16); return 1; }
    if (!strncmp(a, "--dump=", 7)) {
        char *e;
        from = strtoul(a + 7, &e, 16);
        to = strtoul(e + 1, 0, 16);
        return 1;
    }
    if (!strncmp(a, "--write=", 8)) { out = a + 8; return 1; }
    return 0;
}

static int stop_hook(uint32_t a)
{
    if (a != stop || !icount) return 0;
    FILE *f = fopen(out, "wb");
    if (!f) { perror(out); exit(1); }
    fwrite(MEM + from, 1, to - from, f);
    fclose(f);
    printf("stopped at %08x after %llu instructions; wrote %08x-%08x to %s\n", a,
           (unsigned long long)icount, from, to, out);
    for (int k = 0; k < 15; k++) printf("R%d=%08x%s", k, R[k], k % 5 == 4 ? "\n" : " ");
    exit(0);
}

static struct roger_config config = {
    .title = "unpack",
    .image = &image,
    .appdir = ".",
    .initial_mode = 12,
    .wimpslot = 640 * 1024,
    .interpret_gaps = 1,
    .arg = arg,
    .call_addr = stop_hook,
    .usage = "  --stop=ADDR --dump=FROM:TO --write=FILE   (hex addresses)\n",
};

int main(int argc, char **argv)
{
    for (int k = 1; k < argc; k++) {
        if (!strncmp(argv[k], "--entry=", 8)) { config.entry = strtoul(argv[k] + 8, 0, 16); argv[k] = "--headless"; }
        else if (argv[k][0] != '-') {                   /* the file: the (empty) image's extent */
            struct stat st;
            if (!stat(argv[k], &st) && st.st_size <= (long)sizeof nocode * 32) image.end = 0x8000 + st.st_size;
        }
    }
    roger_main(argc, argv, &config);
}
