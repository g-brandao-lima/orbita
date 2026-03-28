# Phase 11: Google OAuth - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Adicionar autenticacao via Google OAuth ao Flight Monitor. Usuario pode fazer login com Google, navegar pelo dashboard com sessao persistente, ver seu nome e foto no header, e fazer logout de qualquer pagina. Rotas protegidas redirecionam para landing page.

</domain>

<decisions>
## Implementation Decisions

### Fluxo de sessao
- **D-01:** Apos login com Google, usuario e sempre redirecionado para /dashboard (pagina principal com grupos)
- **D-02:** Sessao nao expira. Dura ate o usuario fazer logout explicitamente. Cookie httpOnly assinado com user_id.
- **D-03:** Authlib para OAuth + SessionMiddleware (Starlette) com signed cookies. Nao usar JWT.

### Header autenticado
- **D-04:** Claude tem discricionariedade sobre o layout do avatar/nome/logout no header. Deve respeitar o design existente (glassmorphism, Inter font, paleta dark mode #0b0e14).

### Protecao de rotas
- **D-05:** Middleware global protege todas as rotas por padrao. Excecoes explicitas: / (landing), /auth/* (login/callback/logout), HEAD / (UptimeRobot)
- **D-06:** Visitante nao logado que tenta acessar rota protegida e redirecionado para / com flash message "Faca login para acessar"

### Erro e edge cases
- **D-07:** Falha no login Google (cancelamento, erro de rede) redireciona para / com flash message descritiva ("Login cancelado" ou "Erro ao conectar com Google")
- **D-08:** Conta Google sem foto de perfil exibe circulo com iniciais do nome (ex: "GB") em cor accent do design system

### Claude's Discretion
- Layout especifico do avatar/nome/dropdown no header (manter coerencia com design existente)
- Modelo User (campos, tabela) — pesquisa indica: id, google_id, email, name, picture, created_at
- Escolha entre SessionMiddleware (Starlette) ou cookie manual (itsdangerous)
- Estrutura de arquivos para auth (routes, middleware, services)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Codebase atual
- `app/config.py` — Settings via pydantic-settings, precisa adicionar GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET
- `app/templates/base.html` — Header com glassmorphism, div.header-actions e ponto de insercao para avatar/logout
- `app/database.py` — Engine com connect_args condicional (Phase 10), Base declarativa
- `app/models.py` — 4 modelos existentes (RouteGroup, FlightSnapshot, DetectedSignal, BookingClassSnapshot)
- `main.py` — Lifespan com scheduler, exception handlers, router includes
- `app/routes/dashboard.py` — Todas as rotas HTML (index, detail, create, edit, toggle, poll)

### Research do milestone
- `.planning/research/STACK.md` — Authlib 1.6.x, recomendacoes de integracao
- `.planning/research/ARCHITECTURE.md` — Padrao session-based auth para Jinja2 SSR
- `.planning/research/PITFALLS.md` — 188 testes quebram ao adicionar auth middleware (criar fixtures antes)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `base.html` header: div.header-actions ja existe como ponto de insercao para avatar/logout
- `error.html` template: pode ser reutilizado para erros de auth
- Flash messages: ja implementadas (Phase 6) — reusavel para mensagens de auth

### Established Patterns
- pydantic-settings: todas as configs vem de .env via Settings class
- Routes: dashboard.py (HTML), route_groups.py (API JSON), alerts.py (silence)
- Templates: Jinja2 com heranca de base.html
- Dark mode: #0b0e14 fundo, #e2e8f0 texto, Inter font

### Integration Points
- `main.py`: adicionar SessionMiddleware antes dos routers
- `app/routes/`: novo arquivo auth.py para /auth/login, /auth/callback, /auth/logout
- `app/models.py`: novo modelo User
- `base.html`: condicional no header (logado vs nao logado)
- `conftest.py`: fixtures de auth para testes (usuario mock)

</code_context>

<specifics>
## Specific Ideas

- Iniciais no avatar quando nao tem foto (ex: "GB" em circulo accent)
- Flash messages para erros de auth (mesmo padrao das flash messages existentes)
- Middleware global com lista de rotas publicas (nao decorator por rota)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-google-oauth*
*Context gathered: 2026-03-28*
