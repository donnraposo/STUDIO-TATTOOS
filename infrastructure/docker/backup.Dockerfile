# Container da copia de seguranca.
#
# **Base na imagem do PostgreSQL 17**, a mesma versao do servidor. O `pg_dump`
# de um cliente mais antigo que o servidor e recusado na restauracao -- e isso
# so se descobre no dia em que a restauracao importa. Herdando a imagem, as
# duas versoes andam juntas para sempre.
#
# Duas ferramentas a mais: o `age` cifra com chave publica, e o cliente da AWS
# envia para qualquer provedor compativel com S3 pelo `--endpoint-url`.

FROM postgres:17 AS production

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        age \
        awscli \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY infrastructure/backup/ /opt/backup/
RUN chmod +x /opt/backup/*.sh

# O relogio e o processo principal: o container existe para esperar a hora.
CMD ["/opt/backup/schedule.sh"]
