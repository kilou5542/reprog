#!/usr/bin/env python3
"""Reporte des tables d'une ROM source vers une ROM cible (même logiciel 4MV CA), puis corrige le checksum.

  python3 reporter_tables.py source.bin cible.bin sortie.bin
"""
import sys
import marelli4mv as m

TABLES = [  # (adresse, nombre de mots, nom)
    (0x57504, 144, 'correction air / température (enrichissement à froid)'),
    (0x58B00, 288, 'lambda cible de base'),
    (0x58D40, 288, 'lambda cible protection'),
    (0x59046, 24, 'lambda pleine charge'),
    (0x5BA66, 288, 'avance de base'),
    (0x5BCAE, 96, 'avance pleine charge'),
    (0x5C220, 288, 'avance 0x5C220 (plafond)'),
]


def main():
    S, D = m.load(sys.argv[1]), m.load(sys.argv[2])
    for a, n, name in TABLES:
        old = m.words(D, a, n)
        new = m.words(S, a, n)
        m.put_words(D, a, new)
        nd = sum(1 for x, y in zip(old, new) if x != y)
        print(f'0x{a:05X} {name:50} {nd:3} valeurs changées')
    m.fix(D)
    m.save(sys.argv[3], D)
    print('checksums :', m.check(D))


if __name__ == '__main__':
    main()
