#!/usr/bin/env python3
"""Outils Marelli 4MV (036906034xx) : lecture/écriture du dump (octets inversés par mot) et checksum.

Checksums (fonction 0x50678 / 0x50788 du logiciel) :
  - principal : somme 16 bits des MOTS de 0x04000 à 0x7FFFF = mot @0x7FFE8 (compensation @0x7FFEA)
  - zone code : somme 16 bits des octets 0x18584–0x1C4FF = mot @0x7FFEC (inchangée si on ne touche pas le code)
  - boot      : désactivé (drapeau 0x5C863 = 0)
  - somme du code : somme 32 bits des OCTETS de 0x4000 à 0x537F3 = mot long @0x7FF74 (début 0x7FF78,
    longueur 0x7FF7C). Toutes les ROM dont le code a été modifié sans la recalculer n'ont pas démarré
    (v6, v7, v7b, v10, v10b, v11, v5h). Vérifiée par `check_code`, recalculée par `fix_code`.
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


CODE_SUM = 0x7FF74


def code_sum(d):
    debut, longueur = struct.unpack('>II', d[0x7FF78:0x7FF80])
    return sum(d[debut:debut + longueur]) & 0xFFFFFFFF


def check_code(d):
    return code_sum(d) == struct.unpack('>I', d[CODE_SUM:CODE_SUM + 4])[0]


def fix_code(d):
    """À appeler AVANT fix() : la somme du code est dans la zone du checksum principal."""
    d[CODE_SUM:CODE_SUM + 4] = struct.pack('>I', code_sum(d))
    return d


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
            d = load(p)
            m, z = check(d)
            c = check_code(d)
            print(f"{p}: principal {'OK' if m else 'FAUX'}, zone code {'OK' if z else 'FAUX'}, "
                  f"somme du code 0x7FF74 {'OK' if c else 'FAUSSE (toutes les ROM dans ce cas n ont pas démarré)'}")
