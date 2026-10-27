#!/usr/bin/env python3
"""Désassemble la ROM Delphi Z16XE (Motorola CPU32) en un listing texte.

Usage : python3 desassembler.py rom.ori listing.asm [debut_hex fin_hex]
Les adresses du listing sont des offsets fichier (flash vue à 0x40000 par le processeur).
Le code commence à 0x6F80 (vecteur de reset 0x46F80) ; la calibration occupe 0x0000-0x6000.
Les instructions CPU32 TBLU (interpolation de table) sont mal décodées par capstone
(affichées « fmove »/« fsqrt ») : voir MEMOIRE.md, routines de lecture de table.

Nécessite le module capstone (pip install capstone).
"""
import sys

import capstone

FLASH = 0x40000


def desassembler(rom, debut, fin):
    md = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_M68K_040)
    md.skipdata = True
    for ins in md.disasm(rom[debut:fin], FLASH + debut):
        yield '%06x  %-8s %s' % (ins.address - FLASH, ins.mnemonic, ins.op_str)


def main():
    rom = open(sys.argv[1], 'rb').read()
    debut = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x6F80
    fin = int(sys.argv[4], 16) if len(sys.argv) > 4 else len(rom)
    with open(sys.argv[2], 'w') as f:
        for ligne in desassembler(rom, debut, fin):
            f.write(ligne + '\n')


if __name__ == '__main__':
    main()
