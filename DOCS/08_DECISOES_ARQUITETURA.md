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

> **Revisto em 27/09/2026 pelo ADR-024**, na parte de armazenamento. O destino de
> produção continua sendo armazenamento privado compatível com S3; o MVP usa o
> sistema de arquivos atrás da mesma porta, porque a imagem do MinIO deixou de ser
> distribuída livremente. A decisão sobre e-mail segue intacta.

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

**Situação: implementada e comprovada em 26/09/2026** (migração `0004`, etapa M3.1).
Oito cenários cobertos, entre eles a corrida com duas transações paralelas em que a
segunda começa antes do commit da primeira. Os testes escrevem SQL direto, sem
passar por casos de uso: o que se verifica é a garantia do banco, não a lógica da
aplicação.

**Armadilha registrada:** em `text()` do SQLAlchemy, `:period::tstzrange` falha
porque o parser lê `:period:` como marcador de parâmetro. Usar
`CAST(:period AS tstzrange)`.

**Data:** 24/09/2026.

## ADR-012 — Auditoria imutável no nível do banco

> **Revisado em 24/09/2026 durante a implementação da sprint M1.1.** A decisão
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

## ADR-020 — Backend completo antes da interface

**Decisão:** as sprints M1 a M6 entregam apenas backend. Toda a interface do MVP é
construída na sprint M7, sobre a API já pronta e testada.

**Motivo:** decisão do responsável. Evita alternância de contexto entre Python e
Vue a cada sprint e permite consolidar as regras de negócio antes de desenhar as
telas sobre elas.

**Alternativas:** entrega vertical por sprint, com API e tela juntas, que daria
retorno visual contínuo; fatia fina ponta a ponta, que daria algo demonstrável
muito rápido ao custo de retrabalho.

**Consequência e mitigação:** o responsável fica sem interface por várias sprints,
então mal-entendidos de regra podem aparecer tarde, já com o backend pronto. Para
reduzir isso, o contrato publicado em `/api/v1/docs` passa a ser o ponto de
validação ao fim de cada sprint de backend, permitindo executar o fluxo real sem
tela. A tela de login, antes prevista na M1, foi realocada para a M7.

**Data:** 25/09/2026.

> **Revisto em 28/09/2026 pelo ADR-025.** Uma fatia vertical de interface foi
> antecipada; o restante da regra continua valendo.

## ADR-021 — Erro de domínio traduzido em um único lugar

**Decisão:** casos de uso levantam `PermissionDeniedError` ou `BusinessRuleError`,
sem conhecer HTTP. A conversão em resposta acontece em `ErrorHandlers`, registrado
na aplicação: `PermissionDeniedError` vira 403 e `BusinessRuleError` vira 422.

**Motivo:** a primeira implementação repetia `try/except` em cada rota. Com dezenas
de endpoints pela frente, bastaria esquecer um bloco para uma exceção de domínio
escapar como 500 e vazar detalhe interno na resposta. Centralizar também mantém o
domínio livre de códigos de status.

**Consequência:** um erro novo de domínio precisa ser mapeado em `ErrorHandlers`,
senão vira 500. Rotas ficam sem tratamento de erro, apenas compondo casos de uso.

**Data:** 26/09/2026.

## ADR-022 — Autenticação de requisição em peça única

**Decisão:** `SessionAuthenticator` resolve a identidade a partir do cookie e é
usado por todos os roteadores. Nenhum módulo reimplementa a leitura de sessão.

**Motivo:** autorização duplicada por rota é a origem clássica de brechas — basta
uma cópia divergir para um endpoint aceitar sessão expirada ou de conta bloqueada.
A peça única garante que a reconferência do estado da conta a cada requisição, que
sustenta a RN 2.5, valha em todo lugar.

**Consequência:** módulos novos recebem o `Container` e instanciam o autenticador;
não leem o cookie diretamente.

**Data:** 26/09/2026.

## ADR-023 — `audit_log` é o histórico de estado, sem tabela paralela

**Decisão:** não criar `booking_history`. As transições de estado do agendamento —
aprovação, rejeição, remarcação, cancelamento e não comparecimento — ficam no
`audit_log`, gravadas na mesma transação da operação. O mesmo vale para os demais
módulos: nenhuma entidade ganha tabela própria de histórico de estado.

**Motivo:** o `audit_log` já é append-only por gatilho (ADR-012) e já guarda ator,
ação, módulo, entidade e os valores antigo e novo. Uma tabela paralela repetiria a
mesma informação sem a garantia de imutabilidade, e bastaria um caso de uso esquecer
de gravar nela para as duas fontes divergirem — com a pergunta insolúvel de qual
delas está certa. O modelo de dados previa `booking_history` de quando a auditoria
ainda seria por `REVOKE`; com o gatilho, a tabela perdeu a razão de existir.

**Alternativa considerada:** manter `booking_history` para simplificar a consulta do
histórico de um agendamento. Recusada: é um índice sobre o `audit_log`, não uma
segunda fonte, e pode ser resolvida por consulta filtrando `entity_type = 'booking'`.

**Consequência:** a tela de histórico do agendamento lê o `audit_log` filtrado por
entidade. Se o volume exigir, entra índice em `(entity_type, entity_id)` — decisão de
desempenho, não de modelagem. `05_MODELO_DADOS.md` deixou de descrever a tabela.

**Data:** 26/09/2026.

## ADR-024 — Armazenamento em sistema de arquivos no MVP, atrás da porta `ObjectStorage`

**Decisão:** o MVP grava os arquivos enviados em um diretório dentro de volume
nomeado do Docker, por meio de `FilesystemObjectStorage`. A abstração
`ObjectStorage` fica em `app/shared/storage/`, e nenhum caso de uso conhece a
implementação. O armazenamento compatível com S3 do ADR-006 permanece como destino
de produção, a ser retomado na M8.

**Motivo:** a etapa M4.3 precisava de um serviço compatível com S3 em
desenvolvimento e **a imagem do MinIO deixou de ser baixável sem autenticação**,
tanto a oficial quanto a da Bitnami. As alternativas disponíveis eram dublês que não
validam credencial, o que anularia o ganho de exercitar o adaptador, ou trariam um
container grande. Somado ao pedido de não acrescentar container ao ambiente, o
sistema de arquivos passou a ser a opção proporcional: zero serviço novo, e a
gravação em volume nomeado já atende à exigência do ADR-006 de o arquivo não
depender do sistema de arquivos efêmero da imagem.

**Alternativa considerada e recusada: guardar os bytes no PostgreSQL.** Teria a
vantagem real de um único alvo de cópia de segurança, já que o `pg_dump` levaria as
imagens. Recusada pelo efeito no tempo de recuperação: as metas propostas são perda
máxima de 24 horas e recuperação em até 4 horas, e um dump carregando gigabytes de
foto — o pós-venda da Fase 2 multiplica o volume — torna tanto a cópia diária
quanto o teste de restauração trimestral progressivamente mais pesados. Trinta
cópias retidas de vários gigabytes também é custo de armazenamento externo.

**Consequência de segurança, que melhorou o desenho:** sem S3 não há URL assinada.
A imagem passou a ser entregue por `GET /quotes/{id}/reference-images/{id}/content`,
que confere a sessão como qualquer outra rota. **Não existe nenhum endereço capaz de
devolver a foto sem o cookie do usuário** — um link assinado, ao contrário, funciona
sozinho até expirar e basta vazar num histórico ou num encaminhamento. A resposta vai
com `Cache-Control: private, no-store`, para que proxy e navegador não guardem dado
pessoal onde a expiração da sessão não alcança.

**Consequência operacional, registrada na M8:** a cópia de segurança passa a ter
**dois alvos**, o banco e o diretório de arquivos. Uma rotina que leve apenas o
`pg_dump` deixaria as imagens para trás, e a falta apareceria só na restauração. O
teste de restauração precisa cobrir os dois.

**Data:** 27/09/2026.

## ADR-025 — Fatia vertical de interface antecipada, revendo o ADR-020

**Decisão:** o ADR-020 dizia backend completo antes da interface. Passa a valer:
backend completo antes da interface, **exceto uma fatia vertical antecipada** —
acesso, clientes, agenda e orçamentos — construída sobre o que a API já entrega. A
M7 foi dividida em M7.1, agora, e M7.2, depois da M6. O backend fica pausado na
M4.4, que é retomada ao fim da M7.1.

**Motivo:** o risco "toda a interface concentrada na M7" estava aberto no roadmap
desde a reorganização em MVP e Fase 2, e a mitigação registrada — exercitar o
`/api/v1/docs` ao fim de cada sprint de backend — não mitigava o que importa.
Contrato de API mostra que o endpoint responde; não mostra que a regra foi entendida
como o estúdio precisa. Um mal-entendido de tela descoberto na M7, com todo o
backend pronto, é caro exatamente por ser tarde.

Some-se a necessidade concreta de demonstrar o sistema ao responsável antes de as
sprints financeiras começarem. Demonstração de API por documentação interativa não
substitui ver a agenda funcionando.

**Alternativa considerada:** manter o ADR-020 intacto e demonstrar pelo
`/api/v1/docs`. Recusada porque é justamente a mitigação que já se mostrou fraca, e
porque adiaria de novo o único componente do frontend sem biblioteca pronta — a
timeline de macas do ADR-004 —, que é a maior incerteza de estimativa do projeto.

**Consequência boa:** a timeline sai da M7.2 e vai para a M7.1.3. Construí-la agora
tira a maior incerteza de prazo do que resta.

**Consequência ruim, assumida:** quando a M5 entrar, aprovar agendamento passará a
exigir sinal confirmado, e a tela de agenda ganhará o indicador correspondente. É
acréscimo, não reescrita, e está na tabela de pendências de costura do roadmap.

> **Concretizou-se em 30/09/2026, e maior do que o previsto.** Além do indicador,
> a caixa "Approve straight away" do formulário de reserva deixou de funcionar
> para residente: criar já aprovado passou a ser recusado onde há sinal a
> confirmar (ADR-027). Continua sendo acréscimo e não reescrita, mas é mudança de
> comportamento numa tela entregue, não só de aparência.

**Consequência de processo:** a M4 fica aberta em três quartos durante a M7.1. Para
que isso não vire divergência entre código e documentação, a M4.4 está declarada
como a retomada imediata ao fim da M7.1, e o roadmap marca a sprint como pausada, e
não como concluída.

**Data:** 28/09/2026.

## ADR-026 — Registro único dos modelos persistentes

**Decisão:** `app/core/orm_registry.py` importa todos os modelos mapeados e é
importado pela raiz de composição e pelo `env.py` das migrações. Nenhum outro
lugar mantém lista de modelos.

**Motivo:** o SQLAlchemy só conhece uma tabela depois que a classe que a mapeia é
importada, e a falha aparece **na gravação**, não na inicialização. Aconteceu de
verdade: `booking.session_id` aponta para `tattoo_session`, o módulo de agenda
importava `Booking` e nada importava `TattooSession`. A API subia, respondia
consultas e estourava `NoReferencedTableError` no primeiro `INSERT` de
agendamento.

**Por que os testes não pegaram**, e isto é a parte que importa: o pytest carrega
todos os módulos de teste no mesmo processo, e os testes de orçamento importavam
o modelo que faltava. O defeito existia apenas onde nenhum teste olhava — o
servidor rodando. Foi a interface, ao tentar gravar um agendamento, que o
revelou.

**Consequência:** acrescentar tabela passa a exigir uma linha no registro. Em
troca, a lista deixa de existir em dois lugares — o `env.py` mantinha a sua — e
a aplicação não depende mais de um módulo importar outro por acaso.

**Alternativa considerada:** cada fábrica de módulo importar os próprios modelos.
Recusada porque não resolve o caso que causou o defeito: a chave estrangeira
cruza módulos, e o módulo que precisa da tabela registrada não é o dono dela.

**Data:** 29/09/2026.

## ADR-027 — O sinal pertence ao agendamento, não à sessão

**Decisão:** `payment` ganha `booking_id` como origem possível, ao lado de
`session_id`. O sinal de €50 é gravado contra o **agendamento**; o saldo continua
contra a sessão. A restrição garante exatamente uma origem preenchida.

**Motivo:** a RN-PAG-001 diz "**todo agendamento** exigirá um sinal de €50 para
confirmação", e a RN-AGE-005 condiciona a aprovação do horário a esse sinal. A
seção 7 do `05_MODELO_DADOS.md` previa apenas `session_id` ou `guest_week_id` —
mas `booking.session_id` é nulo em todo horário que não pertence a um trabalho
orçado, que é o caso de toda a agenda entregue na M3 e de qualquer reserva feita
por guest, que não acessa orçamento (RN-ORC-001). Sem a coluna, o sinal desses
agendamentos não tinha onde ser gravado e o portão da RN-AGE-005 não tinha o que
conferir.

**A decisão é do responsável**, tomada em 30/09/2026 quando a documentação se
mostrou incompleta: o sinal é pago e recebido pelo estúdio para que o horário
possa ser confirmado, e a solicitação fica pendente até o gestor confirmar no
sistema que recebeu.

**Consequência:** criar agendamento já em `APPROVED` passa a ser recusado onde há
sinal a confirmar. A RN-AGE-005 permite o atalho *"desde que confirmem o sinal"*,
e não existe sinal confirmado para uma linha que ainda não foi gravada. O caminho
é criar, confirmar o sinal, aprovar. O atalho continua aberto exatamente onde a
regra não pede sinal: cliente próprio do guest (RN-GST-004).

**Consequência de modelagem:** `retained_at` e `retained_reason` entram junto. A
RN-AGE-008 diz que, fora do prazo de 24 horas, o cliente **perde** o sinal e paga
um novo. O sinal perdido continua `CONFIRMED` — o estúdio ficou com ele —, mas
precisa sair de cena como sinal daquele horário, senão continuaria satisfazendo o
portão e o cliente aprovaria de novo sem pagar nada.

**Alternativas consideradas:** exigir que todo agendamento nasça de um orçamento,
o que manteria o modelo intacto mas quebraria a agenda da M3 e o guest; ou exigir
sinal só onde há sessão, o que manteria um caminho de aprovação sem portão e
contrariaria a RN-PAG-001 na letra. Ambas recusadas pelo responsável.

**Data:** 30/09/2026.

## ADR-028 — Agenda e financeiro se falam por portas declaradas pela agenda

**Decisão:** a agenda declara `DepositGate` e `BookingSettlementGate` no próprio
domínio; o financeiro as implementa em `PaymentDepositGate` e
`PaymentSettlementGate`; o `Container` liga os dois (ADR-016). A agenda não
importa o módulo financeiro.

**Motivo:** a RN-AGE-005 exige sinal confirmado antes de aprovar, e a RN-PAG-003,
a RN-AGE-008, a RN-AGE-009 e a RN-AGE-010 dão destino ao sinal em cada desfecho.
São regras da agenda que dependem de uma resposta do financeiro. Se a agenda
importasse o financeiro, a regra de aprovação passaria a depender do desenho
interno de pagamento, e trocar aquele desenho quebraria esta — a dependência
ficaria na direção errada, porque quem precisa da resposta é quem deve declarar a
pergunta.

**A porta de desfecho tem um método só**, com o desfecho como dado
(`BookingOutcome`). Uma porta com um método por evento cresceria a cada regra
nova e obrigaria o financeiro a implementar método vazio para o que ainda não
trata.

**Os dois vocabulários ficam separados de propósito.** A agenda fala em
`BookingOutcome` — o que aconteceu com o horário; o financeiro fala em
`SettlementEvent` — o destino do dinheiro. A tradução mora no adaptador, na
fronteira. Um enum compartilhado faria a agenda importar o vocabulário do
financeiro para poder chamá-lo, que é exatamente a dependência que a porta
existe para evitar.

**Consequência:** a `SchedulingFactory` passa a receber fábricas das portas, e
não instâncias prontas — as portas carregam repositórios, e repositório pertence
à transação em curso.

**Alternativa considerada:** o roteador orquestrar os dois módulos, chamando a
agenda e depois o financeiro. Recusada porque põe regra de negócio na rota, o que
o protocolo proíbe, e porque quebraria a atomicidade: um cancelamento gravado com
a retenção falhando deixaria o horário livre e o sinal ainda valendo.

**Data:** 30/09/2026.

## ADR-029 — O sistema retém sozinho e nunca devolve sozinho

**Decisão:** quando o desfecho do agendamento manda o estúdio ficar com o sinal,
o sistema marca a retenção por conta própria. Quando manda devolver, o sistema
**aponta** o que deve voltar e não lança nada: a devolução é registrada pelo
gestor, com valor, forma, motivo e responsável.

**Motivo:** a diferença não é de estilo, é da regra. Reter é escrituração — o
estúdio já está com o dinheiro e a RN-AGE-009 diz que ele fica, mesmo com aviso
de 24 horas; nada se move, só se registra. Devolver é movimento de caixa, e a
RN-PAG-009 é explícita: *"gerente ou proprietário registrará manualmente a
devolução **depois de realizá-la**"*. Um sistema que lançasse a devolução sozinho
estaria afirmando que o dinheiro saiu quando ninguém o mandou sair — e o registro
financeiro é de seis anos (RN-CLI-007).

**Consequência:** `SettleBooking` devolve a lista de pagamentos que a regra manda
devolver, e a grava na auditoria. A interface mostra a lista; o `RefundPayment`
executa quando o gestor o fizer. Um pagamento que deveria ter voltado e não
voltou continua visível, em vez de sumir num lançamento automático que ninguém
conferiu.

**Consequência de modelagem:** `retained_at` é separado de `REFUNDED`. Um sinal
retido continua confirmado. Um estado único esconderia qual dos dois aconteceu, e
os dois são a diferença entre o estúdio ter ficado com o dinheiro e o dinheiro
ter saído do caixa.

**Alternativa considerada:** lançar a devolução automaticamente e deixar o gestor
corrigir. Recusada porque a RN-PAG-007 proíbe apagar pagamento e manda corrigir
por ajuste vinculado — um lançamento automático errado viraria mais um lançamento
no histórico, não um erro desfeito.

**Data:** 30/09/2026.

## ADR-030 — O percentual do artista é dado da pessoa, não constante do código

**Decisão:** cada conta que tatua pode ter um **percentual acordado**, gravado em
`user_account.default_artist_percentage`. Nulo significa "siga a regra da
origem". Na aprovação do orçamento a ordem é: correção explícita do gestor para
**aquele** atendimento, depois o acordo do artista, depois a regra da origem.

**Motivo:** a planilha de controle do estúdio mostra **três** divisões no mesmo
mês — 85/15, 70/30 e 50/50 — e o mesmo artista aparecendo em mais de uma. Até
aqui os dois valores da RN-REP-001 e da RN-REP-002 estavam fixos no
`ArtistPercentagePolicy`, e um terceiro caso não cabia ali: acrescentá-lo
trocaria uma rigidez por outra, porque o estúdio negocia acordos e cada acordo
novo exigiria uma versão nova do sistema.

A precedência não é arbitrária. Um acordo negociado é mais específico que uma
regra geral, e a correção do gestor na aprovação é mais específica que o acordo
— é a RN-CLI-003, que já existia, e é o que explica FARPA aparecer na planilha
em 85/15 e em 70/30 no mesmo mês.

**Consequência:** `ArtistPercentagePolicy.for_origin` recebe o acordo e o
prefere quando existe. O percentual chega ao módulo de orçamentos pela porta
`ArtistTerms`, no desenho do ADR-028: quem precisa da resposta declara a porta,
quem tem o dado a implementa — `AccountArtistTerms`, em identidade —, e o
`Container` liga. Orçamentos continuam sem saber que existe uma tabela de
contas.

**Consequência de regra:** **mudar o acordo não alcança trabalho já aprovado.**
A garantia não está no caso de uso que altera, e sim na cópia que o orçamento
congelou na aprovação (RN-REP-006). É o teste mais importante da suíte deste
campo, porque é a diferença entre renegociar daqui para frente e reescrever o
que alguém já tinha a receber.

**Alternativa considerada:** acrescentar `85` como terceira entrada do mapa de
origens. Recusada porque o percentual não é propriedade da origem — a planilha
mostra o mesmo artista em duas divisões, e o mesmo valor aplicado a origens
diferentes. Seria dar nome de regra a um acordo comercial.

**Alçada:** só gerente e proprietário alteram, e a auditoria guarda o valor
anterior. Este número decide quanto o artista recebe em todo trabalho que
aprovar daqui para frente; deixá-lo mexer seria deixá-lo escrever o próprio
contrato, e mudá-lo sem registro seria mudar o contrato de alguém em silêncio.

**Pendência que não é do código:** a RN-REP-001 e a RN-REP-002 continuam como
estão no documento de regras, falando de dois percentuais. A decisão do
responsável em 06/10/2026 as estende, e **cabe a ele atualizar o texto** — o
documento de regras de negócio não é alterado por quem implementa.

**Data:** 06/10/2026.

## Processo de alteração

Nenhuma decisão acima pode ser alterada sem explicar o impacto, apresentar
alternativa e obter aprovação explícita, conforme o protocolo de desenvolvimento.
