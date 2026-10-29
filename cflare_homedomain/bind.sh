#!/usr/bin/env bash
set -euo pipefail
pause() { [ -n "${NOPAUSE:-}" ] && return; echo; read -t 10 -rp "Fecha em 10s (Enter fecha já)... " _ || true; echo; }
trap pause EXIT   # a janela só fecha depois de você ler o resultado
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # pasta raiz (onde ficam os yml)
VARS="$ROOT/setups_1234.yml"; KEYS="$ROOT/configs_1234.yml"
yget() { { grep -E "^$2:" "$1" || true; } | head -1 | sed -E "s/^$2:[[:space:]]*//; s/\r$//; s/^\"//; s/\"$//"; }
need() { command -v "$1" >/dev/null || { echo "falta: $1" >&2; exit 1; }; }
cf() { curl -sS -H "Authorization: Bearer $CF_TOKEN" "$@"; }
ok() { grep -q '"success": *true'; }
THEME=$(yget "$VARS" front_theme); CUR=$(yget "$VARS" page_counter)   # home = <tema> ; atual = <tema>-<page_counter>

# Religa a home (projeto já existente) ao repo da página atual (<tema>-<page_counter>), na mesma conta.  Uso: bind.sh [conta]
need curl
N="${1:-$(yget "$VARS" user_num)}"
GIT_USER=$(yget "$KEYS" "git_user_$N")
CF_ACCOUNT=$(yget "$KEYS" "cflare_user_$N"); CF_TOKEN=$(yget "$KEYS" "cflare_token_$N")
REPO="$THEME-$CUR"
API="https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/pages/projects"
R=$(cf -X PATCH "$API/$THEME" -H "Content-Type: application/json" --data "{
  \"production_branch\": \"main\",
  \"source\": {\"type\": \"github\", \"config\": {
    \"owner\": \"$GIT_USER\", \"repo_name\": \"$REPO\", \"production_branch\": \"main\",
    \"deployments_enabled\": true, \"production_deployments_enabled\": true,
    \"pr_comments_enabled\": false, \"preview_deployment_setting\": \"none\" }}}")
echo "$R" | ok || { echo "erro:"; echo "$R"; exit 1; }
echo "ligado: $THEME (conta $N) -> github.com/$GIT_USER/$REPO"
