#!/usr/bin/env bash
set -euo pipefail
pause() { [ -n "${NOPAUSE:-}" ] && return; echo; read -t 10 -rp "Fecha em 10s (Enter fecha já)... " _ || true; echo; }
trap pause EXIT   # a janela só fecha depois de você ler o resultado
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # pasta raiz (onde ficam os yml)
VARS="$ROOT/setups_1234.yml"; KEYS="$ROOT/configs_1234.yml"
yget() { { grep -E "^$2:" "$1" || true; } | head -1 | sed -E "s/^$2:[[:space:]]*//; s/\r$//; s/^\"//; s/\"$//"; }
need() { command -v "$1" >/dev/null || { echo "falta: $1" >&2; exit 1; }; }

# Descobre onde mora a home <tema>.pages.dev, procurando em todas as contas do yml.
# Se o token não enxerga o id do yml (403), procura nas contas que o token realmente enxerga.
# Saída (stdout): "<conta> <id_da_conta_cloudflare> <repo>"   | mensagens vão pro stderr
need curl
BASE="https://api.cloudflare.com/client/v4"
THEME=$(yget "$VARS" front_theme)
HEX='[0-9a-f]{32}'
check() {   # check TOKEN ACCOUNT_ID  -> preenche CODE e R
  local OUT; OUT=$(curl -sS -w $'\n%{http_code}' -H "Authorization: Bearer $1" "$BASE/accounts/$2/pages/projects/$THEME" || true)
  CODE=${OUT##*$'\n'}; R=${OUT%$'\n'*}
}
ERR=0; WRONG=""
for N in $(grep -oE '^cflare_token_[0-9]+' "$KEYS" | grep -oE '[0-9]+$' | sort -un); do
  TOK=$(yget "$KEYS" "cflare_token_$N"); CAND=$(yget "$KEYS" "cflare_user_$N"); DISCOVERED=0
  while [ -n "$CAND" ]; do
    ACC=${CAND%% *}; CAND=${CAND#"$ACC"}; CAND=${CAND# }
    check "$TOK" "$ACC"
    if echo "$R" | grep -q '"success": *true'; then
      REPO=$(echo "$R" | grep -oE '"repo_name": *"[^"]*"' | head -1 | sed -E 's/.*: *"//; s/"$//' || true)
      SUB=$(echo "$R" | grep -oE '"subdomain": *"[^"]*"' | head -1 | sed -E 's/.*: *"//; s/"$//' || true)
      if [ -n "$SUB" ] && [ "$SUB" != "$THEME.pages.dev" ]; then
        echo "  conta $N: tem um projeto $THEME na conta Cloudflare $ACC, mas o endereço dele é $SUB (não é $THEME.pages.dev)" >&2
        WRONG="$N $ACC $SUB"
      else
        echo "  conta $N: ACHEI $THEME na conta Cloudflare $ACC (repo ${REPO:-$THEME})" >&2
        echo "$N $ACC ${REPO:-$THEME}"; exit 0
      fi
    elif [ "$CODE" = 404 ] || echo "$R" | grep -q '8000007'; then
      echo "  conta $N: não tem $THEME (conta Cloudflare $ACC)" >&2
    elif [ "$CODE" = 403 ] && [ "$DISCOVERED" = 0 ]; then
      DISCOVERED=1
      echo "  conta $N: o token não enxerga o id $ACC do yml (403); procurando as contas que ele enxerga..." >&2
      L=$(curl -sS -H "Authorization: Bearer $TOK" "$BASE/accounts" || true)
      for X in $(echo "$L" | grep -oE "\"id\": *\"$HEX\"" | grep -oE "$HEX" | sort -u || true); do
        [ "$X" = "$ACC" ] || CAND="$CAND $X"; CAND=${CAND# }
      done
      if [ -z "$CAND" ]; then echo "  conta $N: o token também não consegue listar contas. Confira cflare_user_$N (id da conta) e as permissões do token." >&2; ERR=1; fi
    else
      echo "  conta $N: ERRO http $CODE: $(echo "$R" | cut -c1-200)" >&2; ERR=1
    fi
  done
done
if [ -n "$WRONG" ]; then echo "o endereço $THEME.pages.dev está em uso numa conta que não consigo ver. Arrume o token/id da conta Cloudflare que está dando erro acima (cflare_user_N / cflare_token_N)." >&2; exit 3; fi
if [ "$ERR" = 1 ]; then echo "não deu pra verificar todas as contas (erro acima): abortando, não vou assumir que a home não existe" >&2; exit 2; fi
echo "home $THEME.pages.dev não existe em nenhuma conta" >&2
exit 1
