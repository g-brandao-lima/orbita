---
quick: 260425-0sf
type: summary
completed: 2026-04-25
duration_min: ~12
suite_before: 419
suite_after: 424
commits:
  - 1398699  # test(quota) RED + fix copy fast-flights
  - 0275324  # fix(polling) short-circuit + flash diferenciado
  - 28974df  # feat(cache) 6 rotas BR-internacional
  - 0f65f0d  # docs(debug) mark silent-manual-polling resolved
requirements_completed:
  - QUICK-260425-0sf-FIX1
  - QUICK-260425-0sf-FIX2
  - QUICK-260425-0sf-FIX3
key_files:
  created:
    - tests/test_polling_quota_exhausted.py
  modified:
    - app/services/polling_service.py
    - app/services/quota_service.py
    - app/services/route_cache_service.py
    - app/routes/dashboard.py
    - tests/test_route_cache_service.py
  moved:
    - .planning/debug/silent-manual-polling.md -> .planning/debug/resolved/
---

# Quick 260425-0sf: Fix quota esgotada + cache Travelpayouts expandido + copy

## One-liner

Polling com quota SerpAPI esgotada agora curto-circuita SerpAPI, retorna stats dict, exibe flash polling_sem_quota no manual_polling, e o cache Travelpayouts cobre 6 novos destinos BR-internacional (GIG-SCL, BSB-SCL, GIG-EZE, GRU-LIM, GRU-BOG, GRU-MEX). Copy mentirosa "fast-flights" eliminada do warning.

## O que mudou

### Fix 1 — Short-circuit + stats dict + flash diferenciado

- `run_polling_cycle` virou funcao com retorno tipado: `dict` com chaves `processed_groups`, `snapshots_created`, `snapshots_skipped_quota`, `snapshots_skipped_no_data`.
- Quando `get_remaining_quota(db) <= 0`, calcula `use_serpapi=False` e propaga para `_poll_group(db, group, use_serpapi=False, stats=stats)`.
- Em `_poll_group`, antes de cada chamada `search_flights`, se `not use_serpapi and not was_cache_hit`, consulta `route_cache_service.get_cached_price` direto. Cache miss vira skip + incremento de `snapshots_skipped_quota`. Cache hit segue fluxo normal (search_flights ja faz lookup do route_cache antes de SerpAPI).
- `manual_polling` (dashboard.py) agora recebe `db: Session = Depends(get_db)` e checa `get_remaining_quota` sincronamente. Se 0, redirect 303 `/?msg=polling_sem_quota` sem agendar background task. Se >0, comportamento atual.
- Adicionados 2 entries em `FLASH_MESSAGES`: `polling_sem_quota` e `polling_parcial_quota` (segundo so dispara via injecao manual; sem trigger automatico — vide pendencias).

### Fix 2 — Cache Travelpayouts expandido

- `TOP_BR_ROUTES` cresceu de 28 para 34 rotas. 6 novas: `GIG-SCL`, `BSB-SCL`, `GIG-EZE`, `GRU-LIM`, `GRU-BOG`, `GRU-MEX`.
- Conjunto BR-internacional final: 8 rotas (GRU/GIG/BSB para SCL/EZE/LIM/BOG/MEX).
- Teste `test_top_br_routes_contains_key_routes` atualizado de `== 28` para `== 34` (Rule 1: caused by current task).

### Fix 3 — Copy honesta no warning de quota

- `app/services/polling_service.py:38` — antes citava "Tentando via fast-flights" (removido em v2.3). Agora: "Apenas rotas do cache Travelpayouts serao processadas." Reflete o comportamento real apos esta task.

### Helper auxiliar

- `next_reset_date()` em `quota_service.py` retorna `date` do dia 1 do proximo mes (UTC). Disponivel para futuro uso em templates ou flash dinamico, nao usado ainda.

## Commits gerados

| Hash    | Tipo  | Mensagem |
|---------|-------|----------|
| 1398699 | test  | test(quota): adiciona testes RED para short-circuit quota=0 + corrige copy fast-flights |
| 0275324 | fix   | fix(polling): short-circuit quando quota SerpAPI esgota e flash diferenciado em manual_polling |
| 28974df | feat  | feat(cache): adiciona 6 rotas BR-internacional ao cron Travelpayouts |
| 0f65f0d | docs  | docs(debug): mark silent-manual-polling resolved |

## Suite de testes

- Antes: 419 passed
- Depois: 424 passed (+5 testes RED -> GREEN)
- Arquivo novo: `tests/test_polling_quota_exhausted.py` (5 testes)
- Teste alterado: `tests/test_route_cache_service.py::test_top_br_routes_contains_key_routes` (28 -> 34, scope-bound: causado pela expansao desta task)

## Edge cases descobertos durante implementacao

- Mock target inicial estava errado (`app.services.serpapi_client.search_flights` nao existe; e `SerpApiClient.search_flights_with_insights`). Corrigido no proprio commit RED quando confirmado o caminho real via leitura de `flight_search.py`.
- O teste `test_top_br_routes_contains_key_routes` usava count hardcoded (28). Atualizado para 34 inline (Rule 1, deviation tracked here).
- `_poll_group` aceitava chamada direta sem `stats` em testes existentes; adicionado fallback `if stats is None: stats = {...}` para retrocompatibilidade.

## Pendencias / observacoes

- `polling_parcial_quota` esta no enum mas nao tem trigger automatico atualmente. Cenario "quota era >0 ao abrir handler mas zerou durante o ciclo" exigiria persistir resultado do ciclo (ex: tabela `PollingRun` ou cache compartilhado handler<->background). Fica disponivel para futuro caso surja necessidade real.
- `next_reset_date()` criado mas nao consumido. Templates / emails podem usar para mostrar data exata da renovacao.
- Sentry LoggingIntegration ainda capturando logs como breadcrumbs sem stdout (resolvido em commit anterior `f4d1a9d` com `logging.basicConfig`). Esta task nao toca em logging — apenas garante que o sintoma "silencio total no clique Buscar agora" deixa de existir do lado do usuario via flash diferenciado.

## Self-Check: PASSED

- tests/test_polling_quota_exhausted.py: FOUND
- app/services/quota_service.py (next_reset_date): FOUND
- app/services/polling_service.py (snapshots_skipped_quota, sem fast-flights): FOUND
- app/routes/dashboard.py (polling_sem_quota): FOUND
- app/services/route_cache_service.py (GIG, SCL): FOUND
- Commits 1398699, 0275324, 28974df: FOUND em git log
- Suite full: 424/424 verde
