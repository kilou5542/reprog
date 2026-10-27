#!/usr/bin/env python3
"""Prépare le désassemblage d'une ROM 4MV (à lancer une fois par session, quelques secondes).

  python3 -I preparer.py [rom.bin]       (défaut : ../roms/originales/audiori_036906034CA.bin)

Produit dans travail/ (ignoré par git) :
  rom_le.bin   ROM telle quelle (mots little-endian, comme TunerPro)
  rom_be.bin   octets remis dans l'ordre du CPU (big-endian)
  dis.pkl      {adresse: (taille, mnémonique, opérandes)} pour 0x0-0x7FFFF (capstone, M68K)
  dis.txt      même chose en texte
  db.pkl       fonctions, lectures de tables 1D/2D, positions sur les axes, constantes lues
"""
import os
import pickle
import sys

import capstone

ICI = os.path.dirname(os.path.abspath(__file__))
TRAVAIL = os.path.join(ICI, 'travail')


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ICI, '..', 'roms', 'originales', 'audiori_036906034CA.bin')
    os.makedirs(TRAVAIL, exist_ok=True)
    le = open(src, 'rb').read()
    be = bytes(x for i in range(0, len(le), 2) for x in (le[i + 1], le[i]))
    open(os.path.join(TRAVAIL, 'rom_le.bin'), 'wb').write(le)
    open(os.path.join(TRAVAIL, 'rom_be.bin'), 'wb').write(be)
    md = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_BIG_ENDIAN | capstone.CS_MODE_M68K_040)
    md.skipdata = True
    out = {i.address: (i.size, i.mnemonic, i.op_str) for i in md.disasm(be, 0)}
    pickle.dump(out, open(os.path.join(TRAVAIL, 'dis.pkl'), 'wb'))
    with open(os.path.join(TRAVAIL, 'dis.txt'), 'w') as f:
        for a in sorted(out):
            s, m, o = out[a]
            f.write('%06x: %-10s %s\n' % (a, m, o))
    print(len(out), 'instructions')
    sys.argv = ['build', os.path.join(TRAVAIL, 'dis.pkl'), os.path.join(TRAVAIL, 'db.pkl')]
    exec(open(os.path.join(ICI, 'base_tables.py')).read(), {'__name__': '__main__'})


if __name__ == '__main__':
    main()
