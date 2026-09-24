# Decisões de Arquitetura

**Última atualização:** 24/09/2026

> Registro das decisões tomadas, com motivo, alternativas avaliadas e consequência.
> Uma decisão aceita só pode ser substituída após registro do contexto, do impacto e
> de nova aprovação.

## ADR-001 — Backend em Python com FastAPI

**Decisão:** FastAPI como framework da API.
**Motivo:** validação de entrada por tipo, documentação automática do contrato e
bom desempenho para o porte previsto.
**Alternativas:** Django REST Framework, com mais recursos administrativos prontos,
porém mais acoplado ao próprio ORM e ao seu modelo de usuário; Flask, que exigiria
compor validação e documentação manualmente.
**Consequência:** regras de negócio ficam fora das rotas e dos schemas Pydantic,
para não acoplar o domínio ao framework.
**Data:** 23/09/2026.

## ADR-002 — PostgreSQL como banco

**Decisão:** PostgreSQL.
**Motivo:** além de integridade relacional e transações, oferece `tstzrange` e
restrições `EXCLUDE`, que expressam diretamente as regras de não sobreposição da
agenda.
**Consequência:** testes de comportamento transacional usam PostgreSQL real; SQLite
não substitui, por não suportar esses recursos.
**Data:** 23/09/2026.

## ADR-003 — Sessão de servidor com cookie, sem JWT

**Decisão:** sessão armazenada no servidor, transportada por cookie seguro.
**Motivo:** o bloqueio de conta e a troca de senha precisam revogar acesso
imediatamente. JWT assinado é válido até expirar e exigiria lista de revogação
adicional para atender à regra.
**Consequência:** o cookie carrega apenas um identificador aleatório; nenhum dado
pessoal ou permissão trafega nele. Revisável se surgir cliente nativo.
**Data:** 23/09/2026.

## ADR-004 — Agenda timeline sem licença paga

**Decisão:** construir a visão macas × horário com CSS Grid próprio, em componente
Vue, sem biblioteca de calendário licenciada.
**Motivo:** a visão necessária é timeline por recurso, que nas bibliotecas
avaliadas está na faixa paga. Além do custo recorrente, as regras deste estúdio são
específicas — dois recursos com semânticas diferentes de conflito, solicitações
concorrentes visíveis e modal que não permite ignorar conflito. Adaptar uma
biblioteca genérica a essas regras tende a custar mais do que construir a grade.
**Alternativas:** licença paga do FullCalendar, que entregaria a grade pronta e
testada ao custo de licença por desenvolvedor; visão semana/dia gratuita com macas
por cor, descartada por dificultar a leitura da ocupação simultânea.
**Consequência:** maior esforço inicial no módulo de agenda. O componente é próprio
e sem dependência externa de renderização.
**Data:** 24/09/2026.

## ADR-005 — Hospedagem em VPS único com Docker Compose

**Decisão:** um servidor virtual executando proxy, API, worker e PostgreSQL em
containers.
**Motivo:** proporcional a um estúdio, quatro macas e até quinze usuários
simultâneos. Custo previsível e operação simples.
**Alternativas:** cloud gerenciada, descartada por custo e complexidade
desproporcionais; plataformas simplificadas, com menos controle sobre backup e rede.
**Consequência:** atualização, backup e monitoramento são responsabilidade da
operação. O backup precisa sair do servidor, sob pena de perder dados junto com ele.
**Data:** 24/09/2026.

## ADR-006 — Serviços gerenciados para e-mail e armazenamento

**Decisão:** e-mail por serviço transacional; fotos e comprovantes em armazenamento
privado compatível com S3.
**Motivo:** o pós-venda depende do e-mail diário das 08h. Servidor SMTP próprio em
VPS tem risco alto de entrega em spam, o que quebraria a rotina. Arquivos fora do
container evitam perda ao recriar a imagem.
**Consequência:** a integração fica isolada atrás de um adaptador, permitindo trocar
de provedor sem alterar casos de uso. O provedor final será confirmado na
implementação.
**Data:** 24/09/2026.

## ADR-007 — Outbox em tabela, sem Redis nem Celery

**Decisão:** notificações e e-mails gravados em tabela de outbox, consumidos por um
worker com `SELECT ... FOR UPDATE SKIP LOCKED`.
**Motivo:** garante durabilidade sem introduzir Redis e Celery, que seriam
infraestrutura adicional sem volume que a justifique. A falha de e-mail nunca pode
alterar estado de negócio, e o reinício de um container não pode perder envios.
**Consequência:** entrega assíncrona com repetição controlada e idempotência. Se o
volume crescer, o worker pode ser trocado por fila dedicada sem mudar os casos de uso.
**Data:** 24/09/2026.

## ADR-008 — Worker separado da API

**Decisão:** container próprio para agendador e outbox.
**Motivo:** a lista das 08h e o fechamento das sextas às 20h não podem depender do
ciclo de vida da API, nem executar em duplicidade quando houver mais de um processo
de API.
**Consequência:** um único worker ativo por vez; a topologia de produção deve
garantir isso.
**Data:** 24/09/2026.

## ADR-009 — SQLAlchemy 2 com Alembic

**Decisão:** SQLAlchemy 2.0 como camada de dados e Alembic para migrações.
**Motivo:** suporte maduro a tipos específicos do PostgreSQL, incluindo intervalos e
restrições necessárias à agenda, com tipagem estática na versão 2.
**Consequência:** as restrições `EXCLUDE` entram como operação explícita na
migração, não são geradas automaticamente pela autogeração.
**Data:** 24/09/2026.

## ADR-010 — Hash de senha com Argon2id

**Decisão:** `pwdlib` com Argon2id.
**Motivo:** algoritmo recomendado atualmente para senhas, resistente a ataque por
hardware dedicado. `FastAPI Users` foi avaliado e descartado por estar em modo de
manutenção declarado pelo próprio projeto.
**Consequência:** login, recuperação e sessões são implementados sobre os estados e
permissões próprios do estúdio, sem framework de autenticação de terceiros.
**Data:** 24/09/2026.

## ADR-011 — Integridade de agenda garantida pelo banco

**Decisão:** as duas regras de não sobreposição são restrições `EXCLUDE` no
PostgreSQL, não apenas validação na aplicação.

- Maca: apenas agendamentos aprovados bloqueiam.
- Artista: pendentes e aprovados bloqueiam, mesmo entre macas diferentes.

**Motivo:** validar somente em código não impede a corrida entre duas requisições
simultâneas que consultam a agenda ao mesmo tempo e ambas encontram o horário livre.
**Consequência:** a aplicação captura a violação da restrição e devolve o conflito
ao usuário. Os testes de concorrência precisam abrir transações paralelas reais.
**Data:** 24/09/2026.

## ADR-012 — Auditoria imutável no nível do banco

**Decisão:** a role da aplicação recebe apenas `INSERT` e `SELECT` em `audit_log`;
`UPDATE` e `DELETE` são revogados.
**Motivo:** a regra exige registros que usuários não possam editar nem apagar.
Depender de a aplicação "não oferecer" a operação não é garantia.
**Consequência:** correções em auditoria são impossíveis por desenho. Retenção de
seis anos administrada fora da aplicação.
**Data:** 24/09/2026.

## ADR-013 — Idioma

**Decisão:** interface e mensagens da API em inglês; documentação interna em
português.
**Data:** 23/09/2026.

## ADR-014 — Numeração da documentação preservada

**Decisão:** manter a numeração existente de `00` a `04` e complementar com `05` a
`08`, em vez de renumerar conforme o modelo genérico do protocolo.
**Motivo:** a substância das fases iniciais já existe e está aprovada sob outros
nomes. Renumerar reescreveria documentos validados e dificultaria rastrear o
histórico de aprovações.
**Data:** 24/09/2026.

## Processo de alteração

Nenhuma decisão acima pode ser alterada sem explicar o impacto, apresentar
alternativa e obter aprovação explícita, conforme o protocolo de desenvolvimento.
