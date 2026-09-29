# Plano de Testes e Critérios de Aceite

**Status:** Aprovado. Execução em andamento junto com as sprints.
**Última atualização:** 26/09/2026

> Corresponde à Fase 13 de `02_ROADMAP_PRE_IMPLEMENTACAO.md`. Cada regra crítica
> tem ao menos um cenário de sucesso e um de exceção.

## 0. Cobertura atual

**172 testes aprovados** no backend, executados em container contra PostgreSQL real
no banco isolado `tattoo_studio_test`.

> **A suíte devolve as conexões entre testes.** Cada teste monta um `Container`
> próprio, com engine próprio, e o pool não se fechava sozinho: ao passar de cento
> e poucos testes o PostgreSQL começou a recusar com `sorry, too many clients
> already`, derrubando treze testes que não tinham defeito nenhum. É o tipo de
> falha que acusa o inocente, porque o culpado é o acúmulo. `Database.dispose()`
> existe por isso e o `conftest` o chama no encerramento de cada teste.

**83 testes aprovados** no frontend, em Vitest dentro do container, sobre classes
puras — sem montar componente e sem dependência nova. O que se testa ali é o que
tem chance real de estar errado: fuso horário, aritmética de dinheiro, formatação,
tradução de erro da API e ciclo de sessão.

| Área | Situação |
|---|---|
| Saúde e prontidão | Coberta |
| Auditoria append-only | Coberta, inclusive como role dona da tabela |
| Autenticação e sessão | Coberta: credencial inválida, e-mail inexistente indistinguível, conta bloqueada, conta pendente, `HttpOnly`, expiração por inatividade e absoluta |
| CSRF | Coberta: sem cabeçalho, com token divergente e com token correto |
| **Concorrência de agenda** | ✅ **Coberta.** Inclui corrida com duas transações paralelas reais |
| Permissões de gestão de contas | Coberta: matriz completa dos quatro perfis, mais o caso do último proprietário ativo |
| Fluxo de agenda | Coberta: solicitar, aprovar, rejeitar, cancelar, não comparecer, remarcar, com conflito devolvendo 409 |
| Visibilidade de clientes | Coberta: os três níveis da RN-CLI-004, alerta de duplicidade e união preservando histórico |
| **Integridade de orçamento e sessão** | Coberta por 11 testes de restrição na migração `0005`: aprovado sem percentual congelado, rejeitado sem motivo, sequência duplicada, parcial sem valor cobrado, realizada sem data real, quitada sem confirmação do gestor e dois agendamentos vivos na mesma sessão |
| **Ciclo da sessão** | Coberta: aprovação gerando as sessões previstas com origem e percentual congelados, orçamento pendente sem sessão nenhuma, reaprovação mantendo a realizada e refazendo só as agendadas, artista marcando realizada, artista de fora recebendo 403, parcial registrando o cobrado, parcial com valor igual ao previsto recusada, artista sem confirmar recebimento, gestor confirmando e concluindo, sessão agendada não confirmável, correção de valor sem motivo recusada e com motivo gravada na auditoria, e sessão quitada não podendo ser remarcada |
| **Ajuste das sessões restantes** | Coberta: artista sem ajustar, ajuste que mantém o total deixando o orçamento aprovado, ajuste que muda o total devolvendo a Pendente com o percentual descartado, o cobrado de uma parcial entrando na conta no lugar do previsto, sessão de valor zero recusada, e artista de fora sem ver as sessões |
| **Aritmética das sessões** | Coberta por 8 testes de classe pura: sequência continuando depois do que já foi resolvido, plano que encolheu abaixo do executado não pedindo sessão nenhuma, soma do cobrado com o previsto, e três sessões de €133,33 fechando €399,99 exatos |
| **Ciclo do orçamento** | Coberta: guest sem acesso, residente não aprova, percentual congelado em 70 e em 50 conforme a origem, correção de percentual pelo gestor registrada na auditoria, edição de aprovado voltando a pendente e limpando o percentual, recusa sem motivo, reaprovação bloqueada e visibilidade entre artistas |
| **Imagens de referência** | Coberta: leitura sem sessão devolvendo 401, artista de fora recebendo 403 em listar, ler e anexar, imagem de um orçamento não saindo por outro, tipo não aceito, arquivo acima de 10 MB, arquivo vazio, limite de 10 por orçamento, anexar não reabrindo aprovação, residente sem anexar em aprovado e remoção apagando o arquivo |
| **Armazenamento em sistema de arquivos** | Coberta no adaptador: ida e volta dos bytes, criação da árvore de diretórios, sobrescrita sem deixar o temporário, leitura de chave ausente como erro de domínio, remoção repetida sem erro e chave tentando escapar da raiz nos três formatos |
| **Fuso do estúdio no frontend** | Coberta: horário de verão e horário padrão, mesmo instante escrito com deslocamentos diferentes, e minutos desde a meia-noite atravessando a virada. Uma agenda deslocada por uma hora parece correta na tela, e é por isso que tem teste |
| **Cliente HTTP do frontend** | Coberta: CSRF ausente na leitura e presente na escrita, cookie de sessão enviado, 401 avisando a aplicação, 409 marcado para o modal de conflito, mensagem de campo extraída do erro de validação, corpo de erro que não é JSON e resposta vazia no `DELETE` |
| **Sessão no frontend** | Coberta: reconhecimento pelo cookie, sessão expirada, API fora do ar sem impedir a aplicação de montar, e saída que só esquece o usuário depois de o servidor encerrar |
| **Cliente de API de clientes** | Coberta: tradução da listagem, alerta de duplicidade vindo junto do cliente criado, e o reconhecimento das **duas** formas que o detalhe devolve conforme a RN-CLI-004 |
| **Formatação de dinheiro** | Coberta: texto decimal da API, duas casas sempre, e traço em vez de `NaN` quando o valor é nulo — que é o caso do orçamento pendente |
| Financeiro, pós-venda, ponta a ponta | Pendentes, conforme as sprints correspondentes |
| **Solicitações concorrentes na timeline** | Coberta por 6 testes de classe pura: duas pendências no mesmo horário vão para trilhas diferentes e ambas aparecem (RN-AGE-004); agendamento que começa quando outro termina divide a trilha, porque encostar não é sobrepor (RN-AGE-001); trilha liberada é reaproveitada |
| **Contas que podem receber agendamento** | Coberta: conta bloqueada fica de fora — agendar para ela criaria compromisso que a própria pessoa não veria (RN 2.5) —, gerente que não tatua também, e proprietário que tatua entra |
| **Posicionamento na timeline** | Coberta por 9 testes de classe pura: coluna e extensão, fuso do estúdio contra fuso do navegador, aparo nas duas bordas do expediente, meia-noite como fim do dia, e sessão curta que não pode colapsar para largura zero |
| **Corpo do conflito de agenda** | Coberta: o 409 leva `scope` e o identificador da reserva existente, e um erro de domínio comum continua devolvendo apenas `detail` — a extensão é por dados, não um formato novo imposto a toda resposta de erro |
| **Recorte por intervalo na agenda** | Coberta no backend: agendamento que atravessa a borda do recorte continua aparecendo, outro dia fica de fora, meia janela e janela invertida são recusadas |
| **Permissões de exibição** | Coberta: os quatro perfis, e o caso que justifica o arquivo — o guest **tatua**, então qualquer verificação por "atua como artista" o deixaria entrar nos orçamentos, que a RN-ORC-001 lhe nega |
| **Rascunho de orçamento** | Coberta por 11 testes de classe pura: os limites de cada campo repetindo o `QuoteFieldsRequest`, recusa de `1e3`, `10,50` e três casas decimais num campo de dinheiro, e **a soma das sessões em centavos inteiros** — três sessões de €133,33 fecham exatos €399,99, que em ponto flutuante dariam 399.99000000000007 e fariam a tela acusar diferença onde não há |
| **Apresentação do orçamento** | Coberta: os três estados com o tom certo, as duas origens, e o percentual padrão de cada uma — 70% para cliente próprio, 50% para indicação (RN-REP-001 e RN-REP-002) |
| **Cliente de API de orçamentos** | Coberta: tradução da listagem, cliente e artista presentes na criação e **ausentes na edição** (reatribuir não é editar), percentual congelado chegando como texto, e o envio de imagem como multipart sem `Content-Type` definido à mão — defini-lo produz um corpo que o servidor não consegue separar |
| **Tamanho de arquivo** | Coberta: múltiplos de 1024 como o sistema operacional mostra, byte inteiro sem casa decimal, e traço em vez de `NaN` |
| **Aceite da M7.1.1** | ✅ Os quatro critérios exercitados contra a API: navegação por perfil, 401 devolvendo ao login, conta bloqueada perdendo acesso na requisição seguinte e logout encerrando a sessão no servidor |

## 1. Estratégia

Prioridade para **permissões, concorrência de agenda e consistência financeira** —
as três áreas onde um defeito causa prejuízo real ou vazamento de dados.

Todos os testes rodam em container. **PostgreSQL real é obrigatório**: SQLite não
suporta `tstzrange` nem restrições `EXCLUDE`, que são justamente a garantia central
da agenda. Testar contra SQLite daria falsa aprovação.

| Camada | Ferramenta |
|---|---|
| Unitário e integração | pytest |
| API | pytest + httpx |
| Frontend unitário | Vitest |
| Jornada ponta a ponta | Playwright |

## 2. Testes unitários

- Cálculo de repasse 70/30 e 50/50, com arredondamento a duas casas.
- Repasse proporcional em sessão parcial, sobre o valor efetivamente recebido.
- Retenção do sinal em cancelamento, não comparecimento e remarcação fora de 24h.
- Devolução do excedente acima do sinal.
- Cálculo da semana de guest, sábado a sexta, em `Europe/Dublin`.
- Fronteira do fechamento: sexta às 20h, incluindo o horário de verão.
- Vencimento do pós-venda em 15 dias a partir da data real da sessão.
- Indicadores de relatório: faturamento bruto, receita líquida, sinal sem duplicidade.
- Políticas de autorização por perfil, como funções puras.

## 3. Testes de integração

- Repositórios contra PostgreSQL real.
- Transação de confirmação de pagamento e conclusão de sessão.
- Geração do fechamento semanal com ajustes negativos de devolução posterior.
- Congelamento do percentual na aprovação do orçamento.
- Revogação de sessões ao bloquear conta e ao trocar senha.
- Gravação em `audit_log` nas ações administrativas e financeiras.
- Outbox: gravação na transação de negócio e consumo pelo worker.

## 4. Testes de concorrência — obrigatórios

Estes são os cenários que só o banco pode garantir.

| Cenário | Resultado esperado |
|---|---|
| Duas aprovações simultâneas para a mesma maca no mesmo intervalo | Uma aprova, a outra falha com conflito. Nunca duas aprovadas |
| Dois agendamentos simultâneos do mesmo artista em macas diferentes, horários sobrepostos | Um é criado, o outro é impedido (RN-AGE-014) |
| Solicitações pendentes de artistas diferentes na mesma maca e horário | Ambas são aceitas e concorrem (RN-AGE-004) |
| Confirmação repetida do mesmo pagamento | Efeito único, sem duplicar repasse |
| Execução dupla do fechamento semanal | Um único `payout` por artista e período |
| Reinício do worker durante envio | E-mail não se perde nem duplica, pela `idempotency_key` |

O teste de conflito deve abrir **duas transações reais em paralelo**, não chamadas
sequenciais — chamadas em sequência passariam mesmo com a validação quebrada.

## 5. Testes de permissão — matriz positiva e negativa

Para cada endpoint, testar os quatro perfis e o não autenticado.

| Regra | Cenário negativo obrigatório |
|---|---|
| Gerente não altera perfis nem promove usuários | Tentativa devolve 403 |
| Gerente não bloqueia proprietário ou outro gerente | Tentativa devolve 403 |
| Último proprietário ativo não pode ser bloqueado | Tentativa devolve erro de negócio |
| Residente vê ficha completa só de clientes que cadastrou | Acesso a cliente de terceiro devolve 403 ou projeção reduzida |
| Artista indicado vê só nome, telefone e Instagram | Histórico anterior não aparece na resposta |
| Guest não acessa orçamentos nem pós-venda | Tentativa devolve 403 |
| Guest só reserva dentro de semana paga e ativa | Reserva fora da semana é recusada |
| Residente não edita nem conclui pós-venda | Tentativa devolve 403 |
| Residente e guest não acessam auditoria | Tentativa devolve 403 |
| Gerente não vê auditoria administrativa de conta de proprietário | Registro não aparece na listagem |
| Residente vê apenas a própria produção nos relatórios | Dados de outro artista não retornam |

## 6. Testes financeiros

| Cenário | Verificação |
|---|---|
| Sessão de €100, cliente próprio de residente | Artista €70, estúdio €30; sinal de €50 contado uma vez |
| Tatuagem de €10.000 em quatro sessões de €2.500 | Percentual aplicado por sessão recebida |
| Cancelamento com €100 pré-pagos | Estúdio retém €50, devolve €50, artista não recebe |
| Não comparecimento | Mesma retenção, sem repasse |
| Remarcação com mais de 24h | Valores transferidos para o novo agendamento |
| Remarcação com menos de 24h | Sinal perdido, excedente devolvido |
| Rejeição pelo estúdio | Sinal devolvido integralmente |
| Devolução após repasse pago | Ajuste negativo no fechamento seguinte; fechamento anterior intacto |
| Indicação do estúdio atendida por guest | 50/50, mesmo com a semana já paga |
| Cliente próprio de guest | Não entra no faturamento do estúdio |
| Taxa semanal de €600 | Entra como recebimento do estúdio |

**Reconciliação:** a soma dos relatórios deve bater com recebimentos, devoluções e
repasses do período (`01_REGRAS_DE_NEGOCIO.md` §10.8). Exportações em PDF e Excel
devem preservar os mesmos totais exibidos na tela.

## 7. Testes de segurança

- Sessão expira após 60 minutos de inatividade e após 12 horas totais.
- Bloqueio de conta encerra sessões ativas imediatamente.
- Troca de senha encerra as demais sessões.
- CSRF obrigatório em operações que alteram dados.
- Cookie com `Secure`, `HttpOnly` e `SameSite` em produção.
- Limite de tentativas de login.
- Login e recuperação não revelam se um e-mail existe.
- Fotos e comprovantes não acessíveis sem autorização; sem URL pública.
- Senha nunca retornada por nenhum endpoint.
- `audit_log` não aceita `UPDATE` nem `DELETE` pela role da aplicação.
- Ausência de dados pessoais em logs.

## 8. Testes de pós-venda e notificação

- Pós-venda criado ao concluir a sessão, com vencimento em 15 dias.
- Lista diária das 08h em `Europe/Dublin`, mantendo o horário no verão.
- Gerente recebe obrigatoriamente; proprietário conforme preferência.
- E-mail não contém fotos nem observações.
- Falha de envio fica registrada e **não** altera o estado do pós-venda.
- Reenvio não duplica a notificação interna.
- Resultado "novo acompanhamento" mantém o item pendente com nova data.
- Reabertura exige motivo e nova data.

## 9. Testes ponta a ponta

1. Autocadastro de artista, aprovação e primeiro acesso.
2. Cadastro de cliente, orçamento, aprovação e agendamento com sinal.
3. Solicitações concorrentes pela mesma maca, com aprovação de uma e rejeição da outra.
4. Sessão realizada, pagamento confirmado, conclusão e entrada no repasse.
5. Fechamento de sexta e marcação de transferência.
6. Ciclo do guest: pagamento da semana, ativação, reserva e expiração.
7. Pós-venda: geração, e-mail, conclusão com foto e reabertura.
8. Relatório por período com exportação.

## 10. Testes de desempenho

Conforme `03_REQUISITOS_NAO_FUNCIONAIS.md` §2, com volume realista:

- 15 usuários simultâneos.
- Telas comuns até 3 segundos.
- Relatórios comuns até 10 segundos.

"Condições normais" é definido como: VPS em operação regular, banco com histórico
de pelo menos dois anos de agenda e sem processo de backup em execução.

## 11. Testes de recuperação

- Restauração de backup cifrado em banco temporário isolado.
- Verificação de integridade após restauração.
- Teste trimestral documentado, conforme requisito aprovado.
- Nunca restaurar sobre produção sem janela aprovada e confirmação do alvo.

## 12. Critérios de aprovação

- Todos os testes de concorrência aprovados.
- Matriz de permissões sem acesso indevido conhecido.
- Cálculos financeiros conferidos com os exemplos de `01_REGRAS_DE_NEGOCIO.md`.
- Relatórios reconciliando com os lançamentos do período.
- Nenhum defeito crítico ou alto em aberto.
- Jornadas ponta a ponta executadas em homologação.
- Backup restaurado com sucesso antes do lançamento.
- Homologação do usuário nos quatro perfis.

## 13. Homologação do usuário

Sessões com proprietário e gerente validando: clareza dos estados, leitura da
agenda com as quatro macas, conferência de um fechamento semanal real e uso em
celular e tablet dentro do estúdio.
