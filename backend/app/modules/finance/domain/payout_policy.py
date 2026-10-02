import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser


class PayoutPolicy:
    """Quem pode o quê no repasse (RN-REP-004 e RN-REP-007).

    **"Cada artista visualizará somente seus próprios valores; gerente e
    proprietário visualizarão todos."** É a regra mais literal do módulo, e a
    mais importante: o demonstrativo diz quanto cada pessoa recebeu, e vazá-lo
    entre colegas é o tipo de dano que não se desfaz com um pedido de desculpas.

    Fechar a semana e confirmar a transferência são do gestor. Deixar o artista
    fechar o próprio repasse seria deixá-lo decidir quando recebe; deixá-lo
    confirmar seria deixá-lo declarar que recebeu."""

    def can_close(self, actor: AuthenticatedUser) -> bool:
        return actor.is_staff

    def can_confirm_paid(self, actor: AuthenticatedUser) -> bool:
        return actor.is_staff

    def sees_every_payout(self, actor: AuthenticatedUser) -> bool:
        """Separado de `can_see` porque a listagem decide antes de ter um
        repasse em mão: ela precisa saber qual consulta fazer."""
        return actor.is_staff

    def can_see(self, actor: AuthenticatedUser, artist_id: uuid.UUID) -> bool:
        return actor.is_staff or actor.id == artist_id
