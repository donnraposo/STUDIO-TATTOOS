from decimal import Decimal

from app.modules.identity.domain.user_role import UserRole


class DepositPolicy:
    """O sinal: quanto vale e quais agendamentos o exigem (RN-PAG-001,
    RN-AGE-005 e RN-GST-004).

    **€50 por agendamento**, e não por trabalho: a RN-PAG-001 diz que cada
    sessão agendada exige o seu próprio sinal. O valor integra o preço da
    tatuagem e não é cobrança adicional (RN-PAG-005).

    **A exceção do guest.** A RN-GST-004 diz que o guest recebe diretamente dos
    clientes próprios e que esses valores **não passam pelo estúdio**. Exigir
    deles um sinal confirmado pelo gestor faria o estúdio receber dinheiro que a
    regra diz não passar por ele.

    Como o sistema reconhece esse caso, sem campo novo: o guest não acessa o
    módulo de orçamentos (RN-ORC-001), e quando o estúdio indica um cliente a ele
    é **o gestor quem cria o orçamento e o agendamento**. Logo, um agendamento de
    guest que não pertence a um trabalho orçado é, necessariamente, cliente
    próprio do guest. Quando pertence, veio de um orçamento criado pelo gestor —
    o cliente paga ao estúdio e o sinal é exigido como em qualquer outro
    (RN-GST-005).

    Decisão pura, sobre primitivos: o caso de uso traz o perfil do artista e se o
    horário pertence a um trabalho orçado."""

    AMOUNT = Decimal("50.00")

    def amount(self) -> Decimal:
        return DepositPolicy.AMOUNT

    def requires_deposit(self, artist_role: UserRole, belongs_to_quoted_work: bool) -> bool:
        return not (artist_role == UserRole.GUEST and not belongs_to_quoted_work)
