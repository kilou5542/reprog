"""Résumé d'une fonction : tables, constantes, appels, écritures RAM.   python3 -I bref.py 33402"""
import re
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import T, dump, func_of
for x in sys.argv[1:]:
    a = int(x, 16)
    f = a if a in T else func_of(a)
    print(f'==== {f:05x}')
    for l in dump(f).split('\n'):
        if re.search(r'TBL|jsr|bsr|pea|\.l\{|, \$[0-9a-f]+\(a5\)$|rts', l) and not re.search(r'cmp.w +-\(a0\)|dbcc|addq|adda', l):
            print(l)
