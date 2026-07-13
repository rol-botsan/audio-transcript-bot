#!/usr/bin/env bash
# Lance le bot en local (pas en service systemd) : à exécuter depuis n'importe où sur le VPS.
set -euo pipefail
cd "$(dirname "$0")"
source .venv/bin/activate
python bot.py
