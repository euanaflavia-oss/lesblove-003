#!/usr/bin/env bash
set -euo pipefail
pause() { echo; read -t 10 -rp "Fecha em 10s (Enter fecha já)... " _ || true; echo; }
trap pause EXIT   # a janela só fecha depois de você ler o resultado
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VARS="$DIR/setups_1234.yml"; [ -f "$VARS" ] || VARS="$DIR/setup_vars_1234.yml"
KEYS="$DIR/configs_1234.yml"; [ -f "$KEYS" ] || KEYS="$DIR/setup_keys_1234.yml"
yget() { { grep -E "^$2:" "$1" || true; } | head -1 | sed -E "s/^$2:[[:space:]]*//; s/\r$//; s/^\"//; s/\"$//"; }

N=$(yget "$VARS" user_num)
GIT_USER=$(yget "$KEYS" "git_user_$N")
CF_ACCOUNT=$(yget "$KEYS" "cflare_user_$N"); CF_TOKEN=$(yget "$KEYS" "cflare_token_$N")
NAME="$(yget "$VARS" front_theme)-$(yget "$VARS" page_counter)"   # projeto na Cloudflare = repo no GitHub
API="https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/pages/projects"
cf() { curl -sS -H "Authorization: Bearer $CF_TOKEN" "$@"; }
ok() { grep -q '"success": *true'; }

# projeto já existe?
R=$(cf "$API/$NAME")
if echo "$R" | ok; then echo "$NAME já existe. Nada a fazer."; exit 0; fi

# cria o projeto já conectado ao repo (branch main)
R=$(cf -X POST "$API" -H "Content-Type: application/json" --data "{
  \"name\": \"$NAME\", \"production_branch\": \"main\",
  \"source\": {\"type\": \"github\", \"config\": {
    \"owner\": \"$GIT_USER\", \"repo_name\": \"$NAME\", \"production_branch\": \"main\",
    \"deployments_enabled\": true, \"production_deployments_enabled\": true,
    \"pr_comments_enabled\": false, \"preview_deployment_setting\": \"none\" }}}")
if echo "$R" | ok; then
  echo "ok: $NAME conectado a github.com/$GIT_USER/$NAME (o 1º deploy começa sozinho)"
  echo "url: https://$NAME.pages.dev"
else
  echo "erro:"; echo "$R"; exit 1
fi
