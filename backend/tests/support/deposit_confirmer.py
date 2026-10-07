from fastapi.testclient import TestClient


class DepositConfirmer:
    """Cumpre a pré-condição da RN-AGE-005 num passo: registra o sinal de €50 e
    o confirma, para que o agendamento possa ser aprovado.

    Existe porque **toda** aprovação de agendamento passa a exigir isso, e a
    sequência é sempre a mesma: `POST /payments` e `POST /payments/{id}/confirm`.
    Copiada em cada teste, bastaria uma cópia divergir para o teste passar a
    exercitar outra coisa — e um helper que mente sobre a pré-condição é pior do
    que nenhum.

    Usa a API e não o banco de propósito: é o caminho que o gestor percorre, e
    um atalho pelo `INSERT` deixaria de exercitar justamente o portão que os
    testes querem ver fechado."""

    AMOUNT = "50.00"

    def __init__(self, client: TestClient, api_prefix: str) -> None:
        self._client = client
        self._api_prefix = api_prefix

    def confirm_for(self, booking_id: str, headers: dict[str, str]) -> str:
        """Devolve o identificador do pagamento confirmado."""
        payment_id = self.register_for(booking_id, headers)
        confirmed = self._client.post(
            f"{self._api_prefix}/payments/{payment_id}/confirm", headers=headers
        )
        assert confirmed.status_code == 200, confirmed.text
        return payment_id

    def register_for(self, booking_id: str, headers: dict[str, str]) -> str:
        """Só informa, sem confirmar: é o estado em que a aprovação ainda deve
        ser recusada."""
        reported = self._client.post(
            f"{self._api_prefix}/payments",
            json={
                "booking_id": booking_id,
                "amount": DepositConfirmer.AMOUNT,
                "kind": "DEPOSIT",
                "method": "BANK_TRANSFER",
            },
            headers=headers,
        )
        assert reported.status_code == 201, reported.text
        return reported.json()["id"]
