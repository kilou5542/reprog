# Audi A2 1.4 BBY — Marelli 4MV 036906034CA (E85)

ROM de travail : **`roms/a2_ori_e85_v5f.bin`** (v5 + rupteur franc à 7000, validée sur route) — base de toutes les prochaines modifications ; à essayer : **`roms/a2_ori_e85_v5g.bin`** (v5f + coupure plus rapide au lâcher de pédale), puis **`roms/a2_ori_e85_v5h.bin`** (v5g + apprentissage du modèle papillon débloqué, EGR intacte). L'historique des versions est dans [CHANGELOG.md](CHANGELOG.md).

## Contenu
| Dossier | Contenu |
|---|---|
| `roms/` | ROM de travail (v5f) ; v7c / v10c en alternative non retenue |
| `roms/historique/` | toutes les versions intermédiaires |
| `roms/originales/` | origine CA (`audiori`), ta ROM modifiée « audiEGRoff… », Golf 4 DR, BackupAudiSemiOK, projet WinOLS |
| `tunerpro/` | définition TunerPro `A2_4MV_036906034CA_E85.xdf` |
| `scripts/` | scripts Python qui produisent chaque version |
| `outils_desassemblage/` | aides au désassemblage (références `$xxxx(a5)`, axes) |
| `MESURES.md` | relevés faits sur la voiture (ralenti, pression, angle papillon) |
| `ANALYSE_COUPLE.md` | structure de couple du calculateur (analyse du code en cours) |

## Format du fichier
- 512 Ko, processeur Motorola CPU32 ; RAM du programme `a5 = 0xE5770`.
- Le dump est stocké **octets inversés par mot** : les valeurs 16 bits se lisent en *little-endian*
  (TunerPro : LSB first, WinOLS : « Lo-Hi »). Les adresses données partout sont valables telles
  quelles pour les mots ; pour un octet isolé, c'est l'adresse XOR 1.

## Checksum (TunerPro ne le corrige pas)
- Principal : somme 16 bits des mots de 0x04000 à 0x7FFFF = mot 0x7FFE8, compensation 0x7FFEA.
  Un checksum faux donne le défaut P0605.
- Zone code 0x18584–0x1C4FF : contrôlée à part, à ne pas modifier.

Après une modification dans TunerPro :
```
python3 scripts/marelli4mv.py fix ma_rom.bin ma_rom_ok.bin
python3 scripts/marelli4mv.py ma_rom_ok.bin        # vérification
```
Il faut Python 3. Le désassemblage demande en plus le module `capstone`.

## TunerPro
Sur la v5, la catégorie « Patchs (v8-v10) » du XDF ne veut rien dire (zone vide, 0xFFFF) : ne pas y toucher.

Ouvrir `tunerpro/A2_4MV_036906034CA_E85.xdf`, puis le `.bin`. Les tables sont rangées par catégories :
carburant, lambda, allumage, papillon, couple, ralenti / démarrage, régime maxi (coupure, reprise d'injection 0x5B8EA, limiteur), trims, coupure,
régulateur, boîte, patchs. Les axes sont lus dans le fichier.

Les axes et les tailles ont été établis en désassemblant le code, pas d'après les noms WinOLS.
Certaines unités restent brutes, quand l'échelle n'est pas certaine (couple, modèle papillon, gain injecteur).

## Lecture des trims dans VCDS
- STFT : interne = 40000 + intégrateur ; affiché (40000 − x) / 400, signe normal (+ = enrichit).
- LTFT : affiché (x − 40000) / 400, **signe inversé** sur ce calculateur.

## Reproduire les ROM depuis l'origine
```
cd scripts
O=../roms/originales
H="$O/audiEGRoff__bestlambda_spark3-6_VEcorrectiondiv4_VEtest3rpmmax-testmaxairfilling.bin"
python3 construire_depuis_ori.py $O/audiori_036906034CA.bin "$H" $O/golf4_DR500.bin $O/winols_v4_BackupAudiSemiOK.bin v1.bin
python3 reporter_tables.py "$H" v1.bin v2.bin
python3 etapes_v3_a_v7.py v2.bin "$H" v7c.bin          # v3 à v5 inclus, puis v6/v7 (alternative)
python3 regulateur_coupure.py v5.bin v5r.bin             # v5 : sortie de la v5 de l'historique
python3 conso_e85.py v5r.bin v5_regul_conso.bin
python3 rupteur.py v5.bin v5f.bin 7000                 # ROM de travail
python3 coupure_rapide.py ../roms/originales/A2_CA-DR_7000_afterlogNG4_cranking_idle_VEbyT3_maxairfiling_2torqueori15.bin v5f.bin v5g.bin
python3 adaptation_papillon.py v5g.bin v5h.bin
python3 generer_xdf.py A2.xdf
```
La chaîne a été vérifiée : elle redonne les ROM du dépôt à l'octet près.
