# Plano de Testes e Critérios de Aceite

**Status:** Aprovado. Execução em andamento junto com as sprints.
**Última atualização:** 26/09/2026

> Corresponde à Fase 13 de `02_ROADMAP_PRE_IMPLEMENTACAO.md`. Cada regra crítica
> tem ao menos um cenário de sucesso e um de exceção.

## 0. Cobertura atual

**279 testes aprovados** no backend, executados em container contra PostgreSQL
real no banco isolado `tattoo_studio_test`. Conferido em 07/10/2026, com a suíte
inteira num só comando.

> **A suíte devolve as conexões entre testes.** Cada teste monta um `Container`
> próprio, com engine próprio, e o pool não se fechava sozinho: ao passar de cento
> e poucos testes o PostgreSQL começou a recusar com `sorry, too many clients
> already`, derrubando treze testes que não tinham defeito nenhum. É o tipo de
> falha que acusa o inocente, porque o culpado é o acúmulo. `Database.dispose()`
> existe por isso e o `conftest` o chama no encerramento de cada teste.

**189 testes aprovados** no frontend, em Vitest dentro do container, sobre classes
puras — sem montar componente e sem dependência nova. O que se testa ali é o que
tem chance real de estar errado: fuso horário, aritmética de dinheiro, formatação,
tradução de erro da API, ciclo de sessão e os espelhos de política que decidem o
que a tela mostra.

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
| **Consultas do painel do gestor** | Coberta: pendentes sem janela de data, filtro somado ao recorte por artista, filtro e janela independentes, estado desconhecido recusado, orçamentos pendentes, pagamentos aguardando confirmação vindos do estúdio inteiro, e o artista recusado na fila do gestor |
| **Fila do painel** | Coberta por 11 testes de classe pura: o item abre a agenda **no dia do agendamento** e não no de hoje, o sinal segue o agendamento que ele trava, e o dia fica de fora quando não se conhece; as três origens numa lista só, **ordenadas do mais antigo para o mais recente** qualquer que seja a origem, item que continua aparecendo quando o nome do cliente é desconhecido, e cada origem levando à tela que a decide |
| **Estados da sessão na tela** | Coberta por 6 testes de classe pura: **realizada fica em tom de espera e só quitada fica positiva** — verde em realizada diria ao artista que o trabalho conta para o repasse quando ainda não conta; o artista corrige o que registrou mas não mexe em sessão quitada; confirmar só aparece em sessão que aconteceu |
| **Exigência de sinal na tela** | Coberta por 5 testes: residente e proprietário que tatua exigem sinal, guest não (RN-GST-004), e artista desconhecido erra para o lado de exigir — não oferecer o atalho custa um clique, oferecê-lo custa um 403 |
| **Acordo de percentual por artista** | Coberta por 10 testes de ponta a ponta (ADR-030): artista começa sem acordo, a gestão o define, o acordo vence a regra da origem, a correção na aprovação vence o acordo, esvaziar devolve à origem, artista não mexe no próprio, fora do intervalo recusado, conta que não tatua recusada, e a auditoria guarda o valor anterior |
| **Acordo não alcança trabalho aprovado** | ✅ **Coberta, e é o teste que mais importa do campo.** Aprovado sob 85%, o orçamento e as sessões continuam em 85% depois de o acordo virar 50% (RN-REP-006). A garantia não está no caso de uso que altera: está na cópia congelada na aprovação |
| **Contas na tela** | Coberta por 24 testes de classe pura: papéis e estados nomeados, **bloqueada em vermelho e pendente em alerta** — as duas em vermelho esconderiam que só uma foi decisão de alguém —, acordo ausente exibido como "By origin" e nunca como `0%`, alçada de quem cria e de quem bloqueia, ninguém bloqueia a si mesmo, e quem tatua decidido num lugar só — a resposta vale para a agenda, para o repasse e para a exigência de nome de artista, e escrita em cada tela divergiria em silêncio |
| **Transições do pagamento na tela** | Coberta por 6 testes de classe pura (RN-PAG-007): informado oferece confirmar e recusar, confirmado oferece só devolver, e **recusado não volta de jeito nenhum** — um recusado que voltasse a confirmado apagaria a recusa do histórico |
| **Sinal do agendamento** | Coberta por 8 testes: **informado não basta para aprovar o horário** (RN-AGE-005) — é a diferença que o 403 do botão de aprovar comunicava sozinho —, recusado e devolvido não contam como sinal vivo (RN-AGE-008), e o pagamento integral antecipado substitui o sinal (RN-PAG-004) |
| **Pagamento na tela** | Coberta por 6 testes: informado em alerta porque trava a aprovação, devolvido em neutro porque é desfecho correto (RN-PAG-003) e recusado em vermelho, e **sinal retido exibido como tal** — continua confirmado (RN-AGE-009), e quem lesse só o estado procuraria a devolução que nunca houve |
| **Consequência de cada decisão de agenda** | Coberta por 7 testes, criados depois de o texto apodrecer: a frase da aprovação afirmava que o sinal não era registrado no sistema, e passou a contradizer o painel do sinal logo acima dela no mesmo modal. Os testes prendem o fato que cada frase carrega, e não a redação |
| **Painel do artista** | Coberta por 10 testes de classe pura (seções 10.2 e 10.3): o dia em ordem de acontecer, cancelado e recusado fora, o que está em curso contado como "próximo", e **o repasse exibido é sempre o último fechado, nunca previsão** — um número adiantado diria ao artista quanto ele vai receber sem que ninguém tenha fechado a semana |
| **Faturamento contra a planilha real** | ✅ **Coberta, e e o teste mais valioso do modulo.** O controle de outubro de 2026 do estudio e reproduzido atendimento por atendimento, e os tres totais conferidos: EUR 1.640,00 tatuados, EUR 421,50 do estudio, EUR 1.218,50 dos artistas. E a unica prova de que o sistema devolve o mesmo numero que a planilha |
| **Divisao do faturamento** | Coberta por 13 testes: as duas partes somam sempre o valor pago em qualquer centavo, a divisao e a **mesma** que paga o artista, o sinal nao abate (RN-PAG-005), e os totais somam linhas ja arredondadas |
| **Fronteira do mes** | Coberta: outubro comeca a meia-noite de Dublin, que e 23h de 30 de setembro em UTC no horario de verao; janeiro comeca a meia-noite UTC. O mes e meio-aberto, e o fim de um e o comeco do outro |
| **Alcada do faturamento** | Coberta: o artista leva 403 (RN 10.4). O relatorio mostra quanto todos receberam, e a RN-REP-004 o limita aos proprios valores |
| **Mes na tela** | Coberta por 13 testes de classe pura: o mes corrente vem do fuso do estudio e nao do navegador, a virada do ano anda nos dois sentidos, e a barra da comparacao e relativa ao maior mes — com mes zerado desenhado em zero, nunca removido |
| **Semana de repasse** | Coberta por 9 testes de classe pura: sabado pertence a sexta seguinte, sexta de manha a sexta do mesmo dia, **20h em ponto fecha a semana que termina** e um minuto depois cai na seguinte, 20h de Dublin dando 19h UTC no verao e 20h UTC no inverno, e **a semana que atravessa a virada do horario de verao com 169 horas** — subtrair sete dias em UTC deixaria uma hora de fora |
| **Divisao do repasse** | Coberta por 5 testes: 70% e 50% de valores redondos, o exemplo da RN-PAG-005, meio centavo arredondando **para cima** e nao pelo padrao bancario do Python, e a diferenca entre arredondar por sessao e arredondar no total |
| **Ciclo do repasse** | Coberta: fechamento com a parcela de cada sessao, um repasse por artista, **fechar duas vezes devolvendo o mesmo fechamento**, sessao nao quitada fora, sessao de outra semana fora, semana em curso recusada, artista sem fechar, artista vendo so os proprios repasses, artista recusado no demonstrativo do colega, o demonstrativo exibindo o que a RN-REP-007 lista, confirmacao registrando responsavel, segunda confirmacao recusada e artista sem confirmar |
| **Rotulo da semana no frontend** | Coberta: o periodo comeca no dia **seguinte** a abertura, porque a semana abre as 20h da sexta anterior, e o fechamento aparece as 20h no verao e no inverno — formatado no fuso do estudio, nunca no do navegador |
| **Portão do sinal** | Coberta: sinal apenas informado **não** libera a aprovação, confirmado libera, artista não lança nem confirma pagamento, sinal recusado deixa o cliente pagar outro, dois sinais vivos no mesmo agendamento são recusados, e sinal sem agendamento é recusado |
| **Estados do pagamento** | Coberta por classe pura: o fluxo da RN-PAG-007 inteiro, recusado que nunca volta a confirmado, e devolvido e estornado como estados finais |
| **Desfecho financeiro do agendamento** | Coberta: recusa pelo estúdio devolve tudo, cancelamento e não comparecimento retêm o sinal mesmo com aviso, remarcação dentro do prazo leva os valores junto, fora do prazo retém — e a regra das 24 horas conferida na borda exata, inclusive nas 24 horas cheias |
| **Devoluções** | Coberta: registro manual com forma própria diferente da original, e devolução acima do que entrou recusada |
| **Sinal do guest** | Coberta: cliente próprio do guest não exige sinal (RN-GST-004), indicação do estúdio exige (RN-GST-005), e todo agendamento comum exige |
| **Ciclo da sessão** | Coberta: aprovação gerando as sessões previstas com origem e percentual congelados, orçamento pendente sem sessão nenhuma, reaprovação mantendo a realizada e refazendo só as agendadas, artista marcando realizada, artista de fora recebendo 403, parcial registrando o cobrado, parcial com valor igual ao previsto recusada, artista sem confirmar recebimento, gestor confirmando e concluindo, sessão agendada não confirmável, correção de valor sem motivo recusada e com motivo gravada na auditoria, e sessão quitada não podendo ser remarcada |
| **Ajuste das sessões restantes** | Coberta: artista sem ajustar, ajuste que mantém o total deixando o orçamento aprovado, ajuste que muda o total devolvendo a Pendente com o percentual descartado, o cobrado de uma parcial entrando na conta no lugar do previsto, sessão de valor zero recusada, e artista de fora sem ver as sessões |
| **Aritmética das sessões** | Coberta por 8 testes de classe pura: sequência continuando depois do que já foi resolvido, plano que encolheu abaixo do executado não pedindo sessão nenhuma, soma do cobrado com o previsto, e três sessões de €133,33 fechando €399,99 exatos |
| **Ciclo do orçamento** | Coberta: guest sem acesso, residente não aprova, percentual congelado em 70 e em 50 conforme a origem, correção de percentual pelo gestor registrada na auditoria, edição de aprovado voltando a pendente e limpando o percentual, recusa sem motivo, reaprovação bloqueada e visibilidade entre artistas |
| **Imagens de referência** | Coberta: leitura sem sessão devolvendo 401, artista de fora recebendo 403 em listar, ler e anexar, imagem de um orçamento não saindo por outro, tipo não aceito, arquivo acima de 10 MB, arquivo vazio, limite de 10 por orçamento, anexar não reabrindo aprovação, residente sem anexar em aprovado e remoção apagando o arquivo |
| **Armazenamento em sistema de arquivos** | Coberta no adaptador: ida e volta dos bytes, criação da árvore de diretórios, sobrescrita sem deixar o temporário, leitura de chave ausente como erro de domínio, remoção repetida sem erro e chave tentando escapar da raiz nos três formatos |
| **Fuso do estúdio no frontend** | Coberta: horário de verão e horário padrão, mesmo instante escrito com deslocamentos diferentes, minutos desde a meia-noite atravessando a virada, e **o dia de uma reserva das 00h30 de Dublin**, que em UTC cairia no dia anterior. Uma agenda deslocada por uma hora parece correta na tela, e é por isso que tem teste |
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
