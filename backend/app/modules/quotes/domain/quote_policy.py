import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser
from app.modules.identity.domain.user_role import UserRole
from app.modules.quotes.domain.quote_status import QuoteStatus


class QuotePolicy:
    """Quem pode o quê no orçamento (RN-ORC-001, RN-ORC-002 e RN-ORC-003).

    Repete a assimetria da agenda — residente propõe, gestor decide — com uma
    diferença que não existe lá: **o guest não tem acesso a orçamento**. Por isso
    `can_create` não pode usar `actor.tattoos`, que é verdadeiro para o guest; o
    perfil é conferido explicitamente. Quando um guest atende indicação do
    estúdio, o gestor cria o orçamento por ele."""

    def can_create(self, actor: AuthenticatedUser) -> bool:
        return actor.is_staff or actor.role == UserRole.RESIDENT

    def can_decide(self, actor: AuthenticatedUser) -> bool:
        """Aprovar e rejeitar são do gestor (RN-ORC-002)."""
        return actor.is_staff

    def can_see(self, actor: AuthenticatedUser, artist_id: uuid.UUID) -> bool:
        if self.sees_every_quote(actor):
            return True
        return actor.id == artist_id

    def sees_every_quote(self, actor: AuthenticatedUser) -> bool:
        """Separado de `can_see` porque a listagem decide antes de ter um
        orçamento em mão: ela precisa saber qual consulta fazer, e não julgar um
        registro já carregado."""
        return actor.is_staff

    def can_edit(
        self, actor: AuthenticatedUser, artist_id: uuid.UUID, status: QuoteStatus
    ) -> bool:
        """RN-ORC-003: o residente edita o próprio orçamento **enquanto pendente**.

        Orçamento já aprovado volta a pendente quando alterado, e essa alteração
        é do gestor: deixar o artista mexer no que já foi aprovado permitiria
        derrubar a aprovação sozinho, pelo simples ato de editar."""
        if actor.is_staff:
            return True
        return actor.id == artist_id and status == QuoteStatus.PENDING
