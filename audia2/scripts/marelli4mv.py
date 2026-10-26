#!/usr/bin/env python3
"""Outils Marelli 4MV (036906034xx) : lecture/écriture du dump (octets inversés par mot) et checksum.

Checksums (fonction 0x50678 / 0x50788 du logiciel) :
  - principal : somme 16 bits des MOTS de 0x04000 à 0x7FFFF = mot @0x7FFE8 (compensation @0x7FFEA)
  - zone code : somme 16 bits des octets 0x18584–0x1C4FF = mot @0x7FFEC (inchangée si on ne touche pas le code)
  - boot      : désactivé (drapeau 0x5C863 = 0)
Un checksum principal faux lève le chemin de défaut 63 (P0605).
"""
import struct
import sys

SIZE = 0x80000
MAIN_SUM, MAIN_COMP = 0x7FFE8, 0x7FFEA


def load(path):
    d = bytearray(open(path, 'rb').read())
    if len(d) != SIZE:
        sys.exit(f"{path}: taille {len(d):#x} inattendue")
    d[0::2], d[1::2] = d[1::2], d[0::2]
    return d


def save(path, d):
    out = bytearray(d)
    out[0::2], out[1::2] = out[1::2], out[0::2]
    open(path, 'wb').write(out)


def words(d, a, n):
    return list(struct.unpack(f'>{n}H', d[a:a + 2 * n]))


def put_words(d, a, vals):
    d[a:a + 2 * len(vals)] = struct.pack(f'>{len(vals)}H', *vals)


def main_sum(d):
    return sum(struct.unpack('>%dH' % ((SIZE - 0x4000) // 2), d[0x4000:SIZE])) & 0xFFFF


def check(d):
    return main_sum(d) == words(d, MAIN_SUM, 1)[0], sum(d[0x18584:0x1C500]) & 0xFFFF == words(d, 0x7FFEC, 1)[0]


def fix(d):
    """Le mot de checksum fait partie de la somme : on garde sa valeur et on ajuste la compensation."""
    put_words(d, MAIN_COMP, [0])
    rest = main_sum(d) - words(d, MAIN_SUM, 1)[0]
    put_words(d, MAIN_COMP, [(-rest) & 0xFFFF])
    return d


if __name__ == '__main__':
    # python3 marelli4mv.py fichier.bin [...]          -> vérifie
    # python3 marelli4mv.py fix entree.bin sortie.bin  -> corrige le checksum principal
    if len(sys.argv) == 4 and sys.argv[1] == 'fix':
        d = fix(load(sys.argv[2]))
        save(sys.argv[3], d)
        m, z = check(d)
        print(f"{sys.argv[3]}: principal {'OK' if m else 'FAUX'}, zone code {'OK' if z else 'FAUX (code 0x18584-0x1C4FF modifié)'}")
    else:
        for p in sys.argv[1:]:
            m, z = check(load(p))
            print(f"{p}: principal {'OK' if m else 'FAUX'}, zone code {'OK' if z else 'FAUX'}")
