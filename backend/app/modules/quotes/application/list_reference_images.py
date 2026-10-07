import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.infrastructure.models.quote_reference_image import QuoteReferenceImage
from app.modules.quotes.infrastructure.quote_reference_image_repository import (
    QuoteReferenceImageRepository,
)
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ListReferenceImages:
    """Lista as imagens de um orçamento.

    A visibilidade é a do orçamento: quem não pode ver o orçamento não recebe as
    imagens dele.

    **Não toca no armazenamento.** Listar precisa de metadados, que estão no
    banco; o conteúdo é buscado uma imagem por vez, quando a tela realmente a
    exibe. Abrir os arquivos aqui faria a listagem de um orçamento com dez
    referências ler dezenas de megabytes para mostrar miniaturas."""

    def __init__(
        self,
        quotes: QuoteRepository,
        images: QuoteReferenceImageRepository,
        policy: QuotePolicy,
    ) -> None:
        self._quotes = quotes
        self._images = images
        self._policy = policy

    def execute(
        self, actor: AuthenticatedUser, quote_id: uuid.UUID
    ) -> list[QuoteReferenceImage]:
        quote = self._quotes.find_by_id(quote_id)
        if quote is None:
            raise BusinessRuleError("Quote not found.")

        if not self._policy.can_see(actor, quote.artist_id):
            raise PermissionDeniedError("You cannot see this quote.")

        return self._images.list_for_quote(quote_id)
