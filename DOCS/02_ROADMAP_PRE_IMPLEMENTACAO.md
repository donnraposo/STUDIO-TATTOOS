# Roadmap de Descoberta e Validação Pré-Implementação

**Status:** Concluído. As catorze fases foram encerradas e a implementação foi
autorizada em 24/09/2026; o andamento da construção fica em
`09_ROADMAP_IMPLEMENTACAO.md`.  
**Última atualização:** 26/09/2026  
**Objetivo:** eliminar lacunas funcionais, financeiras e operacionais antes da arquitetura definitiva e do início do desenvolvimento.

## 1. Princípios do processo

- Nenhum código será iniciado enquanto as regras críticas estiverem pendentes.
- Cada decisão será registrada na documentação Markdown da pasta `DOCS`.
- Regras aprovadas substituirão explicitamente versões anteriores quando houver mudança.
- Cada fase terá um critério de saída verificável.
- A implementação dependerá da aprovação final da arquitetura pelo usuário.

## 2. Visão geral

| Fase | Tema | Situação |
|---|---|---|
| 0 | Consolidação das regras já definidas | Concluída |
| 1 | Contexto operacional do estúdio | Concluída |
| 2 | Usuários, acessos e segurança | Concluída |
| 3 | Clientes e proteção de dados | Concluída |
| 4 | Agenda, macas e disponibilidade | Concluída |
| 5 | Orçamentos, sessões e atendimento | Concluída |
| 6 | Pagamentos, cancelamentos e devoluções | Concluída |
| 7 | Repasses e fechamento semanal | Concluída |
| 8 | Operação dos guests | Concluída |
| 9 | Pós-venda e notificações | Concluída |
| 10 | Painéis, relatórios e auditoria | Concluída |
| 11 | Requisitos não funcionais | Concluída |
| 12 | Modelo de dados e arquitetura | Concluída |
| 13 | Plano de testes e critérios de aceite | Concluída |
| 14 | Aprovação para implementação | **Aprovada em 24/09/2026** |

## 3. Fase 0 — Consolidar decisões existentes

### Objetivo

Manter uma fonte única para todas as regras já acordadas.

### Entregável

- `01_REGRAS_DE_NEGOCIO.md`.

### Critério de saída

- Perfis, agenda, sinal, pagamentos, repasses, guest e pós-venda registrados sem contradições conhecidas.

### Situação

Concluída.

## 4. Fase 1 — Definir o contexto operacional

### Decisões aprovadas

- O sistema atenderá somente o estúdio de Cork City nesta versão.
- O fuso horário será `Europe/Dublin`, com ajuste automático do horário de verão.
- A moeda será o euro (€).
- O idioma inicial da interface será inglês.
- O funcionamento padrão será de terça-feira a domingo, das 10h às 20h.
- Segunda-feira será o dia padrão de fechamento.
- O estúdio começará com 4 macas.
- Todas as macas seguirão o mesmo horário-base.
- Gerentes e proprietários poderão adicionar macas.
- Gerentes e proprietários poderão abrir ou bloquear horários excepcionalmente.

### Dependências

Nenhuma.

### Riscos cobertos

- Notificações enviadas no horário incorreto.
- Reservas abertas em períodos sem funcionamento.
- Cálculos financeiros inconsistentes.

### Critério de saída

- Calendário-base, moeda, localidade e recursos físicos definidos.

### Situação

Concluída.

## 5. Fase 2 — Fechar usuários, acessos e segurança

### Decisões aprovadas

- Proprietário controla todos os perfis; gerente administra somente residentes e guests.
- Gerente não altera perfis nem promove usuários.
- Proprietário e gerente podem também atuar como tatuadores.
- Artistas podem solicitar o próprio cadastro, sujeito a autorização.
- Residentes e guests podem ser adicionados diretamente por gerente ou proprietário.
- Login será feito com e-mail e senha, sem autenticação em dois fatores.
- Recuperação de senha ocorrerá por link temporário enviado por e-mail.
- Bloqueio encerra o acesso, mas preserva dados e agendamentos futuros para tratamento administrativo.
- O último proprietário ativo não pode ser bloqueado.
- Alterações relevantes de usuários ficam registradas no histórico.

### Dependências

- Perfis de acesso já definidos nas regras de negócio.

### Riscos cobertos

- Elevação indevida de permissões.
- Perda de rastreabilidade em alterações financeiras.
- Agendamentos órfãos após o bloqueio de um artista.

### Critério de saída

- Nenhuma ação sensível sem responsável e permissão definidos.

### Situação

Concluída.

## 6. Fase 3 — Fechar clientes e proteção de dados

### Decisões aprovadas

- Nome e telefone serão obrigatórios; Instagram será opcional.
- O sistema alertará possíveis duplicidades por telefone ou Instagram.
- Tatuadores verão o cadastro completo somente dos clientes que cadastraram.
- Um artista indicado para outro cliente verá apenas nome, telefone e Instagram no próprio agendamento.
- Gerente e proprietário verão todos os clientes e poderão unir duplicidades.
- Históricos financeiros e de atendimento não poderão ser apagados diretamente.
- Não haverá exclusão automática imediata.
- Registros financeiros serão mantidos por pelo menos seis anos.
- Cadastros inativos serão revisados periodicamente depois de seis anos.
- Pedidos de acesso, correção ou exclusão serão tratados por gerente ou proprietário.
- Consentimentos, questionários de saúde e autorizações de imagem permanecem fora do escopo inicial.

### Dependências

- País de operação.

### Riscos cobertos

- Exposição de dados pessoais e fotos.
- Clientes duplicados com históricos financeiros diferentes.
- Classificação incorreta da origem do atendimento.

### Critério de saída

- Cadastro, vínculo, visibilidade, retenção e exclusão definidos.

### Situação

Concluída.

## 7. Fase 4 — Fechar agenda, macas e disponibilidade

### Decisões aprovadas

- O artista define livremente o horário inicial e final; não existem blocos fixos nem pausa obrigatória.
- A agenda impede sobreposição real de intervalos na mesma maca.
- Gerente e proprietário podem abrir horários excepcionais e bloquear uma maca ou todo o estúdio.
- Solicitações pendentes concorrentes continuam visíveis até a decisão administrativa.
- Após uma aprovação, solicitações conflitantes não podem ser aprovadas e devem ser rejeitadas com devolução aplicável.
- Residente e guest sempre solicitam; gerente e proprietário podem criar um agendamento diretamente aprovado.
- Remarcações são efetivadas somente por gerente ou proprietário.
- Artistas recebem por e-mail as decisões e alterações de agenda.
- O cliente é contatado fora do sistema nesta versão.
- Extensões e conflitos causados por atraso são resolvidos manualmente por gerente ou proprietário.

### Dependências

- Horário de funcionamento e quantidade de macas.
- Matriz de permissões.

### Riscos cobertos

- Dupla reserva.
- Reserva fora do expediente.
- Solicitações concorrentes sem resolução clara.

### Critério de saída

- Todos os estados e transições do agendamento definidos, incluindo exceções.

### Situação

Concluída.

## 8. Fase 5 — Fechar orçamentos, sessões e atendimento

### Decisões aprovadas

- Residentes, gerentes e proprietários podem criar orçamentos; guest não acessa o módulo.
- Orçamentos permanecem pendentes até aprovação ou rejeição manual de gerente ou proprietário.
- Não existe expiração automática.
- Alterar um orçamento aprovado faz com que ele volte ao estado pendente.
- Um orçamento registra descrição, região, tamanho, referências, valores e planejamento das sessões.
- Cada sessão exige seu próprio sinal de €50, incluído no valor total.
- O artista confirma a realização e o gestor confirma o valor recebido.
- Apenas sessões realizadas e com pagamento confirmado são concluídas e entram no repasse.
- Sessões parciais geram repasse somente sobre o valor efetivamente recebido.
- Alteração do valor total exige nova aprovação do orçamento.

### Dependências

- Permissões e fluxo da agenda.

### Riscos cobertos

- Repasse sobre sessão não realizada.
- Divergência entre orçamento, valor recebido e trabalho executado.

### Critério de saída

- Jornada completa entre orçamento, agendamento, sessão e conclusão definida.

### Situação

Concluída.

## 9. Fase 6 — Fechar pagamentos, cancelamentos e devoluções

### Decisões aprovadas

- Pagamentos serão inseridos e tratados manualmente por gerente ou proprietário.
- Depósito, dinheiro e cartão serão apenas formas registradas; não haverá integração de cobrança nesta versão.
- Taxas externas de cartão serão absorvidas pelo estúdio.
- Pagamentos poderão ser informados, confirmados, recusados, devolvidos ou estornados.
- Lançamentos nunca serão apagados; correções serão feitas por ajuste vinculado.
- Cada sessão será quitada integralmente, sem parcelamento adicional além do sinal e do saldo.
- O repasse será liberado somente após realização e quitação integral da sessão.
- Devoluções serão registradas manualmente e vinculadas ao pagamento original.
- A forma de devolução poderá ser diferente da forma original.

### Dependências

- Fluxo do agendamento e do atendimento.

### Riscos cobertos

- Repasse de valor ainda não recebido.
- Estorno sem rastreabilidade.
- Diferença entre caixa e registros do sistema.

### Critério de saída

- Cada entrada, devolução e correção possuir origem, estado e responsável.

### Situação

Concluída.

## 10. Fase 7 — Fechar repasses e fechamento semanal

### Decisões aprovadas

- O fechamento ocorrerá às 20h de sexta-feira no fuso `Europe/Dublin`.
- Somente sessões realizadas e integralmente quitadas entrarão no fechamento.
- Gerente ou proprietário confirmará manualmente a transferência ao artista.
- Devolução posterior a um repasse pago gerará ajuste negativo no fechamento seguinte.
- Alterações de percentuais serão aplicadas somente a novos orçamentos.
- Atendimentos aprovados guardarão o percentual vigente na aprovação.
- O cálculo será feito por sessão e arredondado para duas casas decimais.
- O demonstrativo exibirá sessões, valores, percentuais, ajustes e total líquido.
- O comprovante de transferência será opcional.

### Dependências

- Pagamentos e sessões concluídas.

### Riscos cobertos

- Pagamento duplicado ao artista.
- Percentual aplicado retroativamente de forma indevida.
- Saldo negativo após devolução posterior.

### Critério de saída

- Fechamento semanal reproduzível e auditável com exemplos aprovados.

### Situação

Concluída.

## 11. Fase 8 — Fechar a operação dos guests

### Decisões aprovadas

- O guest solicita cadastro com os mesmos dados básicos do artista e depende de autorização.
- A taxa será de €600 por semana, de sábado a sexta-feira.
- Reservas futuras exigem pagamento antecipado da semana correspondente.
- O guest poderá pagar uma ou várias semanas antecipadamente.
- Cada semana será controlada separadamente.
- Sem semana atual ou futura paga, o guest não terá acesso.
- Semanas consecutivas manterão o acesso sem interrupção.
- Devolução ou transferência da semana dependerá de decisão de gerente ou proprietário.
- Clientes próprios pagarão diretamente ao guest.
- Indicações do estúdio serão pagas ao estúdio e divididas em 50%/50%.

### Dependências

- Usuários, agenda e pagamentos.

### Riscos cobertos

- Guest reservar período não pago.
- Perda de acesso antes do fim do período contratado.
- Histórico inacessível após inativação.

### Critério de saída

- Todo o ciclo entre cadastro, pagamento, acesso, renovação e inativação definido.

### Situação

Concluída.

## 12. Fase 9 — Fechar pós-venda e notificações

### Decisões aprovadas

- Cada sessão gera um pós-venda 15 dias depois da realização.
- A lista será enviada diariamente às 08h para o gerente e, opcionalmente, para o proprietário.
- O e-mail exibirá dados de contato, artista, sessão, atraso e link, sem fotos ou observações.
- Falhas de envio serão registradas sem alterar o estado do pós-venda.
- Haverá uma área exclusiva com pendentes, atrasados, concluídos, busca e filtros.
- Gerente e proprietário editarão e concluirão; residente terá consulta limitada; guest não terá acesso.
- Resultados de contato serão padronizados.
- Novo acompanhamento manterá o item pendente com nova data.
- Somente gerente e proprietário anexarão ou removerão fotos.
- Pós-venda concluído poderá ser reaberto com motivo e nova data.

### Dependências

- Fuso horário, clientes, sessões e permissões.

### Riscos cobertos

- Acompanhamento vencido sem alerta.
- Foto vinculada à sessão incorreta.
- Conclusão sem histórico do responsável.

### Critério de saída

- Geração, envio, consulta, conclusão, correção e auditoria definidos.

### Situação

Concluída.

## 13. Fase 10 — Definir painéis, relatórios e auditoria

### Decisões aprovadas

- Painéis distintos para proprietário/gerente, residente e guest.
- Indicadores do painel para cada perfil estão listados em `01_REGRAS_DE_NEGOCIO.md`.
- Proprietário e gerente terão relatórios operacionais e financeiros.
- Relatórios terão filtros por período, artista e estado.
- Comparação poderá mostrar período atual versus anterior ou dois períodos escolhidos.
- Comparação inclui faturamento bruto, receita líquida, repasses, taxas semanais, sinais retidos, devoluções, artistas e origem de clientes, com variação em valor e percentual.
- Relatórios poderão ser exportados para PDF e Excel.
- Residentes verão somente a própria produção e repasses; guests verão somente repasses de indicações do estúdio.
- Proprietário verá todo o histórico de auditoria; gerente verá ações operacionais e financeiras, sem alterações administrativas relativas a contas de proprietário.
- Residentes e guests não verão auditoria.
- Registros de auditoria serão imutáveis e filtráveis por usuário, ação, módulo e período, mostrando data/hora, responsável, ação e valores anteriores/novos quando aplicável.

### Pontos ainda pendentes

Nenhum. Fórmulas, retenção de auditoria e critérios de homologação foram definidos.

### Dependências

- Todos os fluxos operacionais e financeiros.

### Riscos cobertos

- Relatórios com conceitos financeiros diferentes das regras aprovadas.
- Exposição de faturamento a perfis sem permissão.

### Critério de saída

- Cada indicador possuir definição, fonte, filtro e público autorizado.

### Situação

Concluída.

## 14. Fase 11 — Definir requisitos não funcionais

### Decisões aprovadas

- Primeira versão web responsiva para computador, tablet e celular.
- Acesso necessário 24 horas por dia.
- Planejar até 15 usuários simultâneos.
- Telas comuns até 3 segundos; relatórios comuns até 10 segundos em condições normais.
- Backups automáticos e criptografados, retidos por 30 dias, com teste trimestral de restauração.
- Conexões e dados armazenados terão proteção técnica básica.
- Não é obrigatório hospedar em uma região geográfica específica.
- Sessão expira após 60 minutos sem atividade ou 12 horas totais.
- O serviço de e-mail será definido na arquitetura; falhas ficam registradas e podem ser reenviadas.
- A primeira versão será instalável como PWA; notificações push no aparelho ficam para uma versão futura.

### Dependências

- Contexto operacional e requisitos legais.

### Riscos cobertos

- Perda de dados.
- Acesso indevido.
- Aplicação inadequada para uso móvel no estúdio.

### Critério de saída

- Metas mensuráveis de segurança, recuperação, desempenho e compatibilidade.

### Detalhes técnicos para a arquitetura

- Frequência exata do backup;
- Objetivo de perda máxima de dados e tempo de recuperação;
- Serviço de e-mail;
- Provedor e região de hospedagem, sem restrição geográfica imposta;
- Definição operacional de condições normais para as metas de desempenho.

### Situação

Concluída em alto nível. Parâmetros de implementação serão escolhidos na Fase 12.

## 15. Fase 12 — Produzir o desenho funcional e a arquitetura

### Entregáveis previstos

- Visão consolidada do projeto.
- Matriz final de perfis e permissões.
- Catálogo de regras de negócio revisado.
- Fluxos e estados de agenda, orçamento, pagamento, repasse e pós-venda.
- Modelo de dados e relacionamentos.
- Arquitetura do sistema e fluxo de informações.
- Estrutura prevista de módulos e arquivos.
- Registro das decisões arquiteturais e alternativas avaliadas.
- Roadmap técnico de implementação.

### Dependências

- Fases 1 a 11 concluídas.

### Riscos cobertos

- Arquitetura baseada em regras incompletas.
- Retrabalho estrutural durante o desenvolvimento.

### Critério de saída

- Solução técnica cobre todas as regras aprovadas e não possui dúvida bloqueadora.

### Decisões técnicas alinhadas em 23/09/2026

- Backend Python com FastAPI; banco PostgreSQL; execução dos componentes em containers Docker.
- Frontend Vue 3, TypeScript e Vite.
- Primeira versão responsiva e instalável como PWA; notificações push no aparelho ficam para o futuro.
- Frontend e API no mesmo domínio, com a API sob `/api/v1`.
- Site/PWA usará cookie seguro com sessão validada e revogável no servidor; JWT não será usado como sessão principal do navegador nesta versão.
- Tentativas bloqueadas por conflito na agenda do mesmo artista gerarão notificação interna e e-mail para gerente e proprietário.
- A regra de não sobreposição do mesmo artista vale entre macas e considera solicitações pendentes e agendamentos aprovados; pendências de artistas diferentes continuam podendo concorrer pela mesma maca.
- Ver detalhes, decisões pendentes e riscos em `04_ARQUITETURA_TECNICA.md`.

### Entregáveis produzidos em 24/09/2026

- `05_MODELO_DADOS.md` — entidades, relacionamentos e as restrições `EXCLUDE` que
  garantem as duas regras de não sobreposição no próprio banco.
- `06_ESTRUTURA_PROJETO.md` — árvore de pastas, nove módulos, camadas internas,
  contratos de API e topologia de containers.
- `08_DECISOES_ARQUITETURA.md` — catorze decisões registradas com motivo e
  alternativas avaliadas.

### Decisões fechadas com o responsável

- Numeração da documentação preservada; complementada de `05` a `08` (ADR-014).
- Hospedagem em VPS único com Docker Compose (ADR-005).
- Agenda timeline construída sem biblioteca licenciada (ADR-004).
- E-mail transacional e armazenamento de arquivos por serviços gerenciados (ADR-006).

### Situação

Concluída. As pendências remanescentes, listadas em `04_ARQUITETURA_TECNICA.md` §9,
não bloqueiam a implementação: provedor específico de e-mail, metas de RPO/RTO,
atualização da caixa de notificações e parâmetros de limite de login.

## 16. Fase 13 — Preparar testes e critérios de aceite

### Entregáveis previstos

- Cenários de aceite por módulo.
- Testes de permissões por perfil.
- Casos de conflito de agenda.
- Casos financeiros com sinal, pagamento parcial, cancelamento, devolução e repasse.
- Casos de ativação e expiração de guest.
- Casos de pós-venda e falha de notificação.
- Critérios para homologação do usuário.

### Dependências

- Arquitetura e fluxos aprovados.

### Situação

Concluída em 24/09/2026. Entregue em `07_PLANO_TESTES.md`, cobrindo testes
unitários, integração, concorrência, matriz de permissões, cenários financeiros,
segurança, pós-venda, ponta a ponta, desempenho, recuperação e critérios de
homologação.

### Critério de saída

- Cada regra crítica possuir pelo menos um cenário de sucesso e um de exceção.

## 17. Fase 14 — Aprovação final

Antes de qualquer código:

1. Revisar todas as pendências.
2. Confirmar regras, telas, dados, arquitetura e testes.
3. Registrar decisões finais.
4. Apresentar os arquivos previstos para implementação.
5. Solicitar autorização explícita com a pergunta:

> Arquitetura aprovada. Posso iniciar a implementação?

Somente uma resposta clara de aprovação liberará a criação ou alteração de código.

## 18. Ordem recomendada para as próximas conversas

1. Concluir o desenho funcional, o modelo de dados e a arquitetura na Fase 12.
2. Preparar critérios de aceite e testes na Fase 13.
3. Apresentar a proposta completa e solicitar aprovação explícita antes de qualquer código na Fase 14.
