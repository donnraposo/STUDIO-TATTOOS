import uuid
from decimal import Decimal

from app.modules.identity.infrastructure.user_repository import UserRepository
from app.modules.quotes.domain.artist_terms import ArtistTerms


class AccountArtistTerms(ArtistTerms):
    """A resposta da identidade ao orçamento (RN-REP-001, RN-REP-002).

    Implementa a porta que o orçamento declarou. É aqui que as duas metades se
    encontram, e só aqui.

    **Artista que não existe mais devolve nulo, e não erro.** O orçamento cai
    na regra da origem, que é a resposta certa: uma conta apagada não tem acordo
    próprio, e derrubar a aprovação por causa disso seria impedir o estúdio de
    fechar trabalho por um detalhe de cadastro."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def default_percentage_for(self, artist_id: uuid.UUID) -> Decimal | None:
        artist = self._users.find_by_id(artist_id)
        return artist.default_artist_percentage if artist else None
