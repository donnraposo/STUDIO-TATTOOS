# Contexto do Projeto e Continuidade para Próxima IA

**Última atualização:** 23/09/2026  
**Idioma desta documentação:** português  
**Idioma planejado da interface:** inglês  
**Estado geral:** descoberta e validação funcional em andamento; nenhuma implementação de software foi autorizada.

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
- Execução: componentes containerizados com Docker.
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

**Sprint M3 — Agenda e macas: em andamento**, etapa 1 de 3.

**A etapa M3.1 retirou o maior risco técnico do projeto.** As duas restrições
`EXCLUDE` estão no banco e comprovadas por oito testes, incluindo uma corrida com
duas transações paralelas reais. A maca só é bloqueada por agendamento aprovado;
o artista é bloqueado também por pendência, inclusive entre macas diferentes.

A partir daqui, conflito de agenda é impossível por construção: nem a aplicação
nem uma consulta manual conseguem gravar sobreposição.

**Próximo passo:** etapa M3.2 — casos de uso de solicitar, aprovar e rejeitar,
agora sobre uma fundação que não pode ser burlada. Depois a M3.3, com remarcação,
cancelamento e bloqueios de maca e horário.

## Estado de aprovação e limite de trabalho

- O usuário pediu documentação completa em Markdown dentro da pasta `DOCS`.
- O usuário pediu explicitamente para documentar as decisões técnicas alinhadas; alterações realizadas permanecem restritas à documentação.
- Essa autorização cobre documentação e análise. **Não existe autorização para escrever código, instalar dependências ou implementar o sistema.**
- Não começar implementação ao concluir arquitetura sem perguntar e aguardar aprovação explícita.
- A aprovação final esperada é uma resposta clara à pergunta: “Arquitetura aprovada. Posso iniciar a implementação?”

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
