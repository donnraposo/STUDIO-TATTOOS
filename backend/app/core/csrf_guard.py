import secrets

from fastapi import HTTPException, Request, status


class CsrfGuard:
    """Protecao CSRF por duplo envio de cookie.

    O cookie de sessao e `HttpOnly` e viaja sozinho em qualquer requisicao que o
    navegador dispare, inclusive as iniciadas por outro site. O token CSRF fica
    em um cookie legivel por script e precisa ser reenviado no cabecalho: um site
    de terceiros nao consegue ler o cookie desta origem, entao nao consegue
    montar o cabecalho.

    `SameSite` e defesa adicional, nao substituta, conforme
    DOCS/04_ARQUITETURA_TECNICA.md secao 6."""

    _SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})

    def __init__(self, cookie_name: str, header_name: str) -> None:
        self._cookie_name = cookie_name
        self._header_name = header_name

    @staticmethod
    def issue_token() -> str:
        return secrets.token_urlsafe(32)

    def validate(self, request: Request) -> None:
        if request.method in self._SAFE_METHODS:
            return

        cookie_token = request.cookies.get(self._cookie_name)
        header_token = request.headers.get(self._header_name)

        if not cookie_token or not header_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Missing CSRF token."
            )

        # Comparacao em tempo constante: evita distinguir tokens pelo tempo de resposta.
        if not secrets.compare_digest(cookie_token, header_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Invalid CSRF token."
            )
