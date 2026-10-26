#!/usr/bin/env python3
"""Construit une ROM A2 CA à partir de l'ORIGINE (audiori) avec :
  1. EGR : codes défaut et configuration des défauts EGR désactivés (repris de la ROM « EGRoff »)
  2. modèle papillon Golf 52 mm (0x57786 interpolé)
  3. constantes injecteur E85 / Bosch 0 280 158 170 / 4 bar (gain 0x569A0) — VE d'origine conservée
  4. amorçage « Craaaaanking » (0x59708 + 0x5B8B6) converti depuis BackupAudiSemiOK
  5. ralenti à froid relevé (0x56C58, 0x56C38)
  6. checksum

  python3 construire_depuis_ori.py audiori.bin rom_egroff.bin rom_golf_DR.bin backup_DR.bin sortie.bin
"""
import math
import sys
import marelli4mv as m
from papillon52 import interp, TBL, ANG, RPM, PREF
from separer_carburant import hw, E85, GAIN, GAIN_AX
from ralenti_froid import AJOUT

EGR_ZONES = [(0x54BB8, 0x54BC8), (0x54BF8, 0x54BFA), (0x54C10, 0x54C12), (0x54D4A, 0x54D50),
             (0x5CBAC, 0x5CBB8), (0x5CBDC, 0x5CBE0), (0x5CBEE, 0x5CBF2)]
PRIME, BUDGET, K = 0x59708, 0x5B8B6, 0x57E72


def main():
    ori, egr, golf, backup, out = sys.argv[1:6]
    D, E, G, B = m.load(ori), m.load(egr), m.load(golf), m.load(backup)

    # 1. EGR
    for lo, hi in EGR_ZONES:
        D[lo:hi] = E[lo:hi]
    print('1. EGR : zones', ', '.join(f'{lo:#x}' for lo, _ in EGR_ZONES))

    # 2. modèle papillon 52 mm
    aA, rA = m.words(D, ANG, 16), m.words(D, RPM, 16)
    aG, rG = m.words(G, ANG, 16), m.words(G, RPM, 16)
    TG = [m.words(G, TBL + 0x20 * r, 16) for r in range(16)]
    k = m.words(D, PREF, 1)[0] / m.words(G, PREF, 1)[0]
    for r, rpm in enumerate(rA):
        row = [min(0xFFFF, round(interp(rG, [interp(aG, TG[i], a) for i in range(16)], rpm) * k)) for a in aA]
        m.put_words(D, TBL + 0x20 * r, row)
    print('2. papillon 52 mm : 0x57786 recalé')

    # 3. gain injecteur (VE d'origine inchangée)
    ax, g = m.words(D, GAIN_AX, 12), m.words(D, GAIN, 12)
    g2 = [round(gi * E85 / hw(v)) for gi, v in zip(g, ax)]
    m.put_words(D, GAIN, g2)
    print(f'3. gain 0x569A0 {g} -> {g2}')

    # 4. Craaaaanking : même carburant injecté que BackupAudiSemiOK
    r = (m.words(B, GAIN, 1)[0] * m.words(B, K, 1)[0]) / (m.words(D, GAIN, 1)[0] * m.words(D, K, 1)[0])
    for a in (PRIME, BUDGET):
        m.put_words(D, a, [min(0xFFFF, round(v * r)) for v in m.words(B, a, 16)])
    print(f'4. amorçage (rapport {r:.3f}) 0x59708 = {m.words(D, PRIME, 16)}')

    # 5. ralenti à froid
    for a in (0x56C58, 0x56C38):
        m.put_words(D, a, [v + k for v, k in zip(m.words(D, a, 16), AJOUT)])
        print(f'5. ralenti 0x{a:05X} = {m.words(D, a, 16)}')

    m.fix(D)
    m.save(out, D)
    print('6. checksums :', m.check(D))


if __name__ == '__main__':
    main()
