#!/usr/bin/env python3
"""Recale le modèle de pression papillon (0x57786) pour le papillon Golf 52 mm (036 133 062 M).

Reprend la table de la ROM Golf 036906034DR et l'INTERPOLE sur les axes de l'A2
(angle 0x57064, régime 0x561FC, partagés avec d'autres tables : on n'y touche pas),
avec mise à l'échelle de la pression de référence (0x57AC6 : 1001 Golf -> 1014 A2).

  python3 papillon52.py ROM_A2.bin ROM_GOLF_DR.bin sortie.bin
"""
import sys
import marelli4mv as m

TBL, ANG, RPM, PREF = 0x57786, 0x57064, 0x561FC, 0x57AC6


def interp(xs, ys, x):
    if x <= xs[0]:
        return ys[0]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            return ys[i] + (ys[i + 1] - ys[i]) * (x - xs[i]) / (xs[i + 1] - xs[i])
    return ys[-1]


def main():
    a2, golf, out = sys.argv[1:4]
    A, G = m.load(a2), m.load(golf)
    aA, rA = m.words(A, ANG, 16), m.words(A, RPM, 16)
    aG, rG = m.words(G, ANG, 16), m.words(G, RPM, 16)
    TG = [m.words(G, TBL + 0x20 * r, 16) for r in range(16)]
    k = m.words(A, PREF, 1)[0] / m.words(G, PREF, 1)[0]
    for r, rpm in enumerate(rA):
        row = []
        for ang in aA:
            col = [interp(aG, TG[i], ang) for i in range(16)]
            row.append(min(0xFFFF, round(interp(rG, col, rpm) * k)))
        old = m.words(A, TBL + 0x20 * r, 16)
        m.put_words(A, TBL + 0x20 * r, row)
        print(f"{rpm:5} tr/min  avant {old}\n{'':13}après {row}")
    m.fix(A)
    m.save(out, A)
    print('checksums :', m.check(A))


if __name__ == '__main__':
    main()
