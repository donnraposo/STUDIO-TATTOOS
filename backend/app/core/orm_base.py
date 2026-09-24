from sqlalchemy.orm import DeclarativeBase


class OrmBase(DeclarativeBase):
    """Base declarativa unica do projeto. Todo modelo persistente herda daqui,
    para que o Alembic enxergue um so registro de metadados."""
