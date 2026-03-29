---
phase: 12-data-isolation
verified: 2026-03-28T00:00:00Z
status: passed
score: 11/11 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Verificar que o badge 'Buscas restantes' no dashboard exibe valores com cores corretas"
    expected: "Valor <= 50 aparece em amarelo (#f59e0b); valor <= 10 aparece em vermelho (#ef4444)"
    why_human: "Logica de cor inline no template Jinja2 nao pode ser validada por grep ou pytest sem renderizacao com valores especificos de api_remaining"
  - test: "Verificar que email de alerta chega na caixa do usuario correto em producao"
    expected: "Email enviado para o email do Google do dono do grupo, nao para gmail_recipient fixo"
    why_human: "SMTP real nao e executado em testes (send_email e mockado); requer envio real em staging"
---

# Phase 12: Data Isolation — Verification Report

**Phase Goal:** Cada usuario ve exclusivamente seus proprios dados, alertas vao para o email correto e o consumo de SerpAPI e visivel
**Verified:** 2026-03-28
**Status:** passed
**Re-verification:** No — verificacao inicial

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Usuario A nao consegue ver grupos do Usuario B em nenhuma rota | VERIFIED | `get_groups_with_summary` filtra por `user_id`; detalhe, edicao e toggle verificam `group.user_id != user.id` com 404; 4 testes automatizados passando |
| 2 | Criacao de grupo associa automaticamente ao usuario logado | VERIFIED | `create_group_form` passa `user_id=user.id if user else None` ao criar `RouteGroup`; teste `test_create_group_assigns_current_user_id` passa |
| 3 | Dashboard exibe apenas grupos do usuario logado | VERIFIED | `dashboard_index` passa `user_id=user.id` para `get_groups_with_summary` e `get_dashboard_summary`; teste `test_dashboard_index_shows_only_user_groups` passa |
| 4 | Detalhe, edicao e toggle de grupo rejeita acesso a grupos de outro usuario | VERIFIED | Verificacao `if user and group.user_id != user.id: raise HTTPException(404)` presente em `dashboard_detail`, `edit_group_page`, `edit_group_form` e `toggle_group`; 2 testes passando |
| 5 | Email de alerta e enviado para o email do Google do dono do grupo | VERIFIED | `compose_alert_email` e `compose_consolidated_email` aceitam `recipient_email` com fallback para `settings.gmail_recipient`; polling carrega `group.user` via joinedload e passa `group.user.email` |
| 6 | Polling service carrega user.email via relationship ao enviar email | VERIFIED | `run_polling_cycle` usa `joinedload(RouteGroup.user)`; `_poll_group` usa `recipient = group.user.email if group.user else settings.gmail_recipient` |
| 7 | Usuario pode acessar pagina Meus Alertas e ver apenas sinais dos seus grupos | VERIFIED | Rota `GET /alerts` existe em `dashboard.py` com join/filter `RouteGroup.user_id == user.id`; testes `test_alerts_page_returns_200` e `test_alerts_page_shows_only_user_signals` passando |
| 8 | Pagina Meus Alertas lista sinais com data, tipo, urgencia, rota e preco | VERIFIED | Template `alerts.html` exibe colunas Data, Tipo, Urgencia (badge colorido), Rota e Preco; teste `test_alerts_page_shows_signal_details` passa |
| 9 | Dashboard exibe indicador de buscas SerpAPI restantes no mes | VERIFIED | Summary bar em `index.html` mostra `api_remaining/api_quota` com cores semanticas; `get_dashboard_summary` retorna `api_usage`, `api_remaining`, `api_quota` |
| 10 | Cada chamada SerpAPI incrementa o contador global | VERIFIED | `_poll_group` chama `increment_usage(db)` apos cada `search_flights_with_insights` bem-sucedido |
| 11 | Contador reseta no primeiro dia de cada mes | VERIFIED | `get_current_year_month()` retorna `strftime("%Y-%m")`; registros por `year_month` com unique constraint — novo mes cria novo registro; teste `test_previous_month_does_not_count` passa |

**Score:** 11/11 truths verified

---

## Required Artifacts

| Artifact | Provides | Status | Detalhes |
|----------|----------|--------|----------|
| `app/models.py` | `user_id` FK no RouteGroup + relationship + modelo ApiUsage | VERIFIED | `user_id: Mapped[int \| None]` com `ForeignKey("users.id")`, `user: Mapped["User \| None"]`, classe `ApiUsage` com `year_month`, `search_count` |
| `alembic/versions/add_user_id_to_route_groups.py` | Migration adicionando user_id em route_groups | VERIFIED | `op.add_column`, `op.create_index`, `op.create_foreign_key` presentes |
| `alembic/versions/add_api_usage_table.py` | Migration criando tabela api_usage | VERIFIED | `op.create_table("api_usage", ...)` com coluna `year_month`, `search_count`, `updated_at` |
| `app/services/dashboard_service.py` | Todas as queries filtradas por user_id | VERIFIED | `get_groups_with_summary`, `get_dashboard_summary`, `get_recent_activity`, `get_price_history` aceitam e usam `user_id` |
| `app/routes/dashboard.py` | Todas as rotas passam user.id para services; rota `/alerts` | VERIFIED | `dashboard_index`, `create_group_form`, `dashboard_detail`, `edit_group_page`, `edit_group_form`, `toggle_group` com ownership checks; `def alerts_page` presente |
| `app/services/alert_service.py` | Email enviado para recipient dinamico | VERIFIED | `compose_alert_email(signal, group, recipient_email)` e `compose_consolidated_email(..., recipient_email)` com `msg["To"] = recipient_email or settings.gmail_recipient` |
| `app/services/polling_service.py` | Carrega user.email via joinedload; increment_usage por chamada | VERIFIED | `joinedload(RouteGroup.user)` na query; `increment_usage(db)` apos SerpAPI; quota guard no inicio do ciclo |
| `app/services/quota_service.py` | `get_monthly_usage`, `increment_usage`, `get_remaining_quota` | VERIFIED | As 3 funcoes presentes com `MONTHLY_QUOTA = 250` |
| `app/templates/dashboard/alerts.html` | Pagina Meus Alertas com tabela de sinais | VERIFIED | Template existe, exibe "Meus Alertas", tabela com colunas Data/Tipo/Urgencia/Rota/Preco, estado vazio |
| `app/templates/dashboard/index.html` | Badge de buscas restantes no summary bar | VERIFIED | `metric-value` com `api_remaining`/`api_quota`, logica de cor inline para <= 50 e <= 10 |
| `app/templates/base.html` | Link "Meus Alertas" no nav | VERIFIED | `<a href="/alerts"...>` presente com `title="Meus Alertas"` |
| `tests/test_data_isolation.py` | 6 testes de isolamento | VERIFIED | 6 funcoes `test_` cobrindo query, dashboard, detalhe, toggle e criacao |
| `tests/test_quota_service.py` | 5 testes de quota | VERIFIED | 5 testes cobrindo zero, increment, acumulacao, mes anterior, remaining |
| `tests/test_alerts_page.py` | 3 testes da pagina de alertas | VERIFIED | 3 testes cobrindo 200 status, isolamento por usuario e exibicao de detalhes |
| `tests/conftest.py` | Fixture `second_user` | VERIFIED | `second_user_fixture` presente com google_id distinto |

---

## Key Link Verification

| From | To | Via | Status | Detalhes |
|------|----|-----|--------|----------|
| `app/routes/dashboard.py` | `app/services/dashboard_service.py` | `user.id` passado como parametro | WIRED | `get_groups_with_summary(db, user_id=user_id)`, `get_dashboard_summary(db, user_id=user_id)`, `get_recent_activity(db, user_id=user_id)` |
| `app/models.py` | Alembic migration | `ForeignKey("users.id")` no RouteGroup | WIRED | Migration `add_user_id_to_route_groups.py` com `fk_route_groups_user_id` |
| `app/services/polling_service.py` | `app/services/alert_service.py` | `compose_consolidated_email` recebe `recipient_email` | WIRED | `recipient = group.user.email if group.user else settings.gmail_recipient` passado como `recipient_email=recipient` |
| `app/routes/dashboard.py` | `app/models.py` | Query `DetectedSignal` filtrado por `user_id` via join com RouteGroup | WIRED | `.join(RouteGroup, ...).filter(RouteGroup.user_id == user.id)` em `alerts_page` |
| `app/services/polling_service.py` | `app/services/quota_service.py` | `increment_usage` chamado apos cada SerpAPI call | WIRED | `increment_usage(db)` na linha 109 de `_poll_group`, apos `search_flights_with_insights` |
| `app/routes/dashboard.py` | `app/services/quota_service.py` | `get_monthly_usage` passado ao template via `get_dashboard_summary` | WIRED | `get_dashboard_summary` importa e chama `get_monthly_usage(db)` e `get_remaining_quota(db)` |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `app/templates/dashboard/index.html` (summary bar) | `summary.api_remaining` | `get_dashboard_summary(db)` → `get_remaining_quota(db)` → `ApiUsage.search_count` (DB query) | Sim — query real na tabela `api_usage` | FLOWING |
| `app/templates/dashboard/alerts.html` | `signals` | `db.query(DetectedSignal).join(RouteGroup).filter(RouteGroup.user_id == user.id)` | Sim — query real com join e filtro por usuario | FLOWING |
| `app/routes/dashboard.py:dashboard_index` | `groups` | `get_groups_with_summary(db, user_id=user_id)` → `db.query(RouteGroup).filter(RouteGroup.user_id == user_id)` | Sim — query com filtro real | FLOWING |

---

## Behavioral Spot-Checks

| Behavior | Comando | Resultado | Status |
|----------|---------|-----------|--------|
| 6 testes de isolamento passam | `pytest tests/test_data_isolation.py -v` | 6 passed | PASS |
| 5 testes de quota passam | `pytest tests/test_quota_service.py -v` | 5 passed | PASS |
| 3 testes de alertas passam | `pytest tests/test_alerts_page.py -v` | 3 passed | PASS |
| Suite completa sem regressao | `pytest -x` | 218 passed, 0 failed | PASS |

---

## Requirements Coverage

| Requirement | Plano Fonte | Descricao | Status | Evidencia |
|-------------|-------------|-----------|--------|-----------|
| MULTI-01 | 12-01-PLAN.md | Usuario ve apenas seus proprios grupos de rota, snapshots e sinais | SATISFIED | `user_id` FK no `RouteGroup`, todas as queries filtradas, 6 testes de isolamento passando |
| MULTI-02 | 12-02-PLAN.md | Alertas por email enviados para o email do proprio usuario (do Google) | SATISFIED | `compose_consolidated_email` aceita `recipient_email`; polling usa `group.user.email` via joinedload |
| MULTI-03 | 12-03-PLAN.md | Dashboard exibe indicador de buscas SerpAPI restantes no mes (budget compartilhado) | SATISFIED | `ApiUsage` model, `quota_service`, summary bar exibe `api_remaining/api_quota` |
| MULTI-04 | 12-02-PLAN.md | Usuario pode ver historico de todos os sinais detectados para seus grupos ("Meus alertas") | SATISFIED | Rota `GET /alerts` filtra sinais por usuario via join; template `alerts.html` exibe tabela completa |

Todos os 4 requisitos da fase 12 atribuidos em REQUIREMENTS.md sao SATISFIED. Nenhum requisito orfao encontrado.

---

## Anti-Patterns Found

| Arquivo | Linha | Padrao | Severidade | Impacto |
|---------|-------|--------|-----------|---------|
| `app/services/quota_service.py` | 17 | `datetime.utcnow()` depreciado no Python 3.12+ | Info | Sem impacto funcional; warning de deprecacao nos testes — nao bloqueia meta |
| `app/services/dashboard_service.py` | 46, 338 | `datetime.utcnow()` depreciado | Info | Mesmo padrao pre-existente; nao introduzido pela fase 12 |

Nenhum anti-padrao bloqueador encontrado. Nenhum stub, placeholder ou implementacao vazia identificado.

---

## Human Verification Required

### 1. Cores semanticas no badge de buscas

**Test:** Injetar `api_remaining = 8` no contexto e carregar o dashboard no browser
**Expected:** O valor "8/250" aparece em vermelho (#ef4444)
**Why human:** A logica de cor e inline no Jinja2 com condicionais aninhados; nao ha teste automatizado renderizando o HTML com esse valor especifico

### 2. Email entregue para usuario correto em producao

**Test:** Acionar um ciclo de polling em staging com dois usuarios cadastrados e grupos distintos
**Expected:** Cada usuario recebe email apenas sobre seus proprios grupos, no endereco do Google usado no login
**Why human:** O `send_email` e mockado em todos os testes; somente um envio SMTP real valida o fluxo completo

---

## Gaps Summary

Nenhum gap encontrado. Todos os 11 truths verificados passaram nos tres niveis (existencia, substancia, conexao) mais rastreio de fluxo de dados. A suite completa de 218 testes passa sem regressao.

Os dois itens marcados para verificacao humana sao confirmacoes visuais/SMTP que complementam a cobertura automatizada, mas nao bloqueiam a meta da fase.

---

_Verified: 2026-03-28_
_Verifier: Claude (gsd-verifier)_
