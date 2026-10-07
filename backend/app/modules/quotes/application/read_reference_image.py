import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.application.reference_image_content import ReferenceImageContent
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.infrastructure.quote_reference_image_repository import (
    QuoteReferenceImageRepository,
)
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError
from app.shared.storage.object_storage import ObjectStorage


class ReadReferenceImage:
    """Entrega o conteúdo de uma imagem de referência.

    **É este caso de uso que substitui a URL assinada.** A imagem só sai daqui
    depois de o ator ser autenticado e a visibilidade do orçamento ser conferida,
    exatamente como em qualquer outra leitura do sistema. Não existe endereço que
    devolva a foto sem a sessão.

    A imagem precisa pertencer ao orçamento da rota. Sem essa conferência,
    qualquer pessoa com acesso a um orçamento próprio poderia pedir a imagem de
    outro orçamento passando o identificador dela — o controle estaria no
    orçamento da URL, e o dado viria de outro lugar."""

    def __init__(
        self,
        quotes: QuoteRepository,
        images: QuoteReferenceImageRepository,
        policy: QuotePolicy,
        storage: ObjectStorage,
    ) -> None:
        self._quotes = quotes
        self._images = images
        self._policy = policy
        self._storage = storage

    def execute(
        self, actor: AuthenticatedUser, quote_id: uuid.UUID, image_id: uuid.UUID
    ) -> ReferenceImageContent:
        quote = self._quotes.find_by_id(quote_id)
        if quote is None:
            raise BusinessRuleError("Quote not found.")

        if not self._policy.can_see(actor, quote.artist_id):
            raise PermissionDeniedError("You cannot see this quote.")

        image = self._images.find_by_id(image_id)
        if image is None or image.quote_id != quote_id:
            raise BusinessRuleError("Reference image not found for this quote.")

        return ReferenceImageContent(
            content_type=image.content_type,
            content=self._storage.open(image.object_key),
        )
