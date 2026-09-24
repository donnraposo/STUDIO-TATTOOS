# Plano de Testes e Critérios de Aceite

**Status:** Proposta para aprovação — nenhum teste foi escrito.
**Última atualização:** 24/09/2026

> Corresponde à Fase 13 de `02_ROADMAP_PRE_IMPLEMENTACAO.md`. Cada regra crítica
> tem ao menos um cenário de sucesso e um de exceção.

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
