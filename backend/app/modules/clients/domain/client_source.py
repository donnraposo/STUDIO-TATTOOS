from enum import StrEnum


class ClientSource(StrEnum):
    """Como o cliente chegou ao estúdio (RN-CLI-002).

    É a pergunta que a regra faz para decidir a origem de um atendimento: *"o
    cliente retornou ao mesmo artista **que o trouxe**?"*. Sem ela, o sistema só
    sabia quem digitou o cadastro — que é outra coisa, e diverge justamente no
    caso que importa (RN-GST-005).

    **Existe separada da `QuoteOrigin`, e de propósito.** Os nomes se parecem e
    os fatos não são o mesmo: esta diz de onde o cliente veio, uma vez; aquela
    diz o que vale **neste** atendimento, e pode mudar a cada um. Compartilhar um
    enum faria a primeira parecer decidir a segunda, que é exatamente o que a
    RN-CLI-002 não permite.

    `ARTIST` exige saber qual artista; `STUDIO` não tem artista por definição — o
    cliente chegou ao salão, não pela mão de alguém."""

    ARTIST = "ARTIST"
    STUDIO = "STUDIO"
