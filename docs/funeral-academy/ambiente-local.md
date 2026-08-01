# Ambiente local

Como subir a Funeral Academy na sua máquina, e as armadilhas que já custaram tempo.

## Caminho normal

Requisitos: **Node.js ≥ 18** e **Docker** rodando.

```bash
npx learnhouse dev
```

O comando sobe PostgreSQL (com `pgvector`) e Redis em containers, instala as dependências de
`apps/web`, `apps/collab` (bun) e `apps/api` (uv), e inicia os três serviços com hot reload.

| Serviço | URL |
|---|---|
| Web | http://localhost:3000 |
| API | http://localhost:1338 |
| Collab (WebSocket) | ws://localhost:4000 |

Na primeira execução ele pergunta o e-mail e a senha do administrador. Para rodar sem prompt
(CI, script, terminal sem TTY):

```bash
npx learnhouse dev --admin-email admin@funeralacademy.com.br --admin-password 'SuaSenhaAqui'
```

Se faltarem variáveis de ambiente, o CLI lista o que falta e oferece escrever os defaults de
desenvolvimento. Aceitar é o caminho normal — ele gera o segredo JWT e mantém API e Collab
com a mesma chave.

## Armadilhas

### O e-mail do admin não pode usar TLD reservado

`admin@empresa.local` é **rejeitado** — `.local` é reservado e a validação do Pydantic recusa.
O problema não é a recusa, é *quando* ela acontece: a organização já foi criada, e a API só
falha em seguida, ao criar o usuário. O resultado é um banco meio semeado, com organização e
**nenhum usuário**.

Use um domínio válido: `admin@funeralacademy.com.br`, `admin@school.dev`.

### Reiniciar não conserta um seed pela metade

O `auto_install` decide se precisa instalar checando apenas **se existe alguma organização**.
Com o banco meio semeado a organização existe, então ele pula o seed inteiro — e você fica sem
usuário para sempre, por mais que reinicie.

A saída é recriar o banco:

```bash
docker exec -it learnhouse-db-dev psql -U learnhouse -d postgres \
  -c "DROP DATABASE learnhouse;" -c "CREATE DATABASE learnhouse OWNER learnhouse;"
```

E subir de novo com as credenciais corretas.

### Recriar o banco exige limpar o Redis

A API guarda o `instance_info` em cache no Redis, incluindo o `default_org_slug`. Se você
recriar o Postgres sem limpar o Redis, o front recebe o slug antigo e **toda página responde
404** — sintoma que não parece cache nenhum.

```bash
docker exec -it learnhouse-redis-dev redis-cli FLUSHALL
```

Depois reinicie o servidor Next: o `proxy.ts` também mantém um cache em memória do
`instance_info`.

### Rodando os serviços na mão

Se preferir controlar cada processo (o CLI exige TTY para os prompts):

```bash
# infraestrutura via docker compose gerado pelo CLI
docker compose -f .learnhouse/docker-compose.dev.yml -p learnhouse-dev up -d

cd apps/api    && uv sync && uv run python app.py          # :1338
cd apps/web    && bun install && bunx next dev --turbopack # :3000
cd apps/collab && bun install && bunx tsx watch src/index.ts # :4000
```

A API exige `LEARNHOUSE_INITIAL_ADMIN_PASSWORD` na primeira subida, senão a instalação aborta:

```bash
LEARNHOUSE_INITIAL_ADMIN_EMAIL=admin@funeralacademy.com.br \
LEARNHOUSE_INITIAL_ADMIN_PASSWORD='SuaSenhaAqui' \
uv run python app.py
```

### A versão do Python é travada

`apps/api/pyproject.toml` fixa `requires-python = ">=3.14.6,<3.14.7"`. Um `uv` antigo não
conhece essa versão e falha com `No download found for request`. Atualize o `uv` antes:

```bash
uv self update    # ou: pip install -U uv
uv python install 3.14.6
```

## O que o seed cria

Com os defaults deste fork, uma instalação limpa produz:

| Item | Valor |
|---|---|
| Organização | `Funeral Academy` (slug `funeral-academy`) |
| Idioma padrão | `pt` |
| Watermark | desativada |
| Usuário | `admin`, com o e-mail e a senha informados |

Confira depois de instalar:

```bash
docker exec -it learnhouse-db-dev psql -U learnhouse -d learnhouse \
  -c "SELECT name, slug FROM organization;" \
  -c "SELECT config::jsonb->'customization'->'general' FROM organizationconfig;"
```
