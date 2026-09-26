import uuid

from app.modules.identity.domain.authenticated_user import AuthenticatedUser


class ClientVisibilityPolicy:
    """Quem enxerga o quê de um cliente (RN-CLI-004).

    Há três níveis, e a diferença entre os dois últimos é o ponto sensível:

    - Proprietário e gerente veem todos os clientes por inteiro.
    - O artista vê a ficha completa apenas de quem ele cadastrou.
    - O artista para quem o estúdio indicou um cliente de outro artista vê
      somente nome, telefone e Instagram — nunca o histórico anterior.

    O terceiro caso não é 'negar acesso': é devolver menos campos. Por isso a
    decisão de projeção fica aqui, e não como um simples sim ou não na rota."""

    def can_see_full_record(
        self, actor: AuthenticatedUser, registered_by_artist_id: uuid.UUID
    ) -> bool:
        if actor.is_staff:
            return True
        return actor.id == registered_by_artist_id

    def can_edit(self, actor: AuthenticatedUser, registered_by_artist_id: uuid.UUID) -> bool:
        """RN-CLI-006: o artista corrige apenas os clientes que cadastrou."""
        if actor.is_staff:
            return True
        return actor.id == registered_by_artist_id

    def can_register(self, actor: AuthenticatedUser) -> bool:
        """Residente cadastra durante o agendamento; guest informa os dados na
        própria reserva, sem manter cadastro (RN-CLI-001)."""
        return actor.is_staff or actor.tattoos

    def can_merge(self, actor: AuthenticatedUser) -> bool:
        """Somente proprietário e gerente unem duplicidades (RN-CLI-006)."""
        return actor.is_staff

    def can_list_all(self, actor: AuthenticatedUser) -> bool:
        return actor.is_staff
