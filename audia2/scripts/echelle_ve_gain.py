#!/usr/bin/env python3
"""Change l'échelle de la VE en gardant la même essence : VE 0x57084 × k, gain injecteur 0x569A0 ÷ k.

Demande du 27/10/2026 : seulement ces deux tables (aucune autre compensation). Effets de bord connus :
charge calculée × k (axes d'avance / λ, conversion couple → charge, seuils en charge) ; lancement + 1/k
d'essence (quantités avant le gain) ; consommation affichée × k.

  python3 echelle_ve_gain.py entree.bin sortie.bin [k=0.95]
"""
import sys

import marelli4mv as m


def main():
    src, dst = sys.argv[1:3]
    k = float(sys.argv[3]) if len(sys.argv) > 3 else 0.95
    d = m.load(src)
    ve = m.words(d, 0x57084, 288)
    m.put_words(d, 0x57084, [round(v * k) for v in ve])
    g = m.words(d, 0x569A0, 12)
    m.put_words(d, 0x569A0, [round(v / k) for v in g])
    print('gain', g, '->', m.words(d, 0x569A0, 12))
    m.fix(d)
    assert m.check(d) == (True, True) and m.check_code(d)
    m.save(dst, d)
    print(f'-> {dst}')


if __name__ == '__main__':
    main()
