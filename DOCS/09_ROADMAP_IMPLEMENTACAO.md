# Roadmap de Implementação

**Status:** Aprovado em 24/09/2026. Implementação autorizada.
**Última atualização:** 24/09/2026

> Sequência de sprints para construir o sistema. Cada sprint declara objetivo,
> arquivos, dependências, riscos e resultado esperado. A ordem respeita as
> dependências reais entre módulos: nada que dependa de agenda vem antes dela.

## Regras de execução

- Uma classe própria do projeto por arquivo, sem exceção.
- Clean Code e SOLID; regra de negócio fora de rotas, schemas e tarefas do worker.
- Execução e testes sempre em containers Docker, nunca no host.
- PostgreSQL real nos testes; SQLite não substitui, por causa de `tstzrange` e `EXCLUDE`.
- Documentação atualizada na mesma entrega da mudança.
- Não avançar de sprint com teste crítico, migração ou verificação falhando.

## Situação das sprints

| Sprint | Tema | Situação |
|---|---|---|
| 01 | Fundação técnica | **Concluída em 24/09/2026** |
| 02 | Identidade, acesso e auditoria | Não iniciada |
| 03 | Clientes | Não iniciada |
| 04 | Agenda e macas | Não iniciada |
| 05 | Orçamentos e sessões | Não iniciada |
| 06 | Pagamentos | Não iniciada |
| 07 | Repasses e fechamento semanal | Não iniciada |
| 08 | Guests | Não iniciada |
| 09 | Pós-venda, notificações e worker | Não iniciada |
| 10 | Painéis, relatórios e exportação | Não iniciada |
| 11 | PWA, segurança e implantação | Não iniciada |

---

## Sprint 01 — Fundação técnica

**Objetivo:** aplicações FastAPI e Vue iniciando de forma reproduzível em
containers, com configuração por ambiente, PostgreSQL com as extensões exigidas
pelo modelo de dados, verificação de saúde e ferramentas de qualidade.

**Arquivos:** `compose.yaml`, `infrastructure/docker`, `backend/app/core`,
`backend/app/main.py`, `backend/migrations`, `frontend/src/app`, `.env.example`.

**Dependências:** nenhuma.

**Riscos:** divergência entre desenvolvimento e produção; exposição de segredos;
ausência das extensões `btree_gist` e `citext`, que bloqueariam a Sprint 04.

**Resultado esperado:** `docker compose up` sobe banco, API e interface; a migração
inicial habilita as extensões; `/api/v1/health` e `/api/v1/ready` respondem.

### Evidência de conclusão — 24/09/2026

- Três serviços no ar: `postgres` (healthy), `api` e `frontend`.
- Migração `0001` aplicada; `btree_gist` e `citext` confirmadas em `pg_extension`.
  Sem elas a Sprint 04 não teria como criar as restrições `EXCLUDE`.
- Backend: Ruff sem apontamentos, 3 testes aprovados.
- Frontend: ESLint sem apontamentos, `vue-tsc` sem erro, 3 testes aprovados.
- `GET /api/v1/health` → 200 `{"status":"ok"}`.
- `GET /api/v1/ready` → 200 `{"status":"ready","database":"reachable"}`.
- Interface em `localhost:5173` exibindo Interface, API e Database alcançáveis,
  confirmando o caminho completo navegador → proxy → API → PostgreSQL.

**Refatoração aplicada antes do fechamento:** a primeira versão tinha fábricas
(`get_settings`, `get_database`, `get_session`) como funções soltas convivendo com
classes, ferindo a regra de uma unidade por arquivo. Foram substituídas pela raiz
de composição `Container` (ADR-015 e ADR-016).

## Sprint 02 — Identidade, acesso e auditoria

**Objetivo:** conta de usuário, perfis, autocadastro com aprovação, login, logout,
recuperação de senha, sessões revogáveis e trilha de auditoria imutável.

**Arquivos:** `modules/identity`, `modules/reporting/audit`, migrações.

**Dependências:** Sprint 01.

**Riscos:** escalada de privilégio; sessão permanecer válida após bloqueio de conta.

**Resultado esperado:** os quatro perfis autenticam com acesso isolado; bloqueio e
troca de senha revogam sessões imediatamente; ações administrativas são auditadas.

## Sprint 03 — Clientes

**Objetivo:** cadastro, alerta de duplicidade, visibilidade por perfil, união de
cadastros e anonimização.

**Arquivos:** `modules/clients`.

**Dependências:** Sprint 02.

**Riscos:** exposição de ficha completa ao artista indicado, que deve ver apenas
nome, telefone e Instagram.

**Resultado esperado:** RN-CLI-001 a RN-CLI-007 cobertas, com teste negativo de
visibilidade.

## Sprint 04 — Agenda e macas

> Sprint de maior risco técnico do projeto.

**Objetivo:** macas, horário-base, exceções, solicitações, aprovação, rejeição,
remarcação, bloqueios e as duas restrições de não sobreposição.

**Arquivos:** `modules/scheduling`, migração com as restrições `EXCLUDE`,
`features/scheduling` com a timeline em CSS Grid.

**Dependências:** Sprints 02 e 03.

**Riscos:** dupla reserva por requisições simultâneas; a timeline própria é o maior
esforço de frontend do projeto.

**Resultado esperado:** conflito impossível no banco, comprovado por teste com
transações paralelas reais; modal de conflito sem opção de ignorar.

## Sprint 05 — Orçamentos e sessões

**Objetivo:** orçamento com percentual congelado na aprovação, sessões previstas,
execução, sessão parcial e conclusão.

**Arquivos:** `modules/quotes`.

**Dependências:** Sprint 04.

**Riscos:** alteração retroativa de percentual; divergência entre valor aprovado e
valor executado.

**Resultado esperado:** ciclo completo entre orçamento, agendamento, sessão e
conclusão.

## Sprint 06 — Pagamentos

**Objetivo:** sinal de €50, confirmação manual, estados do pagamento, devoluções e
regras de cancelamento, remarcação e não comparecimento.

**Arquivos:** `modules/finance/payments`.

**Dependências:** Sprint 05.

**Riscos:** arredondamento; lançamento apagado em vez de ajustado.

**Resultado esperado:** nenhum pagamento é apagado; correção sempre por ajuste
vinculado com histórico.

## Sprint 07 — Repasses e fechamento semanal

**Objetivo:** cálculo por sessão, fechamento de sexta às 20h `Europe/Dublin`,
demonstrativo do artista e ajustes negativos de devolução posterior.

**Arquivos:** `modules/finance/payouts`.

**Dependências:** Sprint 06.

**Riscos:** fechamento duplicado; erro na fronteira do horário de verão.

**Resultado esperado:** fechamento reproduzível e auditável, conferido com os
exemplos de `01_REGRAS_DE_NEGOCIO.md`.

## Sprint 08 — Guests

**Objetivo:** semanas pagas, ativação, acesso derivado, reserva restrita à semana
paga e regra 50/50 das indicações do estúdio.

**Arquivos:** `modules/guests`.

**Dependências:** Sprints 04 e 06.

**Riscos:** guest reservando fora da semana paga; perda de acesso antes do fim do
período contratado.

**Resultado esperado:** ciclo entre cadastro, pagamento, acesso, renovação e
inativação funcionando.

## Sprint 09 — Pós-venda, notificações e worker

**Objetivo:** pós-venda com vencimento em 15 dias, área com pendentes e atrasados,
fotos, outbox de e-mail e lista diária das 08h.

**Arquivos:** `modules/aftercare`, `modules/notifications`, container `worker`.

**Dependências:** Sprint 05.

**Riscos:** falha de e-mail alterando estado de negócio; agendador executando em
duplicidade.

**Resultado esperado:** e-mail diário entregue; falha registrada sem alterar estado;
reenvio sem duplicar.

## Sprint 10 — Painéis, relatórios e exportação

**Objetivo:** painéis por perfil, relatórios com os indicadores definidos,
comparação de períodos e exportação em PDF e Excel.

**Arquivos:** `modules/reporting`, `features/dashboard`.

**Dependências:** Sprints 06 a 09.

**Riscos:** relatório não reconciliando com os lançamentos; exposição de faturamento
a perfil sem permissão.

**Resultado esperado:** totais reconciliam com recebimentos, devoluções e repasses;
exportação preserva os mesmos valores da tela.

## Sprint 11 — PWA, segurança e implantação

**Objetivo:** manifesto e service worker, endurecimento de segurança, backup cifrado
com restauração testada e homologação nos quatro perfis.

**Arquivos:** `frontend/src/pwa`, `compose.production.yaml`, runbooks de operação.

**Dependências:** todas as anteriores.

**Riscos:** cache offline guardando dado autenticado; restauração nunca testada.

**Resultado esperado:** sistema homologado e pronto para implantação controlada.

## Critério de avanço

Cada sprint exige critérios de aceite atendidos, testes proporcionais ao risco e
documentação atualizada antes de iniciar a seguinte.
