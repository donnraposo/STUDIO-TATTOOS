import { AccountsClient } from "@/shared/api/AccountsClient";
import { AuthClient } from "@/shared/api/AuthClient";
import { ClientsClient } from "@/shared/api/ClientsClient";
import { HttpClient } from "@/shared/api/HttpClient";
import { PaymentsClient } from "@/shared/api/PaymentsClient";
import { PayoutsClient } from "@/shared/api/PayoutsClient";
import { QuotesClient } from "@/shared/api/QuotesClient";
import { SchedulingClient } from "@/shared/api/SchedulingClient";
import { SessionsClient } from "@/shared/api/SessionsClient";

const http = new HttpClient();
const auth = new AuthClient(http);
const clients = new ClientsClient(http);
const scheduling = new SchedulingClient(http);
const accounts = new AccountsClient(http);
const quotes = new QuotesClient(http);
const payments = new PaymentsClient(http);
const payouts = new PayoutsClient(http);
const sessions = new SessionsClient(http);

/** Os clientes de API da aplicação, sobre um `HttpClient` único.
 *
 * Único de propósito. O tratamento central do 401 é registrado nele uma vez, na
 * inicialização; se cada cliente criasse o seu, o registro valeria só para um e
 * as demais telas continuariam sem tratamento — a pior forma de defeito, a que
 * funciona em quase todo lugar.
 *
 * É também o ponto onde uma tela poderia ser servida por um cliente falso em
 * teste, sem tocar em `fetch`. */
export function useApi(): {
  http: HttpClient;
  auth: AuthClient;
  clients: ClientsClient;
  scheduling: SchedulingClient;
  accounts: AccountsClient;
  quotes: QuotesClient;
  payments: PaymentsClient;
  payouts: PayoutsClient;
  sessions: SessionsClient;
} {
  return { http, auth, clients, scheduling, accounts, quotes, payments, payouts, sessions };
}
