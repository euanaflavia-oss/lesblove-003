#!/usr/bin/env bash
set -euo pipefail
pause() { echo; read -t 10 -rp "Fecha em 10s (Enter fecha já)... " _ || true; echo; }
trap pause EXIT   # a janela só fecha depois de você ler o resultado
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # pasta raiz (ex.: portal/003)
VARS="$DIR/setups_1234.yml"; KEYS="$DIR/configs_1234.yml"
yget() { { grep -E "^$2:" "$1" || true; } | head -1 | sed -E "s/^$2:[[:space:]]*//; s/\r$//; s/^\"//; s/\"$//"; }
need() { command -v "$1" >/dev/null || { echo "falta: $1"; exit 1; }; }
to_bytes() { local v="${1^^}" num; num="${v//[^0-9]/}"; case "$v" in *GB) echo $((num*1073741824));; *MB) echo $((num*1048576));; *KB) echo $((num*1024));; *) echo "$num";; esac; }

N=$(yget "$VARS" user_num)   # conta definida no setups_1234.yml (user_num)
[[ "$N" =~ ^[0-9]+$ ]] && [ -n "$(yget "$KEYS" "git_user_$N")" ] || { echo "user_num inválido no yml: $N"; exit 1; }
GIT_USER=$(yget "$KEYS" "git_user_$N");   GIT_TOKEN=$(yget "$KEYS" "git_token_$N")
CF_ACCOUNT=$(yget "$KEYS" "cflare_user_$N"); CF_TOKEN=$(yget "$KEYS" "cflare_token_$N")
EMAIL=$(yget "$KEYS" "email_$N")
HOST=$(yget "$VARS" git_host); HOST="${HOST:-github.com}"
NAME="$(yget "$VARS" front_theme)-$(yget "$VARS" page_counter)"; CHUNK=$(yget "$VARS" upload_chunks)

# cada conta tem o seu próprio git (histórico/commits separados), na mesma pasta de trabalho
GD="$DIR/.git_repo$N"
g() { git --git-dir="$GD" --work-tree="$DIR" "$@"; }
prep_git() {
  need git
  [ -f "$GD/HEAD" ] || git --git-dir="$GD" init -q -b main   # pasta pode existir vazia (placeholder)
  g config --local user.name "$GIT_USER"; g config --local user.email "$EMAIL"
  git config --global pack.compression 0; git config --global pack.window 0
  mkdir -p "$GD/info"
  printf '%s\n' '.git_repo*' > "$GD/info/exclude"   # só os repos (git não ignora sozinho pastas fora de .git)
  g remote remove origin 2>/dev/null || true
  g remote add origin "https://$GIT_USER:$GIT_TOKEN@$HOST/$GIT_USER/$NAME.git"
}
# pasta temporária só com o que está versionado no repo da conta (nunca publica yml/chaves)
stage_tracked() {
  STAGE=$(mktemp -d); trap 'rm -rf "$STAGE"; pause' EXIT
  ( cd "$DIR" && g ls-files -z | xargs -0 -I{} cp --parents "{}" "$STAGE" )
}

# Cria o repo <tema>-<contador> no GitHub da conta N.  Uso: ./git_create_repo.sh [conta]
need curl
code=$(curl -s -o /tmp/gh_resp.json -w '%{http_code}' -X POST https://api.github.com/user/repos \
  -H "Authorization: Bearer $GIT_TOKEN" -H "Accept: application/vnd.github+json" \
  -d "{\"name\":\"$NAME\",\"private\":${PRIVATE:-false}}")
case "$code" in
  201) echo "repo criado: $GIT_USER/$NAME";;
  422) echo "repo já existe: $GIT_USER/$NAME";;
  *)   echo "erro $code"; cat /tmp/gh_resp.json; exit 1;;
esac
