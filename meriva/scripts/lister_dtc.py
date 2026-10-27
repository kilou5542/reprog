#!/usr/bin/env python3
"""Liste les codes défaut de la ROM Z16XE et l'octet de configuration de chacun.

Usage : python3 lister_dtc.py rom.ori

Table des DTC en 0x6508 : entrées de 12 octets
  [pointeur CPU vers le mot de config (4)] [code BCD (2)] [sous-type (1)] [0 (1)] [pointeur (4)]
L'octet de config est le premier octet du mot pointé (zone 0x3646-0x374C).
  bit 7   : code actif. A 0, la fonction de contrôle 0x649A renvoie « non » et le calculateur
            n'enregistre ni ne déclare résolu ce défaut (vérifié dans le code).
  bits 5/4/2 : types qui comptent pour le voyant moteur (testés ensemble ; non entièrement décodé).
Pour désactiver un code : mettre son octet de config à 0x00, puis recalculer le checksum.
"""
import struct
import sys

DESC = {
    0x105: 'Capteur MAP', 0x110: 'Capteur temp. air', 0x115: 'Capteur temp. eau',
    0x120: 'Capteur papillon 1', 0x220: 'Capteur papillon 2', 0x130: 'Sonde lambda amont',
    0x135: 'Chauffage sonde amont', 0x136: 'Sonde lambda aval', 0x141: 'Chauffage sonde aval',
    0x170: 'Correction richesse', 0x201: 'Injecteur 1', 0x202: 'Injecteur 2', 0x203: 'Injecteur 3',
    0x204: 'Injecteur 4', 0x219: 'Surrégime', 0x230: 'Relais pompe à essence', 0x300: 'Ratés multiples',
    0x301: 'Ratés cyl. 1', 0x302: 'Ratés cyl. 2', 0x303: 'Ratés cyl. 3', 0x304: 'Ratés cyl. 4',
    0x325: 'Capteur cliquetis', 0x335: 'Capteur vilebrequin', 0x340: 'Capteur arbre à cames',
    0x351: 'Bobine 1', 0x352: 'Bobine 2', 0x353: 'Bobine 3', 0x354: 'Bobine 4', 0x400: 'EGR',
    0x420: 'Efficacité catalyseur', 0x443: 'Électrovanne canister', 0x460: 'Jauge carburant',
    0x500: 'Capteur vitesse véhicule', 0x505: 'Régulation ralenti', 0x530: 'Capteur pression clim',
    0x560: 'Tension batterie', 0x571: 'Contacteur frein', 0x602: 'Programmation calculateur',
    0x607: 'Calculateur interne', 0x650: 'Voyant moteur', 0x700: 'Défaut boîte (demande voyant)',
    0x1120: 'Capteur pédale 1', 0x1122: 'Capteur pédale 2', 0x1405: 'EGR', 0x1500: 'Démarreur',
    0x1550: 'Papillon motorisé', 0x1600: 'Calculateur interne', 0x1610: 'Antidémarrage',
    0x1611: 'Antidémarrage', 0x1612: 'Antidémarrage', 0x1613: 'Antidémarrage',
    0x1614: 'Antidémarrage', 0x1615: 'Antidémarrage', 0x1616: 'Antidémarrage',
    0x1620: 'Mémoire calculateur',
}

TABLE_DTC = 0x6508


def lister(rom):
    a = TABLE_DTC
    while True:
        p, code, sous, _, _ = struct.unpack('>IHBBI', rom[a:a + 12])
        if not 0x43000 <= p < 0x44000:
            break
        off = p - 0x40000
        yield code, sous, off, rom[off]
        a += 12


def main():
    rom = open(sys.argv[1], 'rb').read()
    print('| Code | Sous-type | Octet config | Valeur | État | Voyant | Description |')
    print('|---|---|---|---|---|---|---|')
    for code, sous, off, cfg in lister(rom):
        nom = 'P%04X' % code if code < 0xE000 else 'interne %04X' % code
        print('| %s | %02X | 0x%04X | 0x%02X | %s | %s | %s |' % (
            nom, sous, off, cfg, 'actif' if cfg & 0x80 else '**désactivé**',
            'oui' if cfg & 0x34 else 'non', DESC.get(code, '')))


if __name__ == '__main__':
    main()
