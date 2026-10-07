#!/usr/bin/env bash
#
# Relogio da copia diaria.
#
# **Laco de espera e nao `cron`**, de proposito. O `cron` dentro de container
# roda os trabalhos com um ambiente proprio, quase vazio -- as variaveis que o
# compose injeta nao chegam nele sem um arquivo intermediario. E a armadilha
# classica: a copia para de funcionar no primeiro dia e ninguem percebe, porque
# o container continua de pe e o `cron` nao reclama de uma variavel ausente.
#
# Um trabalho por dia nao justifica aquele risco. Este laco calcula quanto falta
# para a proxima hora marcada, dorme, roda e repete -- com o ambiente que o
# compose entregou, e falando no log do container a cada passo.

set -euo pipefail

readonly HOUR="${BACKUP_HOUR:-03}"
readonly SCRIPT="$(dirname "$0")/backup.sh"

echo "[agenda] copia diaria as ${HOUR}:00, fuso $(date +%Z)"

# Confere o ambiente **na subida**, e nao so na primeira execucao. Um container
# que sobe sem credencial e descobre as 3 da manha deixou a noite inteira sem
# copia; aqui ele reclama agora, enquanto alguem esta olhando.
for required in POSTGRES_HOST POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD \
                BACKUP_AGE_RECIPIENT BACKUP_S3_BUCKET \
                AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY; do
  if [ -z "${!required:-}" ]; then
    echo "[agenda] FALHOU: ${required} nao definida. Ver .env.production.example." >&2
    exit 1
  fi
done

while true; do
  now="$(date +%s)"
  target="$(date -d "today ${HOUR}:00:00" +%s)"
  if [ "${target}" -le "${now}" ]; then
    # `date -d tomorrow` resolve a mudanca de horario de verao sozinho; somar
    # 86400 segundos erraria por uma hora duas vezes por ano.
    target="$(date -d "tomorrow ${HOUR}:00:00" +%s)"
  fi

  wait_for=$(( target - now ))
  echo "[agenda] proxima copia em $(( wait_for / 3600 ))h $(( (wait_for % 3600) / 60 ))min"
  sleep "${wait_for}"

  # A copia pode falhar sem derrubar o relogio: um erro de rede as 3h nao pode
  # cancelar a copia de amanha. O erro fica no log, e o `backup.sh` ja grita.
  if bash "${SCRIPT}"; then
    echo "[agenda] copia do dia concluida"
  else
    echo "[agenda] a copia de hoje FALHOU; tentando de novo amanha" >&2
  fi
done
