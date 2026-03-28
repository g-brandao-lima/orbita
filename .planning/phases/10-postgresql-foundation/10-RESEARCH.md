# Phase 10: PostgreSQL Foundation - Research

**Researched:** 2026-03-28
**Domain:** Database migration (SQLite to PostgreSQL) + Alembic schema management
**Confidence:** HIGH

## Summary

Esta fase migra o banco de dados de producao do SQLite efemero (que perde dados a cada redeploy no Render) para PostgreSQL persistente no Neon.tech, e introduz Alembic como gerenciador de migrations. O escopo e estritamente infraestrutural: nenhum modelo novo, nenhuma feature nova, nenhuma mudanca de comportamento visivel ao usuario.

O trabalho principal consiste em: (1) tornar `database.py` e `config.py` agnosticos ao dialeto, com `connect_args` condicional; (2) inicializar o Alembic e gerar a migration baseline a partir dos models existentes; (3) atualizar `render.yaml` para usar a connection string do Neon.tech e rodar `alembic upgrade head` no build; (4) garantir que todos os 188 testes continuam passando com SQLite in-memory sem nenhuma alteracao.

**Primary recommendation:** Alterar `database.py` para detectar o dialeto via prefixo da URL, inicializar Alembic com `env.py` configurado para ler `DATABASE_URL` do ambiente, e mover o build command do Render para incluir `alembic upgrade head` antes do gunicorn.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DB-01 | Sistema usa PostgreSQL (Neon.tech) como banco de dados em producao | Stack: psycopg[binary] 3.3.3 como driver, Neon.tech free tier como hosting. Configuracao em database.py com connect_args condicional e pool_pre_ping=True |
| DB-02 | Alembic gerencia todas as migrations de schema | Alembic 1.18.4 com env.py lendo DATABASE_URL do ambiente. Migration baseline gerada via --autogenerate a partir dos 4 models existentes |
| DB-03 | Testes continuam rodando com SQLite in-memory (sem dependencia de PostgreSQL) | conftest.py existente ja usa SQLite in-memory com StaticPool. Nenhuma alteracao necessaria nos testes. connect_args condicional em database.py garante que check_same_thread so se aplica ao SQLite |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **SDD + TDD obrigatorio:** Spec antes de codigo, testes antes de implementacao, ciclo Red-Green-Refactor
- **YAGNI estrito:** Nao adicionar nada que nao foi explicitamente pedido
- **Sem JS framework no frontend:** Jinja2 + vanilla JS
- **Confirmar spec antes de implementar:** Claude deve apresentar spec e aguardar aprovacao
- **Testes FIRST:** Fast, Independent, Repeatable, Self-validating, Timely
- **Complexidade ciclomatica max 5 por funcao**
- **Auto-allow:** Leitura de arquivos, edicao/criacao, rodar testes, instalar pacotes no venv, git de leitura, bash exploratorio, web research, rodar servidor local

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| psycopg[binary] | 3.3.3 | Driver PostgreSQL para SQLAlchemy | Sucessor oficial do psycopg2. Dialeto dedicado `postgresql+psycopg` no SQLAlchemy 2.0+. O extra `[binary]` inclui extensoes C compiladas, evitando necessidade de build tools no Render |
| Alembic | 1.18.4 | Gerenciamento de migrations de schema | Unica ferramenta production-grade para migrations com SQLAlchemy. Autogenerate a partir dos models, versionamento, upgrade/downgrade |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy | 2.0.40 (existente) | ORM e engine de conexao | Ja instalado. Suporta dialeto psycopg3 nativamente via `postgresql+psycopg` |
| pydantic-settings | 2.9.1 (existente) | Leitura de config do ambiente | Ja instalado. Usado para ler DATABASE_URL do .env e das env vars do Render |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| psycopg[binary] 3.x | psycopg2-binary | psycopg2 esta em modo de manutencao. psycopg3 e o driver ativamente desenvolvido com dialeto dedicado no SQLAlchemy 2.0 |
| Neon.tech | Render PostgreSQL | Render free tier EXPIRA em 30 dias e deleta dados em 44 dias. Inaceitavel para dados persistentes. Neon.tech nao tem expiracao |
| Alembic | Base.metadata.create_all() | create_all() nao consegue alterar tabelas existentes. Phases futuras (11, 12) precisam adicionar User e user_id. Alembic e obrigatorio |

**Installation:**
```bash
pip install "psycopg[binary]==3.3.3"
pip install alembic==1.18.4
```

**Version verification:**
- alembic 1.18.4: verificado via `pip index versions alembic` (latest, 2026-03-28)
- psycopg 3.3.3: verificado via `pip index versions psycopg` (latest, 2026-03-28)

## Architecture Patterns

### Recommended Project Structure (changes only)

```
flight-monitor/
├── alembic.ini                # NEW: Alembic config (sqlalchemy.url vazio, lido do env)
├── alembic/                   # NEW: migration scripts
│   ├── env.py                 # Importa Base.metadata, le DATABASE_URL do ambiente
│   ├── script.py.mako         # Template padrao gerado pelo alembic init
│   └── versions/
│       └── 001_baseline.py    # Migration baseline dos 4 models existentes
├── app/
│   ├── config.py              # MODIFIED: database_url default muda para suportar override
│   └── database.py            # MODIFIED: connect_args condicional + pool_pre_ping
├── main.py                    # MODIFIED: remove Base.metadata.create_all()
├── render.yaml                # MODIFIED: buildCommand inclui alembic upgrade head
└── requirements.txt           # MODIFIED: adiciona psycopg[binary] e alembic
```

### Pattern 1: Conditional connect_args by Dialect

**What:** Aplicar `check_same_thread=False` somente quando o banco e SQLite. Adicionar `pool_pre_ping=True` e `pool_recycle=300` somente quando o banco e PostgreSQL.

**When to use:** Qualquer projeto que suporte multiplos dialetos (SQLite para testes/dev, PostgreSQL para producao).

**Example:**
```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

connect_args = {}
engine_kwargs = {}

if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Confidence:** HIGH. Padrao bem estabelecido documentado em multiplas fontes oficiais.

### Pattern 2: Alembic env.py with Environment Variable

**What:** Configurar `alembic/env.py` para ler DATABASE_URL do ambiente em vez de hardcodar no `alembic.ini`. Isso permite que o mesmo Alembic funcione em dev (SQLite) e producao (PostgreSQL).

**When to use:** Sempre. Nunca hardcodar credentials em alembic.ini.

**Example:**
```python
# alembic/env.py (trecho relevante)
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Importar Base para que target_metadata tenha todos os models
from app.models import Base  # noqa: F401 (side effect: registra models)
from app.database import Base as DBBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = DBBase.metadata

def get_url():
    return os.getenv("DATABASE_URL", "sqlite:///./flight_monitor.db")

def run_migrations_offline():
    url = get_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    from sqlalchemy import create_engine
    url = get_url()
    connectable = create_engine(url)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Confidence:** HIGH. Padrao oficial do Alembic, confirmado pela documentacao do Neon.tech.

### Pattern 3: Render Build Command with Migration

**What:** Rodar `alembic upgrade head` no build command do Render, ANTES do gunicorn iniciar. Isso garante que o schema esta atualizado em cada deploy.

**When to use:** Sempre em deploys com Alembic. Nunca rodar migrations dentro do lifespan da aplicacao (race condition com multiplos workers).

**Example:**
```yaml
# render.yaml
services:
  - type: web
    name: flight-monitor
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt && alembic upgrade head
    startCommand: gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
    envVars:
      - key: DATABASE_URL
        sync: false   # Neon.tech connection string configurada no dashboard do Render
```

**Confidence:** HIGH.

### Anti-Patterns to Avoid

- **Rodar migrations no lifespan do FastAPI:** Race condition com multiplos workers Gunicorn. Migrations devem ser um passo separado no build.
- **Hardcodar connection string no alembic.ini:** Expoe credentials no git. Ler do ambiente.
- **Usar `create_all()` em producao junto com Alembic:** Conflito entre Alembic e create_all(). Remover create_all() do lifespan.
- **Esquecer `pool_pre_ping=True`:** Neon suspende compute apos 5 min de inatividade. Sem pre_ping, a primeira query apos suspensao falha com connection error.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Schema versioning | Sistema proprio de versoes de SQL | Alembic | Autogenerate, rollback, version tracking. Reinventar isso e garantia de bugs |
| Connection pooling | Pool manual de conexoes | SQLAlchemy built-in pool + Neon PgBouncer | SQLAlchemy ja gerencia pool. Neon adiciona PgBouncer no lado do servidor |
| Dialect detection | Parser manual de URL para decidir driver | Prefixo da URL (`sqlite://` vs `postgresql+psycopg://`) | SQLAlchemy ja faz roteamento por dialeto automaticamente |

## Common Pitfalls

### Pitfall 1: check_same_thread Crash no PostgreSQL

**What goes wrong:** `connect_args={"check_same_thread": False}` e SQLite-specific. Quando DATABASE_URL aponta para PostgreSQL, psycopg3 rejeita esse parametro e o app crasha no startup.
**Why it happens:** Copia direta do tutorial FastAPI sem considerar que o parametro e exclusivo do SQLite.
**How to avoid:** Condicional `if settings.database_url.startswith("sqlite")` antes de popular connect_args.
**Warning signs:** App falha ao iniciar com erro "invalid dsn" ou "unexpected keyword argument".

### Pitfall 2: JSON Column Mutation Tracking

**What goes wrong:** `RouteGroup.origins` e `RouteGroup.destinations` usam `mapped_column(JSON)`. Mutacoes in-place (ex: `group.origins.append("GRU")`) nao sao detectadas pelo SQLAlchemy e nao persistem.
**Why it happens:** SQLAlchemy JSON nao rastreia mutacoes internas por padrao. No SQLite isso passa despercebido porque os testes tendem a substituir listas inteiras.
**How to avoid:** Sempre atribuir listas novas: `group.origins = [*group.origins, "GRU"]`. Alternativamente, usar `MutableList.as_mutable(JSON)`.
**Warning signs:** Atualizacoes em origins/destinations "desaparecem" apos save.

### Pitfall 3: Neon Cold Start Timeout

**What goes wrong:** Neon free tier suspende compute apos 5 min de inatividade. Primeira query apos suspensao leva 500ms-2s. Se a aplicacao nao tem pre_ping, a conexao stale causa erro.
**Why it happens:** Modelo serverless do Neon. App foi desenhado para SQLite local que esta sempre disponivel.
**How to avoid:** Usar `pool_pre_ping=True` no engine. UptimeRobot ja pinga a cada 5 min, mantendo Neon aquecido na maioria do tempo.
**Warning signs:** `ConnectionError` ou `OperationalError` intermitentes, especialmente de madrugada.

### Pitfall 4: Migration Baseline Conflita com create_all()

**What goes wrong:** Se `Base.metadata.create_all()` continua no lifespan E Alembic gerencia migrations, ambos tentam criar as mesmas tabelas. Alembic perde tracking porque as tabelas ja existem.
**Why it happens:** Esquecimento de remover create_all() ao introduzir Alembic.
**How to avoid:** Remover `Base.metadata.create_all(bind=engine)` do lifespan no MESMO commit que introduz Alembic.
**Warning signs:** `alembic upgrade head` reporta "nothing to do" mesmo com migrations pendentes.

### Pitfall 5: Neon Pooled vs Direct Connection String

**What goes wrong:** Usar a connection string pooled (com `-pooler` no hostname) para rodar migrations. PgBouncer em modo transaction pode causar erros em DDL statements.
**Why it happens:** Neon fornece 2 connection strings. Desenvolvedores usam a pooled para tudo.
**How to avoid:** Usar connection string DIRETA para migrations (`alembic upgrade head`). Usar connection string POOLED para a aplicacao (runtime). Para simplificar nesta fase, usar a direta para ambos (1 worker Gunicorn, nao precisa de pooling).
**Warning signs:** Migrations falham com erros de prepared statements ou DDL.

## Code Examples

### database.py Completo (Apos Alteracao)

```python
# Source: Padrao estabelecido para dual-dialect SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

connect_args = {}
engine_kwargs = {}

if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### alembic.ini (Trecho Relevante)

```ini
# alembic.ini
[alembic]
script_location = alembic

# Deixar vazio! O env.py le do ambiente.
sqlalchemy.url =
```

### Neon.tech Connection String Format

```
# Direta (para migrations):
postgresql+psycopg://user:password@ep-xxx-yyy-123456.us-east-2.aws.neon.tech/dbname?sslmode=require

# Pooled (para runtime, futuro):
postgresql+psycopg://user:password@ep-xxx-yyy-123456-pooler.us-east-2.aws.neon.tech/dbname?sslmode=require
```

### main.py Lifespan (Apos Remocao de create_all)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Base.metadata.create_all(bind=engine)  # REMOVIDO - Alembic gerencia o schema
    from app.scheduler import init_scheduler, shutdown_scheduler
    init_scheduler()
    yield
    shutdown_scheduler()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| psycopg2 (maintenance mode) | psycopg 3.x (actively developed) | SQLAlchemy 2.0 (2023) | Dialeto dedicado `postgresql+psycopg`, melhor connection handling |
| create_all() em producao | Alembic migrations | Pratica padrao desde 2015+ | Possibilidade de alterar schema sem perder dados |
| SQLite em producao (Render) | PostgreSQL no Neon.tech | Neon free tier estavel desde 2024 | Dados persistem entre redeploys |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Sim | 3.13 local / 3.11.12 Render | Nenhum |
| SQLAlchemy | ORM | Sim | 2.0.40 | Nenhum |
| Alembic | Migrations | Sim (global) | 1.18.4 | Instalar no venv do projeto |
| psycopg[binary] | PostgreSQL driver | Nao | Nao instalado | Instalar via pip |
| Neon.tech account | PostgreSQL hosting | Nao verificado | Free tier | Usuario deve criar conta |
| Render env vars | DATABASE_URL em producao | Sim (plataforma) | N/A | Nenhum |

**Missing dependencies with no fallback:**
- psycopg[binary]: deve ser instalado via `pip install "psycopg[binary]==3.3.3"` e adicionado ao requirements.txt
- Neon.tech account: usuario deve criar conta e banco antes do deploy

**Missing dependencies with fallback:**
- Alembic: instalado globalmente (1.18.4) mas deve ser adicionado ao requirements.txt do projeto para o Render

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3.5 |
| Config file | Nenhum arquivo pytest.ini (usa defaults) |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DB-01 | database.py cria engine PostgreSQL quando URL comeca com postgresql | unit | `python -m pytest tests/test_database.py -x` | Sim (parcial, precisa novos testes) |
| DB-01 | database.py cria engine SQLite quando URL comeca com sqlite | unit | `python -m pytest tests/test_database.py -x` | Sim (parcial) |
| DB-02 | `alembic upgrade head` cria todas as tabelas a partir de banco vazio | integration | `python -m pytest tests/test_alembic.py -x` | Nao (Wave 0) |
| DB-02 | `alembic revision --autogenerate` detecta mudancas nos models | manual | Verificacao manual apos alterar model | N/A (manual) |
| DB-03 | Todos os 188+ testes existentes passam com SQLite in-memory | regression | `python -m pytest tests/ -v` | Sim (188 testes existentes) |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green + `alembic upgrade head` funcional

### Wave 0 Gaps

- [ ] `tests/test_alembic.py`: testes de que alembic upgrade head cria schema correto (covers DB-02)
- [ ] `tests/test_database.py`: adicionar testes para connect_args condicional (covers DB-01)

## Open Questions

1. **Neon.tech account creation**
   - What we know: Free tier sem expiracao, 0.5 GB storage, sem cartao de credito
   - What's unclear: Se o usuario ja possui conta no Neon.tech
   - Recommendation: Incluir passo de criacao de conta/banco como pre-requisito da fase. A connection string sera configurada como env var no Render

2. **Pooled vs Direct connection para runtime**
   - What we know: Neon recomenda pooled para apps e direta para migrations. PgBouncer suporta prepared statements via protocolo (max 1000)
   - What's unclear: Se com 1 worker Gunicorn o pooling faz diferenca pratica
   - Recommendation: Usar connection string DIRETA nesta fase (simplicidade). Trocar para pooled se problemas de conexao surgirem. Com 1 worker e UptimeRobot, a direta e suficiente

3. **Dados existentes no SQLite do Render**
   - What we know: O SQLite atual no Render e efemero (perdido a cada redeploy). Portanto NAO ha dados para migrar
   - What's unclear: Nada. A perda de dados a cada redeploy e exatamente o problema que esta fase resolve
   - Recommendation: Nenhuma migracao de dados necessaria. Alembic upgrade head cria schema limpo no Neon.tech

## Sources

### Primary (HIGH confidence)
- [Neon.tech SQLAlchemy guide](https://neon.com/docs/guides/sqlalchemy) - Configuracao pool_pre_ping, pool_recycle
- [Neon.tech Alembic migrations guide](https://neon.com/docs/guides/sqlalchemy-migrations) - env.py com DATABASE_URL do ambiente, usar conexao direta para migrations
- [Neon.tech connection pooling docs](https://neon.com/docs/connect/connection-pooling) - PgBouncer config, pooled vs direct, max_prepared_statements=1000
- [SQLAlchemy 2.1 PostgreSQL dialect docs](https://docs.sqlalchemy.org/en/21/dialects/postgresql.html) - Dialeto psycopg3, formato de URL
- [Alembic 1.18.4 tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) - Setup padrao
- PyPI registry (verified 2026-03-28): alembic 1.18.4, psycopg 3.3.3

### Secondary (MEDIUM confidence)
- Milestone research files (.planning/research/STACK.md, ARCHITECTURE.md, PITFALLS.md) - Pesquisa previa do milestone v2.0
- Codebase inspection: app/database.py, app/models.py, app/config.py, main.py, tests/conftest.py, render.yaml (verified 2026-03-28)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Versoes verificadas no PyPI, compatibilidade confirmada pela documentacao oficial
- Architecture: HIGH - Padroes bem estabelecidos (connect_args condicional, Alembic env.py com env var, build command com migration)
- Pitfalls: HIGH - Baseado em inspecao direta do codigo atual (check_same_thread hardcoded, create_all no lifespan, JSON columns nos models)

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stack estavel, sem mudancas rapidas esperadas)
