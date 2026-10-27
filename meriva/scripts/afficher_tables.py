#!/usr/bin/env python3
"""Affiche (en Markdown) toutes les tables identifiées, lues dans une ROM Z16XE.

Usage : python3 afficher_tables.py rom.bin [jeu]      (jeu 0 par défaut, 1 pour le second jeu)
        python3 afficher_tables.py rom.bin 0 > ../VALEURS_ORIGINE.md
"""
import sys

from tables import TABLES, lire


def fmt(v):
    if isinstance(v, float):
        return ('%.1f' % v).rstrip('0').rstrip('.') if abs(v) < 1000 else '%.0f' % v
    return str(v)


def main():
    rom = open(sys.argv[1], 'rb').read()
    jeu = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    print('# Valeurs lues dans %s (jeu %d)\n' % (sys.argv[1].split('/')[-1], jeu))
    print('Généré par `scripts/afficher_tables.py`. Définitions : `scripts/tables.py`.\n')
    for cle, (titre, adrs, l, c, t, conv, ay, ax, unite) in TABLES.items():
        a = adrs[jeu] if adrs[jeu] is not None else adrs[0]
        val = lire(rom, cle, jeu) or lire(rom, cle, 0)
        print('## %s\n' % titre)
        autre = ' / jeu 1 : 0x%04X' % adrs[1] if adrs[1] is not None else ' (jeu unique)'
        print('`%s` — 0x%04X%s — %d x %d %s — unité : %s\n' % (
            cle, a, autre, l, c, 'octets' if t == 'B' else 'mots', unite))
        if l == 1 and c == 1:
            print('Valeur : **%s**\n' % fmt(val[0][0]))
            continue
        tete = [''] + ([fmt(x) for x in ax] if ax else [str(i) for i in range(c)])
        print('| ' + ' | '.join(tete) + ' |')
        print('|' + '---|' * len(tete))
        for r, ligne in enumerate(val):
            nom = fmt(ay[r]) if ay else ''
            print('| ' + ' | '.join([nom] + [fmt(v) for v in ligne]) + ' |')
        print()


if __name__ == '__main__':
    main()
