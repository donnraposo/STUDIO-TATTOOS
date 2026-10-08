# Runbook de implantação

> Como colocar o sistema no ar, como fazer a cópia de segurança voltar, e o que
> conferir quando algo parar. Escrito para ser seguido às duas da manhã por
> alguém que não escreveu o código.

**Última atualização:** 07/10/2026 · Sprint M8

---

## 0. O que sobe, e o que **não** sobe

Produção **não executa o mesmo conjunto de containers** que desenvolvimento. A
diferença que mais confunde: o frontend é container em desenvolvimento e **não
é** em produção.

| Container | Papel |
|---|---|
| `caddy` | TLS automático, proxy de `/api` e **entrega do frontend compilado** |
| `api` | FastAPI. Roda a migração antes de subir o servidor |
| `postgres` | Banco, com volume persistente e **sem porta publicada** |
| `backup` | Relógio da cópia diária |

> **O erro previsível aqui** é subir o `compose.yaml` no servidor. Ele é o de
> desenvolvimento: recarga automática, código montado por volume e
> `ENVIRONMENT=development` — que desliga a exigência de HTTPS no cookie de
> sessão e libera o `seed_demo`, capaz de criar contas com senha conhecida.
> O arquivo de produção é o **`compose.production.yaml`**.

---

## 1. Preparar o servidor

Um VPS com Docker e Docker Compose. As portas 80 e 443 precisam estar livres e
alcançáveis, e o domínio do estúdio precisa apontar para o IP **antes** da
primeira subida — o Caddy pede o certificado na hora em que sobe, e um domínio
que ainda não resolve vira uma tentativa gasta no limite do Let's Encrypt.

```bash
git clone https://github.com/donnraposo/STUDIO-TATTOOS.git
cd STUDIO-TATTOOS
```

---

## 2. O par de chaves da cópia

**Faça isto numa máquina que não seja o servidor.** A chave privada não pode
viver lá: o servidor cifra com a pública e **não consegue ler o que escreveu**,
e é isso que impede que uma invasão leve junto o histórico inteiro de cópias.

```bash
age-keygen -o chave-privada-backup.txt
```

A saída traz a linha `Public key: age1...`. Essa é a que vai para o servidor.

> **Guarde a chave privada em dois lugares, fora do servidor.** Sem ela não há
> restauração — nenhuma. Um gerenciador de senhas e um envelope físico é uma
> combinação razoável; duas cópias na mesma máquina não é.

---

## 3. O ambiente

```bash
cp .env.production.example .env.production
chmod 0600 .env.production
nano .env.production
```

O nome é `.env.production`, e não `.env`, de propósito: com o mesmo nome, uma
máquina que tenha o arquivo de desenvolvimento subiria produção com
`ENVIRONMENT=development`.

Preencher, no mínimo:

| Variável | O que é |
|---|---|
| `STUDIO_DOMAIN` | O domínio do estúdio, sem `https://` |
| `ACME_EMAIL` | Endereço **atendido**: é por onde o Let's Encrypt avisa de falha de renovação |
| `POSTGRES_PASSWORD` | `openssl rand -base64 36` |
| `BACKUP_AGE_RECIPIENT` | A chave **pública** do passo 2 |
| `BACKUP_S3_BUCKET` e `BACKUP_S3_ENDPOINT` | Balde separado, no provedor compatível com S3 |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Credencial com acesso **apenas a esse balde** |

---

## 4. Subir

```bash
docker compose -f compose.production.yaml --env-file .env.production up -d --build
```

A primeira subida compila o frontend dentro da imagem do Caddy e leva alguns
minutos. A API roda `alembic upgrade head` antes de abrir a porta.

### Conferir

```bash
docker compose -f compose.production.yaml --env-file .env.production ps
curl -s https://SEU-DOMINIO/api/v1/health      # {"status":"ok"}
curl -sI https://SEU-DOMINIO/ | head -1        # HTTP/2 200
curl -sI http://SEU-DOMINIO/ | head -1         # 308, redirecionando para https
```

E o relógio da cópia, que anuncia o próximo horário ao subir:

```bash
docker compose -f compose.production.yaml --env-file .env.production logs backup
# [agenda] copia diaria as 03:00, fuso IST
# [agenda] proxima copia em 8h 55min
```

### A primeira conta

Não há autocadastro no MVP, e o `seed_demo` se recusa a rodar em produção. A
conta de proprietário é criada uma vez, à mão:

```bash
docker compose -f compose.production.yaml --env-file .env.production exec api \
  python -c "
from app.core.container import Container
from app.modules.identity.domain.user_role import UserRole
from app.modules.identity.domain.user_status import UserStatus
from app.modules.identity.infrastructure.models.user_account import UserAccount
from app.modules.identity.infrastructure.password_hasher import PasswordHasher
import getpass
container = Container()
senha = getpass.getpass('Senha do proprietario: ')
with container.database.session() as s:
    s.add(UserAccount(email='PREENCHA@exemplo.ie', password_hash=PasswordHasher().hash(senha),
                      full_name='PREENCHA', artist_name='PREENCHA', phone='PREENCHA',
                      role=UserRole.OWNER, acts_as_artist=True, status=UserStatus.ACTIVE))
    s.commit()
print('pronto')
"
```

Daí em diante todas as contas saem da tela de contas.

---

## 5. Atualizar uma versão

```bash
git pull
docker compose -f compose.production.yaml --env-file .env.production up -d --build
```

A migração roda sozinha na subida da API. Há um intervalo de alguns segundos em
que o Caddy responde 502, entre o container antigo parar e o novo responder:
para um estúdio com um punhado de usuários isso é aceitável, e evitá-lo exigiria
duas instâncias da API e um desligamento coordenado.

> **Antes de atualizar, confira que a última cópia do dia existe.** Uma migração
> que falha no meio deixa o banco entre duas versões, e a saída é restaurar.

---

## 6. Restaurar

### 6.1 O teste trimestral (não toca em produção)

Exigido pela seção 4 de `03_REQUISITOS_NAO_FUNCIONAIS.md`. O script cria um
banco temporário ao lado, restaura ali, conta as linhas e derruba o banco.

```bash
# A chave privada entra só para o teste, e sai depois.
docker compose -f compose.production.yaml --env-file .env.production cp \
  chave-privada-backup.txt backup:/tmp/age-key

docker compose -f compose.production.yaml --env-file .env.production exec \
  -e BACKUP_AGE_KEY_FILE=/tmp/age-key backup /opt/backup/restore.sh

docker compose -f compose.production.yaml --env-file .env.production exec \
  backup rm -f /tmp/age-key
```

A saída traz a contagem de `user_account`, `client`, `booking`, `quote`,
`tattoo_session`, `payment`, `payout` e `audit_log`, e quantos arquivos vieram
no pacote. **Números em zero onde deveria haver dado é falha, mesmo com o script
terminando em sucesso** — restaurar prova que o arquivo abriu, não que o dado
está lá.

Anote a data do teste. Um teste que ninguém registra é um teste que ninguém sabe
se aconteceu.

### 6.2 A restauração de verdade

Não é automática de propósito: ela sobrescreve o que está no ar.

```bash
# 1. Para a aplicação. O banco continua de pé.
docker compose -f compose.production.yaml --env-file .env.production stop api caddy backup

# 2. Traz e abre o pacote (ajuste o nome).
docker compose -f compose.production.yaml --env-file .env.production exec backup bash -c '
  aws --endpoint-url "$BACKUP_S3_ENDPOINT" s3 cp \
    "s3://$BACKUP_S3_BUCKET/tattoo-studio-AAAA-MM-DDTHH-MM-SS.tar.age" /tmp/p.age
  age --decrypt --identity /tmp/age-key --output /tmp/p.tar /tmp/p.age
  tar --extract --file /tmp/p.tar --directory /tmp'

# 3. Recria o banco e restaura.
docker compose -f compose.production.yaml --env-file .env.production exec backup bash -c '
  export PGPASSWORD="$POSTGRES_PASSWORD"
  dropdb --host postgres --username "$POSTGRES_USER" --force "$POSTGRES_DB"
  createdb --host postgres --username "$POSTGRES_USER" "$POSTGRES_DB"
  pg_restore --host postgres --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    --no-owner --no-privileges /tmp/database.dump'

# 4. Os arquivos enviados. **Este passo some se o armazenamento virar S3.**
docker compose -f compose.production.yaml --env-file .env.production run --rm \
  -v tattoo-studio-production_object_storage:/destino backup \
  tar --extract --file /tmp/objects.tar --directory /destino

# 5. Volta.
docker compose -f compose.production.yaml --env-file .env.production start api caddy backup
```

> **Dois alvos, e não um.** Enquanto o armazenamento for o volume local, uma
> restauração que leve só o banco devolve um sistema que aponta para imagens de
> referência, comprovantes e fotos que não existem mais. O passo 4 não é
> opcional.

---

## 7. Quando algo para

| Sintoma | Onde olhar |
|---|---|
| Site não abre, certificado inválido | `logs caddy`. Domínio aponta para este IP? Portas 80 e 443 abertas? O Caddy precisa da 80 para validar o certificado |
| 502 em tudo | `logs api`. Quase sempre migração falhando na subida |
| 502 só em `/api` | A API caiu depois de subir. `logs api`, e `ps` para ver se reiniciou em laço |
| Login recusa senha certa | `ENVIRONMENT` é `production`? Com outro valor o cookie de sessão não é marcado como seguro e o navegador o descarta no HTTPS |
| Cópia parou | `logs backup`. O relógio reclama de variável ausente **na subida**, não às 3 da manhã |
| Disco cheio | `docker system prune -a` remove imagens antigas. **Nunca** com `--volumes`: ali estão o banco, os arquivos e os certificados |

### O que nunca fazer

- `docker compose ... down -v` em produção. O `-v` apaga os volumes: banco,
  arquivos enviados e certificados, de uma vez.
- Publicar a porta do `postgres`. Ele não tem `ports` de propósito.
- Editar `.env.production` sem reiniciar: o container lê na subida.

---

## 8. O que ficou decidido na M8 — 07/10/2026

| Decisão | Escolha | Consequência |
|---|---|---|
| Armazenamento de arquivos | **Volume local no VPS** | A cópia tem **dois alvos**. Trocar por S3 depois não alcança caso de uso nenhum: a porta `ObjectStorage` existe para isso (ADR-024) |
| Rotina de cópia | **Container no compose** | Viaja com a pilha; um servidor novo já sobe com cópia funcionando |
| Destino da cópia | **Provedor compatível com S3** | Balde separado, retenção de 30 dias feita pelo script |
| Segredos | **`.env.production` no servidor**, 0600 | Suficiente para um VPS com um sistema. O runbook documenta criação e rotação |
| Cifra | **`age` com chave pública** | O servidor escreve e não lê. A chave privada vive fora, e sem ela não há restauração |

### Ainda aguardando o responsável

- **RPO e RTO.** A proposta em `04_ARQUITETURA_TECNICA.md` é perda máxima de 24
  horas e recuperação em até 4 horas. Com cópia diária às 03:00, a perda máxima
  real é de 24 horas — coerente com a proposta.
- **Rotação de credenciais.** Nenhuma periodicidade decidida.
- **Homologação com proprietário e gerente**, que o objetivo da sprint exige e
  que só acontece com o sistema no ar.

---

## 9. O que foi verificado em 07/10/2026

Ensaio completo da pilha de produção, em máquina local, com `STUDIO_DOMAIN=localhost`:

| Passo | Resultado |
|---|---|
| As quatro imagens constroem | ✅ |
| Migração do zero até a `0010` em banco novo | ✅ |
| `https://.../` entrega a interface | ✅ 200, `text/html` |
| `https://.../api/v1/health` pelo mesmo domínio | ✅ `{"status":"ok"}` |
| Rota do SPA recarregada direto | ✅ 200 |
| `http://` redireciona para `https://` | ✅ 308 |
| Cabeçalhos de segurança e `Server` removido | ✅ |
| Banco inacessível de fora | ✅ |
| Relógio da cópia anuncia 03:00 no fuso do estúdio | ✅ |
| `pg_dump` + `tar` + `age` | ✅ |
| **O servidor não decifra o que cifrou** | ✅ `no identity matched any of the recipients` |
| Decifrar e restaurar em banco temporário | ✅ |
| **Dado gravado volta íntegro** | ✅ conta semeada reapareceu na restauração |
| Produção intocada pelo teste | ✅ |

**Não verificado**, porque depende de conta real: o envio ao provedor S3 e a
poda de 30 dias. O script falha ruidosamente se a credencial não servir, e o
relógio confere as variáveis na subida.
