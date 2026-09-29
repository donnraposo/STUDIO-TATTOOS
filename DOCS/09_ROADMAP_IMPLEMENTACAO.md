# Roadmap de Implementação

**Status:** Implementação autorizada. Estratégia de MVP definida em 24/09/2026.
**Última atualização:** 26/09/2026

## Onde o projeto está agora

**Concluído:** sprint 01, M1, M2, M3 e M7.1 — a fatia vertical de interface.
**Pausado:** M4 — orçamentos e sessões, com M4.1 a M4.3 concluídas.
**Próxima:** M4.4 — sessões. A M7.1 fechou em 29/09/2026 e a M4 volta a andar.
**Progresso do MVP:** 4 de 8 sprints em número; o backend está adiante disso e o
frontend, bem atrás.

| O que existe | Detalhe |
|---|---|
| Módulos com código | `health`, `identity`, `clients`, `scheduling`, `quotes`, `reporting` (só auditoria) |
| Migrações aplicadas | `0001` extensões, `0002` identidade e auditoria, `0003` clientes, `0004` agenda, `0005` orçamentos e sessões |
| Endpoints | `/health`, `/ready`, `/auth/*`, `/users/*`, `/clients/*`, `/booths`, `/bookings/*`, `/quotes/*` incluindo as imagens de referência |
| Containers | Três: `postgres`, `api`, `frontend`. Arquivos enviados ficam no volume nomeado `object_storage` (ADR-024) |
| Testes | 145 no backend e 47 no frontend, todos aprovados |
| Frontend | Apenas a tela de status da sprint 01 e os tokens de design |

> **Leitura honesta do avanço.** O backend cobre identidade, clientes, agenda —
> inclusive a prevenção de conflito, que era o risco técnico central — e o
> orçamento. **Falta todo o dinheiro:** sinal, pagamento e repasse. Enquanto essa
> metade não existir, o estúdio continua com controle paralelo, porque o fio
> condutor do MVP não fecha.
>
> O frontend, por outro lado, ainda é quase tudo: existem os tokens de design e uma
> tela de status. A M7.1 começa a mudar isso, e a demonstração que ela permite
> cobre uma das duas dores do estúdio, não as duas.

### Pendências de costura entre sprints

Casos de uso já entregues que dependem de um módulo futuro. Cada ponto está marcado
no código e **precisa ser fechado na sprint indicada** — sem esta lista, a sprint
seguinte fecha sem saber tudo o que tinha de fechar.

| Ponto no código | O que falta | Fecha em |
|---|---|---|
| `ApproveBooking._deposit_is_confirmed` | Consultar o sinal confirmado; hoje devolve verdadeiro fixo (RN-AGE-005) | M5 |
| `CancelBooking`, `RescheduleBooking` | Destino do sinal em cancelamento, não comparecimento e remarcação fora de 24h; hoje só o estado é gravado | M5 |

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
| M4 | Orçamentos e sessões | Backend | ⏸️ **Pausada em 3 de 4 etapas.** ⬅️ Retomada agora, na M4.4 |
| **M7.1** | ⚠️ Fatia vertical de interface | Frontend | ✅ Concluída em 29/09/2026 |
| M5 | Pagamentos e sinal | Backend | Não iniciada |
| M6 | Repasses e fechamento semanal | Backend | Não iniciada |
| M7.2 | Restante da interface do MVP | Frontend | Não iniciada |
| M8 | Implantação mínima | Infra | Não iniciada |

**O detalhamento do frontend está em
[`10_ROADMAP_FRONTEND.md`](10_ROADMAP_FRONTEND.md):** telas, componentes, ordem das
etapas e critérios de aceite. O andamento continua sendo registrado **aqui**, para
não haver duas versões do status.

**Por que a M4 ficou pausada e não concluída.** Faltam as sessões, da etapa M4.4.
Marcar a sprint como concluída seria a mentira mais fácil de contar e a mais cara de
descobrir depois. **A M7.1 fechou em 29/09/2026 e a M4.4 é a próxima etapa do
projeto** — a pausa durou de 27/09 a 29/09/2026.

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

- Endpoints: `GET/POST /booths`, `GET/POST /bookings`, e as ações
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

**Dependência declarada:** a RN-AGE-005 exige sinal confirmado para aprovar, e o
módulo de pagamentos é a sprint M5. A costura está pronta em
`ApproveBooking._deposit_is_confirmed`, que hoje devolve verdadeiro. Travar agora
impediria qualquer uso da agenda. O mesmo vale para o destino do sinal em
cancelamento, não comparecimento e remarcação fora de 24h: o estado fica
registrado aqui, e o efeito financeiro é executado na M5.

### Evidência da etapa M3.1 — 26/09/2026

**O maior risco técnico do projeto foi retirado.** As duas restrições estão no
banco e comprovadas por 8 testes, entre eles a corrida com transações paralelas.

```sql
-- Maca: apenas aprovado bloqueia (RN-AGE-004, RN-AGE-007)
EXCLUDE USING gist (booth_id WITH =, period WITH &&) WHERE (status = 'APPROVED')

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
| M4.4 | Sessões: gerar do orçamento aprovado, marcar realizada, sessão parcial, confirmar recebimento | ⬅️ Próxima |

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
Fase 2 realmente exige. **Ainda não decidido pelo responsável.**

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
