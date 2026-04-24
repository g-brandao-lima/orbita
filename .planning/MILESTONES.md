# Milestones

## v2.3 Growth Features e Cache Centralizado (Shipped: 2026-04-24)

**Phases completed:** 14 phases, 33 plans, 58 tasks

**Key accomplishments:**

- 22 API-level TDD tests covering all Route Group requirements (ROUTE-01 through ROUTE-06) with StaticPool fix for reliable in-memory SQLite test isolation
- DRY refactor extracting get_group_or_404 helper, full quality checklist applied, 28/28 tests passing; human checkpoint verified — Phase 1 complete
- FlightSnapshot + BookingClassSnapshot SQLAlchemy models with save_flight_snapshot service and Gmail config replacing Telegram
- APScheduler-driven 6-hour polling cycle that orchestrates Amadeus data collection across all active route groups with per-group error isolation
- DetectedSignal model with 12 fields, ix_signal_dedup index, and 19 failing RED tests covering BALDE_FECHANDO, BALDE_REABERTO, PRECO_ABAIXO_HISTORICO, JANELA_OTIMA, and deduplication
- 4 signal detectors (BALDE_FECHANDO, BALDE_REABERTO, PRECO_ABAIXO_HISTORICO, JANELA_OTIMA) with 12h dedup and polling integration
- Refactored signal_service.py with _create_signal factory, SRP decomposition into _run_detectors/_deduplicate_and_persist, and human-verified 74/74 tests passing end-to-end
- One-liner:
- 1. [Rule 3 - Blocking] Import verify_silence_token in stub for mock patch target
- polling_service now dispatches Gmail alerts per detected signal via should_alert + compose_alert_email + send_email with SMTP-failure isolation; CLAUDE.md 4.1 checklist applied with no code changes needed
- SQLAlchemy aggregation queries for dashboard with group summaries, price history charts, and BRL formatting via TDD (11 tests)
- Dashboard index with group cards showing BRL prices and urgency badges, detail page with Chart.js price history graph, responsive layout with Jinja2 template inheritance
- Create/edit route group forms with IATA validation, PRG pattern, and active/inactive toggle respecting 10-group limit
- Funcao is_duplicate_snapshot com query temporal (1h window) integrada ao polling para evitar snapshots duplicados no mesmo ciclo de coleta
- Flash messages verdes com fade-out CSS de 5s em todos os redirects de CRUD + pagina de erro amigavel com exception handler global
- compose_consolidated_email via TDD: 1 email por grupo com rota mais barata em destaque, tabela top 3 datas/precos, resumo de outras rotas e datas dd/mm/aaaa
- Refatoracao do polling_service para acumular sinais por grupo e enviar 1 email consolidado via compose_consolidated_email ao final de _poll_group
- Dashboard with summary bar (active groups, cheapest price, next polling), colored cards by price classification, empty state with airplane icon, and dates in dd/mm/aaaa
- Detail page travel dates converted to dd/mm/aaaa format via format_date_br, completing UI-05 across all dashboard pages
- Dashboard UI-SPEC applied: monospace prices 28px, semantic color palette (#22c55e/#f59e0b/#ef4444), card hover shadows, summary bar, CTA min-height 40px
- Sky blue #0ea5e9 applied to detail chart/links, green #22c55e to create/edit submit buttons, all old colors eliminated
- database.py condicional por dialeto (SQLite/PostgreSQL) com Alembic baseline migration das 4 tabelas e pool_pre_ping para Neon.tech
- render.yaml com alembic upgrade head no build e DATABASE_URL como env var secreta para PostgreSQL via Neon.tech
- User model com google_id/email, Authlib instalado, Alembic migration para tabela users, e fixtures test_user/authenticated_client prontas para uso
- Fluxo OAuth completo via Authlib com SessionMiddleware (1 ano), AuthMiddleware global, e 10 testes cobrindo login/callback/logout/middleware
- Conditional header with avatar/name/logout for logged users and "Entrar com Google" for anonymous, plus render.yaml OAuth env vars with proxy trust
- user_id FK on route_groups with full query filtering, ownership checks on all routes, and 6 isolation tests
- Email alerts sent to group owner's Google email via recipient_email param, with Meus Alertas page showing per-user signal history
- Global SerpAPI usage counter with monthly reset, dashboard indicator, and polling auto-stop at 250 searches/month
- Landing page publica com hero, 3 passos "Como funciona", 3 cards diferenciais com SVG e CTA Google OAuth, rota / condicional por estado de login
- Dashboard queries dialect-agnostic (sem func.strftime) e APP_BASE_URL declarado no render.yaml para links de silenciar alerta

---

## v2.1 Clareza de Preco e Robustez (Shipped: 2026-04-20)

**Phases completed:** 11 phases (15, 15.1, 16, 17, 17.1, 19, 20, 21, 21.5, 22, 23). Phase 18 (JWT Sessions) deferida como over-engineering para 200 users em 1 worker.

**Key accomplishments:**

- Fix critico de vazamento de dados na API REST /api/v1/route-groups/ (Phase 15.1)
- Rate limiting em 6 endpoints com limites por custo (login, escrita, polling, autocomplete)
- CI pipeline GitHub Actions rodando pytest em push/PR
- passengers propagado corretamente para SerpAPI e fast-flights (antes hardcoded 1)
- Rotulo "por pessoa, ida e volta" em todos os contextos + total para multi-pax
- Coluna source em FlightSnapshot + badge visual unificado Google Flights
- Cache in-memory 30min reduzindo chamadas duplicadas a API externas
- BookingClassSnapshot e amadeus_client removidos (legacy v1.0, -400 linhas)
- Sentry integrado em producao com LGPD-aware scrubbing e user context
- Contexto historico no email "X% abaixo da media dos ultimos 90 dias"
- Script analyze_signals.py para validacao empirica de sinais
- 258 testes passando, zero regressoes

---

## v2.0 Multi-usuario (Shipped: 2026-03-30)

**Phases completed:** 5 phases, 10 plans, 20 tasks

**Key accomplishments:**

- database.py condicional por dialeto (SQLite/PostgreSQL) com Alembic baseline migration das 4 tabelas e pool_pre_ping para Neon.tech
- render.yaml com alembic upgrade head no build e DATABASE_URL como env var secreta para PostgreSQL via Neon.tech
- User model com google_id/email, Authlib instalado, Alembic migration para tabela users, e fixtures test_user/authenticated_client prontas para uso
- Fluxo OAuth completo via Authlib com SessionMiddleware (1 ano), AuthMiddleware global, e 10 testes cobrindo login/callback/logout/middleware
- Conditional header with avatar/name/logout for logged users and "Entrar com Google" for anonymous, plus render.yaml OAuth env vars with proxy trust
- user_id FK on route_groups with full query filtering, ownership checks on all routes, and 6 isolation tests
- Email alerts sent to group owner's Google email via recipient_email param, with Meus Alertas page showing per-user signal history
- Global SerpAPI usage counter with monthly reset, dashboard indicator, and polling auto-stop at 250 searches/month
- Landing page publica com hero, 3 passos "Como funciona", 3 cards diferenciais com SVG e CTA Google OAuth, rota / condicional por estado de login
- Dashboard queries dialect-agnostic (sem func.strftime) e APP_BASE_URL declarado no render.yaml para links de silenciar alerta

---
