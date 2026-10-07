import uuid
from datetime import UTC, datetime

from app.modules.finance.domain.payout_policy import PayoutPolicy
from app.modules.finance.domain.payout_status import PayoutStatus
from app.modules.finance.infrastructure.models.payout import Payout
from app.modules.finance.infrastructure.payout_repository import PayoutRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.reporting.infrastructure.audit_recorder import AuditRecorder
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class ConfirmPayoutPaid:
    """O gestor confirma que transferiu ao artista (RN-REP-004).

    **Registra; não transfere.** A regra é explícita — "gerente ou proprietário
    confirmará manualmente a transferência" —, e é a mesma linha da M5: o sistema
    retém sozinho, mas nunca move dinheiro sozinho (ADR-029). Um sistema que
    lançasse a transferência estaria afirmando que o dinheiro saiu quando
    ninguém o mandou sair.

    A restrição `ck_payout_paid_requires_actor` garante no banco que pago não
    existe sem quem confirmou e quando — mesmo que alguém remova estas linhas,
    não há como gravar dinheiro saindo sem responsável.

    **Confirmar duas vezes é recusado.** Não é zelo: a segunda confirmação
    reescreveria a data e o responsável da primeira, apagando do histórico quem
    de fato fez a transferência."""

    def __init__(
        self,
        payouts: PayoutRepository,
        policy: PayoutPolicy,
        audit: AuditRecorder,
    ) -> None:
        self._payouts = payouts
        self._policy = policy
        self._audit = audit

    def execute(
        self,
        actor: AuthenticatedUser,
        payout_id: uuid.UUID,
        receipt_object_key: str | None = None,
    ) -> Payout:
        if not self._policy.can_confirm_paid(actor):
            raise PermissionDeniedError("Only the studio management can confirm a payout.")

        payout = self._payouts.find_by_id(payout_id)
        if payout is None:
            raise BusinessRuleError("Payout not found.")

        if PayoutStatus(payout.status) == PayoutStatus.PAID:
            raise BusinessRuleError("This payout has already been confirmed as paid.")

        previous = str(payout.status)
        payout.status = PayoutStatus.PAID
        payout.paid_at = datetime.now(UTC)
        payout.paid_by = actor.id
        payout.receipt_object_key = receipt_object_key
        self._payouts.persist(payout)

        self._audit.record(
            actor_id=actor.id,
            action="PAYOUT_CONFIRMED_PAID",
            module="finance",
            entity_type="payout",
            entity_id=str(payout.id),
            old_values={"status": previous},
            new_values={
                "status": str(PayoutStatus.PAID),
                "net_total": str(payout.net_total),
                "artist_id": str(payout.artist_id),
            },
        )
        return payout
