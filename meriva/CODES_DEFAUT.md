# Codes défaut — Delphi Z16XE (12230554 / EZ)

Liste générée par `scripts/lister_dtc.py` à partir de la ROM d'origine.

## Fonctionnement (vérifié dans le code)

- **Table des codes en 0x6508** : 129 entrées de 12 octets
  `[pointeur vers le mot de config][code BCD][sous-type][0][pointeur]`.
- **Octets de configuration de 0x3646 à 0x374C**, dans la zone de calibration. Un octet par code et
  sous-type (le sous-type distingue, par exemple, tension trop haute et trop basse).
- **Bit 7 = code actif.** Toutes les routines qui enregistrent un défaut (0x62B4) ou le déclarent
  résolu (0x627A) appellent d'abord la fonction de contrôle 0x649A. Elle renvoie « non » si le bit 7
  est à 0 : le défaut est alors ignoré, sans code ni voyant.
- **Le constructeur l'utilise lui-même** : les codes sans objet sur ce moteur sont à `0x00`
  (EGR P0400 / P1405, régulation de ralenti par vanne P0505, cohérent avec un papillon motorisé).
- **Bits 5, 4 et 2** : très probablement les types qui allument le voyant moteur (testés toujours
  ensemble ; le bit 2 est lié à un compteur de cycles). **Non entièrement décodé** : garder le code
  actif sans voyant en ne mettant que ces bits à 0 reste à essayer.

## Désactiver un code

1. Mettre l'octet de configuration à `0x00` (comme les codes désactivés d'usine).
2. Recalculer le checksum : `python3 scripts/fix_checksum.py rom.bin`.

**Précautions**
- Ne jamais désactiver l'antidémarrage (P1610 à P1616), ni P0602, P0607, P1600, P1620.
- Désactiver un code coupe aussi le mode de secours associé (par exemple le retrait d'avance de
  sécurité quand le capteur de cliquetis est en défaut). À réserver aux éléments réellement retirés.
- Supprimer le catalyseur ou ses diagnostics rend la voiture non conforme au contrôle technique.

## Liste complète

| Code | Sous-type | Octet config | Valeur | État | Voyant | Description |
|---|---|---|---|---|---|---|
| P0105 | 01 | 0x3646 | 0xE1 | actif | oui | Capteur MAP |
| P0105 | 02 | 0x3648 | 0xE1 | actif | oui | Capteur MAP |
| P0110 | 02 | 0x364A | 0xC5 | actif | oui | Capteur temp. air |
| P0110 | 01 | 0x364C | 0xC5 | actif | oui | Capteur temp. air |
| P0115 | 00 | 0x364E | 0x00 | **désactivé** | non | Capteur temp. eau |
| P0115 | 02 | 0x3650 | 0xC5 | actif | oui | Capteur temp. eau |
| P0115 | 01 | 0x3652 | 0xC5 | actif | oui | Capteur temp. eau |
| P0115 | 08 | 0x3654 | 0xC5 | actif | oui | Capteur temp. eau |
| P0120 | 01 | 0x3656 | 0xC9 | actif | non | Capteur papillon 1 |
| P0120 | 02 | 0x3658 | 0xC9 | actif | non | Capteur papillon 1 |
| P0120 | 08 | 0x365E | 0xC9 | actif | non | Capteur papillon 1 |
| P0220 | 01 | 0x3660 | 0xC9 | actif | non | Capteur papillon 2 |
| P0220 | 02 | 0x3662 | 0xC9 | actif | non | Capteur papillon 2 |
| P0130 | 01 | 0x3664 | 0xC5 | actif | oui | Sonde lambda amont |
| P0130 | 02 | 0x3666 | 0xC5 | actif | oui | Sonde lambda amont |
| P0130 | 04 | 0x3668 | 0xC5 | actif | oui | Sonde lambda amont |
| P0130 | 0A | 0x366A | 0xC5 | actif | oui | Sonde lambda amont |
| P0130 | 0B | 0x366C | 0xC5 | actif | oui | Sonde lambda amont |
| P0130 | 0C | 0x366E | 0xC5 | actif | oui | Sonde lambda amont |
| P0135 | 00 | 0x3670 | 0xC5 | actif | oui | Chauffage sonde amont |
| P0136 | 01 | 0x3672 | 0xC5 | actif | oui | Sonde lambda aval |
| P0136 | 02 | 0x3674 | 0xC5 | actif | oui | Sonde lambda aval |
| P0136 | 04 | 0x3676 | 0xC5 | actif | oui | Sonde lambda aval |
| P0141 | 00 | 0x3678 | 0xC5 | actif | oui | Chauffage sonde aval |
| P0170 | 01 | 0x367A | 0xC5 | actif | oui | Correction richesse |
| P0170 | 02 | 0x367C | 0xC5 | actif | oui | Correction richesse |
| P0170 | 0A | 0x367E | 0xC5 | actif | oui | Correction richesse |
| P0170 | 0B | 0x3680 | 0xC5 | actif | oui | Correction richesse |
| P0201 | 00 | 0x3682 | 0xE1 | actif | oui | Injecteur 1 |
| P0202 | 00 | 0x3684 | 0xE1 | actif | oui | Injecteur 2 |
| P0203 | 00 | 0x3686 | 0xE1 | actif | oui | Injecteur 3 |
| P0204 | 00 | 0x3688 | 0xE1 | actif | oui | Injecteur 4 |
| P0219 | 01 | 0x368A | 0x89 | actif | non | Surrégime |
| P0230 | 00 | 0x368C | 0x89 | actif | non | Relais pompe à essence |
| P0230 | 01 | 0x368E | 0x89 | actif | non | Relais pompe à essence |
| P0230 | 04 | 0x3690 | 0x89 | actif | non | Relais pompe à essence |
| P0300 | 00 | 0x3692 | 0xC5 | actif | oui | Ratés multiples |
| P0300 | 0A | 0x3694 | 0xC5 | actif | oui | Ratés multiples |
| P0300 | 0B | 0x3696 | 0x89 | actif | non | Ratés multiples |
| P0301 | 00 | 0x3698 | 0xC5 | actif | oui | Ratés cyl. 1 |
| P0302 | 00 | 0x369A | 0xC5 | actif | oui | Ratés cyl. 2 |
| P0303 | 00 | 0x369C | 0xC5 | actif | oui | Ratés cyl. 3 |
| P0304 | 00 | 0x369E | 0xC5 | actif | oui | Ratés cyl. 4 |
| P0325 | 00 | 0x36A0 | 0xC9 | actif | non | Capteur cliquetis |
| P0335 | 00 | 0x36A2 | 0xE1 | actif | oui | Capteur vilebrequin |
| P0335 | 08 | 0x36A4 | 0xE1 | actif | oui | Capteur vilebrequin |
| P0335 | 0A | 0x36A6 | 0x00 | **désactivé** | non | Capteur vilebrequin |
| P0340 | 00 | 0x36A8 | 0xC9 | actif | non | Capteur arbre à cames |
| P0340 | 0A | 0x36AA | 0x89 | actif | non | Capteur arbre à cames |
| P0351 | 00 | 0x36AC | 0xE1 | actif | oui | Bobine 1 |
| P0352 | 00 | 0x36AE | 0xE1 | actif | oui | Bobine 2 |
| P0353 | 00 | 0x36B0 | 0xE1 | actif | oui | Bobine 3 |
| P0354 | 00 | 0x36B2 | 0xE1 | actif | oui | Bobine 4 |
| P0400 | 0A | 0x36B4 | 0x00 | **désactivé** | non | EGR |
| P0400 | 0B | 0x36B6 | 0x00 | **désactivé** | non | EGR |
| P0400 | 0C | 0x36B8 | 0x00 | **désactivé** | non | EGR |
| P0420 | 00 | 0x36BA | 0xE1 | actif | oui | Efficacité catalyseur |
| P0443 | 01 | 0x36BC | 0xC5 | actif | oui | Électrovanne canister |
| P0443 | 04 | 0x36BE | 0xC5 | actif | oui | Électrovanne canister |
| P0460 | 00 | 0x36C0 | 0x89 | actif | non | Jauge carburant |
| P0460 | 01 | 0x36C2 | 0x89 | actif | non | Jauge carburant |
| P0460 | 02 | 0x36C4 | 0x89 | actif | non | Jauge carburant |
| P0500 | 00 | 0x374C | 0xC9 | actif | non | Capteur vitesse véhicule |
| P0505 | 00 | 0x36C6 | 0x00 | **désactivé** | non | Régulation ralenti |
| P0530 | 01 | 0x36C8 | 0x89 | actif | non | Capteur pression clim |
| P0530 | 02 | 0x36CA | 0x89 | actif | non | Capteur pression clim |
| P0560 | 01 | 0x36CC | 0x89 | actif | non | Tension batterie |
| P0560 | 02 | 0x36CE | 0x89 | actif | non | Tension batterie |
| P0571 | 04 | 0x36D0 | 0xC9 | actif | non | Contacteur frein |
| P0602 | 00 | 0x36D2 | 0xC8 | actif | non | Programmation calculateur |
| P0602 | 04 | 0x36D4 | 0xC8 | actif | non | Programmation calculateur |
| P0602 | 08 | 0x36D6 | 0xC8 | actif | non | Programmation calculateur |
| P0607 | 00 | 0x36D8 | 0xC9 | actif | non | Calculateur interne |
| P0650 | 01 | 0x36DA | 0x89 | actif | non | Voyant moteur |
| P0650 | 02 | 0x36DC | 0x89 | actif | non | Voyant moteur |
| P0700 | 0A | 0x36DE | 0xC9 | actif | non | Défaut boîte (demande voyant) |
| P1120 | 01 | 0x36E2 | 0xC9 | actif | non | Capteur pédale 1 |
| P1120 | 02 | 0x36E4 | 0xC9 | actif | non | Capteur pédale 1 |
| P1120 | 08 | 0x36E6 | 0xC9 | actif | non | Capteur pédale 1 |
| P1122 | 01 | 0x36E8 | 0xC9 | actif | non | Capteur pédale 2 |
| P1122 | 02 | 0x36EA | 0xC9 | actif | non | Capteur pédale 2 |
| P1230 | 0A | 0x36EC | 0xC9 | actif | non |  |
| P1230 | 0B | 0x36EE | 0xC9 | actif | non |  |
| P1345 | 00 | 0x36F0 | 0x89 | actif | non |  |
| P1405 | 01 | 0x36F2 | 0x00 | **désactivé** | non | EGR |
| P1405 | 02 | 0x36F4 | 0x00 | **désactivé** | non | EGR |
| P1481 | 01 | 0x36F6 | 0xC9 | actif | non |  |
| P1481 | 04 | 0x36F8 | 0xC9 | actif | non |  |
| P1482 | 01 | 0x36FA | 0xC9 | actif | non |  |
| P1482 | 04 | 0x36FC | 0xC9 | actif | non |  |
| P1483 | 01 | 0x36FE | 0xC9 | actif | non |  |
| P1483 | 04 | 0x3700 | 0xC9 | actif | non |  |
| P1500 | 00 | 0x3702 | 0xC9 | actif | non | Démarreur |
| P1550 | 0A | 0x3704 | 0xC9 | actif | non | Papillon motorisé |
| P1550 | 0B | 0x3706 | 0xC9 | actif | non | Papillon motorisé |
| P1550 | 0C | 0x3708 | 0xC9 | actif | non | Papillon motorisé |
| P1550 | 0D | 0x370A | 0xC9 | actif | non | Papillon motorisé |
| P1530 | 01 | 0x370C | 0x89 | actif | non |  |
| P1530 | 04 | 0x370E | 0x89 | actif | non |  |
| P1571 | 04 | 0x3710 | 0xC9 | actif | non |  |
| P1600 | 0A | 0x3712 | 0xC9 | actif | non | Calculateur interne |
| P1600 | 0B | 0x3714 | 0x89 | actif | non | Calculateur interne |
| P1600 | 0D | 0x3718 | 0x89 | actif | non | Calculateur interne |
| P1600 | 0E | 0x371A | 0x89 | actif | non | Calculateur interne |
| P1610 | 00 | 0x371C | 0xCA | actif | non | Antidémarrage |
| P1610 | 04 | 0x371E | 0x88 | actif | non | Antidémarrage |
| P1611 | 00 | 0x3720 | 0xCA | actif | non | Antidémarrage |
| P1612 | 00 | 0x3722 | 0xCB | actif | non | Antidémarrage |
| P1613 | 00 | 0x3724 | 0xCB | actif | non | Antidémarrage |
| P1614 | 04 | 0x3726 | 0xCB | actif | non | Antidémarrage |
| P1614 | 00 | 0x3728 | 0xCB | actif | non | Antidémarrage |
| P1615 | 00 | 0x372A | 0xCB | actif | non | Antidémarrage |
| P1616 | 00 | 0x372C | 0xCB | actif | non | Antidémarrage |
| P1620 | 0A | 0x372E | 0xE1 | actif | oui | Mémoire calculateur |
| P1620 | 0B | 0x3730 | 0xE1 | actif | oui | Mémoire calculateur |
| P1700 | 0A | 0x36E0 | 0xC9 | actif | non |  |
| P1811 | 08 | 0x3732 | 0xC9 | actif | non |  |
| P1811 | 0A | 0x3734 | 0x89 | actif | non |  |
| P1811 | 0B | 0x3736 | 0x89 | actif | non |  |
| P1813 | 08 | 0x3738 | 0xC9 | actif | non |  |
| P1813 | 0A | 0x373A | 0xC9 | actif | non |  |
| P1813 | 0B | 0x373C | 0x89 | actif | non |  |
| P1813 | 0C | 0x373E | 0x89 | actif | non |  |
| interne E101 | 08 | 0x3740 | 0xC8 | actif | non |  |
| interne E103 | 00 | 0x3742 | 0x89 | actif | non |  |
| interne E104 | 00 | 0x3744 | 0x89 | actif | non |  |
| interne E106 | 00 | 0x3746 | 0xC9 | actif | non |  |
| interne E107 | 00 | 0x3748 | 0x89 | actif | non |  |
| interne E108 | 00 | 0x374A | 0x89 | actif | non |  |
