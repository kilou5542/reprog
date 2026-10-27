#!/usr/bin/env python3
"""Recale le modèle papillon par la calibration (sans patch de code) et élargit la tolérance du P0106 / P1553.

L'apprentissage `$1740` ne peut pas être débloqué (patch de code non écrit par l'outil de flash). La table
0x57986 (8 lignes position EGR × 16 colonnes angle papillon, 0,1 % d'angle) est ajoutée à l'angle du modèle
(fct 0x22DDE : angle modèle = angle + 0x57986 − $1740 − $1742) : elle joue le même rôle. Écart mesuré au ralenti
(26/10, v5g) : modèle −76 mbar à 2,55 % d'angle, −17 mbar à 4,51 % → correction +1,0 % puis +0,2 % d'angle.
Ajout sur toutes les lignes (quelle que soit la position EGR lue) : +16 aux colonnes 0 % et 1,2 %, +2 à 4,2 %.
Tolérance du diagnostic 0x5AF48 (dynamique, dynamique, stabilisé) : +50 mbar.

  python3 modele_p0106.py entree.bin sortie.bin
"""
import sys

import marelli4mv as m

TABLE, NL, NC = 0x57986, 8, 16
AJOUT = [16, 16, 2] + [0] * 13
TOL, TOL_PLUS = 0x5AF48, 50


def main():
    src, dst = sys.argv[1:3]
    d = m.load(src)
    for r in range(NL):
        a = TABLE + 2 * NC * r
        old = m.words(d, a, NC)
        m.put_words(d, a, [v + k for v, k in zip(old, AJOUT)])
    print('0x57986 ligne 0 :', m.words(d, TABLE, NC))
    old = m.words(d, TOL, 3)
    m.put_words(d, TOL, [v + TOL_PLUS for v in old])
    print('0x5AF48 tolérances :', old, '->', m.words(d, TOL, 3))
    m.fix(d)
    assert m.check(d) == (True, True) and m.check_code(d)
    m.save(dst, d)
    print(f'-> {dst}')


if __name__ == '__main__':
    main()
