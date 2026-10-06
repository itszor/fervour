#!/usr/bin/env python3
"""Render screen memory from a headless run (recomp.screen: screen memory
from &20000 below its base) as PNGs, one per bank, in the default
256-colour palette. Usage: screen.py file w h banks out_prefix"""
import sys
from PIL import Image

path, w, h, banks, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
d = open(path, 'rb').read()[0x20000:]
pal = []
for p in range(256):
    t = p & 3
    r = (p >> 2 & 1) << 2 | t | (p >> 4 & 1) << 3
    g = t | (p >> 5 & 1) << 2 | (p >> 6 & 1) << 3
    b = (p >> 3 & 1) << 2 | t | (p >> 7 & 1) << 3
    pal += [r * 17, g * 17, b * 17]
for k in range(banks):
    im = Image.frombytes('P', (w, h), d[k * w * h:(k + 1) * w * h])
    im.putpalette(pal)
    im.convert('RGB').save('%s%d.png' % (out, k))
