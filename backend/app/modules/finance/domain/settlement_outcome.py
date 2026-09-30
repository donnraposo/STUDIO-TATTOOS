from dataclasses import dataclass


@dataclass(frozen=True)
class SettlementOutcome:
    """O que fazer com o dinheiro já recebido de um agendamento.

    Três decisões separadas em vez de um único rótulo, porque as regras separam:
    o sinal pode ser devolvido (RN-PAG-003), retido pelo estúdio (RN-AGE-009 e
    RN-AGE-010) ou seguir para o novo horário (RN-AGE-008), e o que foi pago
    **acima** do sinal segue caminho próprio — é devolvido em quase todos os
    desfechos (RN-PAG-004).

    Imutável: descreve um desfecho já decidido, não um rascunho a preencher."""

    refund_deposit: bool
    retain_deposit: bool
    refund_above_deposit: bool

    @property
    def keeps_everything(self) -> bool:
        """Remarcação dentro do prazo: nada é devolvido nem retirado, os valores
        acompanham o horário novo."""
        return not (self.refund_deposit or self.retain_deposit or self.refund_above_deposit)
