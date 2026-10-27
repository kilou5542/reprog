#!/usr/bin/env python3
"""Analyse d'un log VCDS en mode OBD (PID 0C régime, 06 STFT, 07 LTFT, 0B MAP) pour la VE 0x57084.

Formules de CE calculateur (mode 01, fct 0x4B642 / 0x4B694) : brut 40000 = neutre, carburant x 40000 / brut.
  PID 06 STFT % = (brut - 40000) / 100   (4 fois l'échelle VCDS ; butée 50000 -> 99 %)
  PID 07 LTFT % = (brut - 40000) / 200   (2 fois l'échelle VCDS)
Positif = le calculateur RETIRE de l'essence. Facteur appliqué f = 40000/brut_STFT x 40000/brut_LTFT :
f < 1 = base trop riche -> VE trop haute.
Points gardés : stables (régime ±150 et MAP ±4 kPa entre voisins), LTFT publiée (≠ 0), |STFT| ≤ 25.

  python3 analyse_log_ve.py log.csv
"""
import csv,statistics as st,collections,sys
F=sys.argv[1]
R=[]
for row in list(csv.reader(open(F,encoding='latin-1')))[4:]:
    try: R.append(tuple(float(row[i]) for i in (1,2,4,6,8)))
    except: pass
keep=[]
for i in range(1,len(R)-1):
    t,rpm,s,l,m=R[i]
    a,b=R[i-1],R[i+1]
    if l==0.0 or abs(s)>99: continue
    if abs(b[1]-a[1])>150 or abs(b[4]-a[4])>4: continue
    f=40000/(40000+100*s)*40000/(40000+200*l)
    keep.append((rpm,m*10,s,l,f))
print('points stables gardés',len(keep),'/',len(R))
# bins VE
RPM=[600,700,800,900,1000,1100,1200,1300,1500,1800,1900,2100,2400,2800,3000,3300,3600,3800,4200,4600,5000,5200,5600,6000]
MAP=[150,200,250,300,350,450,500,550,650,800,900,1020]
near=lambda ax,v:min(range(len(ax)),key=lambda i:abs(ax[i]-v))
cells=collections.defaultdict(list)
for rpm,m,s,l,f in keep: cells[(near(RPM,rpm),near(MAP,m))].append(f)
print('\nFacteur carburant appliqué (1.00 = rien) : moyenne [nb points], lignes = régime, colonnes = MAP mbar')
print('      '+''.join(f'{x:>9}' for x in MAP))
for i,r in enumerate(RPM):
    line=''
    for j in range(len(MAP)):
        v=cells.get((i,j))
        line+=f'{st.mean(v):6.2f}[{len(v):1d}]' if v and len(v)<10 else (f'{st.mean(v):6.2f}[+]' if v else '        .')
    if any(cells.get((i,j)) for j in range(len(MAP))): print(f'{r:5} '+line)
# par MAP global
print('\nPar tranche de MAP (tous régimes) : facteur moyen, STFT, LTFT')
bym=collections.defaultdict(list)
for rpm,m,s,l,f in keep: bym[int(m//100*100)].append((f,s,l,rpm))
for k in sorted(bym):
    v=bym[k]; print(f'{k:5}-{k+99} mbar : f={st.mean(x[0] for x in v):.2f}  STFT={st.mean(x[1] for x in v):+5.1f}  LTFT={st.mean(x[2] for x in v):+5.1f}  n={len(v)}  rpm moy {st.mean(x[3] for x in v):.0f}')
