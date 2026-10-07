from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.domain.settled_session import SettledSession
from app.modules.finance.domain.settled_sessions import SettledSessions
from app.modules.quotes.domain.session_status import SessionStatus
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.models.tattoo_session import TattooSession


class QuoteSettledSessions(SettledSessions):
    """A resposta do módulo de orçamentos ao repasse (RN-PAG-008).

    Implementa a porta que o financeiro declarou. É aqui que as duas metades se
    encontram, e só aqui: o repasse continua sem conhecer orçamento, e o
    orçamento continua sem conhecer repasse.

    **Só `PAID_OFF` entra.** A RN-PAG-008 é explícita: "o repasse será liberado
    somente depois que a sessão estiver realizada e integralmente quitada".
    Sessão realizada e ainda não confirmada pelo gestor fica de fora — pagar
    antes da confirmação é pagar sobre dinheiro que o estúdio ainda não viu.

    **O artista vem do orçamento**, não da sessão: é o orçamento que define de
    quem é o atendimento. O percentual, ao contrário, vem da **sessão**, onde foi
    congelado na aprovação (RN-REP-006) — ler o do orçamento mostraria o acordo
    de hoje sobre trabalho aprovado sob outro."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def settled_between(self, opening: datetime, closing: datetime) -> list[SettledSession]:
        statement = (
            select(
                TattooSession.id,
                Quote.artist_id,
                TattooSession.charged_value,
                TattooSession.artist_percentage,
                TattooSession.confirmed_at,
            )
            .join(Quote, Quote.id == TattooSession.quote_id)
            .where(
                TattooSession.status == SessionStatus.PAID_OFF,
                TattooSession.confirmed_at > opening,
                TattooSession.confirmed_at <= closing,
                TattooSession.charged_value > 0,
            )
            .order_by(TattooSession.confirmed_at)
        )

        return [
            SettledSession(
                session_id=row.id,
                artist_id=row.artist_id,
                received_amount=row.charged_value,
                percentage=row.artist_percentage,
                confirmed_at=row.confirmed_at,
            )
            for row in self._session.execute(statement)
        ]
