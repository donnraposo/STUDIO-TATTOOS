#!/usr/bin/env bash
#
# Restauracao de uma copia, **em banco temporario**.
#
# O risco declarado da M8 e "restauracao nunca testada". Uma copia que ninguem
# restaurou e uma hipotese, nao uma garantia -- e o dia de descobrir que o dump
# estava truncado nao pode ser o dia em que o servidor se foi.
#
# Por isso este script **nao toca no banco em producao**. Ele cria um banco
# temporario ao lado, restaura ali, conta as linhas das tabelas que importam e
# derruba o banco no fim. E o teste trimestral que a secao 4 de
# 03_REQUISITOS_NAO_FUNCIONAIS.md exige, e tambem o ensaio de uma restauracao
# de verdade: os mesmos passos, com outro nome de banco.
#
# Para restaurar **de verdade**, o runbook descreve o procedimento -- que passa
# por parar a API antes, e por isso nao e automatico aqui.
#
# Uso:
#   restore.sh                      # a copia mais recente
#   restore.sh <nome-do-arquivo>    # uma copia especifica

set -euo pipefail

readonly WORKDIR="$(mktemp -d)"
readonly TEMP_DB="restore_test_$(date +%Y%m%d_%H%M%S)"

cleanup() {
  rm -rf "${WORKDIR}"
  # O banco temporario sai mesmo quando o script aborta: deixa-lo para tras
  # encheria o disco do servidor a cada teste trimestral.
  PGPASSWORD="${POSTGRES_PASSWORD}" dropdb \
    --host "${POSTGRES_HOST}" --username "${POSTGRES_USER}" \
    --if-exists "${TEMP_DB}" 2>/dev/null || true
}
trap cleanup EXIT

say() { echo "[restore] $*"; }
fail() { echo "[restore] FALHOU: $*" >&2; exit 1; }

require() {
  local name="$1"
  [ -n "${!name:-}" ] || fail "variavel ${name} nao definida."
}

require POSTGRES_HOST
require POSTGRES_DB
require POSTGRES_USER
require POSTGRES_PASSWORD
require BACKUP_S3_BUCKET
require AWS_ACCESS_KEY_ID
require AWS_SECRET_ACCESS_KEY

# A chave **privada** nao vive no servidor: ela e trazida para o teste e vai
# embora depois. Se estivesse aqui, quem invadisse o VPS leria todas as copias.
[ -f "${BACKUP_AGE_KEY_FILE:-/run/secrets/age-key}" ] \
  || fail "chave privada do age ausente. Monte-a so para a restauracao; ver o runbook."
readonly KEY_FILE="${BACKUP_AGE_KEY_FILE:-/run/secrets/age-key}"

aws_s3() {
  if [ -n "${BACKUP_S3_ENDPOINT:-}" ]; then
    aws --endpoint-url "${BACKUP_S3_ENDPOINT}" s3 "$@"
  else
    aws s3 "$@"
  fi
}

# --- Qual copia ------------------------------------------------------------
if [ $# -ge 1 ]; then
  readonly NAME="$1"
else
  say "procurando a copia mais recente"
  NAME="$(aws_s3 ls "s3://${BACKUP_S3_BUCKET}/" | awk '{print $4}' | grep '^tattoo-studio-' | sort | tail -1)"
  readonly NAME
  [ -n "${NAME}" ] || fail "nenhuma copia encontrada no balde."
fi
say "usando ${NAME}"

aws_s3 cp "s3://${BACKUP_S3_BUCKET}/${NAME}" "${WORKDIR}/${NAME}" \
  || fail "nao consegui baixar a copia"

say "decifrando"
age --decrypt --identity "${KEY_FILE}" --output "${WORKDIR}/pacote.tar" "${WORKDIR}/${NAME}" \
  || fail "age nao decifrou. Chave privada errada?"

tar --extract --file "${WORKDIR}/pacote.tar" --directory "${WORKDIR}" \
  || fail "pacote corrompido"

[ -f "${WORKDIR}/database.dump" ] || fail "o pacote nao tem database.dump"
[ -f "${WORKDIR}/objects.tar" ] || fail "o pacote nao tem objects.tar"

# --- Alvo 1: o banco, num banco temporario ---------------------------------
say "criando o banco temporario ${TEMP_DB}"
PGPASSWORD="${POSTGRES_PASSWORD}" createdb \
  --host "${POSTGRES_HOST}" --username "${POSTGRES_USER}" "${TEMP_DB}" \
  || fail "nao consegui criar ${TEMP_DB}"

say "restaurando"
PGPASSWORD="${POSTGRES_PASSWORD}" pg_restore \
  --host "${POSTGRES_HOST}" --username "${POSTGRES_USER}" \
  --dbname "${TEMP_DB}" --no-owner --no-privileges \
  "${WORKDIR}/database.dump" \
  || fail "pg_restore nao concluiu"

# --- A conferencia ---------------------------------------------------------
#
# Restaurar sem conferir prova que o arquivo abriu, nao que o dado esta la. As
# tabelas escolhidas sao as que doem: conta, atendimento, pagamento e repasse.
say "conferindo o que voltou"
PGPASSWORD="${POSTGRES_PASSWORD}" psql \
  --host "${POSTGRES_HOST}" --username "${POSTGRES_USER}" --dbname "${TEMP_DB}" \
  --tuples-only --command "
    SELECT 'user_account   ' || count(*) FROM user_account
    UNION ALL SELECT 'client         ' || count(*) FROM client
    UNION ALL SELECT 'booking        ' || count(*) FROM booking
    UNION ALL SELECT 'quote          ' || count(*) FROM quote
    UNION ALL SELECT 'tattoo_session ' || count(*) FROM tattoo_session
    UNION ALL SELECT 'payment        ' || count(*) FROM payment
    UNION ALL SELECT 'payout         ' || count(*) FROM payout
    UNION ALL SELECT 'audit_log      ' || count(*) FROM audit_log;
  " || fail "o banco restaurou mas nao respondeu a consulta"

# --- Alvo 2: os arquivos ---------------------------------------------------
#
# O teste cobre os dois alvos, e nao so o banco: enquanto o armazenamento for o
# volume local, um banco restaurado sem os arquivos aponta para imagens que nao
# existem.
readonly OBJECTS_OUT="${WORKDIR}/objects"
mkdir -p "${OBJECTS_OUT}"
tar --extract --file "${WORKDIR}/objects.tar" --directory "${OBJECTS_OUT}" \
  || fail "nao consegui extrair os arquivos enviados"
say "arquivos no pacote: $(find "${OBJECTS_OUT}" -type f | wc -l)"

say "OK. Banco temporario ${TEMP_DB} sera removido agora."
