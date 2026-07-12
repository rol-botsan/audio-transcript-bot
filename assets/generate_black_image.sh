#!/usr/bin/env bash
# À exécuter une fois sur le VPS (ffmpeg installé) pour générer l'image noire
# statique utilisée par convert.py.
set -euo pipefail
ffmpeg -y -f lavfi -i color=c=black:s=1280x720 -frames:v 1 "$(dirname "$0")/black.png"
