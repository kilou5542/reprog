# Injection et allumage du 4MV CA : tables et chaînes de calcul (désassemblage)

Analyse du code de la ROM d'origine CA (le code est identique dans toutes tes versions, seules les
valeurs changent). Pour chaque table : adresse, taille (lignes × colonnes), axes, unité, rôle,
fonction qui la lit. Ce qui reste incertain est marqué *(probable)*.

Conventions :
- Températures : brut − 40 = °C (axe eau 0x562EC : 10…160 = −30…120 °C).
- Avance : 0,1° vilebrequin (70 = 7°). Lambda : 0,001 (1000 = λ 1).
- Facteurs : 1000 = ×1 (‰), 1024 = ×1 ou 10000 = ×1 selon la table (précisé).
- « charge » = remplissage relatif `$16C6` en 0,01 % (axe 0x56164 : 11…96 %).
- Le « XDF » est `tunerpro/A2_4MV_036906034CA_E85.xdf`.

## Axes communs

| Axe | Points | Valeurs | Grandeur | Variable |
|---|---|---|---|---|
| 0x5619C | 24 | 600…6000 | régime | `$1E6E` |
| 0x561CC | 16 | 700…5900 | régime | `$1E70` |
| 0x561EC | 8 | 800…4300 | régime | `$1E72` |
| 0x561FC | 16 | 550…6000 | régime | `$1E74` |
| 0x5622C | 16 | 800…5500 | régime | `$1E7A` |
| 0x56164 | 12 | 1121…9643 | charge (0,01 %) | `$1E68` |
| 0x5617C | 8 | 1120…9640 | charge | `$1E6A` |
| 0x5627C | 12 | 150…1020 | pression collecteur (mbar) | `$1E80` |
| 0x56294 | 8 | 150…1020 | pression collecteur | `$1E82` |
| 0x562A4 | 12 | 500…1024 | pression atmosphérique (mbar) `$16D4` | `$1E84` |
| 0x562CC | 16 | 0…150 | température d'air (−40…110 °C) | `$1E88` |
| 0x562EC | 16 | 10…160 | température d'eau (−30…120 °C) | `$1E8A` |
| 0x5630C | 9 | 10…145 | température d'eau (−30…105 °C) | `$1E8C` |
| 0x5625C | 16 | 60…160 | tension batterie (0,1 V) | `$1E7E` |
| 0x5631E | 8 | 0…1000 | position EGR (‰) `$582` | `$1E90` |
| 0x56144 | 16 | 0…831 | angle papillon (0,1 %) | `$1E66` |
| 0x56988 | 12 | 0…800 | dépression aux injecteurs (mbar) | `$1852` |

---

# 1. Injection

## 1.1 Chaîne de calcul

```
pression collecteur ──► charge d'air $16C6 (fct 0x22FF6)
                         ×  masse d'air maxi $16C4  ──►  masse d'air par cylindre $16C0
λ cible (0x3306C) ─► rampe (0x33402) ─► + offsets λ ─► λ final $2034
masse carburant $1030 = masse d'air / (λ × 14,5)           (fct 0x376B8, 14,5 = 0x59768)
   × enrichissement de démarrage      (0x59742, décroissance 0x59754)
   → modes démarrage / reprise après coupure (0x378FC, 0x37B9A)
   × correction adaptative (LTFT, 0x532A8)  × STFT ($107E, 40000 = neutre)
   → film de paroi (fct 0x31382)  × facteur limiteur $15D4
   → coupures (ASR, limiteur, cylindres)
temps d'injection (fct 0x2AAF0) = masse × gain(dépression) × corr. tension + temps mort
phase d'injection 0x5B668
```

## 1.2 Charge d'air (fct 0x22FF6) — base de l'injection

1. Pression utile = MAP − gaz résiduels (`$16D4` × 100 / **0x57058** = 1533), × **0x5705A** (8520) / 1000.
2. × **VE 0x57084** (24 × 12, régime × MAP, 10000 = ×1) → `$16D8`.
3. Correction de dynamique collecteur (remplissage / vidange) : **0x572C4** (24 × 12, régime × MAP),
   pondérée par **0x57AA6** (16, temp. d'air, 1000 = ×1) et par la dérivée de pression `$16F0`.
4. × **0x57504** (16 × 12, temp. d'eau × MAP, 10000 = ×1) → densité selon la température du moteur
   (« Correction air / température d'eau » du XDF).
5. − part **0x57686** (16 × 8, régime 0x561CC × MAP 0x56294, ‰, si 0x57AC8 = 1). Elle vaut 0 partout
   *(probable : gaz recirculés internes)*.
6. Résultat : charge `$16C6` (0,01 %), puis masse d'air `$16C0` = `$16C4` × `$16C6` / 10000, et débit
   d'air `$16CC` en kg/h.

Le modèle papillon (0x57786) n'entre pas dans ce calcul. Il sert au diagnostic P1553 et à la
commande du papillon. Sa correction d'angle **0x57986** (8 × 16, position EGR × angle) vaut 0 partout,
et **0x57A86** (16, temp. d'air) est son facteur 0,90…1,15.

## 1.3 Lambda cible (fct 0x3306C, paramètres fct 0x3332C)

| Table | Taille / axes | Rôle |
|---|---|---|
| **0x58B00** | 24 × 12, régime × charge | λ de base (XDF ✓) |
| **0x58D40** | 24 × 12, régime × charge | **λ moteur froid** (0,850 partout). Utilisée seulement si eau < 20 °C (0x58F80 = 60), mélangée avec le poids **0x58F82**. ⚠️ Le XDF l'appelle « protection composants » : c'est faux. |
| **0x58F82** | 16, temp. d'eau | poids du λ froid : 1000 à −30 °C, 800 à −20 °C, 200 à −10 °C, 0 au-dessus |
| **0x590E2** | 9, temp. d'eau (0x5630C) | λ le plus riche autorisé au-dessus de 1050 tr/min (0x590F4) : 0,900 à froid, 0,993 à chaud |
| **0x59046** | 24, régime | λ pleine charge (XDF ✓), appliqué progressivement selon `$2010` |
| **0x55BEE / 0x55BCE** | 16, régime (0x561CC) | angle papillon de début (77 %) et de fin (79 %) du passage en pleine charge (`$2010` de 0 à 1000) |
| **0x5907A** | 16, régime (0x5622C) | seuil de charge de l'enrichissement lié au retard d'allumage |
| 0x59076, 0x590C0, 0x5909B/C | constantes | enrichissement quand l'avance est retardée (cliquetis, air chaud) : `$11EA` |
| 0x590C8…0x590E0 | constantes | régulation λ pleine charge par la sonde (gains à 0 : inactive) |
| 0x59078, 0x590C2, 0x590C4 | constantes | facteurs finaux (1000 = neutre ; 0x590C4 = 1100 si ASR active) |
| 0x590F6…0x59100 | constantes | rampes de transition du λ (fct 0x33402) |

Après-démarrage (fct 0x32F36, valeurs selon la temp. d'eau 0x562EC) : **0x58FA2** (valeur de départ),
**0x58FC2**, **0x58FE2**, **0x59002**, **0x59024**, **0x5909E** (pente de décroissance /1024),
0x59022 (cadence) et 0x59044.

## 1.4 Masse de carburant et démarrage

| Table | Taille / axes | Rôle |
|---|---|---|
| **0x59768** | constante = **145** | **rapport stœchiométrique × 10 (14,5)**. Inchangé dans tes ROM : l'E85 est porté par le gain injecteur (voir § 1.9). Lue aussi par le modèle de température d'échappement (fct 0xEF08). |
| **0x59742** | 9, temp. d'eau | enrichissement de démarrage (multiplie λ ; 287/1024 à −30 °C, 1024 = neutre). Actif après un démarrage à froid. |
| **0x59754** | 9, temp. d'eau | vitesse de disparition de l'enrichissement 0x59742 |
| **0x59708** | 16, temp. d'eau | amorçage au lancement « Craaaaanking » (XDF ✓) |
| **0x59728** | 12, pression atmosphérique | correction d'altitude du lancement (1000 partout) |
| 0x5976A, 0x597A0, 0x5978E, 0x5977C | 1D | paramètres de la séquence de lancement (fct 0x378FC) |
| 0x597B4…0x597CE | constantes | reprise de l'injection après une coupure : rampes, nombre de cycles (fct 0x37B9A) |
| **0x5B8B6** / **0x5B8D6** | 16 / 9, temp. d'eau | budget d'amorçage (XDF ✓) / *(probable)* sa limite (fct 0x457EE) |

## 1.5 Film de paroi (fct 0x31382) — compensation en accélération / décélération

Modèle « X-τ » par cylindre. Quatre cartes 16 × 8 (régime 0x561CC × MAP 0x56294) : **0x580EA**
et **0x581EA** (moteur froid), **0x582EA** et **0x583EA** (moteur chaud). Le mélange froid / chaud
se fait avec **0x584EA** et **0x5850A** (16, temp. d'eau). En décélération forte : **0x5853C** et
**0x5855C** (16, régime). Interrupteurs : 0x580E6, 0x580E7, 0x580E8.

Ces cartes jouent beaucoup sur les à-coups et les trous à la reprise. Avec l'E85, qui s'évapore moins
bien à froid, ce sont elles qu'il faudra retoucher si tu as des trous à froid.

## 1.6 De la masse au temps d'injection (fct 0x2AAF0, 0x1FEC2)

| Table | Taille / axes | Rôle |
|---|---|---|
| **0x569A0** | 12, dépression aux injecteurs (axe 0x56988) | **gain injecteur** (µs par unité de masse, /256) : le débit dépend de la dépression, car le régulateur n'est pas relié au collecteur (XDF ✓, porte E85 + injecteurs 0280158170) |
| **0x56970** | 12, même axe | correction du temps mort selon la dépression |
| **0x57E74** | 16, tension batterie | **temps mort injecteur** (1498 à 6 V … 59 à 13 V … 13 à 16 V) |
| **0x57E94** | 16, tension batterie | correction de débit selon la tension (1024 partout = neutre) |
| **0x57E72** | constante 1229 (×1,2) | ⚠️ XDF « facteur démarrage » : en réalité appliqué peu après un **redémarrage moteur chaud** (eau ≥ 70 °C, 0x55C82 ; durée 0x55C84) *(probable : vapeur dans le rail)* |
| 0x57E6A / 0x57E6E | 400 | impulsion minimale |
| 0x57E6C / 0x57E70 | 200 / 500 | seuils sous lesquels l'injection est supprimée (modes coupure) |
| **0x5B668** | 24 × 12, régime × charge | **phase d'injection** (angle de fin d'injection) ; 0x5B666 = 180 au démarrage |

Dépression aux injecteurs = pression atmosphérique − pression collecteur (tenant compte de la phase).

## 1.7 Boucle fermée (sonde) et adaptations

- STFT `$107E` (40000 = neutre) : fct 0x36C32. Gains et retards : **0x59550** (8 × 8, régime
  0x59530 × MAP 0x59540), **0x59624** (8 × 8, régime × MAP), 0x59520, 0x596E0, 0x595E0…0x59606.
  Butées 0x596BC / 0x596BE (XDF ✓).
- Régulateur large bande (offset λ `$201E`) : fct 0x35F82.
- LTFT par zones : fct 0x532A8, axes MAP 0x5CE84 et régime 0x5CE74, butées 0x5CEA0 / 0x5CEA2 (XDF ✓).

## 1.8 Interventions sur l'injection

- Limiteur de régime / couple (fct 0x26D96, 0x26E84) : facteur carburant `$15D4` (0x57D46…) et retard
  `$15C4`, tables **0x57D2C** (temp. d'eau), **0x57CE4** et **0x57D04** (régime).
- Coupure en décélération : voir ANALYSE_COUPLE.md et v5g.
- Coupure de cylindres ASR : motifs 0x540F4 (code).

## 1.9 E85 : stœchiométrie 0x59768 ou gain injecteur 0x569A0 ?

Pour le carburant calculé à partir de l'air (cas normal), les deux donnent le même temps d'injection :
temps = air / (λ × AFR) × gain. Mais le calculateur ne fait pas que ce calcul :

| Point | Gain injecteur × 1,45 (ta ROM) | AFR 0x59768 = 98 |
|---|---|---|
| Carburant calculé depuis l'air | ✓ | ✓ identique |
| Masses fixées par table (lancement 0x59708, budget 0x5B8B6, impulsions de démarrage) : elles passent par le gain (fct 0x2AAF0) | mises à l'échelle automatiquement | **pas** mises à l'échelle : à multiplier à la main |
| Modèle de température d'échappement (fct 0xEF08 : débit carburant = débit d'air / (λ mesuré × 0x59768), axe 0x55DD4, cartes 0x55C98 / 0x55D88) | inchangé : l'énergie par kg d'air est presque la même à l'E85 qu'à l'essence, le modèle reste juste | débit ×1,48 : le modèle se décale |
| Grandeurs qui lisent la masse de carburant `$202A` en valeur absolue : purge canister (fct 0x39444), seuils de la régulation λ (0x35CAC, 0x35D10, 0x353AA / 0x594E6), seuil du film de paroi 0x58538 | restent calibrés « essence » | décalés de ×1,48 |
| Consommation affichée (cumul de la masse `$62E`) | à corriger par 0x5BA22 (fait : 541) | 0x5BA22 = 785 directement |
| LTFT / STFT (multiplicatifs), temps morts, impulsion mini (en temps, après le gain) | identique | identique |

Conclusion : le gain injecteur est la méthode la plus cohérente ici. Pour le calculateur, tout reste
en « équivalent essence » ; seule la conversion finale en temps change. Avec l'AFR, il faudrait en plus
recaler le lancement, le modèle d'échappement et quelques seuils.

---

# 2. Allumage

## 2.1 Chaîne de calcul (fct 0x4C744)

```
Lancement :            avance = 0x5BA54 (temp. d'eau)
Moteur tournant :
  base (fct 0x4CE3A) :
     ├─ pleine charge ($16D0) : 0x5BCAE si 0x5C5EE, sinon 0x5BA66
     ├─ 1re / embrayage ($2DE) : 0x5C5F0, bornée à base ± 1,5° et ≤ base
     └─ sinon : mélange base 0x5BA66 ↔ avance de ralenti (0x5BD6E/0x5BF1E + 0x5BD9E + 0x5C5BA − réserve)
  × intervention limiteur ($15C0, $15C4)                         → $270
  + correction temp. d'air 0x5BF4E                               → $26E
  + correction temp. d'eau 0x5C04E (pas au ralenti)              → $26C
  limitation de vitesse de variation (0x5C114 / 0x5C116), + 0x5C128 → $2A6
  + offset clim / ralenti 0x5C55E ($298)
  + retard transitoire d'accélération (fct 0x4E504)
  − réduction de couple ESP/ASR $1F90
  + régulation du ralenti par l'avance $180C (au ralenti)
  + réduction rapide du couple anti-à-coups $2C2 (fct 0x4E19C, si $1270)
  + $F78 (purge)  + anti-à-coups 0x4E3AE (±4,5°)                 → $2A4
  + retard cliquetis par cylindre (fct 0x4D566 / 0x4DA3A)        → avance du cylindre
```

## 2.2 Avance de base et pleine charge

| Table | Taille / axes | Rôle |
|---|---|---|
| **0x5BA66** | 24 × 12, régime × charge | **avance de base** (XDF ✓) |
| **0x5BCAE** | 24 × 4, régime × charge 65…96 % (axe 0x5BCA6) | avance pleine charge (XDF ✓), utilisée si 0x5C5EE ≠ 0 |
| **0x5C5F0** | 16 × 9, régime (0x561CC) × temp. d'eau (0x5630C) | avance spécifique 1re / embrayage (0x5C710, rapport ≤ 0x5A064 = 4, `$671`), limitée à base ± **0x5C712** (1,5°) |
| **0x55EB8** | 24 × 12, régime × charge | **avance optimale (MBT)** du modèle de couple : ne règle pas l'avance, mais l'écart MBT − avance réelle donne la perte de rendement. ⚠️ XDF « Couple 0x55EB8 ». |
| **0x560F8 / 0x56110** | 12 / 12 | courbe perte de rendement (‰) ↔ retard (0…32°) |

## 2.3 Ralenti

| Table | Taille / axes | Rôle |
|---|---|---|
| **0x5BD6E** / **0x5BF1E** | 24, axe 0x5C57E | avance de ralenti selon (régime − consigne + 730) ; 0x5BD6E est choisie si `$18EF` = 1 *(probable : embrayé / point mort)* |
| **0x5BD9E** | 12 × 16, MAP × temp. d'eau | correction de l'avance de ralenti |
| **0x5C5BA** | 12, pression atmosphérique | correction d'altitude (−10° à 500 mbar, 0 à 1024) |
| 0x5C5D2 / 0x5C5D4 | 500 / 30 | retard proportionnel à la réserve du ralenti `$1814` (maxi 3°) |
| 0x5C5E4…0x5C5EC | constantes | passage base ↔ ralenti (vitesse 0x5C5E6 / 0x5C5E8) |
| **0x5C1D8 / 0x5C1CA** | 7, écart de régime (axe en RAM `$2B6`, fct 0x4E880) | bornes haute et basse de l'avance pour la régulation rapide du ralenti |
| **0x5C1F4 / 0x5C1E6** | 7 | idem, variante (clim / moteur chaud 0x5C1C9) |
| **0x5C210** | 8, MAP | plafond de la borne haute |
| **0x5C55E** | 8, axe 0x56E98 | offset clim / ralenti `$298` ; 0x5C55C = −3° |

## 2.4 Corrections de température

| Table | Taille / axes | Rôle |
|---|---|---|
| **0x5BF4E** | 16 × 8, temp. d'air × charge (0x5617C) | correction air chaud (0 → −8° à 110 °C). Elle déclenche aussi l'enrichissement 0x5909C. |
| **0x5C04E** | 9 × 8, temp. d'eau × charge | correction moteur froid (+8° à −30 °C, 0 à chaud) |
| **0x5BA54** | 9, temp. d'eau | avance au lancement (12° à −30 °C, 6° à chaud) |
| **0x5C0E4** | 24, régime | avance de démarrage / sortie de lancement (fct 0x4D3BA), rampe 0x5C118, durée 0x5C5D6 |

## 2.5 Cliquetis (fct 0x4D566, 0x4DA3A, 0x4DED8)

| Table | Taille / axes | Rôle |
|---|---|---|
| **0x5C152** | 16, régime (0x5622C) | pas de retard par détection (−1,8° … −3,2°) |
| **0x5C192** | constante −140 | retard maximal par cylindre (−14°) |
| **0x5C172** | 16, régime | durée de maintien avant de remonter (remontée de +0,5° par pas) |
| **0x5C12C** | 16, régime | retard de sécurité appliqué à tous les cylindres (−12°) *(probable : capteur de cliquetis en défaut)* |
| **0x5C220** | 24 × 12, régime × charge | ⚠️ **seuil d'accélération** (variation d'angle papillon sur 5 échantillons, 0,1 %) : si un cliquetis survient moins de 0x5C460 après une accélération plus forte que ce seuil, le pas de retard est × **0x5C462** (1,9) et appliqué aussi au cylindre suivant. Le XDF l'appelle « Avance plafond » : **ce n'est pas une avance**. |
| 0x5C1AE / 0x5C1B4 | 3 × 2 zones | zones d'adaptation du cliquetis par cylindre (régime / charge) |
| 0x5C1B6, 0x5C1BC, 0x5C1BE | constantes | adaptation (bornes) |
| **0x5BA32** | 5900 | régime au-delà duquel la régulation de cliquetis s'arrête (XDF ✓) |

## 2.6 Interventions de couple par l'allumage

- **Anti-à-coups / réduction rapide** (fct 0x4E19C, actif si `$1270` ≠ 0, demandé par le module
  0x31900–0x32600) : retard calculé avec la courbe de rendement 0x560F8 / 0x56110, plafonné par
  0x5C558 / 0x5C55A (+3°) et limité par **0x5C466** (16 × 7, régime × niveau de réduction) ×
  **0x5C546** (9, temp. d'eau). C'est le retard qui manquait dans ANALYSE_COUPLE.md : il ne sert pas
  à freiner en roue libre, mais à amortir les à-coups de transmission.
- Retard transitoire d'accélération (fct 0x4E504) : 0x5C570 (durée), 0x5C574 / 0x5C576 (seuils),
  0x5C57A (pente).
- Anti-à-coups bornes ±4,5° (fct 0x4E3AE) : 0x5C5DA…0x5C5E2.
- Limiteur de régime : `$15C0` / `$15C4` (fct 0x26D96).

---

# 3. Ce que ça change pour toi

1. **Trois noms faux dans le XDF** (sans conséquence tant qu'on ne les modifie pas) :
   - 0x58D40 = λ **moteur froid**, pas protection composants ;
   - 0x55EB8 = avance **optimale** du modèle de couple ;
   - 0x5C220 = **seuil d'accélération** pour le retard de cliquetis, pas une avance.

   0x5C220 a été modifiée dans ta ROM (165 valeurs sur 288, reprises de la ROM « nom long »,
   probablement comme si c'était une carte d'avance). Effet : le retard renforcé en accélération ne
   se déclenche plus aux mêmes moments. **À remettre d'origine** lors d'une prochaine version (pas
   maintenant).
2. **E85** : la stœchiométrie 0x59768 est restée 14,5 ; le ×1,45 est dans le gain injecteur 0x569A0.
   Ce n'est **pas strictement équivalent** à mettre 0x59768 à ~98 (voir § 1.9) ; garder 14,5 et
   corriger le gain est le choix le plus cohérent sur ce calculateur. Les tables qui comptent
   vraiment pour l'E85 en plus : film de paroi (0x580EA…0x583EA) et enrichissement de démarrage
   (0x59742, 0x58FA2…).
3. **Frein moteur** : le calculateur ne retarde pas l'allumage pour freiner en roue libre (0x4E19C
   n'agit que pour l'anti-à-coups). La piste reste l'air minimum 0x55688 / 0x557E8.

## Tables modifiées par rapport à l'origine CA (v5f)

| Table | Valeurs modifiées | Rapport v5f / origine |
|---|---|---|
| 0x57504 corr. temp. d'eau | 136 / 192 | 0,94 … 1,20 |
| 0x569A0 gain injecteur | 12 / 12 | 0,90 … 0,93 |
| 0x58B00 λ de base | 161 / 288 | 0,88 … 1,05 |
| 0x59046 λ pleine charge | 24 / 24 | 0,93 … 0,99 |
| 0x59708 lancement | 16 / 16 | — |
| 0x5B8B6 budget d'amorçage | 16 / 16 | — |
| 0x5BA66 avance de base | 288 / 288 | — |
| 0x5BCAE avance pleine charge | 72 / 96 | — |
| 0x55EB8 avance optimale | 214 / 288 | 1,00 … 1,38 |
| 0x5C220 seuil d'accélération | 165 / 288 | — |
| 0x55688 couple → charge | 176 / 176 | 0,96 … 3,22 |

Toutes les autres tables listées ici sont d'origine CA dans la v5f.
