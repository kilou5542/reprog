#!/usr/bin/env python3
"""Relève la consigne de ralenti à froid (tables 0x56C58 et 0x56C38, axe eau 0x562EC : -30..+120 °C).

  python3 ralenti_froid.py entree.bin sortie.bin
"""
import sys
import marelli4mv as m

#        -30  -20  -10    0   10   20   30  40  50  60 ... 120 °C
AJOUT = [150, 150, 150, 150, 150, 150, 110, 50, 20, 0, 0, 0, 0, 0, 0, 0]


def main():
    d = m.load(sys.argv[1])
    for a in (0x56C58, 0x56C38):
        old = m.words(d, a, 16)
        new = [v + k for v, k in zip(old, AJOUT)]
        m.put_words(d, a, new)
        print(f'0x{a:05X}\n  avant {old}\n  après {new}')
    m.fix(d)
    m.save(sys.argv[2], d)
    print('checksums :', m.check(d))


if __name__ == '__main__':
    main()
