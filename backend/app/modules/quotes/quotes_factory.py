from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.modules.quotes.application.adjust_remaining_sessions import AdjustRemainingSessions
from app.modules.quotes.application.approve_quote import ApproveQuote
from app.modules.quotes.application.attach_reference_image import AttachReferenceImage
from app.modules.quotes.application.confirm_session_payment import ConfirmSessionPayment
from app.modules.quotes.application.create_quote import CreateQuote
from app.modules.quotes.application.generate_sessions import GenerateSessions
from app.modules.quotes.application.get_quote import GetQuote
from app.modules.quotes.application.list_quotes import ListQuotes
from app.modules.quotes.application.list_reference_images import ListReferenceImages
from app.modules.quotes.application.list_sessions import ListSessions
from app.modules.quotes.application.mark_session_performed import MarkSessionPerformed
from app.modules.quotes.application.read_reference_image import ReadReferenceImage
from app.modules.quotes.application.reject_quote import RejectQuote
from app.modules.quotes.application.remove_reference_image import RemoveReferenceImage
from app.modules.quotes.application.update_quote import UpdateQuote
from app.modules.quotes.domain.artist_percentage_policy import ArtistPercentagePolicy
from app.modules.quotes.domain.quote_policy import QuotePolicy
from app.modules.quotes.domain.reference_image_policy import ReferenceImagePolicy
from app.modules.quotes.domain.session_plan import SessionPlan
from app.modules.quotes.domain.session_policy import SessionPolicy
from app.modules.quotes.infrastructure.quote_reference_image_repository import (
    QuoteReferenceImageRepository,
)
from app.modules.quotes.infrastructure.quote_repository import QuoteRepository
from app.modules.quotes.infrastructure.tattoo_session_repository import TattooSessionRepository
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
        self._session_policy = SessionPolicy()
        self._session_plan = SessionPlan()
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

    @property
    def session_policy(self) -> SessionPolicy:
        return self._session_policy

    def quotes(self, session: Session) -> QuoteRepository:
        return QuoteRepository(session)

    def reference_images(self, session: Session) -> QuoteReferenceImageRepository:
        return QuoteReferenceImageRepository(session)

    def tattoo_sessions(self, session: Session) -> TattooSessionRepository:
        return TattooSessionRepository(session)

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
            sessions=self.generate_sessions(session),
            audit=AuditRecorder(session),
        )

    def generate_sessions(self, session: Session) -> GenerateSessions:
        return GenerateSessions(
            sessions=self.tattoo_sessions(session),
            plan=self._session_plan,
            audit=AuditRecorder(session),
        )

    def mark_session_performed(self, session: Session) -> MarkSessionPerformed:
        return MarkSessionPerformed(
            sessions=self.tattoo_sessions(session),
            quotes=self.quotes(session),
            policy=self._session_policy,
            audit=AuditRecorder(session),
        )

    def confirm_session_payment(self, session: Session) -> ConfirmSessionPayment:
        return ConfirmSessionPayment(
            sessions=self.tattoo_sessions(session),
            policy=self._session_policy,
            audit=AuditRecorder(session),
        )

    def adjust_remaining_sessions(self, session: Session) -> AdjustRemainingSessions:
        return AdjustRemainingSessions(
            sessions=self.tattoo_sessions(session),
            quotes=self.quotes(session),
            policy=self._session_policy,
            plan=self._session_plan,
            audit=AuditRecorder(session),
        )

    def list_sessions(self, session: Session) -> ListSessions:
        return ListSessions(
            sessions=self.tattoo_sessions(session),
            quotes=self.quotes(session),
            policy=self._session_policy,
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
