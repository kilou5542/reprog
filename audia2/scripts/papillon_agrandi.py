#!/usr/bin/env python3
"""Agrandit la section effective du modèle papillon (0x57786) d'un facteur donné.

Le modèle donne la pression collecteur attendue selon l'angle (0x57064) et le régime (0x561FC),
rapportée à la pression de référence 0x57AC6. En régime stabilisé, le débit à travers le papillon
égale celui aspiré par le moteur (proportionnel à la pression collecteur) :
    A x psi(p/p0) = K(régime) x p/p0      soit   A / K = f(p/p0) = (p/p0) / psi(p/p0)
avec psi la fonction d'écoulement compressible (bloquée sous le rapport critique 0,528).
Pour une section A x k, chaque cellule devient f(p'/p0) = k x f(p/p0), résolu par dichotomie.
Les cellules déjà à la pression de référence ne bougent pas ; la table reste croissante selon l'angle.

  python3 papillon_agrandi.py entree.bin sortie.bin [facteur_surface=1.10]
"""
import math
import sys

import marelli4mv as m

TBL, PREF = 0x57786, 0x57AC6
G = 1.4
PR_CRIT = (2 / (G + 1)) ** (G / (G - 1))


def psi(pr):
    pr = min(max(pr, PR_CRIT), 1 - 1e-9)
    return math.sqrt(2 * G / (G - 1) * (pr ** (2 / G) - pr ** ((G + 1) / G)))


def f(pr):
    return pr / psi(pr)


def agrandir(p, p0, k):
    if p >= p0:
        return p
    cible = k * f(p / p0)
    lo, hi = p / p0, 1 - 1e-9
    for _ in range(60):
        mid = (lo + hi) / 2
        if f(mid) < cible:
            lo = mid
        else:
            hi = mid
    return min(p0, round(lo * p0))


def main():
    src, dst = sys.argv[1:3]
    k = float(sys.argv[3]) if len(sys.argv) > 3 else 1.10
    d = m.load(src)
    p0 = m.words(d, PREF, 1)[0]
    for r in range(16):
        a = TBL + 32 * r
        old = m.words(d, a, 16)
        new = [agrandir(p, p0, k) for p in old]
        for i in range(1, 16):                      # croissante selon l'angle
            new[i] = max(new[i], new[i - 1])
        m.put_words(d, a, new)
        print(f'ligne {r:2}  {old}\n          {new}')
    m.fix(d)
    assert m.check(d) == (True, True)
    m.save(dst, d)
    print(f'section x{k} -> {dst}, checksum OK')


if __name__ == '__main__':
    main()
