"""Lecture d'un log VCDS en mode OBD-II, quel que soit l'ordre des PID.

Retourne une liste de tuples (temps s, régime, STFT_obd %, LTFT_obd %, MAP kPa) : PID 012 (0C), 006, 007, 011 (0B).
"""
import csv
import re

PIDS = {'012': 'rpm', '006': 'stft', '007': 'ltft', '011': 'map'}


def lire(path):
    rows = list(csv.reader(open(path, encoding='latin-1')))
    entete = rows[2]
    col = {}
    for i, c in enumerate(entete):
        mm = re.search(r'PID [A-Z] - (\d{3})', c)
        if mm and mm.group(1) in PIDS:
            col[PIDS[mm.group(1)]] = i
    manque = set(PIDS.values()) - set(col)
    if manque:
        raise SystemExit(f'{path} : PID manquants {manque}')
    out = []
    for row in rows[4:]:
        try:
            out.append((float(row[col['rpm'] - 1]), float(row[col['rpm']]), float(row[col['stft']]),
                        float(row[col['ltft']]), float(row[col['map']])))
        except (ValueError, IndexError):
            pass
    return out
