# Mémoire du projet Meriva (à lire en premier, à tenir à jour)

Tout ce qui a été appris sur l'Opel Meriva et son calculateur, pour qu'une nouvelle session reparte
d'ici. **Règle : à chaque découverte ou décision, mettre ce fichier à jour (et committer) au fur et à
mesure.**

Documents détaillés : [README](README.md) (format, checksum, outils),
[INJECTION_ALLUMAGE](INJECTION_ALLUMAGE.md) (tables et chaînes de calcul),
[CODES_DEFAUT](CODES_DEFAUT.md) (codes défaut et désactivation),
[VALEURS_ORIGINE_JEU0](VALEURS_ORIGINE_JEU0.md) / [JEU1](VALEURS_ORIGINE_JEU1.md) (valeurs d'origine).

---

## 1. Le propriétaire et ses règles

- Parle **français** : toujours répondre en français.
- Objectif : passer la voiture à l'**E85** et gagner un peu de puissance.
- Aucune ROM modifiée n'a encore été fabriquée ni demandée : **ne pas en fabriquer sans demande**.
- Git : dépôt `kilou5542/reprog`, dossier `meriva/`, branche `ccr-b93a7069-senejy`. Pas de PR sans demande.
- Il possède un dongle **WiCAN** (OBD) : utile pour logguer avance, régime, MAP, eau.

## 2. La voiture et le calculateur

- Opel **Meriva A 1.6 16V essence, 2004, moteur Z16XE**.
- Calculateur **Delphi** (probablement Multec-S / HSFI-2.1, non confirmé par catalogue),
  papillon motorisé (déduit du code : pédale `$9878` distincte du papillon `$97C6`).
- En-tête du fichier : `DEL 0115214590P`, n° GM **12230554**, code broadcast **EZ**,
  `D05003Z16XE 5`, logiciel `4300Sw1.20UV`, calibration **`HA6A4902.CAL`**.
- ROM d'origine : `roms/originales/meriva_z16xe_12230554_EZ.ori`,
  MD5 `83c7ed470b1eebbf6f6878d296044b9b`.

## 3. Format du fichier

- 256 Ko, flash vue par le processeur à **0x40000** (offset fichier = adresse − 0x40000).
- Processeur **Motorola CPU32** (68332). Mots en **big-endian** (pas d'inversion, contrairement à l'A2).
- Reset 0x46F80 → code à 0x6F80. **a5 = 0x48046** (base des appels et des accès calibration en d16(a5)).
- **Calibration 0x0000–0x6000**, programme ensuite. RAM en 0xFFFF8000+ (adresses `$8xxx`/`$9xxx`.w).
- Pas de VIN ni d'antidémarrage dans ce fichier (ils sont dans l'EEPROM).

## 4. Checksum (vérifié)

- Somme 16 bits des mots de **0x40–0x55** et **0x5E–0x3FFFF**, stockée en **0x5C** (origine 0x352B).
  Routine 0x1F3DC. L'octet 0x5E (0xFB) active le contrôle (0xAA le désactive).
- `scripts/fix_checksum.py rom.bin [sortie.bin]` le recalcule (testé).
- Une seconde somme (`$824C`) porte sur des zones de code et est calculée au démarrage : rien à faire.

## 5. Routines utiles

| Adresse fichier | Rôle |
|---|---|
| 0x5B30 / 0x5B4A | lecture table 1D octets / mots (jsr −$2516 / −$24FC(a5)), index 8.8 en D1, table en A1 |
| 0x5B64 / 0x5BCA | lecture table 2D octets / mots (jsr −$24E2 / −$247C(a5)) : D1 = ligne, D0 = colonne, largeur empilée |
| 0x5F2E | table des PID OBD mode 01 (n° PID → routine) : référence pour les unités |
| 0x0F4E0 | AFR cible moteur tournant ; 0xFC80 AFR de lancement à l'initialisation |
| 0x1075A | temps d'injection final (`$8B3E`) |
| 0x11D56 | masse carburant = masse d'air x 10 / AFR |
| 0x15F86 | avance à l'allumage ; 0x15CB0 avance principale |
| ~0x1F040 | machine d'état moteur (`$9070`) |
| 0x372E6 | commande d'injection (canal 5 = 4 injecteurs ensemble) |
| 0x649A | contrôle « code défaut actif » (bit 7 de l'octet de config) |
| 0x1F3DC | checksum flash |

Les instructions CPU32 **TBLU** (interpolation) sont mal décodées par capstone (« fmove », « fsqrt »).

## 6. Variables RAM (unités confirmées par les réponses OBD quand indiqué)

| Variable | Contenu |
|---|---|
| `$9644` | régime x 5,12 (OBD PID 0C) |
| `$9692` / `$969E` / `$96A0` / `$9698` / `$969A` / `$9694` | index régime : /400 (0–6400) ; /400 −1 (400–6400) ; /400 −2 (800–6400) ; /200 (0–3200) ; /400 (0–3200) ; /800 (0–6400) |
| `$95A2` | température d'eau, °C = 0,75 x octet − 40 (OBD PID 05) ; `$95A8` eau au démarrage |
| `$95AE` / `$95B6` / `$95B4` | index eau : −28…116 °C (13) ; −40…152 °C (17) ; −40…104 °C (13) |
| `$9701` / `$9702` | température d'air (OBD PID 0F) / index −28…116 °C |
| `$9760` | MAP x 51,2 (capteur GM 1 bar, 10,3–104,4 kPa ; OBD PID 0B) |
| `$9778` | MAP dilatée au-dessus de 80 kPa (axe de l'avance principale) |
| `$9782` / `$9788` | index MAP 20–100 kPa (9 points) ; `$9764` MAP corrigée |
| `$851E` | pression atmosphérique ; `$976E` = baro − MAP (dépression) |
| `$8E00` | débit d'air g/s x 256 (OBD PID 10) ; `$8E04` masse d'air par cylindre |
| `$8AFC` | AFR cible x 10 ; `$8B1D` AFR après pleine charge ; `$838C` enrichissement après démarrage |
| `$97C6` | papillon (OBD PID 11, 0–1023) ; `$9878` pédale ; `$97D0` papillon commandé |
| `$8CCE` | avance finale (octet, (x−64) x 0,3516 ; OBD PID 0E) |
| `$9808` | sélecteur de jeu de tables (option EEPROM) |
| `$9070` | état moteur (valeurs 1 à 5 ; signification exacte à confirmer) |
| `$8544` | état des codes défaut (2 octets par code) |

## 7. Ce qui est établi (détail dans INJECTION_ALLUMAGE)

- AFR en **x 10**. Moteur chaud : **14,6 fixe (0x0688)** + boucle fermée ; tables 2D d'AFR **seulement
  sous ~27–30 °C d'eau**. Pleine charge 0x0EA8 au-delà de 90 % de papillon commandé.
- Démarrage : AFR 0x0E32 − 0x0F70 ; amorçage 0x07D2 ; après démarrage 0x0BE4.
- Avance principale 0x16A8 / 0x15F8 ; tables adaptatives à zéro.
- Codes défaut : bit 7 de l'octet de config = actif (voir CODES_DEFAUT).

## 8. Incertitudes et pistes

- Jeu de tables utilisé (0 ou 1) : inconnu.
- Nature exacte de `$97D0` (papillon commandé) et du modèle de température d'échappement : déduites.
- Bits 5/4/2 des codes défaut (voyant) : non entièrement décodés.
- Pas encore localisés : retrait d'avance anti-cliquetis, limiteur de régime, coupure en décélération.
- Unité de l'impulsion d'amorçage (ticks TPU, période inconnue).

## 9. Journal des sessions

- **26–27/10/2026** : identification du calculateur, localisation des tables de démarrage, d'AFR et
  d'avance, checksum, codes défaut ; revérification complète par désassemblage (corrections :
  AFR 2D seulement à froid, axe de 0x07BE = dépression, axe air −28…116 °C, seuil pleine charge sur
  le papillon commandé). Création du dossier `meriva/`, outils et documentation.
