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

### Apprentissage `$1740` (débloqué en v5h)
- Bornes : 0x57028 = +13, 0x5702A = −15 (en 0,1 % d'angle) → besoin −10 dans les bornes.
- Uniquement au ralenti stable : pédale relâchée, moteur chaud, régime à moins de 80 tr/min de la consigne,
  STFT (`$107E`) dans ±20 % ; le LTFT n'est pas testé (sauf s'il est en butée, le STFT dérive alors).

### À refaire après la v5h
Après 5–10 min de ralenti chaud : mêmes relevés (régime, angle, pression, clim éteinte / en route).
L'écart modèle / mesure doit tomber vers 0, l'angle au ralenti peut légèrement changer.
