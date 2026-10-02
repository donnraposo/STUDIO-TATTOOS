/** Contato do cliente: o que qualquer artista autorizado a atender pode ver.
 *
 * É a projeção reduzida da RN-CLI-004 — o que o estúdio entrega ao artista
 * quando lhe indica um cliente cadastrado por outra pessoa. Sem data de
 * cadastro, sem quem cadastrou, sem histórico. */
export interface ClientContact {
  id: string;
  name: string;
  phone: string;
  instagram: string | null;
}

/** De onde o cliente veio (RN-CLI-002).
 *
 * Separado da origem do orçamento de propósito: os nomes se parecem e os fatos
 * não são o mesmo. Este diz de onde o cliente veio, uma vez; aquele diz o que
 * vale **neste** atendimento, e pode mudar a cada um. */
export type ClientSource = "ARTIST" | "STUDIO";

/** Ficha completa. Só chega a gestor e ao artista que cadastrou. */
export interface Client extends ClientContact {
  registeredByArtistId: string;
  /** Quem **trouxe** o cliente. Nulo significa indicação do estúdio — a
   * ausência é o dado, e não a falta dele.
   *
   * Não se confunde com `registeredByArtistId`, que é quem digitou o cadastro e
   * decide a visibilidade da ficha (RN-CLI-004). Os dois coincidem no caso
   * corrente e divergem quando o gestor cadastra por alguém (RN-GST-005). */
  broughtByArtistId: string | null;
  createdAt: string;
}

/** Distingue as duas formas que a API devolve no detalhe de um cliente.
 *
 * O backend decide qual mandar pelo formato da resposta, não por um filtro na
 * rota, então a interface recebe **menos campos** em vez de um 403. A tela
 * precisa saber disso para dizer ao artista que aquilo não é a ficha inteira —
 * sem o aviso, ele concluiria que o cliente não tem histórico, quando na
 * verdade ele é que não pode vê-lo. */
export function isFullRecord(client: ClientContact | Client): client is Client {
  return "registeredByArtistId" in client;
}
