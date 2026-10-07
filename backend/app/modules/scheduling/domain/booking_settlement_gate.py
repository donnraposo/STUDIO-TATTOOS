import uuid
from abc import ABC, abstractmethod

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.scheduling.domain.booking_outcome import BookingOutcome


class BookingSettlementGate(ABC):
    """Porta pela qual a agenda avisa o financeiro que o desfecho mudou.

    Recusar, cancelar, marcar não comparecimento e remarcar têm consequência
    sobre o sinal (RN-PAG-003, RN-AGE-008, RN-AGE-009 e RN-AGE-010). Qual é a
    consequência não é assunto da agenda — ela sabe **o que aconteceu**, não o
    que fazer com o dinheiro.

    Um método só, com o desfecho como dado. Uma porta com um método por evento
    cresceria a cada regra nova e obrigaria o financeiro a implementar método
    vazio para o que ainda não trata."""

    @abstractmethod
    def settle(
        self, actor: AuthenticatedUser, booking_id: uuid.UUID, outcome: BookingOutcome
    ) -> None:
        """Registra a consequência financeira do desfecho."""
