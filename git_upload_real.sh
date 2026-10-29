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

# Commit + push em lotes (upload_chunks) usando o .git_repoN da conta.
prep_git
LIMIT=$(to_bytes "$CHUNK")
echo "conta $N | $GIT_USER/$NAME | lote máx $CHUNK | git: $(basename "$GD")"
echo "listando arquivos (pode demorar em pasta grande)..."
TMP=$(mktemp -d)
push_it() {
  g push --progress --set-upstream origin HEAD:main HEAD:master --force 2>&1 | tee "$TMP/push.log"; local rc=${PIPESTATUS[0]}
  if [ "$rc" -ne 0 ]; then
    echo; echo "===== PUSH FALHOU ====="
    grep -E "path:|commit:|—— |rejected|denied|fatal" "$TMP/push.log" | sort -u
  fi
  return "$rc"
}
( cd "$DIR" && g ls-files --others --modified --exclude-standard -z | { xargs -0 stat -c '%s %n' 2>/dev/null || true; } ) > "$TMP/list"
# divide em lotes: $TMP/b1.lst, b2.lst ... (um arquivo por linha)
awk -v limit="$LIMIT" -v dir="$TMP" '
  BEGIN { b=1 }
  { s=$1+0; name=substr($0,index($0," ")+1)
    if (size+s>limit && n>0) { close(dir "/b" b ".lst"); b++; size=0; n=0 }
    print name > (dir "/b" b ".lst"); size+=s; n++ }' "$TMP/list"
TOTAL=$(find "$TMP" -name 'b*.lst' | wc -l)
if [ "$TOTAL" -eq 0 ]; then
  echo "nada novo para commitar; enviando commits pendentes..."
  cd "$DIR"; push_it
  rm -rf "$TMP"; echo "ok: $HOST/$GIT_USER/$NAME"; exit 0
fi
cd "$DIR"
for ((i=1; i<=TOTAL; i++)); do
  echo "lote $i/$TOTAL: $(wc -l < "$TMP/b$i.lst") arquivos..."
  tr '\n' '\0' < "$TMP/b$i.lst" | g add --pathspec-from-file=- --pathspec-file-nul
  g commit -m "." || true; push_it
  echo "lote $i/$TOTAL enviado"
done
rm -rf "$TMP"
echo "ok: $HOST/$GIT_USER/$NAME"
