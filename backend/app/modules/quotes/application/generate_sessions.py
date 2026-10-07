from decimal import Decimal

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.quotes.domain.quote_origin import QuoteOrigin
from app.modules.quotes.domain.session_plan import SessionPlan
from app.modules.quotes.domain.session_status import SessionStatus
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.models.tattoo_session import TattooSession
from app.modules.quotes.infrastructure.tattoo_session_repository import TattooSessionRepository
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError


class GenerateSessions:
    """Cria as sessões previstas de um orçamento recém-aprovado (RN-ORC-005).

    **Acontece dentro da aprovação, não como um passo separado.** Um orçamento
    aprovado sem sessões é um estado que não significa nada: ninguém tem o que
    marcar como realizado e o repasse não tem sobre o que incidir. Juntar as
    duas coisas na mesma transação garante que esse estado não exista nem por um
    instante — e quem esqueceria de chamar o segundo passo é justamente quem
    aprovou pela tela e foi cuidar de outra coisa.

    **`origin` e `artist_percentage` são copiados aqui, e é este o ato que a
    RN-REP-006 protege.** A sessão carrega o acordo vigente no momento da
    aprovação. Se o orçamento voltar a pendente e for reaprovado com outro
    percentual, o que já foi executado continua valendo o que valia, porque a
    cópia dele não é tocada.

    **Na reaprovação, só o que ainda está agendado é refeito.** Sessão já
    resolvida — realizada, parcial, quitada — fica onde está, com o número de
    sequência que tem; as agendadas são descartadas e recriadas conforme o plano
    novo. Recriar tudo apagaria trabalho executado; não recriar nada deixaria o
    plano antigo valendo sobre um orçamento que mudou."""

    def __init__(
        self,
        sessions: TattooSessionRepository,
        plan: SessionPlan,
        audit: AuditRecorder,
    ) -> None:
        self._sessions = sessions
        self._plan = plan
        self._audit = audit

    def execute(self, actor: AuthenticatedUser, quote: Quote) -> list[TattooSession]:
        percentage = quote.artist_percentage
        if percentage is None:
            raise BusinessRuleError("An approved quote must carry the frozen artist share.")

        existing = self._sessions.list_for_quote(quote.id)
        settled = [record for record in existing if record.status != SessionStatus.SCHEDULED]
        for record in existing:
            if record.status == SessionStatus.SCHEDULED:
                self._sessions.remove(record)

        created = self._create(quote, percentage, settled)

        self._audit.record(
            actor_id=actor.id,
            action="QUOTE_SESSIONS_GENERATED",
            module="quotes",
            entity_type="quote",
            entity_id=str(quote.id),
            new_values={
                "created": len(created),
                "kept": len(settled),
                "artist_percentage": str(percentage),
                "value_per_session": str(quote.planned_value_per_session),
            },
        )
        return created

    def _create(
        self, quote: Quote, percentage: Decimal, settled: list[TattooSession]
    ) -> list[TattooSession]:
        sequence = self._plan.next_sequence([record.sequence_number for record in settled])
        values = self._plan.remaining_values(
            settled_count=len(settled),
            planned_sessions=quote.planned_sessions,
            value_per_session=quote.planned_value_per_session,
        )

        created: list[TattooSession] = []
        for offset, value in enumerate(values):
            created.append(
                self._sessions.persist(
                    TattooSession(
                        quote_id=quote.id,
                        sequence_number=sequence + offset,
                        status=SessionStatus.SCHEDULED,
                        origin=QuoteOrigin(quote.origin),
                        planned_value=value,
                        artist_percentage=percentage,
                    )
                )
            )
        return created
