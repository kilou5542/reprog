"""Liste toutes les lectures de tables (1D / 2D) : adresse, fonction, table, ligne (y), colonne (x), sortie.
Notation axe : variable@FIN[n] ; l'axe commence à FIN - 2n.     python3 -I lectures.py [filtre]"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import DB
P = DB['pos']
f = sys.argv[1].lower() if len(sys.argv) > 1 else ''
def pp(p):
    if p in P:
        ax, n, inp, _ = P[p]
        return f'{p}@{ax:x}[{n}]'
    return str(p)
for a, fn, k, t, y, x, o in DB['lookups']:
    t = f'{t:x}' if isinstance(t, int) else t
    l = f'{a:06x} f{fn:05x} {k:3} {t:>7}  ligne={pp(y)}  col={pp(x) if x else ""}  -> {o}'
    if f in l.lower():
        print(l)
