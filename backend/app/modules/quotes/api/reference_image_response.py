import uuid
from datetime import datetime

from pydantic import BaseModel

from app.modules.quotes.infrastructure.models.quote_reference_image import QuoteReferenceImage


class ReferenceImageResponse(BaseModel):
    """Imagem de referência devolvida ao cliente da API.

    **Não expõe `object_key`.** A chave é o endereço interno do objeto e não diz
    nada de útil a quem consome a API; publicá-la só ofereceria informação para
    tentar alcançar o arquivo por fora da rota que confere a sessão.

    `content_path` é o caminho autenticado que devolve a imagem. Não é um endereço
    assinado nem temporário: ele só responde com o cookie de sessão, então pode
    ser guardado pela interface sem virar um vazamento se for copiado."""

    id: uuid.UUID
    content_type: str
    byte_size: int
    uploaded_at: datetime
    content_path: str

    @classmethod
    def from_model(
        cls, image: QuoteReferenceImage, content_path: str
    ) -> "ReferenceImageResponse":
        return cls(
            id=image.id,
            content_type=image.content_type,
            byte_size=image.byte_size,
            uploaded_at=image.uploaded_at,
            content_path=content_path,
        )
