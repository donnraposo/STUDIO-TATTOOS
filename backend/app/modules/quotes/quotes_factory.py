from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.quotes.application.approve_quote import ApproveQuote
from app.modules.quotes.application.attach_reference_image import AttachReferenceImage
from app.modules.quotes.application.create_quote import CreateQuote
from app.modules.quotes.application.get_quote import GetQuote
from app.modules.quotes.application.list_quotes import ListQuotes
from app.modules.quotes.application.list_reference_images import ListReferenceImages
from app.modules.quotes.application.read_reference_image import ReadReferenceImage
from app.modules.quotes.application.reject_quote import RejectQuote
from app.modules.quotes.application.remove_reference_image import RemoveReferenceImage
from app.modules.quotes.application.update_quote import UpdateQuote
from app.modules.quotes.domain.artist_percentage_policy import ArtistPercentagePolicy
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.domain.reference_image_policy import ReferenceImagePolicy
from app.modules.quotes.infrastructure.quote_reference_image_repository import (
    QuoteReferenceImageRepository,
)
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.storage.object_storage import ObjectStorage


class QuotesFactory:
    """Monta os casos de uso dos orçamentos.

    Recebe o armazenamento pronto do `Container` em vez de construí-lo: o cliente
    S3 mantém conexões e é compartilhado pela aplicação, e a fábrica não precisa
    saber qual implementação está em uso (ADR-006, ADR-016)."""

    def __init__(self, settings: Settings, storage: ObjectStorage) -> None:
        self._policy = QuotePolicy()
        self._percentages = ArtistPercentagePolicy()
        self._storage = storage
        self._image_limits = ReferenceImagePolicy(
            allowed_types=settings.allowed_reference_image_types,
            max_bytes=settings.reference_image_max_bytes,
            max_per_quote=settings.reference_image_max_per_quote,
        )

    @property
    def policy(self) -> QuotePolicy:
        return self._policy

    @property
    def percentages(self) -> ArtistPercentagePolicy:
        return self._percentages

    @property
    def image_limits(self) -> ReferenceImagePolicy:
        return self._image_limits

    def quotes(self, session: Session) -> QuoteRepository:
        return QuoteRepository(session)

    def reference_images(self, session: Session) -> QuoteReferenceImageRepository:
        return QuoteReferenceImageRepository(session)

    def create_quote(self, session: Session) -> CreateQuote:
        return CreateQuote(
            quotes=self.quotes(session),
            policy=self._policy,
            audit=AuditRecorder(session),
        )

    def update_quote(self, session: Session) -> UpdateQuote:
        return UpdateQuote(
            quotes=self.quotes(session),
            policy=self._policy,
            audit=AuditRecorder(session),
        )

    def approve_quote(self, session: Session) -> ApproveQuote:
        return ApproveQuote(
            quotes=self.quotes(session),
            policy=self._policy,
            percentages=self._percentages,
            audit=AuditRecorder(session),
        )

    def reject_quote(self, session: Session) -> RejectQuote:
        return RejectQuote(
            quotes=self.quotes(session),
            policy=self._policy,
            audit=AuditRecorder(session),
        )

    def list_quotes(self, session: Session) -> ListQuotes:
        return ListQuotes(quotes=self.quotes(session), policy=self._policy)

    def get_quote(self, session: Session) -> GetQuote:
        return GetQuote(quotes=self.quotes(session), policy=self._policy)

    def attach_reference_image(self, session: Session) -> AttachReferenceImage:
        return AttachReferenceImage(
            quotes=self.quotes(session),
            images=self.reference_images(session),
            policy=self._policy,
            limits=self._image_limits,
            storage=self._storage,
            audit=AuditRecorder(session),
        )

    def list_reference_images(self, session: Session) -> ListReferenceImages:
        return ListReferenceImages(
            quotes=self.quotes(session),
            images=self.reference_images(session),
            policy=self._policy,
        )

    def read_reference_image(self, session: Session) -> ReadReferenceImage:
        return ReadReferenceImage(
            quotes=self.quotes(session),
            images=self.reference_images(session),
            policy=self._policy,
            storage=self._storage,
        )

    def remove_reference_image(self, session: Session) -> RemoveReferenceImage:
        return RemoveReferenceImage(
            quotes=self.quotes(session),
            images=self.reference_images(session),
            policy=self._policy,
            storage=self._storage,
            audit=AuditRecorder(session),
        )
