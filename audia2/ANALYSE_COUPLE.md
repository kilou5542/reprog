# Structure de couple du 4MV CA (analyse du code, en cours)

Objectif : comprendre le chemin demande de couple → air → papillon, pour reconstruire les tables
selon le matériel (et traiter frein moteur / à-coups en descente / mollesse). Adresses = code CA.

## 1. Demande du conducteur
- Fct 0x3A638 → `$E8E` : cartes **0x5A26C** et **0x5A06C** (16 × 16 : lignes régime axe 0x561FC,
  colonnes pédale ‰ axe 0x56350), mélangées par `$E8A` (0–1000) selon le mode `$E99`.
- Pédale relâchée (colonne 0) en v5g : 0 de 650 à 900 tr/min, −20 à 1000, −58 à 1250, −106 à 1500,
  −193 à 2000… (demande déjà négative = frein moteur demandé). La CA-DR est décalée d'environ +150.
- 0x3A8AA : `$E96` = max(demande conducteur `$E8E`, demande régulateur de vitesse `$212`).
  (0x3A8FA calcule une « pédale équivalente » `$E8C` uniquement pour le régulateur / CAN.)

## 2. Régulation du ralenti
- Consignes de **régime** (et non d'air) : `$177E` / `$1778` → `$180E` / `$1810` (affichées en tr/min
  par VCDS, 0x8C38). 0x56F12 = 680 tr/min (base), 0x56E80 = 1500 (max), 0x56C58 = consigne chaude (850).
- Réserve de **couple** du ralenti `$1776` (0x21380) = base `$177A` (cartes 0x56A18 régime × charge et
  0x56B18 régime × température, nulle à chaud) + correction PI + clim `$E6530` + tension `$17EC`,
  bornée 0x56E7A (0) … 0x56E78 (1000) ; `$1816` = `$1776` + adaptation `$E403E/$E4040`, ≤ 0x5700E (1000).

## 3. Limite de couple réalisable et amortisseur d'à-coups (0x31900–0x32400)
- 0x32094 : limite `$1230` = `$E77CC` × (1000 − `$E76FA`)/1000 − `$E6536` ; `$1232` = min(`$E96`, `$1230`).
- 0x32122 : `$1232` × 955 / 0x58678[rapport `$1224`] → **régime de référence** `$1234` ; `$1226` = régime moteur,
  `$1228` = écart → amortisseur d'à-coups de la transmission (pas la conversion vers l'air).
- 0x31FBE : couple lissé `$126C` (coefficients 0x5857C / 0x585FA), sert à autoriser la coupure
  en décélération (écart `$1272` < 0x5AA7A) ; voir v5g.

## 4. Modèle de couple (rendement d'allumage)
- 0x10D8C : **0x55EB8** (24 × 12, régime × charge, mêmes axes que l'avance) = **avance optimale** (MBT,
  ×0,1°) ; écart avec l'avance réelle (`$E59E2`) → table 0x560F8 (axe 0x56128) → rendement `$1F8A`.
  ⚠️ Dans le XDF elle est appelée « Couple 0x55EB8 » : c'est en réalité l'avance optimale du modèle.
  Elle a été reprise de la ROM « nom long » en v4.

## 5. Chaîne demande de couple → charge → papillon (identifiée)
1. **0x3C002** : `$DC8` = borne(**0** … 10000, couple conducteur lissé `$126C` + réserve ralenti `$1954` (= `$1816`)
   + `$1956`). ⚠️ **La demande totale ne peut pas être négative** : pédale relâchée au-dessus du ralenti,
   la demande conducteur négative est ramenée à 0 (pas de « couple négatif » demandé).
2. **0x26930** (limiteur de régime) : `$160C` = min(`$DC8`, limiteur, couple max disponible `$2060`).
3. **0x37F40** : `$FA0` = `$160C` ± interventions ESP/ASR (`$1350`, `$1352`).
4. **0xD820** : `$2054` = `$FA0` / (1 − perte d'avance `$1F8A`/1000), ≤ 10000 ; dans le mode `$E4032` = 1,
   montée ≤ 0x5580A par cycle et plafond 0x55808.
5. **0xDA3E / 0xDAB6** : demande normalisée `$2050` = `$2054` × 50000 / couple max (0x55668, selon le régime) ;
   **charge de consigne `$2056` = max( 0x55688(régime, `$2050`) , 0x557E8(régime) )**.
6. **0x3B2E4** : `$DF8` = `$2056` + air de purge (`$F76`), ≤ 64000 → commande du papillon.

Unités probables : couple en 0,1 Nm (couple max 0x55668 ≈ 980…1486) ; demande normalisée 50000 = 100 %
du couple max ; charge en 0,01 % (2200 ≈ 22 %).

### Air minimum moteur entraîné (demande = 0)
= max(1re colonne de 0x55688, plancher 0x557E8) :

| Régime | CA d'origine | v5g | CA-DR |
|---|---|---|---|
| 900 | 1440 | 2200 | 3511 |
| 1000 | 1397 | 2200 | 3511 |
| 1250 | 1364 | 2200 | (≈3511) |
| 1500 | 1800 | 2200 | 3511 |
| 2000 | 2600 | 2600 | 3511 |

→ en v5g, entre 900 et 1250 tr/min, ≈ +60 % d'air par rapport à l'origine quand le moteur est entraîné :
cause probable du manque de frein moteur et des à-coups en descente en 1re (avec le seuil de coupure).
Le ralenti (réserve ≈ 150–200 → demande ≈ 7–15 % du max) se situe plutôt entre les colonnes 2 et 3.

## 6. Limites de couple / air maximum (WinOLS « Maximum air filling »)
- 0xDA3E : `$2058` = couple maximum selon le régime (**0x55668**, 16 pts) ; 0xDB4A : `$2060` = couple
  maximum disponible (réductions comprises), utilisé par le limiteur de régime (0x269CA) ;
  `$2064` = `$2060` − réserve ralenti (utilisé par la clim, 0x3BAA2).
- 0xDB8C : 0x55688 lue une 2e fois avec le couple max disponible `$2060` → `$2062` = air maximum,
  utilisé par la **purge canister** (module 0x38600–0x38B50). La 1re lecture (0xDACE, ci-dessus) est la
  conversion couple demandé → charge. 0x55688 a été reprise de la ROM « nom long » en v4.

## Reste à identifier
- La conversion charge de consigne `$DF8` → angle papillon (inverse du modèle 0x57786).
- ~~Le retard d'allumage en décélération~~ : trouvé (fct 0x4E19C, voir INJECTION_ALLUMAGE.md § 2.6). Il ne sert
  qu'à l'anti-à-coups ; il n'y a pas de retard pour freiner en roue libre.
