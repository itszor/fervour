#!/usr/bin/env python3
"""The translated images of Fervour and the steps that build them.

    images.py extract   the ArcFS archive "Fervour" on the disc (extracted/disc,
                        from SuperSpider's weave.py: recipe.json), which holds
                        the game -> extracted/
    images.py unpack    the packed programs -> unpacked/ (see below)
    images.py analyse   SuperSpider (superspider analyse --full) on every image:
                        analysis/<name>.json; analysis/<name>.roots, if there,
                        adds entry points
    images.py roots LOG...
                        merges the gap entries of --trace-gaps runs (libroger's
                        untranslated.log) into analysis/<name>.roots
    images.py gen       superspider gen for every image -> recomp/gen/<name>/,
                        plus recomp/gen/modules.inc (game.c's module list)

What !Fervour.!Run2 runs, and what is translated:
  runimage     !Runimage, the game and its desktop front end. Squeezed
               (Acorn's squeeze: a stub at the end unpacks it to &8000 and
               jumps there), then self-decrypting: the code at &8000
               decrypts the image backwards, XORing with PC - whose PSR
               bits make the key depend on the flags - until it has
               rewritten its own loop, then moves the image from &8064 up a
               word and runs it from &8064. tools/unpack runs all of that
               with libroger's interpreter and saves the image as it is on
               arrival at &8064 (unpacked/RunImage), which is translated
               and entered there.
  fervourmode  50KHzMode: the FervourMode module (*FModeOn defines a
               368x216 256-colour screen mode through Service_ModeExtension
               and selects it). Not packed.
  aehmodule    AEHModule (A.E. Hersee's heap / Wimp utilities): a squeezed
               absolute that inserts the module it carries with OS_Module 11.
               Unpacked to unpacked/AEHModule.
  soundmaster  SM: SoundMaster (A.E. Hersee's music player), likewise.
  joystick     DummyJoy, a Joystick module that reads nothing: !Run2 loads
               it when no Joystick module is present. Not packed.

!Loader (a "loading" window: a Wimp task of its own, also encrypted) and
ColourTrans (ROM on RISC OS 3) are not used.

Modules are translated for the RMA addresses fixed here, in load order.
"""
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
EXT = os.path.join(TOP, 'extracted')
UNP = os.path.join(TOP, 'unpacked')
DISC = os.path.join(TOP, 'extracted', 'disc')     # the disc, as weave.py extracts it
SS = os.environ.get('SUPERSPIDER', os.path.expanduser('~/stuff/superspider'))
APP = '!Fervour'

RUNIMAGE_ENTRY = 0x8064
RMA = 0x1800000


def find(d, leaf):
    for f in os.listdir(os.path.join(EXT, d)):
        if f.split(',')[0].lower() == leaf.lower():
            return os.path.join(d, f)
    raise SystemExit('not found: %s/%s' % (d, leaf))


def images():
    """(name, path relative to the top, base, exec or None, is module)"""
    out = [('runimage', 'unpacked/RunImage', 0x8000, RUNIMAGE_ENTRY, False)]
    base = RMA
    for name, path in [('fervourmode', 'extracted/' + find(APP, '50KHzMode')),
                       ('aehmodule', 'unpacked/AEHModule'),
                       ('soundmaster', 'unpacked/SoundMaster'),
                       ('joystick', 'extracted/' + find(APP, 'DummyJoy'))]:
        out.append((name, path, base, None, True))
        base = (base + os.path.getsize(os.path.join(TOP, path)) + 0xFFF) & ~0xFFF
    return out


def run(cmd, **kw):
    print('+', ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True, **kw)


def extract():
    run([sys.executable, '-I', os.path.join(SS, 'tools', 'arcfs.py'),
         os.path.join(DISC, 'Fervour,fffddc00-00000000'), EXT])


def squeezed_size(path):
    """An Acorn-squeezed absolute: B to the unsqueeze stub, whose header
    (six words just before it) starts with the decoded size."""
    d = open(path, 'rb').read()
    w0 = struct.unpack_from('<I', d, 0)[0]
    assert w0 >> 24 == 0xEA, path + ': not squeezed'
    stub = ((w0 & 0xFFFFFF) << 2) + 8
    return struct.unpack_from('<I', d, stub - 0x24)[0]


def unpack():
    run(['make', '-C', HERE, 'unpack'])
    os.makedirs(UNP, exist_ok=True)
    tool = os.path.join(HERE, 'unpack')
    common = ['--limit=1e9', '--out=' + os.path.join(UNP, 'unpack')]
    # !Runimage: unsqueezed to &8000, decrypted, moved up a word from &8064
    src = os.path.join(EXT, find(APP, '!Runimage'))
    end = 0x8000 + squeezed_size(src) + 4
    run([tool, src, '--stop=8064', '--dump=8000:%x' % end,
         '--write=' + os.path.join(UNP, 'RunImage')] + common)
    # AEHModule, SM: unsqueezed, they insert the module after their code:
    # OS_Module 11 with R1 = &809C, R2 = the length word at &8098
    for leaf, name in [('AEHModule', 'AEHModule'), ('SM', 'SoundMaster')]:
        src = os.path.join(EXT, find(APP, leaf))
        raw = os.path.join(UNP, name + '.absolute')
        run([tool, src, '--stop=8000', '--dump=8000:%x' % (0x8000 + squeezed_size(src)),
             '--write=' + raw] + common)
        d = open(raw, 'rb').read()
        n = struct.unpack_from('<I', d, 0x98)[0]
        mod = d[0x9C:0x9C + n]
        title = mod[struct.unpack_from('<I', mod, 16)[0]:].split(b'\0')[0].decode()
        print('  %s: module %s, %d bytes' % (name, title, n))
        open(os.path.join(UNP, name), 'wb').write(mod)
        os.remove(raw)
    for f in os.listdir(UNP):
        if f.startswith('unpack.'):
            os.remove(os.path.join(UNP, f))


def analyse():
    subprocess.run(['dune', 'build'], cwd=SS, check=True)
    exe = os.path.join(SS, '_build/default/bin/main.exe')
    an = os.path.join(TOP, 'analysis')
    os.makedirs(an, exist_ok=True)
    for name, path, base, exe_addr, module in images():
        img = os.path.join(TOP, path)
        cmd = [exe, 'analyse', img, '%x' % base, '--full', '-o', os.path.join(an, name + '.json')]
        rf = os.path.join(an, name + '.roots')
        if os.path.exists(rf):
            cmd += ['--roots', rf]
        # the program keeps its workspace pointer in r12 all through (see
        # SuperSpider's --global-r12): its window and event dispatch walk
        # records in the workspace
        cmd += ['--module'] if module else ['--exec', '%x' % exe_addr, '--global-r12']
        run(cmd)


def roots(logs):
    """Merges the gap entries the --trace-gaps runs logged in LOGS (libroger's
    untranslated.log) into analysis/<name>.roots, for the next analyse."""
    an = os.path.join(TOP, 'analysis')
    for name, path, base, exe_addr, module in images():
        run([sys.executable, os.path.join(SS, 'tools/gap_roots.py'), os.path.join(TOP, path),
             '%x' % base, os.path.join(an, name + '.roots')] + logs)


def gen():
    exe = os.path.join(SS, '_build/default/bin/main.exe')
    rc = os.path.join(TOP, 'recomp')
    an = os.path.join(TOP, 'analysis')
    mods = []
    for k, (name, path, base, exe_addr, module) in enumerate(images()):
        tab = 'recomp' if not module else 'recomp_' + name
        prefix = 'F' if not module else 'M%d' % k
        run([exe, 'gen', os.path.join(TOP, path), '%x' % base, os.path.join(an, name + '.json'),
             '--c', os.path.join(rc, 'gen', name), '--prefix=' + prefix, '--tabprefix=' + tab, '--files=%d' % (8 if not module else 1)]
            + (['--covtag=%s' % chr(ord('A') + k)] if module else []))
        if module:
            mods.append((path, tab))
    with open(os.path.join(rc, 'gen', 'modules.inc'), 'w') as f:
        f.write('/* generated by ../tools/images.py - the modules, for game.c */\n')
        for _, tab in mods:
            f.write('extern const struct roger_image %s_image;\n' % tab)
        f.write('static const struct roger_module modules[] = {\n')
        for path, tab in mods:
            f.write('    {"../%s", &%s_image, 0},\n' % (path, tab))
        f.write('    {NULL, NULL, 0}};\n')


if __name__ == '__main__':
    if sys.argv[1:2] == ['roots']:
        roots(sys.argv[2:] or ['untranslated.log'])
        sys.exit()
    steps = {'extract': extract, 'unpack': unpack, 'analyse': analyse, 'gen': gen}
    for step in sys.argv[1:] or ['unpack', 'analyse', 'gen']:
        steps[step]()
