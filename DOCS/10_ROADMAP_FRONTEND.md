# Roadmap do Frontend

**Status:** Aprovado em 28/09/2026. Backend pausado temporariamente para a
construção da interface.
**Última atualização:** 28/09/2026

> **Onde fica o andamento.** O estado das sprints continua em
> [`09_ROADMAP_IMPLEMENTACAO.md`](09_ROADMAP_IMPLEMENTACAO.md), que é a fonte única.
> Este documento detalha **o que construir e em que ordem** no frontend, não o que
> já está pronto. Duas fontes de status é como a documentação começa a divergir.

## 1. Por que existe

A M7 previa toda a interface numa sprint só, depois de todo o backend. O próprio
roadmap registrava isso como risco aberto: bloco grande, sem validação incremental,
com mal-entendido de regra aparecendo tarde. A mitigação registrada — exercitar o
`/api/v1/docs` ao fim de cada sprint — nunca foi uma mitigação de verdade, porque
contrato de API não revela erro de entendimento de tela.

A decisão de antecipar uma fatia vertical está no **ADR-025**, que revê o ADR-020.

## 2. Onde o frontend está hoje

Quase no começo, e é importante não se iludir com o que existe:

| O que existe | Situação |
|---|---|
| Vue 3, TypeScript, Vite, Vitest, ESLint | Configurados e funcionando em container |
| `tokens.css` e `base.css` | Tipografia Urbanist na escala 32/24/20/18/16/14 e paleta ouro sobre preto |
| `features/dashboard/DashboardView.vue` | Tela de status da sprint 01; **será substituída** |
| `shared/api/SystemStatusClient.ts` | Único cliente HTTP, sem autenticação |
| `app/router.ts` | Uma rota, sem guarda |

**Não existe:** login, sessão no navegador, cliente HTTP autenticado, componente
compartilhado algum, nenhuma tela de negócio.

## 3. O teto: até onde a API deixa ir

O frontend não pode demonstrar o que o backend ainda não tem. Este é o limite
**hoje**, e ele muda quando a M5 e a M6 entrarem.

| Área | API pronta | Cabe na fatia antecipada |
|---|---|---|
| Autenticação e sessão | ✅ | Sim |
| Contas e permissões | ✅ | Sim, mas fica para a M7.2 por não ser preciso à demonstração |
| Clientes | ✅ | Sim |
| Macas e agenda | ✅ | Sim |
| Orçamentos e imagens de referência | ✅ | Sim |
| Sessões | ❌ M4.4 | Não |
| Pagamentos e sinal | ❌ M5 | Não |
| Repasses | ❌ M6 | Não |
| Pós-venda, relatórios, guest | ❌ Fase 2 | Não |

**A leitura honesta para a demonstração:** das duas dores que justificam o sistema,
a fatia antecipada resolve **uma inteira** — impedir choque de horário nas macas,
com o modal de conflito que não permite ignorar — e **nenhuma parte da outra**,
saber quem recebe quanto. O percentual congelado no orçamento é o mais perto que a
demonstração chega de dinheiro.

## 4. Princípios

Os três primeiros valem para todo arquivo; os demais são específicos do frontend.

- **Um componente por arquivo**, nome do arquivo igual à responsabilidade (ADR-015).
- **Nenhum valor visual fora dos tokens.** Nada de cor, espaçamento ou tamanho
  escrito direto no estilo.
- **Interface em inglês; documentação e comentários em português.**
- **A autorização no frontend é aparência, nunca garantia.** Esconder um botão que o
  perfil não pode usar é cortesia com quem olha a tela. Quem decide é o backend, que
  já recusa com 403. Nenhuma tela pode assumir que, por ter escondido a ação, ela
  está impedida.
- **Regra de negócio não mora em componente.** Cálculo, formatação de dinheiro e
  posicionamento na agenda ficam em classes próprias, testáveis sem montar tela.
- **Todo horário é exibido em `Europe/Dublin`**, nunca no fuso do navegador. A API
  devolve instantes com deslocamento; a tela converte para o fuso do estúdio. Um
  artista viajando não pode ver a agenda deslocada.
- **Toda tela trata quatro estados:** carregando, vazia, com erro e sem permissão.
  Componentes compartilhados para os quatro, para que cada tela não invente o seu.

## 5. Camadas

```text
frontend/src/
├── app/                 inicialização, rotas, guardas, casca visual
├── features/<área>/     telas e componentes daquela área
└── shared/
    ├── api/             um cliente tipado por recurso, sobre um HttpClient único
    ├── composables/     estado reativo compartilhado, como a sessão
    ├── components/      componentes base sem regra de negócio
    └── tokens.css       variáveis de design
```

**Um cliente por recurso, sobre um `HttpClient` único.** O `HttpClient` concentra o
que toda chamada precisa: cabeçalho CSRF por duplo envio, envio do cookie de sessão,
tradução de 401, 403, 409 e 422 em erros tipados. Sem essa peça única, cada tela
repetiria o tratamento e bastaria uma esquecer o 401 para o usuário ver uma tela
quebrada em vez de voltar ao login.

## 6. Etapas da fatia antecipada — M7.1

Ordem escolhida por dependência e por risco: o que é obrigatório primeiro, o que é
barato e estabelece padrão em seguida, o mais arriscado no meio — com tempo de
sobra para ele — e o que fecha a história por último.

### M7.1.1 — Casca da aplicação e acesso

**Entrega:** os três perfis entram no sistema e navegam.

| Peça | Papel |
|---|---|
| `shared/api/HttpClient.ts` | Chamada com cookie, cabeçalho CSRF e erros tipados |
| `shared/api/ApiError.ts` | Erro de API com estado e mensagem do backend |
| `shared/api/AuthClient.ts` | `login`, `logout`, `me` |
| `shared/composables/useSession.ts` | Sessão reativa da aplicação |
| `app/AppShell.vue` | Cabeçalho, navegação por perfil, área de conteúdo |
| `features/auth/LoginView.vue` | Entrada |
| `app/router.ts` | Guarda por sessão e por perfil |
| `shared/components/` | `AppButton`, `AppInput`, `AppCard`, `StatusBadge`, `LoadingState`, `EmptyState`, `ErrorState` |
| `scripts/seed_demo.py` | Dados de demonstração: contas, macas, clientes, agendamentos, orçamentos |

**Critérios de aceite:**

- Proprietário, gerente e residente entram e veem navegação diferente.
- Resposta 401 em qualquer chamada devolve ao login sem tela quebrada.
- Conta bloqueada perde o acesso na requisição seguinte, sem precisar recarregar.
- Sair encerra a sessão no servidor, não apenas no navegador.

> **O script de dados é de desenvolvimento e diz isso em voz alta.** Cria contas com
> senha conhecida; rodá-lo em produção seria abrir o sistema. Recusa-se a executar
> fora de `ENVIRONMENT=development`.

### M7.1.2 — Clientes

**Entrega:** cadastro e consulta, com os três níveis de visibilidade visíveis na
tela.

Telas e componentes: `ClientsView`, `ClientList`, `ClientForm`, `DuplicateWarning`.
Cliente de API: `ClientsClient`.

**Critérios de aceite:**

- Residente vê ficha completa apenas de quem cadastrou (RN-CLI-004).
- Duplicidade **avisa e não bloqueia**: o cliente é criado e o aviso aparece junto.
- Gestor vê e edita qualquer cliente.

Escolhida como segunda etapa por ser a de menor risco: estabelece o padrão de tela
com lista, formulário e os quatro estados, que as seguintes repetem. E é
pré-requisito da agenda — sem cliente não há reserva.

### M7.1.3 — Agenda e macas

> **A etapa de maior risco do frontend.** É o único componente sem biblioteca
> pronta (ADR-004).

**Entrega:** timeline macas × horário, com o ciclo de solicitação e decisão.

| Peça | Papel |
|---|---|
| `BoothTimeline.vue` | Grade em CSS Grid: macas no eixo Y, horas no eixo X |
| `BookingBlock.vue` | Bloco posicionado por início e duração |
| `ConflictModal.vue` | Modal da RN-AGE-007, **sem opção de ignorar** |
| `AvailabilityFilter.vue` | Dia, maca e artista |
| `BookingPlacement.ts` | **Classe pura** que converte início e fim em coluna e extensão na grade |

**`BookingPlacement` é uma classe separada de propósito.** A aritmética de posição —
minutos desde a abertura, largura proporcional, virada de horário de verão — é o que
tem chance real de estar errado, e testá-la exige montar tela nenhuma. Deixá-la
dentro do componente significaria testá-la pela aparência, ou não testá-la.

**Critérios de aceite:**

- Agenda do dia com as quatro macas e o horário de funcionamento, terça a domingo,
  10h às 20h.
- Residente solicita; gestor aprova e recusa com motivo de lista fechada.
- Conflito devolve 409 e **abre o modal com o agendamento existente**, sem caminho
  para ignorar.
- Agendamentos adjacentes, sem intervalo, aparecem encostados e não sobrepostos.
- A grade é renderizada em `Europe/Dublin` mesmo com o navegador em outro fuso.

### M7.1.4 — Orçamentos

**Entrega:** o ciclo do orçamento e as imagens de referência.

Telas e componentes: `QuotesView`, `QuoteList`, `QuoteForm`, `QuoteDecisionPanel`,
`ReferenceImageGallery`, `ReferenceImageUploader`. Cliente de API: `QuotesClient`.

**Critérios de aceite:**

- Residente cria e edita enquanto pendente; guest não vê o módulo.
- Aprovação mostra o percentual congelado, 70% ou 50% conforme a origem.
- **Editar um orçamento aprovado mostra na tela que ele voltou a pendente e que o
  percentual foi descartado.** É a regra mais fácil de parecer bug para quem opera,
  e a tela precisa explicá-la em vez de só executá-la.
- Imagens são enviadas, listadas e removidas, carregando pela rota autenticada.

## 7. O que fica para a M7.2

Depende da M5 e da M6, e entra depois delas.

| Tela | Depende de |
|---|---|
| Sessões e atendimentos | M4.4 |
| Pagamentos, devoluções e estornos | M5 |
| Repasses semanais e demonstrativo | M6 |
| Painel do proprietário e do gerente | M5 e M6 |
| Painel do residente | M6 |
| Usuários e permissões | Nada — a API está pronta, foi adiada por não ser precisa à demonstração |
| Configuração de macas e horários | RN-AGE-011, que está na F3 |

## 8. Fase 2

Painel e área do guest, pós-venda, relatórios e comparação de períodos, histórico de
auditoria, e a PWA instalável com manifesto e service worker — sem cache de dado
autenticado.

## 9. Mapa de tela, perfil e API

| Tela | Quem acessa | Endpoints |
|---|---|---|
| Login | Todos | `POST /auth/login`, `GET /auth/me`, `POST /auth/logout` |
| Clientes | Gestor vê todos; residente, os próprios | `GET/POST /clients`, `GET/PUT /clients/{id}`, `POST /clients/merge` |
| Agenda | Todos os perfis, com recortes diferentes | `GET /booths`, `GET/POST /bookings`, `/approve`, `/reject`, `/cancel`, `/reschedule` |
| Orçamentos | Gestor e residente; **guest não** | `GET/POST /quotes`, `GET/PUT /quotes/{id}`, `/approve`, `/reject` |
| Imagens de referência | Quem vê o orçamento | `GET/POST /quotes/{id}/reference-images`, `DELETE .../{image_id}`, `GET .../{image_id}/content` |

## 10. Testes

Proporcionais ao risco, como no backend, e **sem dependência nova**:

| O que | Como |
|---|---|
| `BookingPlacement` e formatação de dinheiro e data | Vitest sobre classes puras, sem montar componente |
| `HttpClient`: CSRF, 401, 403, 409, 422 | Vitest com `fetch` substituído |
| Clientes de API | Vitest, conferindo caminho, corpo e tradução de erro |
| Telas | Conferência manual contra os critérios de aceite de cada etapa |

**Por que não testes de componente agora:** exigiriam `@vue/test-utils`, e o valor
estaria em cobrir o que já está coberto pelas classes puras. Se a M7.2 mostrar
lógica presa em componente que só se testa montando, a dependência é pedida ali —
com motivo, não por antecipação.

## 11. Riscos

| Risco | Resposta |
|---|---|
| A timeline é o maior esforço sem biblioteca do projeto | Antecipada para a M7.1.3, com a aritmética isolada e testada. Antecipar é o que tira o risco da estimativa da M7.2 |
| A M5 fará a aprovação de agendamento exigir sinal confirmado | Acréscimo de indicador na tela de agenda, não reescrita. Está na tabela de pendências de costura do `09` |
| A demonstração criar a expectativa de que o financeiro existe | Dizer na reunião, com todas as letras, o que não está lá. A seção 3 deste documento serve de roteiro |
| Pausar o backend com a M4 em três quartos | A M4.4 é pequena e está declarada como retomada imediatamente após a M7.1 |
| Tokens de design nunca exercitados em tela real | A M7.1.1 constrói os componentes base antes de qualquer tela de negócio, e é ali que a paleta ouro sobre preto é testada de verdade |
