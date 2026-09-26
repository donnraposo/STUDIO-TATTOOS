# Tattoo Studio — Diretrizes Permanentes

> Carregado automaticamente no início de toda sessão. É a fonte das regras de
> trabalho. Leia antes de qualquer ação.

## 0. Leia a documentação, não o código

Para entender o projeto, **consulte `DOCS/` — não varra o repositório**. A
documentação é mantida atualizada a cada entrega exatamente para evitar isso.

| Preciso entender | Leia |
|---|---|
| Onde o projeto parou e o que vem agora | `DOCS/00_CONTEXTO_E_CONTINUIDADE.md` |
| Regras de negócio | `DOCS/01_REGRAS_DE_NEGOCIO.md` |
| Requisitos de desempenho, segurança e backup | `DOCS/03_REQUISITOS_NAO_FUNCIONAIS.md` |
| Arquitetura da solução | `DOCS/04_ARQUITETURA_TECNICA.md` |
| Entidades, relacionamentos e restrições | `DOCS/05_MODELO_DADOS.md` |
| Pastas, módulos, convenções e API | `DOCS/06_ESTRUTURA_PROJETO.md` |
| Cenários de teste e critérios de aceite | `DOCS/07_PLANO_TESTES.md` |
| Por que cada decisão foi tomada | `DOCS/08_DECISOES_ARQUITETURA.md` |
| **Andamento das sprints** | **`DOCS/09_ROADMAP_IMPLEMENTACAO.md`** |

## 1. O que é o sistema

Gestão interna de um estúdio de tatuagem em Cork City, Irlanda. Quatro perfis —
proprietário, gerente, residente e guest — administram clientes, agenda de macas,
orçamentos, sessões, pagamentos, repasses semanais e pós-venda. O cliente final
**não tem conta nem acesso**.

Moeda: euro. Fuso: `Europe/Dublin`. Interface em inglês; documentação em português.

## 2. MODO ARQUITETO — não implementar sem aprovação

Discutir não é autorizar. Planejar não é autorizar.

Antes de aprovação explícita é **proibido**: criar ou alterar arquivos, escrever
código, instalar dependências, executar comandos que modifiquem o projeto, alterar
o banco.

Palavras que liberam: **OK**, **Aprovado**, **Pode implementar**, **Pode começar**,
**Execute**.

Havendo dúvida crítica, **perguntar antes de propor solução**. Nunca assumir
requisito.

### Nunca

Assumir requisitos · começar pelo código · criar testes sem autorização · alterar
arquitetura aprovada sem explicar impacto, apresentar alternativa e obter aprovação
· instalar dependências sem autorização · remover funcionalidade existente sem
aprovação.

### Sempre

Explicar antes de executar · informar os arquivos que serão modificados ·
implementar em etapas pequenas · testar · documentar · registrar decisões.

## 3. Clean Code e SOLID

- **Uma classe própria do projeto por arquivo. Nunca mais de uma.** Nenhuma função
  de nível superior convive com uma classe no mesmo arquivo.
- Nome do arquivo corresponde à responsabilidade da unidade.
- Sem regra de negócio em rotas, schemas Pydantic ou tarefas do worker.
- Camadas internas não importam a camada de apresentação.
- O caso de uso delimita a transação.
- Extensão por dados tipados (mapas `Record`/`dict`), não por condicional espalhada.
- `__init__.py` não esconde dependência com reexportação extensa.

**Verificação rápida da convenção:**

```bash
for f in $(find backend/app -name "*.py" ! -name "__init__.py"); do
  c=$(grep -cE '^class ' "$f"); fn=$(grep -cE '^def |^async def ' "$f")
  if [ "$c" -gt 1 ] || { [ "$c" -ge 1 ] && [ "$fn" -ge 1 ]; }; then echo "VIOLACAO: $f"; fi
done
```

## 4. Padrões estabelecidos

| Padrão | Onde | ADR |
|---|---|---|
| Raiz de composição em `Container`, com uma fábrica por módulo | `app/core/container.py` | ADR-016 |
| Roteadores são classes com método `build()` | `*/api/*_router.py` | — |
| Erro de domínio traduzido em um único lugar | `app/core/error_handlers.py` | ADR-021 |
| Autenticação de requisição em peça única | `SessionAuthenticator` | ADR-022 |
| Políticas de permissão como funções puras de decisão | `*/domain/*_policy.py` | — |
| Integridade crítica garantida pelo banco, não só pela aplicação | migrações | ADR-011, ADR-012 |

Módulo novo segue esse desenho: `domain/`, `application/`, `infrastructure/`,
`api/` e uma `XFactory` registrada no `Container`.

## 5. Execução — tudo em containers Docker

Nunca no host. Serviços: `postgres`, `api`, `frontend`.

```bash
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api ruff check .
docker compose exec api pytest
docker compose exec frontend npm run lint
docker compose exec frontend npm run typecheck
docker compose exec frontend npm test
```

**PostgreSQL real nos testes.** SQLite não substitui: o projeto depende de `CITEXT`,
`tstzrange` e restrições `EXCLUDE`. A suíte usa o banco isolado
`tattoo_studio_test`, provisionado pelo `DatabaseProvisioner`.

**Armadilha conhecida:** não rodar `npm run build` com o `npm run dev` ativo no
mesmo container. Ambos usam `.next`/`dist` e o dev server passa a servir conteúdo
obsoleto. Recuperação: `docker compose restart frontend`.

## 6. Git

- **Uma branch por sprint:** `feat/m3-agenda`, `feat/m4-orcamentos`. Acumular
  várias sprints numa branch torna o PR grande demais para revisão real.
- Commit descreve **o porquê**, não só o quê. Decisão revista durante a
  implementação entra na mensagem.
- Nunca commitar `.env`.
- O push por SSH falha nesta máquina (chave não registrada); usar a URL HTTPS.

## 7. Documentação é entregável, não etapa final

Toda alteração atualiza a documentação na mesma entrega, para que uma sessão nova
entenda o projeto **sem ler código**.

| Mudou | Atualize |
|---|---|
| Progresso de sprint | `09_ROADMAP_IMPLEMENTACAO.md` e `00_CONTEXTO_E_CONTINUIDADE.md` |
| Decisão de arquitetura | `08_DECISOES_ARQUITETURA.md` |
| Tabela ou campo | `05_MODELO_DADOS.md` |
| Endpoint | `06_ESTRUTURA_PROJETO.md` |
| Cobertura de teste | `07_PLANO_TESTES.md` |
| Regra de negócio | `01_REGRAS_DE_NEGOCIO.md` |

**Cuidado com status congelado.** Cabeçalhos do tipo "nenhum código foi criado"
precisam ser revisados quando deixam de ser verdade — já aconteceu de cinco
documentos afirmarem que o projeto não tinha saído do papel.

## 8. Gate por tarefa

1. Regra e critério de aceite identificados.
2. Contrato e autorização definidos.
3. Migração revisada, quando aplicável.
4. Implementação pequena e coesa.
5. Testes proporcionais ao risco, incluindo o cenário negativo.
6. Ruff, tipos e testes aprovados **dentro do container**.
7. Documentação e ADR atualizados.
8. Evidência registrada no roadmap.
