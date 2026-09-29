from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


class Database:
    """Fabrica de conexoes e sessoes. Encapsula o engine para que os modulos
    dependam desta fronteira, e nao diretamente do SQLAlchemy."""

    def __init__(self, url: str, echo: bool = False) -> None:
        self._engine = create_engine(url, echo=echo, pool_pre_ping=True)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

    @property
    def engine(self) -> Engine:
        return self._engine

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        """Devolve ao servidor as conexoes que o pool mantinha abertas.

        Na aplicacao roda uma vez, no encerramento. Na suite roda a cada teste,
        e ai ela e obrigatoria: cada teste monta um `Container` proprio, com
        engine proprio, e um pool que ninguem fecha continua segurando conexao
        depois que o teste terminou. Foi o que derrubou a suite ao passar de
        cento e poucos testes, com "sorry, too many clients already" -- uma
        falha que nao acusa o teste culpado, porque o culpado e o acumulo."""
        self._engine.dispose()

    def is_reachable(self) -> bool:
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return False
        return True
