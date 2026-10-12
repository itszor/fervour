/* Fervour (Steven Hodgson / A.E. Hersee, 1992): what libroger needs to
 * know about the game, and the desktop it is started from.
 *
 * !Fervour.!Run only opens the Levels directory: the game is started by
 * running a level set (Levels.!Beginner &c.), whose !Run runs !Run2 with
 * the level set's directory as its argument. !Run2: WimpSlot 160K,
 * ColourTrans (RISC OS 2 only), !Loader (a "loading" window), the Joystick
 * (DummyJoy unless there is one), FervourMode, AEHModule and SoundMaster
 * modules, WimpSlot 448K, then !RUNimage <level set>. !Runimage is a Wimp
 * task (see ../README.md); the modules are loaded first here, as !Run2
 * leaves them (gen/modules.inc). */
#define _GNU_SOURCE                                /* strcasestr */
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <stdio.h>
#include <roger.h>

extern const struct roger_image recomp_image;      /* gen/runimage (gen_c.py) */
#include "gen/modules.inc"                          /* FervourMode, AEHModule, SoundMaster, Joystick */

#define APPDIR "../extracted/!Fervour"

static const char *const prefixes[] = {"<Fervour$Dir>.", "<Obey$Dir>.", NULL};
/* !Run sets Fervour$Dir and FLevels$Dir (the directory of level sets);
 * filenames are relative to APPDIR once the prefixes above are stripped */
static const char *const variables[] = {"Fervour$Dir", "", "FLevels$Dir", "Levels", NULL};

/* --levels=NAME: the level set run (a directory in Levels: Beginner,
 * General, Fast, Puzzles, BlankLev) */
static char command_line[256] = "!RUNimage Levels.!Beginner";

static int arg(const char *a)
{
    if (strncmp(a, "--levels=", 9)) return 0;
    const char *n = a + 9 + (a[9] == '!');
    snprintf(command_line, sizeof command_line, "!RUNimage Levels.!%s", n);
    return 1;
}

/* The Levels directory, which !Fervour.!Run opens (with OPENDIR, a utility
 * that does *Filer_OpenDir) as does Select on the Fervour icon: on the
 * desktop (--desktop), a directory viewer of the level sets */
static int cli_hook(uint32_t n, int x)
{
    (void)x;
    if (n != 0x05) return 0;                        /* OS_CLI */
    char s[256];
    int l = 0;
    while (l < 255 && MEM[R[0] + l] >= 32) { s[l] = MEM[R[0] + l]; l++; }
    s[l] = 0;
    const char *p = strcasestr(s, ".OPENDIR ");
    if (!p) return 0;
    roger_log("OS_CLI", "s", s, l);
    roger_filer_open(p + 9);
    return 1;
}

/* A level set double-clicked in the viewer: on RISC OS its !Run would start
 * another Fervour; here it goes to this one, as dragging it to the level
 * set's icon bar icon does - which loads it */
static void filer_run(const char *name)
{
    const char *leaf = strrchr(name, '.');
    if (leaf && leaf[1] == '!' && roger_filer_load(name, -2, 0)) return;
    fprintf(stderr, "fervour: not run: %s\n", name);
}

/* What !Loader leaves for !Runimage, which quits at once without it: the
 * number variable FLoader$Task, the real-time clock in units of 2^16
 * centiseconds (bytes 2-4 of OS_Word 14's five) when the loader started -
 * !Runimage accepts that time or the one before. (!Loader itself is a
 * Wimp task showing a "loading" window while !Run2 goes on; it isn't run.) */
static void init(void)
{
    uint32_t r[16];
    memcpy(r, R, sizeof r);
    uint32_t blk = roger_scratch("");
    MEM[blk] = 3;                                   /* OS_Word 14,3: read the clock */
    R[0] = 14; R[1] = blk;
    roger_swi(0x07);
    uint32_t t = MEM[blk + 2] | MEM[blk + 3] << 8 | MEM[blk + 4] << 16;
    uint32_t name = blk + 16, value = blk + 32;
    memcpy(MEM + name, "FLoader$Task", 13);
    MEM[value] = t; MEM[value + 1] = t >> 8; MEM[value + 2] = t >> 16; MEM[value + 3] = 0;
    R[0] = name; R[1] = value; R[2] = 4; R[3] = 0; R[4] = 1;   /* OS_SetVarVal, a number */
    roger_swi(0x24);
    memcpy(R, r, sizeof r);
    roger_filer_open("<FLevels$Dir>");              /* (!Run's OPENDIR) */
}

/* The desktop: !Runimage puts two icons on the icon bar - the level set
 * (icon 0, on the right: Select plays it) and the application (icon 1, on
 * the left: Select opens the Levels directory, Menu its menu). Click the
 * level set's icon to play; back on the icon bar, quit. */
static void wimp_idle(void)
{
    static int step;
    switch (step++) {
    case 0:
        roger_wimp_click(-2, 0, 4);
        break;
    default:
        roger_wimp_quit();
    }
}

/* Headless runs (--limit): Space on the title page (start), Space again
 * when the level has been introduced (play), then the cursor keys. Key
 * numbers are INKEY's: Space 99, cursor left 26, right 122, up 58, down
 * 42. */
static const struct roger_key keys[] = {
    {99, 3000000, 4000000}, {99, 8000000, 9000000}, {99, 14000000, 15000000},
    {58, 18000000, 26000000}, {26, 20000000, 21000000}, {122, 23000000, 24000000},
};

/* Code SuperSpider doesn't reach, interpreted (any other untranslated
 * address stops the run, or with --trace-gaps is logged and interpreted):
 * where the game returns to after restoring a stack pointer it saved with
 * the stack itself unknown (&2B078), the initial target of a jump vector
 * the game re-points (&3A620: ldr pc,[r0] at &3A56C), and a stretch of the
 * unrolled sprite plotter it enters past a word it patches (&5098C). */
static const uint32_t interpreted[] = {
    0x2B078, 0x2B0D4, 0x3A620, 0x3A664, 0x5098C, 0x509A0, 0, 0,
};

static struct roger_config config = {
    .title = "Fervour (recompiled)",
    /* a controller: Z X steer (the Options file's keys), A and start Space */
    .pad_map = "left=Z,right=X,a=Space,start=Space",
    .image_path = "../unpacked/RunImage",       /* unsqueezed and decrypted: ../tools/images.py */
    .image = &recomp_image,
    .entry = 0x8064,                            /* where the decryption leaves it */
    .modules = modules,
    .command_line = command_line,
    .appdir = APPDIR,
    .dir_prefixes = prefixes,
    .variables = variables,
    .initial_mode = 12,                         /* the desktop's */
    /* Started with fire, the game steers by the mouse: each frame it reads
     * the pointer, steers (at one rate) towards the side of x=732 it's on,
     * then puts it back 11 OS units nearer 732 - so a movement steers for
     * a while after it (&3A574-&3A5DC). The host mouse is captured while
     * it does, and scaled down: an Archimedes mouse gave about 85 OS units
     * a centimetre, a modern one ten times the pixels (--mouse-sens=N) */
    .relative_mouse = 1,
    .mouse_sens = 0.25f,
    .wimpslot = 448 * 1024,                     /* !Run2's */
    .init = init,
    .wimp_idle = wimp_idle,
    .interpreted = interpreted,
    .keys = keys,
    .nkeys = sizeof keys / sizeof keys[0],
    .arg = arg,
    .swi = cli_hook,
    .filer_run = filer_run,
    .usage = "  --levels=NAME     level set (Beginner, General, Fast, Puzzles, BlankLev)\n",
};

int main(int argc, char **argv) { roger_main(argc, argv, &config); }
