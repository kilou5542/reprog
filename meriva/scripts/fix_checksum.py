#!/usr/bin/env python3
"""Recalcule le checksum flash d'un dump Delphi Z16XE (12230554 / EZ, 256 Ko).

Checksum = somme 16 bits (mots big-endian) de 0x00040-0x00055 et 0x0005E-0x3FFFF,
stockée en big-endian à l'offset 0x0005C (routine firmware 0x1F3DC).

Usage : python3 fix_checksum.py fichier_modifie.bin [fichier_sortie.bin]
"""
import struct
import sys

CS_OFFSET = 0x5C


def checksum(data):
    def s16(a, b):
        return sum(struct.unpack('>%dH' % ((b - a) // 2), data[a:b]))
    return (s16(0x40, 0x56) + s16(0x5E, 0x40000)) & 0xFFFF


def main():
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src
    data = bytearray(open(src, 'rb').read())
    if len(data) != 0x40000:
        sys.exit('Taille inattendue : %d octets (attendu 262144)' % len(data))
    old = struct.unpack('>H', data[CS_OFFSET:CS_OFFSET + 2])[0]
    new = checksum(data)
    data[CS_OFFSET:CS_OFFSET + 2] = struct.pack('>H', new)
    open(dst, 'wb').write(data)
    print('Checksum : 0x%04X -> 0x%04X (%s)' % (old, new, 'inchangé' if old == new else 'corrigé'))


if __name__ == '__main__':
    main()
