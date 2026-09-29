"""Registro unico dos modelos persistentes.

O SQLAlchemy so conhece uma tabela depois que a classe que a mapeia e
importada. Quando uma chave estrangeira aponta para uma tabela que ninguem
importou, a resolucao falha **no momento da gravacao** -- nao na inicializacao.

Foi exatamente o que aconteceu: `booking.session_id` aponta para
`tattoo_session`, o modulo de agenda importa `Booking` e nada importava
`TattooSession`. A aplicacao subia, respondia consultas, e so quebrava ao
inserir um agendamento, com `NoReferencedTableError`. A suite de testes nao
pegava porque o pytest carrega todos os modulos de teste no mesmo processo, e os
testes de orcamento importavam o modelo que faltava -- o defeito existia so onde
nao havia teste olhando: o servidor rodando de verdade.

Este modulo existe para que isso nao dependa de sorte. Ele e importado pela raiz
de composicao e pelo `env.py` das migracoes, entao **um unico lugar** lista o que
esta mapeado. Acrescentar tabela e acrescentar uma linha aqui.
"""

from app.core.orm_base import OrmBase
from app.modules.clients.infrastructure.models.client import Client
from app.modules.identity.infrastructure.models.password_reset_token import PasswordResetToken
from app.modules.identity.infrastructure.models.user_account import UserAccount
from app.modules.identity.infrastructure.models.user_session import UserSession
from app.modules.identity.infrastructure.models.user_status_history import UserStatusHistory
from app.modules.quotes.infrastructure.models.quote import Quote
from app.modules.quotes.infrastructure.models.quote_reference_image import QuoteReferenceImage
from app.modules.quotes.infrastructure.models.tattoo_session import TattooSession
from app.modules.reporting.infrastructure.models.audit_log import AuditLog
from app.modules.scheduling.infrastructure.models.booking import Booking
from app.modules.scheduling.infrastructure.models.booth import Booth

#: Tudo o que esta mapeado. A lista e explicita para que o import nao pareca
#: acidental e nenhuma ferramenta de limpeza a remova por "nao estar em uso".
REGISTERED_MODELS = (
    Client,
    PasswordResetToken,
    UserAccount,
    UserSession,
    UserStatusHistory,
    Quote,
    QuoteReferenceImage,
    TattooSession,
    AuditLog,
    Booking,
    Booth,
)

#: Metadados completos, prontos para o Alembic comparar contra o banco.
METADATA = OrmBase.metadata
