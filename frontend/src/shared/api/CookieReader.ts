/** Lê um cookie legível pelo script.
 *
 * Serve a um caso só: o token CSRF, que precisa voltar no cabeçalho pelo
 * esquema de duplo envio. O cookie de sessão é `HttpOnly` e **não** é visível
 * aqui — é justamente isso que impede um script injetado de roubá-lo.
 *
 * Classe própria, e não uma linha solta dentro do cliente HTTP, porque o
 * `document.cookie` é global e trocá-lo em teste seria bagunça. Recebendo a
 * origem dos cookies no construtor, o teste passa uma string e pronto. */
export class CookieReader {
  private readonly source: () => string;

  constructor(source: () => string = () => globalThis.document?.cookie ?? "") {
    this.source = source;
  }

  read(name: string): string | null {
    const prefix = `${name}=`;
    const found = this.source()
      .split(";")
      .map((entry) => entry.trim())
      .find((entry) => entry.startsWith(prefix));

    return found ? decodeURIComponent(found.slice(prefix.length)) : null;
  }
}
