import { AsyncState } from "@/shared/async/AsyncState";

/** Um estado assíncrono novo para a tela que chamar.
 *
 * Ao contrário da sessão, que é única na aplicação, cada tela — e cada lista
 * dentro dela — tem o seu: o carregamento da agenda não pode apagar a mensagem
 * de erro da lista de macas ao lado. */
export function useAsyncState<T>(): AsyncState<T> {
  return new AsyncState<T>();
}
