class ReferenceImagePolicy:
    """Limites das imagens de referência (RN-ORC-004).

    Os três limites vêm da configuração, não do código: são operacionais, e o
    estúdio pode querer aceitar um arquivo maior sem esperar uma versão nova.

    São decisões puras e separadas, uma por limite, em vez de um único
    `is_acceptable`. O motivo é a mensagem: quem recebe a recusa precisa saber se
    o problema foi o tipo, o tamanho ou a quantidade, e um booleano só diria que
    não deu."""

    def __init__(
        self,
        allowed_types: frozenset[str],
        max_bytes: int,
        max_per_quote: int,
    ) -> None:
        self._allowed_types = allowed_types
        self._max_bytes = max_bytes
        self._max_per_quote = max_per_quote

    @property
    def allowed_types(self) -> frozenset[str]:
        return self._allowed_types

    @property
    def max_bytes(self) -> int:
        return self._max_bytes

    @property
    def max_per_quote(self) -> int:
        return self._max_per_quote

    def accepts_type(self, content_type: str) -> bool:
        """Compara sem o parâmetro do cabeçalho: `image/jpeg; charset=binary`
        chega assim de alguns clientes e é o mesmo tipo."""
        return content_type.split(";")[0].strip().lower() in self._allowed_types

    def accepts_size(self, byte_size: int) -> bool:
        return 0 < byte_size <= self._max_bytes

    def accepts_one_more(self, current_count: int) -> bool:
        return current_count < self._max_per_quote
