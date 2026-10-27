"""Désassemble la fonction qui contient chaque adresse.   python3 -I fn.py 22ff6 [4ce3a ...]
TBL(1D) = interpolation 1D (instruction TBL mal décodée par capstone). {=n} = valeur lue dans la ROM."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import T, dump, func_of
for x in sys.argv[1:]:
    a = int(x, 16)
    f = a if a in T else func_of(a)
    print(f'==== fonction {f:05x}')
    print(dump(f))
