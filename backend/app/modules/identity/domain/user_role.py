from enum import StrEnum


class UserRole(StrEnum):
    """Perfis de acesso definidos em DOCS/01_REGRAS_DE_NEGOCIO.md secao 2."""

    OWNER = "OWNER"
    MANAGER = "MANAGER"
    RESIDENT = "RESIDENT"
    GUEST = "GUEST"
