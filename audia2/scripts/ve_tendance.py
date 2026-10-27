#!/usr/bin/env python3
"""Applique à la VE 0x57084 une correction douce (« tendance ») déduite de logs OBD VCDS.

Pour chaque mesure : facteur réellement appliqué f = 40000/(40000+100·STFT_obd) × 40000/(40000+200·LTFT_obd)
(échelles de ce calculateur, voir analyse_log_ve.py), résidu r = f / gain_deja_applique (ex. 0,93 en v5j).
La VE est corrigée par lissage à noyau (régime ±400 tr/min, MAP ±80 mbar) : loin des mesures, la correction
s'efface vers 1 ; elle est appliquée à `force` (70 %) et bornée à ±12 %. Pleine charge (MAP ≥ 900) : toutes les
mesures, même en montée en régime, associées au régime de la ligne précédente (retard de la STFT), poids 0,7.

  python3 ve_tendance.py entree.bin sortie.bin gain_deja_applique log1.csv [log2.csv ...]
"""
import math
import sys

import log_obd
import marelli4mv as m

VE, NR, NC = 0x57084, 24, 12
AX_RPM, AX_MAP = 0x5619C, 0x5627C
FORCE, BORNE = 0.7, 0.12
SR, SM = 400.0, 80.0


def mesures(path, gain):
    R = log_obd.lire(path)
    out = []
    for i in range(1, len(R) - 1):
        t, rpm, s, l, kpa = R[i]
        a, b = R[i - 1], R[i + 1]
        mbar = kpa * 10
        pleine = mbar >= 900
        if not pleine and (l == 0 or abs(b[1] - a[1]) > 150 or abs(b[4] - a[4]) > 4):
            continue
        if s >= 99:
            continue
        f = 40000 / (40000 + 100 * s) * 40000 / (40000 + 200 * l)
        if pleine:
            rpm = R[i - 1][1]          # retard de la STFT : régime de la ligne précédente
        out.append((rpm, mbar, f / gain, 0.7 if pleine else 1.0))
    return out


def main():
    src, dst, gain = sys.argv[1], sys.argv[2], float(sys.argv[3])
    pts = [p for f in sys.argv[4:] for p in mesures(f, gain)]
    d = m.load(src)
    rpm, mp = m.words(d, AX_RPM, NR), m.words(d, AX_MAP, NC)
    ve = m.words(d, VE, NR * NC)
    corr = []
    for i in range(NR):
        ligne = []
        for j in range(NC):
            sw = sv = 0.0
            for r, p, res, wt in pts:
                w = wt * math.exp(-((r - rpm[i]) / SR) ** 2 - ((p - mp[j]) / SM) ** 2)
                sw += w
                sv += w * math.log(res)
            if sw < 1e-3:
                ligne.append(1.0)
                continue
            conf = min(1.0, sw / 3.0)
            c = math.exp(sv / sw * conf * FORCE)
            ligne.append(min(1 + BORNE, max(1 - BORNE, c)))
        corr.append(ligne)
    new = [round(ve[i * NC + j] * corr[i][j]) for i in range(NR) for j in range(NC)]
    m.put_words(d, VE, new)
    m.fix(d)
    assert m.check(d) == (True, True) and m.check_code(d)
    m.save(dst, d)
    print(f'{len(pts)} mesures. Correction appliquée à la VE (lignes = régime, colonnes = MAP mbar) :')
    print('      ' + ''.join(f'{x:>6}' for x in mp))
    for i in range(NR):
        print(f'{rpm[i]:5} ' + ''.join(f'{corr[i][j]:6.2f}' for j in range(NC)))
    print(f'-> {dst}')


if __name__ == '__main__':
    main()
