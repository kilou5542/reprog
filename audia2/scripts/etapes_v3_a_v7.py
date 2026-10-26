#!/usr/bin/env python3
"""Rejoue les étapes v3 à v7 (faites à la main pendant la mise au point) sur la v2.

  v3 : ralenti chaud 850 tr/min (0x56C58, points 60 à 120 °C)
  v4 : tables de couple 0x55688 (16x11) et 0x55EB8 (24x12) reprises de la ROM « audiEGRoff… »
  v5 : régime maxi 6800 (regime_max.py)
  v6 : 0x3C2B4  move.b d0,$DBA(a5) -> clr.b $DBA(a5) : état du défaut EGR (chemin 0x26) forcé « OK »,
       sinon l'adaptation du modèle papillon reste bloquée par le capteur EGR débranché
       + 0x3C2C0  move.w (a1),$DB6(a5) -> clr.w $DB6(a5) : position EGR utilisée forcée à 0 (fermée).
       Sans cette 2e partie (v6/v7 d'origine), la tension du capteur débranché est prise pour une vanne
       ouverte et la voiture NE DÉMARRE PAS (constaté). Sortie = « v7b ».
  v7 : 0x5B970 = 0 : test de débit EGR désactivé

  python3 etapes_v3_a_v7.py a2_ori_e85_v2.bin rom_audiEGRoff.bin sortie_v7.bin
"""
import struct
import sys

import marelli4mv as m
import regime_max


def main():
    src, hyb, out = sys.argv[1:4]
    d, h = m.load(src), m.load(hyb)

    ral = m.words(d, 0x56C58, 16)
    m.put_words(d, 0x56C58, ral[:9] + [850] * 7)                     # v3

    for a, n in ((0x55688, 16 * 11), (0x55EB8, 24 * 12)):             # v4
        d[a:a + 2 * n] = h[a:a + 2 * n]

    for a, vals, _ in regime_max.REGLAGES:                              # v5
        m.put_words(d, a, vals)

    assert d[0x3C2B4:0x3C2B8] == bytes.fromhex('1b400dba')             # v6
    d[0x3C2B4:0x3C2B6] = struct.pack('>H', 0x422D)
    assert d[0x3C2C0:0x3C2C4] == bytes.fromhex('3b510db6')             # move.w (a1),$DB6(a5)
    d[0x3C2C0:0x3C2C4] = bytes.fromhex('426d0db6')                     # clr.w $DB6(a5)

    m.put_words(d, 0x5B970, [0])                                       # v7

    m.fix(d)
    m.save(out, d)
    print(f'-> {out}, checksums : {m.check(d)}')


if __name__ == '__main__':
    main()
