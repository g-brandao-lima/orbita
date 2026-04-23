---
phase: 36-multi-leg
plan: 04
subsystem: dashboard-email-multi
tags: [service, template, email, tdd, wave-3]
dependency_graph:
  requires: [36-01, 36-02, 36-03, RouteGroupLeg, FlightSnapshot.details, multi_leg_service]
  provides:
    - dashboard_service._build_multi_leg_item
    - dashboard_service.booking_urls_oneway
    - alert_service._render_consolidated_multi
    - alert_service.compose_consolidated_email dispatcher por group.mode
    - templates dashboard/index.html card-multi variant
    - templates dashboard/detail.html multi-breakdown section
  affects:
    - app/services/dashboard_service.py
    - app/services/alert_service.py
    - app/routes/dashboard.py
    - app/templates/dashboard/index.html
    - app/templates/dashboard/detail.html
    - tests/test_dashboard.py
    - tests/test_multi_leg_email.py
tech_stack:
  added: []
  patterns:
    - Dispatcher por tipo posicional (detect Session vs list)
    - Email inline hex (documentada excecao a tokens)
    - Jinja2 guard com {% if group.mode == "multi_leg" and legs_breakdown %}
    - booking_urls one-way helper separado do roundtrip
key_files:
  created: []
  modified:
    - app/services/dashboard_service.py
    - app/services/alert_service.py
    - app/routes/dashboard.py
    - app/templates/dashboard/index.html
    - app/templates/dashboard/detail.html
    - tests/test_dashboard.py
    - tests/test_multi_leg_email.py
decisions:
  - "booking_urls one-way: criado helper separado `booking_urls_oneway` no mesmo arquivo (app/services/dashboard_service.py) em vez de aceitar `return_date=None` no helper roundtrip. Motivo: booking_urls existente faz strftime(return_date) sem guard, e monkey-patch quebraria 10+ callers. Decisao low-risk, localizada."
  - "Recomendacao no email multi: renderizada INLINE dentro de _render_consolidated_multi (nao ha helper reutilizavel exportado em alert_service; o bloco de recomendacao do roundtrip esta inline em _render_consolidated_html). Mesmo padrao aplicado ao multi."
  - "Dispatcher compose_consolidated_email: detecta Session via hasattr(obj, 'query'). Preserva backward-compat total com 18 callers roundtrip (tests + polling_service)."
  - "Email hex inline: excecao documentada (Gmail/Outlook nao suportam CSS vars). Hex mapeado 1:1 para tokens de base.html (--bg-1=#0E1220, --brand-500=#6366F1, --accent-500=#22D3EE, --text-0=#F8FAFC->FFFFFF para contraste)."
metrics:
  duration_minutes: 10
  completed_date: 2026-04-23
  tasks_total: 4
  tasks_completed: 4
  tests_green_new: 4
  tests_red_resolved: 1
  commits: 4
  files_changed: 7
---

# Phase 36 Plan 04: Multi-Leg Dashboard, Detalhe e Email Summary

Adaptacao do dashboard (card home + pagina de detalhe) e do email consolidado para o modo multi-trecho. Implementa D-16 (card multi), D-17 (comparadores one-way por leg), D-18 (breakdown trecho-a-trecho no detalhe), D-19 (email consolidado com recomendacao Phase 34 MANDATORIA no topo) e D-20 (subject "Orbita multi: ..."). Fecha Phase 36.

## Pre-Task Discoveries

### booking_urls one-way (Task 1)

`grep -rn "def booking_urls" app/`:
- app/services/dashboard_service.py:504 — `booking_urls(origin, destination, departure_date, return_date, passengers=1)`

A assinatura atual chama `return_date.strftime("%Y-%m-%d")` sem guard; nao aceita None. Decisao: criar helper dedicado `booking_urls_oneway(origin, destination, departure_date, passengers=1)` no mesmo arquivo (linhas 504-545). Retorna as mesmas 4 chaves, com parametros one-way nos agregadores:
- Google Flights: hash `#flt=O.D.YYYY-MM-DD;c:BRL;e:1;sd:1;t:f;tt:o` (flag `tt:o` = one-way)
- Decolar: rota `/shop/flights/results/oneway/O/D/YYYY-MM-DD/pax/0/0`
- Skyscanner: `/transport/flights/o/d/YYMMDD/` sem segunda data
- Kayak: `/flights/O-D/YYYY-MM-DD` sem segunda data

Teste `test_multi_leg_compare_urls_are_one_way` valida heuristicamente: Google Flights sem asterisco `*`, Kayak com apenas uma data `YYYY-MM-DD`.

### Helper de render de recomendacao (Task 2)

`grep -nE "def (_render_recommendation|render_recommendation|_recommendation_html|format_recommendation)" app/services/*.py`:
- Retornou apenas `build_recommendation_for_group` (engine, nao render).

No roundtrip (`_render_consolidated_html`), o bloco de recomendacao e inline em linhas 370-390. Nao ha helper reutilizavel. Seguindo o mesmo padrao, `_render_consolidated_multi` renderiza o bloco INLINE com a mesma engine de recomendacao (`_build_multi_leg_item` reaproveitado para computar a Recommendation antes do render).

## Servicos Estendidos

### dashboard_service.py

- **`_build_multi_leg_item(db, group) -> dict`** — handler dedicado para grupos `mode=multi_leg`. Emite:
  - `mode="multi_leg"`, `legs_chain`, `legs_count`, `total_price`, `legs_breakdown`, `recommendation`
  - Campos legados preservados (group, cheapest_snapshot, signal) para sort do dashboard nao quebrar
  - Query do ultimo snapshot filtra por `airline == "MULTI"` (nao por origins/destinations do grupo, que para multi sao placeholders)
  - Recomendacao usa totals_history dos ultimos 90 dias de snapshots MULTI do mesmo grupo
  - `days_to_departure` computado a partir de `snapshot.departure_date` (primeiro leg, conforme Pitfall 3)
  - Pitfall 7 respeitado: sem snapshot retorna `total_price=None` e `legs_breakdown=None`
- **`booking_urls_oneway(origin, destination, departure_date, passengers=1) -> dict`** — novo helper para URLs one-way por leg (D-17).
- **`get_groups_with_summary`** — branch no topo do loop: se `group.mode == "multi_leg"`, usa `_build_multi_leg_item` e pula queries roundtrip.

### alert_service.py

- **`_render_consolidated_multi(db, group, snapshot, signals_list) -> dict`** — render multi-leg. Retorna `{subject, html, text, message}`.
  - Subject D-20: `f"Orbita multi: {group.name} {total_br} ({N} trechos)"`
  - HTML ordem fixa por D-19: `recommendation-block` (topo, SEMPRE presente) -> cadeia (mono 20px) -> total (mono 28px brand) -> tabela breakdown -> rodape total -> cluster comparadores por leg -> CTA
  - Plain text identico: "Recomendacao: ..." antes da cadeia e antes do primeiro "Trecho"
  - Fallback de recomendacao: "Recomendacao: Coletando historico. Aguarde alguns ciclos..." quando `recommendation is None` (D-19 mandatorio mesmo sem amostras)
  - Cluster comparadores: 4 botoes one-way por leg usando `booking_urls_oneway`
- **`compose_consolidated_email`** — dispatcher dual:
  - Novo formato: `(db, group, snapshots, signals)` — detectado via `hasattr(first_arg, "query")`
  - Legado: `(signals, snapshots, group, recipient_email=None, db=None)` — 18 callers pre-existentes preservados
  - Dispatch automatico para `_render_consolidated_multi` quando `group.mode == "multi_leg"`

### app/routes/dashboard.py

- **`dashboard_detail`** — contexto extra para grupos multi_leg: `legs_chain`, `legs_breakdown`, `total_price`, `format_price_brl`. Computado via `_build_multi_leg_item` (reuso total da logica do service).

## Templates

### index.html

- Branch `{% if item.group.mode == "multi_leg" %}` no loop de cards.
- Card multi: `<article class="card card-multi">` com badge MULTI, chain-line (IATAs + setas `-&gt;` em `--accent-500`), total price mono 28px, recommendation block reaproveitado, empty state pt-BR exato.
- CSS via tokens: `--accent-500`, `--text-0/1/2/3`, `--brand-500`, `--bg-2`, `--sp-*`, `--r-*`. Unica cor hardcoded permitida: `rgba(34,211,238,0.12)` para fundo do badge (prescrito pelo UI-SPEC).
- Mobile: cadeia empilha em 1 coluna, setas escondidas em `<768px`.

### detail.html

- Secao `<section class="multi-breakdown">` renderizada quando `group.mode == "multi_leg"` e `legs_breakdown` truthy.
- Header "Combinacao mais barata encontrada" + cadeia.
- Por leg: `<article class="leg-row">` com "Trecho N: ORIG -> DEST", "Saida em DD/MM/AAAA", preco mono 20px, "via AIRLINE", cluster "Comparar este trecho em" + 4 botoes.
- Rodape: separador `--border-2`, "Total do roteiro" label + valor mono 28px.
- Empty state: `<section class="multi-empty">` quando mode=multi_leg mas sem breakdown.

## Testes

| Arquivo | Teste | Estado pre-plan | Estado pos-plan |
|---------|-------|-----------------|-----------------|
| test_dashboard.py | test_multi_leg_service_returns_chain_and_breakdown | NEW | GREEN |
| test_dashboard.py | test_multi_leg_service_empty_snapshot_guard | NEW | GREEN |
| test_dashboard.py | test_multi_leg_compare_urls_are_one_way | NEW | GREEN |
| test_multi_leg_email.py | test_consolidated_multi_has_chain_and_total | RED (Plan 01) | GREEN |
| test_multi_leg_email.py | test_consolidated_multi_has_recommendation_before_legs | NEW | GREEN |

- Full suite: **410 passed, 0 failed** (previamente 405 passed, 1 failed — o ultimo RED da fase virou GREEN)
- Zero regressao em alert_service, polling_service, roundtrip dashboard

## Task 4: Checkpoint Visual (Auto-aprovado)

`workflow.auto_advance=true` na config. Checkpoint visual dashboard multi + Gmail:
- Auto-approved: `AUTO_CFG=true`
- Log: "Auto-approved: card multi + detalhe breakdown + email consolidado multi renderizam via SSR + servidor nao iniciado interativamente"
- Validacao real (servidor rodando + Gmail real) fica para o usuario quando conveniente. Testes automatizados cobrem: endpoint 200 OK via TestClient (previos), render template importavel, service retorna estrutura correta, email retorna subject/html/text estruturados.

## Must-Haves Verification

- [x] Dashboard home card multi: badge MULTI, cadeia mono com setas ciano, total 28px, recomendacao Phase 34
- [x] Pagina /groups/{id} breakdown trecho-a-trecho com preco, data e cia por leg + total
- [x] Cada leg tem cluster "Comparar este trecho em" com 4 botoes one-way (D-17)
- [x] Email subject "Orbita multi: {nome} R$ X,XX (N trechos)" (D-20)
- [x] Email corpo: RECOMENDACAO MANDATORIA NO TOPO (D-19) + cadeia + total destaque + tabela breakdown
- [x] Card multi mantem paridade estrutural (mesmo card-top / card-price-area / card-bottom)
- [x] Empty state "Primeira busca em andamento..." para grupo multi sem snapshot

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `compose_consolidated_email` tem assinatura legada incompativel com contrato novo do plano**
- **Found during:** Task 2 leitura
- **Issue:** Plano especifica `compose_consolidated_email(db, group, snapshots, signals) -> EmailPayload`. Assinatura existente e `(signals, snapshots, group, recipient_email=None, db=None) -> MIMEMultipart`. Alterar posicional quebraria 18 callers (polling_service + tests).
- **Fix:** Dispatcher dual que detecta formato via `hasattr(first_arg, "query")` (Session) vs list. Mantem backward-compat 100% e suporta a nova forma esperada pelos testes de Plan 04.
- **Files modified:** app/services/alert_service.py
- **Commit:** ba460ae

**2. [Rule 2 - Missing context] `dashboard_detail` nao passava breakdown para template detail.html**
- **Found during:** Task 3 implementacao do template
- **Issue:** Template espera `legs_chain`, `legs_breakdown`, `total_price`, `format_price_brl` mas a rota so passava `group`, `chart_data`, `format_date_br`, `user`.
- **Fix:** Branch `if group.mode == "multi_leg":` na rota computa via `_build_multi_leg_item` e passa no context.
- **Files modified:** app/routes/dashboard.py
- **Commit:** c678c87

**3. [Rule 1 - Scope] Plan contrato de `_build_multi_leg_item` incluia `Recommendation.label`/`Recommendation.class_slug`, mas dataclass real usa `action`/`reason`**
- **Found during:** Task 3 leitura da Phase 34
- **Issue:** Plano assumia campos que nao existem em `Recommendation` (dataclass frozen em price_prediction_service.py). Corrigido no template para `recommendation.action` e `recommendation.reason` (padrao identico ao card roundtrip ja existente).
- **Fix:** Templates usam os campos reais; email renderiza `rec_label = recommendation.action`.
- **Files modified:** app/templates/dashboard/index.html, app/services/alert_service.py
- **Commits:** ba460ae, c678c87

### Intentional simplifications

- **Auto-approve do checkpoint human-verify:** `workflow.auto_advance=true`. Verificacao real pelo usuario fica para o momento conveniente (servidor + Gmail live).
- **Card multi reusa classes do card roundtrip (.card-top, .card-price-area, .card-bottom)** em vez de gerar um layout totalmente novo, garantindo paridade visual e mobile-responsiveness sem CSS adicional.

## Deferred Issues

- Nenhum issue adiado. Scope fechado conforme plano.

## Self-Check: PASSED

Files modified:
- FOUND: app/services/dashboard_service.py
- FOUND: app/services/alert_service.py
- FOUND: app/routes/dashboard.py
- FOUND: app/templates/dashboard/index.html
- FOUND: app/templates/dashboard/detail.html
- FOUND: tests/test_dashboard.py
- FOUND: tests/test_multi_leg_email.py

Commits:
- FOUND: 0048e44 test(36-04): add RED tests for multi_leg dashboard_service (chain, breakdown, oneway URLs)
- FOUND: 3cb99f3 feat(36-04): extend dashboard_service with multi_leg breakdown + booking_urls_oneway
- FOUND: ba460ae feat(36-04): add _render_consolidated_multi with mandatory recommendation at top (D-19, D-20)
- FOUND: c678c87 feat(36-04): render multi-leg card in index.html + breakdown in detail.html
