# Mesures sur la voiture

## 26/10/2026 — ralenti chaud, ROM v5g (apprentissage du modèle papillon encore bloqué)

Moteur à 90 °C, VCDS.

| Situation | Régime | Angle papillon (VCDS) | Pression collecteur |
|---|---|---|---|
| Clim éteinte | 870 tr/min | 2,35 – 2,75 % (moy. 2,55 %) | **32 kPa** (320 mbar) |
| Clim en route | 930 tr/min | 4,31 – 4,71 % (moy. 4,51 %) | **41 kPa** (410 mbar) |

Consigne de ralenti (0x56C58, boîte manuelle) : 850 tr/min à 90 °C. Pression normale pour un 1.4 16V sain
(pas de prise d'air).

### Comparaison au modèle papillon (0x57786)
Hypothèse : axe d'angle du modèle en 0,1 % (= % VCDS × 10). Pression attendue à l'angle mesuré :

| Table | Clim éteinte (mesure 320) | Clim en route (mesure 410) |
|---|---|---|
| CA d'origine (44 mm) | 241 (+79) | 354 (+56) |
| ROM nom long | 248 (+72) | 393 (+17) |
| v5g (Golf 52 mm) | 244 (**+76**) | 393 (+17) |
| Golf DR | 233 (+87) | 393 (+17) |

Même la table d'origine montre l'écart : il est normalement absorbé par la correction d'angle apprise `$1740`
(angle modèle = angle + 0x57986 − `$1740` − `$1742`, fct 0x22DDE), remise à zéro en permanence tant que le
capteur EGR débranché met `$DBA` en défaut. Correction nécessaire ≈ −1,0 % d'angle.

### Diagnostic P1553 (chemin 0x33, VAG 01553, OBD P0106) — fct 0x404EC
- Défaut si |pression modèle filtrée − pression mesurée| > tolérance.
- Tolérance 0x5AF48 : 140 mbar en stabilisé, 200 mbar en dynamique ; + 30 (0x5AF5A, véhicule lent),
  + 80 décroissant après certains événements (0x5AF6A), + 60 si mesure < modèle (0x5AF6C).
- Écart permanent constaté ≈ +80 mbar → marge réduite à 60–90 mbar : P1553 probable dans les transitions
  à bas régime.

### Apprentissage `$1740` (débloqué en v5i)
- Bornes : 0x57028 = +13, 0x5702A = −15 (en 0,1 % d'angle) → besoin −10 dans les bornes.
- Uniquement au ralenti stable : pédale relâchée, moteur chaud, régime à moins de 80 tr/min de la consigne,
  STFT (`$107E`) dans ±20 % ; le LTFT n'est pas testé (sauf s'il est en butée, le STFT dérive alors).

### À refaire après la v5i
Après 5–10 min de ralenti chaud : mêmes relevés (régime, angle, pression, clim éteinte / en route).
L'écart modèle / mesure doit tomber vers 0, l'angle au ralenti peut légèrement changer.

## 27/10/2026 — v5i, premier démarrage

| Situation | Régime | Angle papillon | Pression collecteur |
|---|---|---|---|
| Ralenti, clim éteinte (juste après démarrage, apprentissage en cours) | 850 tr/min | — | **29 kPa** |

Relevé VCDS (groupes 001–003), ralenti chaud, clim éteinte :

| Grandeur | Valeur |
|---|---|
| Régime | 850 tr/min (847 en groupe 002) |
| Température d'eau | 97,0 °C |
| Régulation lambda (STFT) | +4,0 % |
| Conditions réglage de base | 10111111 (un critère non rempli) |
| Charge | 16,3 % |
| Temps d'injection | 3,0 ms |
| Pression collecteur | **288,8 mbar** (v5g : 320) |
| Angle papillon (capteur 1, groupe 003) | 2,0° |
| Avance | 2,0° |

Après quelques minutes : STFT +3,0 %, pression 288,8 mbar, papillon 2,0°, avance 2,0° (stable).
Groupe 032 : « add. » **+8,0 %** (= LTFT au ralenti : le calculateur retire ~7 % d'essence), « mult. » 0,0 % (pas
encore relevé dans ce cycle : il faut rouler en charge partielle).

Clim en route (même jour, v5i) :

| Grandeur | Valeur | v5g (26/10) |
|---|---|---|
| Régime | 850 tr/min | 930 |
| Eau / air admission | 90 °C / 64 °C | — |
| STFT | +3,0 % | — |
| Conditions (groupe 001) | 10011111 (clim en route, catalyseur < 300 °C) | — |
| Charge | 28,4 % | — |
| Correction d'altitude (groupe 006) | **−2,0 %** (pression atmosphérique apprise, plausible) | — |
| Pression collecteur | **487,7 mbar** | 410 |
| Papillon | 3,8° | 4,5 % |
| Avance | **0,0°** | — |

Ralenti clim en route : **stable et régulier** (retour de l'utilisateur).

## Protocole de validation de la v5i (ex-v5h) (apprentissage du modèle papillon débloqué)

### Préparation
1. Flasher `roms/a2_ori_e85_v5i.bin`, effacer les codes défaut.
2. Apprentissage du papillon VCDS (01 → 04 → groupe 060, « ADP OK »), couper le contact 10 s.
3. Démarrer, laisser chauffer jusqu'à 80–90 °C, puis **10 min de ralenti** sans toucher à rien
   (clim éteinte, pas de consommateur) : c'est là que `$1740` s'apprend.

### Relevés à noter (même format que le 26/10)
| Moment | Régime | Angle papillon | Pression | STFT | LTFT | Codes défaut |
|---|---|---|---|---|---|---|
| Ralenti chaud, juste après chauffe | | | | | | |
| Ralenti chaud, après 10 min | | | | | | |
| Ralenti chaud, clim en route | | | | | | |
| Lendemain, ralenti chaud | | | | | | |

### Critères de validation
| Point | Attendu | Si ce n'est pas le cas |
|---|---|---|
| Démarrages (dont un moteur froid le lendemain) | normaux, sans voyant | revenir à la v5g |
| Redémarrages après avoir roulé (3 ou 4) | normaux, sans voyant | revenir à la v5g |
| Codes défaut EGR | aucun (EGR restée endormie) | noter le code, revenir à la v5g |
| Ralenti | stable, ~850–870 tr/min | noter régime et angle |
| Angle papillon au ralenti | peut baisser un peu (le calculateur compense) | — |
| STFT au ralenti | oscille dans ±5 % (condition d'apprentissage : ±20 %) | régler le mélange d'abord |
| P1553 | n'apparaît plus, y compris en transitions à bas régime | noter les conditions (régime, pédale, chaud / froid) |

La v5i est validée si, après plusieurs jours, tous les critères sont remplis : elle remplace alors la v5g
comme ROM de travail.

## 27/10/2026 — log OBD v5i (régime, STFT, LTFT, MAP), 8 min de route

Fichier : `logs/2026-10-27_v5i_obd_rpm_stft_ltft_map.csv`, analyse : `scripts/analyse_log_ve.py`.
942 lignes (~2 par seconde), 288 points stables exploitables. Facteur appliqué f (1,00 = rien ; < 1 = le
calculateur retire de l'essence, base trop riche) :

| MAP | f moyen | STFT | LTFT | Points |
|---|---|---|---|---|
| 200–299 mbar | 0,93 | +0,4 | +8,6 | 100 |
| 300–399 mbar | 0,91 | −0,1 | +12,9 | 59 |
| 400–499 mbar | 0,81 | −0,6 | +26,2 | 52 |
| 500–599 mbar | **0,73** | +5,6 | **+31,9** (proche de la butée +35) | 50 |
| 600–699 mbar | 0,78 | +16,1 | +11,4 | 14 |
| 700–999 mbar | ~0,85 | +9…18 | +4 | 13 |

- **Base trop riche partout**, surtout entre 400 et 600 mbar et vers 3000–3800 tr/min (f 0,62…0,72).
- L'erreur n'augmente pas aux faibles charges : **ce n'est pas le profil d'une erreur de temps mort** (hypothèse
  abandonnée). C'est un profil de **remplissage (VE)**, plus une part de richesse générale (gain / taux d'éthanol).
- **Pleine charge (MAP ≈ 1000)** : l'OBD affiche LTFT = 0 (pas publiée / pas appliquée) et une STFT de +13 à
  **+55 %**, au-delà de sa butée normale (±25 %) : variable à éclaircir, montées en régime non stabilisées.
  Profil marqué : maxi vers 3800–4300 tr/min, retour vers 0 à 5300 tr/min.
- Il manque des paliers stables en moyenne / forte charge pour conclure case par case.
