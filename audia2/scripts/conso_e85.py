#!/usr/bin/env python3
"""Consommation affichée au combiné, recalée pour l'E85.

Le calculateur cumule la MASSE de carburant de chaque injection ($62E, avant le gain injecteur)
et la convertit en volume avec 0x5BA22 = masse volumique (g/l, 740 d'origine) :
  volume = masse x 800 / 0x5BA22   (0x49440 : débit instantané, 0x495E8 : compteur)
Les injecteurs n'interviennent donc pas. En revanche, separer_carburant.py a réduit la masse
calculée d'un facteur E85 = 1,45 (le gain injecteur reprend ce facteur) : la masse réelle d'E85
vaut masse_calculée x 1,45. D'où 0x5BA22 = masse volumique E85 / 1,45.

  python3 conso_e85.py entree.bin sortie.bin [masse_volumique_g_l]
"""
import sys

import marelli4mv as m
from separer_carburant import E85

DENSITE = 0x5BA22
RHO_E85 = 785          # g/l, E85 (éthanol 789, essence 740-750)


def main():
    src, dst = sys.argv[1:3]
    rho = float(sys.argv[3]) if len(sys.argv) > 3 else RHO_E85
    d = m.load(src)
    old = m.words(d, DENSITE, 1)[0]
    new = round(rho / E85)
    m.put_words(d, DENSITE, [new])
    m.fix(d)
    assert m.check(d) == (True, True)
    m.save(dst, d)
    print(f'0x{DENSITE:05X} : {old} -> {new} (affichage x{old / new:.3f}) -> {dst}, checksum OK')


if __name__ == '__main__':
    main()
