# Milestones

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
