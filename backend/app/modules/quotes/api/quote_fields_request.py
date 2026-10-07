from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.modules.quotes.domain.quote_details import QuoteDetails
from app.modules.quotes.domain.quote_origin import QuoteOrigin


class QuoteFieldsRequest(BaseModel):
    """Os campos editáveis de um orçamento (RN-ORC-004).

    Serve diretamente à edição e é a base da criação, que acrescenta cliente e
    artista. Uma lista só, num lugar só.

    O texto é aparado pelo próprio schema, com `strip_whitespace`, em vez de por
    `.strip()` espalhado nos casos de uso: limpar espaço do que foi digitado é
    assunto da borda da aplicação, não da regra de negócio.

    Os limites de valor repetem as restrições da migração `0005` de propósito. O
    banco recusa por último, mas quem está digitando merece a mensagem de campo
    antes disso."""

    origin: QuoteOrigin
    description: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    body_region: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
    ]
    size_estimate: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
    ]
    total_value: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    planned_sessions: int = Field(ge=1)
    planned_value_per_session: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    estimated_duration_minutes: int = Field(gt=0)
    notes: Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=2000)] = None

    def to_details(self) -> QuoteDetails:
        """Observação vazia vira ausente: `""` e `"   "` não são uma anotação."""
        return QuoteDetails(
            origin=self.origin,
            description=self.description,
            body_region=self.body_region,
            size_estimate=self.size_estimate,
            total_value=self.total_value,
            planned_sessions=self.planned_sessions,
            planned_value_per_session=self.planned_value_per_session,
            estimated_duration_minutes=self.estimated_duration_minutes,
            notes=self.notes or None,
        )
