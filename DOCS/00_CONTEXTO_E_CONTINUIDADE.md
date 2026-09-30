# Contexto do Projeto e Continuidade para Próxima IA

**Última atualização:** 30/09/2026  
**Idioma desta documentação:** português  
**Idioma planejado da interface:** inglês  
**Estado geral:** implementação em andamento. Sprint 01, M1, M2, M3, M4, M5 e a fatia vertical de interface M7.1 concluídas. A próxima é a M6 — repasses e fechamento semanal. O desenho funcional está fechado desde 24/09/2026.

> **Onde ler o andamento:** este arquivo resume o contexto e as decisões. O estado
> sprint por sprint fica em [`09_ROADMAP_IMPLEMENTACAO.md`](09_ROADMAP_IMPLEMENTACAO.md),
> que é a fonte em caso de divergência.

## Leia primeiro

1. [`01_REGRAS_DE_NEGOCIO.md`](01_REGRAS_DE_NEGOCIO.md) é a fonte detalhada das regras aprovadas.
2. [`02_ROADMAP_PRE_IMPLEMENTACAO.md`](02_ROADMAP_PRE_IMPLEMENTACAO.md) mostra as fases, dependências, pendências e critérios para avançar.
3. [`03_REQUISITOS_NAO_FUNCIONAIS.md`](03_REQUISITOS_NAO_FUNCIONAIS.md) registra metas de desempenho, compatibilidade, segurança, backup e e-mail.
4. Este arquivo resume o contexto, as decisões mais importantes e o ponto exato em que a conversa parou.

Se uma regra resumida aqui divergir da regra detalhada, verificar os dois arquivos com o usuário e corrigir a documentação antes de avançar. Não reabrir decisões claramente aprovadas sem uma contradição real.

## Objetivo

Criar um sistema interno para a operação de um estúdio de tatuagem em Cork City, Irlanda. O sistema é usado por proprietário, gerente, tatuadores residentes e guests para administrar usuários, clientes, agenda de macas, orçamentos, sessões, pagamentos, repasses e pós-venda.

O escopo desta versão é **um único estúdio**. Não projetar agora uma plataforma multiestúdio ou SaaS. Clientes não terão contas nem acesso ao sistema. A cobrança por cartão será inserida manualmente nesta versão, sem integração com adquirente ou gateway.

## Configuração operacional aprovada

- Local: Cork City, Irlanda.
- Fuso: `Europe/Dublin`, com mudança automática entre horário padrão e de verão.
- Moeda: euro (€).
- Idioma da interface: inglês.
- Funcionamento: terça a domingo, 10h às 20h; segunda-feira fechado.
- Quatro macas iniciais; gerente e proprietário podem adicionar macas.
- Todas as macas seguem o mesmo horário-base. Gerente e proprietário podem excepcionalmente abrir ou bloquear horários e bloquear uma maca ou o estúdio todo.

## Decisões tecnológicas alinhadas

- Backend: Python com FastAPI.
- Banco de dados: PostgreSQL.
- Execução: componentes containerizados com Docker. **Desenvolvimento e produção não
  sobem o mesmo conjunto** — em produção o frontend compilado é servido pelo Caddy e
  não tem container próprio. A contagem e as decisões abertas estão na seção 8 de
  `04_ARQUITETURA_TECNICA.md` e na sprint M8 do roadmap.
- Frontend: Vue 3, TypeScript e Vite.
- Primeira versão: sistema web responsivo e instalável como PWA; não será um aplicativo nativo separado.
- Interface na raiz do domínio e API sob `/api/v1`, pelo mesmo domínio.
- Login web/PWA com cookie seguro e sessão validada no servidor. JWT não será a sessão principal do navegador nesta versão.
- Tentativas de agendamento bloqueadas por conflito na agenda do artista notificarão gerente e proprietário dentro do sistema e por e-mail.
- Push no celular é uma evolução futura da PWA. Bibliotecas e serviços específicos permanecem pendentes; consultar `04_ARQUITETURA_TECNICA.md`.

## Perfis e acesso

- Há quatro perfis: proprietário, gerente, tatuador residente e guest.
- Proprietário e gerente também podem atuar como tatuadores, mantendo permissões administrativas; aplicam-se as mesmas regras financeiras de artista.
- Proprietário administra todos os perfis e pode atribuir/permutar perfis. Gerente não altera perfis nem promove usuários; administra usuários residentes e guests.
- Gerente e proprietário podem ativar/bloquear residentes e guests. Somente proprietário pode bloquear gerente/proprietário; o último proprietário ativo não pode ser bloqueado.
- Artistas podem solicitar autocadastro com nome artístico, e-mail único, telefone, perfil solicitado (residente ou guest), senha e confirmação. O pedido fica pendente sem acesso. Rejeição exige motivo, comentário opcional e permite correção e reenvio. Aprovação, rejeição e bloqueio notificam por e-mail.
- Gerente/proprietário podem adicionar residentes e guests diretamente; essas contas ficam ativas após o cadastro. Somente proprietário cria gerente/proprietário, com nome, e-mail, telefone, perfil, credenciais e indicação se também atua como tatuador (nome artístico obrigatório nesse caso).
- Login por e-mail/senha; recuperação por link temporário; sem autenticação de dois fatores. Bloqueio e troca de senha encerram sessões ativas.
- Bloqueio remove acesso, mas preserva histórico. Agendamentos futuros não são cancelados automaticamente; gerente/proprietário recebe alerta para transferir ou cancelar.

## Regras de negócio-chave

### Clientes

- Nome e telefone obrigatórios; Instagram opcional.
- Residente pode cadastrar cliente durante agendamento e vê o cadastro completo somente de clientes que cadastrou. Gerente/proprietário veem todos.
- Cliente pode estar vinculado a mais de um artista. Se retornar ao artista que o trouxe, permanece como cliente próprio; se o estúdio encaminhar esse cliente a outro artista, o atendimento é indicação do estúdio.
- Artista Y recebe somente nome, telefone e Instagram do cliente ligado a X quando indicado para novo atendimento; não vê ficha completa nem histórico anterior.
- Só gerente/proprietário corrigem origem/percentual do atendimento; mudança vale somente para aquele atendimento.
- Duplicidade é alertada por telefone/Instagram sem bloqueio automático. Residente edita seus clientes; gerente/proprietário editam todos e podem unir duplicidades preservando vínculos/histórico. Exclusão direta de cliente com histórico é proibida.
- Retenção: sem exclusão automática imediata; dados são mantidos enquanto necessários; registros financeiros por pelo menos seis anos; cadastros inativos revisados depois de seis anos. Solicitações de acesso/correção/exclusão são avaliadas por gerente/proprietário. Excluir ou anonimizar dados quando não houver justificativa de retenção.
- Termos de consentimento, questionário de saúde e autorização de uso de imagem ficam fora do escopo atual.

### Agenda e macas

- Maca e bancada contam como um só recurso, chamado maca e numerado. O artista define início e fim sem blocos fixos; não há intervalo de limpeza obrigatório cadastrado.
- Reserva registra cliente, artista, maca, data e intervalo. Residente e guest solicitam; gerente/proprietário podem criar diretamente aprovada, inclusive o próprio agendamento quando atuam como tatuadores, desde que sinal confirmado e sem conflito.
- Estados: `Solicitada → Aprovada ou Rejeitada → Realizada, Cancelada ou Não compareceu`.
- Pendentes não bloqueiam a maca e podem concorrer. Solicitações concorrentes aparecem juntas, com data/hora de pedido. Após aprovação, maca fica ocupada naquele intervalo; não se pode aprovar reserva sobreposta. Modal de conflito mostra reserva existente e não permite ignorar conflito.
- O mesmo artista não poderá ter solicitações pendentes ou agendamentos aprovados sobrepostos, mesmo em macas diferentes. A tentativa conflitante será impedida e notificará gerente e proprietário no sistema e por e-mail. A pendência ocupa o horário do artista, não a maca para outros artistas.
- Rejeição exige motivo: Horário ocupado, Estúdio fechado ou Horário remarcado; observação opcional. Sinal é devolvido quando o estúdio rejeita.
- Cliente paga sinal de €50 antes da aprovação. Gerente/proprietário confirma depósito, dinheiro ou cartão (e registra usuário, valor, data/hora e forma). Sem confirmação, não aprova.
- Cliente pode remarcar se avisar com ao menos 24h; gerente/proprietário efetiva a mudança e transfere o valor pago para o novo horário. Fora de 24h, perde sinal, que fica com o estúdio; valor pago acima dele é devolvido.
- Cancelamento sem nova data: estúdio retém sinal, inclusive com aviso de 24h; devolve eventual valor acima do sinal. Não comparecimento: mesma retenção de €50 e devolução do excedente. Nunca há parcela do sinal ao artista.
- Sinal integra o valor total da sessão e não é adicional. Quando a sessão ocorre, sinal entra na base do repasse. Cada sessão de um projeto tem seu próprio sinal de €50.
- Gerente/proprietário podem bloquear uma maca ou todas, reabrir horário e registrar data/horário/motivo; histórico guarda mudanças.
- E-mails de estado/alteração vão para o artista. Cliente é contatado fora do sistema. Falha de e-mail não muda estado e fica registrada.
- Atrasos/extensão não prolongam reserva automaticamente; gerente/proprietário resolve por transferência ou remarcação registrada.

### Orçamentos e sessões

- Residente, gerente e proprietário criam orçamentos; guest não tem acesso. Para indicação do estúdio atendida por guest, gerente/proprietário criam orçamento e agendamento.
- Orçamento fica pendente até aprovação/rejeição manual por gerente/proprietário; sem validade automática. Alterar aprovado volta a pendente. Rejeição exige motivo e permite observação.
- Campos: cliente, artista, origem (próprio/estúdio), descrição, região do corpo, tamanho, referências opcionais, valor total, quantidade e valor previsto de sessões, duração estimada por sessão e observações.
- Artista marca sessão realizada; gerente/proprietário confirma recebimento. Somente sessão realizada e integralmente paga fica concluída e entra em repasse. Pagamento parcial extra não é permitido além do sinal e saldo integral.
- Sessão parcialmente executada tem estado próprio e repasse apenas sobre o valor efetivamente recebido; gestor ajusta sessões restantes. Alteração do total exige nova aprovação.

### Finanças e repasses

- Residente, proprietário e gerente quando atuam como tatuadores: cliente próprio = 70% artista / 30% estúdio; indicação do estúdio = 50%/50%.
- Guest: cliente próprio paga diretamente a ele, além da taxa semanal de €600; indicação do estúdio paga ao estúdio e divide 50%/50%, inclusive se a semana guest já estiver paga.
- Para sessão de múltiplas etapas, repasse proporcional ao valor da sessão efetivamente paga. Tatuagem de €10.000 em quatro sessões de €2.500 calcula a porcentagem em cada €2.500.
- Pagamentos inseridos manualmente por gerente/proprietário; formas registráveis: depósito, dinheiro, cartão. Sem integração de cartão nesta versão; taxas de cartão são absorvidas pelo estúdio.
- Estados de pagamento: informado, confirmado, recusado, devolvido ou estornado. Pagamento nunca é apagado; correções são ajustes vinculados, com histórico.
- Sessão integralmente quitada; artista recebe só após sessão realizada e quitada.
- Devolução manual, ligada ao pagamento, com valor, data, forma, motivo, observação e comprovante opcional; pode usar forma diferente. Exibe devolvido e retido.
- Repasse fecha sexta às 20h (`Europe/Dublin`), inclui recebimentos até sexta às 20h. Calculado por sessão e arredondado a 2 casas. Gerente/proprietário marca transferência manualmente; comprovante opcional.
- Devolução/estorno após repasse já pago vira ajuste negativo no próximo repasse e não altera o fechamento anterior.
- Percentual do orçamento aprovado fica congelado; mudança de padrão só afeta novos orçamentos. Para mudar um atendimento existente, gerente/proprietário edita motivo e reaprova.
- Demonstrativo: sessões, valor recebido, percentual, ajustes positivos/negativos, total líquido; estados calculado/pago/ajustado.
- Sinal exemplo: sessão €100, €50 pagos na reserva e €50 depois; se cliente próprio de residente, artista recebe €70 e estúdio €30. Se cancelado/não comparece, estúdio fica com €50 e, se €100 foram pré-pagos, devolve €50; artista não recebe.

### Guest

- Guest solicita cadastro e depende de aprovação. A taxa é €600 por semana de sábado a sexta (`Europe/Dublin`), paga adiantado.
- Pode pagar uma ou mais semanas futuras; cada semana registrada separadamente. Pode reservar somente dentro das semanas pagas. Sem semana atual/futura paga, conta inativa; semanas consecutivas mantêm acesso.
- Gerente ativa/renova após confirmar pagamento. Devolução ou transferência de semana fica a critério do gerente/proprietário, registrando motivo, semana original/nova, valor, data e responsável.
- Guest vê disponibilidade, solicita macas e informa nome, telefone e Instagram do cliente na reserva. Não tem cadastro de clientes, orçamento ou pós-venda.
- Cliente próprio paga direto ao guest. Cliente indicado pelo estúdio é cadastrado e associado pelo gerente/proprietário; paga ao estúdio e guest recebe 50%.

### Pós-venda

- Cada sessão gera lembrete de pós-venda 15 dias depois da data real.
- Às 08h, diariamente, gerente recebe e-mail obrigatório com clientes pendentes; proprietário opta por receber. E-mail inclui cliente, telefone, Instagram, artista, data da sessão, dias de atraso e link autenticado; não inclui fotos/observações.
- Falha de e-mail fica registrada, não altera estado. Área própria separa pendentes, atrasados e concluídos, busca por cliente e filtra artista/data/vencimento.
- Residente consulta apenas registros das próprias sessões; não edita nem conclui. Só gerente/proprietário editam, anexam/removem foto, concluem ou reabrem. Guest não acessa.
- Conclusão registra usuário, data/hora, resultado, observações e fotos de cicatrização; todas as edições são auditadas.
- Resultados: cicatrização normal, orientação reforçada, novo acompanhamento, avaliação do tatuador, possível retoque, cliente não respondeu ou outro (observação obrigatória). Novo acompanhamento define nova data e continua pendente.
- Reabertura de concluído exige motivo e nova data. Fotos e reaberturas/exclusões ficam no histórico.
- A PWA instalável está prevista desde a primeira versão; notificações push no aparelho continuam fora do primeiro escopo.

### Painéis, relatórios e auditoria

- Painel gerente/proprietário: agenda, solicitações, pagamentos aguardando, repasses de sexta, guest perto do vencimento, pós-venda, ocupação de macas, faturamento.
- Residente: agenda, solicitações/orçamentos, clientes cadastrados por ele, repasse previsto e consulta de pós-venda próprio.
- Guest: semanas pagas, validade, disponibilidade, próprias solicitações/agendamentos e repasses de indicações.
- Relatórios para gerente/proprietário: faturamento por período, receita por artista, próprio versus indicação, pagamento por forma, sinais retidos/devoluções, repasses, taxa guest, ocupação de macas, cancelamento/falta, sessões, pós-venda.
- Comparação: período atual/anterior ou dois períodos escolhidos; faturamento bruto, receita líquida, repasses, taxa guest, sinal retido, devolução/estorno, artista, origem e variação absoluta/percentual.
- Filtros por período, artista e estado; exportação em PDF e Excel.
- Residente acessa somente produção e repasses próprios; guest somente seus repasses de indicações.
- Auditoria: proprietário vê tudo; gerente vê operacional/financeiro, mas não alterações administrativas de contas de proprietário; artistas não acessam. Logs imutáveis, filtráveis por usuário, ação, módulo e período; mostram data/hora, responsável, ação e valores antigo/novo quando houver.
- Relatórios usam base de caixa: faturamento bruto recebido = recebimentos confirmados no estúdio (sessões/sinais/guest), cada transação uma vez e antes de devoluções/repasses; receita líquida operacional = recebimentos brutos menos devoluções efetivadas e repasses líquidos a artistas. O repasse já contém a divisão de 70/30 ou 50/50, portanto não subtrair novamente a parte do artista ao usar a parcela do estúdio. Pagamentos diretos de cliente próprio do guest não entram no faturamento do estúdio; a taxa semanal de €600 entra. Exemplo: sessão de cliente próprio do residente paga €100, repasse €70, receita operacional líquida €30.

## Documentos existentes e sua função

| Arquivo | Função |
|---|---|
| `00_CONTEXTO_E_CONTINUIDADE.md` | Este resumo para a próxima IA e ponto de retomada. |
| `01_REGRAS_DE_NEGOCIO.md` | Regras detalhadas e fontes oficiais de proteção de dados na Irlanda. |
| `02_ROADMAP_PRE_IMPLEMENTACAO.md` | Fases, dependências, riscos, critérios e situação atual. |
| `03_REQUISITOS_NAO_FUNCIONAIS.md` | Requisitos técnicos aprovados em alto nível. |
| `04_ARQUITETURA_TECNICA.md` | Visão da solução, segurança, PWA, notificações e riscos. |
| `05_MODELO_DADOS.md` | Entidades, relacionamentos e restrições de integridade. |
| `06_ESTRUTURA_PROJETO.md` | Pastas, módulos, camadas, contratos de API e containers. |
| `07_PLANO_TESTES.md` | Cenários de teste e critérios de aceite. |
| `08_DECISOES_ARQUITETURA.md` | Catorze decisões registradas com motivo e alternativas. |

## Onde paramos

### Concluído

**Fases 0 a 13 do roadmap estão concluídas.** As fases 0 a 11 fecharam o desenho
funcional: contexto do estúdio, perfis e acesso, clientes e privacidade, agenda,
orçamentos e sessões, pagamentos, repasses, guests, pós-venda, painéis, relatórios,
auditoria e requisitos não funcionais.

Em 24/09/2026 foram concluídas a Fase 12 e a Fase 13, com quatro entregáveis novos
(`05` a `08`) e as decisões pendentes de arquitetura fechadas.

### Decisões tomadas em 24/09/2026

- Numeração da documentação preservada e complementada (ADR-014).
- Hospedagem em VPS único com Docker Compose e Caddy (ADR-005).
- Agenda timeline própria em CSS Grid, sem licença paga (ADR-004).
- E-mail transacional e armazenamento de arquivos gerenciados (ADR-006).
- SQLAlchemy 2 com Alembic (ADR-009) e Argon2id via `pwdlib` (ADR-010).
- Outbox em tabela com worker separado, sem Redis ou Celery (ADR-007, ADR-008).
- Integridade da agenda garantida por restrições `EXCLUDE` no PostgreSQL (ADR-011).
- Auditoria imutável por revogação de permissão no banco (ADR-012).

### Fase atual

**Implementação autorizada em 24/09/2026.** A Fase 14 foi aprovada e o
desenvolvimento seguiu para `09_ROADMAP_IMPLEMENTACAO.md`.

**Sprint 01 — Fundação técnica: concluída.** O repositório deixou de conter apenas
documentação. Existe aplicação funcional em containers: FastAPI com verificação de
saúde e prontidão, PostgreSQL com as extensões `btree_gist` e `citext` aplicadas por
migração, e interface Vue 3 com TypeScript consumindo a API.

Convenção reforçada e aplicada: **uma unidade exportada por arquivo** (ADR-015),
com raiz de composição em `Container` (ADR-016). O Sprint 01 foi refatorado para
atender a regra antes de ser fechado.

**Identidade visual definida.** Tipografia Urbanist com a escala 32/24/20/18/16/14,
paleta ouro sobre preto extraída do monograma do estúdio, tokens centralizados em
`frontend/src/shared/tokens.css`. A logo está em `frontend/public/brand/logo.jpg`.

**Entrega reorganizada em MVP e Fase 2** (ADR-019). O MVP cobre o ciclo
irredutível do negócio — login, cliente, agenda com prevenção de conflito,
orçamento, sinal, sessão paga e repasse semanal — mais implantação. Guests,
pós-venda, relatórios, PWA, autocadastro e recuperação de senha vão para a Fase 2.
Nada foi descartado, apenas resequenciado. Objetivo declarado: **uso real no
estúdio**, não demonstração.

**Sprint M1 — Identidade e acesso: concluída em 26/09/2026.** Entrega:

- Tabelas de identidade, sessão, histórico de estado e auditoria append-only.
- Autenticação com Argon2id, sessão no servidor com cookie `HttpOnly`, dupla
  expiração (60 minutos de inatividade, 12 horas absolutas) e CSRF por duplo envio.
- Gestão de contas pelo gestor, com a matriz de permissões da RN 2 aplicada e
  auditada.

Endpoints disponíveis: `/health`, `/ready`, `/auth/login`, `/auth/logout`,
`/auth/me`, `GET /users`, `POST /users`, `POST /users/{id}/block` e
`POST /users/{id}/unblock`. **51 testes aprovados.**

Decisões revistas ou tomadas durante a implementação, todas registradas:
imutabilidade da auditoria por gatilho em vez de `REVOKE` (ADR-012 revisado);
estados como texto com `CHECK` em vez de `ENUM` nativo (ADR-018); backend completo
antes da interface (ADR-020); tradução central de erro de domínio (ADR-021).

**Sprint M2 — Clientes: concluída em 26/09/2026.** Cadastro, alerta de
duplicidade, visibilidade em três níveis e união preservando histórico. Os três
níveis da RN-CLI-004 estão cobertos por teste, incluindo o artista indicado que vê
apenas nome, telefone e Instagram.

**Sprint M3 — Agenda e macas: concluída em 26/09/2026**, nas três etapas.

**A etapa M3.1 retirou o maior risco técnico do projeto.** As duas restrições
`EXCLUDE` estão no banco e comprovadas por oito testes, incluindo uma corrida com
duas transações paralelas reais. A maca só é bloqueada por agendamento aprovado;
o artista é bloqueado também por pendência, inclusive entre macas diferentes.

A partir daqui, conflito de agenda é impossível por construção: nem a aplicação
nem uma consulta manual conseguem gravar sobreposição.

As etapas M3.2 e M3.3 completaram o ciclo: solicitar, aprovar, rejeitar,
cancelar, marcar não comparecimento e remarcar, além da gestão de macas.
Conflito volta como `409` com o agendamento existente, alimentando o modal da
RN-AGE-007.

**Dependência declarada:** o portão do sinal na aprovação (RN-AGE-005) e o destino
financeiro de cancelamento, não comparecimento e remarcação fora de 24h dependem do
módulo de pagamentos. A costura está em `ApproveBooking._deposit_is_confirmed`.

**Sprint M4 — Orçamentos e sessões: em andamento**, etapa 1 de 3.

**A etapa M4.1 entregou o modelo.** Migração `0005` com `quote`,
`quote_reference_image`, `tattoo_session` e a coluna `booking.session_id`. O
percentual congelado da RN-REP-006 deixou de depender da aplicação: o banco recusa
orçamento aprovado sem percentual gravado, do mesmo modo que recusa sessão parcial
sem valor cobrado e sessão quitada sem confirmação do gestor. **104 testes
aprovados.**

Duas decisões da etapa: a tabela é `tattoo_session`, não `session`, por colisão com
a sessão de banco do SQLAlchemy e com `user_session`; e `origin` e
`artist_percentage` são copiados do orçamento para a sessão, nunca lidos de volta no
momento do repasse, porque o orçamento pode ser reaprovado com outro percentual e o
que já foi executado precisa continuar valendo o que valia.

**A etapa M4.2 entregou o ciclo do orçamento.** Criar, editar, aprovar e rejeitar,
em `/quotes/*`. O percentual é congelado na aprovação, com 70% para cliente próprio
e 50% para indicação do estúdio, e o gestor pode corrigir o percentual deste
atendimento — a correção fica na auditoria junto do padrão que teria sido aplicado.

Duas regras que só existem juntas: editar um orçamento aprovado o devolve a
pendente **e apaga o percentual congelado**. Um percentual sobrevivente num
orçamento pendente pareceria inofensivo e permitiria à próxima aprovação passar sem
regravá-lo, aplicando o acordo antigo a um valor novo. Há teste para isso.

O guest não acessa orçamentos (RN-ORC-001), e a política confere o **perfil**, não
se a pessoa tatua: o guest tatua, então qualquer verificação por "atua como artista"
o deixaria passar. **119 testes aprovados.**

**A etapa M4.3 entregou as imagens de referência**, e com uma decisão revista: a
imagem do MinIO deixou de ser distribuída livremente, e o armazenamento passou a ser
um diretório em volume nomeado atrás da porta `ObjectStorage`, **sem container novo**
(ADR-024). O provedor gerenciado compatível com S3 do ADR-006 segue como destino de
produção, retomado na M8.

A troca melhorou a segurança. Sem S3 não há URL assinada: a imagem é entregue por
`GET /quotes/{id}/reference-images/{id}/content`, que confere a sessão como qualquer
rota. **Nenhum endereço devolve a foto sem o cookie do usuário.** **139 testes
aprovados.**

Duas coisas para quem continuar o trabalho:

- **A cópia de segurança passou a ter dois alvos**, o banco e o diretório de
  arquivos. Está registrado na M8, junto da exigência de o teste de restauração
  cobrir os dois.
- **A ordem entre banco e arquivo é inversa nas duas operações**, de propósito:
  anexar grava o arquivo antes da linha, remover apaga a linha antes do arquivo. A
  regra é que o banco nunca aponte para arquivo inexistente, então a sobra possível é
  sempre arquivo órfão — lixo invisível — e nunca imagem quebrada na tela.

**Backend pausado em 28/09/2026 para a construção da interface** (ADR-025). A M4
ficou em três quartos: falta a etapa M4.4, com as sessões, que volta ao fim da M7.1.
A sprint está marcada como **pausada**, não concluída.

**Em andamento: M7.1 — fatia vertical de interface.** O detalhamento está em
[`10_ROADMAP_FRONTEND.md`](10_ROADMAP_FRONTEND.md); o andamento, no `09`.

O motivo da mudança: o risco "toda a interface concentrada na M7" estava aberto
desde a reorganização em MVP e Fase 2, e a mitigação registrada — exercitar o
`/api/v1/docs` — não mitigava o que importa. Contrato de API mostra que o endpoint
responde, não que a regra foi entendida como o estúdio precisa.

**O que a fatia antecipada permite demonstrar:** acesso, clientes, agenda com
prevenção de conflito e orçamento até a aprovação com percentual congelado. **O que
ela não permite:** sinal, pagamento, sessão executada e repasse. Das duas dores que
justificam o sistema, a demonstração resolve inteira a de choque de horário nas
macas e nenhuma parte da de saber quem recebe quanto.

**A etapa M7.1.1 está fechada.** Login em tela dividida, casca com barra lateral,
cliente HTTP com CSRF e tratamento central do 401, sessão, componentes base,
formatadores de fuso e dinheiro, e o mecanismo dos quatro estados de tela.

Os quatro critérios de aceite foram exercitados contra a API, não apenas lidos no
código: navegação diferente por perfil, 401 devolvendo ao login com o destino
preservado, **conta bloqueada respondendo 200 antes e 401 depois** do bloqueio sem
nova autenticação no meio, e o **mesmo cookie** recusado depois do logout — a sessão
deixa de existir no servidor, não só na interface.


**A linguagem visual foi definida em 28/09/2026**, a partir do monograma e de telas
de referência entregues pelo responsável: cromo escuro com área de trabalho clara,
barra lateral, rótulo em caixa alta sobre todo título, título de display grande,
tudo em pílula, cartão herói com uma única ação, e o ouro do monograma no lugar do
carmim da referência. Está registrada na seção 4.0 de
[`10_ROADMAP_FRONTEND.md`](10_ROADMAP_FRONTEND.md). O banner é a fotografia do
estúdio em `frontend/public/brand/studio.webp`, e o monograma vetorizado está em
`frontend/public/brand/logo.svg`.

**A etapa M7.1.2 entregou a tela de clientes** em 29/09/2026: lista, cadastro,
edição e alerta de duplicidade. A RN-CLI-004 foi verificada com dados reais — o
proprietário vê três clientes, cada residente vê apenas os que cadastrou.

O ambiente foi destravado e o `scripts/seed_demo.py` existe. Duas correções de
ambiente ficaram registradas: as portas publicadas mudaram para **5433** e
**8001**, para conviver com outro projeto na máquina, e a imagem do banco passou
a ser `postgres:17` em vez da variante alpine, que quebrava ao criar cluster novo.

**A etapa M7.1.3 está fechada.** A timeline de macas existe em `/schedule`:
macas no eixo Y, horas no eixo X, em CSS Grid sem biblioteca (ADR-004). Aprovar,
recusar com motivo de lista fechada e o **modal de conflito da RN-AGE-007**, que
não oferece caminho para ignorar. O maior risco de estimativa do frontend saiu do
caminho.

**A interface encontrou dois defeitos que nenhum teste pegava:**

1. O `409` de conflito não levava a reserva existente — o modal exigido pela
   RN-AGE-007 era impossível de construir, e nada acusava.
2. A API **não conseguia gravar agendamento nenhum**: `booking.session_id` aponta
   para `tattoo_session` e nenhum caminho de importação da aplicação carregava
   esse modelo. Os testes passavam porque o pytest carrega tudo no mesmo
   processo. Corrigido por `app/core/orm_registry.py` (ADR-026).

**A M7.1.3 foi fechada em duas partes**, e a primeira foi declarada concluída
antes de estar: cobria RN-AGE-001 a 007 e 014, mas deixava a RN-AGE-004 pela
metade e as RN-AGE-008, 009 e 010 de fora. A segunda parte fechou o que faltava,
conferindo tela a tela contra a seção 4 das regras.

O defeito mais sério estava na **RN-AGE-004**: duas solicitações no mesmo horário
se empilhavam e a de cima escondia a de baixo, então o gestor decidia sem saber
que havia concorrência.

**A etapa M7.1.4 fechou a fatia antecipada** em 29/09/2026: orçamentos e imagens
de referência em `/quotes`. Criar, editar, aprovar com o percentual congelado,
rejeitar com motivo, e anexar, listar e remover imagens pela rota autenticada.

**A regra que a tela precisava explicar, e explica:** editar um orçamento
aprovado o devolve a Pendente e descarta o percentual acordado (RN-ORC-003 e
RN-REP-006). O formulário avisa **antes** de salvar, com o percentual que será
perdido escrito no aviso. Verificado com dados reais: um orçamento aprovado a
70% voltou a Pendente com a participação zerada ao ter o valor total alterado.

**A M7.1.4 encontrou um defeito de interface:** decidido o orçamento, o modal
continuava no modo de decisão, oferecendo "Confirm approval" sobre algo já
aprovado — e o segundo clique voltava do servidor com "Only a pending quote can
be approved.", que quem acabara de aprovar lia como falha da própria aprovação.

**Interface: 83 testes.** Componentes base agora cobrem todo controle — nenhum
`<button>`, `<input>`, `<select>` ou `<textarea>` cru fora de
`shared/components`, com uma exceção declarada. Responsividade de celular e
tablet entregue.

**A etapa M4.4 fechou a M4** em 30/09/2026: as sessões existem, e com elas o ciclo
vai do orçamento aprovado à sessão concluída — a unidade sobre a qual a M6 vai
calcular repasse.

**As sessões nascem da aprovação, na mesma transação.** Orçamento aprovado sem
sessões não significa nada: ninguém tem o que marcar como realizado e o repasse
não tem sobre o que incidir. Na reaprovação, sessão já resolvida fica onde está e
só as agendadas são refeitas pelo plano novo.

**Realizada e concluída são estados diferentes, e é de propósito.** O artista
marca que a sessão aconteceu; o gestor confirma quanto entrou. Só depois das duas
a sessão vale para repasse (RN-ORC-005). Confirmar um valor diferente do informado
exige motivo, que fica na auditoria.

**Sessão parcial e o ajuste da RN-ORC-006 funcionam:** uma sessão de €250 cobrada
a €100 vira `PARTIALLY_DONE`, e quando o gestor refaz as restantes e o
comprometido deixa de fechar com o valor aprovado, o orçamento volta a Pendente
com o percentual congelado descartado.

**`CANCELLED` e `NO_SHOW` ficaram fora**, embora existam na tabela desde a M4.1:
quem os produz é o cancelamento e o não comparecimento do agendamento, cuja
consequência é financeira (RN-PAG-004) e pertence à M5.

**Backend: 172 testes.** Um defeito da própria suíte apareceu ao crescê-la — cada
teste montava um engine que ninguém devolvia, e o PostgreSQL passou a recusar
conexão com `too many clients`, derrubando treze testes sadios. `Database.dispose()`
existe por causa disso.

**A sprint M5 fechou em 30/09/2026, e com ela o portão do sinal.** Até então a
RN-AGE-005 e a RN-PAG-002 estavam escritas mas não valiam: `ApproveBooking` tinha
um `_deposit_is_confirmed` que devolvia `True` sempre. Aprovar um agendamento
agora exige pagamento confirmado.

As decisões desta sprint estão registradas como **ADR-027** (o sinal pertence ao
agendamento), **ADR-028** (agenda e financeiro se falam por portas declaradas pela
agenda) e **ADR-029** (o sistema retém sozinho e nunca devolve sozinho).

**O sinal pertence ao agendamento, não à sessão.** Foi a pergunta que a
documentação não fechava: a RN-PAG-001 diz "todo agendamento exigirá €50" e o
modelo só previa pagamento ligado a sessão ou a semana de guest — mas
`booking.session_id` é nulo em todo horário que não vem de orçamento. Decidido
com o usuário: o sinal é pago e recebido pelo estúdio para que o horário possa
ser confirmado, e a solicitação fica pendente até o gestor confirmar no sistema
que recebeu. `payment.booking_id` entrou no modelo por isso.

**Cliente próprio do guest não exige sinal** (RN-GST-004): esses valores não
passam pelo estúdio. O sistema reconhece o caso sem campo novo — o guest não
acessa orçamento (RN-ORC-001), então um agendamento de guest sem sessão ligada é
necessariamente cliente próprio dele.

**O sistema retém sozinho, mas nunca devolve sozinho.** Reter é escrituração: o
estúdio já está com o dinheiro e a RN-AGE-009 diz que ele fica, mesmo com aviso
de 24 horas. Devolver é movimento de caixa, e a RN-PAG-009 manda o gestor
registrar a devolução **depois de realizá-la**. O sistema aponta o que deve
voltar; não lança a saída por conta própria.

**Criar agendamento já aprovado mudou.** A RN-AGE-005 permite ao gestor criar em
Aprovada *"desde que confirmem o sinal"*, e o sinal pertence ao agendamento, que
não existe no instante da criação. O atalho passa a ser recusado onde há sinal a
confirmar e continua aberto onde a regra não o pede. O caminho é: criar,
confirmar o sinal, aprovar.

> **Pendência desta entrega.** A suíte inteira não completou num só comando: a VM
> do Docker desta máquina passou a somente-leitura no meio da execução e derrubou
> o container da API. As suítes de agenda (31 testes) e de financeiro (32)
> passaram depois da última alteração, com Ruff limpo. Falta rodar `pytest`
> inteiro depois de reiniciar o Docker.

**A etapa M7.2.1 fechou em 30/09/2026** — painel do gestor com o que está
esperando decisão, antecipada a pedido do estúdio.

O problema relatado: o gerente precisa abrir o calendário para descobrir se existe
solicitação de agendamento; se não abrir, não sabe, e se abrir e não reparar, passa
batido. A RN-AGE-012 já previa que "uma nova solicitação aparecerá no painel de
gerente e proprietário", e a seção 10.1 lista o conteúdo desse painel — nunca foi
construído, e o `HomeView` é marcador de lugar.

A área mostra as três origens da seção 10.1: solicitações de agendamento,
pagamentos aguardando confirmação e orçamentos pendentes. O contador fica na barra
lateral, visível em toda tela — é ele que resolve a dor, porque o problema é
justamente não estar no painel. Atualiza sozinho a cada minuto.

**Não há migração nem tabela nova.** Pendência é estado que já existe: agendamento
em `REQUESTED`, pagamento em `REPORTED`, orçamento em `PENDING`. A tabela
`notification` do modelo de dados serve à caixa interna com e-mail e é da sprint
F2, junto do worker.

No backend entraram três filtros por estado — `GET /bookings`, `GET /quotes` e o
novo `GET /payments` — e nada além disso. `BookingRepository.list_pending`, que
existia desde a M3 e nunca fora chamado, deu lugar ao filtro genérico.

**O ciclo de atualização mora no estado compartilhado**, e não na tela do painel:
se a tela carregasse, o contador só saberia de algo novo enquanto o gestor
estivesse no painel — justamente onde ele não está quando o problema acontece.
Quem liga e desliga o ciclo é a casca, que é onde se sabe quem entrou; o
residente não vê a fila do estúdio, e buscá-la para ele seria pedir um 403 por
minuto ao servidor.

**Conferido contra a aplicação rodando:** um sinal foi confirmado pela API, sem
tocar na tela, e o contador caiu de 4 para 3 em 20 segundos. Como residente, zero
requisições em 15 segundos de observação.

**Próximo passo:** sprint M6 — repasses e fechamento semanal. Cálculo por sessão,
fechamento de sexta às 20h `Europe/Dublin`, demonstrativo do artista e ajustes
negativos de devolução posterior (RN-REP-003 a RN-REP-007).

## Estado de aprovação e limite de trabalho

**A implementação foi autorizada em 24/09/2026.** A pergunta "Arquitetura aprovada.
Posso iniciar a implementação?" foi respondida e a Fase 14 abriu o desenvolvimento.
Escrever código deixou de ser proibido.

O que continua valendo, sprint após sprint:

- **Aprovação é por sprint e por etapa, não geral.** Discutir não é autorizar;
  planejar não é autorizar. Antes de aprovação explícita não se altera arquivo,
  banco ou dependência. As palavras que liberam estão em `CLAUDE.md`, seção 2.
- **Dependência nova exige autorização própria**, caso a caso. `pwdlib` foi
  autorizada assim (ADR-010).
- Não assumir requisito. Dúvida crítica se pergunta antes de propor solução.
- Arquitetura já registrada não muda sem explicar o impacto, apresentar
  alternativa e obter aprovação.

## Orientação para a próxima IA

Leia este arquivo e depois os documentos `01` a `08` conforme a necessidade. **Não
varra o repositório nem repita perguntas já resolvidas** — a documentação é mantida
atualizada justamente para evitar isso.

O desenho está completo. Se a implementação ainda não tiver sido aprovada, o único
passo pendente é obter a aprovação da Fase 14. Se tiver sido aprovada, siga o plano
de implementação por etapas, respeitando:

- uma classe própria do projeto por arquivo, sem exceção;
- Clean Code e SOLID, com regras de negócio fora de rotas, schemas e tarefas;
- reutilização dos módulos e variáveis já definidos, criando o novo sempre alinhado
  ao padrão vigente;
- execução sempre em containers Docker, nunca no host;
- PostgreSQL real nos testes, nunca SQLite, por causa de `tstzrange` e `EXCLUDE`;
- atualização da documentação na mesma entrega da mudança.

Nunca alterar arquitetura já registrada sem explicar o impacto, apresentar
alternativa e obter aprovação explícita.
