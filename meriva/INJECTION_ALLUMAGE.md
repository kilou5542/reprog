# Injection et allumage — Delphi Z16XE (12230554 / EZ)

Toutes les tables trouvées, avec la chaîne de calcul qui les utilise. Les adresses sont des offsets
dans le fichier `.ori` ; les valeurs d'origine sont dans [VALEURS_ORIGINE_JEU0](VALEURS_ORIGINE_JEU0.md)
et [VALEURS_ORIGINE_JEU1](VALEURS_ORIGINE_JEU1.md). Définitions exploitables : `scripts/tables.py`.

**Deux jeux de tables.** Beaucoup de tables existent en deux exemplaires choisis par l'option de
configuration `$9808` (jeu 0 si `$9808 = 0`). `$9808` vaut 1 quand `($82BC & 6) == 2`, octet venant
de l'EEPROM. **Le jeu utilisé par la voiture n'est pas connu : modifier les deux.** Pour le savoir,
logguer l'avance en OBD : à 2000 tr/min et 100 kPa, le jeu 0 donne 4,9° et le jeu 1 donne 7,0°.

---

## 1. Chaîne de calcul du carburant (vérifiée)

```
masse_carburant = masse_air x 10 / AFR_cible         (0x11D56 ; AFR_cible = $8AFC, AFR x 10)
temps = masse_carburant x constante_injecteur / 0x431C x corrections  (0x1075A)
      + temps mort ($8B50), puis x facteur tension batterie ($8B40)
```
- **Constante injecteur 0x07BE** : 9 mots, axe = dépression (pression atmosphérique − MAP),
  0 à 80 kPa par pas de 10 (rampe sans retour : plus de dépression = plus de débit).
  Le temps d'injection est **proportionnel** à cette constante.
- L'AFR cible est en **AFR x 10** (146 = 14,6:1). Plus la valeur est basse, plus c'est riche.

## 2. AFR cible

### Moteur tournant (routine 0xF4E0)
1. **Eau sous le seuil** (0x0E6A : 26,8 °C jeu 0 / 29,8 °C jeu 1 ; 0x0E68 : 30,5 °C en mode très froid) :
   AFR = table froide 2D + correction régime − enrichissement après démarrage.
   - Table froide : **0x0CA8** (jeu 0) / 0x0C32 (jeu 1), 13 températures (−40 à 104 °C) x 9 MAP (20 à 100 kPa).
   - Après un démarrage très froid (sous −34 °C) : 0x0D94 / 0x0D1E.
   - Correction régime : 0x0E6C / 0x0E7D, 17 points de 0 à 6400 tr/min, valeur − 20 en dixièmes d'AFR.
2. **Eau au-dessus du seuil** : AFR = **14,6 fixe (0x0688)** − enrichissement après démarrage.
   La sonde lambda corrige ensuite (boucle fermée).
3. **Pleine charge** (« power enrichment ») : si le papillon commandé (`$97D0`) dépasse le seuil
   **0x0F42 / 0x0F4B** (90 %, 9 points 0–6400 tr/min, hystérésis 0x0E94), l'AFR cible devient le plus
   riche entre la valeur ci-dessus et **0x0EA8** (17 régimes 0–6400 x 9 positions 50–100 %,
   12,4 à 13,5:1), multipliée par 0x0E96 / 256 selon l'eau (255 partout = neutre).
4. **Protection catalyseur** : un modèle de température d'échappement (0x4A76 jeu 0, régime x débit
   d'air ; jeu 1 vide), corrigé par l'AFR et l'avance, déclenche un enrichissement quand il dépasse
   un seuil : AFR maxi 0x0E0A / 0x0E1B (14,2 → 11,0 selon l'excès).

### Démarrage (moteur pas encore tournant)
- **AFR de lancement = table 0x0E32 (jeu 1 : 0x0E3F) − enrichissement initial 0x0F70 / 0x0F71.**
  Table de 13 points, eau de −28 à 116 °C : 2,4 → 12,0:1.
- Enrichissement initial 2,0 d'AFR, qui décroît (facteur 0x0E30 / 0x0E31, période 0x0F72 / 0x0F73).
- **Impulsion d'amorçage 0x07D2 / 0x07F4** : 17 mots (eau −40 à 152 °C), un tir simultané sur les
  4 injecteurs à la mise en route (routine 0x1F9F8 → 0x372E6, canal 5 = tous). Unité : ticks TPU,
  raisonner en pourcentage. Non corrigée par la constante injecteur.
- **Enrichissement après démarrage 0x0BE4 / 0x0BF1** (13 points, −28 à 116 °C, en AFR retiré),
  0x0BFE / 0x0C0B en mode très froid (eau < −34 °C, seuil 0x0668) ; décroissance : périodes
  0x0C18 / 0x0F54 selon l'eau, facteur 0x0E8E.
- **Noyage** : pédale ≥ 95 % (0x0F6F) pendant le lancement → AFR forcé à 8,0 (0x0F6E).

## 3. Allumage (routine 0x15F86)

Unité : **degrés = (octet − 64) x 0,3516** (90/256 ; confirmé par la réponse OBD PID 0E).

```
avance = principale (ou ralenti) + corr. eau + corr. air + corr. baro + corr. AFR + adaptatif
         − retraits (sécurité ; retrait anti-cliquetis normal pas encore localisé), bornée entre 0x1361 (−10,9°) et 0x1362 (+49,9°)
```
| Table | Jeu 0 | Jeu 1 | Lignes x colonnes |
|---|---|---|---|
| **Avance principale** | **0x16A8** | **0x15F8** | 16 régimes (400–6400) x 11 MAP (20…80, 85, 90, 95, 100 kPa) |
| Avance ralenti | 0x142A | 0x1390 | 17 régimes (0–3200 par 200) x 9 MAP |
| Avance ralenti, variante | 0x155E | 0x14C4 | idem |
| Avance ralenti, 3e variante | 0x17AA | 0x1758 | 9 régimes (0–3200 par 400) x 9 MAP |
| Correction eau | 0x19DC | 0x1966 | 13 températures (−28 à 116 °C) x 9 MAP |
| Correction air admis | 0x18A4 | 0x182E | 13 températures (−28 à 116 °C) x 9 MAP |
| Correction pression atmosphérique | 0x1942 | 0x191E | 4 baro (75–105 kPa) x 9 dépressions |
| Correction selon l'AFR cible | 0x1A7E | — | 8 régimes (800–6400) x 7 AFR (10 à 16) |
| Avance au lancement | 0x1376 | 0x1383 | 13 températures |
| Retrait si capteur cliquetis en défaut | 0x17FC | 0x1807 | 11 MAP |
| Tables adaptatives (0x1140, 0x11C8, 0x1250, 0x12D8) | — | — | toutes à 0 : inactives |

L'axe MAP de la table principale est dilaté au-dessus de 80 kPa (pas de 5 kPa).
L'avance pleine charge d'origine est basse entre 2000 et 4400 tr/min (5 à 9°) : calibration limitée
par le cliquetis sur l'essence ordinaire. C'est là que l'E85 peut apporter du gain.

## 4. Méthode envisagée pour l'E85 (non essayée sur la voiture)

1. Multiplier **0x07BE** par environ 1,40 (stœchio E85 ≈ 9,8 contre 14,6 ; E70–E85 réel → 1,35–1,45).
   Les tables d'AFR restent alors en « AFR équivalent essence » ; **garder 146 en 0x0688**.
2. Ne pas diviser en plus les tables d'AFR (double enrichissement).
3. Enrichissement à froid propre à l'éthanol : baisser 0x0E32 sous ~20 °C (−20 à −40 %), augmenter
   0x0F70, l'impulsion d'amorçage 0x07D2 / 0x07F4 (+40 % + supplément à froid) et 0x0BE4 / 0x0BFE à froid.
4. Avance : +1 à 2° par palier sur les colonnes 80–100 kPa entre 2000 et 4800 tr/min, uniquement en
   E85, en logguant.
5. Recalculer le checksum (`scripts/fix_checksum.py`).
