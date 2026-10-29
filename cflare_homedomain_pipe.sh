#!/usr/bin/env bash
set -euo pipefail
pause() { echo; read -t 10 -rp "Fecha em 10s (Enter fecha já)... " _ || true; echo; }
trap pause EXIT   # a janela só fecha depois de você ler o resultado
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # pasta raiz (ex.: portal/004)
S="$DIR/cflare_homedomain"; export NOPAUSE=1
VARS="$DIR/setups_1234.yml"; KEYS="$DIR/configs_1234.yml"
yget() { { grep -E "^$2:" "$1" || true; } | head -1 | sed -E "s/^$2:[[:space:]]*//; s/\r$//; s/^\"//; s/\"$//"; }

# Home (<tema>.pages.dev) -> repo da página atual (<tema>-<page_counter>), sempre via Git.
#  não existe em conta nenhuma   : create -> deploy
#  existe em OUTRA conta (CF)    : delete (conta antiga) -> create (conta atual) -> deploy
#  existe na MESMA conta (CF)    : bind -> deploy
T=$(yget "$VARS" user_num)                                  # conta atual
set +e; F=$(bash "$S/find.sh"); RC=$?; set -e
if [ "$RC" = 0 ]; then
  read -r O OACC _ <<<"$F"                                  # conta (e id Cloudflare) onde a home está hoje
  if [ "$OACC" = "$(yget "$KEYS" "cflare_user_$T")" ]; then
    bash "$S/bind.sh" "$T"; bash "$S/deploy.sh" "$T"
  else
    bash "$S/delete.sh" "$O" "$OACC"; bash "$S/delete.sh" "$T"; bash "$S/create.sh" "$T"; bash "$S/deploy.sh" "$T" || echo "(o 1º deploy da criação já começa sozinho)"
  fi
elif [ "$RC" = 1 ]; then
  bash "$S/create.sh" "$T"; bash "$S/deploy.sh" "$T" || echo "(o 1º deploy da criação já começa sozinho)"
else
  exit 1
fi
