# Regras de Negócio — Gestão do Estúdio de Tatuagem

**Status:** Em elaboração  
**Última atualização:** 23/09/2026

## 1. Objetivo e escopo

O sistema será uma ferramenta interna para gerir artistas, clientes, agenda, macas, pagamentos, repasses e pós-venda do estúdio.

Não haverá acesso para clientes nesta fase. Termos de consentimento, questionários de saúde e autorizações de uso de imagem também ficam fora do escopo inicial.

O escopo atual contempla somente o estúdio de Cork City. A comercialização futura para outros estúdios não faz parte desta versão.

### 1.1 Configuração operacional

- **Localização:** Cork City, Irlanda;
- **Fuso horário:** `Europe/Dublin`, com ajuste automático do horário de verão;
- **Moeda:** euro (€);
- **Idioma inicial da interface:** inglês;
- **Funcionamento padrão:** terça-feira a domingo, das 10h às 20h;
- **Fechamento padrão:** segunda-feira;
- **Quantidade inicial:** 4 macas;
- Todas as macas seguem o mesmo horário-base;
- Gerentes e proprietários podem adicionar macas;
- Gerentes e proprietários podem abrir ou bloquear horários quando necessário;
- Uma alteração excepcional de horário prevalece sobre o funcionamento padrão na data afetada.

## 2. Perfis e atuação como tatuador

O sistema terá quatro perfis de acesso:

- **Proprietário**;
- **Gerente**;
- **Tatuador residente**;
- **Guest**.

Proprietários e gerentes também poderão atuar como tatuadores. Nesse caso, conservarão suas permissões administrativas e terão agenda, clientes, atendimentos e repasses próprios.

### 2.1 Proprietário

- Possui acesso administrativo completo.
- Pode criar usuários, atribuir ou alterar perfis e promover usuários.
- Pode cadastrar e editar tatuadores residentes e guests.
- Pode gerir agenda, macas, clientes, orçamentos, sessões, pagamentos, estornos, repasses, percentuais, pós-vendas e relatórios.
- Pode classificar um atendimento como indicação do estúdio e corrigir essa classificação.
- Pode optar por receber a lista diária de pós-venda.
- Pode atuar como tatuador.

### 2.2 Gerente

- Administra a operação do estúdio.
- Pode cadastrar e editar tatuadores residentes e guests; o novo cadastro fica ativo no perfil correspondente.
- Pode ativar ou renovar semanas de acesso de guests após confirmar o pagamento.
- Pode gerir agenda, macas, clientes, orçamentos, sessões e pós-vendas.
- Pode consultar o faturamento e os repasses.
- Pode registrar, corrigir e estornar pagamentos.
- Pode definir preços e percentuais de repasse.
- Pode classificar um atendimento como indicação do estúdio e corrigir essa classificação.
- Não pode atribuir, alterar ou promover perfis de acesso.
- Recebe obrigatoriamente a lista diária de pós-venda.
- Pode atuar como tatuador.

### 2.3 Tatuador residente

- Pode cadastrar somente o nome e o contato de um cliente.
- Pode consultar apenas clientes vinculados aos seus atendimentos.
- Pode criar e acompanhar os próprios orçamentos e atendimentos.
- Pode solicitar, remarcar e cancelar horários, respeitando as regras de aprovação do estúdio.
- Pode consultar a própria agenda e os próprios repasses semanais.
- Pode consultar os pós-vendas vinculados às suas sessões, sem editar ou concluir.
- Não pode gerir usuários, permissões ou dados de outros artistas.

### 2.4 Guest

- Possui acesso temporário e limitado.
- Pode consultar a disponibilidade de macas e horários durante as semanas pagas.
- Pode solicitar reservas e informar nome e contato do cliente em cada reserva.
- Não pode gerir o cadastro completo de clientes.
- Pode consultar os próprios agendamentos e os repasses de clientes indicados pelo estúdio.
- Não participa do módulo de pós-venda.
- Fica inativo ao final do período pago e volta a acessar somente após renovação pelo gerente ou proprietário.

### 2.5 Ativação e bloqueio de usuários

- O proprietário pode ativar ou bloquear qualquer usuário.
- O gerente pode ativar ou bloquear tatuadores residentes e guests.
- O gerente não pode bloquear proprietários ou outros gerentes.
- O último proprietário ativo não pode ser bloqueado, evitando que o estúdio fique sem administração.
- Ativação, bloqueio e reativação devem permanecer registrados com data, hora e usuário responsável.
- O usuário bloqueado perde o acesso imediatamente e não pode criar solicitações ou reservas.
- Cadastro, histórico, pagamentos e atendimentos do usuário bloqueado permanecem preservados.
- Agendamentos futuros não são cancelados automaticamente.
- Gerente e proprietário recebem um alerta e devem transferir ou cancelar os agendamentos futuros do usuário bloqueado.
- O usuário poderá ser reativado conforme a mesma hierarquia de permissões usada no bloqueio.

### 2.6 Cadastro e autorização de usuários

- Um tatuador pode preencher o próprio cadastro para solicitar acesso.
- O cadastro feito pelo próprio tatuador entra com estado **Pendente de autorização** e não permite acesso às áreas internas.
- Gerente ou proprietário pode autorizar, editar ou bloquear cadastros de residentes e guests.
- Gerente ou proprietário também pode adicionar diretamente residentes e guests pela área de gerenciamento de usuários.
- Um residente ou guest adicionado diretamente por gerente ou proprietário fica ativo após a conclusão do cadastro.
- Somente o proprietário pode criar ou atribuir os perfis de gerente e proprietário.
- O gerente não pode promover usuários nem alterar perfis de acesso.
- Autorização, rejeição, edição, bloqueio e alteração de perfil devem ficar registrados no histórico.

O autocadastro do artista exigirá:

- Nome artístico;
- E-mail;
- Telefone;
- Tipo solicitado: residente ou guest;
- Senha;
- Confirmação de senha.

A confirmação de senha será usada apenas para validar o preenchimento e não será armazenada separadamente.

- O e-mail será único no sistema e não poderá estar associado a mais de uma conta.
- Aprovação, rejeição ou bloqueio gerará uma notificação por e-mail ao artista.
- A rejeição exigirá um motivo e aceitará uma observação opcional.
- O artista poderá corrigir um cadastro rejeitado e reenviá-lo para análise.

Após a autorização:

- O residente ficará ativo e poderá acessar as áreas permitidas ao seu perfil.
- O cadastro do guest ficará aprovado, mas seu acesso dependerá de uma semana paga e ativa.

### 2.7 Autenticação e recuperação de acesso

- O acesso será feito com e-mail e senha.
- Não haverá autenticação em dois fatores nesta versão.
- A recuperação de senha será feita por link temporário enviado ao e-mail cadastrado.
- Senhas nunca poderão ser visualizadas por gerentes, proprietários ou outros usuários.
- A alteração da senha encerrará as demais sessões ativas da conta.
- O bloqueio da conta encerrará imediatamente todas as suas sessões ativas.

### 2.8 Cadastro de gerente e proprietário

Somente um proprietário poderá criar usuários com perfil de gerente ou proprietário. O cadastro exigirá:

- Nome;
- E-mail;
- Telefone;
- Perfil;
- Senha;
- Confirmação de senha;
- Indicação se também atua como tatuador;
- Nome artístico, obrigatório somente quando também atuar como tatuador.

## 3. Clientes e origem do atendimento

### RN-CLI-001 — Dados cadastrados pelos artistas

O cadastro básico do cliente terá:

- Nome obrigatório;
- Telefone obrigatório;
- Instagram opcional;
- Artista responsável pelo cadastro;
- Histórico de agendamentos, sessões, pagamentos e pós-vendas;
- Data e usuário responsável por cada criação ou alteração.

O tatuador residente poderá cadastrar um novo cliente durante a criação do agendamento. O guest continuará limitado a informar os dados básicos necessários em suas próprias reservas.

### RN-CLI-002 — Relação entre cliente e artista

Um cliente poderá estar vinculado a mais de um tatuador. A origem será determinada em cada atendimento:

- Se o cliente retornar ao mesmo artista que o trouxe, será considerado cliente próprio do artista.
- Se o cliente retornar ao estúdio e for encaminhado a outro artista, o novo atendimento será considerado indicação do estúdio.

### RN-CLI-003 — Correção da origem

Somente gerente e proprietário poderão alterar a origem ou o percentual de um atendimento. A alteração valerá apenas para o atendimento corrigido e não modificará atendimentos anteriores ou futuros.

### RN-CLI-004 — Visibilidade dos clientes

- Proprietário e gerente poderão consultar todos os clientes e seus históricos.
- O tatuador poderá consultar o cadastro completo somente dos clientes cadastrados por ele.
- Quando um cliente cadastrado pelo artista X for encaminhado pelo estúdio ao artista Y, o artista Y verá apenas nome, telefone e Instagram dentro do próprio agendamento.
- O artista Y não terá acesso ao cadastro completo nem ao histórico anterior desse cliente.

### RN-CLI-005 — Possíveis duplicidades

- Ao cadastrar ou alterar um cliente, o sistema verificará telefone e, quando informado, Instagram.
- Uma possível duplicidade gerará um alerta, mas não bloqueará automaticamente o cadastro.

### RN-CLI-006 — Edição e união de cadastros

- O tatuador poderá corrigir nome, telefone e Instagram somente dos clientes cadastrados por ele.
- Proprietário e gerente poderão editar qualquer cliente.
- Somente proprietário e gerente poderão unir cadastros duplicados.
- A união preservará vínculos, agendamentos, sessões, pagamentos e pós-vendas em um único cadastro.
- Nenhum usuário poderá apagar diretamente um cliente que possua histórico financeiro ou de atendimento.
- Edições e uniões ficarão registradas com data, hora e usuário responsável.

### RN-CLI-007 — Retenção e solicitações sobre dados pessoais

- Não haverá exclusão automática imediata dos dados de clientes.
- Os dados permanecerão enquanto forem necessários para relacionamento, histórico de atendimento, obrigações financeiras ou defesa de direitos.
- Registros financeiros serão mantidos por pelo menos seis anos.
- Cadastros sem atividade serão submetidos a revisão periódica depois de seis anos.
- Solicitações de acesso, correção ou exclusão serão avaliadas por gerente ou proprietário.
- Quando não houver justificativa para manter a identificação, contato e fotos serão apagados ou anonimizados, preservando somente os registros cuja conservação seja necessária.
- Toda correção, anonimização ou exclusão ficará registrada sem conservar no histórico o conteúdo pessoal que deveria ter sido removido.

## 4. Macas e agenda

### RN-AGE-001 — Unidade reservável

Maca e bancada formam um único recurso, identificado no sistema apenas como **maca**. Cada maca será numerada e terá sua própria disponibilidade por data e intervalo de horário.

- Não haverá blocos fixos de duração.
- O artista definirá o horário inicial e final ao solicitar o agendamento.
- A duração será calculada a partir desses horários.
- Não haverá pausa obrigatória entre dois agendamentos consecutivos da mesma maca.
- A disponibilidade será calculada pela sobreposição real dos intervalos de horário.

### RN-AGE-002 — Dados do agendamento

Cada agendamento deverá registrar, no mínimo:

- Cliente;
- Artista;
- Maca;
- Data;
- Horário inicial e final.

### RN-AGE-003 — Estados do agendamento

O fluxo será:

`Solicitada → Aprovada ou Rejeitada → Realizada, Cancelada ou Não compareceu`

### RN-AGE-004 — Solicitações concorrentes

- Uma solicitação pendente não bloqueia a maca.
- Mais de um artista poderá solicitar a mesma maca no mesmo horário.
- As solicitações concorrentes serão exibidas juntas, incluindo a data e a hora em que cada uma foi enviada.
- Após uma aprovação, a maca deixará de aparecer como disponível naquele intervalo.
- As demais solicitações conflitantes não poderão ser aprovadas e deverão ser rejeitadas com o tratamento financeiro aplicável.

### RN-AGE-005 — Aprovação

Somente gerente ou proprietário poderá aprovar ou rejeitar uma solicitação. Uma solicitação não poderá ser aprovada enquanto o pagamento do sinal não estiver confirmado.

- Residente e guest sempre criarão o agendamento no estado **Solicitada**.
- Gerente e proprietário poderão criar um agendamento diretamente no estado **Aprovada**, desde que confirmem o sinal e não exista conflito.
- Gerente e proprietário, quando atuarem como tatuadores, poderão aprovar o próprio agendamento.
- Toda aprovação registrará data, hora e usuário responsável.

### RN-AGE-006 — Rejeição

A rejeição ficará registrada e exigirá um dos seguintes motivos:

- Horário ocupado;
- Estúdio fechado;
- Horário remarcado.

Uma observação complementar será opcional.

### RN-AGE-007 — Prevenção de conflito

O sistema nunca permitirá dois agendamentos aprovados para a mesma maca em horários sobrepostos.

Se gerente ou proprietário tentar adicionar ou alterar um agendamento para um intervalo ocupado, um modal exibirá os dados do agendamento existente e informará que será necessário escolher outra maca ou outro horário. O modal não permitirá ignorar o conflito.

### RN-AGE-008 — Remarcação

- Somente gerente ou proprietário efetivará uma remarcação solicitada pelo cliente.
- A solicitação feita com pelo menos 24 horas de antecedência transferirá o sinal e os demais valores pagos para o novo agendamento.
- Fora desse prazo, o cliente perderá o sinal e precisará pagar um novo sinal para outro agendamento.
- Qualquer valor antecipado acima do sinal será devolvido.

### RN-AGE-009 — Cancelamento sem nova data

Em cancelamento sem remarcação, o sinal permanecerá com o estúdio para compensar o horário reservado e o trabalho de preparação do desenho, mesmo que o aviso ocorra com pelo menos 24 horas de antecedência. Valores pagos acima do sinal serão devolvidos.

### RN-AGE-010 — Não comparecimento

Em caso de não comparecimento, o estúdio reterá o sinal. Valores pagos acima do sinal serão devolvidos. O tatuador não receberá repasse pelo atendimento não realizado.

### RN-AGE-011 — Bloqueios de disponibilidade

- Gerente e proprietário poderão bloquear uma maca específica ou todas as macas.
- Cada bloqueio registrará data, horário e motivo.
- Os motivos poderão incluir manutenção, evento, fechamento ou outro motivo informado pelo gestor.
- Um período bloqueado não aparecerá como disponível para novas solicitações.
- Gerente e proprietário poderão reabrir o período posteriormente.
- Criação, alteração e remoção do bloqueio permanecerão no histórico com o usuário responsável.

### RN-AGE-012 — Notificações da agenda

- Uma nova solicitação aparecerá no painel de gerente e proprietário.
- Aprovação, rejeição, remarcação ou cancelamento gerará um e-mail para o artista.
- As alterações também aparecerão no painel do artista.
- Uma tentativa de agendamento bloqueada por conflito na agenda do artista notificará gerente e proprietário no sistema e por e-mail.
- O sistema não enviará mensagens diretamente ao cliente nesta versão.
- Artista ou equipe confirmará o atendimento com o cliente por telefone ou Instagram.
- Uma falha no envio do e-mail não alterará o estado do agendamento e ficará registrada para acompanhamento.

### RN-AGE-013 — Atraso e extensão de sessão

- O sistema não prolongará automaticamente uma reserva quando a sessão ultrapassar o horário previsto.
- Se houver outro agendamento na mesma maca, gerente ou proprietário deverá transferir um dos atendimentos para outra maca disponível ou remarcar manualmente.
- Toda transferência ou remarcação ficará registrada com o usuário responsável.

### RN-AGE-014 — Não sobreposição na agenda do artista

- Um artista não poderá ter solicitações pendentes ou agendamentos aprovados em intervalos sobrepostos, mesmo que sejam em macas diferentes.
- Uma solicitação pendente ocupa somente o horário daquele artista; não bloqueia a maca para solicitações de outros artistas, conforme RN-AGE-004.
- Se o artista já tiver uma solicitação pendente ou agendamento aprovado no intervalo, o sistema impedirá a criação do novo agendamento e informará o conflito.
- A administração será notificada dentro do sistema e por e-mail. O conflito não poderá ser ignorado nem substituído por uma inclusão manual.
- Solicitações rejeitadas e agendamentos cancelados deixam de ocupar a agenda do artista. Os registros históricos serão preservados.

## 5. Orçamentos e sessões

### RN-ORC-001 — Acesso ao orçamento

- Tatuador residente, gerente e proprietário poderão criar orçamentos.
- O guest não terá acesso ao módulo de orçamentos e continuará com acesso somente à agenda para seus próprios clientes.
- Quando um guest atender um cliente indicado pelo estúdio, gerente ou proprietário criará o orçamento e o agendamento.

### RN-ORC-002 — Aprovação e validade

- O orçamento não terá vencimento automático.
- Depois de enviado para análise, permanecerá pendente até uma decisão manual.
- Somente gerente ou proprietário poderá aprovar ou rejeitar o orçamento.
- A decisão ficará registrada com data, hora e usuário responsável.

### RN-ORC-003 — Edição

- O residente criará e enviará o orçamento no estado **Pendente**.
- O residente poderá editar o orçamento enquanto estiver pendente.
- Se um orçamento aprovado for alterado, voltará ao estado **Pendente** e exigirá nova aprovação.
- A rejeição exigirá um motivo e aceitará uma observação opcional.
- Gerente e proprietário poderão criar, editar, aprovar ou rejeitar orçamentos.
- Toda edição e mudança de estado ficará registrada com data, hora e usuário responsável.

### RN-ORC-004 — Campos do orçamento

O orçamento conterá:

- Cliente;
- Artista;
- Origem: cliente do artista ou indicação do estúdio;
- Descrição da tatuagem;
- Região do corpo;
- Tamanho estimado;
- Imagens de referência opcionais;
- Valor total;
- Quantidade prevista de sessões;
- Valor previsto por sessão;
- Duração estimada de cada sessão;
- Observações.

### RN-ORC-005 — Realização e conclusão de sessão

- O artista marcará a sessão como **Realizada**.
- Gerente ou proprietário confirmará o valor recebido.
- A sessão ficará **Concluída** somente depois da confirmação da realização e do pagamento.
- Apenas sessões concluídas poderão entrar no repasse.
- Correções posteriores permanecerão registradas com data, hora, motivo e usuário responsável.

### RN-ORC-006 — Sessão realizada parcialmente

- Uma sessão interrompida ou executada parcialmente será marcada como **Realizada parcialmente**.
- O valor efetivamente cobrado será registrado e confirmado por gerente ou proprietário.
- O repasse será calculado somente sobre o valor efetivamente recebido naquela sessão.
- Gerente ou proprietário ajustará as sessões restantes.
- Se o ajuste alterar o valor total aprovado, o orçamento voltará ao estado **Pendente** e exigirá nova aprovação.

## 6. Sinal e pagamentos

### RN-PAG-001 — Valor e finalidade do sinal

Todo agendamento exigirá um sinal de **€50** para confirmação. O sinal faz parte do preço total da tatuagem e não é um valor adicional.

- Em trabalhos com várias sessões, cada sessão agendada exigirá seu próprio sinal de €50.
- O sinal de cada sessão fará parte do valor previsto para aquela sessão.
- A soma dos sinais e saldos das sessões não poderá ultrapassar o valor total aprovado do orçamento, salvo se o orçamento for alterado e novamente aprovado.

### RN-PAG-002 — Confirmação do pagamento

- O cliente pagará o sinal antes da aprovação do horário.
- O pagamento poderá ocorrer por depósito, dinheiro ou cartão.
- Em depósito, o comprovante será enviado ao estúdio.
- Gerente ou proprietário confirmará o recebimento e registrará forma de pagamento, data, hora e usuário responsável.
- Sem confirmação do pagamento, o agendamento não poderá ser aprovado.

### RN-PAG-003 — Rejeição pelo estúdio

Se o estúdio rejeitar a solicitação, o sinal será devolvido integralmente ao cliente.

### RN-PAG-004 — Pagamento integral antecipado

O cliente poderá pagar antecipadamente o preço integral da tatuagem. Gerente ou proprietário registrará esse pagamento durante a aprovação.

Se o atendimento for cancelado, não comparecido ou remarcado fora do prazo, o estúdio reterá €50 e devolverá o restante. Não haverá repasse ao artista.

### RN-PAG-005 — Atendimento realizado

Quando o atendimento for realizado, o sinal integrará o preço da tatuagem e a base de cálculo do repasse.

Exemplo para uma tatuagem de €100 feita por um residente para cliente próprio:

- Sinal antecipado: €50;
- Saldo no atendimento: €50;
- Total pago pelo cliente: €100;
- Repasse ao artista: €70;
- Parcela do estúdio: €30.

### RN-PAG-006 — Registro manual e cartão

- Todos os recebimentos serão inseridos e confirmados manualmente por gerente ou proprietário nesta versão.
- Depósito, dinheiro e cartão permanecerão como formas de pagamento registráveis.
- Não haverá integração com operadora, terminal ou gateway de cartão nesta versão.
- Quando houver pagamento por cartão em solução externa, os dados da transação serão registrados manualmente.
- Taxas cobradas pela operadora serão absorvidas pelo estúdio e não reduzirão o repasse do artista.
- Integração e cobrança automática por cartão ficam reservadas para uma versão futura.

### RN-PAG-007 — Estados e correções

O pagamento seguirá o fluxo:

`Informado → Confirmado ou Recusado → Devolvido ou Estornado`

- Somente gerente e proprietário poderão confirmar, recusar, devolver ou estornar.
- Um pagamento nunca será apagado.
- Correções serão feitas por lançamento de ajuste vinculado ao registro original.
- Cada ação registrará valor, forma de pagamento, data, motivo e usuário responsável.

### RN-PAG-008 — Quitação da sessão

- O valor de cada sessão será cobrado integralmente.
- O sinal será a única antecipação prevista para a sessão.
- O restante deverá ser pago até a conclusão da sessão.
- Não haverá parcelamento adicional do valor de uma mesma sessão.
- O repasse será liberado somente depois que a sessão estiver realizada e integralmente quitada.

### RN-PAG-009 — Devoluções

- Gerente ou proprietário registrará manualmente a devolução depois de realizá-la.
- O registro informará valor, data, forma utilizada, motivo e observação.
- Um comprovante poderá ser anexado quando existir.
- A devolução ficará vinculada ao pagamento original.
- O sistema mostrará o valor devolvido e o valor retido pelo estúdio.
- A forma de devolução poderá ser diferente da forma do pagamento original.
- O lançamento original permanecerá preservado no histórico.

## 7. Repasses e regras financeiras

### RN-REP-001 — Cliente próprio

Para proprietário, gerente ou residente atuando como tatuador:

- Artista: **70%** do valor da tatuagem;
- Estúdio: **30%** do valor da tatuagem.

### RN-REP-002 — Indicação do estúdio

Quando o atendimento for indicação do estúdio, independentemente de o artista ser proprietário, gerente, residente ou guest:

- Artista: **50%** do valor da tatuagem;
- Estúdio: **50%** do valor da tatuagem.

O cliente pagará ao estúdio e o estúdio fará o repasse ao artista.

### RN-REP-003 — Trabalho com várias sessões

Em trabalhos divididos em sessões, cada pagamento recebido pelo estúdio gerará o repasse proporcional ao valor daquela sessão.

Exemplo: uma tatuagem de €10.000 dividida em quatro sessões de €2.500 terá o percentual calculado separadamente sobre cada €2.500 recebido.

### RN-REP-004 — Fechamento semanal

- Os repasses serão realizados às sextas-feiras.
- Pagamentos recebidos na própria sexta-feira entrarão no repasse daquele dia.
- Cada artista visualizará somente seus próprios valores; gerente e proprietário visualizarão todos.
- O período semanal será encerrado às 20h de sexta-feira, no fuso `Europe/Dublin`.
- O sistema calculará os repasses depois do fechamento.
- Gerente ou proprietário confirmará manualmente a transferência ao artista.
- A confirmação registrará data, hora, valor e usuário responsável.

### RN-REP-005 — Ajustes após repasse pago

- Uma devolução ou um estorno ocorrido depois do pagamento do repasse não alterará o fechamento anterior.
- A parcela anteriormente repassada ao artista será lançada como ajuste negativo no próximo repasse.
- O ajuste ficará vinculado ao pagamento original e registrará valor, motivo, data e usuário responsável.

### RN-REP-006 — Vigência dos percentuais

- Alterações nos percentuais padrão serão aplicadas somente a novos orçamentos.
- Cada orçamento aprovado guardará o percentual vigente no momento da aprovação.
- Uma mudança posterior do padrão não alterará atendimentos já aprovados.
- Para alterar o percentual de um atendimento existente, gerente ou proprietário deverá editar o orçamento, informar o motivo e aprová-lo novamente.

### RN-REP-007 — Cálculo e demonstrativo

- O repasse será calculado separadamente para cada sessão e arredondado para duas casas decimais.
- O fechamento semanal somará os valores calculados por sessão.
- O demonstrativo do artista exibirá sessões incluídas, valor recebido por sessão, percentual aplicado, ajustes positivos ou negativos e total líquido.
- O repasse poderá ficar nos estados **Calculado**, **Pago** ou **Ajustado**.
- Gerente ou proprietário poderá anexar um comprovante opcional da transferência.

## 8. Guest

### RN-GST-001 — Taxa semanal

O guest pagará **€600 por semana**, antecipadamente. A semana contratada começa no sábado e termina na sexta-feira.

### RN-GST-002 — Reserva futura

Para reservar datas de uma semana futura, o guest deverá pagar antecipadamente os €600 referentes àquela semana. Gerente ou proprietário confirmará o recebimento e ativará o período.

### RN-GST-003 — Expiração do acesso

Após o término da sexta-feira contratada, o guest ficará inativo. O acesso será restabelecido somente depois da confirmação de uma nova semana paga.

### RN-GST-004 — Clientes próprios

O guest receberá diretamente de seus clientes próprios. Esses valores não passarão pelo estúdio e não estarão sujeitos ao repasse de 70%/30%.

### RN-GST-005 — Indicação do estúdio

Quando o guest atender um cliente indicado pelo estúdio:

- Gerente ou proprietário cadastrará o cliente e o associará ao guest.
- O cliente pagará ao estúdio.
- O guest receberá 50% e o estúdio ficará com 50%.
- Essa regra será aplicada mesmo que o guest já tenha pago os €600 da semana.

### RN-GST-006 — Cancelamento ou transferência da semana

- A taxa semanal de €600 poderá ser devolvida ou transferida para outra semana.
- A decisão ficará a critério de gerente ou proprietário, independentemente de a semana já ter começado.
- A administração informará a decisão e o motivo.
- Devolução ou transferência registrará semana original, nova semana quando aplicável, valor, data e usuário responsável.
- O lançamento original permanecerá preservado no histórico.

### RN-GST-007 — Semanas antecipadas e acesso

- O guest poderá pagar uma ou várias semanas antecipadamente.
- Cada semana será registrada separadamente, de sábado a sexta-feira, no fuso `Europe/Dublin`.
- Depois da confirmação, o guest poderá acessar a agenda e reservar somente datas pertencentes às semanas pagas.
- Sem semana atual ou futura paga, a conta ficará inativa e não permitirá acesso.
- Semanas consecutivas pagas manterão o acesso sem interrupção.
- A renovação poderá ser registrada durante uma semana ainda ativa.

## 9. Pós-venda

### RN-POS-001 — Geração

Cada sessão realizada gerará um pós-venda próprio, com vencimento 15 dias após a data efetiva da sessão.

### RN-POS-002 — Lista diária

- Todos os dias, às 08h no horário local do estúdio, o sistema enviará por e-mail a lista de pós-vendas pendentes.
- O gerente receberá obrigatoriamente.
- O proprietário receberá opcionalmente, conforme sua preferência.
- A primeira versão será uma PWA instalável que abrirá o mesmo sistema web no aparelho. Em uma etapa futura, poderá enviar notificações push, condicionadas à autorização do usuário e ao suporte do dispositivo.
- O e-mail exibirá cliente, telefone, Instagram, artista responsável, data da sessão, dias em atraso e link para abrir o pós-venda no sistema.
- Fotos e observações não serão incluídas no e-mail e permanecerão disponíveis somente após autenticação.

### RN-POS-003 — Permanência na lista

O pós-venda continuará aparecendo diariamente até ser concluído pelo estúdio.

### RN-POS-004 — Registro da conclusão

A conclusão poderá registrar:

- Usuário responsável;
- Data e hora;
- Resultado do contato;
- Observações;
- Fotos da tatuagem após a cicatrização.

Toda edição ou conclusão ficará registrada com a identificação do gerente ou proprietário responsável.

### RN-POS-005 — Permissões

- Gerente e proprietário poderão editar e concluir o pós-venda.
- O residente poderá somente consultar os pós-vendas relacionados às próprias sessões.
- O guest não terá acesso ao módulo.

### RN-POS-006 — Área exclusiva

- O sistema terá uma área exclusiva para pós-venda, separada da agenda.
- O link do e-mail diário abrirá diretamente essa área depois da autenticação.
- As permissões da área seguirão as regras definidas para gerente, proprietário, residente e guest.
- A área separará os registros em **Pendentes**, **Atrasados** e **Concluídos**.
- Permitirá busca por cliente e filtros por artista, data da sessão e vencimento.
- Cada item exibirá os detalhes da sessão e o histórico de ações.
- O botão de conclusão ficará disponível somente para gerente e proprietário.
- O residente terá visualização somente leitura e limitada aos próprios clientes.

### RN-POS-007 — Resultado e novo acompanhamento

O resultado do contato será um dos seguintes:

- Cicatrização normal;
- Orientações reforçadas;
- Necessita novo acompanhamento;
- Necessita avaliação do tatuador;
- Possível retoque;
- Cliente não respondeu;
- Outro, com observação obrigatória.

Quando o resultado exigir novo acompanhamento, gerente ou proprietário definirá uma nova data e o item permanecerá pendente. Nos demais resultados, o pós-venda poderá ser concluído.

### RN-POS-008 — Fotos e reabertura

- Somente gerente e proprietário poderão anexar ou remover fotos de cicatrização.
- O residente poderá visualizar as fotos relacionadas às próprias sessões.
- Um pós-venda concluído poderá ser reaberto por gerente ou proprietário.
- A reabertura exigirá motivo e nova data de acompanhamento.
- Exclusões de fotos e reaberturas permanecerão registradas no histórico.

## 10. Telas previstas

- Painel principal;
- Agenda e disponibilidade de macas;
- Solicitações de agendamento;
- Clientes;
- Orçamentos;
- Sessões e atendimentos;
- Pagamentos, devoluções e estornos;
- Repasses semanais;
- Pós-venda;
- Cadastro de tatuadores residentes;
- Cadastro e ativação semanal de guests;
- Usuários e permissões;
- Configuração de macas e horários do estúdio;
- Relatórios;
- Histórico de auditoria.

### 10.1 Painel de proprietário e gerente

- Agenda do dia;
- Solicitações pendentes;
- Pagamentos aguardando confirmação;
- Repasses da próxima sexta-feira;
- Guests próximos do vencimento;
- Pós-vendas pendentes e atrasados;
- Ocupação das macas;
- Faturamento do período.

### 10.2 Painel do residente

- Agenda própria;
- Solicitações e orçamentos pendentes;
- Clientes cadastrados pelo artista;
- Repasse semanal previsto;
- Pós-vendas próprios para consulta.

### 10.3 Painel do guest

- Semanas pagas e validade do acesso;
- Disponibilidade de macas;
- Solicitações e agendamentos próprios;
- Repasses de indicações do estúdio.

### 10.4 Relatórios operacionais e financeiros

Proprietário e gerente terão acesso aos seguintes relatórios:

- Faturamento por período;
- Receita do estúdio por artista;
- Clientes próprios versus indicações do estúdio;
- Pagamentos por forma;
- Sinais retidos e devoluções;
- Repasses por artista;
- Taxas semanais de guests;
- Ocupação das macas;
- Cancelamentos e não comparecimentos;
- Sessões realizadas;
- Pós-vendas pendentes, atrasados e concluídos.

Os relatórios permitirão filtros por período, artista e estado.

#### Definições dos indicadores

- **Faturamento bruto recebido:** soma dos pagamentos confirmados que entraram no estúdio no período, incluindo pagamentos de sessões, sinais e semanas de guest, antes de devoluções e repasses. Cada pagamento entra uma única vez. O sinal de uma sessão realizada é parte do preço total e não é contado novamente além do pagamento recebido.
- **Receita líquida do estúdio:** faturamento bruto recebido menos devoluções efetivadas e repasses líquidos aos artistas. O repasse já incorpora a divisão de 70%/30% ou 50%/50%; não se subtrai novamente a parcela do artista depois de calcular a parte do estúdio.
- A receita líquida do estúdio é um indicador operacional antes de despesas operacionais e impostos; não substitui demonstrativos contábeis ou fiscais.
- Pagamentos entram pela data em que foram confirmados; devoluções e repasses entram pela data em que foram efetivados.
- Pagamentos diretos de clientes próprios de guests não entram no faturamento do estúdio; a taxa semanal de €600 entra como recebimento do estúdio.
- “Período anterior” é o intervalo imediatamente anterior com a mesma duração do período selecionado.
- O repasse por artista é calculado por sessão realizada e quitada, com ajustes posteriores discriminados.

Exemplo: €100 recebidos por uma sessão concluída de cliente próprio de residente contam €100 no faturamento bruto recebido. Após o repasse líquido de €70, a receita líquida operacional do estúdio é €30. O sinal de €50 já está incluído nos €100.

### 10.5 Comparação de faturamento

A comparação financeira exibirá:

- Período atual versus período anterior;
- Dois períodos escolhidos pelo usuário;
- Faturamento bruto;
- Receita líquida do estúdio;
- Repasses aos artistas;
- Taxas semanais de guests;
- Sinais retidos;
- Devoluções e estornos;
- Comparação por artista;
- Clientes próprios versus indicações do estúdio;
- Variação em valor e percentual.

Relatórios e comparações poderão ser exportados para **PDF** e **Excel**.

### 10.6 Visibilidade por artista

- O residente visualizará somente relatórios da própria produção e de seus repasses.
- O guest visualizará somente seus repasses referentes a indicações do estúdio.

### 10.7 Histórico de auditoria

- O proprietário poderá consultar todo o histórico de auditoria.
- O gerente poderá consultar ações operacionais e financeiras, mas não alterações administrativas relativas a contas de proprietário.
- Residentes e guests não terão acesso ao histórico de auditoria.
- Os registros de auditoria não poderão ser editados nem apagados por usuários do sistema.
- O histórico permitirá filtros por usuário, ação, módulo e período.
- Cada registro exibirá data e hora, usuário, ação e, quando aplicável, valores anteriores e novos.
- Os registros serão mantidos por seis anos. Durante esse prazo, usuários não poderão editá-los ou apagá-los.
- Ao fim de seis anos, o estúdio revisará se existe motivo para conservar registros específicos por mais tempo.

### 10.8 Critérios de aceite de relatórios

- Valores de relatórios devem reconciliar com recebimentos, devoluções e repasses registrados no período.
- O sinal de sessão realizada nunca pode ser contado em duplicidade.
- Filtros e exportações PDF/Excel devem preservar os mesmos totais exibidos na tela.
- Cada perfil somente poderá consultar dados autorizados pelas regras de acesso.

## 11. Pontos pendentes

Nenhum ponto funcional permanece pendente nesta seção. Requisitos técnicos e homologação geral permanecem no roadmap.

## 12. Referências oficiais

- [Data Protection Commission — Principles of Data Protection](https://dataprotection.ie/en/organisations/data-protection-basics/principles-data-protection)
- [Data Protection Commission — Retention under the GDPR](https://www.dataprotection.ie/en/faqs/responsibilities-data-controllers/how-long-should-personal-data-be-held-meet-obligations-imposed-gdpr)
- [Data Protection Commission — Right to erasure](https://www.dataprotection.ie/en/individuals/know-your-rights/right-erasure-articles-17-19-gdpr)
- [Irish Revenue — Keeping records](https://www.revenue.ie/en/starting-a-business/starting-a-business/keeping-records.aspx)
