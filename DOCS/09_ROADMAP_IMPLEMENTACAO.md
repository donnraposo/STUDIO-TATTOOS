# Roadmap de Implementação

**Status:** Implementação autorizada. Estratégia de MVP definida em 24/09/2026.
**Última atualização:** 24/09/2026

> Sequência de sprints para construir o sistema, organizada em **MVP** e **Fase 2**.
> Cada sprint declara objetivo, arquivos, dependências, riscos e resultado esperado.

## Estratégia

O sistema existe para resolver duas dores concretas: **impedir choque de horário nas
macas** e **saber quem recebe quanto**. O MVP entrega o ciclo irredutível que permite
ao estúdio parar de usar planilha:

```text
login → cliente → agendar maca → sinal €50 → sessão feita e paga → repasse de sexta
```

Se qualquer elo faltar, o estúdio mantém controle paralelo e o sistema não substitui
nada. Por isso o corte não foi por módulo, e sim por esse fio condutor.

**Objetivo do MVP: uso real no estúdio.** Isso define o nível de acabamento —
prevenção de conflito à prova de concorrência, cálculo financeiro correto e
implantação com backup testado. Não é demonstração.

### Decisões de escopo

| Tema | Decisão | Razão |
|---|---|---|
| Guests e taxa semanal | Fase 2 | Encurta o MVP em uma sprint; o guest segue controlado fora do sistema, como hoje |
| Orçamentos | **Completo no MVP** | Decisão do responsável: fluxo integral com descrição, região, tamanho, referências e aprovação |
| Pós-venda | Fase 2 | Já é feito fora do sistema hoje |
| Relatórios e exportação | Fase 2 | O gestor consulta as telas; exportação vem depois |
| PWA instalável | Fase 2 | O site responsivo já atende no celular |
| Autocadastro e recuperação de senha | Fase 2 | O gestor cria as contas diretamente |

Nada foi descartado. Tudo que saiu do MVP está preservado na Fase 2.

## Regras de execução

- Uma unidade exportada por arquivo, sem exceção (ADR-015).
- Clean Code e SOLID; regra de negócio fora de rotas, schemas e tarefas do worker.
- Execução e testes sempre em containers Docker, nunca no host.
- PostgreSQL real nos testes; SQLite não substitui, por causa de `CITEXT`,
  `tstzrange` e `EXCLUDE`.
- Documentação atualizada na mesma entrega da mudança.
- Não avançar de sprint com teste crítico, migração ou verificação falhando.

## Situação

### MVP

**Estratégia de execução: backend completo primeiro, interface depois** (ADR-020).

| Sprint | Tema | Camada | Situação |
|---|---|---|---|
| 01 | Fundação técnica | Ambas | ✅ Concluída em 24/09/2026 |
| **M1** | Identidade e acesso | Backend | 🔄 Em andamento — etapa 1 de 3 |
| M2 | Clientes | Backend | Não iniciada |
| M3 | ⚠️ Agenda e macas | Backend | Não iniciada |
| M4 | Orçamentos e sessões | Backend | Não iniciada |
| M5 | Pagamentos e sinal | Backend | Não iniciada |
| M6 | Repasses e fechamento semanal | Backend | Não iniciada |
| M7 | Interface completa do MVP | Frontend | Não iniciada |
| M8 | Implantação mínima | Infra | Não iniciada |

**Ponto de validação sem interface.** Enquanto o frontend não existe, o contrato
publicado em `/api/v1/docs` é o meio de exercitar cada módulo e conferir as regras
de negócio. Ao fim de cada sprint de backend, o responsável consegue executar o
fluxo por ali.

### Fase 2

| Sprint | Tema |
|---|---|
| F1 | Guests e taxa semanal |
| F2 | Pós-venda, notificações e worker |
| F3 | Painéis, relatórios e exportação |
| F4 | PWA instalável |
| F5 | Autocadastro e recuperação de senha |

---

# MVP

## Sprint 01 — Fundação técnica

**Objetivo:** aplicações FastAPI e Vue iniciando de forma reproduzível em
containers, com configuração por ambiente, PostgreSQL com as extensões exigidas
pelo modelo de dados, verificação de saúde e ferramentas de qualidade.

**Arquivos:** `compose.yaml`, `infrastructure/docker`, `backend/app/core`,
`backend/migrations`, `frontend/src/app`, `.env.example`.

**Dependências:** nenhuma.

**Riscos:** divergência entre desenvolvimento e produção; exposição de segredos;
ausência das extensões `btree_gist` e `citext`, que bloqueariam a M3.

### Evidência de conclusão — 24/09/2026

Commit `e2d3cb2`.

- Três serviços no ar: `postgres` (healthy), `api` e `frontend`.
- Migração `0001` aplicada; `btree_gist` e `citext` confirmadas em `pg_extension`.
- Backend: Ruff sem apontamentos, 3 testes aprovados.
- Frontend: ESLint sem apontamentos, `vue-tsc` sem erro, 3 testes aprovados.
- `GET /api/v1/health` → 200; `GET /api/v1/ready` → 200 com banco alcançável.
- Interface confirmando o caminho navegador → proxy → API → PostgreSQL.

**Refatoração aplicada antes do fechamento:** fábricas soltas substituídas pela
raiz de composição `Container` (ADR-015 e ADR-016).

**Identidade visual definida:** Urbanist com escala 32/24/20/18/16/14 e paleta ouro
sobre preto extraída do monograma, em `frontend/src/shared/tokens.css`.

## Sprint M1 — Identidade e acesso

**Objetivo:** contas criadas pelo gestor, login, sessões revogáveis e trilha de
auditoria imutável. Autocadastro e recuperação de senha ficam para a F5.

**Arquivos:** `modules/identity`, `modules/reporting`, migrações,
`features/auth` no frontend.

**Dependências:** Sprint 01.

**Riscos:** escalada de privilégio; sessão permanecer válida após bloqueio de conta.

**Resultado esperado:** proprietário, gerente e residente autenticam com acesso
isolado; bloqueio e troca de senha revogam sessões imediatamente; ações
administrativas são auditadas.

### Etapas

| Etapa | Escopo | Situação |
|---|---|---|
| M1.1 | Modelo de dados, migração e auditoria imutável | ✅ Concluída em 24/09/2026 |
| M1.2 | Hash de senha, login, sessão, expiração e CSRF | Em andamento |
| M1.3 | Gestão de contas pelo gestor e matriz de permissões | Não iniciada |

A tela de login e os guardas de rota migraram para a sprint M7, junto com o
restante da interface.

### Evidência da etapa M1.1 — 24/09/2026

Commit `549d273`.

- Tabelas: `user_account`, `user_session`, `user_status_history`,
  `password_reset_token` e `audit_log`.
- Migração `0002` aplicada e revertida com sucesso nos dois sentidos.
- Ruff sem apontamentos; 6 testes aprovados.
- Suíte passa a usar banco isolado `tattoo_studio_test`, provisionado e migrado
  pelo `DatabaseProvisioner`.

**Imutabilidade da auditoria comprovada.** `UPDATE` e `DELETE` em `audit_log`
falham mesmo conectado como dono do banco:

```text
ERROR:  audit_log e append-only: UPDATE nao e permitido (ADR-012)
```

### Decisões revistas durante a etapa M1.1

| Tema | O que mudou |
|---|---|
| Auditoria imutável | `REVOKE` sozinho seria contornável pela role dona da tabela. Substituído por gatilho (ADR-012 revisado). |
| Estados | Texto com `CHECK` em vez de `ENUM` nativo, para evitar `ALTER TYPE` a cada novo estado (ADR-018). |

### Defeito corrigido durante a etapa M1.1

`migrations/env.py` sobrescrevia a URL do banco incondicionalmente, fazendo a suíte
de testes migrar o banco de desenvolvimento. Só apareceu ao isolar o banco de teste.

## Sprint M2 — Clientes

**Objetivo:** cadastro com nome e telefone obrigatórios, Instagram opcional, alerta
de duplicidade, visibilidade por perfil e união de cadastros.

**Arquivos:** `modules/clients`, `features/clients`.

**Dependências:** M1.

**Riscos:** exposição de ficha completa ao artista indicado, que deve ver apenas
nome, telefone e Instagram (RN-CLI-004).

**Resultado esperado:** RN-CLI-001 a RN-CLI-006 cobertas, com teste negativo de
visibilidade. A retenção de RN-CLI-007 fica na F3.

## Sprint M3 — Agenda e macas

> **Sprint de maior risco técnico do MVP.**

**Objetivo:** macas, horário-base, exceções, solicitações, aprovação, rejeição,
remarcação, bloqueios e as duas restrições de não sobreposição.

**Arquivos:** `modules/scheduling`, migração com as restrições `EXCLUDE`,
`features/scheduling` com a timeline em CSS Grid.

**Dependências:** M1 e M2.

**Riscos:** dupla reserva por requisições simultâneas; a timeline própria é o maior
esforço de frontend do projeto.

**Resultado esperado:** conflito impossível no banco, comprovado por teste com
transações paralelas reais; modal de conflito sem opção de ignorar.

## Sprint M4 — Orçamentos e sessões

**Objetivo:** orçamento completo com descrição, região do corpo, tamanho, imagens de
referência, sessões previstas e aprovação pelo gestor. Percentual congelado na
aprovação. Execução, sessão parcial e conclusão.

**Arquivos:** `modules/quotes`, `features/quotes`.

**Dependências:** M3.

**Riscos:** alteração retroativa de percentual; divergência entre valor aprovado e
valor executado.

**Resultado esperado:** ciclo completo entre orçamento, agendamento, sessão e
conclusão.

## Sprint M5 — Pagamentos e sinal

**Objetivo:** sinal de €50, confirmação manual pelo gestor, estados do pagamento,
devoluções e as regras de cancelamento, remarcação e não comparecimento.

**Arquivos:** `modules/finance/payments`, `features/finance`.

**Dependências:** M4.

**Riscos:** arredondamento; lançamento apagado em vez de ajustado.

**Resultado esperado:** nenhum pagamento é apagado; correção sempre por ajuste
vinculado com histórico.

## Sprint M6 — Repasses e fechamento semanal

**Objetivo:** cálculo por sessão, fechamento de sexta às 20h `Europe/Dublin`,
demonstrativo do artista e ajustes negativos de devolução posterior.

**Arquivos:** `modules/finance/payouts`.

**Dependências:** M5.

**Riscos:** fechamento duplicado; erro na fronteira do horário de verão.

**Resultado esperado:** fechamento reproduzível e auditável, conferido com os
exemplos de `01_REGRAS_DE_NEGOCIO.md`.

## Sprint M7 — Interface completa do MVP

**Objetivo:** construir todas as telas do MVP sobre a API já pronta e testada —
login, clientes, agenda com a timeline de macas, orçamentos, pagamentos e repasses.

**Arquivos:** `frontend/src/features/*`, componentes compartilhados em
`frontend/src/shared/components`.

**Dependências:** M1 a M6.

**Riscos:** concentrar todo o esforço de interface em uma sprint torna a estimativa
menos confiável; mal-entendidos de regra aparecem tarde, já com o backend pronto. A
validação pelo `/api/v1/docs` ao fim de cada sprint de backend existe para reduzir
esse risco.

**Resultado esperado:** os três perfis operam o ciclo completo pela interface, em
desktop e celular, sobre os tokens e componentes já definidos.

## Sprint M8 — Implantação mínima

**Objetivo:** colocar o MVP em uso real com segurança proporcional ao dado que ele
passa a guardar.

**Arquivos:** `compose.production.yaml`, configuração do proxy, runbooks.

**Dependências:** M6.

**Riscos:** restauração nunca testada; segredo exposto; banco acessível
publicamente.

**Resultado esperado:** sistema no ar em VPS com TLS, backup cifrado diário enviado
para fora do servidor, restauração testada em banco temporário e homologação com
proprietário e gerente.

> Sem esta sprint o MVP não recebe dado real do estúdio. Ela é o que separa
> "funciona na minha máquina" de "o estúdio depende disto".

---

# Fase 2

Preservada integralmente. Cada item mantém o detalhamento das regras já aprovadas
em `01_REGRAS_DE_NEGOCIO.md`.

## Sprint F1 — Guests e taxa semanal

Semanas pagas de sábado a sexta, ativação pelo gerente, acesso derivado das semanas,
reserva restrita à semana paga e regra 50/50 das indicações do estúdio.

## Sprint F2 — Pós-venda, notificações e worker

Pós-venda com vencimento em 15 dias, área com pendentes e atrasados, fotos de
cicatrização, outbox de e-mail e lista diária das 08h.

## Sprint F3 — Painéis, relatórios e exportação

Painéis por perfil, indicadores definidos em `01_REGRAS_DE_NEGOCIO.md` seção 10.4,
comparação de períodos, exportação em PDF e Excel, e a política de retenção de
RN-CLI-007.

## Sprint F4 — PWA instalável

Manifesto e service worker, sem cache de dado autenticado. Web Push permanece fora
de escopo.

## Sprint F5 — Autocadastro e recuperação de senha

Autocadastro de artista com aprovação, rejeição com motivo, reenvio após correção e
recuperação de senha por link temporário.

## Critério de avanço

Cada sprint exige critérios de aceite atendidos, testes proporcionais ao risco e
documentação atualizada antes de iniciar a seguinte.
