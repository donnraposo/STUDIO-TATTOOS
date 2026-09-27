import os
import uuid
from pathlib import Path

from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.storage.object_storage import ObjectStorage


class FilesystemObjectStorage(ObjectStorage):
    """Armazenamento em diretório do sistema de arquivos.

    A raiz é um volume nomeado do Docker, não um caminho dentro da imagem: o
    conteúdo sobrevive a recriar o container e a reconstruir a imagem, que é o
    requisito do ADR-006 quando ele diz que arquivo não pode depender do sistema
    de arquivos efêmero.

    **A cópia de segurança passa a ter dois alvos**, o banco e este diretório. Uma
    rotina que leve apenas o `pg_dump` deixaria as imagens para trás, e a falta só
    apareceria no dia da restauração. Está registrado na sprint M8.

    A gravação é feita em arquivo temporário seguido de `os.replace`, que é
    atômico no mesmo sistema de arquivos. Escrever direto no destino final deixaria
    um arquivo truncado se o processo morresse no meio, e o banco apontaria para
    uma imagem pela metade — pior do que não ter imagem, porque parece existir."""

    def __init__(self, root: str) -> None:
        self._root = Path(root)

    def put(self, key: str, content: bytes, content_type: str) -> None:
        """`content_type` não é usado aqui: o tipo vive na linha do banco.

        Fica na assinatura porque pertence ao contrato da porta, que precisa
        servir também a um provedor compatível com S3, onde o tipo acompanha o
        objeto."""
        destination = self._resolve(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.partial")
        staging.write_bytes(content)
        os.replace(staging, destination)

    def open(self, key: str) -> bytes:
        destination = self._resolve(key)
        if not destination.is_file():
            raise BusinessRuleError("The stored file is no longer available.")
        return destination.read_bytes()

    def remove(self, key: str) -> None:
        self._resolve(key).unlink(missing_ok=True)

    def _resolve(self, key: str) -> Path:
        """Impede que a chave escape da raiz.

        As chaves são geradas pela aplicação e hoje nunca contêm `..`, mas esta
        classe não tem como saber disso, e um dia um caminho pode chegar de outro
        lugar. Uma chave capaz de sair da raiz transformaria o armazenamento em
        leitura e escrita arbitrárias no sistema de arquivos do container."""
        candidate = (self._root / key).resolve()
        root = self._root.resolve()
        if candidate != root and root not in candidate.parents:
            raise BusinessRuleError("Invalid storage key.")
        return candidate
