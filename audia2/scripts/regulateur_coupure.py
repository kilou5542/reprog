#!/usr/bin/env python3
"""Coupure d'injection en descente quand le régulateur de vitesse est actif (4MV CA).

Logiciel d'origine (module pédale 0x24B5A) : tant que le régulateur est engagé ($1188 = 2 ou 8),
la pédale est forcée « partielle » ($162C = 4) et à 1000 ($1616). La coupure en décélération
(0x3D08A) exige $162C = 1 et ressort dès que $1616 > 650 : elle est donc impossible au régulateur,
même quand celui-ci demande son couple minimal.

Patch :
  1. Butées négatives du correcteur PI élargies (BUTEES) : le régulateur peut enfin réduire
     le couple en descente au lieu de laisser la vitesse monter de plusieurs km/h.
  2. Le forçage de la pédale est levé quand la voiture dépasse la consigne ET que le régulateur
     demande peu de couple : la pédale suit le capteur réel (pied levé) et la coupure normale
     s'enclenche avec ses propres conditions (régime, température, temporisations).
     Hystérésis selon l'état du cycle précédent ($162B = 2 : pédale forcée), voir SEUILS.
Les quatre seuils sont des mots signés éditables dans WinOLS (adresse affichée à l'exécution).
Mettre ECART_COUPURE à 32767 désactive la partie coupure.

  python3 regulateur_coupure.py entree.bin sortie.bin
"""
import struct
import sys

import capstone

import marelli4mv as m

HOOK = 0x24B5A          # tst.b $E4555.l (6 octets) -> jmp NEW.l
NEW = 0x7F1C0           # zone libre (FF) 0x7F1B4-0x7FF6F, couverte par le checksum principal
FORCE = 0x24B90         # move.b #2,$162B(a5) ; #4,$162C ; $1616 = 1000
NORMAL = 0x24C08        # traitement pédale normal
# Seuils (mots signés) : écart vitesse - consigne en 1/16 km/h, couple régulateur $244 en 1/16 Nm
SEUILS = (32,    # ECART_COUPURE  : coupure si vitesse >= consigne + 2 km/h ...
          160,   # COUPLE_COUPURE : ... et demande du régulateur <= 10 Nm
          8,     # ECART_REPRISE  : coupure maintenue tant que vitesse >= consigne + 0,5 km/h ...
          480)   # COUPLE_REPRISE : ... et demande <= 30 Nm
# Butées du correcteur PI (0x4EE36) : origine P -160 / +480, I -1280 / +5120 (soit -10/+40 Nm).
# La butée négative trop courte empêche le régulateur de retenir la voiture en descente.
BUTEES = {0x5C778: -480,    # P mini (-30 Nm)
          0x5C77C: -8000}   # I mini (-62 Nm après >>3)


def assemble():
    c = bytearray()

    def w(*vals):
        for v in vals:
            c.extend(struct.pack('>H', v & 0xFFFF))

    def l(v):
        c.extend(struct.pack('>I', v))

    fix = {}      # position du déplacement -> (étiquette, taille)
    labels = {}
    fx = []

    def br(op, label, short=False):
        if short:
            fix[len(c) + 1] = (label, 1, len(c) + 2)
            w(op << 8)
        else:
            w(op << 8)
            fix[len(c)] = (label, 2, len(c))
            w(0)

    w(0x4A39); l(0x000E4555)                  # tst.b $E4555.l      (régulateur codé)
    br(0x67, 'normal')                        # beq.w normal
    w(0x162D, 0x1188)                         # move.b $1188(a5),d3
    w(0x0C03, 0x0002)                         # cmpi.b #2,d3
    br(0x67, 'chk', True)                     # beq.s chk
    w(0x0C03, 0x0008)                         # cmpi.b #8,d3
    br(0x66, 'normal')                        # bne.w normal
    w(0x0C2D, 0x0001, 0x0E98)                 # cmpi.b #1,$E98(a5)
    br(0x67, 'chk', True)                     # beq.s chk
    w(0x322D, 0x1618)                         # move.w $1618(a5),d1
    w(0xB279); l(0x00059260)                  # cmp.w $59260.l,d1
    br(0x62, 'normal')                        # bhi.w normal
    labels['chk'] = len(c)
    # écart de vitesse en 1/16 km/h : $20DA (km/h x16) - consigne $118C (km/h) x16
    w(0x322D, 0x20DA)                         # move.w $20DA(a5),d1
    w(0x302D, 0x118C)                         # move.w $118C(a5),d0
    w(0xE948)                                 # lsl.w #4,d0
    w(0x9240)                                 # sub.w d0,d1
    w(0x302D, 0x0244)                         # move.w $244(a5),d0   (couple régulateur)
    w(0x0C2D, 0x0002, 0x162B)                 # cmpi.b #2,$162B(a5)  (forcée au cycle précédent ?)
    br(0x66, 'rel', True)                     # bne.s rel
    w(0xB279); fx.append((len(c), 0)); l(0)   # cmp.w ECART_COUPURE.l,d1
    br(0x6D, 'force', True)                   # blt.s force
    w(0xB079); fx.append((len(c), 2)); l(0)   # cmp.w COUPLE_COUPURE.l,d0
    br(0x6E, 'force', True)                   # bgt.s force
    br(0x60, 'normal', True)                  # bra.s normal
    labels['rel'] = len(c)
    w(0xB279); fx.append((len(c), 4)); l(0)   # cmp.w ECART_REPRISE.l,d1
    br(0x6D, 'force', True)                   # blt.s force
    w(0xB079); fx.append((len(c), 6)); l(0)   # cmp.w COUPLE_REPRISE.l,d0
    br(0x6E, 'force', True)                   # bgt.s force
    labels['normal'] = len(c)
    w(0x4EF9); l(NORMAL)                      # jmp NORMAL.l
    labels['force'] = len(c)
    w(0x4EF9); l(FORCE)                       # jmp FORCE.l
    seuils = len(c)
    w(*SEUILS)

    for pos, (lab, size, base) in fix.items():
        disp = labels[lab] - base
        if size == 1:
            assert -128 <= disp <= 127 and disp != 0
            c[pos] = disp & 0xFF
        else:
            c[pos:pos + 2] = struct.pack('>h', disp)
    for pos, off in fx:
        c[pos:pos + 4] = struct.pack('>I', NEW + seuils + off)
    return bytes(c), NEW + seuils


def main():
    src, dst = sys.argv[1:3]
    d = m.load(src)
    if d[HOOK:HOOK + 6] != bytes.fromhex('4a39000e4555'):
        sys.exit(f"0x{HOOK:X} ne contient pas le code d'origine : {d[HOOK:HOOK + 6].hex()}")
    code, seuils = assemble()
    if d[NEW:NEW + len(code)] != b'\xff' * len(code):
        sys.exit(f"zone 0x{NEW:X} non libre")
    d[NEW:NEW + len(code)] = code
    d[HOOK:HOOK + 6] = struct.pack('>HI', 0x4EF9, NEW)
    for a, v in BUTEES.items():
        d[a:a + 2] = struct.pack('>h', v)
    m.fix(d)
    assert m.check(d) == (True, True)
    m.save(dst, d)

    md = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_BIG_ENDIAN | capstone.CS_MODE_M68K_040)
    for i in md.disasm(bytes(d[HOOK:HOOK + 6]), HOOK):
        print(f'{i.address:06x}: {i.mnemonic:10} {i.op_str}')
    print('...')
    for i in md.disasm(bytes(d[NEW:seuils]), NEW):
        print(f'{i.address:06x}: {i.mnemonic:10} {i.op_str}')
    print(f'seuils @0x{seuils:05X} : {struct.unpack(">4h", d[seuils:seuils + 8])}')
    print('butées PI :', {hex(a): struct.unpack('>h', d[a:a + 2])[0] for a in BUTEES})
    print(f'-> {dst} (checksum OK)')


if __name__ == '__main__':
    main()
