#!/usr/bin/env python3
"""Relève toutes les limites de régime du 4MV CA (régime moteur = $1DA4 / $18E0).

  1. limiteur par le couple (fonction 0x26930) : 0x57CAC..0x57CB6
  2. coupure d'injection (fonction 0x14F58, drapeau $1DB6 lu par l'injection en 0x45E88) : 0x5653A / 0x5653C
  3. défaut de surrégime (chemin 44, fonction 0x15196) : 0x56542
  4. régulation de cliquetis désactivée au-delà de 0x5BA32 (fonction 0x49C1A)

  python3 regime_max.py entree.bin sortie.bin
"""
import sys
import marelli4mv as m

REGLAGES = [
    (0x57CAC, [6800, 6650, 6000, 6800, 6600, 6900], 'limiteur couple : début, relâche, bas de rampe, régulateur on/off, maxi'),
    (0x5653A, [7000, 7000], 'coupure injection (seuils haut / bas)'),
    (0x56542, [7300], 'seuil du défaut de surrégime'),
    (0x5BA32, [6800], 'régime maxi de la régulation de cliquetis'),
]


def main():
    d = m.load(sys.argv[1])
    for a, vals, name in REGLAGES:
        old = m.words(d, a, len(vals))
        m.put_words(d, a, vals)
        print(f'0x{a:05X} {name}\n   {old} -> {vals}')
    m.fix(d)
    m.save(sys.argv[2], d)
    print('checksums :', m.check(d))


if __name__ == '__main__':
    main()
