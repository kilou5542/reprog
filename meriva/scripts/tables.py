"""Définition des tables identifiées dans la ROM Delphi Z16XE (12230554 / EZ, 256 Ko).

Toutes les adresses sont des offsets dans le fichier .ori (le processeur voit la flash à 0x40000).
Les tables existent souvent en deux jeux, choisis par l'option de configuration $9808 :
jeu 0 si $9808 = 0, jeu 1 sinon. Le jeu utilisé par la voiture n'est pas encore connu.

Chaque adresse a été trouvée en suivant le code jusqu'à la lecture de la table (voir MEMOIRE.md).
"""

# --- Axes ------------------------------------------------------------------------------------
# Températures : échelle GM, °C = 0,75 x octet - 40 (confirmé par la réponse OBD PID 05/0F).
EAU17 = [-40 + 12 * i for i in range(17)]          # index $95b6 / $95a2*16 : -40..152 °C
EAU13 = [-28 + 12 * i for i in range(13)]          # index $95ae : -28..116 °C
EAU13F = [-40 + 12 * i for i in range(13)]         # index $95b4 : -40..104 °C
AIR13 = [-28 + 12 * i for i in range(13)]          # index $9702 (air admis) : -28..116 °C
RPM400_17 = [400 * i for i in range(17)]           # $9692 : 0..6400
RPM400_16 = [400 + 400 * i for i in range(16)]     # $969e : 400..6400
RPM200_17 = [200 * i for i in range(17)]           # $9698 : 0..3200
RPM400_9 = [400 * i for i in range(9)]             # $969a : 0..3200
RPM800_9 = [800 * i for i in range(9)]             # $9694 : 0..6400
RPM800_8 = [800 + 800 * i for i in range(8)]       # $96a2 : 800..6400
MAP9 = [20 + 10 * i for i in range(9)]             # $9782/$9788 : 20..100 kPa
MAP11 = [20, 30, 40, 50, 60, 70, 80, 85, 90, 95, 100]  # $9778 : axe dilaté au-dessus de 80 kPa
DEPR9 = [10 * i for i in range(9)]                 # $976e = baro - MAP : 0..80 kPa de dépression
BARO4 = [75, 85, 95, 105]                          # $851e : pression atmosphérique, kPa
PAP9 = [50 + 6.25 * i for i in range(9)]           # $97d0 : papillon commandé 50..100 %
AFR7 = [10 + i for i in range(7)]                  # AFR cible 10..16


def afr(x):
    return x / 10


def deg(x):
    """Avance : (octet - 64) x 0,3516 ° (90/256, confirmé par la réponse OBD PID 0E)."""
    return (x - 64) * 90 / 256


def deg_brut(x):
    return x * 90 / 256


def pct(x):
    return x / 2.55


def temp(x):
    return x * 0.75 - 40


def brut(x):
    return x


# --- Tables ----------------------------------------------------------------------------------
# cle: (titre, [adresse jeu 0, adresse jeu 1 ou None], lignes, colonnes, 'B' octet / 'W' mot BE,
#       conversion, axe lignes, axe colonnes, unité)
TABLES = {
    # Démarrage
    'afr_demarrage': ('AFR de lancement (démarreur)', [0x0E32, 0x0E3F], 1, 13, 'B', afr, None, EAU13, 'AFR'),
    'enrich_demarrage': ('Enrichissement initial du lancement (retiré de l\'AFR)', [0x0F70, 0x0F71], 1, 1, 'B', afr, None, None, 'AFR'),
    'enrich_dem_facteur': ('Décroissance de l\'enrichissement de lancement (facteur /256)', [0x0E30, 0x0E31], 1, 1, 'B', brut, None, None, '/256'),
    'enrich_dem_periode': ('Période de décroissance de l\'enrichissement de lancement', [0x0F72, 0x0F73], 1, 1, 'B', brut, None, None, 'boucles'),
    'impulsion_amorcage': ('Impulsion d\'amorçage (tir simultané 4 injecteurs)', [0x07D2, 0x07F4], 1, 17, 'W', brut, None, EAU17, 'ticks TPU'),
    'apres_demarrage': ('Enrichissement après démarrage (retiré de l\'AFR)', [0x0BE4, 0x0BF1], 1, 13, 'B', afr, None, EAU13, 'AFR'),
    'apres_demarrage_tf': ('Enrichissement après démarrage, mode très froid', [0x0BFE, 0x0C0B], 1, 13, 'B', afr, None, EAU13, 'AFR'),
    'apres_dem_periode': ('Période de décroissance après démarrage', [0x0C18, 0x0C25], 1, 13, 'B', brut, None, EAU13, 'boucles'),
    'apres_dem_periode_tf': ('Période de décroissance après démarrage, très froid', [0x0F54, 0x0F61], 1, 13, 'B', brut, None, EAU13, 'boucles'),
    'apres_dem_facteur': ('Facteur de décroissance après démarrage (/256)', [0x0E8E, 0x0E8F], 1, 1, 'B', brut, None, None, '/256'),
    'seuil_tres_froid': ('Seuil eau du mode « démarrage très froid »', [0x0668, 0x0669], 1, 1, 'B', temp, None, None, '°C'),
    'noyage_afr': ('AFR forcé « noyage » (pédale enfoncée pendant le lancement)', [0x0F6E, None], 1, 1, 'B', afr, None, None, 'AFR'),
    'noyage_seuil': ('Seuil pédale du mode noyage', [0x0F6F, None], 1, 1, 'B', pct, None, None, '%'),
    'avance_demarrage': ('Avance pendant le lancement', [0x1376, 0x1383], 1, 13, 'B', deg, None, EAU13, '°'),

    # Carburant
    'constante_injecteur': ('Constante injecteur (temps par unité de carburant)', [0x07BE, None], 1, 9, 'W', brut, None, DEPR9, 'brut'),
    'stoechio': ('AFR cible moteur chaud (stœchiométrie)', [0x0688, None], 1, 1, 'B', afr, None, None, 'AFR'),
    'seuil_chaud': ('Seuil eau de passage à l\'AFR stœchio', [0x0E6A, 0x0E6B], 1, 1, 'B', temp, None, None, '°C'),
    'seuil_chaud_tf': ('Seuil eau de passage à l\'AFR stœchio, mode très froid', [0x0E68, 0x0E69], 1, 1, 'B', temp, None, None, '°C'),
    'afr_froid': ('AFR boucle ouverte moteur froid', [0x0CA8, 0x0C32], 13, 9, 'B', afr, EAU13F, MAP9, 'AFR'),
    'afr_froid_tf': ('AFR boucle ouverte moteur froid, après démarrage très froid', [0x0D94, 0x0D1E], 13, 9, 'B', afr, EAU13F, MAP9, 'AFR'),
    'afr_correction_regime': ('Correction de l\'AFR froid selon le régime (valeur - 20)', [0x0E6C, 0x0E7D], 1, 17, 'B', lambda x: (x - 20) / 10, None, RPM400_17, 'AFR'),
    'afr_pleine_charge': ('AFR pleine charge (power enrichment)', [0x0EA8, None], 17, 9, 'B', afr, RPM400_17, PAP9, 'AFR'),
    'pleine_charge_mult_eau': ('Multiplicateur pleine charge selon l\'eau (/256)', [0x0E96, None], 1, 17, 'B', brut, None, EAU17, '/256'),
    'pleine_charge_seuil': ('Seuil papillon commandé d\'entrée en pleine charge', [0x0F42, 0x0F4B], 1, 9, 'B', pct, None, RPM800_9, '%'),
    'pleine_charge_hyst': ('Hystérésis du seuil pleine charge', [0x0E94, None], 1, 1, 'B', brut, None, None, 'brut'),
    'afr_protection': ('AFR maxi de protection (température d\'échappement modélisée)', [0x0E0A, 0x0E1B], 1, 17, 'B', afr, None, list(range(17)), 'AFR'),
    'modele_temp_echappement': ('Modèle de température d\'échappement (régime x débit d\'air)', [0x4A76, 0x49D0], 15, 11, 'B', brut, [800 + 400 * i for i in range(15)], [8 * i for i in range(11)], 'brut'),

    # Allumage
    'avance_principale': ('Avance principale', [0x16A8, 0x15F8], 16, 11, 'B', deg, RPM400_16, MAP11, '°'),
    'avance_ralenti': ('Avance ralenti', [0x142A, 0x1390], 17, 9, 'B', deg, RPM200_17, MAP9, '°'),
    'avance_ralenti_b': ('Avance ralenti, variante', [0x155E, 0x14C4], 17, 9, 'B', deg, RPM200_17, MAP9, '°'),
    'avance_ralenti_c': ('Avance ralenti, 3e variante', [0x17AA, 0x1758], 9, 9, 'B', deg, RPM400_9, MAP9, '°'),
    'avance_corr_eau': ('Correction d\'avance selon l\'eau', [0x19DC, 0x1966], 13, 9, 'B', deg, EAU13, MAP9, '°'),
    'avance_corr_air': ('Correction d\'avance selon l\'air admis', [0x18A4, 0x182E], 13, 9, 'B', deg, AIR13, MAP9, '°'),
    'avance_corr_baro': ('Correction d\'avance selon la pression atmosphérique', [0x1942, 0x191E], 4, 9, 'B', deg, BARO4, DEPR9, '°'),
    'avance_corr_afr': ('Correction d\'avance selon l\'AFR cible', [0x1A7E, None], 8, 7, 'B', deg, RPM800_8, AFR7, '°'),
    'retrait_securite': ('Retrait d\'avance si capteur de cliquetis en défaut', [0x17FC, 0x1807], 1, 11, 'B', deg_brut, None, MAP11, '°'),
    'avance_mini': ('Butée d\'avance mini', [0x1361, None], 1, 1, 'B', deg, None, None, '°'),
    'avance_maxi': ('Butée d\'avance maxi', [0x1362, None], 1, 1, 'B', deg, None, None, '°'),
}


def lire(rom, cle, jeu=0):
    titre, adrs, l, c, t, conv, ay, ax, unite = TABLES[cle]
    a = adrs[jeu]
    if a is None:
        return None
    n = l * c
    if t == 'B':
        brutes = list(rom[a:a + n])
    else:
        brutes = [int.from_bytes(rom[a + 2 * i:a + 2 * i + 2], 'big') for i in range(n)]
    return [[conv(v) for v in brutes[r * c:(r + 1) * c]] for r in range(l)]
