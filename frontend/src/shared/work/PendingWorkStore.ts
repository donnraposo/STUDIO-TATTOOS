import { computed, readonly, ref, type ComputedRef, type DeepReadonly, type Ref } from "vue";

import type { ClientsClient } from "@/shared/api/ClientsClient";
import type { PaymentsClient } from "@/shared/api/PaymentsClient";
import type { QuotesClient } from "@/shared/api/QuotesClient";
import type { SchedulingClient } from "@/shared/api/SchedulingClient";
import type { PendingWorkItem } from "@/shared/domain/PendingWork";
import { PendingWorkAssembler } from "@/shared/work/PendingWorkAssembler";

/** O que está esperando decisão do gestor (RN-AGE-012 e seção 10.1).
 *
 * **Estado único da aplicação, como a sessão, e pela mesma razão.** O contador
 * precisa aparecer na barra lateral, que é casca e não tela — e a convenção diz
 * que só a tela fala com a API. Um estado compartilhado em `shared/` resolve os
 * dois: ele busca, a casca lê, a tela lê o mesmo.
 *
 * **O ciclo de atualização mora aqui, e não na tela do painel.** Se a tela
 * carregasse, o contador só saberia de algo novo enquanto o gestor estivesse no
 * painel — justamente onde ele não está quando o problema acontece. Com o ciclo
 * no estado, o número acompanha o gestor em qualquer tela.
 *
 * **Falhar não derruba nada.** Uma requisição que não volta deixa o número como
 * estava, e o ciclo seguinte tenta de novo. Um contador momentaneamente velho é
 * muito melhor do que uma tela quebrada — e o gestor não perde nada, porque a
 * pendência continua onde estava.
 *
 * As quatro consultas vão juntas a cada ciclo, incluindo a de clientes, que
 * serve só para dar nome aos itens. É junção sobre conjunto pequeno, como já se
 * faz na agenda; o gatilho para mudar isso é volume, não estética. */
export class PendingWorkStore {
  /** Um minuto. O gerente fica com o sistema aberto durante o expediente, e uma
   * solicitação que chega às 14h05 não pode esperar ele navegar. */
  static readonly INTERVAL_MS = 60_000;

  private readonly scheduling: SchedulingClient;
  private readonly payments: PaymentsClient;
  private readonly quotes: QuotesClient;
  private readonly clients: ClientsClient;
  private readonly assembler: PendingWorkAssembler;

  private readonly current = ref<PendingWorkItem[]>([]);
  private readonly loading = ref(false);
  private timer: ReturnType<typeof setInterval> | null = null;

  constructor(
    scheduling: SchedulingClient,
    payments: PaymentsClient,
    quotes: QuotesClient,
    clients: ClientsClient,
    assembler: PendingWorkAssembler = new PendingWorkAssembler(),
  ) {
    this.scheduling = scheduling;
    this.payments = payments;
    this.quotes = quotes;
    this.clients = clients;
    this.assembler = assembler;
  }

  get items(): DeepReadonly<Ref<PendingWorkItem[]>> {
    return readonly(this.current);
  }

  get count(): ComputedRef<number> {
    return computed(() => this.current.value.length);
  }

  get isLoading(): DeepReadonly<Ref<boolean>> {
    return readonly(this.loading);
  }

  /** Carrega agora e passa a repetir. Chamar duas vezes não cria dois ciclos. */
  start(): void {
    void this.refresh();
    if (this.timer === null) {
      this.timer = setInterval(() => void this.refresh(), PendingWorkStore.INTERVAL_MS);
    }
  }

  /** Para o ciclo e esquece o que sabia.
   *
   * Esquecer importa: quem sai da conta não pode deixar na tela o número de
   * pendências do estúdio para o próximo que entrar. */
  stop(): void {
    if (this.timer !== null) {
      clearInterval(this.timer);
      this.timer = null;
    }
    this.current.value = [];
  }

  async refresh(): Promise<void> {
    this.loading.value = true;
    try {
      const [bookings, payments, quotes, clients] = await Promise.all([
        this.scheduling.listPending(),
        this.payments.listAwaitingConfirmation(),
        this.quotes.listPending(),
        this.clients.list(),
      ]);
      this.current.value = this.assembler.assemble({
        bookings,
        payments,
        quotes,
        clientNames: Object.fromEntries(clients.map((client) => [client.id, client.name])),
      });
    } catch {
      // Silêncio deliberado: ver o comentário da classe. O ciclo seguinte tenta
      // de novo, e o 401 já tem tratamento central no `HttpClient`.
    } finally {
      this.loading.value = false;
    }
  }
}
