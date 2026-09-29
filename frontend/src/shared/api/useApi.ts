import { AccountsClient } from "@/shared/api/AccountsClient";
import { AuthClient } from "@/shared/api/AuthClient";
import { ClientsClient } from "@/shared/api/ClientsClient";
import { HttpClient } from "@/shared/api/HttpClient";
import { SchedulingClient } from "@/shared/api/SchedulingClient";

const http = new HttpClient();
const auth = new AuthClient(http);
const clients = new ClientsClient(http);
const scheduling = new SchedulingClient(http);
const accounts = new AccountsClient(http);

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
export function useApi(): {
  http: HttpClient;
  auth: AuthClient;
  clients: ClientsClient;
  scheduling: SchedulingClient;
  accounts: AccountsClient;
} {
  return { http, auth, clients, scheduling, accounts };
}
