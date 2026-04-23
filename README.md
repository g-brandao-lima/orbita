# Órbita

> O radar das passagens aéreas. Compre passagem no momento certo.

A Órbita monitora rotas que você cadastra e te avisa por email quando o preço está historicamente baixo. Publico-alvo: viajantes BR que sabem usar Google Flights mas cansam de ficar checando toda semana.

**Produção:** https://orbita-flights.fly.dev
**Repositório:** https://github.com/g-brandao-lima/orbita

## O que faz

- **Monitoramento diário** de rotas via Aviasales Data API (cache bulk 4×/dia) + SerpAPI (refresh on-demand)
- **Histórico 180 dias** por rota: média, mediana, melhor preço registrado
- **Detecção de sinais** (preço abaixo da média, janela ótima) com alerta por email consolidado
- **Price Prediction** determinística: recomenda "Compre até DD/MM" com base em histórico (sem ML)
- **Multi-trecho**: roteiro encadeado (ex: BR → Itália → Espanha → BR) em um único grupo-pai, com sinal de compra aplicado sobre o preço total do encadeamento
- **Páginas públicas SEO** `/rotas/{ORIG}-{DEST}` indexadas no Google com dados históricos
- **Landing hero carousel**: card dinâmico que rotaciona pelas rotas mais recentes do cache, com auto-play, setas e pause no hover
- **Affiliate monetizado** via Aviasales (marker 714304) — usuário compra, Órbita recebe comissão
- **Tracking próprio** de cliques em "Comprar agora" no banco local
- **Admin panel** `/admin/stats` com quota SerpAPI, cache hit rate Travelpayouts, cliques afiliados

## Stack

| Camada | Tecnologia |
|---|---|
| Runtime | Python 3.11 |
| Web | FastAPI 0.115 + gunicorn + uvicorn[standard] (uvloop) |
| DB produção | PostgreSQL (Neon.tech free tier) |
| DB testes | SQLite in-memory |
| Migrations | Alembic 1.18 |
| ORM | SQLAlchemy 2.0 |
| Auth | Google OAuth via Authlib |
| Templates | Jinja2 SSR (paleta Órbita indigo-cyan) |
| JS | Vanilla puro (sem framework) — wizard multi-leg, hero carousel |
| Gráficos | Chart.js (CDN, só no detalhe de grupo) |
| Fontes | Space Grotesk + JetBrains Mono (Google Fonts) |
| Scheduler | APScheduler BackgroundScheduler (cron in-process) |
| Email | Gmail SMTP SSL 465 |
| Imagens | Pillow (OG image dinâmica por rota) |
| Rate limit | slowapi |
| Observabilidade | Sentry |
| Hospedagem | Fly.io (máquina always-on GRU, ~US$4/mês) |
| Fonte de dados primária | Travelpayouts (Aviasales Data API) |
| Fonte secundária | SerpAPI (refresh sob demanda) |

## Arquitetura em 1 diagrama

```
┌────────────────────────────┐
│ Cron 4×/dia (APScheduler)  │──► Travelpayouts Data API (free)
│ 00:30 06:30 12:30 18:30    │    fetch_calendar das TOP 28 rotas BR
└────────────────────────────┘
              │
              ▼
┌────────────────────────────┐
│ route_cache (Postgres)     │
│ TTL 6h, key=(O,D,dates)    │
└────────────────────────────┘
              │
              ▼ lookup
┌────────────────────────────┐          ┌──────────────────────────┐
│ search_flights_ex()        │◄─────────┤ multi_leg_service        │
│  cache miss ─► SerpAPI     │          │ N trechos cartesianos    │
└────────────────────────────┘          │ escolhe combo mais barato│
              │                         └──────────────────────────┘
              ▼ servido do banco                      │
┌────────────────────────────────────────────────────────────────┐
│ Dashboard logado │ /rotas/X-Y SEO │ /sitemap.xml │ Hero carousel│
└────────────────────────────────────────────────────────────────┘
              │
              ▼ user clica "Comprar agora"
┌────────────────────────────┐
│ GET /comprar/O-D?dep&ret   │
│ loga AffiliateClick + 302  │
└────────────────────────────┘
              │
              ▼
┌────────────────────────────┐
│ aviasales.com?marker=714304│── comissão ──► Órbita
└────────────────────────────┘
```

## Setup local

```bash
git clone https://github.com/g-brandao-lima/orbita.git
cd orbita
python -m venv .venv
.venv/Scripts/activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# Copiar .env.example → .env e preencher
# Secrets necessários: DATABASE_URL, SERPAPI_API_KEY, TRAVELPAYOUTS_TOKEN,
# TRAVELPAYOUTS_MARKER, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
# GMAIL_*, SESSION_SECRET_KEY, APP_BASE_URL, ADMIN_EMAIL, SENTRY_DSN

# Schema (SQLite local cria no primeiro startup)
alembic upgrade head

# Rodar
python main.py
# Abre em http://localhost:8000
```

## Testes

```bash
.venv/Scripts/python.exe -m pytest -q
# 419 testes, ~18s
```

Cobertura inclui: model layer, services (search, signal, alert, prediction, multi-leg, dashboard), routes (auth, dashboard, public, admin), templates (renderização via TestClient), integração polling + signal + email.

## Deploy (Fly.io)

```bash
fly deploy
# build + push + rolling restart. ~3min.
```

Secrets gerenciados via `fly secrets set KEY=VALUE`. Cron APScheduler **exige always-on**: `fly.toml` tem `auto_stop_machines=off` e `min_machines_running=1`.

**NÃO escalar horizontalmente** (`fly scale count N` com N>1) — APScheduler in-process duplica cron em cada máquina, gera emails em dobro.

## Estrutura

```
app/
├── auth/            # OAuth Google, middleware, dependencies
├── routes/          # FastAPI routers (public, dashboard, admin, route_groups, alerts)
├── services/        # Lógica de negócio:
│   ├── flight_search.py            # cache-first search (route_cache → SerpAPI)
│   ├── multi_leg_service.py        # N trechos cartesianos + combo mais barato
│   ├── polling_service.py          # cron de coleta de snapshots
│   ├── signal_service.py           # detecção de sinais (abaixo média, janela ótima)
│   ├── alert_service.py            # email consolidado (roundtrip + multi-leg)
│   ├── prediction_service.py       # recomendação "Compre até DD/MM" determinística
│   ├── dashboard_service.py        # montagem de cards (roundtrip + multi)
│   ├── route_cache.py              # TTL 6h, key composta
│   ├── travelpayouts_client.py     # Aviasales Data API
│   ├── public_route_service.py     # SEO público + hero carousel
│   └── affiliate_tracking.py       # logging de cliques
├── templates/       # Jinja2: landing, dashboard/, public/route, admin/stats
├── static/js/       # Vanilla: multi-leg builder, hero-carousel
├── models.py        # SQLAlchemy: User, RouteGroup, RouteGroupLeg, FlightSnapshot,
│                    # RouteCache, Alert, AffiliateClick, etc.
├── schemas.py       # Pydantic: RouteGroupCreate, RouteGroupMultiCreate com validate_chain
├── database.py      # engine + SessionLocal + get_db
├── config.py        # pydantic-settings (.env)
├── scheduler.py     # APScheduler jobs
└── observability.py # Sentry init
alembic/versions/    # Migrations sequenciais
tests/               # pytest, SQLite in-memory, 419 testes
.planning/           # Docs internos do workflow GSD
    milestones/      # Arquivo histórico de milestones (v1.0, v1.1, v1.2, v2.0, v2.1, v2.2)
    phases/          # Phases ativas do milestone corrente
    quick/           # Tarefas quick avulsas
    archive/         # Relatórios antigos (Flight Monitor era)
```

## Histórico do projeto

- **Fev-Mar/2026:** v1 MVP "Flight Monitor" monolito Amadeus+SQLite (single-user)
- **Mar/2026:** v2.0 multi-user OAuth + PostgreSQL + landing
- **Abr/2026:** v2.1-v2.2 clareza de preço + UX polish
- **Abr/2026:** v2.3 cache Travelpayouts + SEO público + affiliate + **rebrand Órbita**
- **Abr/2026:** migração Render → Fly.io
- **Abr/2026:** Price Prediction Engine (Phase 34) — recomendação "Compre até DD/MM" com backtest
- **Abr/2026:** Multi-Leg Trip Builder (Phase 36) — roteiros encadeados, sinal sobre total
- **Abr/2026:** Hero carousel na landing — prova de vida rotacionando rotas reais

Ver `.planning/milestones/` para arquivo completo de cada versão e `.planning/archive/` para relatórios históricos da era Flight Monitor.

## Roadmap

v2.3 encerrando. Próximo milestone em planejamento. Ideias candidatas:

- Domínio próprio (`orbita.com.br` ou similar)
- Cloudflare CDN na frente do Fly
- Onboarding wizard (Phase 35, condicional a tração orgânica)
- Filtro de hero carousel por rotas com sinal ativo no momento

## Licença

Uso pessoal. Sem licença open-source.
