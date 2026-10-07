from enum import StrEnum


class QuoteStatus(StrEnum):
    """Estados do orçamento (RN-ORC-002 e RN-ORC-003).

    Não há vencimento automático: o orçamento fica em `PENDING` até uma decisão
    manual do gestor, por quanto tempo for.

    O ciclo não é de mão única. Alterar um orçamento aprovado o devolve a
    `PENDING` e exige nova aprovação, porque o percentual do artista é congelado
    na aprovação (RN-REP-006) e mudar o valor sem reaprovar deixaria um
    percentual antigo aplicado a um trabalho novo."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
