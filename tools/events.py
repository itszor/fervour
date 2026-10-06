#!/usr/bin/env python3
"""Print a libroger event log (recomp.events) with hex strings decoded.
Usage: events.py [file] [from-line-substring]"""
import sys

path = sys.argv[1] if len(sys.argv) > 1 else 'recomp.events'
start = sys.argv[2] if len(sys.argv) > 2 else None
on = start is None
for line in open(path):
    if not on and start in line:
        on = True
    if not on:
        continue
    p = line.split()
    out = []
    for x in p[2:]:
        if len(x) > 8 and len(x) % 2 == 0 and all(c in '0123456789abcdef' for c in x):
            b = bytes.fromhex(x)
            if sum(32 <= c < 127 for c in b) >= len(b) * 0.8:
                out.append(repr(b.decode('latin1')))
                continue
        out.append(x)
    print(p[0], p[1] if len(p) > 1 else '', ' '.join(out))
