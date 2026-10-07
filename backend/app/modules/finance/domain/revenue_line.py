import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class RevenueLine:
    """Um atendimento no detalhamento do período (RN 10.4).

    É a linha da planilha que o estúdio mantém à mão: quando entrou, de quem foi
    o trabalho, quanto o cliente pagou, quanto ficou com o artista e quanto ficou
    com o estúdio.

    **`percentage` é o congelado da sessão** (RN-REP-006), e não o acordo
    vigente. Um relatório de março precisa mostrar março: lendo o percentual de
    hoje, cada renegociação reescreveria o passado.

    **`settled_at` é quando o estúdio reconheceu o dinheiro**, não quando a
    tatuagem foi feita. É o mesmo critério do repasse (RN-REP-004), e é o que
    faz os dois números baterem quando alguém os compara.

    **Sem o nome do artista, de propósito.** Quem resolve identificador em nome
    é a tela, como já faz no repasse — carregar o nome aqui faria o relatório
    depender do módulo de identidade para dizer um número.

    Imutável: descreve um fato já ocorrido."""

    session_id: uuid.UUID
    artist_id: uuid.UUID
    settled_at: datetime
    value: Decimal
    percentage: Decimal
    artist_amount: Decimal
    studio_amount: Decimal
    #: Verdadeiro quando o repasse desta sessão já foi transferido ao artista.
    #: É a coluna "Status" da planilha, e o que o estúdio confere no fim do mês.
    transferred: bool
