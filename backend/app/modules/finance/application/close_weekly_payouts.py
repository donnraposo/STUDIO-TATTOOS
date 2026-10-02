import uuid
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.finance.domain.payout_policy import PayoutPolicy
from app.modules.finance.domain.payout_share import PayoutShare
from app.modules.finance.domain.payout_status import PayoutStatus
from app.modules.finance.domain.payout_week import PayoutWeek
from app.modules.finance.domain.settled_session import SettledSession
from app.modules.finance.domain.settled_sessions import SettledSessions
from app.modules.finance.infrastructure.models.payout import Payout
from app.modules.finance.infrastructure.models.payout_item import PayoutItem
from app.modules.finance.infrastructure.payout_item_repository import PayoutItemRepository
from app.modules.finance.infrastructure.payout_repository import PayoutRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class CloseWeeklyPayouts:
    """Fecha a semana e calcula o repasse de cada artista (RN-REP-004 e
    RN-REP-007).

    **Calculado sob demanda, e não por agendador.** A regra diz que o sistema
    calcula "depois do fechamento" das 20h de sexta; ela não diz *quando*
    exatamente, e ninguém consulta repasse às 20h de sexta. O resultado é
    idêntico ao de um processo agendado e evita subir infraestrutura que só a
    Fase 2 realmente exige (ADR-008). Decisão do responsável, 02/10/2026.

    **Semana que ainda não terminou não fecha.** É a parte da regra que o cálculo
    sob demanda precisa respeitar explicitamente: sem esta recusa, abrir a tela
    numa quarta-feira fecharia a semana corrente com metade dos pagamentos, e o
    resto cairia em lugar nenhum — porque a semana já estaria fechada quando os
    demais chegassem.

    **Fechar duas vezes devolve o mesmo fechamento.** Um repasse é fotografia, e
    recalcular sobre uma semana já fechada reescreveria o que o artista já viu.
    A garantia de verdade é `uq_payout_period`, no banco: com cálculo sob
    demanda, duas abas abertas são dois processos, e só o banco arbitra isso.

    **A idempotência está no repasse, não no filtro de sessões**, e a diferença
    custou um defeito: filtrando apenas as sessões já pagas, a segunda chamada
    não encontrava nada a fazer e devolvia lista vazia — o gestor abriria a tela
    de novo e veria a semana sem repasse nenhum, como se o fechamento tivesse
    sumido. Quem já tem repasse na semana é devolvido como está; só quem não tem
    é calculado.

    **Sessão já paga nunca entra de novo.** O filtro é explícito aqui, e o índice
    único é a rede embaixo dele: sem o filtro, o fechamento inteiro falharia por
    causa de uma sessão que não deveria estar na lista; sem o índice, uma falha
    no filtro pagaria duas vezes o mesmo trabalho."""

    def __init__(
        self,
        payouts: PayoutRepository,
        items: PayoutItemRepository,
        sessions: SettledSessions,
        policy: PayoutPolicy,
        week: PayoutWeek,
        share: PayoutShare,
        audit: AuditRecorder,
    ) -> None:
        self._payouts = payouts
        self._items = items
        self._sessions = sessions
        self._policy = policy
        self._week = week
        self._share = share
        self._audit = audit

    def execute(
        self, actor: AuthenticatedUser, reference: datetime, now: datetime | None = None
    ) -> list[Payout]:
        if not self._policy.can_close(actor):
            raise PermissionDeniedError("Only the studio management can close a payout week.")

        closing = self._week.closing_for(reference)
        moment = now or datetime.now(UTC)
        if closing > moment:
            raise BusinessRuleError(
                "This week has not closed yet. Payouts are calculated after Friday 20:00."
            )

        opening = self._week.opening_for(closing)
        existing = self._payouts.list_for_week(closing)
        settled_artists = {payout.artist_id for payout in existing}

        already_paid = self._items.paid_session_ids()
        by_artist = self._group(
            [
                settled
                for settled in self._sessions.settled_between(opening, closing)
                if settled.session_id not in already_paid
            ]
        )

        created = [
            self._close_one(artist_id, settled, opening, closing)
            for artist_id, settled in by_artist.items()
            if artist_id not in settled_artists
        ]
        closed = existing + created

        self._audit.record(
            actor_id=actor.id,
            action="PAYOUT_WEEK_CLOSED",
            module="finance",
            entity_type="payout_week",
            entity_id=closing.isoformat(),
            new_values={
                "period_start": opening.isoformat(),
                "period_end": closing.isoformat(),
                "created": len(created),
                "already_closed": len(existing),
            },
        )
        return closed

    @staticmethod
    def _group(settled: list[SettledSession]) -> dict[uuid.UUID, list[SettledSession]]:
        grouped: dict[uuid.UUID, list[SettledSession]] = defaultdict(list)
        for session in settled:
            grouped[session.artist_id].append(session)
        return grouped

    def _close_one(
        self,
        artist_id: uuid.UUID,
        settled: list[SettledSession],
        opening: datetime,
        closing: datetime,
    ) -> Payout:
        payout = self._payouts.persist(
            Payout(
                artist_id=artist_id,
                period_start=opening,
                period_end=closing,
                gross_total=Decimal("0.00"),
                adjustments_total=Decimal("0.00"),
                net_total=Decimal("0.00"),
                status=PayoutStatus.CALCULATED,
            )
        )

        gross = Decimal("0.00")
        for session in settled:
            amount = self._share.of(session.received_amount, session.percentage)
            self._items.persist(
                PayoutItem(
                    payout_id=payout.id,
                    session_id=session.session_id,
                    received_amount=session.received_amount,
                    percentage=session.percentage,
                    amount=amount,
                )
            )
            gross += amount

        payout.gross_total = gross
        payout.net_total = gross
        self._payouts.persist(payout)
        return payout
