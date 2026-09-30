/** As três origens de pendência do painel do gestor (seção 10.1).
 *
 * O tipo existe para que a lista seja **uma só**. Três listas separadas na tela
 * obrigariam o gestor a olhar três lugares — exatamente o problema que a área
 * resolve, em escala menor. */
export type PendingWorkKind = "BOOKING" | "PAYMENT" | "QUOTE";

/** Um item esperando decisão, na forma que a tela mostra.
 *
 * Achatado de propósito: a lista não precisa do agendamento inteiro nem do
 * orçamento inteiro, precisa de quem é, o quê, desde quando, e para onde ir.
 * Carregar os registros completos faria a área depender do formato de três
 * módulos, e qualquer mudança em um deles mexeria nela.
 *
 * `since` é o instante em que o item passou a esperar — é ele que ordena a
 * lista e o que diz ao gestor o que está parado há mais tempo. */
export interface PendingWorkItem {
  id: string;
  kind: PendingWorkKind;
  title: string;
  detail: string;
  since: string;
  /** Nome da rota que decide este item. A lista não navega: devolve a intenção
   * e a tela decide, como manda a fronteira entre camadas. */
  route: string;
}
