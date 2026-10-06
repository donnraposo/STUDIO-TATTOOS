# Roadmap de Implementação

**Status:** Implementação autorizada. Estratégia de MVP definida em 24/09/2026.
**Última atualização:** 01/10/2026

## Onde o projeto está agora

**Concluído:** sprint 01, M1, M2, M3, M4, M5, M6, M7.1 e **a M7.2 inteira**, nas
seis etapas.

**Fora do plano original e ja entregue:** a **M9**, o faturamento do estudio
(07/10/2026) — o controle mensal que o estudio mantinha em planilha, pedido pelo
responsavel durante a M7.2.

**Próxima:** a M8 — implantação mínima.

> **O fio condutor do MVP fechou em 02/10/2026.** `login → cliente → agendar →
> sinal €50 → sessão feita e paga → repasse de sexta`: o último elo entrou com a
> M6, e o estúdio deixa de precisar calcular fora do sistema quanto paga a cada
> artista.

> **O portão do sinal estava aberto e foi fechado na M5.** A RN-AGE-005 e a
> RN-PAG-002 dizem que uma solicitação não pode ser aprovada sem sinal
> confirmado, e até 30/09/2026 o `ApproveBooking` tinha um `_deposit_is_confirmed`
> que devolvia `True` sempre — declarado como costura, mas na prática uma regra
> escrita que o sistema não cumpria.

**Progresso do MVP:** 9 das 10 sprints fechadas. Falta a M8.

> Este número dizia "9 das 11" e **não batia com a tabela logo abaixo**, que tem
> dez linhas. Conferido contra ela em 06/10/2026.

> Esta tabela descrevia 26/09/2026 e **ficou congelada por cinco dias**, afirmando
> 145 testes, migrações até a `0005` e "falta todo o dinheiro" com a M5 já
> entregue. Reescrita em 01/10/2026. É a terceira vez que isso acontece neste
> projeto, e é exatamente o que a seção 7 da `CLAUDE.md` adverte.

| O que existe | Detalhe |
|---|---|
| Módulos com código | `health`, `identity`, `clients`, `scheduling`, `quotes`, `finance`, `reporting` (só auditoria) |
| Migrações aplicadas | `0001` a `0010`: extensões, identidade e auditoria, clientes, agenda, orçamentos e sessões, pagamentos, renomeação `bench`, origem do cliente, repasses e percentual por artista |
| Endpoints | `/health`, `/ready`, `/auth/*`, `/users/*`, `/clients/*`, `/benches`, `/bookings/*`, `/quotes/*` com imagens e sessões, `/payments/*` e `/payouts/*` |
| Containers | Três: `postgres`, `api`, `frontend`. Arquivos enviados ficam no volume nomeado `object_storage` (ADR-024) |
| Testes | 279 no backend e 189 no frontend, todos aprovados |
| Frontend | Acesso, painel, clientes, agenda com a timeline e o sinal, orçamentos com sessões, pagamentos, repasses, e contas com o acordo de percentual |

> **Leitura honesta do avanço.** O fio condutor do MVP está completo no backend,
> do login ao repasse de sexta. As duas dores que justificam o sistema têm
> resposta: impedir choque de horário e saber quem recebe quanto.
>
> **O ciclo passou a se percorrer inteiro pela interface em 06/10/2026.**
> `entrar → cliente → solicitar horário → lançar e confirmar o sinal → aprovar →
> sessão feita e quitada → repasse de sexta`, sem a API em nenhum passo. O
> último elo era o sinal, e era também o único ponto em que a interface
> prometia uma ação que o servidor recusava.
>
> **A M7.2 fechou em 06/10/2026.** Toda tela do MVP existe, e cada perfil tem a
> sua entrada: o gestor abre na fila do que espera decisão, o artista no próprio
> dia.
>
> **O que falta do MVP é a M8**, implantação. Nenhuma linha do MVP tem API
> pronta e interface ausente.

### Pendências de costura entre sprints

Casos de uso já entregues que dependem de um módulo futuro. Cada ponto está marcado
no código e **precisa ser fechado na sprint indicada** — sem esta lista, a sprint
seguinte fecha sem saber tudo o que tinha de fechar.

| Ponto no código | O que falta | Fecha em |
|---|---|---|
| `ConfirmSessionPayment` | O recebimento da sessão ainda é um valor digitado; passa a se apoiar num `payment` de tipo `BALANCE` confirmado (RN-PAG-008). **Não fechou na M7.2.3:** aquela etapa era de interface, e esta é mudança de backend — passa a existir um estado intermediário entre a sessão realizada e a quitada, e o repasse lê a sessão. Precisa de decisão antes de código | Pendente de decisão |
| `payment.guest_week_id` | Coluna e origem da taxa semanal; a tabela `guest_week` ainda não existe (RN-GST-001) | Sprint do guest |

**Fechadas na M5, em 30/09/2026:**

| Ponto no código | Como fechou |
|---|---|
| `ApproveBooking._deposit_is_confirmed` | Substituído pela porta `DepositGate`, respondida pelo financeiro (ADR-028). O método devolvia verdadeiro fixo |
| `CancelBooking`, `RejectBooking`, `RescheduleBooking` | Passam o desfecho pela porta `BookingSettlementGate`; a retenção é gravada e a devolução é apontada (ADR-029) |

### Riscos abertos

| Risco | Situação |
|---|---|
| As restrições `EXCLUDE` são a hipótese técnica central do projeto | ✅ **Risco retirado em 26/09/2026.** Escritas e provadas com transações paralelas reais |
| Toda a interface concentrada na M7 | Bloco grande e sem validação incremental. Mitigar exercitando `/api/v1/docs` ao fim de cada sprint de backend |

### Retomar o ambiente

```bash
docker compose up -d
docker compose exec api alembic upgrade head
```

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

**Estratégia de execução: backend primeiro, com uma fatia de interface antecipada**
(ADR-020, revisto pelo ADR-025).

| Sprint | Tema | Camada | Situação |
|---|---|---|---|
| 01 | Fundação técnica | Ambas | ✅ Concluída em 24/09/2026 |
| M1 | Identidade e acesso | Backend | ✅ Concluída em 26/09/2026 |
| M2 | Clientes | Backend | ✅ Concluída em 26/09/2026 |
| M3 | ⚠️ Agenda e macas | Backend | ✅ Concluída em 26/09/2026 |
| M4 | Orçamentos e sessões | Backend | ✅ Concluída em 30/09/2026 |
| **M7.1** | ⚠️ Fatia vertical de interface | Frontend | ✅ Concluída em 29/09/2026 |
| M5 | Pagamentos e sinal | Backend | ✅ Concluída em 30/09/2026 |
| M6 | Repasses e fechamento semanal | Backend | ✅ Concluída em 02/10/2026 |
| **M7.2** | Restante da interface do MVP | Frontend | ✅ **Concluída em 06/10/2026**, nas seis etapas |
| **M9** | Faturamento do estúdio | Ambas | ✅ **Concluída em 07/10/2026** |
| M8 | Implantação mínima | Infra | Não iniciada |

**O detalhamento do frontend está em
[`10_ROADMAP_FRONTEND.md`](10_ROADMAP_FRONTEND.md):** telas, componentes, ordem das
etapas e critérios de aceite. O andamento continua sendo registrado **aqui**, para
não haver duas versões do status.

**A M4 esteve pausada de 27/09 a 29/09/2026**, com três das quatro etapas prontas.
Marcá-la como concluída naquele momento seria a mentira mais fácil de contar e a
mais cara de descobrir depois. A M4.4 fechou em 30/09/2026 e a sprint está inteira.

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
| M1.2 | Hash de senha, login, sessão, expiração e CSRF | ✅ Concluída em 25/09/2026 |
| M1.3 | Gestão de contas pelo gestor e matriz de permissões | ✅ Concluída em 26/09/2026 |

### Evidência da etapa M1.3 — 26/09/2026

- Endpoints: `GET /users`, `POST /users`, `POST /users/{id}/block`,
  `POST /users/{id}/unblock`.
- Ruff sem apontamentos; **51 testes aprovados**.
- Auditoria das ações administrativas gravada na mesma transação da operação.

**Matriz de permissões, coberta por teste em `AccountManagementPolicy`:**

| Ator | Cria | Bloqueia | Lista |
|---|---|---|---|
| Proprietário | Qualquer perfil | Qualquer conta | Sim |
| Gerente | Residente e guest | Residente e guest | Sim |
| Residente e guest | Não | Não | Não |

**Três garantias que o teste comprova:**

1. **O último proprietário ativo não pode ser bloqueado** (RN 2.5). A contagem usa
   `SELECT ... FOR UPDATE` para que dois bloqueios simultâneos não leiam "dois
   proprietários ativos" ao mesmo tempo e removam ambos.
2. **Bloquear encerra as sessões na mesma transação.** Se o commit falhar, a conta
   continua ativa e as sessões também — nunca fica um estado pela metade.
3. **Conta criada por gestor já nasce ativa** (RN 2.6); `PENDING_APPROVAL` pertence
   ao autocadastro, que está na Fase 2.

**Decisões tomadas durante a etapa:**

- Tradução de erro de domínio centralizada em `ErrorHandlers`, registrada na
  aplicação. Sem isso, cada rota repetiria `try/except` para converter os mesmos
  erros, e bastaria esquecer um para vazar detalhe interno em uma resposta 500.
- `SessionAuthenticator` extraído do `AuthRouter` para que todo módulo autentique
  da mesma forma. Autorização duplicada por rota é como brechas aparecem.
- `StatusHistoryRepository` criado ao perceber que o caso de uso acessava o atributo
  privado `_session` do repositório de contas, quebrando o encapsulamento.

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

### Evidência da etapa M1.2 — 25/09/2026

Commit `dced4f5`.

- Endpoints: `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`.
- Argon2id via `pwdlib`, dependência autorizada pelo responsável (ADR-010).
- Sessão no servidor com cookie `HttpOnly`, dupla expiração e CSRF por duplo envio.
- Ruff sem apontamentos; 21 testes aprovados em três execuções consecutivas.

**Três garantias de segurança cobertas por teste:**

| Garantia | Como é obtida |
|---|---|
| Login não revela se um e-mail existe | Verificação de hash descartável quando a conta não é encontrada, para que o tempo de resposta não denuncie a diferença |
| Bloqueio derruba o acesso na hora (RN 2.5) | A conta é reconferida a cada requisição, não apenas no login |
| CSRF | Duplo envio de cookie com comparação em tempo constante; o cookie de sessão é `HttpOnly` e o token CSRF precisa voltar no cabeçalho |

**Decisões tomadas durante a etapa:**

- Uma fábrica por módulo (`IdentityFactory`) em vez de concentrar tudo no
  `Container`, que viraria um objeto-deus com nove módulos previstos.
- `EmailStr` do Pydantic descartado: exigiria a dependência `email-validator`
  apenas para validar formato no login, onde isso não acrescenta segurança.

**Defeito corrigido nos próprios testes:** o helper de login não verificava a
pré-condição, produzindo falha instável com mensagem enganosa duas linhas adiante.

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

### Evidência — 26/09/2026

- Endpoints: `GET /clients`, `POST /clients`, `GET /clients/{id}`,
  `PUT /clients/{id}`, `POST /clients/merge`.
- Migração `0003`; Ruff sem apontamentos; **69 testes aprovados**.

**Os três níveis de visibilidade da RN-CLI-004, cobertos por teste:**

| Quem | Vê |
|---|---|
| Proprietário e gerente | Ficha completa de qualquer cliente |
| Artista que cadastrou | Ficha completa |
| Artista indicado pelo estúdio | **Apenas nome, telefone e Instagram** |

O terceiro caso não devolve 403: devolve menos campos. O artista indicado precisa
dos dados para atender, mas não do histórico. A restrição está no **formato da
resposta** (`ClientContactResponse`), não em um filtro na rota — assim não há como
esquecer de omitir um campo.

**Duas decisões de modelagem:**

- **Duplicidade alerta, nunca bloqueia** (RN-CLI-005). Duas pessoas podem
  legitimamente compartilhar um telefone, e travar o cadastro atrapalharia o
  atendimento. O aviso volta junto com o cliente já criado.
- **União não apaga o duplicado** (RN-CLI-006). Ele recebe `merged_into_id`
  apontando para o sobrevivente. Apagar quebraria agendamentos, sessões e
  pagamentos já ligados a ele, e a regra proíbe excluir cliente com histórico.
  As consultas ignoram registros já unidos, então a duplicidade some das listas
  sem perder o vínculo.

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

### Etapas

| Etapa | Escopo | Situação |
|---|---|---|
| M3.1 | Modelo, migração e as duas restrições `EXCLUDE` | ✅ Concluída em 26/09/2026 |
| M3.2 | Casos de uso: solicitar, aprovar e rejeitar | ✅ Concluída em 26/09/2026 |
| M3.3 | Remarcação, cancelamento e macas | ✅ Concluída em 26/09/2026 |

> Horário-base e bloqueio de horário excepcional (RN-AGE-011) ficaram fora: são
> configuração operacional e não bloqueiam o ciclo do MVP. Entram na F3.

### Evidência das etapas M3.2 e M3.3 — 26/09/2026

- Endpoints: `GET/POST /benches`, `GET/POST /bookings`, e as ações
  `/approve`, `/reject`, `/cancel` e `/reschedule` sobre `/bookings/{id}`.
- Ruff sem apontamentos; **93 testes aprovados**, sendo 24 de agenda.

**A assimetria que estrutura o módulo:** residente e guest **solicitam**;
proprietário e gerente **decidem**. O gestor pode criar já aprovado (RN-AGE-005).

| Regra | Como é garantida |
|---|---|
| Conflito de maca ou artista | Restrição do banco; o repositório traduz a violação em `409` com o agendamento conflitante, alimentando o modal da RN-AGE-007 |
| Recusa exige motivo previsto | Lista fechada validada no schema (RN-AGE-006) |
| Artista não cancela, solicita | `SchedulingPolicy.can_decide` restrito ao gestor (RN-AGE-008) |
| Recusado e cancelado liberam a agenda | Saem da cláusula `WHERE` das restrições (RN-AGE-014) |
| Não comparecimento é estado próprio | `NO_SHOW`, separado de `CANCELLED` (RN-AGE-010) |

**Decisão de projeto:** `RequestBooking` **não** verifica conflito antes de gravar.
Conferir e depois gravar reabriria exatamente a janela de corrida que o ADR-011
fecha. Quem decide é a restrição, no momento da gravação.

**Dependência declarada, resolvida em 30/09/2026:** a RN-AGE-005 exige sinal
confirmado para aprovar, e o módulo de pagamentos era a sprint M5. A costura
estava pronta em
`ApproveBooking._deposit_is_confirmed`, que devolvia verdadeiro fixo, porque
travar naquele momento impediria qualquer uso da agenda. O mesmo valia para o
destino do sinal em cancelamento, não comparecimento e remarcação fora de 24h: o
estado ficava registrado aqui e o efeito financeiro esperava a M5.

> **A M5 fechou os dois pontos.** O método deu lugar à porta `DepositGate`
> (ADR-028), e os desfechos passam pela `BookingSettlementGate`. Aprovar
> agendamento agora exige sinal confirmado, como a regra sempre disse.

### Evidência da etapa M3.1 — 26/09/2026

**O maior risco técnico do projeto foi retirado.** As duas restrições estão no
banco e comprovadas por 8 testes, entre eles a corrida com transações paralelas.

```sql
-- Maca: apenas aprovado bloqueia (RN-AGE-004, RN-AGE-007)
EXCLUDE USING gist (bench_id WITH =, period WITH &&) WHERE (status = 'APPROVED')

-- Artista: pendente e aprovado bloqueiam, mesmo entre macas (RN-AGE-014)
EXCLUDE USING gist (artist_id WITH =, period WITH &&)
WHERE (status IN ('REQUESTED', 'APPROVED'))
```

| Cenário coberto | Resultado |
|---|---|
| Dois aprovados sobrepostos na mesma maca | Recusado |
| Pendentes de artistas diferentes na mesma maca | **Permitido** — concorrem até a decisão |
| Mesmo artista sobreposto em macas diferentes | Recusado |
| Pendente já ocupa a agenda do próprio artista | Recusado o segundo |
| Recusado e cancelado | Liberam a agenda, preservando histórico |
| Agendamentos adjacentes, sem intervalo | Permitidos (RN-AGE-001) |
| Intervalo vazio | Recusado |
| **Duas transações paralelas reais** | **Apenas uma vence** |

Os testes escrevem SQL direto, sem passar por casos de uso: o que se verifica é a
garantia do banco. Se a aplicação inteira fosse reescrita, as regras continuariam
valendo.

**Detalhe de implementação:** em `text()` do SQLAlchemy, `:period::tstzrange` não
funciona — o parser lê `:period:` como marcador de parâmetro. A forma correta é
`CAST(:period AS tstzrange)`.

## Sprint M4 — Orçamentos e sessões

**Objetivo:** orçamento completo com descrição, região do corpo, tamanho, imagens de
referência, sessões previstas e aprovação pelo gestor. Percentual congelado na
aprovação. Execução, sessão parcial e conclusão.

**Arquivos:** `modules/quotes`, `features/quotes`.

**Dependências:** M3.

**Riscos:** alteração retroativa de percentual; divergência entre valor aprovado e
valor executado; as imagens de referência trazem armazenamento de objetos, que é a
primeira dependência de infraestrutura externa do projeto.

**Resultado esperado:** ciclo completo entre orçamento, agendamento, sessão e
conclusão.

### Etapas

Dividida como a M3, pelo mesmo motivo: a sprint acumula modelo, ciclo de aprovação,
execução de sessão e upload de arquivo. Entregar em bloco único tira a chance de
conferir cada regra antes da seguinte.

| Etapa | Escopo | Situação |
|---|---|---|
| M4.1 | Tabelas `quote`, `quote_reference_image` e `tattoo_session`; migração `0005`; `booking.session_id` | ✅ Concluída em 26/09/2026 |
| M4.2 | Ciclo do orçamento: criar, editar, aprovar, rejeitar, percentual congelado | ✅ Concluída em 27/09/2026 |
| M4.3 | Imagens de referência: armazenamento privado, upload e leitura autenticada | ✅ Concluída em 27/09/2026 |
| M4.4 | Sessões: gerar do orçamento aprovado, marcar realizada, sessão parcial, confirmar recebimento | ✅ Concluída em 30/09/2026 |

As imagens de referência ganharam etapa própria ao se confirmar o que a decisão de
escopo já indicava: elas trazem a primeira dependência de infraestrutura externa do
projeto, e misturar isso com o ciclo de aprovação juntaria dois assuntos sem relação
numa entrega só.

**Decisões de escopo tomadas em 26/09/2026:**

| Tema | Decisão |
|---|---|
| Imagens de referência (RN-ORC-004) | **Upload completo nesta sprint**, não apenas a tabela. Decisão revista durante a M4.3: o armazenamento é volume nomeado atrás da porta `ObjectStorage`, sem container novo, porque a imagem do MinIO deixou de ser distribuída livremente (ADR-024). O provedor gerenciado do ADR-006 segue como destino de produção, na M8 |
| Limites das imagens | 10 MB por arquivo, JPEG/PNG/WebP, até 10 por orçamento. Em `Settings`, ajustáveis por ambiente |
| Remoção de imagem | Incluída, embora a RN-ORC-004 não a mencione: anexar o arquivo errado é banal. Apaga o arquivo de verdade, não só desvincula, porque imagem é dado pessoal (RN-CLI-007) |
| Histórico de estado | `audit_log`, sem tabela paralela (ADR-023) |
| Ordem em relação à M5 | M4 antes da M5: pagamento se liga à sessão, então a sessão precisa existir primeiro. A conclusão de sessão da RN-ORC-005 depende de pagamento confirmado e entra na lista de pendências de costura |

### Evidência da etapa M4.4 — 30/09/2026

**A sessão existe, e com ela a M4 fecha.** O ciclo vai do orçamento aprovado à
sessão concluída, que é a unidade sobre a qual a M6 vai calcular repasse.

Confronto com as regras:

| Regra | Como o backend cumpre |
|---|---|
| **RN-ORC-005** | O artista marca realizada; o gestor confirma o valor recebido; só então a sessão fica `PAID_OFF`. São dois atos e dois estados, não um campo booleano |
| **RN-ORC-005**, correções | Confirmar um valor diferente do informado **exige motivo**, que vai para a auditoria no campo `reason` |
| **RN-ORC-006** | Sessão interrompida vira `PARTIALLY_DONE` com o valor efetivamente cobrado, e é ele que entra no cálculo do comprometido |
| **RN-ORC-006**, ajuste | O gestor refaz as sessões restantes; se o comprometido deixar de fechar com o valor aprovado, o orçamento volta a Pendente e o percentual congelado é descartado |
| **RN-REP-006** | `origin` e `artist_percentage` são copiados para cada sessão na aprovação. Reaprovar com outro percentual não alcança o que já foi executado |

**Decisões tomadas durante a implementação:**

| Tema | Decisão |
|---|---|
| Quando as sessões nascem | **Na aprovação, mesma transação.** Orçamento aprovado sem sessões não significa nada: ninguém tem o que marcar como realizado e o repasse não tem sobre o que incidir. Um segundo passo dependeria de alguém lembrar de chamá-lo depois de aprovar pela tela |
| Reaprovação | Sessão já resolvida fica onde está, com o número de sequência que tem; as agendadas são descartadas e recriadas pelo plano novo. Recriar tudo apagaria trabalho executado; não recriar nada deixaria o plano velho valendo |
| Parcial e completa num caso de uso só | Valor ausente significa sessão inteira. Um parâmetro booleano ao lado do valor diria a mesma coisa duas vezes e abriria a chance de dizer as duas diferente. Parcial exige cobrar **menos** que o previsto — aceitar o valor igual marcaria como interrompida uma sessão que correu inteira |
| `CANCELLED` e `NO_SHOW` | **Fora desta etapa.** Os dois estados existem na tabela desde a M4.1, mas quem os produz é o cancelamento e o não comparecimento do agendamento, cuja consequência é financeira (RN-PAG-004) e pertence à M5 |
| Confirmação de recebimento | Lançada à mão, como a RN-PAG-006 permite nesta versão. Na M5 ela passa a se apoiar num pagamento confirmado em vez de num valor digitado |

**Um defeito de infraestrutura de teste apareceu ao crescer a suíte.** Cada teste
monta um `Container` próprio, com engine próprio, e o pool nunca era devolvido:
ao passar de cento e poucos testes o PostgreSQL começou a recusar conexão com
`sorry, too many clients already`, derrubando treze testes que não tinham nada de
errado. `Database.dispose()` existe por isso, e o `conftest` o chama a cada teste.

- Ruff limpo; **172 testes** no backend; verificação de uma classe por arquivo sem
  apontamento. Conferido também contra o servidor rodando: aprovação gerando as
  quatro sessões com 70% congelado, parcial de €100 sobre €250, correção para
  €150 recusada sem motivo e aceita com ele, e o ajuste devolvendo o orçamento a
  Pendente por não fechar com o total aprovado.

### Evidência da etapa M4.3 — 27/09/2026

- Endpoints: `GET/POST /quotes/{id}/reference-images`,
  `DELETE /quotes/{id}/reference-images/{image_id}` e
  `GET /quotes/{id}/reference-images/{image_id}/content`.
- Ruff sem apontamentos; **139 testes aprovados**, sendo 20 novos: 12 das imagens
  pela API e 8 do adaptador de armazenamento.
- **Nenhum container novo no ambiente.**

**A imagem do MinIO deixou de ser distribuída livremente**, e a decisão de escopo
desta sprint foi revista por isso: o armazenamento passou a ser um diretório em
volume nomeado, atrás da porta `ObjectStorage` (ADR-024). O destino de produção
continua sendo provedor gerenciado compatível com S3, retomado na M8.

**A troca melhorou a segurança em vez de piorar.** Sem S3 não há URL assinada, e a
imagem passou a ser entregue por rota autenticada: **não existe endereço capaz de
devolver a foto sem o cookie de sessão.** Um link assinado funciona sozinho até
expirar, e basta vazar num histórico de navegador ou num encaminhamento. A resposta
vai com `Cache-Control: private, no-store`.

| Garantia | Como é obtida |
|---|---|
| Imagem segue a visibilidade do orçamento | `QuotePolicy.can_see` no caso de uso de leitura; artista de fora recebe 403, não a foto |
| Imagem de um orçamento não sai por outro | A leitura confere que a imagem pertence ao orçamento da rota. Sem isso, o controle estaria no orçamento da URL e o dado viria de outro lugar |
| Limites de tipo, tamanho e quantidade | `ReferenceImagePolicy`, com 10 MB, JPEG/PNG/WebP e 10 por orçamento vindos de `Settings` — são operacionais, o estúdio muda sem nova versão |
| Chave do objeto nunca sai na resposta | `ReferenceImageResponse` não tem o campo; o que sai é o caminho autenticado |
| Nome do arquivo enviado não entra na chave | A chave é sorteada. O nome vem do cliente e pode trazer caminho, acento ou o nome da pessoa retratada |
| Chave não escapa da raiz do armazenamento | `FilesystemObjectStorage` recusa `..` e caminho absoluto, com teste para os três formatos |

**A ordem entre banco e arquivo é deliberada e inversa nas duas operações.** Anexar
grava o arquivo antes da linha; remover apaga a linha antes do arquivo. As duas
seguem a mesma regra: **o banco nunca deve apontar para um arquivo que não existe.**
A sobra possível é sempre arquivo órfão, que é lixo invisível, nunca linha órfã, que
aparece na tela como imagem quebrada. Fica uma janela estreita na remoção, se o commit
falhar depois de o arquivo já ter sido apagado; está registrada no próprio caso de uso
em vez de disfarçada.

**Anexar não devolve o orçamento a pendente**, e há teste para isso. A RN-ORC-003
trata de alterar o orçamento, e imagem de referência não é termo do acordo. Reabrir
uma aprovação porque alguém acrescentou uma foto puniria o cuidado de documentar
melhor o trabalho. A permissão, ainda assim, é a de editar: num orçamento aprovado,
só o gestor anexa.

**Gravação atômica.** O arquivo é escrito em temporário e movido com `os.replace`.
Escrever direto no destino deixaria um arquivo truncado se o processo morresse no
meio, e o banco apontaria para uma imagem pela metade — pior do que imagem ausente,
porque parece existir.

**A suíte não ganhou dependência de serviço.** Cada teste recebe uma raiz de
armazenamento própria, em diretório temporário, montada no `conftest`. Sem isso, um
arquivo gravado por um teste ficaria visível para os seguintes e o teste do limite de
quantidade passaria ou falharia conforme a ordem de execução.

### Evidência da etapa M4.2 — 27/09/2026

- Endpoints: `GET/POST /quotes`, `GET/PUT /quotes/{id}`, `POST /quotes/{id}/approve`
  e `/reject`.
- Ruff sem apontamentos; **119 testes aprovados**, sendo 15 novos do ciclo do
  orçamento.

**A regra que estrutura a etapa:** residente propõe, gestor decide — a mesma
assimetria da agenda, com uma diferença que não existe lá. **O guest não acessa
orçamento** (RN-ORC-001), e como o guest tatua, a política confere o **perfil**, não
se a pessoa atua como artista. Qualquer verificação por `actor.tattoos` o deixaria
passar.

| Regra | Como é garantida |
|---|---|
| Percentual congelado na aprovação | 70% para cliente próprio, 50% para indicação (RN-REP-001 e RN-REP-002), gravados no orçamento. Restrição do banco recusa aprovado sem percentual |
| Gestor corrige o percentual do atendimento | Campo opcional na aprovação (RN-CLI-003). A auditoria guarda o aplicado **e** o padrão da origem, para que um acordo fora do padrão seja rastreável |
| Editar aprovado volta a pendente | E **apaga o percentual congelado**, a data e o responsável (RN-ORC-003) |
| Recusa exige motivo | Texto livre com `min_length`, para que campo vazio não satisfaça a exigência |
| Residente edita só o próprio e só pendente | `QuotePolicy.can_edit`. Editar o que já foi aprovado derrubaria a aprovação sozinho |

**O cenário que mais importa está coberto por teste:** editar um orçamento aprovado
limpa o percentual. As duas regras separadas parecem inofensivas; juntas, um
percentual sobrevivente num orçamento pendente permitiria à próxima aprovação passar
sem regravá-lo, aplicando o acordo antigo a um valor novo.

**Decisões de projeto da etapa:**

- **`QuoteDetails`, um objeto de valor com os campos editáveis.** A primeira versão
  passava os oito campos soltos: `CreateQuote.execute` com dez parâmetros,
  `UpdateQuote.execute` com onze, a mesma lista repetida em dois schemas e duas
  rotas. Acrescentar um campo ao orçamento significava editar seis lugares, com a
  chance de esquecer o caminho menos usado. Agora criar e editar recebem
  `details`, e `QuoteRequest` herda de `QuoteFieldsRequest` acrescentando apenas
  cliente e artista.
- **A edição não aceita `client_id` nem `artist_id`.** Reatribuir um orçamento a
  outro cliente ou artista não é edição; numa tela de correção de valores, isso
  moveria histórico de atendimento sem deixar claro que foi o que aconteceu.
- **Aparar texto é do schema, não do caso de uso.** `strip_whitespace` no
  `QuoteFieldsRequest` em vez de `.strip()` espalhado: limpar espaço do que foi
  digitado é assunto da borda, não da regra de negócio.
- **Aprovar e rejeitar são ações próprias, não um `PUT` mudando `status`.** A
  aprovação congela percentual e registra quem decidiu; não é editar um campo.

**Ponto ainda aberto:** o motivo de rejeição segue como texto livre, conforme
registrado na M4.1. Se o estúdio quiser lista fechada, é `CHECK` em migração nova.

### Evidência da etapa M4.1 — 26/09/2026

- Migração `0005`: `quote`, `quote_reference_image`, `tattoo_session` e a coluna
  `booking.session_id`. Aplicada, revertida e reaplicada com sucesso.
- Ruff sem apontamentos; **104 testes aprovados**, sendo 11 novos de restrição.

**A regra que o banco passou a garantir, e não só a aplicação:**

| Restrição | O erro que ela impede |
|---|---|
| `ck_quote_approved_freezes_percentage` | Orçamento aprovado sem percentual congelado. Sem a restrição, bastaria um caminho de aprovação esquecer de gravar `artist_percentage` para que o repasse fosse calculado meses depois com o percentual vigente na data do cálculo, sobre um trabalho acordado sob outro percentual (RN-REP-006) |
| `ck_tattoo_session_partial_requires_charged` | Sessão parcial sem valor cobrado, que não tem sobre o que calcular repasse (RN-ORC-006) |
| `ck_tattoo_session_paid_off_requires_confirmation` | Sessão quitada sem confirmação do gestor, ou seja, trabalho não pago entrando no repasse de sexta (RN-ORC-005) |
| `ck_tattoo_session_performed_requires_date` | Sessão realizada sem data real, que deixaria o pós-venda sem vencimento (RN-POS-001) |
| `uq_tattoo_session_sequence` | Duas sessões número 1 no mesmo orçamento, tornando ambígua a ordem que liga cada sinal de €50 à sua sessão |
| `uq_booking_live_session` | Dois agendamentos vivos para a mesma sessão, isto é, a mesma sessão executada duas vezes |

**Duas decisões tomadas durante a etapa:**

- **A tabela se chama `tattoo_session`, não `session`.** `Session` já é a sessão de
  banco do SQLAlchemy, importada em todo repositório, e `user_session` é a sessão de
  login. O nome final de tabela estava explicitamente reservado para a revisão de
  implementação na seção 14 do modelo de dados.
- **`origin` e `artist_percentage` são copiados do orçamento para a sessão**, em vez
  de lidos do orçamento na hora do repasse. O orçamento pode voltar a pendente e ser
  reaprovado com outro percentual; o que já foi executado continua valendo o que
  valia. Uma consulta ao orçamento no momento do cálculo reescreveria o passado.

**O índice da sessão é parcial de propósito.** Cancelado e recusado saem da cláusula
`WHERE`, como nas restrições `EXCLUDE` da `0004`: remarcar depois de cancelar
continua possível. Há teste para o caso oposto — dois agendamentos sem sessão ligada
convivem, porque o índice só vale quando `session_id` não é nulo, e é isso que
mantém funcionando toda a agenda entregue na M3.

**Ponto a confirmar na M4.2:** o motivo de rejeição do orçamento ficou como texto
livre. A RN-ORC-003 exige motivo, mas não define lista fechada, diferente da
RN-AGE-006 na agenda. Se o estúdio quiser lista fechada, é `CHECK` na `0006`.

## Sprint M5 — Pagamentos e sinal

**Objetivo:** sinal de €50, confirmação manual pelo gestor, estados do pagamento,
devoluções e as regras de cancelamento, remarcação e não comparecimento.

**Arquivos:** `modules/finance/payments`, `features/finance`.

**Dependências:** M4.

**Riscos:** arredondamento; lançamento apagado em vez de ajustado.

**Resultado esperado:** nenhum pagamento é apagado; correção sempre por ajuste
vinculado com histórico.

### Evidência da sprint M5 — 30/09/2026

**O sinal existe e o portão fechou.** Aprovar um agendamento passa a exigir
pagamento confirmado (RN-AGE-005 e RN-PAG-002), e os desfechos do horário têm
consequência registrada sobre o dinheiro.

| Regra | Como o backend cumpre |
|---|---|
| **RN-PAG-001** | €50 por agendamento, e um sinal vivo por vez, garantido pelo índice parcial `uq_payment_live_deposit` |
| **RN-PAG-002** | Informar e confirmar são atos separados; confirmado não existe sem quem confirmou e quando, por restrição de banco |
| **RN-PAG-006** | Só gerente e proprietário lançam e confirmam; depósito, dinheiro e cartão são registros manuais, sem gateway |
| **RN-PAG-007** | `Informado → Confirmado ou Recusado → Devolvido ou Estornado` num mapa de dados; recusado é final e não volta a confirmado; não há rota de exclusão |
| **RN-PAG-009** | Devolução é linha própria vinculada ao original, com forma que pode diferir da do pagamento |
| **RN-PAG-003** | Recusa pelo estúdio aponta o sinal para devolução integral |
| **RN-AGE-009 / 010** | Cancelamento e não comparecimento retêm o sinal, mesmo com aviso de 24 horas |
| **RN-AGE-008** | Dentro do prazo os valores acompanham o horário; fora dele o sinal é retido e o agendamento passa a exigir um novo |
| **RN-GST-004** | Cliente próprio do guest não exige sinal — esses valores não passam pelo estúdio |

**Duas perguntas que a documentação não fechava foram decididas com o usuário:**

| Pergunta | Decisão |
|---|---|
| Onde grava o sinal de um agendamento sem sessão? | **No agendamento.** O sinal é pago e recebido pelo estúdio para que o horário possa ser confirmado; a solicitação fica pendente até o gestor confirmar no sistema que recebeu. `payment.booking_id` entrou no modelo por isso |
| Cliente próprio do guest exige sinal? | **Não.** A RN-GST-004 prevalece: esses valores não passam pelo estúdio |

**Decisões tomadas durante a implementação:**

| Tema | Decisão |
|---|---|
| Retém sozinho, devolve nunca | Reter é escrituração — o estúdio já está com o dinheiro e a RN-AGE-009 diz que ele fica. Devolver é movimento de caixa, e a RN-PAG-009 manda o gestor registrar **depois de realizá-la**. O sistema aponta o que deve voltar; não lança a saída sozinho |
| `retained_at` separado de `REFUNDED` | Um sinal retido continua confirmado. Um estado só esconderia se o dinheiro ficou ou saiu |
| Criar já aprovado | A RN-AGE-005 permite *"desde que confirmem o sinal"*, e o sinal pertence ao agendamento — que não existe no instante da criação. O atalho passa a ser recusado onde há sinal a confirmar, e continua aberto onde a regra não o pede (RN-GST-004). O caminho é: criar, confirmar o sinal, aprovar |
| Fronteira entre os módulos | A agenda declara as portas `DepositGate` e `BookingSettlementGate`; o financeiro as implementa; o `Container` liga. A agenda continua sem saber o que é um pagamento (ADR-016) |
| `guest_week_id` | Fora da `0006`: a tabela `guest_week` ainda não existe, e chave estrangeira para tabela inexistente quebra a migração. Entra na sprint do guest |

- Ruff limpo; **205 testes** no backend; uma classe por arquivo sem apontamento.

> **A suíte inteira só foi conferida no dia seguinte à entrega.** A VM do Docker
> desta máquina passou a sistema de arquivos somente-leitura no meio da primeira
> execução e derrubou o container da API — a mesma instabilidade já registrada
> nas entregas anteriores. O commit da M5 foi feito declarando isso, com as
> suítes de agenda (31) e de financeiro (32) verdes mas o total não conferido.
> Reiniciado o Docker, `pytest` inteiro passou: 205 testes.

## Sprint M6 — Repasses e fechamento semanal

**Objetivo:** cálculo por sessão, fechamento de sexta às 20h `Europe/Dublin`,
demonstrativo do artista e ajustes negativos de devolução posterior.

**Arquivos:** `modules/finance/payouts`.

**Dependências:** M5.

**Riscos:** fechamento duplicado; erro na fronteira do horário de verão.

**Resultado esperado:** fechamento reproduzível e auditável, conferido com os
exemplos de `01_REGRAS_DE_NEGOCIO.md`.

### Decisão a tomar nesta sprint: agendador ou cálculo sob demanda

A RN-REP-004 diz que **"o sistema calculará os repasses depois do fechamento"** das
20h de sexta. Cálculo agendado precisa de agendador, e o worker está planejado para a
Fase 2 (ADR-008). Duas saídas, com efeito direto em quantos containers a implantação
da M8 precisa hospedar:

| Caminho | Containers | Observação |
|---|---|---|
| Worker mínimo já na M6 | +1 em produção | A Fase 2 reaproveita o container para o outbox e a lista diária das 08h |
| Cálculo sob demanda | nenhum a mais | A semana encerra às 20h por regra de data; o cálculo acontece quando alguém abre a tela de repasses daquela semana |

**Recomendação registrada:** cálculo sob demanda no MVP. O resultado é idêntico —
ninguém consulta repasse às 20h de sexta — e evita subir infraestrutura que só a
Fase 2 realmente exige.

> **Decidido pelo responsável em 02/10/2026: cálculo sob demanda.** A M8 segue
> com três containers, e o worker continua previsto apenas para a Fase 2.

Seja qual for o caminho, o risco de fechamento duplicado continua sendo resolvido no
banco, por unicidade da semana fechada, e não pela garantia de que só existe um
processo executando.

## Sprint M7.1 — Fatia vertical de interface

> **Detalhamento completo em [`10_ROADMAP_FRONTEND.md`](10_ROADMAP_FRONTEND.md).**
> Aqui fica apenas o resumo e o andamento.

**Objetivo:** interface utilizável e demonstrável sobre o que a API já entrega —
acesso, clientes, agenda com a timeline de macas e orçamentos.

**Arquivos:** `frontend/src/app`, `frontend/src/features/*`,
`frontend/src/shared/*`, e `scripts/seed_demo.py` para os dados de demonstração.

**Dependências:** M1, M2, M3 e as etapas M4.1 a M4.3.

**Riscos:** a timeline de macas é o único componente do frontend sem biblioteca
pronta (ADR-004) e a maior incerteza de estimativa do projeto; a demonstração pode
criar a expectativa de que o financeiro já existe.

### Etapas

| Etapa | Escopo | Situação |
|---|---|---|
| M7.1.1 | Casca, acesso, cliente HTTP, componentes base e dados de demonstração | ✅ Concluída em 29/09/2026 |
| M7.1.2 | Clientes | ✅ Concluída em 29/09/2026 |
| M7.1.3 | ⚠️ Agenda e macas, com a timeline em CSS Grid | ✅ Concluída em 29/09/2026, em duas partes |
| M7.1.4 | Orçamentos e imagens de referência | ✅ Concluída em 29/09/2026 |

### Evidência da etapa M7.1.4 — 29/09/2026

**O ciclo do orçamento existe em `/quotes`**, e com ele a fatia vertical fecha:
da autenticação ao dinheiro acordado, tudo o que a API entrega tem tela.

Confronto com a seção 5 das regras de negócio:

| Regra | Como a tela cumpre |
|---|---|
| **RN-ORC-001** | O item "Quotes" não aparece para o guest. A rota existe para todos, e quem digitar o endereço recebe 403 da API, que o `AsyncState` mostra **sem** oferecer "tentar de novo" — insistir não muda permissão |
| **RN-ORC-002** | Aprovar e rejeitar só aparecem para gestor. O detalhe mostra a decisão registrada: data, hora e o percentual congelado |
| **RN-ORC-003** | **O formulário avisa antes de salvar** que editar um aprovado o devolve a Pendente e descarta o percentual acordado, com o número escrito no aviso. Cliente e artista não aparecem na edição: reatribuir não é editar |
| **RN-ORC-004** | Todos os campos, incluindo as imagens de referência opcionais |
| **RN-REP-006** | A aprovação mostra o que será congelado — 70% para cliente próprio, 50% para indicação — e aceita a correção pontual da RN-CLI-003 num campo opcional, que vazio mantém o padrão |
| **RN-PAG-001** | O formulário avisa quando sessões × valor por sessão não fecha com o total. **Avisa, não impede:** o backend não recusa esse caso hoje, e bloquear só no navegador daria a impressão de uma garantia que o sistema não tem |

**Verificado com dados reais, não só em teste.** Um orçamento aprovado a 70% teve
o valor total alterado e voltou a Pendente com a participação zerada; a imagem de
referência subiu, apareceu na lista e foi removida, e a rota de leitura devolveu
`image/png` com `private, no-store`.

**Um defeito de interface apareceu no caminho.** Decidido o orçamento, o modal
continuava no modo de decisão, oferecendo "Confirm approval" sobre algo já
aprovado — e o segundo clique voltava com "Only a pending quote can be
approved.", que quem acabara de aprovar lia como falha da própria aprovação. O
modal agora volta à leitura quando o estado muda debaixo dele.

**Corrigido junto:** o item "Overview" ficava aceso sobre qualquer tela, porque a
rota raiz é prefixo de todas as outras e a classe `router-link-active` é de
prefixo. Dois itens marcados ao mesmo tempo, e nenhum dizendo onde se está.

**Dois componentes base novos**, porque a alternativa era controle cru na tela:
`AppTextarea` para a descrição e as observações, e `AppFileInput`, que esconde o
`<input type="file">` — cujo botão nativo nenhum navegador deixa estilizar por
completo — atrás de um `AppButton`.

**Três classes puras novas**, testáveis sem montar tela: `QuoteDraftCheck`
(validação e a soma das sessões **em centavos inteiros**, porque três sessões de
€133,33 somam 399.99000000000007 em ponto flutuante e a tela acusaria diferença
onde não há), `QuoteDisplay` (estados, origens e percentual padrão) e `ByteSize`.

- ESLint e `vue-tsc` limpos; **83 testes** no frontend; quatro verificações de
  convenção sem apontamento.

### Correção de status — 29/09/2026

> **Esta etapa foi declarada concluída antes de estar.** O registro original
> cobria RN-AGE-001 a 007 e 014, mas deixava a **RN-AGE-004 pela metade** e as
> RN-AGE-008, 009 e 010 **de fora**. A segunda parte, abaixo, fechou o que
> faltava. O erro foi de registro, não de código: eu marquei como pronto o que
> ainda não cumpria as regras.

### Evidência da etapa M7.1.3, segunda parte — 29/09/2026

Confronto tela a tela com a seção 4 das regras de negócio, e o que faltava:

| Regra | O que a tela não fazia | Agora |
|---|---|---|
| **RN-AGE-004** | Duas solicitações no mesmo horário se empilhavam e **a de cima escondia a de baixo** — o gestor decidia sem saber que havia concorrência | `LanePacker` distribui em trilhas; o modal mostra a data e hora do pedido, que é o critério da regra |
| **RN-AGE-005** | Aprovava em silêncio sem mencionar sinal | A tela informa que o depósito precisa ser confirmado e que o sistema ainda não o registra |
| **RN-AGE-008** | Remarcação inexistente na tela | Novo intervalo e maca opcional, pelo endpoint que já existia sem uso |
| **RN-AGE-009 / 010** | Cancelamento e não comparecimento inexistentes | No modal de decisão, com motivo obrigatório |

**Cada decisão mostra o que faz com o dinheiro antes de ser confirmada.** As
regras tratam o sinal de formas diferentes em cada caso — cancelar retém mesmo
com aviso de 24h, não comparecer retém e ainda tira o repasse do artista,
remarcar depende do prazo. Isso virou `BookingConsequence`, classe pura: o texto
da regra não pode variar de tela para tela.

**O que a tela não executa, e diz:** o efeito financeiro pertence à M5. A
interface informa a consequência determinada pela regra; quem a aplica é o
módulo de pagamentos, que ainda não existe.

**Entregue junto:** alinhamento dos botões, responsividade de celular e tablet,
e a unificação dos campos em `AppField` e `.control`. Detalhe em
[`10_ROADMAP_FRONTEND.md`](10_ROADMAP_FRONTEND.md).

- ESLint e `vue-tsc` limpos; **59 testes** no frontend; quatro verificações de
  convenção sem apontamento.

### Evidência da etapa M7.1.3, primeira parte — 29/09/2026

**A timeline existe e mostra o dia.** Macas no eixo Y, horas no eixo X, em CSS
Grid sem biblioteca (ADR-004). O maior risco de estimativa do frontend saiu do
caminho.

- Rota `/schedule`; backend ganhou recorte por intervalo em `GET /bookings`.
- ESLint sem apontamentos, `vue-tsc` sem erro, **47 testes** no frontend, **9
  deles** só da aritmética de posicionamento.

**`BookingPlacement` é classe pura, separada do componente.** A aritmética —
minutos desde a abertura, largura proporcional, virada do horário de verão — é o
que tem chance real de estar errado, e testá-la não exige montar tela. Dentro do
componente, seria testada pela aparência ou não seria testada. Os nove testes
cobrem, entre outros:

| Cenário | Por que importa |
|---|---|
| Mesmo instante com deslocamentos diferentes cai na mesma coluna | Agenda deslocada por uma hora **parece correta** na tela; é o erro que ninguém percebe |
| Sessão que começou antes da abertura é **aparada**, não descartada | Ela ocupa a maca de verdade; sumir esconderia ocupação real |
| Meia-noite lida como fim do dia | Sem isso o bloco apareceria invertido, com fim antes do começo |
| Sessão de dez minutos nunca colapsa para largura zero | Bloco invisível faria a maca parecer livre |

**Pendente e aprovado parecem diferentes, e isso não é decoração:** pendente não
bloqueia a maca para outro artista, aprovado bloqueia (RN-AGE-004). O pendente é
contorno âmbar; o aprovado, bloco sólido escuro.

**O nome do cliente é composto no navegador**, cruzando a lista que a interface
já consome. Não é gambiarra a desfazer: é junção sobre conjunto pequeno, e o
gatilho para levá-la ao servidor é volume, não estética. Quem não acessa o
cadastro de clientes — o guest — vê o bloco sem nome, em vez de tela quebrada.

**Aprovar, recusar e o modal de conflito entraram no mesmo dia.** A recusa usa
seletor e não campo livre, porque a lista da RN-AGE-006 é fechada: ela alimenta o
tratamento financeiro do sinal e os relatórios de cancelamento, e texto livre
tornaria os dois inúteis. A observação segue livre e opcional.

**O modal da RN-AGE-007 não tem saída pelo conflito.** Sem botão de "criar assim
mesmo", sem fechar clicando no fundo, sem Esc. A única ação é voltar e escolher
outro horário. Isso não é rigor decorativo: a restrição `EXCLUDE` recusaria a
gravação de qualquer jeito (ADR-011), e um botão de ignorar produziria um erro
incompreensível em vez de uma explicação — ensinando a equipe a insistir.

**Exercitado de ponta a ponta:** com um aprovado das 15h30 às 16h30 na maca 1,
aprovar o pendente das 16h às 18h abriu o modal identificando o agendamento
existente pelo nome e horário.

### Dois defeitos encontrados pela tela, e corrigidos

**O `409` não levava a reserva conflitante.** `BookingConflictError` carregava
`scope` e `conflicting_booking_id` desde a M3, mas o `ErrorHandlers` serializava
só a mensagem. O modal exigido pela RN-AGE-007 era **impossível de construir**, e
nada acusava isso: o conflito era recusado corretamente, o teste passava, e só a
tela ficava sem poder cumprir a regra. Agora um erro de domínio pode expor um
dicionário `details` que a resposta incorpora — extensão por dados, sem
condicional no tradutor.

**A API não conseguia gravar agendamento nenhum.** `booking.session_id` aponta
para `tattoo_session`, e **nenhum caminho de importação da aplicação carregava
esse modelo** — só o `env.py` das migrações e a suíte de testes. O servidor subia,
respondia consultas e quebrava com `NoReferencedTableError` no primeiro `INSERT`.
A suíte não pegava porque o pytest carrega todos os módulos de teste no mesmo
processo, e os testes de orçamento importavam o modelo que faltava: **o defeito
existia exatamente onde não havia teste olhando, que é o servidor rodando de
verdade.**

A correção é `app/core/orm_registry.py`, um registro único importado pela raiz de
composição e pelo `env.py`. Um lugar só lista o que está mapeado, e a duplicação
de listas entre aplicação e migrações desapareceu junto.

### Evidência da etapa M7.1.2 — 29/09/2026

- Tela `/clients`: lista, cadastro, edição e alerta de duplicidade.
- Ruff não se aplica; ESLint sem apontamentos, `vue-tsc` sem erro, **30 testes
  aprovados** no frontend, verificações de convenção sem resultado.

**A RN-CLI-004 foi verificada com dados reais**, e não por inspeção de código:

| Quem | Vê |
|---|---|
| Proprietário | 3 clientes |
| `resident@studio.ie` | 2 — os que cadastrou |
| `resident2@studio.ie` | 1 — o que cadastrou |

**A tela não filtra nada.** O backend já devolve apenas o que o ator pode ver; se
o frontend repetisse a regra, teria de acertá-la duas vezes, e a cópia da
interface seria a que silenciosamente ficaria para trás. O que a tela faz é
**explicar** o recorte — "Only the clients you registered" —, para que o
residente não conclua que o estúdio tem dois clientes no total.

**O alerta de duplicidade avisa e não bloqueia** (RN-CLI-005), e o texto diz isso
com todas as letras: "Saved. Possible duplicate." O cliente já foi criado quando
o aviso aparece, em tom de atenção e não de erro — se soasse como falha, quem
está na recepção acharia que precisa refazer o cadastro.

**Correção estrutural feita no caminho.** A verificação de convenção acusou os
três componentes de apresentação importando de `shared/api`. Eles importavam
apenas **tipos**, o que é legítimo, mas em vez de afrouxar a regra separei
domínio de infraestrutura como no backend: os tipos foram para `shared/domain/`.
Agora `shared/api` significa exatamente "fala com a rede", e a verificação volta
a ser precisa sem exceção.

**O que ficou de fora:** a união de cadastros duplicados (RN-CLI-006). A API está
pronta, mas a ação exige escolher dois registros e confirmar o sobrevivente, que
é uma interação própria. Não está nos critérios de aceite desta etapa e entra na
M7.2, junto das telas de gestão.

### Evidência da etapa M7.1.1 — 28/09/2026

> **Fechada em 29/09/2026.** Este registro nasceu dizendo "aceite não
> verificado", porque o Docker estava travado quando a etapa foi escrita. O
> ambiente foi destravado, o `seed_demo.py` construído e os quatro critérios
> exercitados. O texto abaixo foi atualizado; o que valia antes está no commit
> `2b5476b`.

**Verificado:** ESLint sem apontamentos, `vue-tsc` sem erro, **38 testes
aprovados**, e as três verificações de convenção do `CLAUDE.md` sem resultado —
nenhum valor visual fora dos tokens, nenhum componente de apresentação falando com
a API.

**Os quatro critérios de aceite, e como cada um foi provado:**

| Critério | Prova |
|---|---|
| Os perfis entram e veem navegação diferente | Proprietário vê Overview, Clients e System; residente vê Overview e Clients, **sem System**. Conferido na tela e fixado em teste de `ProfilePermissions`, para não depender de conferência manual |
| 401 devolve ao login sem tela quebrada | Recarregar uma rota protegida sem sessão levou a `/login?redirect=/`, preservando o destino |
| Conta bloqueada perde acesso na requisição seguinte | `GET /auth/me` do residente respondeu **200 antes e 401 depois** do bloqueio pelo proprietário, sem nova autenticação no meio. A conta foi desbloqueada em seguida (RN 2.5) |
| Sair encerra a sessão no servidor | Reutilizar o **mesmo cookie** depois do logout respondeu 401. Não é só a interface esquecendo: a sessão deixou de existir |

**Fundações entregues**, e o motivo de cada uma existir como peça própria:

| Peça | Existe porque |
|---|---|
| `HttpClient` | Única costura com a rede. O tratamento do 401 é registrado nele uma vez: a sessão cai no meio do uso de verdade, já que o backend reconfere a conta a cada requisição (RN 2.5). Se cada tela tratasse, bastaria uma esquecer |
| `ApiError` | Traduz `detail` nas **duas** formas que o backend usa: texto, do `ErrorHandlers`, e lista de objetos, do Pydantic. Tratar só a primeira faria todo formulário recusado mostrar "status 422" e esconder o campo errado |
| `SessionStore` | Estado da sessão, somente leitura para as telas. `restore` nunca propaga falha — tela branca é resposta pior que o formulário de login. `signOut` encerra no servidor **antes** de esquecer localmente |
| `ProfilePermissions` | Espelha as políticas do backend para **esconder**, nunca para impedir |
| `StudioClock` | `Europe/Dublin` fixo, nunca o fuso do navegador. Tem teste atravessando a virada do horário de verão |
| `MoneyFormatter` | Recebe texto decimal, não número: `Numeric(12,2)` existe para que arredondamento binário não toque em repasse |
| `AsyncState` | Dá mecanismo à regra dos quatro estados, que existia só no papel. Separa "proibido" de "falhou", porque 403 não muda por insistir |

**Interface entregue:** login em tela dividida, casca com barra lateral, dez
componentes base e a entrada provisória. A linguagem visual extraída das
referências está na seção 4.0 de [`10_ROADMAP_FRONTEND.md`](10_ROADMAP_FRONTEND.md).

### Duas correções de ambiente que a etapa exigiu

| Problema | Correção |
|---|---|
| Outro projeto na máquina ocupava 5432 e 8000 | As portas publicadas deste projeto passaram a **5433** e **8001**. Dentro da rede do compose nada mudou; só o acesso a partir do host. O `/api/v1/docs` agora é `http://localhost:8001/api/v1/docs` |
| `postgres:17-alpine` quebrava ao criar cluster novo | Trocada pela variante Debian, `postgres:17`. O erro era `Exec format error` carregando `dict_snowball.so` durante o `initdb`, com arquitetura correta dos dois lados. **A causa provável era a VM do Docker, que naquele momento estava com o sistema de arquivos em modo somente leitura** — a troca de imagem pode não ter sido necessária e pode ser revertida |

**Armadilha confirmada, e ela custou tempo:** o observador de arquivos do Vite não
enxerga arquivo novo em `public/` nem alteração em `tokens.css` através do bind
mount do Windows. O sintoma é imagem que não aparece e token que chega vazio ao
navegador, sem erro nenhum. A recuperação é `docker compose restart frontend`.

**Dados de demonstração:** `backend/scripts/seed_demo.py` cria as cinco contas, as
quatro macas, três clientes e um orçamento pendente. Recusa-se a rodar fora de
`ENVIRONMENT=development` e é idempotente.

**Resultado esperado:** os três perfis entram no sistema, cadastram cliente,
solicitam e decidem agendamento com prevenção de conflito visível, e percorrem o
orçamento até a aprovação com percentual congelado.

**O que esta sprint não demonstra, e precisa ser dito na apresentação:** sinal,
pagamento, sessão executada e repasse. Das duas dores que justificam o sistema, a
fatia resolve inteira a de choque de horário e nenhuma parte da de saber quem recebe
quanto.

## Sprint M7.2 — Restante da interface do MVP

**Objetivo:** completar a interface com o que depende das sprints financeiras —
sessões, pagamentos, repasses, painéis por perfil e gestão de usuários.

**Dependências:** M4.4, M5, M6 e a M7.1, cuja casca e componentes base são
reaproveitados por inteiro.

**Riscos:** menores que os da M7 original, porque o padrão de tela, os componentes
base e a timeline já existem e foram exercitados.

**Resultado esperado:** os três perfis operam o ciclo completo pela interface, em
desktop e celular.

### Etapas

Dividida como a M3, a M4 e a M7.1, pelo mesmo motivo: a sprint acumula painel,
sessões, pagamentos, repasses e gestão de contas. Entregar em bloco único tira a
chance de conferir cada regra antes da seguinte.

**A M7.2.1 é antecipada e não espera a M6.** As demais etapas dependem de
repasse; o painel não depende. Ela pode sair antes ou em paralelo à M6, que é
backend.

| Etapa | Escopo | Situação |
|---|---|---|
| **M7.2.1** | ⚠️ Painel do gestor: o que está esperando decisão | ✅ Concluída em 30/09/2026 |
| M7.2.2 | Sessões e atendimentos | ✅ Concluída em 02/10/2026 |
| M7.2.3 | Pagamentos, sinal e devoluções | ✅ Concluída em 06/10/2026 |
| M7.2.4 | Repasses e demonstrativo do artista | ✅ Concluída em 02/10/2026, junto com a M6 |
| M7.2.5 | Painel do residente e do guest | ✅ Concluída em 06/10/2026 |
| M7.2.6 | Usuários e permissões | ✅ Concluída em 06/10/2026, com o acordo de percentual por artista (ADR-030) |

### Etapa M7.2.1 — Painel do gestor: o que está esperando decisão

**O problema, relatado pelo estúdio em 30/09/2026.** Hoje o gerente precisa abrir
o calendário para descobrir se existe solicitação de agendamento. Se não abrir,
não sabe; se abrir e não reparar, passa batido. Uma solicitação esquecida é um
horário que o cliente acha reservado e o estúdio não confirmou.

**A regra já previa isso, e não estava construída.** A RN-AGE-012 diz que "uma
nova solicitação **aparecerá no painel** de gerente e proprietário", e a seção
10.1 lista o conteúdo desse painel. O `HomeView` entregue na M7.1.1 é marcador de
lugar.

**Entrega:** a área de pendências no painel do gestor, com três origens, e um
contador na barra lateral visível em **toda** tela — é o contador que resolve a
dor, porque não exige estar na tela certa para saber que há algo esperando.

| Origem | Regra | Por que está aqui |
|---|---|---|
| Solicitações de agendamento | RN-AGE-005, RN-AGE-012 | A dor relatada |
| Pagamentos aguardando confirmação | RN-PAG-002, seção 10.1 | Desde a M5 o sinal não confirmado **trava a aprovação**; esquecê-lo trava a agenda |
| Orçamentos pendentes | RN-ORC-002, seção 10.1 | Não têm vencimento automático: ficam pendentes pelo tempo que for, sem nada cobrar decisão |

**Decisões tomadas com o responsável antes de começar:**

| Pergunta | Decisão |
|---|---|
| Onde encaixar | Etapa própria, antecipada. Não depende da M6 |
| O que aparece na área | Os três itens da seção 10.1, não só as solicitações |
| Atualização | A cada minuto, enquanto a tela estiver aberta. O gerente fica com o sistema aberto durante o expediente, e uma solicitação que chega às 14h05 não pode esperar ele navegar |
| Painel do residente | **Fora desta etapa.** A seção 10.2 o prevê e ele entra na M7.2.5; a dor relatada é do gestor |
| Notificação por e-mail | **Fora do MVP.** A RN-AGE-012 também a prevê, mas depende do `email_outbox` e do worker, declarados na sprint F2 |

**O que falta no backend, e é pequeno:**

| Ponto | O que falta |
|---|---|
| `GET /bookings` | Filtro por estado. Hoje só há janela de data, e pedir as pendentes sem data traria o histórico inteiro |
| Pagamentos aguardando confirmação | Só existe listagem por agendamento; falta a consulta do que está `REPORTED` no estúdio |
| `GET /quotes` | Devolve todos; falta o filtro por estado |

**Nenhuma migração.** Solicitação pendente é agendamento em `REQUESTED`; pagamento
aguardando é `payment` em `REPORTED`; orçamento pendente é `quote` em `PENDING`. A
tabela `notification` do modelo de dados é da sprint F2 e serve à caixa interna
com e-mail — não é o que esta etapa precisa.

**Critérios de aceite:**

- O contador aparece na barra lateral em toda tela, e some quando não há
  pendência.
- Gestor vê as três origens; residente e guest não veem a área nesta etapa.
- Cada item leva à tela onde a decisão é tomada, sem o gestor procurar.
- A área se atualiza sozinha a cada minuto, sem recarregar a página.
- Zero pendências mostra estado vazio explícito, não área em branco.

### Evidência da etapa M7.2.1 — 30/09/2026

**Os cinco critérios foram exercitados contra a aplicação rodando**, não só em
teste:

| Critério | Como foi conferido |
|---|---|
| Contador em toda tela | Com quatro pendências no painel, navegado para `/clients`: o contador continua na barra, com `aria-label` para leitor de tela |
| As três origens, ordenadas | Duas solicitações, um sinal informado e um orçamento pendente apareceram na mesma fila, do mais antigo para o mais recente |
| Atualização sozinha | Um sinal foi confirmado **pela API**, sem tocar na tela; o contador caiu de 4 para 3 em 20 segundos |
| Recorte por perfil | Entrando como residente: sem área, sem contador, e **zero requisições** em 15 segundos de observação — a fila do estúdio não é pedida por quem não decide |
| Celular | Em 375px o contador acompanha a navegação horizontal e cada item vira bloco |

**A ordem da fila é o ponto, e tem teste.** Do mais antigo para o mais recente,
qualquer que seja a origem. Ordenar pelo mais recente mostraria primeiro o que
acabou de chegar e empurraria para o fim o que está parado — o contrário do que a
área existe para fazer. É defeito que ninguém vê numa tela com três itens e que
custa uma solicitação esquecida numa com trinta.

**O ciclo de atualização mora no estado compartilhado, não na tela do painel.**
Se a tela carregasse, o contador só saberia de algo novo enquanto o gestor
estivesse no painel — justamente onde ele não está quando o problema acontece.

**Ligar e desligar o ciclo é decidido na casca**, que é onde se sabe quem entrou.
O residente não vê a fila do estúdio, e buscá-la para ele seria pedir ao servidor
um 403 por minuto.

**Código morto encontrado e removido:** `BookingRepository.list_pending` existia
desde a M3 e nunca foi chamado. Virou o filtro por estado, que serve às três
origens pelo mesmo desenho, em vez de um método próprio para cada pergunta.

**Alcance maior que o previsto, e é honesto dizer:** o `HomeView` mostrava
"Coming next" em três cartões cujas telas já existiam desde a M7.1. Foi corrigido
junto, porque a etapa reescreve essa tela de qualquer forma.

- ESLint e `vue-tsc` limpos; **97 testes** no frontend e **212** no backend;
  quatro verificações de convenção sem apontamento.

#### Correção, no mesmo dia — o item abria a agenda no dia errado

**O critério dizia "sem o gestor procurar", e a entrega não cumpria.** Clicar em
`Open` numa solicitação de outra semana levava à agenda do **dia de hoje**, e o
gestor tinha de achar a data. O item que existe para acabar com a procura
terminava nela.

| O que mudou | Por quê |
|---|---|
| `PendingWorkItem` ganha `query` | O item passa a dizer **para onde** ir, não só em que tela |
| `SchedulingView` lê `?day=` do endereço | E o devolve ao endereço ao trocar de dia, para que voltar pelo navegador não perca o dia aberto e o endereço possa ser copiado |
| `StudioClock.dayKey` e `today` | O dia no fuso do estúdio |

**Um segundo defeito apareceu no caminho, e era mais antigo.** A agenda calculava
o dia de hoje com `toISOString().slice(0, 10)` — isto é, em **UTC**. Às 00h30 de
Dublin no horário de verão, ela abria no dia anterior. Uma hora de largura, só de
madrugada e só em parte do ano: o tipo de defeito que ninguém reproduz quando é
relatado. Está desde a M7.1.3 e tem teste agora.

**O sinal segue o agendamento que ele trava**, quando esse agendamento está na
fila — que é o caso comum, porque um sinal por confirmar é justamente o que
impede aquela aprovação (RN-AGE-005). Não estando, o item vai à agenda sem data:
melhor abrir no dia de hoje do que num dia errado.

**Conferido na aplicação rodando**, com o Docker de volta: clicar em `Open` num
agendamento de 1 de outubro, estando o estúdio em 30 de setembro, abriu
`/schedule?day=2026-10-01` com o campo de data naquele dia e a reserva na grade.

**Dois acabamentos saíram dessa conferência:**

| O que apareceu | Decisão |
|---|---|
| Cada dia consultado viraria uma entrada de histórico | `replace` e não `push`: sair da agenda passaria a exigir um toque em voltar para cada dia que se olhou. Voltar leva de onde se veio — o painel, quando foi ele que trouxe |
| `?day=ontem` caía no dia de hoje, mas a barra continuava exibindo `ontem` | O endereço é acertado também na montagem. Um endereço que mente sobre o que está na tela leva outra pessoa ao mesmo engano quando é copiado |

### Evidência da etapa M7.2.2 — 02/10/2026

**As sessões têm tela.** O backend delas existia desde a M4.4 e nenhuma
interface as consumia; agora o ciclo do orçamento vai da aprovação à sessão
quitada sem sair do navegador.

A lista e as decisões moram **dentro do detalhe do orçamento**, e não em tela
própria: a sessão não existe fora dele, e uma rota separada obrigaria quem decide
a procurar o orçamento de que ela veio.

| Regra | Como a tela cumpre |
|---|---|
| **RN-ORC-005** | O artista marca realizada; o gestor confirma o recebimento. São dois botões, para gente diferente, e a tela esconde o que não cabe a quem olha |
| **RN-ORC-006** | A caixa "the session was interrupted" pede o valor cobrado, e o campo recusa valor **igual ou maior** que o previsto antes de enviar |
| **RN-ORC-005**, correções | Confirmar valor diferente do informado revela o campo de motivo e trava o botão enquanto ele estiver vazio |
| **RN-REP-006** | O modal mostra o percentual congelado da sessão, não o padrão vigente |

**Realizada aparece em tom de espera; só quitada aparece em verde.** Não é
estética: realizada ainda não entra em repasse, e pintá-la de positivo diria ao
artista que o trabalho terminou quando ele ainda não conta para o fechamento de
sexta.

**A tela diz o que o ato não faz.** "This records that the studio received the
money. It does not move anything — the payment happens outside the system." Quem
opera dinheiro não deve precisar deduzir se um botão movimenta caixa, e a
RN-PAG-006 reserva qualquer automação para uma versão futura.

**Exercitado contra a aplicação rodando:**

| Passo | Resultado |
|---|---|
| Aprovar o orçamento | Quatro sessões `SCHEDULED` de €250 apareceram no detalhe |
| Marcar parcial com €250 | Recusado na tela, com a explicação, e o botão travado |
| Marcar parcial com €100 | `PARTIALLY PERFORMED`, mostrando "€100.00 of €250.00 planned" |
| Confirmar €150 sem motivo | Botão travado; o campo de motivo apareceu sozinho |
| Confirmar €150 com motivo | `SETTLED`, e as ações do artista somem — desfazer confirmação é do gestor |

#### Defeito corrigido junto: a caixa "Approve straight away"

**A M5 fechou o portão do sinal e deixou um botão mentindo.** Criar agendamento
já aprovado passou a ser recusado onde há sinal a confirmar (ADR-027), e o
formulário continuava oferecendo a caixa — o gestor marcava e levava 403.

A tela agora **esconde o atalho** onde ele não vale e explica o caminho: criar a
solicitação, confirmar os €50, aprovar. Um botão que o servidor recusa ensina a
equipe a desconfiar dos próprios botões.

`DepositRequirement` decide isso por perfil, porque um agendamento novo nunca
nasce ligado a um orçamento — e a exceção da RN-GST-004 é do guest com cliente
próprio. **Erra para o lado de exigir** quando não reconhece o artista: não
oferecer o atalho custa um clique, oferecê-lo custa um 403.

- ESLint e `vue-tsc` limpos; **115 testes** no frontend; quatro verificações de
  convenção sem apontamento.

### Evidência da sprint M9 — Faturamento do estúdio — 07/10/2026

**A planilha do estúdio passou a existir dentro do sistema.** O controle mensal
que o estúdio mantinha à mão — cada atendimento com valor, percentual, comissão
do tatuador e parte da casa — é agora uma tela, com as mesmas colunas e na mesma
ordem.

#### O que o responsável pediu, e o que isso quis dizer

A conversa começou com "controle de **gastos**", e a planilha mostrava
faturamento. Perguntado, o responsável esclareceu: *"as despesas gastas são os
pagamentos que entram e que saem do estúdio"* e *"por enquanto teremos
detalhamento apenas de pagamentos e lucros com as tatuagens lançadas apenas"*.

Ou seja: **o gasto do estúdio é a comissão que ele paga ao tatuador, e o lucro é
a parte que fica.** Aluguel, material e contas ficam de fora por enquanto.

Isso eliminou a entidade nova inteira. Nenhuma migração: o relatório lê o que já
está gravado.

#### A prova de que o número é o mesmo

`tests/finance/test_revenue_report.py` reproduz **o controle real de outubro de
2026**, atendimento por atendimento, e confere os três totais:

| | Planilha do estúdio | Sistema |
|---|---|---|
| VALOR TOTAL TATTOOS | € 1.640,00 | € 1.640,00 |
| VALOR STUDIO | € 421,50 | € 421,50 |
| VALOR TOTAL TATUADORES | € 1.218,50 | € 1.218,50 |

É o teste mais valioso do módulo, e não por ser o maior: é a única prova de que
o sistema devolve o mesmo número que a planilha — que é a pergunta que o estúdio
vai fazer no primeiro mês de uso.

**A planilha também confirma o ADR-030 na prática:** três divisões convivendo no
mesmo mês, e o mesmo artista em mais de uma. YTALO aparece em 85/15 e em 50/50;
FARPA em 85/15 e em 70/30.

#### Decisões

| O que | Decisão |
|---|---|
| Onde mora | No **financeiro**, reusando `SettledSessions` e `PayoutShare` (ADR-031). Em `reporting` exigiria três portas novas para fazer uma leitura |
| O cálculo | O **mesmo** que paga o artista. Um cálculo próprio daria ao estúdio dois números para a mesma coisa, e um centavo de diferença não é conversa sobre software |
| Parte do estúdio | **O resto**, não uma segunda multiplicação: calculadas em separado, as duas falhariam a soma quando o arredondamento subisse |
| O sinal | **Não abate** (RN-PAG-005): já integra o preço e a base do repasse. A coluna "Depósito" é informativa, e está vazia em todas as linhas do controle de outubro |
| Comparação entre meses | **Tabela e não gráfico de barras.** O estúdio compara três números por mês; barras mostram um. A barra continua, deitada, ao lado do número |
| Mês vazio | Fica na tabela, zerado. Sumir com ele faria a comparação mentir sobre o tempo |
| Quem vê | Só gerente e proprietário (RN 10.4). O relatório mostra quanto **todos** receberam, e a RN-REP-004 limita o artista aos próprios valores |
| Escrita | **Não existe.** Um relatório que corrigisse dado ao passar seria um relatório que muda o passado |

#### Duas coisas que a verificação pegou

**`--border-thin` é shorthand de borda, não comprimento.** Eu o usei como altura
da barra e como medida de um utilitário de leitor de tela — CSS inválido nos
dois casos. A barra ganhou token próprio (`--chart-bar-height`), e o utilitário
foi substituído por um cabeçalho de coluna com nome, que a tabela merecia.

**A comparação entre meses nasceu como gráfico de barras clicáveis**, com um
`<button>` cru — violação da convenção, cuja única exceção documentada é o
`BookingBlock`. Refeita como tabela, o que resolveu a convenção **e** o
problema de fundo: barras mostram um número por mês, e o estúdio precisa de
três.

#### Exercitado contra a aplicação rodando

| Passo | Resultado |
|---|---|
| Abrir `/revenue` como proprietário | Outubro de 2026 com os três indicadores no topo |
| Conferir a tabela | `Ytalo €250 → €212,50 / €37,50`, `Farpa €130 → €110,50 / €19,50`, `Ytalo €120 → €60,00 / €60,00` — idêntico à planilha |
| Totais exibidos | € 1.790,00, porque o banco de desenvolvimento tinha **um atendimento residual de €150** de uma verificação anterior. € 1.640,00 + € 150,00, e as três colunas batem na soma |
| Comparação entre meses | Doze meses, com os vazios zerados e em ordem; outubro marcado como o mês aberto |

**Pendência que precisa de decisão:** o responsável pediu que "os valores e
porcentagens cobradas possam ser alterados". Para trabalho **futuro** isso já
existe (ADR-030 e RN-CLI-003). Alterar atendimento **já quitado** contraria a
RN-REP-006 e a RN-PAG-007, e está registrada no ADR-031 como pendente.

**Verificação:**

- Nenhuma migração: o relatório não cria tabela.
- Ruff limpo; **279 testes** no backend, sendo 21 novos.
- ESLint e `vue-tsc` limpos; **189 testes** no frontend, sendo 13 novos.
- As quatro verificações de convenção sem apontamento.

### Evidência da etapa M7.2.5 — 06/10/2026

**A tela de entrada deixou de ser decorativa para metade da equipe.** O gestor
tinha a fila do que espera decisão desde a M7.2.1; o artista abria o mesmo
endereço e via uma saudação, um banner e três atalhos.

O painel responde às três perguntas que o artista faz ao entrar: **o que tenho
hoje, o que estou esperando o estúdio decidir, e quanto entrou no último
fechamento.**

| Regra | Como a tela cumpre |
|---|---|
| **Seção 10.2** | Agenda própria do dia, solicitações próprias pendentes e orçamentos próprios por aprovar |
| **Seção 10.3** | O guest vê o mesmo sem orçamentos (RN-ORC-001) e sem clientes (RN-GST-004) — os cartões somem, em vez de mostrarem zero |
| **RN-REP-004** | O repasse exibido é o do artista, porque é só isso que o servidor devolve |
| **RN-CLI-004** | O nome do cliente encaminhado aparece **dentro do agendamento**, buscado à parte |
| **Seção 10.1** | O proprietário que tatua vê a fila **e** o próprio dia: a alçada administrativa não o tira da maca |

**O recorte é todo do backend.** `ListBookings` já devolve ao artista apenas a
própria agenda, a RN-REP-004 faz o mesmo com o repasse e a RN-CLI-004 com o
cliente. A tela não refiltra nada — duas versões das mesmas regras divergiriam,
e a do navegador seria a que ficaria para trás.

#### O que a regra pede e **não** foi inventado

| Pedido | Situação |
|---|---|
| **Repasse semanal previsto** (10.2) | Não existe. O repasse só nasce no fechamento de sexta às 20h (RN-REP-004), e um número calculado no navegador para a semana em curso seria o sistema dizendo ao artista quanto ele vai receber sem que ninguém tenha fechado nada. O cartão mostra o **último fechado** e o rótulo diz exatamente isso |
| **Pós-vendas próprios** (10.2) | Fase 2 — o módulo não existe |
| **Semanas pagas e validade do acesso** (10.3) | Depende da tabela `guest_week`, que é da sprint F1 |

#### Um defeito encontrado durante a verificação

O painel do residente mostrava **"Client"** no horário das 11h, em vez do nome.
Não era defeito de código: `GET /clients` devolve ao artista só os clientes que
ele cadastrou, e corretamente — lá a regra é o cadastro completo.

Mas a RN-CLI-004 é explícita na outra metade: *"o artista Y verá apenas nome,
telefone e Instagram **dentro do próprio agendamento**"*. A agenda dele estava
dizendo que alguém vem às 11h sem dizer quem.

Os nomes que faltam passam a ser buscados um a um por `GET /clients/{id}`, que
já devolve a projeção reduzida a qualquer artista. Poucos por dia, e só os que
faltam. O gatilho para levar essa junção ao servidor é volume, não estética.

#### Exercitado contra a aplicação rodando

| Perfil | Resultado |
|---|---|
| Residente | "1 booking today", 11:00–13:00 com **Niamh O'Sullivan** pelo nome; cartões de solicitações, orçamentos e último repasse |
| Residente, sem fechamento | "Last payout —", com "nothing closed yet — a week closes every Friday at 20:00" em vez de um zero que pareceria saldo |
| Guest | Mesmo painel **sem o cartão de orçamentos**, e sem Clients e Quotes na navegação |
| Guest, dia vazio | "Nothing on the bench today", em vez de lista vazia sem explicação |

**Verificação:**

- ESLint e `vue-tsc` limpos; **176 testes** no frontend, sendo 10 novos.
- As quatro verificações de convenção do frontend sem apontamento.
- Nenhuma alteração no backend: todos os recortes já existiam.

### Evidência da etapa M7.2.3 — 06/10/2026

**O sinal era a última peça que faltava para o ciclo se percorrer inteiro pela
interface.** O backend existia desde a M5 e nenhuma tela o consumia: o gestor
via no painel que havia um pagamento esperando, e precisava da API para fazer
qualquer coisa a respeito.

#### Onde cada coisa ficou, e por quê

Um recebimento pertence **ou** ao agendamento **ou** à sessão, nunca a nenhum
dos dois: o sinal confirma o horário reservado (RN-PAG-001), o saldo quita a
sessão (RN-PAG-008). Isso decidiu o desenho sozinho.

| Peça | Onde | Por quê |
|---|---|---|
| **Lançar** o sinal | Dentro do agendamento, no modal de decisão | É onde a origem já é conhecida. Numa tela separada o gestor teria de procurar o agendamento numa lista para dizer de onde veio o dinheiro |
| **Confirmar e recusar** | Nos dois lugares | A pergunta aparece nos dois: no agendamento é o que destrava a aprovação; na fila é o que está parado |
| **Devolver** | Tela de pagamentos | Não acompanha decisão de horário: devolve-se depois, e às vezes muito depois |
| **Histórico** | Tela de pagamentos, por estado | Seis anos de registro financeiro (RN-CLI-007) não cabem numa lista para o navegador peneirar |

#### O defeito que isto fecha

Até aqui o botão de aprovar devolvia **403** quando não havia recebimento
confirmado, e nada na tela dizia o quê. A RN-AGE-005 estava sendo cumprida pelo
servidor e comunicada por um código de erro.

Agora o painel do sinal fica no mesmo modal, acima dos botões, e diz em que pé
está: nada recebido, recebido e não conferido, ou confirmado. **Informado não
basta** — é exatamente a diferença que o 403 estava tentando explicar sozinho.

O painel entra por `slot`, e não por `props`: o `BookingDecision` decide sobre
horário e continua sem conhecer pagamento. Quem monta é a tela, que é quem fala
com a API.

#### Decisões de tela

| O que | Decisão |
|---|---|
| Valor do sinal | **Não é campo.** A RN-PAG-001 diz €50, e um campo aberto convidaria a digitar outro valor — que o estúdio descobriria no fechamento de sexta. Aparece como fato. O campo só existe no pagamento integral antecipado (RN-PAG-004), livre por definição |
| Recusado, devolvido e estornado | **Sem botão nenhum.** A RN-PAG-007 proíbe o retorno, e um botão que o servidor recusa ensina a equipe a desconfiar dos próprios botões |
| `REFUNDED` | **Neutro, não vermelho.** Devolver é o desfecho correto quando o estúdio recusa a solicitação (RN-PAG-003). Vermelho ali ensinaria a tratar o certo como erro — e aí o vermelho da recusa deixaria de significar alguma coisa |
| `REPORTED` | **Alerta, não cinza.** É a única coisa desta tela que trava outra |
| Sinal retido | Mostrado como tal. Um sinal retido continua `CONFIRMED` (RN-AGE-009); quem lesse só o estado procuraria a devolução que nunca houve |
| Decidir sobre o sinal | **Não fecha o agendamento.** Lançar, confirmar e aprovar é uma sequência só; fechar o modal a cada passo mandaria o gestor procurar o mesmo horário três vezes |

#### Dois textos que tinham apodrecido

**A fila do painel levava o sinal para a agenda.** Era o mais perto que existia
de um lugar onde resolver, porque esta tela não existia — mas lá não havia botão
nenhum para confirmar recebimento, e o gestor chegava sem o que fazer. Passa a
levar à tela que decide, e o teste que guardava o destino antigo foi reescrito
dizendo por que mudou.

**A frase da aprovação dizia que o sinal não era registrado no sistema** e
mandava confirmá-lo por fora. Verdade até esta etapa, e falsa a partir dela —
e agora contradizia o painel logo acima, no mesmo modal. Um texto que contradiz
o que está na tela ao lado é pior do que texto nenhum: ensina a não ler nenhum
dos dois. Corrigido, e o `BookingConsequence` **ganhou o teste que não tinha** —
é uma classe que guarda o que cada decisão faz com o dinheiro, e foi o texto
dela que apodreceu em silêncio.

#### Exercitado contra a aplicação rodando

| Passo | Resultado |
|---|---|
| Criar solicitação e abri-la | Painel do sinal: "Nothing received for this booking yet. It cannot be approved until a payment is confirmed." |
| Lançar o sinal | €50 fixo, sem campo de valor; modal continuou aberto |
| Logo após o lançamento | `AWAITING CONFIRMATION`, com "Reported, not confirmed — approval stays blocked until then" |
| Confirmar o recebimento | `CONFIRMED`, sem fechar o agendamento |
| Aprovar | Aceito — **o mesmo botão que devolvia 403** |
| `/payments` com "Awaiting confirmation" | Vazio, porque a fila tinha acabado de ser resolvida |
| Filtro "Confirmed" | O sinal, com "Record refund" como única ação — confirmar e recusar somem, como manda a transição |
| Registrar devolução de €50 em dinheiro | Aceito; a forma da devolução difere da original, como a RN-PAG-009 prevê |
| Filtro "Refunded" | O lançamento continua lá, agora `REFUNDED` e **sem ação nenhuma**. Nada foi apagado |

> O banco de desenvolvimento ficou com esse agendamento aprovado e o sinal dele
> devolvido — combinação que a operação não produziria. É resíduo da
> verificação, e some no próximo `seed_demo`.

**Armadilha reencontrada:** o Vite dentro do container serviu o módulo antigo
duas vezes, e na segunda eu só percebi porque fui conferir o texto corrigido na
aplicação em vez de confiar no arquivo em disco. `docker compose restart
frontend` resolve, e é o que a seção 5 da `CLAUDE.md` já registra.

**Verificação:**

- ESLint e `vue-tsc` limpos; **166 testes** no frontend, sendo 25 novos.
- As quatro verificações de convenção do frontend sem apontamento.
- Nenhuma alteração no backend: a API de pagamentos estava pronta desde a M5.

### Evidência da etapa M7.2.6 — 06/10/2026

**O gestor passa a administrar contas e acordos pela tela.** Até aqui criar
conta, bloquear e reativar só existiam na API, e o percentual do artista não
existia em lugar nenhum: eram dois números fixos no código.

#### O que a planilha do estúdio mostrou, e o código não previa

A planilha de controle do mês traz **três divisões convivendo** — 85/15, 70/30 e
50/50 — e o mesmo artista aparecendo em mais de uma. A RN-REP-001 e a RN-REP-002
definem duas; a terceira não estava em lugar nenhum da documentação.

**Isto foi perguntado, não suposto.** A decisão do responsável foi que o
percentual mora **no artista e no atendimento**: um acordo padrão por pessoa, e
a correção pontual que a RN-CLI-003 já dava ao gestor na aprovação do orçamento.
É o que explica o mesmo artista em duas divisões no mesmo mês.

| Decisão | Onde ficou |
|---|---|
| O percentual vira dado e deixa de ser constante | `user_account.default_artist_percentage`, migração `0010` |
| Nulo significa "siga a regra da origem" | Os artistas existentes continuam em 70/30 e 50/50 sem ninguém preencher nada |
| A ordem de precedência | Correção do atendimento, depois acordo do artista, depois regra da origem |
| Orçamentos não passam a conhecer contas | Porta `ArtistTerms` no desenho do ADR-028 |

**A regra que mais importa é a que não mudou.** Alterar o acordo **não alcança
trabalho já aprovado** (RN-REP-006), e a garantia não está no caso de uso que
altera: está na cópia que o orçamento congelou na aprovação. É o teste central
do arquivo, e a tela repete o aviso para quem renegocia, porque sem ele o gestor
esperaria ver o repasse da semana mudar e abriria um chamado quando não mudasse.

#### A tela

| Regra | Como a tela cumpre |
|---|---|
| **RN 2.2** | Os papéis oferecidos vêm da alçada de quem cria: o gerente não cria gerente nem proprietário |
| **RN 2.3** | "Also tattoos" só aparece para gestão; residente e guest tatuam por definição |
| **RN 2.5** | Bloquear exige motivo, e o botão fica travado sem ele. O texto diz o que o bloqueio **não** faz: não apaga histórico e não cancela agendamento futuro |
| **RN 2.5** | Ninguém se bloqueia: quem o fizesse perderia a sessão no mesmo instante, sem volta |
| **RN-CLI-003** | Só gestão altera o acordo, e a auditoria guarda o valor anterior |
| **Banco** | Artista sem nome de artista o banco recusa; o formulário exige antes, em vez de deixar o gestor descobrir por um 422 depois de sete campos |

**Conta bloqueada aparece na lista.** Escondê-la esconderia justamente o botão
que devolve o acesso a ela — e não há exclusão de conta, de propósito: apagar
quem assinou um atendimento apagaria o atendimento.

**Acordo ausente aparece como "By origin", nunca como 0%.** Nulo não é zero: a
regra depende do atendimento, então não existe um número único a mostrar, e
escrever zero diria ao artista que ele trabalha de graça. A frase é explicada
uma vez, abaixo do título, em vez de repetida em cada cartão.

#### Exercitado contra a aplicação rodando

| Passo | Resultado |
|---|---|
| Abrir `/accounts` como proprietário | 14 contas, com papel, estado, contato e acordo |
| Definir 85% para um artista | Cartão passou a exibir `85%`; a lista recarregou antes de o modal fechar |
| Reabrir e esvaziar o campo | Botão virou "End agreement"; o artista voltou a "By origin" |
| Cartão da própria conta | Sem "Block" — ninguém se bloqueia |
| Conta de gerente que não tatua | Sem "Share" e sem linha de acordo |
| Trocar o papel para residente no formulário | "Artist name" ganhou obrigatoriedade e a caixa "Also tattoos" sumiu |

#### Seed com a equipe real

`seed_demo.py` passa a trazer os nove artistas do estúdio pelos nomes que ele
usa. **Duas coisas ficaram em branco de propósito**, e as duas são decisão do
estúdio na tela nova: o perfil de cada um — nada na documentação diz quem é
guest, e chutar colocaria alguém fora da exigência de sinal da RN-GST-004 — e o
percentual, porque a planilha mostra acordos de 85% sem dizer de quem, e
escrever o acordo errado de alguém é pior do que não escrever nenhum.

Junto saiu um defeito de documentação: o comando de execução registrado no
próprio arquivo não funcionava, por faltarem `PYTHONPATH` e a senha de
demonstração. Corrigido no cabeçalho.

**Pendência que não é do código:** a RN-REP-001 e a RN-REP-002 continuam
descrevendo dois percentuais. A decisão de 06/10/2026 as estende, e **cabe ao
responsável atualizar o texto** — o documento de regras de negócio não é
alterado por quem implementa.

**Verificação:**

- Migração `0010` aplicada; Ruff limpo; **258 testes** no backend, sendo 10 do
  acordo de percentual.
- ESLint e `vue-tsc` limpos; **139 testes** no frontend, sendo 24 novos.
- As três verificações de convenção do frontend sem apontamento. A segunda delas
  **acusou uma violação real durante a entrega**: o modal de conta nova importava
  um tipo de `shared/api`. Corrigido na raiz — o que o componente emite passou a
  ser tipo próprio, e quem traduz para o corpo da requisição é a tela.

### Evidência da sprint M6 — 02/10/2026

**O último elo do MVP fechou.** O estúdio deixa de calcular fora do sistema
quanto paga a cada artista.

| Regra | Como o backend cumpre |
|---|---|
| **RN-REP-003** | Cada sessão quitada vira um item, com o valor recebido e o percentual congelado dela |
| **RN-REP-004** | Semana de sexta 20h a sexta 20h no fuso do estúdio; artista vê só os próprios valores, gestor vê todos; a confirmação registra data, hora, valor e responsável |
| **RN-REP-005** | `payout_adjustment` com valor negativo, vinculado ao pagamento devolvido e único por pagamento |
| **RN-REP-006** | O percentual vem congelado da sessão, não do padrão vigente, e é copiado para o item |
| **RN-REP-007** | Cálculo por sessão arredondado a duas casas; o demonstrativo exibe sessões, valor recebido, percentual, ajustes e líquido; três estados |

**Decisões tomadas com o responsável antes de qualquer código:**

| Pergunta | Decisão |
|---|---|
| Quem dispara o cálculo? | **Sob demanda.** A regra diz "depois do fechamento", não *quando*, e ninguém consulta repasse às 20h de sexta. Resultado idêntico ao de um agendador e **nenhum container a mais** na M8 — o worker segue para a Fase 2 (ADR-008) |
| O que o sistema faz com o dinheiro? | **Só registra a confirmação.** O gestor transfere por fora; o sistema nunca move dinheiro sozinho, mesma linha do ADR-029 |

**O risco declarado da sprint era a fronteira do horário de verão, e está
coberto.** A semana que atravessa a virada tem **169 horas**, não 168: subtrair
sete dias em UTC deixaria uma hora de fora, e nela caberia um pagamento
confirmado na madrugada de sábado. O `PayoutWeek` calcula no fuso do estúdio e
tem teste nas duas estações.

**Duas decisões de cálculo que decidem dinheiro:**

| Decisão | Por quê |
|---|---|
| Arredonda **por sessão**, não no total | A RN-REP-007 é literal. Somar antes e arredondar no fim dá outro número, e a diferença sai do bolso do artista. Tem teste com os dois caminhos lado a lado |
| Meio centavo arredonda **para cima** | `ROUND_HALF_UP`, não o padrão do Python. O arredondamento bancário é mais justo estatisticamente e contabilmente surpreendente — ninguém quer explicar por que €0,125 virou €0,12 numa semana e €0,13 na outra |

**Um defeito encontrado pelo próprio teste.** A idempotência estava no filtro de
sessões, não no repasse: fechar duas vezes devolvia **lista vazia**, e o gestor
abriria a tela de novo e veria a semana sem repasse nenhum, como se o fechamento
tivesse sumido. Agora quem já tem repasse na semana é devolvido como está, e só
quem não tem é calculado.

**A terceira porta entre módulos**, e desta vez quem pergunta é o financeiro: o
repasse declara `SettledSessions` e o módulo de orçamentos a implementa
(ADR-028). Consultar a tabela de sessões direto faria o cálculo do repasse
depender do desenho interno daquele módulo.

**A tela saiu junto**, embora fosse a etapa M7.2.4: o backend sozinho não
demonstra repasse, e a dependência dela era exatamente esta sprint. `/payouts`
mostra a lista com o recorte do servidor, o demonstrativo em modal e a
confirmação da transferência.

**Pendência mantida, e é honesto dizer:** a costura em que
`ConfirmSessionPayment` passa a se apoiar num pagamento `BALANCE` confirmado
continua aberta. O repasse lê a sessão, então quando ela entrar nada na M6 muda —
fazê-la aqui misturaria dois assuntos numa entrega só.

- Ruff limpo; **248 testes** no backend e **105** no frontend; uma classe por
  arquivo e as quatro verificações do frontend sem apontamento.

### Renomeação de `booth` para `bench` — 30/09/2026

**O estúdio corrigiu o termo em inglês.** A unidade reservável é uma **bench**;
`booth` descreve uma cabine fechada, que não é o que existe no salão. O nome em
português nas regras de negócio continua **maca**, e o documento `01` não foi
tocado.

**Renomeado no banco, e não só rotulado na tela.** Nome errado em tabela
sobrevive a qualquer correção de interface: reaparece em cada consulta, cada log
e cada migração futura, e a próxima pessoa a ler o esquema aprende o termo
errado. A migração `0007` renomeia tabela, a coluna `booking.bench_id`, os
índices e as duas restrições.

**As restrições precisavam ir junto, e isso não é cosmético.** O
`BookingRepository` traduz a violação de `booking_bench_no_overlap` no `scope`
que alimenta o modal da RN-AGE-007 — o nome é contrato entre o banco e a
aplicação. Deixá-lo para trás faria o código procurar um nome que o banco não usa
mais, e o conflito voltaria como erro genérico: a agenda funcionando em tudo,
menos na regra que ela existe para garantir.

**A migração `0004` não foi editada.** Ela cria `booth` porque foi isso que ela
criou; reescrevê-la faria um banco novo nascer com `bench` e a `0007` falhar ao
renomear o que já teria outro nome. Migração aplicada é histórico, não rascunho.

| Onde | O que mudou |
|---|---|
| Banco | Tabela, coluna, três índices e duas restrições |
| Backend | 5 arquivos renomeados, `BenchRepository`, `CreateBench`, rota `/benches`, e o `scope` do conflito passou de `booth` para `bench` |
| Frontend | `Bench`, `BenchTimeline.vue`, `benchId`, e o rótulo "Bench 1" na tela |
| Documentação | `05`, `06`, `09` e `10`. O `01` não foi tocado: lá o termo é maca |

### Cliente guarda quem o trouxe — 01/10/2026

**A RN-CLI-002 decide dinheiro a partir de uma pergunta que o sistema não sabia
responder:** *"o cliente retornou ao mesmo artista **que o trouxe**?"*. O que
existia era `registered_by_artist_id`, e ele responde outra coisa — quem digitou
o cadastro. Coincidem quando o artista cadastra o próprio cliente e divergem
justamente no caso que importa: a RN-GST-005 manda o **gestor** cadastrar o
cliente indicado pelo estúdio, e ali o campo antigo aponta para quem não trouxe
ninguém.

**Decisões tomadas com o responsável antes de qualquer código:**

| Pergunta | Decisão |
|---|---|
| O campo novo substitui `registered_by_artist_id`? | **Convivem.** A RN-CLI-004 amarra a visibilidade da ficha a quem cadastrou; trocar um pelo outro deixaria o cliente de indicação do estúdio sem dono, e nenhum artista veria a ficha dele |
| Ele decide a origem do orçamento? | **Sugere.** A RN-CLI-002 diz que a origem é determinada em cada atendimento, e a RN-CLI-003 dá a correção ao gestor. O formulário abre preenchido; quem orça confirma ou troca |

**Nulo significa indicação do estúdio** — a ausência é o dado, e não a falta
dele. Os cadastros anteriores à migração `0008` ficam nulos, e isso é correto:
gravar quem cadastrou como se fosse quem trouxe inventaria uma afirmação que
ninguém fez, e ela sairia do banco como verdade no primeiro repasse.

**Criar e editar ganharam contratos separados**, e não é preciosismo. Na criação
`source` tem padrão, porque todo cliente vem de algum lugar; na edição o padrão
seria desastre, porque alterar a origem é do gestor (RN-CLI-003) e o artista
corrigindo um telefone levaria 403 por causa de um campo que nem viu. O mesmo
`None` significaria "use o padrão" num caso e "não toque" no outro.

**A sugestão erra para o lado seguro.** Sem saber quem trouxe, sugere indicação
do estúdio: paga 50% ao artista, e errar assim significa pagar a menos até
alguém conferir, em vez de pagar a mais e precisar cobrar de volta.

- Ruff limpo; **221 testes** no backend e **101** no frontend; uma classe por
  arquivo e as quatro verificações do frontend sem apontamento.

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

### O que vai ao ar: contagem de containers

A topologia detalhada está na seção 8 de `04_ARQUITETURA_TECNICA.md`. O resumo que
esta sprint precisa:

| Container | Papel |
|---|---|
| `caddy` | TLS automático, proxy de `/api/v1` e **entrega do frontend compilado** |
| `api` | FastAPI |
| `postgres` | Banco com volume persistente |

**Três no cenário mínimo.** O container `frontend` do `compose.yaml` **não vai para
produção**: o Vue é compilado em arquivos estáticos que o Caddy serve. Quem montar o
`compose.production.yaml` copiando o de desenvolvimento vai subir um servidor de
desenvolvimento em produção — é o erro previsível aqui.

### Três decisões abertas que mudam a contagem

| Decisão | Opções | Recomendação registrada |
|---|---|---|
| Armazenamento de arquivos | Manter o volume local do ADR-024 ou trocar por provedor gerenciado compatível com S3 | **Gerenciado**, se o custo couber: os arquivos passam a sobreviver à perda do VPS e a cópia de segurança volta a ter um alvo só. A porta `ObjectStorage` existe para que a troca não alcance caso de uso nenhum. **Nenhuma das duas opções acrescenta container** |
| Worker/agendador | Necessário no MVP apenas se o fechamento da M6 for agendado | **Cálculo sob demanda**, conforme a seção da M6. Decisão do responsável |
| Rotina de backup | Container próprio (1) ou `cron` no host chamando `pg_dump` (0) | Nenhuma preferência registrada. As duas atendem ao requisito, que é cópia cifrada diária **fora do servidor** com restauração testada |

**Enquanto o armazenamento for o volume local, o backup tem dois alvos**, não um: o
banco e o diretório de arquivos. Uma cópia que leva só o `pg_dump` deixaria as
referências dos orçamentos, as fotos de cicatrização e os comprovantes para trás, e a
perda apareceria justamente no dia em que o servidor se fosse. **O teste de
restauração precisa cobrir os dois alvos**, não só o banco.

Ao fim da Fase 2 a contagem vai a **4 a 6 containers**, quando o worker deixa de ser
opcional por causa da lista diária das 08h e do outbox (ADR-007, ADR-008).

### Pendências de produção que não são contagem de container

- **Gestão de segredos.** Hoje há `.env` não versionado em desenvolvimento; produção
  precisa de definição própria. Não decidido.
- **RPO e RTO.** Proposta em `04_ARQUITETURA_TECNICA.md`: perda máxima de 24 horas e
  recuperação em até 4 horas. Aguarda confirmação do responsável.
- **Retenção de cópias por 30 dias e teste de restauração trimestral**, já aprovados
  em `03_REQUISITOS_NAO_FUNCIONAIS.md` seção 4.

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
