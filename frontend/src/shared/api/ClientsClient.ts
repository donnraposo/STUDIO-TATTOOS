import type { Client, ClientContact, ClientSource } from "@/shared/domain/Client";
import { HttpClient } from "@/shared/api/HttpClient";

/** As duas formas em que a API descreve um cliente, em `snake_case`.
 *
 * Confinadas a este arquivo: é a única parte da interface que precisa conhecer
 * a convenção de nomes do backend. */
interface ContactPayload {
  id: string;
  name: string;
  phone: string;
  instagram: string | null;
}

interface ClientPayload extends ContactPayload {
  registered_by_artist_id: string;
  brought_by_artist_id: string | null;
  created_at: string;
}

interface RegisteredPayload {
  client: ClientPayload;
  possible_duplicates: ContactPayload[];
}

/** Resultado do cadastro: o cliente **e** o alerta de duplicidade.
 *
 * Os dois vêm juntos porque a RN-CLI-005 manda alertar sem bloquear. O cadastro
 * já aconteceu; cabe a quem cadastrou decidir se era mesmo a mesma pessoa. */
export interface RegisteredClient {
  client: Client;
  possibleDuplicates: ClientContact[];
}

/** Cadastro de clientes (`/clients`). */
export class ClientsClient {
  private readonly http: HttpClient;

  constructor(http: HttpClient = new HttpClient()) {
    this.http = http;
  }

  async list(): Promise<Client[]> {
    const payload = await this.http.get<ClientPayload[]>("/clients");
    return payload.map(ClientsClient.toClient);
  }

  /** `source` e `broughtByArtistId` dizem **de onde o cliente veio**
   * (RN-CLI-002). Omitidos, valem o padrão: trazido pelo próprio autor do
   * cadastro, que é o caso corrente. */
  async register(client: {
    name: string;
    phone: string;
    instagram: string | null;
    source: ClientSource;
    broughtByArtistId: string | null;
  }): Promise<RegisteredClient> {
    const payload = await this.http.post<RegisteredPayload>("/clients", {
      name: client.name,
      phone: client.phone,
      instagram: client.instagram,
      source: client.source,
      brought_by_artist_id: client.broughtByArtistId,
    });
    return {
      client: ClientsClient.toClient(payload.client),
      possibleDuplicates: payload.possible_duplicates.map(ClientsClient.toContact),
    };
  }

  /** Pode devolver a ficha completa ou apenas o contato, conforme quem
   * pergunta (RN-CLI-004). Quem chama decide o que mostrar com `isFullRecord`. */
  async find(id: string): Promise<Client | ClientContact> {
    const payload = await this.http.get<ClientPayload | ContactPayload>(`/clients/${id}`);
    return "registered_by_artist_id" in payload
      ? ClientsClient.toClient(payload)
      : ClientsClient.toContact(payload);
  }

  /** `source` nulo **não mexe** na origem, e é o padrão.
   *
   * Na criação o campo tem padrão porque todo cliente vem de algum lugar; na
   * edição, um padrão faria toda correção de telefone tentar reescrever a
   * origem — e, como alterá-la é de gerente e proprietário (RN-CLI-003), o
   * artista corrigindo um Instagram receberia 403 sem entender por quê. */
  async update(
    id: string,
    client: {
      name: string;
      phone: string;
      instagram: string | null;
      source: ClientSource | null;
      broughtByArtistId: string | null;
    },
  ): Promise<Client> {
    const payload = await this.http.put<ClientPayload>(`/clients/${id}`, {
      name: client.name,
      phone: client.phone,
      instagram: client.instagram,
      source: client.source,
      brought_by_artist_id: client.broughtByArtistId,
    });
    return ClientsClient.toClient(payload);
  }

  private static toContact(payload: ContactPayload): ClientContact {
    return {
      id: payload.id,
      name: payload.name,
      phone: payload.phone,
      instagram: payload.instagram,
    };
  }

  private static toClient(payload: ClientPayload): Client {
    return {
      ...ClientsClient.toContact(payload),
      registeredByArtistId: payload.registered_by_artist_id,
      broughtByArtistId: payload.brought_by_artist_id,
      createdAt: payload.created_at,
    };
  }
}
