import { useApi } from "@/shared/api/useApi";
import { PendingWorkStore } from "@/shared/work/PendingWorkStore";

const { scheduling, payments, quotes, clients } = useApi();
const store = new PendingWorkStore(scheduling, payments, quotes, clients);

/** Acesso à fila de pendências única da aplicação.
 *
 * Criada uma vez, no carregamento do módulo, como a sessão. Uma instância por
 * componente daria a cada um a sua própria fila, com o seu próprio ciclo de
 * atualização — quatro requisições por minuto para cada tela aberta, e um
 * contador que discordaria da lista logo abaixo dele. */
export function usePendingWork(): { pending: PendingWorkStore } {
  return { pending: store };
}
