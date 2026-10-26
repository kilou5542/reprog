#!/usr/bin/env python3
"""Rupteur franc par coupure d'injection (comportement de la ROM « audiEGRoff… »), appliqué sur la v5.

En v5, le limiteur par le couple (fct 0x26930) démarrait à 6800 (0x57CAC), AVANT la coupure d'injection
à 7000 (0x5653A). Il ramène le couple vers la table 0x57C3C (350 sur tous les points), le régime chute,
et sous 0x57CB0 (6000) le couple est rendu d'un coup : le régime oscille 6000 <-> 7000.
Dans la ROM d'origine de l'utilisateur, la coupure d'injection (6100) arrivait avant le limiteur
par le couple (6600) : rupteur franc.

Ici : la coupure d'injection fait le rupteur, le limiteur par le couple est placé au-dessus (sécurité),
et la régulation de cliquetis s'arrête à 5900 comme d'origine (en v5/v5b elle allait jusqu'à 6800 :
probable faux cliquetis à haut régime, retard d'allumage et reprise tardive constatée vers 5000-5900).
Coupure (0x14F58) : seuil en rapport = 0x5653A - 0x56548[rapport] (décalages nuls) ; au point mort
0x5653A - 0x56546 (2500).

  python3 rupteur.py entree.bin sortie.bin [regime_coupure=6800]
"""
import sys

import marelli4mv as m


def reglages(cut):
    return [
        (0x5653A, [cut, cut], 'coupure injection (haut / bas)'),
        (0x57CAC, [cut + 300, cut + 150, cut - 300, cut + 300, cut + 150, cut + 400],
         'limiteur couple : début, relâche, bas de rampe, régulateur on/off, maxi (au-dessus de la coupure)'),
        (0x5B8EA, [cut], 'reprise de l\'injection après coupure de régime (fct 0x46782 : coupe 100 % '
                         'des injections au seuil et ne réinjecte que sous cette valeur ; 5610 d\'origine)'),
        (0x56542, [max(7300, cut + 500)], 'seuil du défaut de surrégime'),
        (0x5BA32, [5900], 'fin de la régulation de cliquetis : 5900 comme l\'origine et la ROM nom long '
                          '(au-delà, détection non calibrée -> faux cliquetis, retard d\'allumage)'),
    ]


def main():
    src, dst = sys.argv[1:3]
    cut = int(sys.argv[3]) if len(sys.argv) > 3 else 6800
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
