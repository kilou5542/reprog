"""Qui écrit / lit une variable RAM.   python3 -I qui.py 16c6 1fd4   (offsets de $xxxx(a5))"""
import collections
import re
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import A, D, func_of, norm
for v in sys.argv[1:]:
    v = v.strip('$').lower()
    ws, rs = collections.Counter(), collections.Counter()
    for a in A:
        s, m, o = D[a]
        o = norm(o)
        if f'${v}(a5)' not in o:
            continue
        ops = [x.strip() for x in re.split(r',(?![^(]*\))', o)]
        f = func_of(a)
        if ((len(ops) == 2 and ops[1] == f'${v}(a5)' and not m.startswith(('cmp', 'tst', 'btst')))
                or (len(ops) == 1 and m.startswith(('clr', 'st', 'sf', 'addq', 'subq', 'neg')))):
            ws[f] += 1
        else:
            rs[f] += 1
    print(f'${v}: écrit par', ' '.join(f'{k:05x}' for k in ws), '| lu par', ' '.join(f'{k:05x}' for k in rs))
