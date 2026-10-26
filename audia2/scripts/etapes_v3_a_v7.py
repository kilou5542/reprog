#!/usr/bin/env python3
"""Rejoue les étapes v3 à v7 (faites à la main pendant la mise au point) sur la v2.

  v3 : ralenti chaud 850 tr/min (0x56C58, points 60 à 120 °C)
  v4 : tables de couple 0x55688 (16x11) et 0x55EB8 (24x12) reprises de la ROM « audiEGRoff… »
  v5 : régime maxi 6800 (regime_max.py)
  v6 : l'adaptation du modèle papillon est bloquée tant que le capteur EGR (débranché) est en défaut
       ($DBA != 0). On débloque UNIQUEMENT les deux adaptations du modèle papillon :
         0x226C2  bne.w (si $DBA) -> nop nop   (intégrateur d'adaptation $174E/$1740)
         0x23A62  bne.w (si $DBA) -> nop nop   (adaptation du modèle 0x57786)
       Le statut EGR reste « en défaut » comme en v5 (code défaut masqué depuis la v1), donc toute la
       surveillance / apprentissage EGR (0x46C80-0x47F00) reste endormie. Sortie = « v7c ».
       Historique : forcer $DBA = 0 (v6/v7) recopiait le capteur débranché comme position EGR -> pas de
       démarrage ; v7b (position forcée à 0) démarrait une fois, puis voyant « vanne EGR non calibrée »
       (apprentissage EGR sur un capteur fictif, valeurs stockées en EEPROM) et plus de redémarrage.
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

    for a, orig in ((0x226C2, '66000052'), (0x23A62, '660001da')):   # v6 : bne.w -> nop nop
        assert d[a:a + 4] == bytes.fromhex(orig), hex(a)
        d[a:a + 4] = bytes.fromhex('4e714e71')

    m.put_words(d, 0x5B970, [0])                                       # v7

    m.fix(d)
    m.save(out, d)
    print(f'-> {out}, checksums : {m.check(d)}')


if __name__ == '__main__':
    main()
