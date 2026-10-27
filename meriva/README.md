# Opel Meriva 1.6 16V Z16XE (2004) — Delphi 12230554 / EZ

Analyse de la ROM d'origine en vue d'un passage à l'**E85**. Aucune ROM modifiée pour l'instant.

## Contenu
| Fichier / dossier | Contenu |
|---|---|
| `MEMOIRE.md` | **à lire en premier** : tout ce qui a été appris (pour une nouvelle session) |
| `INJECTION_ALLUMAGE.md` | tables d'injection, d'AFR, de démarrage et d'allumage, avec les chaînes de calcul |
| `CODES_DEFAUT.md` | les 129 codes défaut, leur octet de configuration et comment les désactiver |
| `VALEURS_ORIGINE_JEU0.md` / `..._JEU1.md` | valeurs d'origine de toutes les tables (deux jeux) |
| `roms/originales/` | lecture d'origine du calculateur (`meriva_z16xe_12230554_EZ.ori`) |
| `scripts/` | checksum, définition des tables, affichage des tables, liste des codes défaut |
| `outils_desassemblage/` | désassemblage CPU32, liste des appels de tables, affichage d'un passage |

## Format du fichier
- 256 Ko, processeur Motorola CPU32, flash vue à **0x40000** (adresses données en offsets fichier).
- Mots en **big-endian** (TunerPro : MSB first ; WinOLS : « Hi-Lo »).
- Calibration de 0x0000 à 0x6000, programme ensuite ; `a5 = 0x48046`.

## Checksum
Somme 16 bits des mots de 0x40–0x55 et 0x5E–0x3FFFF, stockée en 0x5C. Après une modification :
```
python3 scripts/fix_checksum.py ma_rom.bin ma_rom_ok.bin
```

## Scripts
```
cd scripts
python3 afficher_tables.py ../roms/originales/meriva_z16xe_12230554_EZ.ori 0   # tables du jeu 0
python3 lister_dtc.py ../roms/originales/meriva_z16xe_12230554_EZ.ori          # codes défaut
```
Il faut Python 3. Le désassemblage demande en plus le module `capstone` :
```
cd outils_desassemblage
python3 desassembler.py ../roms/originales/meriva_z16xe_12230554_EZ.ori full.asm
python3 appels_tables.py full.asm
./voir.sh full.asm 015cb0 0 60
```
