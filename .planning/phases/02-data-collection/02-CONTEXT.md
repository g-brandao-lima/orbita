# Phase 2: Data Collection - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning
**Source:** Requirements + project constraints (user skipped discussion — all implementation choices at Claude's Discretion)

<domain>
## Phase Boundary

Sistema faz polling autônomo da Amadeus API a cada 6 horas para cada grupo ativo, encontra as 5 combinações mais baratas dentro do período configurado, captura booking classes + classificação de preço histórico, e persiste tudo como snapshots no banco SQLite. Falhas de API não devem crashar o scheduler.

</domain>

<decisions>
## Implementation Decisions

### Locked (from requirements and project constraints)

- Polling interval: exatamente 6 horas (COLL-01)
- Por ciclo: as 5 combinações mais baratas de (origem × destino × data_ida × data_volta) dentro do período do grupo (COLL-02)
- Para cada combinação: capturar booking classes com contagem via Amadeus Flight Availabilities Search (COLL-03)
- Para cada combinação: capturar classificação histórica LOW/MEDIUM/HIGH via Amadeus Flight Price Analysis (COLL-04)
- Persistência: snapshots com timestamp no banco SQLite (COLL-05)
- Tratamento de falhas: gracioso — sem crashar o scheduler; próximo ciclo executa normalmente (COLL-06)
- Scheduler: APScheduler embedded (definido em PROJECT.md — sem Celery)
- Banco: SQLite via SQLAlchemy sync (herdado da Phase 1)
- Budget de API: ~2000 calls/mês no free tier Amadeus; máximo ~4 grupos ativos com 2 pollings/dia
- `app/config.py` deve ser atualizado: substituir `telegram_bot_token` e `telegram_chat_id` por `gmail_sender`, `gmail_app_password`, `gmail_recipient` (alinhamento com decisão de Phase 1 de usar Gmail)

### Claude's Discretion

- Endpoints Amadeus a usar e sequência exata (ex: Flight Cheapest Date Search → Flight Offers Search → Availabilities → Price Analysis)
- Esquema do modelo de dados para snapshots (tabela flat com JSON, tabelas relacionais, ou híbrido)
- Estratégia de retry em caso de timeout ou 429 (skip do ciclo com log, backoff, etc.)
- Comportamento quando credenciais Amadeus ausentes no .env (iniciar sem fazer calls, ou logar aviso)
- Estrutura dos serviços: onde colocar lógica de Amadeus client vs lógica de scheduler vs lógica de persistência

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 artifacts (foundation to build on)
- `app/models.py` — RouteGroup model com campos origins/destinations (JSON), travel_start/travel_end, is_active
- `app/config.py` — Settings via pydantic-settings; ADICIONAR gmail_sender/gmail_app_password/gmail_recipient, REMOVER telegram_*
- `app/database.py` — SQLAlchemy engine sync, SessionLocal, Base, get_db dependency
- `app/services/route_group_service.py` — padrão de service layer estabelecido na Phase 1
- `.env.example` — template de variáveis de ambiente (já tem AMADEUS_CLIENT_ID, AMADEUS_CLIENT_SECRET, Gmail vars)

### Project constraints
- `.planning/REQUIREMENTS.md` — COLL-01 a COLL-06 (requisitos desta phase)
- `.planning/PROJECT.md` — constraints de budget Amadeus, decisões arquiteturais

</canonical_refs>

<specifics>
## Specific Implementation Notes

- Budget Amadeus: com 4 grupos ativos e 4 ciclos/dia, cada ciclo pode usar no máximo ~12-13 calls (2000 / 4 grupos / 4 ciclos / 10 dias de margem ≈ 12 calls/ciclo/grupo). O planner deve dimensionar os endpoints respeitando esse budget.
- Amadeus capeia contagem de assentos em 9 — isso é normal, não é erro de implementação.
- A Phase 3 (Signal Detection) vai comparar snapshots consecutivos — o esquema de dados deve facilitar essa query (buscar snapshots anteriores por rota+datas).

</specifics>

<deferred>
## Deferred Ideas

Nenhum item discutido para diferir — usuário optou por ir direto ao planejamento.

</deferred>

---

*Phase: 02-data-collection*
*Context gathered: 2026-03-25 (express — sem discussão interativa)*
