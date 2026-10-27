#!/usr/bin/env python3
"""Fabrique la ROM E85 v2 depuis l'origine.

Usage : python3 e85.py ../roms/originales/meriva_z16xe_12230554_EZ.ori ../roms/meriva_e85_v2.bin

- Constante injecteur 0x07BE x 1,25 (gain global ; la sonde lambda complète en E85, SP reste roulable).
- AFR de lancement 0x0E32 / 0x0E3F : l'AFR effectif (table - enrichissement initial 0x0F70, laissé
  à 2,0) est divisé par 2,0 à -28 °C ... 1,3 à chaud. Attention : si table - 0x0F70 tombe à 0, le
  code force l'AFR à 0,1 (noyage) ; l'AFR effectif est donc gardé >= 0,1.
- Impulsion d'amorçage 0x07D2 / 0x07F4 : x 1,25, plus x 1,6 à froid (bornée à 0x7FF0, limite du code).
- Checksum recalculé.
"""
import struct
import sys

from fix_checksum import CS_OFFSET, checksum

GAIN = 1.25
# facteur d'enrichissement du lancement, eau -28..116 °C (13 points)
F_LANCEMENT = [2.0, 2.0, 1.9, 1.8, 1.6, 1.5, 1.4, 1.3, 1.3, 1.3, 1.3, 1.3, 1.3]
# supplément à froid de l'amorçage, eau -40..152 °C (17 points)
F_AMORCAGE = [1.6, 1.6, 1.6, 1.6, 1.4, 1.4, 1.2, 1.1] + [1.0] * 9


def mots(d, a, n):
    return [struct.unpack('>H', d[a + 2 * i:a + 2 * i + 2])[0] for i in range(n)]


def ecrire_mots(d, a, v):
    for i, x in enumerate(v):
        d[a + 2 * i:a + 2 * i + 2] = struct.pack('>H', min(int(round(x)), 0xFFFF))


def main():
    d = bytearray(open(sys.argv[1], 'rb').read())
    ecrire_mots(d, 0x07BE, [x * GAIN for x in mots(d, 0x07BE, 9)])
    for a, init in ((0x0E32, 0x0F70), (0x0E3F, 0x0F71)):
        for i, f in enumerate(F_LANCEMENT):
            effectif = max(d[a + i] - d[init], 1)
            d[a + i] = d[init] + max(1, int(round(effectif / f)))
    for a in (0x07D2, 0x07F4):
        ecrire_mots(d, a, [min(x * GAIN * f, 0x7FF0) for x, f in zip(mots(d, a, 17), F_AMORCAGE)])
    d[CS_OFFSET:CS_OFFSET + 2] = struct.pack('>H', checksum(d))
    open(sys.argv[2], 'wb').write(d)


if __name__ == '__main__':
    main()
