import { AuthClient } from "@/shared/api/AuthClient";
import { HttpClient } from "@/shared/api/HttpClient";

const http = new HttpClient();
const auth = new AuthClient(http);

/** Os clientes de API da aplicação, sobre um `HttpClient` único.
 *
 * Único de propósito. O tratamento central do 401 é registrado nele uma vez, na
 * inicialização; se cada cliente criasse o seu, o registro valeria só para um e
 * as demais telas continuariam sem tratamento — a pior forma de defeito, a que
 * funciona em quase todo lugar.
 *
 * À medida que as etapas avançarem, os clientes de clientes, agenda e
 * orçamentos entram aqui. É também o ponto onde uma tela poderia ser servida
 * por um cliente falso em teste, sem tocar em `fetch`. */
export function useApi(): { http: HttpClient; auth: AuthClient } {
  return { http, auth };
}
