# Arquitetura Técnica — Proposta em Validação

**Status:** Arquitetura aprovada e em implementação.  
**Última atualização:** 26/09/2026  
**Escopo:** primeira versão do sistema interno do estúdio em Cork City.

> Este documento descreve a arquitetura da solução. A implementação foi autorizada
> em 24/09/2026 e está em andamento; o progresso por sprint fica em
> `09_ROADMAP_IMPLEMENTACAO.md`.

## 1. Objetivo e limites

O sistema apoiará proprietário, gerente, tatuadores residentes e guests na gestão de usuários, clientes, agenda de macas, orçamentos, sessões, pagamentos, repasses, pós-venda e relatórios. Clientes não terão contas.

A solução será uma aplicação web responsiva que poderá ser instalada como PWA. A PWA abrirá o mesmo sistema web em uma janela própria; não haverá aplicativo nativo separado nesta versão. Os agendamentos e demais operações que dependem de disponibilidade atualizada exigirão conexão com o sistema.

## 2. Decisões tecnológicas alinhadas

- **Backend:** Python com FastAPI.
- **Banco de dados:** PostgreSQL.
- **Containers:** os componentes da aplicação serão executados em containers Docker.
- **Frontend:** Vue 3 com TypeScript e Vite.
- **Entrega no celular:** PWA instalável; notificações push ficam para uma etapa futura.
- **Interface/API:** mesmo domínio, com o frontend na raiz e a API em `/api/v1`.
- **Autenticação web/PWA:** sessão validada pelo servidor e transportada por cookie seguro; JWT não será o mecanismo de sessão do navegador nesta versão.
- **Notificações de tentativa de agendamento bloqueada por conflito do artista:** caixa dentro do sistema e e-mail para gerente e proprietário.
- **Autenticação em dois fatores:** fora da primeira versão, conforme regra já aprovada.

O usuário aprovou documentação dessas decisões, mas ainda não autorizou implementação.

## 3. Visão geral e comunicação

```text
Navegador ou PWA instalada
          |
          | HTTPS — mesmo domínio
          v
Proxy web / entrega do frontend Vue
          |
          +---- /api/v1 ----> API FastAPI
                                  |
                                  +---- PostgreSQL
                                  +---- armazenamento privado de arquivos
                                  +---- registro de notificações e fila de envio
                                                   |
                                                   +---- serviço de e-mail
                                                   +---- Web Push (versão futura)
```

O proxy web deverá entregar os arquivos estáticos do frontend e encaminhar `/api/v1` à API. Manter a interface e a API no mesmo domínio simplifica cookies, reduz configuração de CORS e mantém a autenticação no servidor.

O FastAPI validará identidade, permissões, regras de negócio e dados de entrada. PostgreSQL será a fonte persistente para usuários, sessões, clientes, agendamentos, pagamentos, histórico e notificações. O armazenamento de imagens e comprovantes é um serviço ainda a escolher; seus metadados e vínculos permanecerão no banco.

## 4. Organização lógica do backend

Recomenda-se iniciar como **monólito modular**: uma aplicação FastAPI organizada por módulos de negócio, com uma implantação principal e sem microserviços nesta fase.

Módulos previstos:

- **Identidade e acesso:** contas, solicitações de cadastro, estado da conta, sessões e permissões.
- **Clientes:** cadastro, vínculos com artistas, duplicidades, visibilidade e histórico.
- **Agenda:** macas, disponibilidade, solicitações, aprovações, conflitos, bloqueios e remarcações.
- **Orçamentos e sessões:** aprovação, execução, conclusão e ligação com os pagamentos.
- **Financeiro:** pagamentos, sinais, devoluções, repasses e fechamento semanal.
- **Guests:** semanas pagas, acesso e atendimentos indicados pelo estúdio.
- **Pós-venda:** vencimentos, contatos, resultados, fotos e histórico.
- **Notificações:** caixa interna, e-mail, tentativas e evolução futura para push.
- **Relatórios e auditoria:** consultas autorizadas, exportações e trilha imutável.

A divisão em pacotes, nomes de arquivos e contratos detalhados dos endpoints será fechada junto ao modelo de dados e à estrutura do projeto.

## 5. Agenda e integridade contra conflitos

O backend deverá validar dois recursos independentes:

1. **Maca:** solicitações pendentes de artistas diferentes podem concorrer pela mesma maca. A aprovação não pode criar sobreposição com outro agendamento aprovado nessa maca.
2. **Artista:** o mesmo artista não pode manter solicitações pendentes ou agendamentos aprovados em intervalos sobrepostos, mesmo em macas diferentes. Uma solicitação pendente ocupa o horário daquele artista, mas não bloqueia a maca para outros artistas.

Uma colisão da agenda do artista impedirá a criação, inclusive por inclusão administrativa, e gerará notificação para gerente e proprietário dentro do sistema e por e-mail. O backend verificará a regra transacionalmente; a arquitetura do banco deverá impedir que duas operações concorrentes contornem a validação. PostgreSQL oferece tipos de intervalo e restrições de exclusão adequados para expressar regras de não sobreposição, cuja definição exata será detalhada no modelo de dados. [Documentação do PostgreSQL](https://www.postgresql.org/docs/current/rangetypes.html)

Solicitações rejeitadas e agendamentos cancelados deixam de ocupar a agenda futura, preservando seus registros históricos. Os demais estados e regras permanecem em `01_REGRAS_DE_NEGOCIO.md`.

## 6. Autenticação e segurança de sessão

O navegador receberá somente um identificador aleatório de sessão no cookie. O estado da sessão ficará no servidor, associado ao usuário e consultável/revogável pelo backend. Não guardar dados pessoais, papéis ou permissões no valor do cookie.

Requisitos alinhados:

- Cookie apenas por HTTPS em produção, com `Secure`, `HttpOnly` e política `SameSite` adequada.
- Proteção anti-CSRF para operações que alteram dados; `SameSite` é defesa adicional, não substitui o token CSRF.
- Sessão expira após 60 minutos de inatividade ou 12 horas totais.
- Bloqueio de conta e troca de senha revogam imediatamente as sessões ativas.
- Sem autenticação em dois fatores na primeira versão.
- Autorização por perfil e por vínculo com o registro; não confiar em controles apenas na interface.
- Limitar tentativas de login e evitar revelar se um e-mail existe durante login/recuperação; política e parâmetros detalhados ainda serão definidos.

JWT não será usado como sessão principal do site/PWA. A decisão pode ser revista se surgir um cliente nativo ou uma integração que realmente precise de bearer tokens. JWT assinado não é necessariamente criptografado e requer mecanismo adicional de revogação antecipada; para as necessidades atuais, sessão de servidor é mais direta. [OWASP: gestão de sessões](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [OWASP: JWT](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html)

### Biblioteca de autenticação

A biblioteca exata ainda não foi escolhida. `pwdlib` com Argon2id é a proposta para hash de senhas, conforme a documentação do FastAPI. FastAPI Users foi avaliada como opção, mas o próprio projeto informa que está em modo de manutenção; não será adotada sem avaliação adicional de compatibilidade e manutenção. A solução final deverá cobrir login, recuperação de senha, sessões revogáveis e integração com os estados e permissões próprios do estúdio. [FastAPI: hash de senhas](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/), [estado do FastAPI Users](https://github.com/fastapi-users/fastapi-users)

## 7. PWA e notificações

A primeira versão deverá ser responsiva e instalável como PWA, com manifesto e service worker. A instalação continuará apontando para o mesmo sistema web, não para um aplicativo nativo separado.

O service worker poderá manter recursos estáticos necessários à abertura da interface. Dados de clientes, pagamentos, sessões, fotos e respostas autenticadas não deverão ser armazenados em cache offline. Reservas e demais operações de negócio exigirão comunicação online com a API.

Na primeira versão, notificações serão persistidas na caixa interna e enviadas por e-mail conforme as regras de cada evento. Falha de e-mail será registrada e poderá ser reenviada sem perder a notificação interna ou alterar o estado do negócio.

Em uma etapa futura, o PWA poderá oferecer Web Push. O usuário terá de conceder permissão; o backend armazenará as inscrições por dispositivo e o worker enviará os avisos. A notificação abrirá uma rota autenticada do mesmo site. Em iOS/iPadOS, o Web Push para web apps requer que o usuário adicione a aplicação à Tela de Início. A compatibilidade deverá ser verificada nos dispositivos suportados quando essa etapa for planejada. [MDN: PWA instalável](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Installing), [MDN: Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API), [WebKit: Web Push para web apps Apple](https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/)

## 8. Containers e execução

Topologia lógica prevista:

- **Web/proxy:** entrega o frontend compilado e encaminha chamadas à API pelo mesmo domínio.
- **API:** serviço FastAPI sem estado local durável; arquivos enviados não dependerão do sistema de arquivos efêmero do container.
- **PostgreSQL:** banco persistente com volume/cópias de segurança; não perder dados ao recriar containers.
- **Worker/agendador:** execução de e-mails, lista diária de pós-venda às 08h em `Europe/Dublin`, tentativas de envio e futura entrega de push.
- **Serviços externos:** e-mail e armazenamento privado de arquivos, ainda a selecionar.

Docker será usado nos ambientes de desenvolvimento, teste e execução. A forma de hospedagem, proxy/TLS, armazenamento persistente em produção, gestão de segredos e cópias de segurança ainda será definida. O mecanismo de fila/agendamento não está escolhido; a proposta é usar uma fila durável/outbox para não perder envios quando um container reiniciar.

## 9. Decisões fechadas em 24/09/2026

As pendências desta seção foram resolvidas. O registro formal, com motivo e
alternativas avaliadas, está em `08_DECISOES_ARQUITETURA.md`.

| Pendência | Decisão | ADR |
|---|---|---|
| Biblioteca de autenticação e hash | `pwdlib` com Argon2id; sessões próprias no servidor | ADR-010 |
| Camada de dados e migrações | SQLAlchemy 2 + Alembic | ADR-009 |
| Worker, agendador e fila | Outbox em tabela, worker em container separado, sem Redis/Celery | ADR-007, ADR-008 |
| E-mail e armazenamento | Serviços gerenciados: transacional para e-mail, compatível com S3 para arquivos | ADR-006 |
| Hospedagem, proxy e TLS | VPS único com Docker Compose e Caddy com TLS automático | ADR-005 |
| Modelo de dados | Completo em `05_MODELO_DADOS.md` | ADR-011 |
| Estrutura de módulos e API | Completa em `06_ESTRUTURA_PROJETO.md` | — |
| Componente de calendário | Timeline própria em CSS Grid, sem licença paga | ADR-004 |
| Integridade da agenda | Restrições `EXCLUDE` no PostgreSQL | ADR-011 |
| Auditoria imutável | `UPDATE` e `DELETE` revogados na role da aplicação | ADR-012 |

### Pendências remanescentes, não bloqueantes

- Escolha do provedor específico de e-mail entre os candidatos; a integração fica
  isolada atrás de um adaptador e pode ser trocada sem afetar casos de uso.
- Metas de RPO e RTO: proposta inicial de backup diário cifrado enviado para fora
  do servidor, com perda máxima aceitável de 24 horas e recuperação em até 4 horas.
  Depende de confirmação do responsável.
- Comportamento da caixa interna de notificações: proposta de atualização periódica
  por consulta, sem canal em tempo real na primeira versão.
- Parâmetros finais de limite de tentativas de login.

## 10. Riscos e respostas arquiteturais

| Risco | Resposta prevista |
|---|---|
| Dupla reserva por solicitações simultâneas | Validação no backend e restrições transacionais no PostgreSQL. |
| Sessão ativa após bloqueio de usuário | Sessão armazenada no servidor e revogação imediata. |
| Perda de e-mail por reinício de container | Registro durável de notificação, worker e reenvio com idempotência. |
| Exposição de fotos ou comprovantes | Armazenamento privado, links autorizados e arquivos fora do container efêmero. |
| PWA mostrar disponibilidade antiga | Agendamento sempre validado pela API; não permitir gravação offline. |
| Dependência de biblioteca de autenticação em manutenção | Avaliar manutenção/compatibilidade antes de selecionar e isolar a integração. |

## 11. Referências técnicas

- [FastAPI — segurança e autenticação](https://fastapi.tiangolo.com/tutorial/security/)
- [PostgreSQL — tipos de intervalo](https://www.postgresql.org/docs/current/rangetypes.html)
- [Vue — TypeScript](https://vuejs.org/guide/typescript/overview)
- [FullCalendar — conectores React/Vue](https://fullcalendar.io/docs/plugin-index)
- [OWASP — gestão de sessões](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [MDN — Progressive Web Apps](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)

## 12. Próxima etapa

Continuar a Fase 12: decidir os componentes pendentes, concluir o modelo de dados e definir módulos e estrutura de projeto. Em seguida, preparar os cenários de teste e critérios de aceite da Fase 13. A implementação só poderá começar após apresentação da arquitetura completa e aprovação explícita do usuário, conforme `02_ROADMAP_PRE_IMPLEMENTACAO.md`.
