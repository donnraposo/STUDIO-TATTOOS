# Tattoo Studio — Sistema Interno

Sistema de gestão interna para um estúdio de tatuagem em Cork City, Irlanda.
Administra usuários, clientes, agenda de macas, orçamentos, sessões, pagamentos,
repasses e pós-venda.

## Documentação

A documentação em `DOCS/` é a fonte de verdade. **Leia-a antes do código.**

| Documento | Conteúdo |
|---|---|
| [`00_CONTEXTO_E_CONTINUIDADE.md`](DOCS/00_CONTEXTO_E_CONTINUIDADE.md) | Resumo e ponto de retomada |
| [`01_REGRAS_DE_NEGOCIO.md`](DOCS/01_REGRAS_DE_NEGOCIO.md) | Regras aprovadas |
| [`02_ROADMAP_PRE_IMPLEMENTACAO.md`](DOCS/02_ROADMAP_PRE_IMPLEMENTACAO.md) | Fases de descoberta |
| [`03_REQUISITOS_NAO_FUNCIONAIS.md`](DOCS/03_REQUISITOS_NAO_FUNCIONAIS.md) | Desempenho, segurança, backup |
| [`04_ARQUITETURA_TECNICA.md`](DOCS/04_ARQUITETURA_TECNICA.md) | Visão da solução |
| [`05_MODELO_DADOS.md`](DOCS/05_MODELO_DADOS.md) | Entidades e restrições |
| [`06_ESTRUTURA_PROJETO.md`](DOCS/06_ESTRUTURA_PROJETO.md) | Pastas, módulos e API |
| [`07_PLANO_TESTES.md`](DOCS/07_PLANO_TESTES.md) | Cenários e critérios de aceite |
| [`08_DECISOES_ARQUITETURA.md`](DOCS/08_DECISOES_ARQUITETURA.md) | ADRs |
| [`09_ROADMAP_IMPLEMENTACAO.md`](DOCS/09_ROADMAP_IMPLEMENTACAO.md) | Sprints |

## Stack

FastAPI · PostgreSQL · SQLAlchemy 2 · Alembic · Vue 3 · TypeScript · Vite · Docker

## Como executar

Tudo roda em containers. **Nunca execute no host.**

```bash
cp .env.example .env
docker compose up -d
```

| Serviço | Endereço |
|---|---|
| Interface | http://localhost:5173 |
| API | http://localhost:8000/api/v1 |
| Documentação da API | http://localhost:8000/api/v1/docs |

### Migrações

```bash
docker compose exec api alembic upgrade head
```

### Verificações

```bash
docker compose exec api ruff check .
docker compose exec api pytest
docker compose exec frontend npm run lint
docker compose exec frontend npm run typecheck
docker compose exec frontend npm test
```

## Convenções

- Uma classe própria do projeto por arquivo, sem exceção.
- Clean Code e SOLID; regra de negócio fora de rotas, schemas e tarefas.
- Todo valor visual vem de variável em `frontend/src/shared/tokens.css`.
- Interface e mensagens da API em inglês; documentação em português.
- PostgreSQL real nos testes; SQLite não substitui.
- Documentação atualizada na mesma entrega da mudança.
