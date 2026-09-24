# Estrutura do Projeto

**Status:** Proposta para aprovação — nenhuma pasta ou arquivo de aplicação foi criado.
**Última atualização:** 24/09/2026

> Define a árvore de diretórios, a responsabilidade de cada pasta, as convenções de
> código e os contratos de API. Não autoriza implementação.

## 1. Árvore geral

```text
tattoo-studio/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── modules/
│   │   ├── shared/
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── infrastructure/
│   ├── docker/
│   └── environments/
├── DOCS/
├── scripts/
├── compose.yaml
├── compose.production.yaml
└── README.md
```

| Pasta | Responsabilidade |
|---|---|
| `backend/app/core` | Configuração, segurança, sessão, dependências, erros e base do banco |
| `backend/app/modules` | Módulos de negócio, independentes entre si |
| `backend/app/shared` | Primitivos técnicos realmente compartilhados, sem regra de negócio |
| `backend/migrations` | Migrações Alembic, artefatos gerados |
| `backend/tests` | Testes espelhando a estrutura dos módulos |
| `frontend/src` | Interface Vue por funcionalidade |
| `infrastructure/docker` | Imagens, entrypoints e configuração de containers |
| `infrastructure/environments` | Exemplos de variáveis por ambiente, sem segredos |
| `DOCS` | Documentação oficial e decisões |
| `scripts` | Automações explícitas de desenvolvimento e operação |

## 2. Backend — monólito modular

### 2.1 Módulos

Os nove módulos de negócio já previstos em `04_ARQUITETURA_TECNICA.md` §4:

```text
backend/app/modules/
├── identity/      contas, cadastro, aprovação, sessões, permissões
├── clients/       cadastro, vínculos, duplicidades, visibilidade
├── scheduling/    macas, disponibilidade, solicitações, conflitos, bloqueios
├── quotes/        orçamentos, sessões, execução e conclusão
├── finance/       pagamentos, sinais, devoluções, repasses, fechamento
├── guests/        semanas pagas, acesso, atendimentos indicados
├── aftercare/     vencimentos, contatos, resultados, fotos
├── notifications/ caixa interna, outbox de e-mail, worker
└── reporting/     relatórios autorizados, exportações e auditoria
```

### 2.2 Camadas internas de cada módulo

```text
modules/scheduling/
├── domain/
│   ├── entities/
│   ├── value_objects/
│   ├── enums/
│   └── repositories/      contratos (interfaces)
├── application/
│   ├── use_cases/
│   └── dto/
├── infrastructure/
│   ├── models/            SQLAlchemy
│   └── repositories/      implementações
└── api/
    ├── routes.py
    ├── schemas/           Pydantic
    └── dependencies/
```

Dependências apontam sempre para o domínio. O domínio não conhece FastAPI,
SQLAlchemy nem HTTP.

### 2.3 Convenções obrigatórias

- **Uma classe própria do projeto por arquivo.** Nunca mais de uma.
- Nome do arquivo corresponde à responsabilidade da classe.
- Sem regra de negócio em rotas, schemas Pydantic ou tarefas do worker.
- Módulos não importam detalhes internos uns dos outros; a comunicação passa por
  casos de uso e contratos.
- O caso de uso delimita a transação.
- `__init__.py` não esconde dependências com reexportação extensa.
- Migrações são artefatos gerados pelo Alembic e seguem a convenção da ferramenta.

## 3. Frontend — organização por funcionalidade

```text
frontend/src/
├── app/            inicialização, rotas, guardas de perfil
├── features/
│   ├── auth/
│   ├── dashboard/
│   ├── scheduling/
│   ├── clients/
│   ├── quotes/
│   ├── finance/
│   ├── guests/
│   ├── aftercare/
│   └── reporting/
├── shared/
│   ├── components/
│   ├── composables/
│   ├── tokens.css      variáveis de design centralizadas
│   └── api/            cliente HTTP tipado
└── pwa/                manifesto e service worker
```

**Regras:**
- Um componente por arquivo.
- Todo valor visual vem de variável CSS; nenhum valor mágico no estilo.
- Interface em inglês (`01_REGRAS_DE_NEGOCIO.md` §1.1); documentação em português.
- Componentes de tela compõem; não declaram estilo próprio.

### 3.1 Componente de agenda

Decisão registrada em `08_DECISOES_ARQUITETURA.md` (ADR-004): a visão timeline
macas × horário será construída com CSS Grid próprio, sem licença paga.

```text
features/scheduling/components/
├── BoothTimeline.vue        grade: macas no eixo Y, horas no eixo X
├── BookingBlock.vue         bloco posicionado por início e duração
├── ConflictModal.vue        modal de RN-AGE-007, sem opção de ignorar
└── AvailabilityFilter.vue
```

O posicionamento usa `grid-column` calculado a partir do intervalo, evitando
cálculo manual de pixels.

## 4. Contratos de API

Prefixo `/api/v1`, mesmo domínio do frontend.

| Recurso | Endpoints principais |
|---|---|
| Autenticação | `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`, `POST /auth/password-reset` |
| Usuários | `GET/POST /users`, `POST /users/{id}/approve`, `/reject`, `/block`, `/unblock` |
| Cadastro público | `POST /registrations` (autocadastro de artista) |
| Clientes | `GET/POST /clients`, `PATCH /clients/{id}`, `POST /clients/{id}/merge` |
| Macas | `GET/POST /booths`, `POST /schedule-exceptions` |
| Agenda | `GET /bookings`, `POST /bookings`, `POST /bookings/{id}/approve`, `/reject`, `/reschedule`, `/cancel` |
| Orçamentos | `GET/POST /quotes`, `POST /quotes/{id}/approve`, `/reject` |
| Sessões | `POST /sessions/{id}/mark-done`, `POST /sessions/{id}/confirm-payment` |
| Pagamentos | `GET/POST /payments`, `POST /payments/{id}/confirm`, `/refuse`, `/refund` |
| Repasses | `GET /payouts`, `POST /payouts/{id}/mark-paid` |
| Guests | `GET/POST /guest-weeks`, `POST /guest-weeks/{id}/activate` |
| Pós-venda | `GET /aftercare`, `POST /aftercare/{id}/complete`, `/reopen`, `/photos` |
| Relatórios | `GET /reports/{name}`, `GET /reports/{name}/export` |
| Auditoria | `GET /audit-logs` |
| Notificações | `GET /notifications`, `POST /notifications/{id}/read` |
| Saúde | `GET /health`, `GET /ready` |

**Convenções:**
- Autenticação por cookie de sessão; token CSRF obrigatório em operações que alteram dados.
- Listas paginadas por `page` e `page_size`.
- Erros padronizados com código, mensagem e campo quando aplicável.
- Conflito de agenda devolve `409` com os dados do agendamento existente, alimentando o modal.
- Operações financeiras críticas aceitam chave de idempotência.
- Respostas e mensagens visíveis em inglês.

## 5. Containers

```text
compose.yaml
├── proxy        Caddy — TLS automático, serve o frontend, encaminha /api/v1
├── api          FastAPI
├── worker       agendador e outbox
├── postgres     banco com volume persistente
└── mailhog      captura de e-mail apenas em desenvolvimento
```

Em produção, `mailhog` sai e o e-mail vai para o serviço transacional.

O `worker` é um container separado da `api`. Ele executa a lista diária das 08h
`Europe/Dublin`, o fechamento de sexta às 20h e o consumo do outbox. Separar evita
que reinício da API interrompa envios e que o agendador rode duplicado quando
houver mais de um processo de API.

## 6. Ambientes

| Ambiente | Uso |
|---|---|
| Desenvolvimento | Docker Compose local, banco efêmero, MailHog, armazenamento local compatível com S3 |
| Teste | Executado em container, PostgreSQL real — nunca SQLite, pelas restrições `EXCLUDE` e `tstzrange` |
| Produção | VPS único com Docker Compose, Caddy com TLS, volume persistente e backup cifrado fora do servidor |

Segredos vêm de variáveis de ambiente, nunca das imagens ou do repositório.

## 7. Pendências deste documento

- Nomes finais de arquivos serão confirmados ao iniciar cada sprint.
- Contratos detalhados de request e response por endpoint, na implementação.
- Escolha final do provedor de e-mail transacional entre os candidatos avaliados.
