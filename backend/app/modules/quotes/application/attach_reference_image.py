import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.domain.quote_status import QuoteStatus
from app.modules.quotes.domain.reference_image_policy import ReferenceImagePolicy
from app.modules.quotes.infrastructure.models.quote_reference_image import QuoteReferenceImage
from app.modules.quotes.infrastructure.quote_reference_image_repository import (
    QuoteReferenceImageRepository,
)
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError
from app.shared.storage.object_storage import ObjectStorage


class AttachReferenceImage:
    """Anexa uma imagem de referência ao orçamento (RN-ORC-004).

    **Grava o arquivo antes da linha do banco, de propósito.** O armazenamento
    não participa da transação, então uma das duas inconsistências é inevitável
    se algo falhar no meio, e elas não têm o mesmo peso: arquivo sem linha é lixo
    invisível, que ninguém vê e uma limpeza remove; linha sem arquivo é um
    registro quebrado que aparece na tela do usuário como imagem que não abre.
    Entre as duas, a ordem escolhida deixa acontecer a inofensiva.

    **Anexar não devolve o orçamento a pendente.** A RN-ORC-003 trata de alterar
    o orçamento, e imagem de referência não é termo do acordo: é a tatuagem que a
    pessoa quer. Reabrir uma aprovação porque alguém acrescentou uma foto puniria
    justamente o cuidado de documentar melhor o trabalho. A permissão, ainda
    assim, é a de editar: num orçamento já aprovado, só o gestor anexa."""

    _EXTENSION_BY_TYPE = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    def __init__(
        self,
        quotes: QuoteRepository,
        images: QuoteReferenceImageRepository,
        policy: QuotePolicy,
        limits: ReferenceImagePolicy,
        storage: ObjectStorage,
        audit: AuditRecorder,
    ) -> None:
        self._quotes = quotes
        self._images = images
        self._policy = policy
        self._limits = limits
        self._storage = storage
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        quote_id: uuid.UUID,
        content: bytes,
        content_type: str,
    ) -> QuoteReferenceImage:
        quote = self._quotes.find_by_id(quote_id)
        if quote is None:
            raise BusinessRuleError("Quote not found.")

        if not self._policy.can_edit(actor, quote.artist_id, QuoteStatus(quote.status)):
            raise PermissionDeniedError("You cannot change this quote.")

        self._ensure_within_limits(quote_id, content, content_type)

        key = self._build_key(quote_id, content_type)
        self._storage.put(key, content, content_type)

        image = self._images.persist(
            QuoteReferenceImage(
                quote_id=quote_id,
                object_key=key,
                content_type=content_type,
                byte_size=len(content),
                uploaded_by=actor.id,
            )
        )

        self._audit.record(
            actor_id=actor.id,
            action="QUOTE_REFERENCE_IMAGE_ATTACHED",
            module="quotes",
            entity_type="quote_reference_image",
            entity_id=str(image.id),
            new_values={
                "quote_id": str(quote_id),
                "content_type": content_type,
                "byte_size": len(content),
            },
        )
        return image

    def _ensure_within_limits(
        self, quote_id: uuid.UUID, content: bytes, content_type: str
    ) -> None:
        """Confere antes de gravar o arquivo, para não subir o que será recusado."""
        if not self._limits.accepts_type(content_type):
            accepted = ", ".join(sorted(self._limits.allowed_types))
            raise BusinessRuleError(f"Unsupported image type. Accepted types: {accepted}.")

        if not self._limits.accepts_size(len(content)):
            limit = self._limits.max_bytes // (1024 * 1024)
            raise BusinessRuleError(f"The image must not be empty and must be up to {limit} MB.")

        if not self._limits.accepts_one_more(self._images.count_for_quote(quote_id)):
            raise BusinessRuleError(
                f"A quote takes up to {self._limits.max_per_quote} reference images."
            )

    def _build_key(self, quote_id: uuid.UUID, content_type: str) -> str:
        """Chave por orçamento, com nome sorteado.

        O nome original do arquivo **não** entra na chave. Ele vem do cliente e
        pode trazer caminho, acento ou o nome da pessoa retratada; sorteando o
        nome, a chave nunca depende do que foi enviado nem revela nada."""
        extension = self._EXTENSION_BY_TYPE.get(content_type.split(";")[0].strip().lower(), "")
        return f"quotes/{quote_id}/{uuid.uuid4()}{extension}"
