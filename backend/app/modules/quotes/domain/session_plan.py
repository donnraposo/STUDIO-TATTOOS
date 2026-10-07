from collections.abc import Sequence
from decimal import Decimal


class SessionPlan:
    """A aritmética das sessões de um orçamento (RN-ORC-005 e RN-ORC-006).

    Decisão pura, sem banco e sem ator: dado o que já foi executado e o que o
    orçamento prevê, quais sessões ainda precisam existir e quanto o conjunto
    compromete.

    Existe separada dos casos de uso porque é a parte que erra em silêncio.
    Gerar uma sessão a mais depois de uma reaprovação, ou somar o previsto onde
    deveria entrar o cobrado, não levanta exceção nenhuma — aparece semanas
    depois, no repasse, como um número que ninguém consegue explicar."""

    def next_sequence(self, settled_sequences: Sequence[int]) -> int:
        """A numeração continua de onde as sessões já resolvidas pararam.

        Reaproveitar um número usado colidiria com
        `uq_tattoo_session_sequence`, e a colisão apareceria como erro de banco
        na reaprovação de um orçamento cuja primeira sessão já foi feita."""
        return max(settled_sequences, default=0) + 1

    def remaining_values(
        self, settled_count: int, planned_sessions: int, value_per_session: Decimal
    ) -> list[Decimal]:
        """Quantas sessões ainda faltam, e por quanto cada uma.

        Nunca devolve lista negativa: o gestor pode reaprovar um orçamento com
        menos sessões do que já foram realizadas, e o que já aconteceu não se
        desfaz — nesse caso não falta nenhuma."""
        return [value_per_session] * max(planned_sessions - settled_count, 0)

    def committed_total(
        self, settled_values: Sequence[Decimal], remaining_values: Sequence[Decimal]
    ) -> Decimal:
        """O que o trabalho inteiro compromete: o que já foi cobrado mais o que
        ainda está previsto.

        É a soma que a RN-ORC-006 manda comparar com o valor aprovado depois de
        o gestor ajustar as sessões restantes. Soma `Decimal` do começo ao fim,
        e começa em `Decimal("0")` e não em `0` para que uma lista vazia devolva
        decimal e não inteiro."""
        return sum(settled_values, Decimal("0")) + sum(remaining_values, Decimal("0"))
