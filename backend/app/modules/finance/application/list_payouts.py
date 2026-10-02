from app.modules.finance.domain.payout_policy import PayoutPolicy
from app.modules.finance.infrastructure.models.payout import Payout
from app.modules.finance.infrastructure.payout_repository import PayoutRepository
from app.modules.identity.domain.authenticated_user import AuthenticatedUser


class ListPayouts:
    """Os repasses visiveis a quem pergunta (RN-REP-004).

    "Cada artista visualizara somente seus proprios valores; gerente e
    proprietario visualizarao todos." O recorte e feito na consulta, e nao
    filtrando depois de trazer tudo: o que nao deve ser visto nao sai do banco.

    E a regra mais importante do modulo. O demonstrativo diz quanto cada pessoa
    recebeu, e vazar isso entre colegas e dano que nao se desfaz."""

    def __init__(self, payouts: PayoutRepository, policy: PayoutPolicy) -> None:
        self._payouts = payouts
        self._policy = policy

    def execute(self, actor: AuthenticatedUser) -> list[Payout]:
        if self._policy.sees_every_payout(actor):
            return self._payouts.list_all()
        return self._payouts.list_for_artist(actor.id)
