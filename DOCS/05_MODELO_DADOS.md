# Modelo de Dados

**Status:** Proposta para aprovação — nenhuma migração foi criada.
**Última atualização:** 24/09/2026
**Banco:** PostgreSQL

> Este documento traduz as regras de `01_REGRAS_DE_NEGOCIO.md` em entidades,
> relacionamentos e restrições. Ele não autoriza implementação.

## 1. Princípios

1. **Chaves públicas em UUID.** Evita enumeração de registros em URLs e e-mails.
2. **Dinheiro em `NUMERIC(12,2)`.** Nunca ponto flutuante. Moeda única: euro.
3. **Tempo em `TIMESTAMPTZ`,** persistido em UTC. O fuso operacional
   `Europe/Dublin` é aplicado na borda, ao calcular semanas de guest, fechamento
   de sexta às 20h e a lista diária das 08h.
4. **Histórico financeiro é imutável.** Pagamento nunca é apagado ou editado;
   correções entram como lançamento de ajuste vinculado (RN-PAG-007).
5. **Integridade de agenda no banco, não só na aplicação.** As duas regras de não
   sobreposição são restrições do PostgreSQL, imunes a concorrência.
6. **Percentual congelado na aprovação** do orçamento (RN-REP-006).
7. **Estados são texto com `CHECK`, não `ENUM` nativo** (ADR-018). A garantia
   permanece no banco, mas acrescentar um estado nas próximas sprints passa a ser
   alteração de restrição, sem `ALTER TYPE`. O `StrEnum` em Python é a fonte dos
   valores válidos na aplicação.

## 2. Extensões necessárias

| Extensão | Uso |
|---|---|
| `btree_gist` | Permite combinar igualdade (`booth_id`, `artist_id`) com sobreposição de intervalo na mesma restrição `EXCLUDE` |
| `citext` | E-mail único sem diferenciar maiúsculas |

## 3. Identidade e acesso

### `user_account`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `email` | citext UNIQUE NOT NULL | Único no sistema |
| `password_hash` | text NOT NULL | Argon2id |
| `full_name` | text NOT NULL | |
| `artist_name` | text NULL | Obrigatório quando atua como tatuador |
| `phone` | text NOT NULL | |
| `role` | enum NOT NULL | `OWNER`, `MANAGER`, `RESIDENT`, `GUEST` |
| `acts_as_artist` | boolean NOT NULL | Proprietário/gerente que também tatua |
| `status` | enum NOT NULL | `PENDING_APPROVAL`, `ACTIVE`, `BLOCKED`, `REJECTED` |
| `requested_role` | enum NULL | Perfil pedido no autocadastro |
| `created_by` | uuid FK NULL | Nulo quando é autocadastro |
| `created_at` / `updated_at` | timestamptz | |

**Regras:**
- `CHECK (NOT (acts_as_artist OR role IN ('RESIDENT','GUEST')) OR artist_name IS NOT NULL)` — garante nome artístico de quem tatua.
- O último proprietário ativo não pode ser bloqueado (RN 2.5). Verificação em caso de uso transacional, não em constraint, por depender de contagem.

### `user_status_history`

`id`, `user_id`, `from_status`, `to_status`, `reason`, `note`, `actor_id`, `created_at`.
Atende autorização, rejeição, bloqueio e reativação com rastreabilidade.

### `user_session`

`id` (uuid, é o valor do cookie), `user_id`, `created_at`, `last_seen_at`,
`idle_expires_at`, `absolute_expires_at`, `revoked_at`, `ip`, `user_agent`.

Sessão vive no servidor (`03_REQUISITOS_NAO_FUNCIONAIS.md` §3). Bloqueio de conta e
troca de senha fazem `UPDATE ... SET revoked_at = now()` em todas as sessões do
usuário, revogando o acesso imediatamente.

### `password_reset_token`

`id`, `user_id`, `token_hash`, `expires_at`, `used_at`. Guarda apenas o hash.

## 4. Clientes

### `client`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `name` | text NOT NULL | |
| `phone` | text NOT NULL | |
| `instagram` | text NULL | |
| `registered_by_artist_id` | uuid FK NOT NULL | Define visibilidade (RN-CLI-004) |
| `merged_into_id` | uuid FK NULL | Autorreferência; união de duplicidades |
| `anonymized_at` | timestamptz NULL | RN-CLI-007 |
| `created_at` / `updated_at` | timestamptz | |

**Índices:** `phone` e `instagram` para o alerta de duplicidade (RN-CLI-005), que
avisa sem bloquear.

**Visibilidade:** residente vê ficha completa apenas onde
`registered_by_artist_id = ele`. Artista indicado vê somente nome, telefone e
Instagram, projeção feita na camada de aplicação a partir do agendamento.

**Exclusão:** proibida quando há histórico. A anonimização preenche
`anonymized_at` e limpa contato, preservando os registros financeiros.

## 5. Agenda

### `booth` (maca)

`id`, `number` (int UNIQUE), `label`, `active` (boolean), `created_at`.

### `studio_hours`

`weekday` (0–6) PK, `opens_at` (time), `closes_at` (time), `closed` (boolean).
Padrão: terça a domingo 10h–20h, segunda fechado.

### `schedule_exception`

`id`, `date`, `booth_id` (NULL = todas as macas), `opens_at`, `closes_at`,
`blocked` (boolean), `reason`, `actor_id`, `created_at`, `removed_at`.

Cobre abertura excepcional e bloqueio de maca ou do estúdio inteiro (RN-AGE-011).
Uma exceção prevalece sobre `studio_hours` na data afetada.

### `booking`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `client_id` | uuid FK NOT NULL | |
| `artist_id` | uuid FK NOT NULL | |
| `booth_id` | uuid FK NOT NULL | |
| `period` | tstzrange NOT NULL | Início e fim; sem blocos fixos |
| `status` | enum NOT NULL | `REQUESTED`, `APPROVED`, `REJECTED`, `DONE`, `CANCELLED`, `NO_SHOW` |
| `session_id` | uuid FK NULL | Liga à sessão do orçamento |
| `requested_at` | timestamptz NOT NULL | Ordena solicitações concorrentes |
| `decided_at` / `decided_by` | | |
| `rejection_reason` | enum NULL | `SLOT_TAKEN`, `STUDIO_CLOSED`, `RESCHEDULED` |
| `rejection_note` | text NULL | |

### 5.1 As duas restrições de não sobreposição

Este é o ponto crítico da integridade da agenda. São **dois recursos distintos com
semânticas diferentes**, e ambos precisam ser garantidos pelo banco.

**Maca — só agendamento aprovado bloqueia** (RN-AGE-004 e RN-AGE-007). Solicitações
pendentes de artistas diferentes podem concorrer pelo mesmo horário:

```sql
ALTER TABLE booking ADD CONSTRAINT booking_booth_no_overlap
EXCLUDE USING gist (booth_id WITH =, period WITH &&)
WHERE (status = 'APPROVED');
```

**Artista — pendente e aprovado bloqueiam** (RN-AGE-014). O mesmo artista não pode
ter sobreposição nem em macas diferentes:

```sql
ALTER TABLE booking ADD CONSTRAINT booking_artist_no_overlap
EXCLUDE USING gist (artist_id WITH =, period WITH &&)
WHERE (status IN ('REQUESTED', 'APPROVED'));
```

**Por que no banco e não apenas na aplicação:** duas requisições simultâneas podem
ambas consultar a agenda, ambas ver o horário livre e ambas gravar. A verificação em
código não impede essa corrida; a restrição `EXCLUDE` impede, porque a segunda
gravação falha na transação. A aplicação captura a violação e devolve o modal de
conflito exigido por RN-AGE-007, que não permite ignorar o conflito.

Rejeitados e cancelados saem das cláusulas `WHERE` e deixam de ocupar a agenda,
preservando o registro histórico (RN-AGE-014).

### `booking_history`

`id`, `booking_id`, `from_status`, `to_status`, `reason`, `note`, `actor_id`,
`created_at`. Registra aprovação, rejeição, remarcação, transferência e cancelamento.

## 6. Orçamentos e sessões

### `quote` (orçamento)

| Campo | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `client_id`, `artist_id` | uuid FK | |
| `origin` | enum NOT NULL | `ARTIST_OWN`, `STUDIO_REFERRAL` |
| `description`, `body_region`, `size_estimate` | text | |
| `total_value` | numeric(12,2) | |
| `planned_sessions` | int | |
| `planned_value_per_session` | numeric(12,2) | |
| `estimated_duration_minutes` | int | |
| `notes` | text | |
| `status` | enum NOT NULL | `PENDING`, `APPROVED`, `REJECTED` |
| `artist_percentage` | numeric(5,2) NULL | **Congelado na aprovação** (RN-REP-006) |
| `approved_at` / `approved_by` | | |
| `rejection_reason` / `rejection_note` | | |

Alterar um orçamento aprovado devolve `status` para `PENDING` e exige nova
aprovação (RN-ORC-003).

### `quote_reference_image`

`id`, `quote_id`, `object_key`, `uploaded_by`, `uploaded_at`.
Somente a chave privada do objeto; nunca URL pública.

### `session`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `quote_id` | uuid FK NOT NULL | |
| `sequence_number` | int NOT NULL | Ordem dentro do orçamento |
| `status` | enum NOT NULL | `SCHEDULED`, `DONE`, `PARTIALLY_DONE`, `PAID_OFF`, `CANCELLED`, `NO_SHOW` |
| `planned_value` | numeric(12,2) | |
| `charged_value` | numeric(12,2) NULL | Valor efetivo, pode diferir em sessão parcial |
| `performed_at` | timestamptz NULL | Data real, base do vencimento do pós-venda |
| `marked_done_by` | uuid NULL | Artista marca realizada |
| `confirmed_by` / `confirmed_at` | | Gestor confirma recebimento |
| `artist_percentage` | numeric(5,2) | Cópia do orçamento no momento da aprovação |

`UNIQUE (quote_id, sequence_number)`.

**Conclusão:** só entra em repasse quando realizada **e** integralmente quitada
(RN-ORC-005). Sessão parcial gera repasse apenas sobre o valor recebido
(RN-ORC-006).

## 7. Financeiro

### `payment`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `session_id` | uuid FK NULL | Nulo em taxa de guest |
| `guest_week_id` | uuid FK NULL | Nulo em pagamento de sessão |
| `client_id` | uuid FK NULL | |
| `amount` | numeric(12,2) NOT NULL | |
| `kind` | enum NOT NULL | `DEPOSIT` (sinal €50), `BALANCE`, `FULL_PREPAY`, `GUEST_WEEK` |
| `method` | enum NOT NULL | `BANK_TRANSFER`, `CASH`, `CARD` |
| `status` | enum NOT NULL | `REPORTED`, `CONFIRMED`, `REFUSED`, `REFUNDED`, `CHARGED_BACK` |
| `confirmed_at` / `confirmed_by` | | Só gerente/proprietário |
| `receipt_object_key` | text NULL | Comprovante privado |

`CHECK` garantindo exatamente uma origem: `session_id` ou `guest_week_id` preenchido.

**Imutabilidade:** sem `UPDATE` de valor. Correção entra como `payment_refund` ou
`payout_adjustment` vinculado (RN-PAG-007).

### `payment_refund`

`id`, `payment_id`, `amount`, `method`, `reason`, `note`, `receipt_object_key`,
`refunded_at`, `actor_id`. A forma de devolução pode diferir da original
(RN-PAG-009).

### `payout` (repasse semanal)

`id`, `artist_id`, `period_start`, `period_end`, `gross_total`,
`adjustments_total`, `net_total`, `status` (`CALCULATED`, `PAID`, `ADJUSTED`),
`paid_at`, `paid_by`, `receipt_object_key`, `created_at`.

`UNIQUE (artist_id, period_end)`. O `period_end` é a sexta às 20h `Europe/Dublin`
convertida para UTC (RN-REP-004).

### `payout_item`

`id`, `payout_id`, `session_id`, `received_amount`, `percentage`, `amount`.
O cálculo é por sessão, arredondado a duas casas (RN-REP-007).

### `payout_adjustment`

`id`, `payout_id`, `related_payment_id`, `amount` (negativo), `reason`, `actor_id`.
Devolução posterior a um repasse pago não altera o fechamento anterior: entra como
ajuste negativo no seguinte (RN-REP-005).

## 8. Guest

### `guest_week`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | uuid PK | |
| `guest_id` | uuid FK NOT NULL | |
| `week_start` | date NOT NULL | Sempre sábado |
| `week_end` | date NOT NULL | Sexta seguinte |
| `fee_amount` | numeric(12,2) NOT NULL | €600 |
| `status` | enum NOT NULL | `PENDING_PAYMENT`, `ACTIVE`, `REFUNDED`, `TRANSFERRED` |
| `transferred_to_week_id` | uuid FK NULL | |
| `reason`, `actor_id` | | Devolução ou transferência (RN-GST-006) |

`UNIQUE (guest_id, week_start)`.

**Acesso do guest:** derivado, não armazenado como flag. A conta está ativa quando
existe `guest_week` com `status = 'ACTIVE'` cobrindo a data corrente. Reserva só é
aceita se o `period` do agendamento cair dentro de uma semana ativa (RN-GST-007).
Derivar evita estado divergente quando a semana vence.

## 9. Pós-venda

### `aftercare`

`id`, `session_id` UNIQUE, `due_date`, `status` (`PENDING`, `COMPLETED`),
`result` (enum), `notes`, `completed_at`, `completed_by`, `created_at`.

`due_date` = `session.performed_at + 15 dias` (RN-POS-001).

**Atrasado é derivado**, não é estado persistido: `due_date < hoje AND status = 'PENDING'`.
Evita job noturno só para mudar rótulo.

**Resultados** (RN-POS-007): `NORMAL_HEALING`, `GUIDANCE_REINFORCED`,
`NEEDS_FOLLOW_UP`, `NEEDS_ARTIST_REVIEW`, `POSSIBLE_TOUCH_UP`, `NO_RESPONSE`,
`OTHER` (observação obrigatória).

### `aftercare_photo`

`id`, `aftercare_id`, `object_key`, `uploaded_by`, `uploaded_at`, `removed_at`,
`removed_by`. Remoção é lógica, preservando histórico (RN-POS-008).

### `aftercare_event`

`id`, `aftercare_id`, `action`, `reason`, `new_due_date`, `actor_id`, `created_at`.
Registra conclusão, reabertura e novo acompanhamento.

## 10. Notificações

### `notification`

`id`, `recipient_user_id`, `type`, `title`, `body`, `payload` jsonb, `read_at`,
`created_at`. Caixa interna do sistema.

### `email_outbox`

`id`, `to_email`, `subject`, `template`, `payload` jsonb, `status`
(`PENDING`, `SENT`, `FAILED`), `attempts`, `last_error`, `scheduled_for`,
`sent_at`, `idempotency_key` UNIQUE, `created_at`.

**Padrão outbox.** A transação de negócio grava a linha e termina. O worker lê com
`SELECT ... FOR UPDATE SKIP LOCKED` e envia. Assim uma falha de e-mail nunca altera
estado de agendamento ou pós-venda (`03_REQUISITOS_NAO_FUNCIONAIS.md` §5), e o
reinício de um container não perde envios. A `idempotency_key` impede duplicata na
repetição.

## 11. Auditoria

### `audit_log`

`id`, `actor_id`, `action`, `module`, `entity_type`, `entity_id`, `old_values`
jsonb, `new_values` jsonb, `reason`, `created_at`.

**Imutabilidade real:** gatilho `BEFORE UPDATE OR DELETE` levanta exceção para
qualquer role, inclusive a dona da tabela, somado a `REVOKE` para `PUBLIC`
(ADR-012). Não basta a aplicação "não oferecer" edição, nem basta o `REVOKE`: o
dono da tabela poderia conceder o privilégio de volta a si mesmo.

`TRUNCATE` continua funcionando, por ser DDL e não disparar gatilhos de linha — é
o mecanismo usado pela suíte de testes para limpar a tabela entre cenários.

Retenção de seis anos. Filtros por usuário, ação, módulo e período.

**Visibilidade:** proprietário vê tudo; gerente não vê alterações administrativas
de contas de proprietário; residentes e guests não acessam.

## 12. Relacionamentos centrais

```text
user_account 1 ── N client            (registered_by_artist_id)
user_account 1 ── N booking           (artist_id)
user_account 1 ── N guest_week
client       1 ── N quote
quote        1 ── N session
session      1 ── 0..1 booking
session      1 ── N payment
session      1 ── 0..1 aftercare
payment      1 ── N payment_refund
payout       1 ── N payout_item ── 1 session
payout       1 ── N payout_adjustment
booth        1 ── N booking
```

## 13. Decisões de modelagem que merecem destaque

| Decisão | Razão |
|---|---|
| `tstzrange` + `EXCLUDE` em vez de colunas `start`/`end` | Transforma a regra de conflito em garantia do banco, imune a concorrência |
| Acesso do guest derivado das semanas | Elimina divergência entre flag e realidade quando a semana vence |
| "Atrasado" derivado no pós-venda | Dispensa job só para trocar rótulo de estado |
| `artist_percentage` copiado em `quote` e `session` | Congela o percentual da aprovação; mudança de padrão não afeta o passado |
| Outbox em tabela, sem Redis | Durabilidade sem infraestrutura adicional no porte atual |
| `audit_log` append-only por gatilho | Imutabilidade garantida pelo banco, resistente inclusive à role dona da tabela |
| Estados como texto com `CHECK` | Mesma garantia do `ENUM` nativo, sem `ALTER TYPE` a cada novo estado |

## 14. Pendências deste documento

- Validar os nomes finais de tabelas e colunas na revisão de implementação.
- Definir índices adicionais depois de conhecer os relatórios mais usados.
- Confirmar política de retenção da tabela `user_session`.
