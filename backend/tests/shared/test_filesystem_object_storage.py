"""Garantias do armazenamento em sistema de arquivos.

Não passam por caso de uso nem por rota: o que se verifica é o adaptador, que é a
peça que a M8 vai trocar por um provedor gerenciado. Se estas garantias não
estiverem escritas aqui, a troca não terá contra o que ser conferida.
"""

from pathlib import Path

import pytest

from app.shared.errors.business_rule_error import BusinessRuleError
from app.shared.storage.filesystem_object_storage import FilesystemObjectStorage


def test_stores_and_reads_back_the_same_bytes(tmp_path: Path) -> None:
    storage = FilesystemObjectStorage(str(tmp_path))

    storage.put("quotes/abc/image.png", b"reference-bytes", "image/png")

    assert storage.open("quotes/abc/image.png") == b"reference-bytes"


def test_creates_the_directory_tree_of_the_key(tmp_path: Path) -> None:
    """A chave traz o orçamento no caminho; o diretório não existe antes."""
    storage = FilesystemObjectStorage(str(tmp_path))

    storage.put("quotes/deep/nested/image.png", b"x", "image/png")

    assert (tmp_path / "quotes" / "deep" / "nested" / "image.png").is_file()


def test_overwrites_without_leaving_the_temporary_file(tmp_path: Path) -> None:
    """A gravação é em arquivo temporário seguido de troca atômica.

    O cenário negativo é o temporário sobreviver: um `.partial` esquecido no
    diretório seria contado por qualquer rotina que varresse o armazenamento, e
    apareceria numa cópia de segurança como se fosse conteúdo."""
    storage = FilesystemObjectStorage(str(tmp_path))
    storage.put("image.png", b"first", "image/png")

    storage.put("image.png", b"second", "image/png")

    assert storage.open("image.png") == b"second"
    assert [entry.name for entry in tmp_path.iterdir()] == ["image.png"]


def test_reading_a_missing_key_fails_as_a_business_rule(tmp_path: Path) -> None:
    """Arquivo ausente vira erro de domínio, e não `FileNotFoundError`.

    A linha existir no banco e o arquivo não é a inconsistência que a ordem de
    gravação evita, mas ela pode chegar de uma cópia restaurada pela metade. Vira
    422 com mensagem, não 500."""
    storage = FilesystemObjectStorage(str(tmp_path))

    with pytest.raises(BusinessRuleError):
        storage.open("nao/existe.png")


def test_removing_twice_is_not_an_error(tmp_path: Path) -> None:
    storage = FilesystemObjectStorage(str(tmp_path))
    storage.put("image.png", b"x", "image/png")

    storage.remove("image.png")
    storage.remove("image.png")

    assert not (tmp_path / "image.png").exists()


@pytest.mark.parametrize(
    "escaping_key",
    ["../fora.png", "quotes/../../fora.png", "/etc/passwd"],
)
def test_a_key_cannot_escape_the_storage_root(tmp_path: Path, escaping_key: str) -> None:
    """Chave que sai da raiz transformaria o armazenamento em leitura e escrita
    arbitrárias no sistema de arquivos do container.

    Hoje as chaves são geradas pela aplicação e nunca têm `..`. O adaptador não
    tem como saber disso, e um dia o caminho pode chegar de outro lugar."""
    storage = FilesystemObjectStorage(str(tmp_path / "root"))

    with pytest.raises(BusinessRuleError):
        storage.put(escaping_key, b"x", "image/png")
