import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser


class SessionPolicy:
    """Quem pode o quê na sessão (RN-ORC-005 e RN-ORC-006).

    Separada da `QuotePolicy` porque a assimetria aqui é outra. No orçamento, o
    artista mexe **enquanto pendente**; na sessão, ele age justamente depois da
    aprovação — marcar realizada é o registro de um trabalho que aconteceu, e
    quem sabe que aconteceu é quem tatuou.

    Confirmar o recebimento é do gestor, e é a metade que falta para a sessão
    entrar em repasse. Deixar o artista confirmar o próprio recebimento seria
    deixá-lo liberar o próprio pagamento."""

    def can_mark_performed(self, actor: AuthenticatedUser, artist_id: uuid.UUID) -> bool:
        """RN-ORC-005: o artista marca a própria sessão como realizada.

        O gestor também marca — ele opera o sistema pelo artista que não
        registrou, e é ele quem responde pelo guest, que não acessa o módulo
        (RN-ORC-001)."""
        return actor.is_staff or actor.id == artist_id

    def can_confirm(self, actor: AuthenticatedUser) -> bool:
        """RN-ORC-005: gerente ou proprietário confirma o valor recebido."""
        return actor.is_staff

    def can_adjust(self, actor: AuthenticatedUser) -> bool:
        """RN-ORC-006: gerente ou proprietário ajusta as sessões restantes."""
        return actor.is_staff

    def can_see(self, actor: AuthenticatedUser, artist_id: uuid.UUID) -> bool:
        return actor.is_staff or actor.id == artist_id
