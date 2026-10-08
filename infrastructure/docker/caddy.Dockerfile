# Caddy com o frontend ja compilado dentro.
#
# **Nao ha container de frontend em producao** (secao 8 de
# 04_ARQUITETURA_TECNICA.md). O Vue vira arquivos estaticos e quem os entrega e
# o Caddy, que ja esta ali para o TLS e para o proxy da API. Um servidor so,
# um dominio so -- e e o mesmo dominio que dispensa CORS e mantem o cookie de
# sessao simples (secao 3).
#
# O build do Vue acontece aqui, e nao numa etapa separada da esteira, para que
# subir o compose seja suficiente: quem clonar o repositorio num servidor novo
# nao precisa lembrar de compilar nada antes.

FROM node:22-alpine AS build

WORKDIR /app

# package.json antes do resto: a camada de dependencias so e refeita quando ele
# muda, e nao a cada alteracao de componente.
COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

FROM caddy:2-alpine AS production

# A pasta que o Caddyfile serve. O conteudo e imutavel: uma versao nova do
# frontend e uma imagem nova, nao um arquivo trocado em disco.
COPY --from=build /app/dist /srv/studio

COPY infrastructure/caddy/Caddyfile /etc/caddy/Caddyfile
