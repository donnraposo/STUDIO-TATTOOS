"""Aritmética das sessões (RN-ORC-005 e RN-ORC-006).

Classe pura, sem banco: é o tipo de conta que erra em silêncio. Gerar uma sessão
a mais depois de uma reaprovação, ou somar o previsto onde deveria entrar o
cobrado, não levanta exceção nenhuma — aparece semanas depois, no repasse.
"""

from decimal import Decimal

from app.modules.quotes.domain.session_plan import SessionPlan


def test_sequence_starts_at_one_when_nothing_was_done() -> None:
    assert SessionPlan().next_sequence([]) == 1


def test_sequence_continues_after_the_sessions_already_settled() -> None:
    """Reaproveitar um número colidiria com `uq_tattoo_session_sequence`, e a
    colisão apareceria na reaprovação de um orçamento já em execução."""
    assert SessionPlan().next_sequence([1, 2]) == 3


def test_sequence_ignores_gaps_and_uses_the_highest() -> None:
    assert SessionPlan().next_sequence([1, 4]) == 5


def test_remaining_covers_what_is_missing_from_the_plan() -> None:
    values = SessionPlan().remaining_values(
        settled_count=1, planned_sessions=4, value_per_session=Decimal("250.00")
    )

    assert values == [Decimal("250.00")] * 3


def test_remaining_is_empty_when_the_plan_shrank_below_what_was_done() -> None:
    """O gestor pode reaprovar com menos sessões do que já foram realizadas. O
    que aconteceu não se desfaz — só não falta mais nenhuma."""
    values = SessionPlan().remaining_values(
        settled_count=3, planned_sessions=2, value_per_session=Decimal("250.00")
    )

    assert values == []


def test_committed_total_adds_what_was_charged_to_what_is_still_planned() -> None:
    total = SessionPlan().committed_total(
        [Decimal("100.00"), Decimal("250.00")], [Decimal("250.00")]
    )

    assert total == Decimal("600.00")


def test_committed_total_of_nothing_is_decimal_zero() -> None:
    """Zero inteiro compararia igual, mas entraria numa soma de `Decimal` como
    tipo alheio — e é comparado contra `total_value`, que é decimal exato."""
    total = SessionPlan().committed_total([], [])

    assert total == Decimal("0")
    assert isinstance(total, Decimal)


def test_committed_total_keeps_the_cents_exact() -> None:
    """Três sessões de 133,33 fecham 399,99. Em ponto flutuante dariam
    399.99000000000007, e o repasse sairia de um número que ninguém escreveu."""
    total = SessionPlan().committed_total([], [Decimal("133.33")] * 3)

    assert total == Decimal("399.99")
