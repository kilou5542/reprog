# Mémoire du projet (à lire en premier, à tenir à jour)

Ce fichier rassemble tout ce qui a été appris sur l'Audi A2 et son calculateur, pour qu'une nouvelle
session reparte d'ici sans tout redécouvrir. **Règle : à chaque découverte ou décision, mettre ce
fichier à jour (et committer) au fur et à mesure, pas seulement en fin de session.**

Documents détaillés : [README](README.md) (format, checksum, reproduction des ROM), [CHANGELOG](CHANGELOG.md)
(chaque version et pourquoi), [MESURES](MESURES.md) (relevés voiture, protocole v5h),
[ANALYSE_COUPLE](ANALYSE_COUPLE.md) (chaîne couple → air → papillon),
[INJECTION_ALLUMAGE](INJECTION_ALLUMAGE.md) (toutes les tables d'injection et d'allumage).

---

## 1. Le propriétaire et ses règles

- Parle **français** : toujours répondre en français.
- **Ne pas fabriquer de nouvelle ROM tant qu'il n'a pas validé la v5g et la v5h** (« Je ne veux pas qu'on
  s'en occupe maintenant. D'abord, je ferai la vérification de la dernière ROM »). L'analyse est permise.
- **Régulateur de vitesse abandonné pour l'instant** ; on travaille à partir de la v5 / v5f.
- **Ne rien toucher qui ressemble à l'EGR** (v6/v7/v7b ont empêché le démarrage ou le redémarrage).
- **XDF sans accents** (ASCII pur, fins de ligne CRLF) : `generer_xdf.py` s'en charge.
- Préfère **reconstruire les tables intelligemment d'après le matériel** plutôt que de recopier une ROM.
- Git : dépôt `kilou5542/reprog`, dossier `audia2/`, branche `ccr-b93a7069-senejy`. Pas de PR sans demande.
- Il a aussi une Fiat Scudo / Peugeot 206 S16 (IAW 48P2) : travail terminé (ROM E85 « Romdrop-like »),
  hors de ce dépôt.

## 2. La voiture

- Audi A2 1.4 16V **BBY**, Marelli **4MV 036906034CA** (logiciel CA ; la DR a le même code, calibration
  différente : la clim et le régulateur ne marchent pas avec la DR).
- Papillon **Golf 52 mm 036 133 062 M** (origine 44 mm), collecteur **Polo GTI**, admission modifiée.
- Injecteurs **0 280 158 170**, régulateur **4 bar sans prise de dépression** (référencé atmosphère).
- **E85**. Sonde lambda large bande d'origine.
- **Vanne EGR bloquée et débranchée** (connecteur impossible à rebrancher). Le capteur débranché met le
  statut EGR `$DBA` en défaut ; le code défaut est masqué depuis la v1.
- Ralenti mesuré (26/10/2026, v5g, 90 °C) : 870 tr/min, 32 kPa, papillon 2,55 % ; clim : 930 tr/min, 41 kPa, 4,51 %.

## 3. État des ROM (détail dans CHANGELOG)

| ROM | État |
|---|---|
| **v5f** | ✅ ROM de travail, validée sur route (rupteur franc à 7000) |
| **v5g** | à essayer : coupure plus rapide au lâcher de pédale (filtre `$126C` repris de la CA-DR) |
| **v5h** | à essayer : v5g + apprentissage du modèle papillon débloqué (2 `nop`, EGR intacte) ; protocole dans MESURES.md |
| v6, v7, v10, v11 | ❌ ne démarrent pas (forcer `$DBA` = 0 recopie le capteur EGR débranché) |
| v7b, v10b | ❌ démarrent une fois puis plus (apprentissage EGR réveillé, valeurs en EEPROM) |
| v5b–v5e | ❌ rupteur oscillant (cause : reprise d'injection 0x5B8EA restée à 5610) |

Chaîne de fabrication reproductible à l'octet près : voir README.

## 4. Le calculateur : format et méthode

- CPU32 (68332). Dump de 512 Ko **octets inversés par mot** : mots en little-endian dans le fichier
  (TunerPro « LSB first »). Pour un octet isolé, adresse XOR 1.
- RAM : `a5 = 0xE5770` ; `$xxx(a5)` = adresse absolue 0xE5770 + xxx (le code utilise les deux formes).
  EEPROM recopiée vers 0xE4000–0xE4600 (ex. `$E4574` = adaptation papillon).
- Calibration 0x55000–0x5D000 ; il y a aussi du code dans 0x50000–0x54FFF.
- Checksum : somme des mots 0x4000–0x7FFFF = mot 0x7FFE8, compensation 0x7FFEA ; zone code
  0x18584–0x1C4FF contrôlée à part (mot 0x7FFEC). `scripts/marelli4mv.py fix`.
- Interpolations :
  - **2D** : `jsr 0x49A6C` (non signé) / `0x49ABA` (signé). Empilés : largeur de ligne (octets), position
    ligne, position colonne, adresse table. Positions = index × 256 + fraction.
  - **1D** : en ligne, instruction CPU32 `TBL` que capstone décode à tort en `fsmove` (affiché `TBL(1D)`).
  - **Axes** : `move.w #n-1 ; move.w entrée ; pea FIN_AXE` puis recherche en arrière ; l'axe commence à
    FIN − 2n. La position est rangée dans `$1E66`…`$1E9C` (copies en `$18CC`… / adresses 0xE7xxx).
- **Outils** (`outils_desassemblage/`, lancer avec `python3 -I`) :
  - `preparer.py` (une fois par session : crée `travail/` avec ROM big-endian, désassemblage, base) ;
  - `fn.py ADR` (désassemble la fonction, valeurs ROM annotées) ; `bref.py ADR` (résumé) ;
  - `qui.py VAR` (qui écrit / lit `$VAR(a5)`) ; `lectures.py [filtre]` (toutes les lectures de tables) ;
  - `xref.py travail/rom_be.bin VAR` (références brutes) ; `axes4mv.py` (ancien, remplacé par lectures.py).
- Pièges : capstone mal aligné par endroits (vérifier avec le binaire) ; `skipdata` crée des `dc.w`.
  Les noms WinOLS des fichiers de l'utilisateur sont souvent faux : « ne te fie pas aux noms ».

## 5. Unités

- Températures : brut − 40 = °C. Avance : 0,1°. Lambda : 0,001. Charge `$16C6` : 0,01 %.
- Angle papillon `$200C` et axe modèle papillon : 0,1 %. Pédale : ‰. Tension : 0,1 V. Pressions : mbar.
- Facteurs : 1000, 1024 ou 10000 = ×1 selon la table (voir INJECTION_ALLUMAGE.md).
- STFT `$107E` : 40000 = neutre ; VCDS affiche (40000 − x)/400. LTFT : (x − 40000)/400, **signe inversé**.

## 6. Variables RAM importantes (`$xxx` = offset de a5)

| Var | Sens |
|---|---|
| `$1DA4` / `$18E0` | régime |
| `$1686` | pression collecteur (MAP) ; `$16D4` pression atmosphérique |
| `$1FD0` / `$1FD4` | température d'air / d'eau (brut, −40) |
| `$16C6` | charge relative ; `$16C0` masse d'air par cylindre ; `$16CC` débit d'air |
| `$200C` | angle papillon ; `$20C4` tension |
| `$2034` | λ final ; `$1030`→`$1038`→`$1036`→`$202A`→`$202C` masse de carburant (étapes) |
| `$1856` / `$1854` | gain injecteur / correction temps mort selon la dépression |
| `$272` | avance de base ; `$2A6` avance corrigée ; `$2A4` avance finale avant cliquetis |
| `$1F8E` / `$1F8A` | avance optimale (MBT) / perte de rendement d'allumage |
| `$D4C`, `$D4E` | états moteur (lancement, ralenti, coupure…) ; `$18EC` mode d'allumage |
| `$DBA` | statut EGR (en défaut, ne pas forcer) ; `$DB8` capteur, `$DB6` position utilisée ; `$582` position EGR |
| `$1740` / `$174E` | correction d'angle apprise du modèle papillon / intégrateur (EEPROM `$E4574`) |
| `$126C`, `$1272` | couple conducteur lissé, écart (autorisation de coupure en décélération) |
| `$1270`, `$1274`, `$1277` | demande de réduction de couple de l'anti-à-coups (→ retard d'allumage 0x4E19C) |
| `$DC8`→`$160C`→`$FA0`→`$2054`→`$2050`→`$2056`→`$DF8` | chaîne couple → charge → papillon |
| `$1776` / `$1816`, `$177E` / `$180E` | réserve de couple du ralenti / consigne de régime de ralenti |
| `$671` | embrayage enfoncé ; `$20D4` rapport |
| `$62C` | coupure d'injection (100 % = toutes) ; `$62E` cumul carburant (consommation) |

### Entrée du capteur EGR (pour une éventuelle entrée TOR)
- Fct 0x3C272 : `$DB8` = conversion QADC canal **AN8** (`jsr 0x282D0` avec 0xC8 ; résultat 10 bits,
  0…1023 = 0…5 V). Diagnostic 0x28218 : plage valide **0x5A846 = 61 (0,30 V) … 0x5A848 = 983 (4,80 V)**,
  chemin de défaut 0x26 → `$DBA` (0 = OK et `$DB6` = `$DB8` ; 1…4 = défauts).
- Lecteurs de `$DB8` : seulement 0x3C272 et une liste de diagnostic (0xB7FC). Pour l'utiliser comme
  entrée TOR sans réveiller l'EGR, les deux états doivent rester **hors** de 0,30…4,80 V (≈0 V et ≈5 V),
  et un patch doit lire `$DB8` (aucun code n'en fait un interrupteur aujourd'hui). Brochage à vérifier
  sur un schéma (non connu ici).
- **Lisible dans VCDS : groupe de mesure 074, champ 3** (tension du capteur EGR en volts,
  `$DB8` × 5000 / 1024 mV, fct 0xB7FC). Champs 1 et 2 : `$590` / `$58E` en % ; champ 4 : état `$587` (texte).
- Groupes de mesure : table en 0x54360… (mot = n° de groupe, puis 4 pointeurs vers les fonctions de champ).

## 7. Fonctions repérées

| Adresse | Rôle |
|---|---|
| 0x125EA–0x13400 | calcul des positions sur les axes |
| 0x0E792 | capteurs de température (linéarisation 0x55C4E) |
| 0x0D792–0x0DFA2 | cœur couple / carburant : 0xDD56 = chaîne carburant principale |
| 0x10D8C | modèle de couple : MBT 0x55EB8, rendement 0x560F8 / 0x56110 |
| 0x1FEC2, 0x2000C, 0x20078, 0x2AAF0 | conversion masse → temps d'injection |
| 0x205A2–0x22600 | ralenti (consignes, réserve, PI) |
| 0x22DDE, 0x22FF6, 0x23962 | modèle papillon / charge d'air / adaptation du modèle |
| 0x26930, 0x26D96, 0x26E84 | limiteur de régime par le couple (avance + carburant) |
| 0x31382 | film de paroi ; 0x31900–0x32600 anti-à-coups (régime de référence 0x58678) |
| 0x3306C, 0x3332C, 0x32B8E, 0x32F36, 0x33402 | λ cible, paramètres, enrichissements, rampes |
| 0x35F82, 0x36838, 0x36C32 | régulation λ (large bande, STFT) ; 0x532A8 LTFT |
| 0x375C4, 0x376B8, 0x37742, 0x378FC, 0x37B9A | enrichissement démarrage, masse carburant, lancement, reprise |
| 0x3A638, 0x3A8AA | demande conducteur (0x5A26C / 0x5A06C) |
| 0x3C002 | demande totale bornée à 0 ; 0x3D08A / 0x3D15A / 0x3D1A0 coupure décélération |
| 0x404EC | diagnostic P1553 (chemin 0x33) |
| 0x14F58, 0x46782 | coupure de régime / coupure de toutes les injections |
| 0x457EE, 0x45E78 | injection par cylindre (lancement / normal, phase 0x5B668) |
| 0x46C80–0x47F00 | EGR (surveillance, apprentissage) : NE PAS RÉVEILLER |
| 0x4C560–0x4E900 | allumage (0x4C744 composition, 0x4CE3A base, 0x4D2E4 corrections, 0x4DA3A cliquetis) |
| 0x49A6C / 0x49ABA | interpolation 2D |

## 8. Ce qu'on sait (résumé des conclusions)

- **Rupteur** : régler ensemble 0x5653A/C (coupure), **0x5B8EA (reprise après coupure totale)**,
  0x57CAC ×6 (limiteur par le couple), 0x56542 (défaut), 0x5BA32 (fin cliquetis). Voir `rupteur.py`.
- **P1553** : |pression modèle − MAP| > tolérance 0x5AF48 (140/200 mbar + 0x5AF5A, 0x5AF6A, 0x5AF6C).
  Le modèle 0x57786 est corrigé par l'apprentissage `$1740` (bornes +13 / −15, en 0,1 %), bloqué par
  `$DBA` en 0x226C2 et 0x23A62 → v5h les remplace par `nop`. Apprentissage : ralenti stable, chaud,
  STFT dans ±20 % (LTFT non testé).
  `$1740` n'est **pas** dans les groupes de mesure VCDS (seulement dans une liste interne Marelli de
  0x5C variables, fct 0x4C96, identifiant → adresse) ; le groupe VCDS 060 « ADP OK » est l'étalonnage des
  butées du papillon, une autre chose. Vérification de la v5h : indirecte (P1553 absent, écart MAP / modèle).
- **Coupure en décélération** : seuils 0x5A904 (entrée) / 0x5A9E0 (reprise) 5 lignes × 9 températures,
  ligne = rapport (0x53B30) ; embrayage → coupure immédiate ; filtre `$126C` (0x5857C / 0x585FA) cause du
  délai au lâcher → v5g.
- **Frein moteur / à-coups en 1re en descente** : le calculateur ne demande jamais de couple négatif
  (0x3C002) et ne retarde pas l'allumage pour freiner. L'air en roue libre = max(colonne 0 de 0x55688,
  0x557E8) : 2200 en v5g contre ~1400 d'origine entre 900 et 1250 tr/min. Pistes (plus tard) : baisser cet
  air, relever la ligne 0 de 0x5A904 (~2000 à chaud).
- **E85** : stœchiométrie 0x59768 = 14,5 gardée, ×1,45 dans le gain injecteur 0x569A0. Pas strictement
  équivalent à changer 0x59768 (lancement, modèle d'échappement 0xEF08, purge, seuils) : le gain est le
  bon choix. Conso affichée : 0x5BA22 = 541.
- **Noms XDF corrigés** : 0x58D40 = λ moteur froid ; 0x55EB8 = avance optimale ; 0x5C220 = seuil
  d'accélération du cliquetis (modifiée à tort dans la v5f, à remettre d'origine plus tard) ;
  0x55688 = conversion couple → charge ; 0x57E72 = facteur redémarrage à chaud.

## 9. À faire / en attente

- Attendre le retour de l'utilisateur sur v5g puis v5h (protocole MESURES.md).
- Ensuite seulement, si demandé : air minimum en roue libre (0x55688 col. 0 / 0x557E8), ligne 0 de
  0x5A904, remise d'origine de 0x5C220, conso E85 sur la ROM retenue, suivi du P1553.
- Reste inconnu : conversion `$DF8` → angle papillon (inverse du modèle 0x57786) ; rôle exact de
  0x5C1AE/0x5C1B4 (zones cliquetis), 0x5C466 (axe colonnes), 0x57E74 (unité du temps mort).

## 10. Journal des sessions

- **26–27/10/2026** : P1553, EGR, rupteur (v5f validée), coupure rapide (v5g), apprentissage papillon
  (v5h), mesures de ralenti, chaîne couple → air, décompilation complète injection / allumage, XDF à
  54 tables, comparaison E85 stœchio / gain, outils de désassemblage rapatriés, création de ce fichier.
