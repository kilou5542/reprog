"""Fonctions communes aux outils (après preparer.py)."""
import bisect
import collections
import os
import pickle
import re
import struct

ICI = os.path.dirname(os.path.abspath(__file__))
TRAVAIL = os.path.join(ICI, 'travail')
D = pickle.load(open(os.path.join(TRAVAIL, 'dis.pkl'), 'rb'))
A = sorted(D)
BIN = open(os.path.join(TRAVAIL, 'rom_le.bin'), 'rb').read()
DB = pickle.load(open(os.path.join(TRAVAIL, 'db.pkl'), 'rb'))
T = DB['funcs']
A5 = 0xE5770


def w(a, n=1, b=BIN):
    """Mots signés lus dans le fichier (little-endian)."""
    return list(struct.unpack('<%dh' % n, b[a:a + 2 * n]))


def norm(o):
    """$e7xxx.l -> $xxx(a5) (même variable RAM)."""
    def f(m):
        v = int(m.group(1), 16)
        return f'${v - A5:x}(a5)' if A5 <= v < 0xF0000 else m.group(0)
    return re.sub(r'\$([0-9a-f]{5,6})\.l', f, o)


def func_of(a):
    return T[bisect.bisect_right(T, a) - 1]


def fend(f):
    k = bisect.bisect_right(T, f)
    return T[k] if k < len(T) else f + 0x400


def ann(o):
    """Ajoute la valeur lue dans la ROM après chaque adresse de calibration."""
    def f(m):
        v = int(m.group(1), 16)
        return f'${v:x}.l{{={w(v)[0]}}}' if 0x55000 <= v < 0x5D000 else m.group(0)
    return re.sub(r'\$([0-9a-f]{5})\.l', f, o)


def dump(f, end=None):
    end = end or fend(f)
    out = []
    for a in A[bisect.bisect_left(A, f):]:
        if a >= end:
            break
        s, m, o = D[a]
        out.append(f'{a:06x}: {"TBL(1D)" if m == "fsmove" else m:10} {ann(norm(o))}')
    return '\n'.join(out)
