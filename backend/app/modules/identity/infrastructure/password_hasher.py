from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher


class PasswordHasher:
    """Hash de senha com Argon2id (ADR-010).

    Encapsula a biblioteca para que os casos de uso dependam desta fronteira.
    Trocar o algoritmo no futuro nao alcanca o dominio."""

    def __init__(self) -> None:
        self._hasher = PasswordHash((Argon2Hasher(),))

    def hash(self, plain_password: str) -> str:
        return self._hasher.hash(plain_password)

    def verify(self, plain_password: str, password_hash: str) -> bool:
        return self._hasher.verify(plain_password, password_hash)
