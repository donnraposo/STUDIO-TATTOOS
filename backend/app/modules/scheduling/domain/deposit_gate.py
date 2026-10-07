import uuid
from abc import ABC, abstractmethod


class DepositGate(ABC):
    """Porta que a agenda usa para perguntar se o sinal está confirmado.

    A RN-AGE-005 diz que uma solicitação não pode ser aprovada enquanto o
    pagamento do sinal não estiver confirmado, e a RN-PAG-002 repete pelo outro
    lado. Quem sabe responder é o módulo financeiro — mas quem **precisa** da
    resposta é a agenda, e por isso a porta é dela.

    Se a agenda importasse o módulo financeiro, a ordem ficaria invertida: a
    regra de aprovação passaria a depender do desenho interno de pagamento, e
    trocar aquele desenho quebraria esta. Com a porta aqui, o financeiro
    implementa e a raiz de composição liga os dois (ADR-016).

    Recebe o agendamento e o artista por identificador, não o objeto: a porta
    não devolve dado da agenda para o financeiro, só faz uma pergunta."""

    @abstractmethod
    def is_required_for(self, artist_id: uuid.UUID, belongs_to_quoted_work: bool) -> bool:
        """Se aquele horário exige sinal (RN-PAG-001 e RN-GST-004).

        Pergunta separada porque a agenda precisa dela **antes de o agendamento
        existir**: criar já aprovado exige sinal confirmado, e não há sinal
        confirmado para uma linha que ainda não foi gravada."""

    @abstractmethod
    def is_satisfied_for(
        self, booking_id: uuid.UUID, artist_id: uuid.UUID, belongs_to_quoted_work: bool
    ) -> bool:
        """Verdadeiro quando o horário pode ser aprovado: ou o sinal está
        confirmado, ou aquele agendamento não exige sinal (RN-GST-004)."""
