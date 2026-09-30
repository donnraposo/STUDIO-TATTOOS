import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser


class PaymentPolicy:
    """Quem pode o quê no pagamento (RN-PAG-002, RN-PAG-006, RN-PAG-007 e
    RN-PAG-009).

    A regra é curta e não tem exceção: **confirmar, recusar, devolver e estornar
    são de gerente ou proprietário**. O artista não decide sobre dinheiro que o
    estúdio recebe — é sobre esse recebimento que o repasse dele é calculado, e
    deixá-lo confirmar o próprio recebimento seria deixá-lo liberar o próprio
    pagamento.

    Informar um pagamento também é do gestor nesta versão: a RN-PAG-006 diz que
    **todos** os recebimentos são inseridos e confirmados manualmente por gerente
    ou proprietário. O artista não lança recebimento.

    Ver é outra coisa: o artista precisa acompanhar os pagamentos dos próprios
    atendimentos, porque é deles que sai o repasse (RN-REP-007)."""

    def can_register(self, actor: AuthenticatedUser) -> bool:
        return actor.is_staff

    def can_decide(self, actor: AuthenticatedUser) -> bool:
        """Confirmar, recusar, devolver e estornar."""
        return actor.is_staff

    def can_see(self, actor: AuthenticatedUser, artist_id: uuid.UUID) -> bool:
        return actor.is_staff or actor.id == artist_id
