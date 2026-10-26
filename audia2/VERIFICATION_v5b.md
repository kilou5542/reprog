# Vérification complète — `roms/a2_ori_e85_v5b.bin`

Comparaison octet par octet avec l'origine CA (`audiori`) et avec la ROM « audiEGRoff… » (nom long).

## Généralités
- Checksum principal (0x7FFE8 / 0x7FFEA) et zone code (0x18584–0x1C4FF) : **OK**.
- **Aucune modification du code** : toutes les différences sont dans la calibration (0x54838–0x5D000), plus le mot de compensation du checksum.
- Zone 0x7FFBE–0x7FFC1 : identique à l'origine (la ROM nom long y avait d'autres valeurs, sans effet constaté).

## Toutes les zones modifiées par rapport à l'origine
| Zone | Rôle | Version | Contrôle |
|---|---|---|---|
| 0x54BB8–0x54D4F, 0x5CBAC–0x5CBF1 | configuration des défauts EGR (désactivés) | v1 | identique à la ROM nom long, pas de voyant constaté |
| 0x55688 (16×11), 0x55EB8 (24×12) | tables de couple | v4 | identiques à la ROM nom long |
| 0x5653A / 0x5653C | coupure d'injection (rupteur) | v5b | 6800 / 6800 |
| 0x569A0 | gain injecteur (E85 + 0 280 158 170 à 4 bar) | v1 | × 0,902 partout (1,45 / 1,607), cohérent |
| 0x56C38, 0x56C58 | consignes de ralenti | v1, v3 | décroissantes avec la température ; 850 à chaud |
| 0x57504 | correction air / température d'eau | v2 | lignes 0–11 = ROM nom long ; lignes 100/110 °C = origine (+6 %) |
| 0x57786 | modèle papillon 52 mm (Golf DR) | v1 | croissant selon l'angle, ≤ pression de référence, décroissant selon le régime |
| 0x57CAC–0x57CB6 | limiteur par le couple | v5b | 7100 / 6950 / 6500 / 7100 / 6950 / 7200, au-dessus de la coupure |
| 0x58B00, 0x58D40, 0x59046 | lambda cible | v2 | = ROM nom long ; base 0,85–1,05, pleine charge 0,88 → 0,85 |
| 0x59708, 0x5B8B6 | amorçage et budget (Craaaaanking) | v1 | 2 impulsions sous −10 °C et au-dessus de 40 °C, 1 entre les deux |
| 0x5BA32 | fin de la régulation de cliquetis | v5 | 6800 (5900 d'origine et dans la ROM nom long) |
| 0x5BA66, 0x5BCAE, 0x5C220 | avance | v2 | = ROM nom long ; base −4,0° à 33,0° |

Restent d'origine (volontairement) : VE 0x57084, K de démarrage 0x57E72 = 1229, trims STFT 30000–50000 /
LTFT 26000–54000 (plafond 41600), test de débit EGR 0x5B970 = 0001, conso 0x5BA22 = 740.

## Autres seuils liés au régime (recherchés dans tout le code)
Seuils de calibration entre 5500 et 6600 lus par le code et comparés au régime :
- 0x57ACA = 5700 : l'adaptation du modèle papillon ne se fait que sous 5700 (bloquée en v5 de toute façon) ;
- 0x5AF8C = 5800 : une fonction de diagnostic (0x41F56) n'est active que sous 5800.
Aucun autre limiteur de régime. Axes en régime limités à 6000 : au-delà, les tables gardent leur dernière colonne.

## Points à surveiller (non modifiés)
- **Débit injecteurs en haut du compte-tours.** Estimation : environ 0,33 g d'air par cylindre et par cycle,
  E85 à λ 0,85–0,88, injecteurs environ 200 cm³/min à 4 bar. Il faut alors environ 15–16 ms d'injection, temps mort compris,
  pour une fenêtre de 17,6 ms à 6800 tr/min, soit **environ 90 % de rapport cyclique**. À vérifier par log VCDS
  (temps d'injection et lambda à pleine charge au-dessus de 6000).
- **Lignes 100 / 110 °C de 0x57504** : +6 % d'origine (la ROM nom long les avait à 1,00). C'est une protection contre la surchauffe, gardée.
- **Rupteur au point mort** : 6800 − 2500 = 4300 tr/min (0x56546, réglage d'origine).
- **Mollesse et délai avant coupure** par rapport à la ROM nom long : seul le modèle papillon diffère dans ce domaine (voir CHANGELOG).
