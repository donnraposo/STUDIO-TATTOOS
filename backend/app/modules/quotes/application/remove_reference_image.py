import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.infrastructure.quote_reference_image_repository import (
    QuoteReferenceImageRepository,
)
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError
from app.shared.storage.object_storage import ObjectStorage


class RemoveReferenceImage:
    """Remove uma imagem de referência do orçamento.

    **A ordem é o inverso da de anexar, pelo mesmo motivo.** Ao anexar, o arquivo
    vem antes da linha; ao remover, a linha sai antes do arquivo. As duas
    escolhas seguem a mesma regra: o banco nunca deve apontar para um arquivo que
    não existe. A sobra possível é sempre arquivo sem linha, que é invisível ao
    usuário, nunca linha sem arquivo, que aparece como imagem quebrada.

    Resta uma janela estreita: se o commit falhar depois de o arquivo ter sido
    apagado, a linha volta apontando para um objeto que já não existe. Fechá-la
    exigiria remover o arquivo somente após o commit, o que esta arquitetura não
    oferece ao caso de uso — a transação é encerrada pelo contexto de sessão. Fica
    registrado em vez de disfarçado.

    **O arquivo é apagado de verdade, não só desvinculado.** A imagem é dado
    pessoal: guardar para sempre o que ninguém mais usa contraria a orientação de
    retenção da RN-CLI-007."""

    def __init__(
        self,
        quotes: QuoteRepository,
        images: QuoteReferenceImageRepository,
        policy: QuotePolicy,
        storage: ObjectStorage,
        audit: AuditRecorder,
    ) -> None:
        self._quotes = quotes
        self._images = images
        self._policy = policy
        self._storage = storage
        self._audit = audit

    def execute(
        self, actor: AuthenticatedUser, quote_id: uuid.UUID, image_id: uuid.UUID
    ) -> None:
        quote = self._quotes.find_by_id(quote_id)
        if quote is None:
            raise BusinessRuleError("Quote not found.")

        if not self._policy.can_edit(actor, quote.artist_id, QuoteStatus(quote.status)):
            raise PermissionDeniedError("You cannot change this quote.")

        image = self._images.find_by_id(image_id)
        if image is None or image.quote_id != quote_id:
            raise BusinessRuleError("Reference image not found for this quote.")

        key = image.object_key
        self._audit.record(
            actor_id=actor.id,
            action="QUOTE_REFERENCE_IMAGE_REMOVED",
            module="quotes",
            entity_type="quote_reference_image",
            entity_id=str(image.id),
            old_values={"quote_id": str(quote_id), "object_key": key},
        )
        self._images.remove(image)
        self._storage.remove(key)
