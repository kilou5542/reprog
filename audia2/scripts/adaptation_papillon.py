#!/usr/bin/env python3
"""Débloque l'apprentissage du modèle papillon sans toucher à l'EGR.

Le modèle papillon (0x57786) est consulté avec l'angle corrigé :
    angle modèle = angle mesuré + 0x57986 - $1740 - $1742          (fct 0x22DDE)
`$1740` est appris en roulant (intégrateur `$174E`, borné entre `$1752` et `$1756`, copié en `$E4574`) à partir
de l'écart pression attendue / mesurée. Avec le capteur EGR débranché, `$DBA` (statut EGR) est en défaut et
ces deux tests remettent l'apprentissage à zéro en permanence :
    0x226BE  tst.b $DBA(a5) / 0x226C2 bne.w -> clr $174E, clr $1740
    0x23A5E  tst.b $DBA(a5) / 0x23A62 bne.w -> adaptation du modèle sautée
On remplace seulement ces deux sauts par des `nop`. `$DBA` n'est pas modifié : toute la surveillance et
l'apprentissage EGR (0x46C80-0x47F00) restent endormis, comme dans la v5 (contrairement à la v7b).

La somme du code (mot long 0x7FF74, voir marelli4mv.py) est recalculée : sans elle, la ROM ne démarre pas
(v5h, 27/10/2026). Sortie actuelle = v5i.

  python3 adaptation_papillon.py entree.bin sortie.bin
"""
import sys

import marelli4mv as m

SAUTS = ((0x226C2, '66000052'), (0x23A62, '660001da'))


def main():
    src, dst = sys.argv[1:3]
    d = m.load(src)
    for a, orig in SAUTS:
        assert d[a:a + 4] == bytes.fromhex(orig), f'0x{a:05X} : {d[a:a + 4].hex()}'
        d[a:a + 4] = bytes.fromhex('4e714e71')
        print(f'0x{a:05X} bne.w -> nop nop')
    m.fix_code(d)
    m.fix(d)
    assert m.check(d) == (True, True) and m.check_code(d)
    m.save(dst, d)
    print(f'-> {dst}, checksums et somme du code OK')


if __name__ == '__main__':
    main()
