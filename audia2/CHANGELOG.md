# Changelog — Audi A2 BBY, Marelli 4MV 036906034CA

Matériel : papillon Golf 52 mm (036 133 062 M, origine 44 mm), collecteur Polo GTI, injecteurs
Bosch 0 280 158 170, régulateur de pression 4 bar sans durite de dépression (F 026 403 006),
E85, sonde lambda large bande d'origine. Vanne EGR obturée et débranchée.

Toutes les adresses sont celles du code (mots identiques dans le fichier ; voir README).
Chaque version a un checksum correct.

## Branche actuelle (base : `audiori`, logiciel CA)

La base CA est gardée : avec la DR, le régulateur de vitesse et la climatisation ne fonctionnent pas.

### v11 — `roms/historique/a2_ori_e85_v11_NE_DEMARRE_PAS.bin` (❌ abandonnée : la voiture ne démarre pas)
- **Modèle papillon 0x57786 agrandi de +10 % de section effective** (≈ 52 → 54,5 mm équivalent),
  pour un papillon légèrement plus gros et une admission plus libre en amont, afin d'éviter le P1553.
  Calcul cellule par cellule avec l'écoulement compressible (débit papillon = débit moteur) ; les cellules
  à la pression de référence ne bougent pas, la table reste croissante selon l'angle.
  Effet : pression attendue +10 à +50 mbar à faible ouverture, presque rien près de la pleine ouverture.
- Script : `papillon_agrandi.py entree.bin sortie.bin 1.10` (facteur réglable).
- ❌ Essai : la voiture ne démarre pas. La pression modélisée (sortie `$16B2`, fct 0x22DDE) sert aussi au
  calcul de charge : +10 à +50 mbar aux petits angles / bas régimes = plus d'air calculé, donc plus de carburant
  au démarrage (noyé en E85) et/ou moins d'ouverture commandée. Ne plus modifier cette table sans logs.

### v10 — `roms/a2_ori_e85_v10.bin` (version à utiliser)
- **Consommation affichée recalée pour l'E85** : 0x5BA22 (masse volumique carburant) 740 → 541.
  Le combiné reçoit masse de carburant × 800 / 0x5BA22 ; la masse calculée porte l'E85 / 1,45
  (cf. v1), d'où 785 g/l / 1,45. Affinage : valeur × conso affichée / conso réelle.
- Script : `conso_e85.py`.
- ⚠️ Pas encore vérifié sur un plein.

### v9 — `roms/historique/a2_ori_e85_v9_regul.bin`
Régulateur de vitesse : il prenait de la vitesse en descente.
- **Butées négatives du correcteur PI élargies** (fct 0x4EB02) :
  P 0x5C778 −160 → −480, I 0x5C77C −1280 → −8000 (environ −10 → −62 Nm).
  À l'origine, le régulateur pouvait ajouter environ 70 Nm en montée mais n'en retirer qu'environ 20 en descente.
- **Coupure d'injection au régulateur** (patch 0x24B5A → routine 0x7F1C0) : quand le régulateur
  est engagé, le module pédale forçait la pédale « partielle / 1000 », ce qui interdisait la
  coupure en décélération. Ce forçage est maintenant levé quand vitesse ≥ consigne + 2 km/h et
  demande ≤ 10 Nm (maintenu jusqu'à consigne + 0,5 km/h / 30 Nm). Seuils modifiables à 0x7F238–0x7F23E.
- Script : `regulateur_coupure.py` (appliqué sur la v7).
- ⚠️ Pas encore essayé sur route.

### v8 — `roms/historique/a2_ori_e85_v8_regul.bin` (abandonnée)
- Première version du patch de coupure au régulateur, basée sur un seuil de couple −790.
  Ce seuil n'était quasiment jamais atteint à cause des butées PI : remplacée par la v9.

### v7
- Test de débit EGR désactivé : 0x5B970 = 0.

### v6
- 0x3C2B4 : `move.b d0,$DBA(a5)` → `clr.b $DBA(a5)`. Le statut du défaut capteur EGR (chemin 0x26)
  est forcé « OK » : avec le capteur débranché, il bloquait l'adaptation du modèle papillon (une des causes du P1553).

### v5
- Régime maxi 6800 tr/min, dans les quatre dispositifs (`regime_max.py`) :
  limiteur par le couple 0x57CAC (6 valeurs), coupure d'injection 0x5653A/0x5653C (7000),
  défaut de surrégime 0x56542 (7300), fin de régulation de cliquetis 0x5BA32 (6800).
  La coupure d'injection à 6100, d'origine, avait été oubliée dans l'ancienne ROM.

### v4
- Tables de couple 0x55688 (16×11) et 0x55EB8 (24×12) reprises de ta ROM « audiEGRoff… ».

### v3
- Ralenti chaud 850 tr/min (0x56C58, points 60 à 120 °C).

### v2
- Reprise de tes tables depuis la ROM « audiEGRoff… » (`reporter_tables.py`) :
  - correction air / température 0x57504 ;
  - lambda cible 0x58B00 / 0x58D40 / 0x59046 ;
  - avance 0x5BA66 / 0x5BCAE / 0x5C220.
- ℹ️ 0x57504 fait 16 × 12 mais seules les 12 premières lignes (jusqu'à 80 °C) ont été reprises.
  Les lignes 100 °C et 110 °C restent donc à +6 % (enrichissement de protection d'origine), alors que ta
  ROM les avait mises à 1,00. C'est plutôt plus sûr, modifiable dans le XDF.

### v1 — `roms/historique/a2_ori_e85.bin` (`construire_depuis_ori.py`)
- Défauts EGR désactivés (codes et configuration repris de « audiEGRoff… »).
- Modèle papillon 0x57786 recalé pour le 52 mm, interpolé depuis la Golf DR (pression de référence 0x57AC6).
- Injection E85 : gain injecteur 0x569A0 × 1,45 / (débit 0 280 158 170 à 4 bar) ; VE d'origine conservée.
- Démarrage « Craaaaanking » (0x59708 + 0x5B8B6) converti depuis BackupAudiSemiOK.
- Ralenti à froid relevé (+150 tr/min jusqu'à 20 °C, puis dégressif jusqu'à 50 °C) : 0x56C58 / 0x56C38.

## Ancienne branche (base : ta ROM « audiEGRoff… », abandonnée)
- `a2_tune_papillon52.bin` : modèle papillon 52 mm.
- `a2_tune_papillon52_e85inj.bin` : + séparation carburant / air (gain ×, VE ÷, amorçage) (`separer_carburant.py`).
- `a2_tune_papillon52_e85inj_cranking.bin` : + Craaaaanking (`porter_cranking.py`).
- `a2_e85_final.bin` : + ralenti à froid relevé.

## Analyses sans modification
- Trims : STFT 30000–50000 (±25 %), LTFT 26000–54000, plafond 41600 après démarrage. Les signes affichés par VCDS sont dans le README.
- Régulateur refusé en 5ᵉ : les rapports de boîte (0x5A036…) sont identiques dans toutes les ROM CA, donc ce n'est pas l'ancienne ROM.
  La piste est la reconnaissance du rapport (fenêtre 410 ± 19 en 5ᵉ) si la taille des pneus a changé.
