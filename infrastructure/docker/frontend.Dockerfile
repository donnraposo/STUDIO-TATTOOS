FROM node:22-alpine AS base

WORKDIR /app

FROM base AS development

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./

EXPOSE 5173
CMD ["npm", "run", "dev"]

# **Nao ha estagio de producao aqui, e e de proposito.**
#
# A secao 8 de 04_ARQUITETURA_TECNICA.md decidiu que em producao o Vue vira
# arquivos estaticos servidos pelo Caddy, que ja esta no ar pelo TLS e pelo
# proxy da API -- um dominio so, sem CORS e com o cookie de sessao simples.
#
# Ate 07/10/2026 este arquivo tinha um estagio `production` com nginx, que
# ninguem usava e que contradizia aquela decisao. Era um convite ao erro que o
# proprio roadmap da M8 adverte: subir um segundo servidor web em producao
# porque havia um estagio chamado `production` esperando por isso.
#
# O build do frontend em producao mora em `caddy.Dockerfile`, junto de quem o
# serve.
