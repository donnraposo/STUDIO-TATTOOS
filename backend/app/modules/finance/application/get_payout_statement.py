import uuid

from app.modules.finance.application.payout_statement import PayoutStatement
from app.modules.finance.domain.payout_policy import PayoutPolicy
from app.modules.finance.infrastructure.payout_adjustment_repository import (
    PayoutAdjustmentRepository,
)
from app.modules.finance.infrastructure.payout_item_repository import PayoutItemRepository
from app.modules.finance.infrastructure.payout_repository import PayoutRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.errors.permission_denied_error import PermissionDeniedError


class GetPayoutStatement:
    """O demonstrativo de um repasse (RN-REP-007).

    **A permissao e conferida contra o artista do repasse**, e nao contra quem
    pede: o artista ve o proprio, o gestor ve todos. E a regra mais importante do
    modulo -- o demonstrativo diz quanto alguem recebeu."""

    def __init__(
        self,
        payouts: PayoutRepository,
        items: PayoutItemRepository,
        adjustments: PayoutAdjustmentRepository,
        policy: PayoutPolicy,
    ) -> None:
        self._payouts = payouts
        self._items = items
        self._adjustments = adjustments
        self._policy = policy

    def execute(self, actor: AuthenticatedUser, payout_id: uuid.UUID) -> PayoutStatement:
        payout = self._payouts.find_by_id(payout_id)
        if payout is None:
            raise BusinessRuleError("Payout not found.")

        if not self._policy.can_see(actor, payout.artist_id):
            raise PermissionDeniedError("You cannot see this payout.")

        return PayoutStatement(
            payout=payout,
            items=self._items.list_for_payout(payout_id),
            adjustments=self._adjustments.list_for_payout(payout_id),
        )
