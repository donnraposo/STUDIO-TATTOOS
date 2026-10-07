from abc import ABC, abstractmethod


class ObjectStorage(ABC):
    """Contrato de armazenamento privado de arquivos (ADR-006, revisto na M4.3).

    Fica em `shared/` e não dentro de `quotes/` porque três módulos vão depender
    dele: as imagens de referência do orçamento, as fotos de cicatrização do
    pós-venda e os comprovantes de pagamento. Se a abstração morasse no módulo de
    orçamentos, os outros dois passariam a importá-lo — uma dependência entre
    módulos de negócio que não existe no domínio.

    **Não há método que devolva endereço.** O arquivo é lido por `open` e
    entregue por um endpoint que confere a sessão, de modo que não existe nenhum
    endereço capaz de abrir a imagem sem o cookie do usuário. Um esquema com URL
    assinada seria mais frágil: o endereço funciona sozinho enquanto não expira, e
    basta ele vazar num histórico de navegador ou num encaminhamento.

    O contrato é deliberadamente pequeno. Gravar, ler e remover é tudo o que os
    casos de uso precisam, e um contrato maior tornaria mais difícil a troca para
    provedor gerenciado prevista na M8."""

    @abstractmethod
    def put(self, key: str, content: bytes, content_type: str) -> None:
        """Grava o objeto sob a chave informada, sobrescrevendo se existir.

        `content_type` faz parte do contrato porque um provedor compatível com S3
        o guarda junto do objeto. A implementação em sistema de arquivos o ignora:
        ali o tipo vive na linha do banco, que é a fonte usada para responder."""

    @abstractmethod
    def open(self, key: str) -> bytes:
        """Devolve o conteúdo do objeto. Falha se a chave não existir."""

    @abstractmethod
    def remove(self, key: str) -> None:
        """Remove o objeto. Não falha se a chave já não existir."""
