#!/usr/bin/env python3
"""Génère la définition TunerPro (.xdf) pour Audi A2 BBY, Marelli 4MV 036906034CA (+ patchs v10).

Le fichier .bin lu par TunerPro est le dump tel quel : octets inversés par mot, donc valeurs 16 bits
en little-endian (lsbfirst). Les adresses ci-dessous sont celles du code (big-endian) ; elles sont
identiques dans le fichier pour les mots, et XOR 1 pour les octets isolés.
Les axes sont lus dans le fichier (ils suivent donc les modifications), avec leur conversion.

  python3 generer_xdf.py sortie.xdf
"""
import sys
import unicodedata
from xml.sax.saxutils import escape

LE, SIGNED = 0x02, 0x01

# Axes : nom -> (adresse, nombre de points, formule, unité, signé)
AX = {
    'rpm24':  (0x5619C, 24, 'X', 'tr/min', False),
    'rpm16':  (0x561FC, 16, 'X', 'tr/min', False),
    'charge': (0x56164, 12, 'X/100', '% charge', False),
    'map':    (0x5627C, 12, 'X', 'mbar', False),
    'eau':    (0x562EC, 16, 'X-40', '°C eau', False),
    'angle':  (0x57064, 16, 'X', 'angle papillon (brut)', False),
    'depr':   (0x56988, 12, 'X', 'mbar dépression', False),
    'couple_x': (0x563DE, 11, 'X', 'demande (brut)', False),
    'charge4': (0x5BCA6, 4, 'X/100', '% charge', False),
    'vitesse': (0x5C7CE, 8, 'X/16', 'km/h', False),
}

# Catégories
CATS = ['Carburant / E85', 'Lambda', 'Allumage', 'Papillon / air', 'Couple', 'Ralenti / démarrage',
        'Régime maxi', 'Trims', 'Coupure décélération', 'Régulateur de vitesse', 'Boîte de vitesses',
        'Patchs (v8-v10)']

# Tables : (catégorie, titre, adresse, lignes, colonnes, axe lignes, axe colonnes, formule, unité, signé, décimales, description)
TABLES = [
    (0, 'VE (rendement volumétrique)', 0x57084, 24, 12, 'rpm24', 'map', 'X/10000', 'facteur', False, 4,
     'Lecture 0x2317A. Masse d\'air = f(pression collecteur) x VE. Gardée d\'origine en v10 (E85 porté par le gain).'),
    (0, 'Correction air / température d\'eau (enrichissement à froid)', 0x57504, 16, 12, 'eau', 'map', 'X/10000', 'facteur', False, 4,
     'Lecture 0x232E8. 1.0000 = neutre. Lignes 100/110 °C : +6 % d\'origine (protection surchauffe).'),
    (0, 'Gain injecteur (vs dépression)', 0x569A0, 1, 12, None, 'depr', 'X', 'brut', False, 0,
     'Fct 0x1FF8A. Porte le facteur E85 x1,45 et le débit des 0 280 158 170 à 4 bar.'),
    (1, 'Lambda cible de base', 0x58B00, 24, 12, 'rpm24', 'charge', 'X/1000', 'lambda', False, 3, 'Lecture 0x33094.'),
    (1, 'Lambda cible protection (composants)', 0x58D40, 24, 12, 'rpm24', 'charge', 'X/1000', 'lambda', False, 3, 'Lecture 0x330F0.'),
    (1, 'Lambda pleine charge', 0x59046, 1, 24, None, 'rpm24', 'X/1000', 'lambda', False, 3, 'Lecture 0x3315E.'),
    (2, 'Avance de base', 0x5BA66, 24, 12, 'rpm24', 'charge', 'X/10', '°', True, 1, 'Fct 0x4CD32.'),
    (2, 'Avance pleine charge (correction)', 0x5BCAE, 24, 4, 'rpm24', 'charge4', 'X/10', '°', True, 1, 'Fct 0x4CF0E.'),
    (2, 'Avance 0x5C220 (plafond)', 0x5C220, 24, 12, 'rpm24', 'charge', 'X/10', '°', True, 1, 'Fct 0x4E7DA.'),
    (3, 'Modèle papillon (pression vs angle) - 52 mm', 0x57786, 16, 16, 'rpm16', 'angle', 'X', 'mbar', False, 0,
     'Lectures 0x22EC6 / 0x23A20. Recalé Golf 52 mm (036 133 062 M). Cause du P1553 si faux.'),
    (4, 'Couple 0x55688', 0x55688, 16, 11, 'rpm16', 'couple_x', 'X', 'brut', False, 0, 'Lectures 0xDACE / 0xDBCE.'),
    (4, 'Couple 0x55EB8', 0x55EB8, 24, 12, 'rpm24', 'charge', 'X', 'brut', False, 0, 'Fct 0x10D8C.'),
    (5, 'Consigne ralenti (table 1)', 0x56C58, 1, 16, None, 'eau', 'X', 'tr/min', False, 0, 'Froid relevé +150 en v7, chaud 850.'),
    (5, 'Consigne ralenti (table 2)', 0x56C38, 1, 16, None, 'eau', 'X', 'tr/min', False, 0, ''),
    (5, 'Amorçage démarrage (Craaaaanking)', 0x59708, 1, 16, None, 'eau', 'X', 'brut', False, 0,
     'Masse d\'amorçage par impulsion.'),
    (5, 'Budget total d\'amorçage', 0x5B8B6, 1, 16, None, 'eau', 'X', 'brut', False, 0, ''),
    (6, 'Limiteur par le couple (début, relâche, bas rampe, régul on/off, maxi)', 0x57CAC, 1, 6, None, None, 'X', 'tr/min', False, 0,
     'Fct 0x26930. Les 4 groupes de régime maxi doivent rester cohérents.'),
    (6, 'Coupure injection surrégime (haut / bas)', 0x5653A, 1, 2, None, None, 'X', 'tr/min', False, 0, 'Fct 0x14F58.'),
    (9, 'Couple de base régulateur (par rapport x vitesse)', 0x5C7DE, 6, 8, None, 'vitesse', 'X/16', 'Nm', True, 1,
     'Lignes = rapport 0 à 5. Couple pour rouler à plat.'),
    (9, 'Gain P régulateur (par rapport 0-5)', 0x5C780, 1, 6, None, None, 'X', 'brut', False, 0, ''),
    (9, 'Gain I régulateur (par rapport 0-5)', 0x5C78C, 1, 6, None, None, 'X', 'brut', False, 0, ''),
    (10, 'Centre de chaque rapport (vitesse/régime)', 0x5A046, 1, 5, None, None, 'X', 'brut', False, 0,
     'Reconnaissance du rapport engagé (fct 0x3A100).'),
    (10, 'Seuils entre rapports', 0x5A038, 1, 6, None, None, 'X', 'brut', False, 0, ''),
]

# Constantes : (catégorie, titre, adresse, formule, unité, signé, décimales, bits, description)
CONSTS = [
    (0, 'Facteur injection démarrage (K)', 0x57E72, 'X', 'brut', False, 0, 16, 'Multiplie le temps d\'injection (fct 0x2AAF0).'),
    (0, 'Masse volumique carburant (conso ordinateur de bord)', 0x5BA22, 'X', 'g/l', False, 0, 16,
     'Origine 740 (essence). E85 : 785 / 1,45 = 541. Affinage : valeur x conso affichée / conso réelle.'),
    (3, 'Pression de référence modèle papillon', 0x57AC6, 'X', 'mbar', False, 0, 16, ''),
    (6, 'Reprise injection après coupure de régime', 0x5B8EA, 'X', 'tr/min', False, 0, 16,
     'Fct 0x46782 : au seuil de coupure, 100 % des injections coupées jusqu\'à repasser sous cette valeur. Origine 5610 : mettre = coupure.'),
    (6, 'Seuil défaut surrégime', 0x56542, 'X', 'tr/min', False, 0, 16, 'Chemin de défaut 44.'),
    (6, 'Régime maxi régulation de cliquetis', 0x5BA32, 'X', 'tr/min', False, 0, 16, ''),
    (7, 'STFT butée basse (40000 = neutre)', 0x596BC, '(40000-X)/400', '% (signe VCDS)', False, 1, 16, 'Brut 30000 = +25 %.'),
    (7, 'STFT butée haute', 0x596BE, '(40000-X)/400', '% (signe VCDS)', False, 1, 16, 'Brut 50000 = -25 %.'),
    (7, 'LTFT butée basse', 0x5CEA0, '(X-40000)/400', '% (signe VCDS)', False, 1, 16, ''),
    (7, 'LTFT butée haute', 0x5CEA2, '(X-40000)/400', '% (signe VCDS)', False, 1, 16, ''),
    (7, 'LTFT plafond après démarrage', 0x5CEB8, '(X-40000)/400', '% (signe VCDS)', False, 1, 16, ''),
    (8, 'Sortie coupure : pédale >', 0x5AA76, 'X/10', '% pédale', False, 1, 16, ''),
    (8, 'Entrée coupure : seuil $1272', 0x5AA7A, 'X', 'brut', False, 0, 16, ''),
    (9, 'Vitesse mini régulateur', 0x59254, 'X', 'km/h', False, 0, 16, ''),
    (9, 'Vitesse maxi régulateur', 0x59256, 'X', 'km/h', False, 0, 16, ''),
    (9, 'Désactivation si vitesse > consigne +', 0x57E64, 'X', 'km/h', False, 0, 16, ''),
    (9, 'Couple maxi régulateur', 0x5C772, 'X/16', 'Nm', True, 1, 16, ''),
    (9, 'Couple mini régulateur', 0x5C774, 'X/16', 'Nm', True, 1, 16, ''),
    (9, 'Butée P haute', 0x5C776, 'X/16', 'Nm', True, 1, 16, 'Origine 480.'),
    (9, 'Butée P basse', 0x5C778, 'X/16', 'Nm', True, 1, 16, 'Origine -160, v9 -480.'),
    (9, 'Butée I haute', 0x5C77A, 'X/128', 'Nm', True, 1, 16, 'Origine 5120.'),
    (9, 'Butée I basse', 0x5C77C, 'X/128', 'Nm', True, 1, 16, 'Origine -1280, v9 -8000.'),
    (9, 'Montée maxi du couple par cycle', 0x5C77E, 'X/16', 'Nm', True, 1, 16, ''),
    (10, 'Nombre de rapports', 0x5A036, 'X', '', False, 0, 16, ''),
    (10, 'Tolérance reconnaissance rapport', 0x5A054, 'X', 'brut', False, 0, 16, ''),
    (11, 'Coupure régulateur : écart vitesse pour couper', 0x7F238, 'X/16', 'km/h', True, 2, 16,
     'Patch 0x7F1C0. 2047.9 (brut 32767) = coupure désactivée.'),
    (11, 'Coupure régulateur : couple maxi pour couper', 0x7F23A, 'X/16', 'Nm', True, 1, 16, ''),
    (11, 'Coupure régulateur : écart vitesse pour maintenir', 0x7F23C, 'X/16', 'km/h', True, 2, 16, ''),
    (11, 'Coupure régulateur : couple maxi pour maintenir', 0x7F23E, 'X/16', 'Nm', True, 1, 16, ''),
]


REMPLACE = {'°': 'deg', '×': 'x', '≥': '>=', '≤': '<=', '→': '->', '«': '"', '»': '"', '’': "'",
            'œ': 'oe', '—': '-', '–': '-', '…': '...', '±': '+/-'}


def ascii_seul(texte):
    """TunerPro gère mal les accents : tout le fichier est ramené à l'ASCII pur."""
    for k, v in REMPLACE.items():
        texte = texte.replace(k, v)
    texte = unicodedata.normalize('NFKD', texte).encode('ascii', 'ignore').decode('ascii')
    return texte


class Xdf:
    def __init__(self):
        self.out = []
        self.uid = 0x1000

    def add(self, s):
        self.out.append(s)

    def next_uid(self):
        self.uid += 1
        return self.uid

    @staticmethod
    def math(f):
        return f'      <MATH equation="{escape(f)}">\n        <VAR id="X" />\n      </MATH>\n'

    @staticmethod
    def flags(signed):
        return f'0x{LE | (SIGNED if signed else 0):02X}'

    def axis(self, ident, n, ax):
        if ax is None:
            labels = ''.join(f'      <LABEL index="{i}" value="{i}" />\n' for i in range(n))
            return (f'    <XDFAXIS id="{ident}" uniqueid="0x0">\n      <EMBEDDEDDATA mmedelementsizebits="16" mmedmajorstridebits="-32" mmedminorstridebits="0" />\n'
                    f'      <units></units>\n      <indexcount>{n}</indexcount>\n      <datatype>0</datatype>\n      <unittype>0</unittype>\n'
                    f'      <DALINK index="0" />\n{labels}' + self.math('X') + '    </XDFAXIS>\n')
        a, cnt, f, unit, signed = AX[ax]
        assert cnt == n, (ax, cnt, n)
        return (f'    <XDFAXIS id="{ident}" uniqueid="0x0">\n'
                f'      <EMBEDDEDDATA mmedtypeflags="{self.flags(signed)}" mmedaddress="0x{a:X}" mmedelementsizebits="16" mmedmajorstridebits="0" mmedminorstridebits="0" />\n'
                f'      <units>{escape(unit)}</units>\n      <indexcount>{n}</indexcount>\n      <embedinfo type="1" />\n'
                f'      <datatype>0</datatype>\n      <unittype>0</unittype>\n      <DALINK index="0" />\n'
                + self.math(f) + '    </XDFAXIS>\n')

    def table(self, cat, title, a, rows, cols, yax, xax, f, unit, signed, dec, desc):
        self.add(f'  <XDFTABLE uniqueid="0x{self.next_uid():X}" flags="0x0">\n'
                 f'    <title>{escape(title)} [0x{a:05X}]</title>\n'
                 f'    <description>{escape(desc)}</description>\n'
                 f'    <CATEGORYMEM index="0" category="{cat + 1}" />\n')
        self.add(self.axis('x', cols, xax))
        self.add(self.axis('y', rows, yax))
        self.add(f'    <XDFAXIS id="z">\n'
                 f'      <EMBEDDEDDATA mmedtypeflags="{self.flags(signed)}" mmedaddress="0x{a:X}" mmedelementsizebits="16" '
                 f'mmedrowcount="{rows}" mmedcolcount="{cols}" mmedmajorstridebits="0" mmedminorstridebits="0" />\n'
                 f'      <units>{escape(unit)}</units>\n      <decimalpl>{dec}</decimalpl>\n      <outputtype>1</outputtype>\n'
                 + self.math(f) + '    </XDFAXIS>\n  </XDFTABLE>\n')

    def const(self, cat, title, a, f, unit, signed, dec, bits, desc):
        addr = a ^ 1 if bits == 8 else a
        self.add(f'  <XDFCONSTANT uniqueid="0x{self.next_uid():X}" flags="0x0">\n'
                 f'    <title>{escape(title)} [0x{a:05X}]</title>\n'
                 f'    <description>{escape(desc)}</description>\n'
                 f'    <CATEGORYMEM index="0" category="{cat + 1}" />\n'
                 f'    <EMBEDDEDDATA mmedtypeflags="{self.flags(signed)}" mmedaddress="0x{addr:X}" mmedelementsizebits="{bits}" mmedmajorstridebits="0" mmedminorstridebits="0" />\n'
                 f'    <units>{escape(unit)}</units>\n    <decimalpl>{dec}</decimalpl>\n    <datatype>0</datatype>\n    <unittype>0</unittype>\n'
                 f'    <DALINK index="0" />\n' + self.math(f) + '  </XDFCONSTANT>\n')


def main():
    x = Xdf()
    x.add('<?xml version="1.0" encoding="UTF-8"?>\n<XDFFORMAT version="1.70">\n  <XDFHEADER>\n    <flags>0x1</flags>\n'
          '    <deftitle>Audi A2 BBY - Marelli 4MV 036906034CA (E85, v10)</deftitle>\n'
          '    <description>Dump 512 Ko tel que lu (mots little-endian). CHECKSUM NON GÉRÉ PAR TUNERPRO : '
          'après modification, lancer "python3 marelli4mv.py fix entree.bin sortie.bin".</description>\n'
          '    <author>généré par generer_xdf.py</author>\n'
          '    <BASEOFFSET offset="0" subtract="0" />\n'
          '    <DEFAULTS datasizeinbits="16" sigdigits="2" outputtype="1" signed="0" lsbfirst="1" float="0" />\n'
          '    <REGION type="0xFFFFFFFF" startaddress="0x0" size="0x80000" regionflags="0x0" name="Binary File" desc="" />\n')
    for i, c in enumerate(CATS):
        x.add(f'    <CATEGORY index="0x{i:X}" name="{escape(c)}" />\n')
    x.add('  </XDFHEADER>\n')
    for t in TABLES:
        x.table(*t)
    for c in CONSTS:
        x.const(*c)
    x.add('</XDFFORMAT>\n')
    texte = ascii_seul(''.join(x.out))
    open(sys.argv[1], 'w', encoding='ascii', newline='\r\n').write(texte)
    print(f'{len(TABLES)} tables, {len(CONSTS)} constantes -> {sys.argv[1]}')


if __name__ == '__main__':
    main()
