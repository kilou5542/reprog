#!/usr/bin/env python3
"""Liste les appels aux routines de lecture de table, avec la table et les entrées passées.

Usage : python3 appels_tables.py listing.asm
(listing produit par desassembler.py)

Routines (adresses CPU, appelées en jsr d16(a5) avec a5 = 0x48046) :
  -$2516 = 0x45B30 : table 1D d'octets  (A1 = table, D1 = index 8.8)
  -$24fc = 0x45B4A : table 1D de mots   (A1 = table, D1 = index 8.8)
  -$24e2 = 0x45B64 : table 2D d'octets  (A1 = table, D1 = ligne 8.8, D0 = colonne 8.8, largeur empilée)
  -$247c = 0x45BCA : table 2D de mots   (idem)
L'adresse de table affichée est un offset fichier. Quand la table est choisie par $9808 (deux jeux),
le script ne voit souvent que l'une des deux branches : relire le code avec voir.sh.
"""
import re
import sys

A5 = 0x48046
ROUTINES = {'-$2516': '1D octets', '-$24fc': '1D mots', '-$24e2': '2D octets', '-$247c': '2D mots'}


def main():
    lignes = open(sys.argv[1]).read().split('\n')
    for k, l in enumerate(lignes):
        m = re.search(r'jsr\s+(-\$[0-9a-f]+)\(a5\)', l)
        if not m or m.group(1) not in ROUTINES:
            continue
        reg = {}
        largeur = None
        for c in lignes[max(0, k - 16):k]:
            p = c.split(None, 2)
            if len(p) < 3:
                continue
            ins = p[1] + ' ' + p[2]
            mm = re.match(r'lea\.l\s+(-?)\$([0-9a-f]+)\(a5\), (a\d)', ins)
            if mm:
                v = A5 + (-1 if mm.group(1) else 1) * int(mm.group(2), 16) - 0x40000
                reg[mm.group(3)] = 'T%04X' % v
            mm = re.match(r'movea\.l\s+(a\d), (a\d)', ins)
            if mm:
                reg[mm.group(2)] = reg.get(mm.group(1), '?' + mm.group(1))
            mm = re.match(r'(move\.[wlb]|moveq)\s+(.+), (d\d)$', ins)
            if mm:
                s = mm.group(2)
                reg[mm.group(3)] = reg.get(s, s) if re.match(r'd\d$', s) else s
            mm = re.match(r'move\.l\s+(d\d), -\(a7\)', ins)
            if mm:
                largeur = reg.get(mm.group(1))
        print(l.split()[0], ROUTINES[m.group(1)], 'table=%s' % reg.get('a1'),
              'ligne(d1)=%s' % reg.get('d1'), 'colonne(d0)=%s' % reg.get('d0'), 'largeur=%s' % largeur)


if __name__ == '__main__':
    main()
