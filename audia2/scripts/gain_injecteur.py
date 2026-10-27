#!/usr/bin/env python3
"""Multiplie le gain injecteur 0x569A0 par un facteur et compense ce qui ne doit pas changer.

Le gain convertit la masse de carburant calculée en temps d'injection (fct 0x2AAF0). Le changer revient à
corriger une richesse identique partout (log du 27/10/2026 : médiane 0,92). Pour ne rien changer d'autre :
  - lancement : quantité 0x59708 et budget 0x5B8B6 sont des masses, avant le gain -> / facteur ;
  - consommation affichée : cumul des masses / 0x5BA22 -> 0x5BA22 / facteur (les trims revenant vers 0,
    la masse calculée augmente de 1 / facteur pour le même carburant réel).
Somme du code 0x7FF74 inchangée (calibration seule) ; checksum principal corrigé.

  python3 gain_injecteur.py entree.bin sortie.bin [facteur=0.93]
"""
import sys

import marelli4mv as m

TABLES = (
    (0x569A0, 12, 'gain injecteur', 'x'),
    (0x59708, 16, 'amorçage au lancement (Craaaaanking)', '/'),
    (0x5B8B6, 16, 'budget d\'amorçage', '/'),
    (0x5BA22, 1, 'masse volumique (consommation affichée)', '/'),
)


def main():
    src, dst = sys.argv[1:3]
    k = float(sys.argv[3]) if len(sys.argv) > 3 else 0.93
    d = m.load(src)
    for a, n, nom, op in TABLES:
        old = m.words(d, a, n)
        new = [min(0xFFFF, round(v * k if op == 'x' else v / k)) for v in old]
        m.put_words(d, a, new)
        print(f'0x{a:05X} {nom} ({op}{k})\n   {old}\n-> {new}')
    m.fix(d)
    assert m.check(d) == (True, True) and m.check_code(d)
    m.save(dst, d)
    print(f'-> {dst}, checksums et somme du code OK')


if __name__ == '__main__':
    main()
