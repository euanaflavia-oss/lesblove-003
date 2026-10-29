#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
get() { { grep -E "^$1:" "$2" || true; } | head -1 | sed -E 's/^[^:]+:[[:space:]]*//; s/\r$//; s/"//g'; }

N=$(get user_num setups_1234.yml)
GIT_USER=$(get git_user_$N configs_1234.yml)
GIT_TOKEN=$(get git_token_$N configs_1234.yml)
EMAIL=$(get email_$N configs_1234.yml)
NAME="$(get front_theme setups_1234.yml)-$(get page_counter setups_1234.yml)"
HOST=$(get git_host setups_1234.yml); HOST=${HOST:-github.com}

# cria 1MB numa pasta temporária (não usa o seu repo) e sobe só no branch teste-upload
T=$(mktemp -d); head -c 1000000 /dev/urandom > "$T/teste_1mb.bin"; cd "$T"
git init -q -b teste-upload
git config user.name "$GIT_USER"; git config user.email "$EMAIL"
git add . && git commit -qm "teste 1MB"
git push --force "https://$GIT_USER:$GIT_TOKEN@$HOST/$GIT_USER/$NAME.git" teste-upload
echo "ok: 1MB enviado no branch teste-upload"
read -t 10 -rp "Fecha em 10s... " _ || true
