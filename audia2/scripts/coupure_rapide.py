#!/usr/bin/env python3
"""Coupure d'injection plus rapide au lâcher de pédale (comportement de la ROM « A2_CA-DR »).

La coupure en décélération (fct 0x3D08A, test en 0x3D15A) attend, sauf embrayage enfoncé, que
|couple `$E6606` - couple lissé `$126C`| < 0x5AA7A. Le lissage (fct 0x31FBE) est un filtre du 1er ordre dont
le coefficient (‰) vient des tables 0x5857C / 0x585FA (9 lignes régime, axe 0x56402 ; 7 colonnes couple,
axe 0x563F4). Plus le coefficient est grand, plus le lissage rattrape vite et plus la coupure arrive tôt.

Les tables de la ROM source sont ré-interpolées sur les axes de la ROM cible (axes différents CA / DR),
et 0x5AA7A est recopié.

  python3 coupure_rapide.py source_CADR.bin cible.bin sortie.bin
"""
import sys

import marelli4mv as m

AX_REG, AX_COUPLE = 0x56402, 0x563F4
TABLES = (0x5857C, 0x585FA)
LIGNES, COLONNES = 9, 7
SEUIL = 0x5AA7A


def s16(x):
    return x - 65536 if x > 32767 else x


def interp(ax, x):
    """Position fractionnaire de x sur l'axe (bornée aux extrémités, comme le calculateur)."""
    if x <= ax[0]:
        return 0.0
    for i in range(len(ax) - 1):
        if x <= ax[i + 1]:
            return i + (x - ax[i]) / (ax[i + 1] - ax[i])
    return float(len(ax) - 1)


def lire(tab, fi, fj):
    i0, j0 = min(int(fi), LIGNES - 2), min(int(fj), COLONNES - 2)
    di, dj = fi - i0, fj - j0
    a, b = tab[i0][j0], tab[i0][j0 + 1]
    c, d = tab[i0 + 1][j0], tab[i0 + 1][j0 + 1]
    return (a * (1 - dj) + b * dj) * (1 - di) + (c * (1 - dj) + d * dj) * di


def main():
    src, dst, out = sys.argv[1:4]
    S, D = m.load(src), m.load(dst)
    sr, sc = [s16(x) for x in m.words(S, AX_REG, LIGNES)], [s16(x) for x in m.words(S, AX_COUPLE, COLONNES)]
    dr, dc = [s16(x) for x in m.words(D, AX_REG, LIGNES)], [s16(x) for x in m.words(D, AX_COUPLE, COLONNES)]
    for t in TABLES:
        tab = [m.words(S, t + 2 * COLONNES * r, COLONNES) for r in range(LIGNES)]
        for r in range(LIGNES):
            fi = interp(sr, dr[r])
            row = [round(lire(tab, fi, interp(sc, dc[c]))) for c in range(COLONNES)]
            old = m.words(D, t + 2 * COLONNES * r, COLONNES)
            m.put_words(D, t + 2 * COLONNES * r, row)
            print(f'0x{t:05X} {dr[r]:5} tr/min  {old} -> {row}')
    seuil = m.words(S, SEUIL, 1)
    print(f'0x{SEUIL:05X} seuil d\'écart {m.words(D, SEUIL, 1)} -> {seuil}')
    m.put_words(D, SEUIL, seuil)
    m.fix(D)
    assert m.check(D) == (True, True)
    m.save(out, D)
    print(f'-> {out}, checksum OK')


if __name__ == '__main__':
    main()
