import { computed, ref, type ComputedRef, type Ref } from "vue";

import { ApiError } from "@/shared/api/ApiError";

/** Os quatro estados de uma tela, num lugar só: carregando, com dado, vazia e
 * com erro.
 *
 * A regra de que toda tela trata os quatro já estava escrita; faltava o
 * mecanismo. Sem ele, cada tela declara `loading`, `error` e `data` à mão, e a
 * terceira esquece de zerar o erro antes de tentar de novo — deixando a
 * mensagem antiga na tela durante a nova tentativa.
 *
 * **`forbidden` é separado de `failed` de propósito.** Um 403 não muda por
 * insistir, e oferecer "tentar de novo" ali seria enganar quem clica. É essa
 * distinção que alimenta a `prop` `retryable` do `ErrorState`.
 *
 * Guarda a última operação para que `retry` não exija que a tela lembre dos
 * argumentos. */
export class AsyncState<T> {
  private readonly value = ref<T | null>(null) as Ref<T | null>;
  private readonly failure = ref<ApiError | Error | null>(null);
  private readonly running = ref(false);
  private readonly started = ref(false);
  private lastOperation: (() => Promise<T>) | null = null;

  get data(): Ref<T | null> {
    return this.value;
  }

  get isLoading(): Ref<boolean> {
    return this.running;
  }

  /** Vazio é diferente de "ainda não carregou": só vale depois da primeira
   * tentativa bem-sucedida, senão toda tela pisca "nada encontrado" antes de o
   * dado chegar. */
  get isEmpty(): ComputedRef<boolean> {
    return computed(() => {
      if (!this.started.value || this.running.value || this.failure.value) {
        return false;
      }
      const current = this.value.value;
      return current === null || (Array.isArray(current) && current.length === 0);
    });
  }

  get error(): Ref<ApiError | Error | null> {
    return this.failure;
  }

  get errorMessage(): ComputedRef<string> {
    return computed(() => this.failure.value?.message ?? "");
  }

  get isRetryable(): ComputedRef<boolean> {
    return computed(() => {
      const current = this.failure.value;
      return !(current instanceof ApiError && current.isForbidden);
    });
  }

  async run(operation: () => Promise<T>): Promise<void> {
    this.lastOperation = operation;
    this.running.value = true;
    this.failure.value = null;
    try {
      this.value.value = await operation();
      this.started.value = true;
    } catch (error) {
      this.failure.value = error instanceof Error ? error : new Error(String(error));
    } finally {
      this.running.value = false;
    }
  }

  async retry(): Promise<void> {
    if (this.lastOperation) {
      await this.run(this.lastOperation);
    }
  }
}
