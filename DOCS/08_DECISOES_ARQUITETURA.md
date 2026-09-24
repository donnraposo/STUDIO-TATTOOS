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

> **Revisado em 24/09/2026 durante a implementação da Sprint 02.1.** A decisão
> original baseava-se apenas em `REVOKE` e não se sustentou na prática. O texto
> abaixo substitui a versão anterior; o histórico está ao final da seção.

**Decisão:** `audit_log` é append-only por gatilho no banco. Um gatilho
`BEFORE UPDATE OR DELETE` levanta exceção, e o `REVOKE` de `UPDATE` e `DELETE`
para `PUBLIC` permanece como camada adicional.

**Motivo:** a regra exige registros que usuários não possam editar nem apagar, e
depender de a aplicação "não oferecer" a operação não é garantia. O `REVOKE`
sozinho também não é: no PostgreSQL, a role **dona** da tabela pode conceder o
privilégio de volta a si mesma, e a aplicação é dona das tabelas que cria. O
gatilho recusa a operação para qualquer role, inclusive a dona, e só pode ser
contornado removendo-o explicitamente por DDL — ato que é ele próprio detectável.

**Consequência:** correções em auditoria são impossíveis por desenho. `TRUNCATE`
continua funcionando, por ser DDL e não disparar gatilhos de linha — é assim que a
suíte de testes limpa a tabela entre cenários. Retenção de seis anos administrada
fora da aplicação.

**Verificação:** comprovado por teste automatizado e manualmente conectado como
dono do banco; ambos recebem `ERROR: audit_log e append-only`.

**Histórico:** versão original de 24/09/2026 previa somente
`REVOKE UPDATE, DELETE ... FROM <role da aplicação>`. Substituída no mesmo dia, ao
constatar que o dono da tabela contornaria a restrição.

## ADR-018 — Estados como texto com `CHECK`, não `ENUM` nativo

**Decisão:** perfis, estados de conta, de agendamento, de pagamento e demais
enumerações são colunas de texto com restrição `CHECK`, e não tipos `ENUM` nativos
do PostgreSQL.

**Motivo:** as sprints seguintes acrescentam estados a quase todos os módulos. Com
`ENUM` nativo, cada novo valor exige `ALTER TYPE`, que tem restrições de execução e
não pode ser revertido de forma simples. Com `CHECK`, passa a ser alteração de
restrição em uma migração comum.

**Alternativas:** `ENUM` nativo, mais autodescritivo no banco e com validação
idêntica, porém rígido para evoluir; texto livre sem restrição, descartado por
perder a garantia no banco.

**Consequência:** a garantia continua no banco, não apenas na aplicação. O nome da
restrição segue o padrão `ck_<tabela>_<campo>`. O `StrEnum` correspondente em Python
permanece a fonte dos valores válidos na camada de aplicação.

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

## ADR-015 — Uma unidade exportada por arquivo

**Decisão:** cada arquivo do projeto expõe exatamente uma unidade própria — uma
classe, uma função pura ou um tipo. No backend, nenhuma função de nível superior
convive com uma classe no mesmo arquivo.

**Motivo:** manutenibilidade. O nome do arquivo passa a declarar sua
responsabilidade, a navegação fica previsível e o histórico do Git mostra
exatamente o que mudou, sem ruído de alterações não relacionadas no mesmo arquivo.

**Consequência:** mais arquivos e mais imports explícitos. Fábricas e provedores
que antes ficariam soltos ao lado da classe passam a ser métodos do container de
composição (ADR-016). A convenção vale desde o primeiro commit de código; o Sprint
01 foi refatorado para atendê-la antes de avançar.

**Data:** 24/09/2026.

## ADR-016 — Raiz de composição em classe `Container`

**Decisão:** a construção de `Settings`, `Database` e demais dependências de
infraestrutura fica concentrada na classe `Container`, que também fornece a sessão
de banco aos casos de uso.

**Motivo:** evita fábricas com estado espalhadas por módulos e cumpre a inversão de
dependência: os módulos recebem a dependência pronta e não sabem como ela é
construída. Também torna o teste direto — basta instanciar um `Container` com outra
configuração, sem manipular cache global.

**Alternativas:** funções `get_*` com `lru_cache` por arquivo, que foi a primeira
implementação e produzia funções soltas convivendo com classes, ferindo ADR-015;
biblioteca de injeção de dependência, descartada por acoplar o domínio a um
framework adicional.

**Consequência:** `Container.instance()` é o ponto único de acesso em produção;
`Container.reset()` existe para os testes descartarem a instância compartilhada.

**Data:** 24/09/2026.

## ADR-017 — SQLAlchemy síncrono com psycopg 3

**Decisão:** acesso ao banco de forma síncrona, com `psycopg` 3 como driver.

**Motivo:** a lógica transacional deste sistema é a parte mais delicada —
fechamento semanal, confirmação de pagamento e as restrições de agenda. Código
síncrono é substancialmente mais simples de escrever e revisar corretamente nesse
contexto, e os testes dispensam infraestrutura de loop de eventos. Para até quinze
usuários simultâneos, o ganho de E/S assíncrona não compensa a complexidade.

**Alternativas:** SQLAlchemy assíncrono com `asyncpg`, idiomático em FastAPI e
melhor sob alta concorrência, porém desproporcional ao porte e mais propenso a erro
em transações compostas.

**Consequência:** rotas que tocam o banco são declaradas como funções síncronas e o
FastAPI as executa em pool de threads. Revisável se o volume crescer de forma
mensurável.

**Data:** 24/09/2026.

## ADR-019 — Entrega em MVP e Fase 2

**Decisão:** o sistema passa a ser entregue em duas ondas. O MVP cobre o ciclo
irredutível — login, cliente, agenda com prevenção de conflito, orçamento, sinal,
sessão paga e repasse semanal — mais uma sprint de implantação. Guests, pós-venda,
relatórios, PWA, autocadastro e recuperação de senha vão para a Fase 2.

**Motivo:** o estúdio precisa parar de usar planilha o quanto antes. O corte foi
feito pelo fio condutor do negócio, não por módulo: se qualquer elo do ciclo
faltar, o controle paralelo continua e o sistema não substitui nada.

**Alternativas:** entregar os onze sprints antes do primeiro uso, descartado por
adiar demais o valor; MVP apenas demonstrativo, descartado porque o objetivo
declarado é uso real, e simplificações que não sobrevivem ao uso real gerariam
retrabalho maior.

**Consequência:** nada é descartado, apenas resequenciado. A sprint M7 de
implantação passa a integrar o MVP — sem TLS, backup e restauração testada o
sistema não pode receber dado real. O orçamento entra completo no MVP por decisão
do responsável, mesmo sendo candidato natural a simplificação.

**Data:** 24/09/2026.

## Processo de alteração

Nenhuma decisão acima pode ser alterada sem explicar o impacto, apresentar
alternativa e obter aprovação explícita, conforme o protocolo de desenvolvimento.
