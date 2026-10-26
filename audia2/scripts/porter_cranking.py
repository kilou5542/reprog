#!/usr/bin/env python3
"""Porte l'amorçage « Craaaaanking » d'une ROM à calibration Golf DR (version WinOLS BackupAudiSemiOK)
vers une ROM à calibration A2 CA, en gardant la MÊME quantité de carburant injectée.

  - 0x59708 : masse d'amorçage par impulsion (axe eau 0x562EC, -30..+120 °C)
  - 0x5B8B6 : budget total d'amorçage (même axe) — 63 partout sur la CA, vraie table sur la DR
Carburant injecté ∝ masse × gain injecteur (0x569A0, à dépression nulle) × 0x57E72,
donc on multiplie par (gain_DR × K_DR) / (gain_cible × K_cible).

  python3 porter_cranking.py source_DR.bin cible_CA.bin sortie.bin
"""
import sys
import marelli4mv as m

PRIME, BUDGET, GAIN, K = 0x59708, 0x5B8B6, 0x569A0, 0x57E72


def main():
    src, dst, out = sys.argv[1:4]
    S, D = m.load(src), m.load(dst)
    r = (m.words(S, GAIN, 1)[0] * m.words(S, K, 1)[0]) / (m.words(D, GAIN, 1)[0] * m.words(D, K, 1)[0])
    print(f'rapport de conversion : {r:.3f}')
    for name, a in (('amorçage 0x59708', PRIME), ('budget 0x5B8B6', BUDGET)):
        s, old = m.words(S, a, 16), m.words(D, a, 16)
        new = [min(0xFFFF, round(v * r)) for v in s]
        m.put_words(D, a, new)
        print(f'{name}\n  source {s}\n  avant  {old}\n  après  {new}')
    m.fix(D)
    m.save(out, D)
    print('checksums :', m.check(D))


if __name__ == '__main__':
    main()
