import uuid

from app.modules.clients.domain.client_source import ClientSource
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ClientSourceResolver:
    """Traduz "de onde veio" no artista que trouxe, ou em ninguém (RN-CLI-002).

    Decisão pura, num lugar só, porque cadastrar e corrigir fazem a mesma
    pergunta e errariam em silêncio se cada um a respondesse por conta própria.
    O erro seria gravar `STUDIO` com um artista junto — uma contradição que
    ninguém vê no banco e que decide dinheiro depois.

    **Nulo significa indicação do estúdio.** A ausência é o dado, e não a falta
    dele: o cliente chegou ao salão, não pela mão de alguém.

    **Quem omite o artista está falando de si.** É o caso corrente — o residente
    cadastra o próprio cliente —, e obrigá-lo a escolher-se numa lista seria
    ruído. Nomear outra pessoa é do gestor: deixar o artista apontar um colega
    como quem trouxe o cliente mexeria no repasse alheio."""

    def resolve(
        self,
        actor: AuthenticatedUser,
        source: ClientSource,
        brought_by_artist_id: uuid.UUID | None,
    ) -> uuid.UUID | None:
        if source == ClientSource.STUDIO:
            if brought_by_artist_id is not None:
                raise BusinessRuleError(
                    "A studio referral has no artist who brought the client."
                )
            return None

        if brought_by_artist_id is None:
            return actor.id

        if brought_by_artist_id != actor.id and not actor.is_staff:
            raise PermissionDeniedError(
                "You cannot record another artist as the one who brought the client."
            )
        return brought_by_artist_id
