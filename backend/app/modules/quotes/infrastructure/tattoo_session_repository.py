import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.quotes.infrastructure.models.tattoo_session import TattooSession


class TattooSessionRepository:
    """Acesso às sessões de tatuagem.

    O parâmetro se chama `record` e não `session`: neste arquivo `Session` já é
    a sessão de banco do SQLAlchemy, e duas coisas diferentes com o mesmo nome
    em quinze linhas é o tipo de confusão que passa na revisão."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist(self, record: TattooSession) -> TattooSession:
        self._session.add(record)
        self._session.flush()
        return record

    def find_by_id(self, session_id: uuid.UUID) -> TattooSession | None:
        return self._session.get(TattooSession, session_id)

    def list_for_quote(self, quote_id: uuid.UUID) -> list[TattooSession]:
        statement = (
            select(TattooSession)
            .where(TattooSession.quote_id == quote_id)
            .order_by(TattooSession.sequence_number)
        )
        return list(self._session.execute(statement).scalars())

    def remove(self, record: TattooSession) -> None:
        """Apaga de verdade, e só é chamado para sessão ainda agendada.

        Sessão realizada nunca passa por aqui: ela é histórico, e o que sai do
        banco não aparece em auditoria de repasse nenhuma."""
        self._session.delete(record)
        self._session.flush()
