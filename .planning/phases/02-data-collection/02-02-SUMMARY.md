---
phase: 02-data-collection
plan: "02"
subsystem: amadeus-client
tags: [amadeus, api-wrapper, tdd, booking-classes, price-metrics]
dependency_graph:
  requires: [app/config.py]
  provides: [app/services/amadeus_client.py]
  affects: [polling_service (plan 03)]
tech_stack:
  added: [amadeus-sdk-12.0.0]
  patterns: [sdk-wrapper, graceful-degradation, quartile-classification]
key_files:
  created:
    - app/services/amadeus_client.py
    - tests/test_amadeus_client.py
  modified: []
decisions:
  - "ResponseError handled gracefully in get_price_metrics returning None instead of propagating"
  - "classify_price as standalone function (not method) for pure testability"
metrics:
  duration: 2min
  completed: "2026-03-25T03:19:00Z"
---

# Phase 02 Plan 02: Amadeus Client Wrapper Summary

Wrapper do Amadeus SDK com 3 metodos de alto nivel (offers, availability, price metrics) e funcao classify_price que deriva LOW/MEDIUM/HIGH a partir de quartis historicos.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | RED - Testes do AmadeusClient com mocks do SDK | acb182f | tests/test_amadeus_client.py |
| 2 | GREEN - Implementar AmadeusClient e classify_price | 87f2bdc | app/services/amadeus_client.py |

## What Was Built

### AmadeusClient (app/services/amadeus_client.py)

Classe wrapper que encapsula o Amadeus SDK com:

- **is_configured**: property que retorna False quando credenciais ausentes (client_id ou client_secret vazios)
- **search_cheapest_offers**: busca ate 250 ofertas via Flight Offers Search GET, ordena por preco e retorna top N
- **get_availability**: monta body com originDestinations ida/volta e chama Flight Availabilities POST
- **get_price_metrics**: busca quartis historicos via Itinerary Price Metrics GET, retorna None em caso de ResponseError

### classify_price (funcao pura)

Recebe preco e lista de metricas com quartileRanking, retorna:
- "LOW" se preco <= FIRST quartile
- "MEDIUM" se preco <= MEDIUM quartile
- "HIGH" se preco > MEDIUM quartile
- None se metricas vazias ou quartis ausentes

## Test Coverage

11 testes unitarios cobrindo:
- Configuracao: 2 testes (com/sem credenciais)
- search_cheapest_offers: 2 testes (top 5, menos que 5 disponivel)
- get_availability: 1 teste (retorna booking classes)
- get_price_metrics: 2 testes (sucesso, 404 retorna None)
- classify_price: 4 testes (LOW, MEDIUM, HIGH, sem metricas)

Suite completa: 45 testes passando (11 novos + 34 existentes).

## Deviations from Plan

None - plan executed exactly as written.

## Decisions Made

1. **ResponseError graceful degradation**: get_price_metrics captura qualquer ResponseError (nao so 404) e retorna None com log warning, evitando que falha de metricas quebre o polling inteiro.
2. **classify_price como funcao standalone**: separada da classe para ser pura e testavel sem mocks.

## Known Stubs

None - all functionality fully wired.

## Self-Check: PASSED

- [x] app/services/amadeus_client.py exists
- [x] tests/test_amadeus_client.py exists
- [x] Commit acb182f found
- [x] Commit 87f2bdc found
- [x] 02-02-SUMMARY.md exists
