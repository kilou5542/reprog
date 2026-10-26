#!/usr/bin/env python3
"""Sépare « carburant » et « air » sans changer l'injection en régime stabilisé.

Matériel : injecteurs Bosch 0 280 158 170 (125,3 g/min @3 bar) au lieu de 0 280 158 171 (90 g/min),
régulateur 4 bar au lieu de 3 bar (circuit sans retour, pression fixe / atmosphère), carburant E85.

  - gain injecteur 0x569A0 (axe dépression 0x56988, mbar) : × E85 / ratio_inj × sqrt((3+v)/(4+v))
  - VE 0x57084 (24×12, axe pression 0x5627C) : × inverse, avec v = 1013 - pression collecteur
    => produit gain × VE inchangé : même injection qu'avant en régime stabilisé
  - amorçage 0x59708 : même compensation (v ≈ 0) pour garder la même quantité au démarrage

  python3 separer_carburant.py entree.bin sortie.bin
"""
import math
import sys
import marelli4mv as m

E85 = 1.45                     # carburant E85 / essence (en masse, densité incluse)
R_INJ = 125.3 / 90.0           # 0 280 158 170 / 0 280 158 171
P_OLD, P_NEW = 3.0, 4.0        # bar, relatif à l'atmosphère
GAIN, GAIN_AX, VE, VE_AX, PRIME = 0x569A0, 0x56988, 0x57084, 0x5627C, 0x59708


def hw(v_mbar):
    """Débit réel du nouveau matériel / débit supposé par la ROM, à dépression v."""
    v = max(0.0, v_mbar) / 1000
    return R_INJ * math.sqrt((P_NEW + v) / (P_OLD + v))


def main():
    src, dst = sys.argv[1:3]
    d = m.load(src)
    ax = m.words(d, GAIN_AX, 12)
    g = m.words(d, GAIN, 12)
    g2 = [round(gi * E85 / hw(v)) for gi, v in zip(g, ax)]
    m.put_words(d, GAIN, g2)
    print('gain 0x569A0  avant', g, '\n              après', g2)

    pax = m.words(d, VE_AX, 12)
    for r in range(24):
        row = m.words(d, VE + 0x18 * r, 12)
        m.put_words(d, VE + 0x18 * r, [min(0xFFFF, round(x * hw(1013 - p) / E85)) for x, p in zip(row, pax)])
    print('VE 0x57084 : facteur par colonne', [round(hw(1013 - p) / E85, 3) for p in pax])

    pr = m.words(d, PRIME, 16)
    k = hw(0) / E85
    pr2 = [min(0xFFFF, round(x * k)) for x in pr]
    m.put_words(d, PRIME, pr2)
    print(f'amorçage 0x59708 ×{k:.3f}', pr, '->', pr2)

    m.fix(d)
    m.save(dst, d)
    print('checksums :', m.check(d))


if __name__ == '__main__':
    main()
