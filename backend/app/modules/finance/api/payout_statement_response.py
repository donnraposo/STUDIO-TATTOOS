from pydantic import BaseModel

from app.modules.finance.api.payout_adjustment_response import PayoutAdjustmentResponse
from app.modules.finance.api.payout_item_response import PayoutItemResponse
from app.modules.finance.api.payout_response import PayoutResponse
from app.modules.finance.application.payout_statement import PayoutStatement


class PayoutStatementResponse(BaseModel):
    """O demonstrativo completo (RN-REP-007).

    As tres pecas vao juntas porque e assim que se le: um repasse sem os itens e
    um numero sem explicacao, e e justamente a explicacao que o artista confere
    contra o proprio extrato."""

    payout: PayoutResponse
    items: list[PayoutItemResponse]
    adjustments: list[PayoutAdjustmentResponse]

    @classmethod
    def from_statement(cls, statement: PayoutStatement) -> "PayoutStatementResponse":
        return cls(
            payout=PayoutResponse.from_model(statement.payout),
            items=[PayoutItemResponse.from_model(item) for item in statement.items],
            adjustments=[
                PayoutAdjustmentResponse.from_model(adjustment)
                for adjustment in statement.adjustments
            ],
        )
