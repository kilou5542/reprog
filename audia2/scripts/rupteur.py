#!/usr/bin/env python3
"""Rupteur franc (validé sur route : v5f, 7000 tr/min), appliqué sur la v5.

Trois mécanismes doivent être réglés ensemble :
  - coupure d'injection (fct 0x14F58) : 0x5653A / 0x5653C = seuil haut / bas (hystérésis 0x5653E = 100) ;
    au point mort, seuil - 0x56546 (2500) ;
  - coupure de toutes les injections (fct 0x46782) : au seuil, $62C = 100 % ; l'injection ne reprend
    que sous 0x5B8EA (5610 d'origine -> reprise tardive vers 5600 constatée en v5..v5e) ;
  - limiteur par le couple (fct 0x26930) : 0x57CAC..0x57CB6 (début, relâche, bas de rampe, régulateur
    on/off, maxi). Les 6 valeurs égales au seuil suppriment la remontée lente du couple (rampe 0x57C2E).
Réglage repris de la ROM « A2_CA-DR_7000 » de l'utilisateur. Défaut de surrégime à seuil + 200 ;
fin de la régulation de cliquetis laissée à 5900 (origine CA).

  python3 rupteur.py entree.bin sortie.bin [regime=7000]
"""
import sys

import marelli4mv as m


def reglages(cut):
    return [
        (0x5653A, [cut, cut], 'coupure injection (haut / bas)'),
        (0x5B8EA, [cut], 'reprise de l\'injection après coupure (fct 0x46782)'),
        (0x57CAC, [cut] * 6, 'limiteur par le couple : 6 valeurs égales au seuil'),
        (0x56542, [cut + 200], 'seuil du défaut de surrégime'),
        (0x5BA32, [5900], 'fin de la régulation de cliquetis (origine CA)'),
    ]


def main():
    src, dst = sys.argv[1:3]
    cut = int(sys.argv[3]) if len(sys.argv) > 3 else 7000
    d = m.load(src)
    for a, vals, name in reglages(cut):
        old = m.words(d, a, len(vals))
        m.put_words(d, a, vals)
        print(f'0x{a:05X} {name}\n   {old} -> {vals}')
    m.fix(d)
    assert m.check(d) == (True, True)
    m.save(dst, d)
    print(f'-> {dst}, checksum OK')


if __name__ == '__main__':
    main()
