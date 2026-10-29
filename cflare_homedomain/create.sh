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

# Cria o projeto da home (<tema>.pages.dev) já conectado ao repo da página atual (<tema>-<page_counter>).  Uso: create.sh [conta]
need curl
N="${1:-$(yget "$VARS" user_num)}"
GIT_USER=$(yget "$KEYS" "git_user_$N")
CF_ACCOUNT=$(yget "$KEYS" "cflare_user_$N"); CF_TOKEN=$(yget "$KEYS" "cflare_token_$N")
REPO="$THEME-$CUR"
API="https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/pages/projects"
if cf "$API/$THEME" | ok; then echo "$THEME já existe na conta $N (use bind.sh)"; exit 0; fi
R=$(cf -X POST "$API" -H "Content-Type: application/json" --data "{
  \"name\": \"$THEME\", \"production_branch\": \"main\",
  \"source\": {\"type\": \"github\", \"config\": {
    \"owner\": \"$GIT_USER\", \"repo_name\": \"$REPO\", \"production_branch\": \"main\",
    \"deployments_enabled\": true, \"production_deployments_enabled\": true,
    \"pr_comments_enabled\": false, \"preview_deployment_setting\": \"none\" }}}")
echo "$R" | ok || { echo "erro:"; echo "$R"; exit 1; }
SUB=$(echo "$R" | grep -oE '"subdomain": *"[^"]*"' | head -1 | sed -E 's/.*: *"//; s/"$//' || true)
if [ -n "$SUB" ] && [ "$SUB" != "$THEME.pages.dev" ]; then echo "ATENÇÃO: o endereço ficou $SUB e NÃO $THEME.pages.dev (nome já usado em outra conta?)"; fi
echo "criado: $THEME (conta $N) -> github.com/$GIT_USER/$REPO"
