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

/** Ficha completa. Só chega a gestor e ao artista que cadastrou. */
export interface Client extends ClientContact {
  registeredByArtistId: string;
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
