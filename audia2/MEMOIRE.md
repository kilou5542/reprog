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
- **Ne pas fabriquer de nouvelle ROM sans sa demande** (v5g validée le 27/10, v5h ne démarre pas, v5i demandée et fabriquée le 27/10) (« Je ne veux pas qu'on
  s'en occupe maintenant. D'abord, je ferai la vérification de la dernière ROM »). L'analyse est permise.
- **Régulateur de vitesse abandonné pour l'instant** ; on travaille à partir de la v5g (ROM de travail).
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
| v5f | ✅ validée (rupteur franc à 7000), remplacée par la v5g |
| **v5g** | ✅ **ROM de travail** (validée 27/10) : coupure au lâcher bien plus rapide, frein moteur amélioré, pas de voyant ; à-coups en 1re pas encore testés |
| **v5k** | essayée (27/10, log 18 h 55) : **médiane 0,989** (v5g 0,928), démarre ; reste 2400 tr/min faible charge un peu pauvre, 3300–3800 tr/min faible charge riche, pleine charge > 5500 pauvre (+6–9 %) ; LTFT en cours de réapprentissage. Contenu : **v5g** + gain × 0,93 (lancement / conso compensés) + tendance VE (2 logs) + modèle papillon 0x57986 (+1,6 % aux petits angles) + tolérances P0106 +50 mbar ; **tables seules** |
| v5j ⛔ | NE PAS FLASHER (basée sur v5i) : v5i + gain injecteur × 0,93 (lancement 0x59708 / 0x5B8B6 et conso 0x5BA22 ÷ 0,93) + **tendance VE** à 70 % du log (`ve_tendance.py`, ±12 % maxi) |
| v5h | ❌ **ne démarre pas** (2 essais, 27/10) : v5g + 2 `nop` ; cause très probable : somme du code 0x7FF74 non recalculée |
| v5i | ❌ a démarré le 27/10 puis **ne redémarre plus** (comme la v7b) ; piste : valeur apprise en EEPROM (pression atmosphérique `$E4044`). Retour v5g |
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
- ⚠️ **MÉCANISME DU « DÉMARRE UNE FOIS PUIS PLUS JAMAIS » (trouvé le 27/10)** : à l'init (fct 0x0FC2A), si le
  défaut 0x3F (P0605) est mémorisé, le calculateur refait la somme principale (fct 0x50678) ; si elle échoue encore,
  fct 0x1F23C met `$1886` = 1, et la fct 0x1F244 ne remet plus à 0 le bit 3 de 0xFFFA19 (étage de sortie, coupé par
  `ori.b #8`) → **plus d'allumage** (P1357/1360/1363/1366 « court-circuit à la masse »). P0605 revient en v5i alors
  que le FICHIER v5i a des sommes justes → **le contenu du calculateur ≠ fichier**. Hypothèse forte : l'outil de flash
  n'écrit que la zone de calibration ; les patchs de CODE (0x226C2, 0x23A62, 0x3C2B4, 0x24B5A…) ne sont pas écrits,
  mais la compensation 0x7FFEA (calculée avec le patch) l'est → somme fausse dans le calculateur. Explique v5h, v6,
  v7, v7b, v10, v10b, v11, v5i. Retour à une ROM sans patch de code → somme juste → le défaut se lève → redémarre.
  **Conséquence : pas de patch de code tant que l'outil de flash n'écrit pas tout le programme** (à vérifier :
  relire le calculateur complet et comparer au fichier).
  **Confirmation 27/10 : v5g reflashée → démarre au quart de tour** (comme v5/v5g après v7b).
- **P0605 (ROM Error, chemin 0x3F)** : levé par la fct 0x50678 (somme principale, plus la somme boot si 0x5C863 ≠ 0 ;
  0x5C863 = 0) et par la fct 0x50788 (somme des octets 0x18584–0x1C4FF = 0x7FFEC, active car 0x5C862 = 1). Dans ce
  2e cas seulement : `$1AF` = 1, fct 0x1F23C et `ori.b #8, $FFFA19` (coupure d'un étage de sortie, probable).
  La v5i passe ces deux contrôles (vérifié). Relevé du 27/10 après non-redémarrage de la v5i : P0605, P1404 / P1439
  (réglage de base EGR non fait / erreur G212), **P1357 / P1360 / P1363 / P1366 (circuits d'allumage 1–4, court-
  circuit à la masse)** ; groupe 006 : correction d'altitude −2 % (normale → piste pression atmosphérique écartée).
- ⚠️ **Somme du code** : mot long **0x7FF74** = somme 32 bits des OCTETS de 0x4000 à 0x537F3 (début en
  0x7FF78, longueur en 0x7FF7C). **Toutes les ROM au code modifié sans la recalculer n'ont pas démarré**
  (v6, v7, v7b une fois seulement, v10, v10b, v11, v5h) ; toutes celles où elle est juste ont démarré.
  **Confirmé le 27/10 : la v5i (= v5h + somme recalculée) démarre.** Les conclusions passées « l'EGR forcée
  empêche le démarrage » (v6/v7/v10/v11) sont donc à relativiser (le problème EGR de la v7b reste réel).
  Le vérificateur n'a pas été trouvé dans l'application (probablement le démarrage / chargeur). Outil :
  `marelli4mv.py` (vérifie) et `fix_code()` à appeler avant `fix()` (fait dans `adaptation_papillon.py` ; les
  anciens scripts de code — etapes_v3_a_v7, regulateur_coupure — ne le font pas encore). 0x7FF70 = 0x04563628 : sens inconnu.
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
- Microcontrôleur de type 68376 *(probable)* : QADC en 0xFFF200 (CCW 0xFFF230, résultat 0xFFF2B0),
  CTM4 en 0xFFF400 *(probable)*, TPU en 0xFFFE00 (16 canaux ; CFSR 0xFFFE0C…12 : fonctions B, C, D, E, F
  changées en marche ; microcode Marelli, non décodé). Pas d'entrée PWM / fréquence libre identifiable
  depuis la ROM : dépend du câblage du boîtier.
- Idée pour réutiliser AN8 avec un signal analogique (ex. capteur éthanol converti en tension) sans
  réveiller l'EGR : vider la plage valide (0x5A846 > 0x5A848) pour que le statut reste en défaut, et lire
  `$DB8` par patch. Non fait, à proposer seulement quand l'utilisateur le demandera.
- Capteur éthanol GM / Continental 13577429 (SE1004S) : pas de fiche officielle publique trouvée.
  Données concordantes (revendeurs, GM) : 12 V, 3 broches, sortie à collecteur ouvert (rappel au 5 V côté
  calculateur), fréquence 50 Hz = 0 % → 150 Hz = 100 % (linéaire), 180–190 Hz = carburant contaminé ;
  largeur d'impulsion 1 ms = −40 °C → 5 ms = 125 °C. À vérifier à l'oscilloscope. Il faut un convertisseur
  fréquence → tension pour l'entrée AN8.
  Consommation sur le 12 V : non publiée (à mesurer) ; rappel du signal 2,2–10 kΩ (doc AEM) ; fusible bas
  calibre sur un + après contact.
- Groupes de mesure : table en 0x54360… (mot = n° de groupe, puis 4 pointeurs vers les fonctions de champ).

### Enregistrement (logs)
- WiCAN Pro (firmware d'origine, émulation ELM327) : gère ISO 9141-2 / ISO 14230-4 (ligne K), donc les PID
  OBD standard (mode 01) de l'EOBD. Les groupes de mesure VAG (KWP1281, ex. groupe 074) ne sont a priori
  **pas** lisibles par un ELM327. Piste non vérifiée : la liste interne de 0x5C variables (fct 0x4C96) si
  elle répond à un service KWP2000 « local identifier ».
- Log automatique WiCAN Pro : Automate › Parameters (Standard PIDs : régime 0C, charge 04, papillon 11, λ
  sonde 24 ou λ commandé 44 si publiés) + Automate › Settings (Enabled) + Logger (Record parameters, CSV,
  carte SD FAT32 ≤ 32 Go, fichiers /sd/logs). ⚠️ La doc AutoPID ne cite que des protocoles CAN alors que le
  moteur de l'A2 répond en ligne K : à tester (protocole Automatic ou commande d'init ATSP4 / ATSP5).
  Une appli téléphone connectée met AutoPID en pause. Préférer logger λ plutôt que l'AFR (E85).
- WiCAN de l'utilisateur (capture du 27/10) : interface ancienne (page « CAN » : bitrate 500K, mode Normal,
  TCP 35000, protocole elm327, MQTT désactivé, adresse 192.168.0.10, mot de passe AP par défaut) → pas de
  menus Automate / Logger visibles : firmware à mettre à jour pour le log autonome. Diagnostic de l'A2 par ligne
  K : les réglages CAN n'interviennent pas.

### Pression atmosphérique et observateur de pression (vu en analysant l'échec de la v5h)
- `$16D4` pression atmosphérique : au démarrage (fct 0x22C68) = EEPROM `$E4044` si somme `$E4048` bonne et
  drapeau `$E4046`, sinon 0x57AE2 = 1000. Apprise moteur tournant (fct 0x23962, bloquée par `$DBA` en 0x23A62)
  à partir du modèle papillon, bornes 0x57ACC = 550 / 0x57ACE = 1050.
- `$1686` (MAP utilisée partout) = **observateur** (fct 0x23CE2) qui mélange le modèle papillon `$16BA` et la
  mesure `$16B4`, gains 0x57B7E / 0x57B5E / 0x57B3E / 0x57BA8 selon le régime ; inactif au lancement
  (`$D4E` = 0 ou 1) et si 0x57B32 = 0.
- `$1740` : relu en EEPROM `$E4574` à l'init (fct 0x22570, somme `$E4576`, défaut 0x54E0E), sauvé fct 0x22BF2.

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
- **Boucle fermée quasi permanente** (fct 0x36D64, drapeau `$1071`) : sonde large bande, la STFT régule
  dès que λ cible **ou** λ mesuré est dans **0,800…1,200** (0x596FC / 0x596FE), y compris pleine charge
  (λ 0,86–0,95) et moteur froid (0,85). Conditions : interrupteur 0x59622, sonde prête `$1DF3`, pas de
  défaut (`$11A0` bit 11), pas de coupure / lancement (`$193B` ≠ 0x20/0x40/0x80), 5 s (0x59704) après un
  redémarrage à chaud, pas de coupure ASR ; délai d'entrée 0x596C0 × 0x59624 / 1000. Hors conditions, la
  STFT revient vers 40000 de 200 (0x59702) par pas.
- **E85** : stœchiométrie 0x59768 = 14,5 gardée, ×1,45 dans le gain injecteur 0x569A0. Pas strictement
  équivalent à changer 0x59768 (lancement, modèle d'échappement 0xEF08, purge, seuils) : le gain est le
  bon choix. Conso affichée : 0x5BA22 = 541.
- **Noms XDF corrigés** : 0x58D40 = λ moteur froid ; 0x55EB8 = avance optimale ; 0x5C220 = seuil
  d'accélération du cliquetis (modifiée à tort dans la v5f, à remettre d'origine plus tard) ;
  0x55688 = conversion couple → charge ; 0x57E72 = facteur redémarrage à chaud.

### Groupes de mesure VCDS utiles (fichier label Ross-Tech 036-906-034-APE.LBL, fourni le 27/10)
- 001 régime / eau / STFT / conditions réglage de base (bits : eau > 80 °C, régime < 2000, papillon fermé,
  régulation λ correcte, ralenti, clim coupée, catalyseur > 300 °C, pas de défaut) ; 002 régime / charge /
  **temps d'injection** / MAP ; 003 régime / MAP / papillon / avance ; 004 tension / eau / air ;
  005 état de charge ; **006 champ 4 = correction d'altitude** (pression atmosphérique apprise, −30…+5 %) ;
  010 avance ; 014–016 ratés ; **022 / 023 retard de cliquetis par cylindre** ; 028 test capteur cliquetis ;
  030 état sondes ; 032 LTFT ralenti / charge partielle (voir ci-dessous) ; 033 / 099 régulation λ ;
  050 / 054–056 ralenti (056 régulateur en Nm, 055 adaptation stabilisation) ; 060–062 papillon / pédale ;
  070 purge ; **074 EGR (min, max, tension actuelle, état d'adaptation)** ; 075 test EGR ; 100 readiness ;
  120 / 122 ASR / boîte ; 125 CAN.
- **Groupe 001 champ 4** (fct 0xC368) : l'ordre des bits du label est **inversé** pour ce calculateur. Lu de gauche
  à droite : pas de défaut mémorisé · catalyseur > 300 °C (`$9E6` > 0x56646 = 340, et `$9E8` = 2) · clim coupée ·
  toujours 1 · régulation λ active (`$1083`) · ralenti (`$D4C` = 4) · régime < 2000 · eau > 80 °C (`$1FD8` ≥ 120).
  « 10111111 » au ralenti prolongé = **catalyseur modélisé sous 300 °C** (normal au ralenti).
- Connexion (login) **11463 = activation du régulateur de vitesse**, 16167 = désactivation.
- Codage : +1 ABS, +2 airbag, +4 clim ; dernier chiffre 1 = boîte manuelle, 3 = automatique.

### Tables de remplissage (VE) dans les ROM (comparées à l'origine CA, 27/10)
- v5g / v5i : **VE 0x57084 d'origine**, 0x572C4 d'origine, 0x57504 modifiée (0,94…1,20), modèle papillon
  0x57786 recalé ; E85 + injecteurs portés par le gain 0x569A0 (×0,90…0,93), temps mort 0x57E74 d'origine.
- ROM « nom long » : VE 0x57084 modifiée partout (×0,68…1,41), 0x57504 idem v5g.
- CA-DR : VE ×0,41…1,09, dynamique 0x572C4 ×0,31…4,0, correction d'angle 0x57986, **0x57058 = −1** (gaz
  résiduels ≈ 0) et **0x5705A = 9870** (+16 % de pression utile), gain 0x569A0 = table Golf DR (415…335),
  **temps mort 0x57E74 très relevé** (13 → 306 à 14 V). Ses modifications de VE compensaient donc d'autres
  réglages : ne pas les recopier.
- Méthode retenue (proposée) : d'abord injecteurs (temps mort, gain), puis VE à partir de logs moteur chaud,
  adaptation LTFT neutralisée (0x5CDD2 = 0) pour que la STFT porte toute l'erreur ; VE × (1 + STFT VCDS).
  La VE fixe la charge `$16C6` utilisée partout (axes d'avance, λ, couple, papillon) : elle doit rester physique.
- **27/10 : l'utilisateur ne veut PAS de ROM spécifique pour les relevés ; il garde la v5i.** Donc relevés avec
  LTFT actif : erreur totale = STFT et LTFT combinées (le carburant est multiplié par (1 + STFT) × 40000 / LTFT).
  À logger : régime, **MAP** (axe de la VE, pas la charge), STFT, LTFT (en direct : PID OBD 07 via WiCAN si
  publié ; VCDS n'a pas de LTFT en direct, le groupe 032 ne donne que des instantanés), température d'eau et
  d'air, temps d'injection. Vérifier le signe de l'outil (VCDS : LTFT inversé, STFT normal).
- OBD générique (VCDS mode OBD-II, 27/10) : protocole **ISO 9141-2** (ligne K broche 7, 10,4 kbit/s, init 5 bauds
  adresse 0x33 ; ELM327 : ATSP3), ~0,8 échantillon/s ; PID confirmés : 0C régime,
  04 charge (6,7 % au ralenti), **34 λ large bande** (1,005 ; 0,023 mA), 0B MAP (49 kPa clim en route), **06 STFT, 07 LTFT**.
- **Signes et échelles (vérifiés dans le code)** : brut 40000 = neutre, carburant × 40000 / brut ; positif = le
  calculateur RETIRE de l'essence pour OBD 06 / 07 et VCDS 032. **Échelles : VCDS 001 / 032 = (brut − 40000)/400
  (vraie valeur) ; OBD 06 STFT = (brut − 40000)/100 (×4, fct 0x4B642, ≥ 50000 → 99 %) ; OBD 07 LTFT =
  (brut − 40000)/200 (×2, fct 0x4B694).** VCDS 001 « Lambda Controller » = (40000 − brut)/400 (signe inverse).
  Facteur réel = 40000/(40000 + 100·STFT_obd) × 40000/(40000 + 200·LTFT_obd).
- Relevé OBD 27/10, ralenti clim en route (49 kPa) : STFT −3,9 %, **LTFT +20,3 %** (le calculateur retire ~17 %).
- **Log OBD du 27/10 (v5i)**, échelles corrigées : base trop riche (f 0,96 à 250 mbar → 0,85 à 550 mbar ; 0,80–0,85
  à 3300–4200 tr/min mi-charge) ; pleine charge 0,89–0,93 jusqu'à 4500, **1,04–1,07 au-dessus de 5500 (trop pauvre)**.
  Profil VE + richesse générale ; pas un profil de temps mort.
- Filtre des logs (demande du 27/10) : en **pleine charge (MAP ≥ 90 kPa) toutes les mesures sont gardées**, même
  en montée en régime ; la STFT est associée au régime de la ligne précédente (retard ~1 s). `analyse_log_ve.py`
  affiche les deux (retard 0 / 1) ; `ve_tendance.py` utilise le retard 1, poids 0,7.
- 2e log OBD (27/10 17 h, v5g, bouchons) : médiane 0,93 ; les deux logs : 0,928 → gain × 0,93 confirmé.
- **Décision de l'utilisateur (27/10) : corriger À LA FOIS le gain injecteur et la VE.** Proposition : gain 0x569A0
  × ~0,93 (médiane f = 0,92 sur 397 points, quartiles 0,85–0,96), puis VE case par case × f / 0,93 (dont hausse en
  pleine charge > 5500 tr/min, déjà pauvre), et compenser le lancement (0x59708, 0x5B8B6 passent par le gain)
  de +7,5 % pour ne pas dégrader le démarrage à froid. Attente d'un 2e log (paliers stables mi / forte charge). Détail : MESURES.md, script
  `scripts/analyse_log_ve.py`, logs dans `logs/`.

### Adaptation de richesse (LTFT)
- **Groupe VCDS 032** (fct 0x99E0 / 0x9A44) : ce ne sont pas un additif et un multiplicatif « Bosch » mais deux
  **instantanés de la LTFT** (`$28`, valeur de la carte au point courant) pris une fois par cycle (fct 0x3F0E8) :
  champ 1 « add. » = `$BFE` au **ralenti** ; champ 2 « mult. » = `$BFC` en **charge partielle** (zones 2,7…6 des
  axes). Affichage = brut/400 − 100 (pas de 1 %) ; **0,0 % = pas encore relevé** (brut < 30000).
- **Signe** : le carburant est multiplié par 40000 / LTFT → **VCDS +8 % = le calculateur RETIRE ~7 %** (base
  trop riche). La STFT VCDS (« Lambda Controller ») a le signe normal (+ = ajoute).
- Carte **8 × 8** en EEPROM 0xE43D8 (fct 0x532A8) : régime 0x5CE64 [680…5600] × MAP 0x5CE74 [150…1000 mbar],
  interpolée ; butées 0x5CEA0 / 0x5CEA2 = 26000 / 54000 (±35 %) ; STFT ±25 % (0x596BC / 0x596BE).
- Relevé du 27/10 (v5g, outil à préciser) : LTFT **+15 % ralenti, +40 % roulage faible charge, −10 % pleine
  charge haut régime**. Hypothèse principale si « + » = ajout d'essence : gain injecteur 0x569A0 trop fort
  (~10 %) **et** temps mort 0x57E74 trop court pour les 0 280 158 170 (erreur forte aux impulsions courtes).
  Autre piste : MAP de l'observateur (modèle papillon non appris) à faible charge. Vérifier le signe selon l'outil.

## 9. À faire / en attente

- v5g validée (ROM de travail). Attendre : test des à-coups en 1re en descente sur v5g, puis retour sur la v5h
  (protocole MESURES.md). Toute nouvelle ROM part de la v5g (ou de la v5h si elle est validée).
- Ensuite seulement, si demandé : air minimum en roue libre (0x55688 col. 0 / 0x557E8), ligne 0 de
  0x5A904, remise d'origine de 0x5C220, conso E85 sur la ROM retenue, suivi du P1553.
- Reste inconnu : conversion `$DF8` → angle papillon (inverse du modèle 0x57786) ; rôle exact de
  0x5C1AE/0x5C1B4 (zones cliquetis), 0x5C466 (axe colonnes), 0x57E74 (unité du temps mort).

## 10. Journal des sessions

- **26–27/10/2026** : P1553, EGR, rupteur (v5f validée), coupure rapide (v5g), apprentissage papillon
  (v5h), mesures de ralenti, chaîne couple → air, décompilation complète injection / allumage, XDF à
  54 tables, comparaison E85 stœchio / gain, outils de désassemblage rapatriés, création de ce fichier.
