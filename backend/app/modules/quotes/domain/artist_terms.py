import uuid
from abc import ABC, abstractmethod
from decimal import Decimal


class ArtistTerms(ABC):
    """Porta pela qual o orçamento pergunta o acordo de um artista.

    Quem sabe responder é o módulo de identidade, dono das contas. Quem
    **precisa** da resposta é a aprovação do orçamento, que congela o percentual
    (RN-REP-006) — e por isso a porta é dela, como nas demais fronteiras do
    projeto (ADR-028).

    **Nulo significa "use a regra da origem".** A ausência é o dado: a maior
    parte dos artistas não tem acordo próprio e segue os 70% de cliente próprio
    ou os 50% de indicação do estúdio.

    Devolve apenas o número. Se devolvesse a conta inteira, o orçamento passaria
    a conhecer perfil, estado e credencial de alguém para decidir uma divisão de
    dinheiro — e mexer na conta quebraria o orçamento."""

    @abstractmethod
    def default_percentage_for(self, artist_id: uuid.UUID) -> Decimal | None:
        """O percentual acordado com este artista, ou nulo se não houver."""
