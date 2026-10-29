#!/usr/bin/env bash
set -euo pipefail
pause() { echo; read -t 10 -rp "Fecha em 10s (Enter fecha já)... " _ || true; echo; }
trap pause EXIT   # a janela só fecha depois de você ler o resultado
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VARS="$DIR/setups_1234.yml"; [ -f "$VARS" ] || VARS="$DIR/setup_vars_1234.yml"
KEYS="$DIR/configs_1234.yml"; [ -f "$KEYS" ] || KEYS="$DIR/setup_keys_1234.yml"
yget() { { grep -E "^$2:" "$1" || true; } | head -1 | sed -E "s/^$2:[[:space:]]*//; s/\r$//; s/^\"//; s/\"$//"; }

N=$(yget "$VARS" user_num)
CF_ACCOUNT=$(yget "$KEYS" "cflare_user_$N"); CF_TOKEN=$(yget "$KEYS" "cflare_token_$N")
NAME="$(yget "$VARS" front_theme)-$(yget "$VARS" page_counter)"

# Manda a Cloudflare refazer o deploy a partir do Git (branch main). Não envia nada do seu PC.
R=$(curl -sS -X POST "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/pages/projects/$NAME/deployments" \
  -H "Authorization: Bearer $CF_TOKEN" -F branch=main)
if echo "$R" | grep -q '"success": *true'; then
  echo "deploy disparado a partir do Git: https://$NAME.pages.dev"
else
  echo "erro:"; echo "$R"; exit 1
fi
