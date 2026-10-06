from app.modules.identity.domain.authenticated_user import AuthenticatedUser


class RevenuePolicy:
    """Quem vê o faturamento do estúdio (RN 10.4).

    A regra é curta: *"proprietário e gerente terão acesso aos seguintes
    relatórios"*. O artista não entra, e não é descuido — este relatório mostra
    quanto **todo mundo** recebeu e quanto a casa ficou. A RN-REP-004 já limita
    o artista aos próprios valores, e abrir o faturamento a ele contradiria
    aquela regra por outra porta.

    O artista continua vendo o que lhe diz respeito na tela de repasses, com o
    recorte que é dele.

    Função pura de decisão: sem banco, sem HTTP."""

    def can_see(self, actor: AuthenticatedUser) -> bool:
        return actor.is_staff
