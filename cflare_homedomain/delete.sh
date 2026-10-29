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

# Apaga o projeto da home (<tema>.pages.dev) numa conta.  Uso: delete.sh [conta [id_da_conta_cloudflare]]   (sem args: usa o que o find.sh achar)
need curl
N="${1:-}"; ACC="${2:-}"
if [ -z "$N" ]; then read -r N ACC _ <<<"$(NOPAUSE=1 bash "$ROOT/cflare_homedomain/find.sh")"; fi
CF_ACCOUNT="${ACC:-$(yget "$KEYS" "cflare_user_$N")}"; CF_TOKEN=$(yget "$KEYS" "cflare_token_$N")
API="https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT/pages/projects"
R=$(cf "$API/$THEME")
if ! echo "$R" | ok; then echo "$THEME não existe na conta $N: nada a apagar"; exit 0; fi
SUB=$(echo "$R" | grep -oE '"subdomain": *"[^"]*"' | head -1 | sed -E 's/.*: *"//; s/"$//' || true)
if [ "$SUB" != "$THEME.pages.dev" ]; then echo "NÃO apaguei: o projeto $THEME da conta $N tem endereço $SUB (esperado $THEME.pages.dev)"; exit 1; fi
D=$(cf -X DELETE "$API/$THEME")
if ! echo "$D" | ok; then
  # a Cloudflare não deixa apagar projeto com muitos deploys (>100): apaga os deploys primeiro
  echo "não deu pra apagar de primeira; apagando os deploys antes (pode demorar)..."
  IDS=$(mktemp); trap 'rm -f "$IDS"; pause' EXIT
  UUID='[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
  for ((P=1; P<=1000; P++)); do                       # 1) lista tudo (sem apagar enquanto lista)
    L=$(cf "$API/$THEME/deployments?per_page=25&page=$P")
    PG=$(echo "$L" | grep -oE "\"id\": *\"$UUID\"" | grep -oE "$UUID" | sort -u || true)
    NEW=$(echo "$PG" | grep -vxFf "$IDS" || true)
    [ -n "$NEW" ] || break
    echo "$NEW" >> "$IDS"
  done
  TOTAL=$(wc -l < "$IDS" | tr -d ' '); i=0
  echo "$TOTAL deploys encontrados"
  while read -r id; do                                 # 2) apaga um a um (force = inclusive os com alias)
    i=$((i+1)); cf -X DELETE "$API/$THEME/deployments/$id?force=true" >/dev/null </dev/null || true
    if [ $((i % 10)) -eq 0 ]; then echo "  $i/$TOTAL"; fi
  done < "$IDS"
  D=$(cf -X DELETE "$API/$THEME")                      # 3) tenta apagar o projeto de novo
  echo "$D" | ok || { echo "não consegui apagar $THEME (conta $N):"; echo "$D"; exit 1; }
fi
echo "apagado: $THEME (conta $N)"
