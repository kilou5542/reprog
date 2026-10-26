# Changelog — Audi A2 BBY, Marelli 4MV 036906034CA

Matériel : papillon Golf 52 mm (036 133 062 M, origine 44 mm), collecteur Polo GTI, injecteurs
Bosch 0 280 158 170, régulateur de pression 4 bar sans durite de dépression (F 026 403 006),
E85, sonde lambda large bande d'origine. Vanne EGR obturée et débranchée.

Toutes les adresses sont celles du code (mots identiques dans le fichier ; voir README).
Chaque version a un checksum correct.

## Branche actuelle (base : `audiori`, logiciel CA)

La base CA est gardée : avec la DR, le régulateur de vitesse et la climatisation ne fonctionnent pas.

### v5d — `roms/a2_ori_e85_v5d_regime_nomlong.bin` (test : régime strictement identique à la ROM nom long)
- v5c toujours avec le problème de rupteur. Recherche de toutes les valeurs 5700–6000 dans la ROM : seules 0x57CB0
  (bas de rampe du limiteur) et 0x59712 (amorçage, sans rapport) diffèrent de la ROM nom long.
- Test décisif : tous les réglages de régime recopiés de la ROM nom long (0x5653A–0x56549 : coupure 6100,
  0x57CAC–0x57CB7 : limiteur 6600/6450/5800/6600/6400/6700, 0x5BA32 = 5900). Si le rupteur redevient bon,
  la cause est dans ces valeurs ; sinon elle est ailleurs (VE / modèle papillon / gain → estimation du couple).

### v5c — `roms/a2_ori_e85_v5c.bin` (❌ rupteur toujours mauvais)
- Constaté en v5b : rupteur toujours mauvais, reprise vers 5000–5900.
- En v5, 0x5BA32 (régime au-delà duquel la régulation de cliquetis est coupée, fct 0x49C1A) était passé de 5900 à 6800.
  Entre 5900 et 6800 la détection n'est pas calibrée : probable faux cliquetis → fort retard d'allumage près du rupteur,
  puissance retrouvée seulement en redescendant. Remis à **5900**, comme l'origine et la ROM nom long.
- Vérifié : la coupure d'injection elle-même reprend 100 tr/min sous le seuil (hystérésis 0x5653E = 100, identique
  partout) ; seuil spécial 0x56554/0x56556 (1200/1300) seulement en mode dégradé (`$E4033` = 3).
- Différences avec la v5b : 0x5BA32 et checksum.

### v5b — `roms/historique/a2_ori_e85_v5b.bin` (rupteur encore mauvais, voir v5c)
- Constaté en v5 : rupteur qui oscille 6000 ↔ 7000. Le limiteur par le couple (0x57CAC, 6800) agissait avant
  la coupure d'injection (0x5653A, 7000), rabattait le couple vers 0x57C3C (350) puis le rendait d'un coup
  sous 0x57CB0 (6000).
- Comme dans la ROM « audiEGRoff… », la coupure d'injection fait maintenant le rupteur : 0x5653A/0x5653C = 6800 ;
  limiteur par le couple placé au-dessus (7100 / 6950 / 6500 / 7100 / 6950 / 7200) comme sécurité.
- Script : `rupteur.py entree.bin sortie.bin 6800`. Différences avec la v5 : 0x5653A–0x5653D, 0x57CAC–0x57CB7, checksum.

### v5 + régulateur + conso — `roms/historique/a2_ori_e85_v5_regul_conso.bin` (mise de côté, régulateur abandonné pour l'instant)
- Configuration EGR de la v5 conservée telle quelle (aucun voyant constaté) : pas de patch 0x3C2B4 / 0x226C2 /
  0x23A62, test de débit EGR inchangé. L'adaptation du modèle papillon reste donc bloquée, comme en v5.
- Ajouts : régulateur v9 (butées PI 0x5C778 / 0x5C77C, coupure 0x24B5A → 0x7F1C0) et conso E85 (0x5BA22 = 541).
- Différences avec la v5 : uniquement ces zones et le checksum.
- `roms/a2_ori_e85_v5.bin` : **ROM de travail retenue**. Démarre et redémarre sans voyant ; base des prochaines modifications.

### v10c — `roms/a2_ori_e85_v10c.bin` (non retenue pour l'instant)
- v7c + régulateur (v8/v9) + conso E85 (v10).

### v7c — `roms/a2_ori_e85_v7c.bin` (non essayée, alternative si le P1553 revient)
- On ne touche plus au capteur EGR : son statut reste « en défaut » comme en v5 (code défaut masqué depuis la v1),
  donc toute la surveillance / apprentissage EGR (0x46C80–0x47F00) reste endormie.
- Seules les deux adaptations du modèle papillon, bloquées par ce statut, sont débloquées :
  0x226C2 et 0x23A62 `bne.w` → `nop nop`.
- Différences avec la v5 : 0x226C2, 0x23A62, 0x5B971 = 0 (test débit EGR), checksum.

### v10b — `roms/historique/a2_ori_e85_v10b_NE_REDEMARRE_PAS.bin` (même défaut que v7b)
- v10 + correctif EGR de la v7b (0x3C2C0). Aucune autre différence avec la v10.

### v7b — `roms/historique/a2_ori_e85_v7b_NE_REDEMARRE_PAS.bin` (❌ démarre une fois, puis plus)
- Constaté : démarre, voyant moteur « vanne EGR non calibrée », puis ne redémarre plus après arrêt.
  Le statut « capteur sain » réveille l'apprentissage EGR, qui apprend une position fictive (0) et la stocke
  en EEPROM (`$E4190`–`$E4198`). Abandonnée au profit de la v7c.
- **Correctif du patch v6** : en plus de `$DBA` forcé à 0, 0x3C2C0 `move.w (a1),$DB6(a5)` → `clr.w $DB6(a5)`.
  `$DB6` est la position EGR utilisée par la gestion (0x46CAE, 0x471A6…). Avec le statut forcé « OK », la v6 y
  recopiait la tension du capteur débranché (`$DB8`, entrée 0xC8) = vanne vue ouverte → **pas de démarrage**
  (v6, v7 et donc v8 à v11 concernées). En v5 le défaut était détecté et `$DB6` restait à 0 : on force ce 0.
- Différences avec la v5 : 0x3C2B4, 0x3C2C0, 0x5B970 = 0, checksum.

### v11 — `roms/historique/a2_ori_e85_v11_NE_DEMARRE_PAS.bin` (❌ abandonnée : la voiture ne démarre pas)
- **Modèle papillon 0x57786 agrandi de +10 % de section effective** (≈ 52 → 54,5 mm équivalent),
  pour un papillon légèrement plus gros et une admission plus libre en amont, afin d'éviter le P1553.
  Calcul cellule par cellule avec l'écoulement compressible (débit papillon = débit moteur) ; les cellules
  à la pression de référence ne bougent pas, la table reste croissante selon l'angle.
  Effet : pression attendue +10 à +50 mbar à faible ouverture, presque rien près de la pleine ouverture.
- Script : `papillon_agrandi.py entree.bin sortie.bin 1.10` (facteur réglable).
- ❌ Essai : la voiture ne démarre pas — mais la v7 non plus : la cause principale est le patch v6 (voir v7b).
  En plus, la pression modélisée (sortie `$16B2`, fct 0x22DDE) sert aussi au
  calcul de charge : +10 à +50 mbar aux petits angles / bas régimes = plus d'air calculé, donc plus de carburant
  au démarrage (noyé en E85) et/ou moins d'ouverture commandée. Ne plus modifier cette table sans logs.

### v10 — `roms/historique/a2_ori_e85_v10_NE_DEMARRE_PAS.bin` (contient le défaut de la v6)
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

### v7 — ❌ ne démarre pas (constaté), voir v7b
- Test de débit EGR désactivé : 0x5B970 = 0.

### v6 — ❌ même défaut, voir v7b
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
