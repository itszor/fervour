Fervour (A.E. Hersee / Clares, 1992) - static recompilation
===========================================================

Disc image: `Fervour (19xx)(-)[b].adf` (flagged a bad dump; the game runs).
The disc holds an ArcFS archive, `Fervour`, with !Fervour (the game),
!ARV, !MaxMem, !MonType, the joystick utilities and ArcFS's read-only
filing system.

A recipe: this repository holds no game data. It rebuilds the game from
your own copy, recognised by content (recipe.json):

    ./build.sh "Fervour (19xx)(-).zip"      (the TOSEC zip, or the .adf in it)
    cd recomp && ./fervour

build.sh runs recipe.json's steps with SuperSpider's tools/weave.py
(~/stuff/superspider, or $SUPERSPIDER; $SS below): it extracts the disc to
extracted/disc, then the steps below. Needs python3, OCaml/dune, gcc and
SDL3.

    tools/images.py extract    the ArcFS archive on the disc -> extracted/
                               ($SS/tools/arcfs.py)
    tools/images.py unpack     the packed programs -> unpacked/ (tools/unpack)
    tools/images.py analyse    SuperSpider (~/stuff/superspider) on each image
    tools/images.py gen        superspider gen -> recomp/gen/
    recomp/                    make regen (unpack, analyse, gen), make, ./fervour
    tools/events.py            the event log with its strings decoded
    tools/screen.py            screen banks of a headless run as PNGs

Running
-------

    cd recomp && make && ./fervour [--levels=NAME] [--no-sound] [--scale=N] [--fullscreen]
    ./fervour --levels=General     a level set: Beginner (the default), General, Fast, Puzzles, BlankLev
    ./fervour --trace-gaps         interpret untranslated code instead of stopping, logging it
    ./fervour --limit=N            headless, deterministic: Space (start), Space (play), cursor keys

Keys (the title page): Space or fire to start, P password, L start at
level 1, I instructions, D or F12 back to the desktop. A level starts with
its message; Space again to play. Steering: the cursor keys.

What runs
---------

!Fervour.!Run only opens the Levels directory; a level set's !Run runs
!Run2 with its directory: WimpSlot 160K, ColourTrans (RISC OS 2 only),
!Loader, the Joystick module (DummyJoy when there is none), FervourMode,
AEHModule, SoundMaster, WimpSlot 448K, then !RUNimage <level set>.

- !Runimage (the front end and the game) is squeezed with Acorn's squeeze
  and then encrypted: the code at &8000 decrypts the image from its end
  backwards, XORing with PC - whose PSR bits make the key depend on the
  flags - until it has rewritten its own loop, then moves the image up a
  word from &8064 and runs it there. tools/unpack runs that with
  libroger's interpreter and saves the image as it arrives at &8064;
  that image is translated and run from &8064.
- !Loader is a Wimp task of its own showing a "loading" window while
  !Run2 goes on. !Runimage quits at once unless the loader left it the
  number variable FLoader$Task (the clock when it started, in 2^16
  centisecond units). The loader isn't run; game.c sets the variable as
  the loader does.
- The modules are loaded before the program as !Run2 leaves them
  (recomp/gen/modules.inc): FervourMode (50KHzMode: *FModeOn finds a free
  mode number, patches its own service handler to claim it and selects
  it - a 368x216 256-colour mode it defines with Service_ModeExtension),
  AEHModule and SoundMaster (A.E. Hersee's heap / Wimp helpers and music
  player; each comes as a squeezed absolute that inserts the module it
  carries, unpacked by tools/images.py), DummyJoy.
- !Runimage is a Wimp task: it puts two icons on the icon bar, the level
  set (Select plays it) and Fervour (Select opens the Levels directory,
  Menu its menu). libroger has no desktop; game.c's wimp_idle clicks the
  level set's icon, and quits the task when it is back on the icon bar.
  The game then takes over the screen in FervourMode's mode.
- SoundMaster drives the sound DMA itself: it claims the sound buffer
  interrupt (device 9), programs MEMC's sound registers for RISC OS 3.1's
  own buffers and mixes four channels into them.

Not available: the desktop front end's windows - the level editor,
options, high scores and passwords windows - which the program creates and
keeps but libroger doesn't show. The level sets' !Help (on the disc a
"cheat" module made with The Hacker, not help) isn't used.

The code
--------

SuperSpider finds 10101 code words in !Runimage (155 functions; with
--global-r12: it keeps a workspace pointer in r12 all through), 9726 in
SoundMaster, 1565 in AEHModule, 60 in FervourMode. Play-testing interprets
three short stretches, listed in game.c, and the words the game patches in
its sprite plotter while they differ from what was translated.

What it took
------------

libroger: modules' *commands and service calls; modes modules define
(Service_ModeExtension), shown at their own size; the sound DMA driven by
the program (MEMC sound registers, device 9); module SWIs interruptible;
OS_IntOff/IntOn; self-modified code at run time; a Wimp keeping windows
and icons; OS_Byte 121 scans, 112/113 returning the previous bank;
OS_Word 14, number variables, OS_File along paths, OS_ReadMemMapInfo,
OS_SpriteOp select in headless runs; scripted key holds (key:N:ms).

SuperSpider: see its fervour/FERVOUR.md.
