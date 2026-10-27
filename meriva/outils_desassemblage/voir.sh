#!/bin/sh
# Affiche le listing autour d'une adresse : voir.sh listing.asm ADRESSE [AVANT] [APRES]
# ex. : ./voir.sh full.asm 00f4e0 0 120
n=$(grep -n "^$2 " "$1" | cut -d: -f1)
[ -z "$n" ] && { echo "adresse $2 introuvable (instruction mal alignée ?)"; exit 1; }
sed -n "$((n-${3:-20})),$((n+${4:-40}))p" "$1"
