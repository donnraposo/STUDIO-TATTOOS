from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceImageContent:
    """O arquivo de uma imagem de referência, pronto para ser respondido.

    O tipo vem da linha do banco e não do arquivo: é o que foi validado contra a
    lista de tipos aceitos no momento do upload. Deduzir o tipo do conteúdo na
    hora de responder abriria a porta para servir como imagem algo que passou por
    outro caminho.

    Existe como objeto próprio em vez de um par solto porque conteúdo e tipo não
    fazem sentido separados: responder os bytes com o tipo errado é o mesmo que
    não responder."""

    content_type: str
    content: bytes
