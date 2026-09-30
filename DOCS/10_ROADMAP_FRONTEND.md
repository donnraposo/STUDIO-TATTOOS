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

> Esta seção descrevia o estado de 28/09/2026, quando nada existia. **Reescrita em
> 30/09/2026**, ao fim da M7.1 — cabeçalho que descreve um passado é a armadilha
> que a `CLAUDE.md` seção 7 chama de status congelado.

A fatia antecipada está inteira: quatro telas de negócio sobre a casca, com
sessão, cliente HTTP autenticado e biblioteca de componentes exercitada.

| O que existe | Situação |
|---|---|
| Vue 3, TypeScript, Vite, Vitest, ESLint | Em container, com lint e tipos limpos |
| `tokens.css` e `base.css` | Escala 32/24/20/18/16/14, paleta ouro sobre preto, e a pílula única de campo |
| Casca, sessão e guarda de rota | `AppShell`, `SessionStore`, `HttpClient` com CSRF e 401 central |
| 17 componentes base | Todo controle passa por eles; uma exceção declarada (`BookingBlock`) |
| Clientes, agenda, orçamentos | `ClientsView`, `SchedulingView` com a timeline, `QuotesView` |
| Painel com o que espera decisão | `HomeView` com a fila das três origens e o contador na casca |
| 90 testes | Classes puras, sem montar componente |

**Não existe ainda:** sessões, pagamentos, repasses e gestão de contas — e é
isso que falta da M7.2.

**O `DashboardView` da sprint 01 continua em `/status`**, agora como tela de
diagnóstico do gestor, e não como página inicial.

## 3. O teto: até onde a API deixa ir

O frontend não pode demonstrar o que o backend ainda não tem. Este é o limite
**hoje**, e ele muda a cada sprint de backend.

| Área | API pronta | Tela existe |
|---|---|---|
| Autenticação e sessão | ✅ | ✅ M7.1.1 |
| Contas e permissões | ✅ | ❌ M7.2 — adiada por não ser precisa à demonstração |
| Clientes | ✅ | ✅ M7.1.2 |
| Macas e agenda | ✅ | ✅ M7.1.3 |
| Orçamentos e imagens de referência | ✅ | ✅ M7.1.4 |
| Sessões | ✅ M4.4 | ❌ M7.2 |
| Pagamentos e sinal | ✅ M5 | ❌ M7.2 |
| Repasses | ❌ M6 | ❌ M7.2 |
| Pós-venda, relatórios, guest | ❌ Fase 2 | ❌ Fase 2 |

**O teto deixou de ser o backend.** Até 29/09/2026 a coluna da API era o limite;
hoje o backend está à frente da interface em duas sprints inteiras. Sessões e
pagamentos existem e nenhuma tela os consome.

**A leitura honesta para a demonstração:** das duas dores que justificam o
sistema, a interface resolve **uma inteira** — impedir choque de horário nas
macas, com o modal de conflito que não permite ignorar — e **nenhuma parte da
outra**, saber quem recebe quanto. O percentual congelado no orçamento é o mais
perto que a demonstração chega de dinheiro.

> **Uma tela entregue mudou de comportamento sem mudar de código.** A M5 fechou o
> portão da RN-AGE-005, e a caixa "Approve straight away" do `BookingForm` passou
> a ser recusada pelo backend para residente: criar já aprovado só vale onde não
> há sinal a confirmar (ADR-027). A tela ainda oferece a caixa — é a próxima
> pendência da M7.2, agora que a M7.2.1 fechou.

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

## 4.0 Linguagem visual

**Fonte:** o monograma do estúdio, em ouro sobre preto, e um conjunto de telas de
referência de outro produto, entregues em 28/09/2026 como padrão de desenho a
seguir. **As cores são as nossas; a estrutura é a da referência.** Onde a
referência usa carmim como destaque, usamos o ouro do monograma.

### O que foi extraído da referência

| Padrão | Como se aplica aqui |
|---|---|
| **Cromo escuro, trabalho claro** | Barra lateral e cartões herói em preto; área de trabalho em off-white levemente quente, para conversar com o ouro |
| **Barra lateral, não superior** | A lista de telas do MVP chega a nove itens (`01` §10); no topo, metade sumiria atrás de um menu já na terceira sprint |
| **Kicker sobre todo título** | Rótulo em caixa alta com espaçamento largo, acima de cada título. É o que dá ritmo à página e diz onde a pessoa está antes de dizer o que há ali |
| **Título de display grande** | Escala própria, acima dos 32px do style guide original, com entrelinha apertada e muito silêncio em volta |
| **Tudo em pílula** | Botões, campos, item ativo do menu e selos. O campo tem preenchimento sutil em vez de borda forte, para não competir com o botão |
| **Cartão herói** | Retângulo muito arredondado, fundo escuro, título grande e **uma** ação clara. Duas ações de igual peso num herói é a forma mais rápida de a tela não dizer nada |
| **Destaque com parcimônia** | O ouro aparece no kicker sobre escuro, no botão primário, no avatar e no item ativo. Em mais lugares, deixaria de destacar |

### O banner

`frontend/public/brand/banner.svg`, usado no cartão herói e no lado de marca do
login. **É SVG e não fotografia**, por três motivos: pesa poucos kilobytes e escala
sem perda; nasce das formas do próprio monograma, sem depender de banco de imagens
cujo direito de uso teria de ser verificado; e é escuro e calmo do lado esquerdo de
propósito, que é onde o texto branco se apoia — uma foto de estúdio, com pontos
claros imprevisíveis, deixaria a leitura refém do recorte.

**O texto não é embutido na imagem.** Ele é marcação por cima, para poder ser
traduzido, reescrito e reposicionado sem gerar imagem nova.

### Componentes que sustentam o padrão

| Componente | Existe para |
|---|---|
| `SectionKicker` | O rótulo em caixa alta, que aparece em toda tela |
| `PageHeader` | Abertura de tela: kicker, título de display e ações. Nenhuma tela decide sozinha o tamanho do próprio título |
| `HeroBanner` | O cartão herói, com o banner de fundo |

### O que ainda não está decidido

- **Ícones.** A referência usa ícone ao lado de cada item do menu e dentro dos
  botões. Ainda não há conjunto escolhido, e escolher significa dependência nova ou
  desenhar à mão. Fica para antes da M7.1.2, quando a navegação cresce.
- **Densidade da agenda.** A referência é espaçosa, e a timeline de macas precisa
  do oposto: muita informação num dia. É o primeiro ponto onde o padrão vai ter de
  ceder, e a decisão pertence à M7.1.3.

## 4.1 SOLID aplicado ao frontend

Os cinco princípios não são decoração aqui; cada um vira uma regra verificável.

| Princípio | Como se manifesta nesta base |
|---|---|
| **Responsabilidade única** | Um componente **compõe** ou **apresenta**, nunca os dois. Tela busca dado e orquestra; componente de apresentação recebe por `props` e devolve por `emits`. Cálculo não é responsabilidade de nenhum dos dois: vai para classe pura |
| **Aberto/fechado** | Variação por mapa tipado. Um `StatusBadge` traduz estado em token por um `Record<BookingStatus, BadgeTone>`; acrescentar estado é uma linha de dados. Cadeia de `v-if` obriga a editar o componente a cada estado novo, e é onde se esquece um |
| **Substituição de Liskov** | Todo campo de formulário honra o mesmo contrato: `modelValue`, `update:modelValue`, `disabled`, `error`. O formulário troca um campo por outro sem saber qual é |
| **Segregação de interface** | `props` pequenas e específicas. Um componente que precisa de três campos não recebe a entidade inteira. Componente com quinze `props` e oito booleanos são vários componentes disfarçados de um |
| **Inversão de dependência** | Tela depende do cliente tipado do recurso, nunca de `fetch`. O `HttpClient` é a única costura com a rede; trocar transporte não toca em tela nenhuma |

**A fronteira que mais importa é a do meio.** Um componente de apresentação que
importa um cliente de API deixa de ser reutilizável e passa a ser testável só com
rede falsa. A verificação está em `CLAUDE.md` e não deve devolver nada:

```bash
grep -rln "shared/api" frontend/src/features --include=*.vue | grep -v "View\.vue"
```

## 4.2 Padrão de componentização

**Três camadas, com fronteira rígida:**

| Camada | Pasta | Conhece domínio | Fala com a API | Exemplo |
|---|---|---|---|---|
| Base | `shared/components` | Não | Não | `AppButton`, `AppInput`, `EmptyState` |
| Apresentação de domínio | `features/<x>/components` | Sim | **Não** | `BookingBlock`, `ClientList` |
| Tela | `features/<x>/*View.vue` | Sim | **Sim, só ela** | `SchedulingView` |

**Nomenclatura**, para que o nome do arquivo já diga a camada:

| Sufixo ou prefixo | Significa |
|---|---|
| `App*` | Componente base, sem domínio |
| `*View` | Tela, ligada a uma rota |
| `*Modal` | Sobreposição com decisão |
| `*Form` | Formulário de uma entidade |
| `*List` | Coleção sem lógica de busca |

**Regras que valem para todo componente:**

- `<script setup lang="ts">`, com `defineProps<T>()` e `defineEmits<T>()` tipados.
  Nada de `props` declaradas só em tempo de execução.
- Um componente por arquivo, nome do arquivo igual ao do componente (ADR-015).
- **Conteúdo variável entra por `slot`, não por `prop` booleana.** Três booleanos
  que ligam pedaços de marcação são três componentes esperando para nascer.
- Estados de carregando, vazio, erro e sem permissão usam os componentes
  compartilhados. Nenhuma tela desenha o seu próprio "nada encontrado".

## 4.2.1 O que os componentes base garantem

**Todo controle passa por um componente base.** Nenhum `<button>`, `<input>`,
`<select>` ou `<textarea>` cru fora de `shared/components` — tamanho e cor vêm do
componente, e controle solto sai do padrão já na primeira tela. A verificação
está no `CLAUDE.md`.

| Peça | Garante |
|---|---|
| `AppButton` | **Todos os tons carregam a mesma borda**, transparente quando não deve aparecer. Sem isso o tom com borda fica mais alto que o sem borda, e dois botões lado a lado nunca se alinham |
| `AppField` | Rótulo, marca de obrigatório e mensagem de erro, uma vez só. `AppInput` e `AppSelect` repetiam os três |
| `.control` em `base.css` | A pílula: altura, respiro, borda, raio e preenchimento. Campo de texto e seletor precisam ser **indistinguíveis em altura**, e três cópias divergiriam no primeiro ajuste |
| `AppModal` | Rolagem própria. Sem ela, num celular deitado o modal passa das duas bordas e o topo fica inalcançável — o primeiro campo some |
| `AppTextarea` | Mesmo contrato do `AppInput` e mesma pílula, com o raio aberto: numa caixa de várias linhas o canto arredondado dobraria as pontas do texto para dentro |
| `AppBadgeCount` | **Some quando é zero.** Um contador mostrando "0" ocupa o mesmo espaço e a mesma atenção de um que mostra "3", e ensina o olho a ignorá-lo — o oposto do que ele existe para fazer |
| `AppFileInput` | Esconde o `<input type="file">` — cujo botão nativo nenhum navegador deixa estilizar por completo — atrás de um `AppButton`. Escondido com `opacity`, **não** com `display: none`, que o tiraria do alcance do teclado. Limpa o valor depois de cada escolha, senão escolher o mesmo arquivo duas vezes não dispara evento e parece travamento |

**Uma exceção, declarada:** `BookingBlock` usa `<button>` cru. Não é botão do
sistema, é superfície posicionada na grade, com largura vinda de `grid-column` e
tons ditados pelo estado do agendamento. Forçá-lo no `AppButton` significaria
sobrescrever tudo o que o `AppButton` padroniza.

## 4.2.2 Responsividade

Dois pontos de quebra, e um comportamento decidido por tela em cada um.

| Tela | Em 64rem (tablet) | Em 40rem (celular) |
|---|---|---|
| Casca | Lateral vira barra fixa no topo | Navegação rola na horizontal; rótulo de seção e nome completo somem |
| Cabeçalho de página | — | Título e ações empilham; as ações ocupam a largura |
| Modal | — | Ocupa a largura, respiro menor, ações em coluna |
| Timeline | — | Coluna de macas encolhe. **A grade continua rolando na horizontal** |
| Formulários | — | Campos de hora empilham |
| Lista de clientes | — | Nome em cima, ação embaixo |

**A timeline não se comprime de propósito.** Espremer dez horas em 375px
tornaria os blocos ilegíveis, e agenda que não se lê não serve. Rolagem
horizontal é a resposta certa aqui, não uma limitação.

## 4.3 Padrão de CSS

**Todo valor visual vem de `tokens.css`.** Nenhuma cor, espaçamento, tipografia,
raio, sombra ou duração escrita dentro de componente. `tokens.css` e `base.css` são
os únicos arquivos onde literal é permitido.

**Valor novo vira token, decidido uma vez.** Se um componente precisa de um
espaçamento que não existe na escala, a pergunta certa não é "qual valor uso aqui",
é "por que a escala não cobre este caso". Inventar o valor no componente resolve a
tela e estraga o sistema.

- `<style scoped>` sempre; estilo global apenas em `base.css`.
- **Sem `:deep()` alcançando o interior de outro componente.** Isso transforma o
  detalhe de implementação dele em contrato público, e o próximo que reorganizar a
  marcação quebra um estilo que mora em outro arquivo.
- Layout por Grid e Flex. Posição em pixel só na timeline, e mesmo lá por grade
  (ADR-004).
- Mobile primeiro.

### A única exceção, e por que ela existe

**Variável CSS não funciona dentro de `@media`.** `@media (max-width: var(--bp-sm))`
é inválido: a condição da consulta é avaliada antes de o custom property existir.
Não é limitação do projeto, é do CSS.

Então os pontos de quebra são **a única exceção** à regra de nenhum literal em
componente, e ela é contida assim:

- Os valores são declarados uma vez, em comentário no topo de `tokens.css`, e
  nenhum outro valor de quebra pode aparecer.
- A verificação ignora linhas de `@media` — e só elas.
- Se um dia a lista crescer a ponto de incomodar, a saída é `@custom-media` por
  plugin de PostCSS, que é dependência nova e será pedida com motivo.

**Um grupo de token ainda falta** e entra na M7.1.1, antes da primeira tela: as
**camadas de `z-index`**. Sem elas, o modal de conflito e o cabeçalho fixo da
timeline vão disputar sobreposição com números escolhidos no susto.

```bash
# Nenhuma das duas buscas pode devolver resultado
grep -rnE '#[0-9a-fA-F]{3,8}|rgba?\(|hsla?\(' frontend/src --include=*.vue
grep -rnE '[0-9](px|rem|em)\b' frontend/src --include=*.vue | grep -v '@media'
```

Rodando hoje, a segunda busca aponta `minmax(10rem, 1fr)` na tela de status da
sprint 01 — medida de trilha de grade escrita à mão. Ela sai na M7.1.1 junto com a
tela, e o valor equivalente nasce como token.

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
| `shared/components/` | `AppButton`, `AppInput`, `AppSelect`, `AppTextarea`, `AppCheckbox`, `AppFileInput`, `AppField`, `AppCard`, `AppModal`, `StatusBadge`, `LoadingState`, `EmptyState`, `ErrorState`, e — vindos da referência — `SectionKicker`, `PageHeader`, `HeroBanner`, `BrandLockup` |
| `shared/format/` | `StudioClock` e `MoneyFormatter`, classes puras |
| `shared/async/` | `AsyncState`, o mecanismo dos quatro estados |
| `shared/tokens.css` | Camadas de `z-index`, escala de display, kicker, largura da lateral e preenchimento de campo |

> **Entregue em 28/09/2026, com duas pendências.** O `scripts/seed_demo.py` não foi
> construído e os critérios de aceite não foram verificados, por conflito de porta
> com outro projeto na máquina. Detalhe na evidência da M7.1.1 em
> [`09_ROADMAP_IMPLEMENTACAO.md`](09_ROADMAP_IMPLEMENTACAO.md).
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
| `BenchTimeline.vue` | Grade em CSS Grid: macas no eixo Y, horas no eixo X |
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

### M7.1.4 — Orçamentos ✅

**Entrega:** o ciclo do orçamento e as imagens de referência. Concluída em
29/09/2026.

Telas e componentes: `QuotesView`, `QuoteList`, `QuoteForm`, `QuoteDetail`,
`ReferenceImages`. Cliente de API: `QuotesClient`. Classes puras:
`QuoteDraftCheck` e `QuoteDisplay`, mais `ByteSize` em `shared/format`.

> **Três componentes viraram dois, e o nome mudou.** O plano previa
> `QuoteDecisionPanel`, `ReferenceImageGallery` e `ReferenceImageUploader`.
> Decisão e leitura são o mesmo modal — separá-los obrigaria a duplicar os campos
> do orçamento nos dois —, e galeria e envio são a mesma lista: o botão de enviar
> mora no cabeçalho dela. `QuoteDetail` e `ReferenceImages` é o que existe.

**Critérios de aceite, todos verificados com dados reais:**

- Residente cria e edita enquanto pendente; guest não vê o módulo.
- Aprovação mostra o percentual congelado, 70% ou 50% conforme a origem.
- **Editar um orçamento aprovado mostra na tela que ele voltou a pendente e que o
  percentual foi descartado.** É a regra mais fácil de parecer bug para quem opera,
  e a tela precisa explicá-la em vez de só executá-la. O aviso aparece **antes** de
  salvar, com o percentual que será perdido escrito nele.
- Imagens são enviadas, listadas e removidas, carregando pela rota autenticada.

**Dinheiro é texto do começo ao fim.** `Quote.totalValue` é `string`, não
`number`: a API devolve decimal exato e converter para `number` reintroduziria o
arredondamento binário que o `Numeric(12, 2)` do banco existe para evitar. Onde a
tela precisa somar — sessões × valor por sessão, para o aviso da RN-PAG-001 — a
conta é feita **em centavos inteiros** dentro de `QuoteDraftCheck`.

**O que a tela avisa mas não impede.** A RN-PAG-001 diz que a soma das sessões não
passa do total aprovado, e o backend não recusa esse caso hoje. Bloquear no
navegador criaria uma trava que só existe ali, e daria a impressão de uma garantia
que o sistema não tem. O aviso informa; o que impede é o que o servidor recusa.

## 7. O que fica para a M7.2

| Tela | Depende de | Situação da dependência |
|---|---|---|
| **Painel do gestor com o que está esperando decisão** | RN-AGE-012 e seção 10.1 | ✅ **Etapa M7.2.1, concluída em 30/09/2026** |
| Corrigir "Approve straight away" no `BookingForm` | ADR-027 | ✅ Pronta — a tela é que ficou para trás |
| Sinal: registrar, confirmar, recusar e devolver | M5 | ✅ Pronta |
| Sessões e atendimentos | M4.4 | ✅ Pronta |
| Repasses semanais e demonstrativo | M6 | ❌ Não iniciada |
| Painel do proprietário e do gerente | M5 e M6 | Metade pronta |
| Painel do residente | M6 | ❌ Não iniciada |
| Usuários e permissões | Nada — a API está pronta, foi adiada por não ser precisa à demonstração | ✅ Pronta |
| Configuração de macas e horários | RN-AGE-011, que está na F3 | ❌ Fase 3 |

**A ordem mudou de critério.** Quando a M7.2 foi planejada, ela esperava o
backend. Agora espera só a M6 — e as três primeiras linhas da tabela podem
começar a qualquer momento. A primeira delas é correção de defeito, não tela
nova: o `BookingForm` oferece uma ação que o servidor recusa.

## 7.1 Etapa M7.2.1 — Painel do gestor: o que está esperando decisão ✅

> **Antecipada a pedido do estúdio e concluída em 30/09/2026.** Não dependia da
> M6. A evidência fica no `09`, como sempre.

**O problema.** O gerente precisa abrir o calendário para descobrir se existe
solicitação de agendamento. Se não abrir, não sabe; se abrir e não reparar, passa
batido. Uma solicitação esquecida é um horário que o cliente acha reservado e o
estúdio não confirmou.

**A regra já previa.** A RN-AGE-012 diz que "uma nova solicitação **aparecerá no
painel** de gerente e proprietário", e a seção 10.1 lista o que esse painel mostra.
O `HomeView` entregue na M7.1.1 é marcador de lugar.

**Entrega:** a área de pendências no painel do gestor, com três origens, e um
contador na barra lateral visível em **toda** tela.

**O contador é o que resolve a dor, e por isso mora na casca.** A área no painel
ajuda quem já está no painel; o problema relatado é justamente não estar. Na
lateral, o número acompanha o gerente onde quer que ele esteja no sistema.

Telas e componentes previstos:

| Peça | Camada | Papel |
|---|---|---|
| `PendingWorkStore.ts` | `shared/work` | Estado único da aplicação, como o `SessionStore`. É o que permite o contador viver na casca sem ela falar com a API. **O ciclo de um minuto mora aqui** |
| `PendingWorkAssembler.ts` | `shared/work` | Classe pura: monta a fila única das três origens e a ordena. 7 testes, sem montar tela |
| `PendingWork.ts` | `shared/domain` | O item achatado que a lista desenha — nem o agendamento inteiro, nem o orçamento inteiro |
| `PaymentsClient.ts` | `shared/api` | Pagamentos e sinal. Sem método de exclusão, porque não há rota: pagamento nunca é apagado (RN-PAG-007) |
| `AppBadgeCount.vue` | base | Contador em pílula. **Some quando é zero** — um contador mostrando "0" ensina o olho a ignorá-lo |
| `PendingWorkList.vue` | apresentação | Uma lista, não três. Recebe por `props`, devolve por `emits` |
| `HomeView.vue` | tela | **Lê** o estado compartilhado; não o busca |
| `AppShell.vue` | casca | Lê o estado, desenha o contador e decide ligar ou desligar o ciclo conforme o perfil |

**Por que um store e não uma chamada na casca.** A convenção diz que só a tela
fala com a API, e o contador precisa do dado fora de qualquer tela. O caminho que
não quebra a regra é o mesmo já usado pela sessão: estado único em `shared/`,
que busca, e casca e tela que apenas leem.

**Por que o ciclo mora no estado e não na tela do painel.** Se a tela carregasse,
o contador só saberia de algo novo enquanto o gestor estivesse no painel —
justamente onde ele não está quando o problema acontece.

**Por que a casca liga e desliga o ciclo.** É nela que se sabe quem entrou. O
residente não vê a fila do estúdio, e buscá-la para ele seria pedir ao servidor
um 403 por minuto. Conferido: entrando como residente, zero requisições em 15
segundos de observação.

**Falhar não derruba nada.** Uma requisição que não volta deixa o número como
estava e o ciclo seguinte tenta de novo. Contador momentaneamente velho é muito
melhor do que tela quebrada — e nada se perde, porque a pendência continua onde
estava.

**Critérios de aceite:**

- O contador aparece na barra lateral em toda tela, e some quando não há
  pendência.
- Gestor vê as três origens — solicitações de agendamento, pagamentos aguardando
  confirmação e orçamentos pendentes. Residente e guest não veem a área nesta
  etapa; o painel deles é a M7.2.5, conforme a seção 10.2.
- Cada item leva à tela onde a decisão é tomada, sem o gestor procurar.
- A área se atualiza sozinha a cada minuto, sem recarregar a página.
- Zero pendências mostra estado vazio explícito, não área em branco.
- Responsivo: no celular o contador acompanha a navegação horizontal da casca.

**Os cinco foram exercitados contra a aplicação rodando**, e o mais importante
deles precisou do relógio: um sinal foi confirmado pela API, sem tocar na tela, e
o contador caiu de 4 para 3 em 20 segundos.

**O que esta etapa não é.** Não é a caixa de notificações do modelo de dados — a
tabela `notification` e o `email_outbox` servem ao e-mail e ao worker, declarados
na sprint F2. Aqui não há tabela nova: pendência é estado que já existe nas
tabelas de agendamento, pagamento e orçamento.

## 8. Fase 2

Painel e área do guest, pós-venda, relatórios e comparação de períodos, histórico de
auditoria, e a PWA instalável com manifesto e service worker — sem cache de dado
autenticado.

## 9. Mapa de tela, perfil e API

| Tela | Quem acessa | Endpoints |
|---|---|---|
| Login | Todos | `POST /auth/login`, `GET /auth/me`, `POST /auth/logout` |
| Clientes | Gestor vê todos; residente, os próprios | `GET/POST /clients`, `GET/PUT /clients/{id}`, `POST /clients/merge` |
| Agenda | Todos os perfis, com recortes diferentes | `GET /benches`, `GET/POST /bookings`, `/approve`, `/reject`, `/cancel`, `/reschedule` |
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
| A M5 fará a aprovação de agendamento exigir sinal confirmado | ⚠️ **Concretizado em 30/09/2026, e maior do que o previsto.** Não é só indicador: a caixa "Approve straight away" deixou de funcionar para residente (ADR-027). Registrado nas pendências de costura do `09` |
| O backend andar mais rápido que a interface | Aconteceu: M4.4 e M5 entregues sem tela. O risco não é técnico, é de expectativa — quem vê a demonstração não sabe o que existe por trás. A seção 3 deste documento serve de roteiro na reunião |
| A demonstração criar a expectativa de que o financeiro existe | Dizer na reunião, com todas as letras, o que não está lá. A seção 3 deste documento serve de roteiro |
| Pausar o backend com a M4 em três quartos | A M4.4 é pequena e está declarada como retomada imediatamente após a M7.1 |
| Tokens de design nunca exercitados em tela real | A M7.1.1 constrói os componentes base antes de qualquer tela de negócio, e é ali que a paleta ouro sobre preto é testada de verdade |
