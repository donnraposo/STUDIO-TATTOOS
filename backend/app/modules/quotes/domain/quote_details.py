from dataclasses import dataclass
from decimal import Decimal

from app.modules.quotes.domain.quote_origin import QuoteOrigin


@dataclass(frozen=True)
class QuoteDetails:
    """Os campos descritivos e de valor de um orçamento (RN-ORC-004).

    Existe porque criar e editar tratam exatamente do mesmo conjunto de campos.
    Sem este objeto, os dois casos de uso carregavam oito argumentos idênticos
    cada um, o roteador repetia a lista duas vezes e acrescentar um campo ao
    orçamento significava editar seis lugares — com a chance de esquecer um deles
    justamente no caminho menos usado.

    Imutável porque não é um rascunho a ser preenchido aos poucos: representa o
    orçamento pretendido, já validado, num único instante.

    Não inclui cliente nem artista de propósito. Quem é atendido e por quem não é
    um detalhe do trabalho: é a identidade do atendimento, definida na criação e
    intocada pela edição."""

    origin: QuoteOrigin
    description: str
    body_region: str
    size_estimate: str
    total_value: Decimal
    planned_sessions: int
    planned_value_per_session: Decimal
    estimated_duration_minutes: int
    notes: str | None = None
