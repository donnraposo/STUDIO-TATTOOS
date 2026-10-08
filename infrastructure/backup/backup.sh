#!/usr/bin/env bash
#
# Copia de seguranca diaria: banco + arquivos enviados, cifrados e enviados
# para fora do servidor.
#
# **Dois alvos, e nao um.** Enquanto o armazenamento for o volume local do VPS
# (decisao de 07/10/2026), uma copia que leve so o `pg_dump` deixaria para tras
# as imagens de referencia dos orcamentos, os comprovantes e as fotos de
# cicatrizacao. A perda apareceria justamente no dia em que o servidor se
# fosse -- e o banco restaurado apontaria para arquivos que nao existem mais.
#
# **Cifrada com chave publica.** O servidor guarda apenas a chave publica do
# `age`: ele consegue escrever uma copia e **nao consegue le-la**. Quem invadir
# o VPS leva o banco em producao, que ja e ruim, mas nao leva o historico
# inteiro de copias junto. A chave privada vive fora do servidor, e sem ela nao
# ha restauracao -- esta e a troca, e o runbook diz onde guarda-la.
#
# **Falha ruidosa e proposital.** Copia que falha em silencio e pior do que
# copia nenhuma: cria a confianca sem o lastro. Qualquer erro aborta o script
# com codigo diferente de zero e mensagem no log do container.

set -euo pipefail

readonly MOMENT="$(date +%Y-%m-%dT%H-%M-%S)"
readonly WORKDIR="$(mktemp -d)"
readonly ARCHIVE="${WORKDIR}/tattoo-studio-${MOMENT}.tar"
readonly ENCRYPTED="${ARCHIVE}.age"

cleanup() {
  # O diretorio temporario guarda o dump em claro. Sai sempre, inclusive
  # quando o script aborta no meio.
  rm -rf "${WORKDIR}"
}
trap cleanup EXIT

say() {
  echo "[backup ${MOMENT}] $*"
}

fail() {
  echo "[backup ${MOMENT}] FALHOU: $*" >&2
  exit 1
}

require() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    fail "variavel ${name} nao definida. Ver .env.production.example."
  fi
}

require POSTGRES_HOST
require POSTGRES_DB
require POSTGRES_USER
require POSTGRES_PASSWORD
require BACKUP_AGE_RECIPIENT
require BACKUP_S3_BUCKET
require AWS_ACCESS_KEY_ID
require AWS_SECRET_ACCESS_KEY

readonly OBJECTS_ROOT="${STORAGE_ROOT:-/var/lib/tattoo-studio/objects}"
readonly S3_ENDPOINT="${BACKUP_S3_ENDPOINT:-}"
readonly RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

aws_s3() {
  if [ -n "${S3_ENDPOINT}" ]; then
    aws --endpoint-url "${S3_ENDPOINT}" s3 "$@"
  else
    aws s3 "$@"
  fi
}

say "iniciando"

# --- Alvo 1: o banco -------------------------------------------------------
#
# Formato `custom` e nao SQL puro: permite restaurar tabela a tabela e e
# comprimido. O `pg_dump` vem da imagem do PostgreSQL 17, a mesma versao do
# servidor -- um dump feito por cliente mais antigo que o servidor e recusado
# na hora de restaurar, e so se descobre no pior dia.
say "exportando o banco"
PGPASSWORD="${POSTGRES_PASSWORD}" pg_dump \
  --host "${POSTGRES_HOST}" \
  --port "${POSTGRES_PORT:-5432}" \
  --username "${POSTGRES_USER}" \
  --dbname "${POSTGRES_DB}" \
  --format custom \
  --file "${WORKDIR}/database.dump" \
  || fail "pg_dump nao concluiu"

# --- Alvo 2: os arquivos enviados ------------------------------------------
say "empacotando os arquivos enviados"
if [ -d "${OBJECTS_ROOT}" ]; then
  tar --create --file "${WORKDIR}/objects.tar" --directory "${OBJECTS_ROOT}" . \
    || fail "nao consegui empacotar ${OBJECTS_ROOT}"
else
  # Nao e erro: um estudio que ainda nao enviou arquivo nenhum tem o diretorio
  # vazio. Mas fica registrado, porque o diretorio sumir depois de existir e
  # outra coisa.
  say "AVISO: ${OBJECTS_ROOT} nao existe; a copia vai so com o banco"
  tar --create --file "${WORKDIR}/objects.tar" --files-from /dev/null
fi

tar --create --file "${ARCHIVE}" --directory "${WORKDIR}" database.dump objects.tar \
  || fail "nao consegui montar o pacote"

# --- Cifra -----------------------------------------------------------------
say "cifrando"
age --encrypt --recipient "${BACKUP_AGE_RECIPIENT}" --output "${ENCRYPTED}" "${ARCHIVE}" \
  || fail "age nao cifrou o pacote"

# O pacote em claro sai agora, e nao so no `trap`: entre cifrar e enviar ha uma
# rede pelo meio, e nao ha razao para o arquivo legivel esperar ali.
rm -f "${ARCHIVE}"

readonly SIZE="$(du -h "${ENCRYPTED}" | cut -f1)"
say "pacote cifrado com ${SIZE}"

# --- Sai do servidor -------------------------------------------------------
#
# O requisito e que a copia **nao** fique so no VPS: um servidor perdido leva
# junto a copia guardada nele, e ai nao havia copia.
say "enviando para ${BACKUP_S3_BUCKET}"
aws_s3 cp "${ENCRYPTED}" "s3://${BACKUP_S3_BUCKET}/$(basename "${ENCRYPTED}")" \
  || fail "envio para o S3 nao concluiu"

# --- Retencao --------------------------------------------------------------
#
# 30 dias, conforme a secao 4 de 03_REQUISITOS_NAO_FUNCIONAIS.md. A poda vem
# **depois** do envio: podar antes deixaria uma janela em que a copia nova
# falhou e as antigas ja tinham ido.
say "removendo copias com mais de ${RETENTION_DAYS} dias"
readonly LIMIT="$(date -d "${RETENTION_DAYS} days ago" +%Y-%m-%d)"
aws_s3 ls "s3://${BACKUP_S3_BUCKET}/" | while read -r _ _ _ name; do
  case "${name}" in
    tattoo-studio-*)
      stamp="${name#tattoo-studio-}"
      stamp="${stamp%%T*}"
      if [[ "${stamp}" < "${LIMIT}" ]]; then
        say "removendo ${name}"
        aws_s3 rm "s3://${BACKUP_S3_BUCKET}/${name}"
      fi
      ;;
  esac
done

say "concluida"
