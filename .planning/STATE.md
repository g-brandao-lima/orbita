# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-24)

**Core value:** Detectar o momento certo de comprar uma passagem antes que o preço suba, usando dados de booking class inventory (Amadeus API) que nenhum sistema consumer expõe.
**Current focus:** Phase 1 - Foundation

## Current Position

Phase: 1 of 5 (Foundation)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-03-24 — Roadmap criado; projeto inicializado

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: -
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: SQLite over PostgreSQL — uso pessoal, volume pequeno, zero configuração
- [Init]: APScheduler embedded (não Celery) — single-user, sem workers distribuídos
- [Init]: FastAPI + Jinja2 sem JS framework — interface mínima, sem complexidade de build
- [Init]: Amadeus como única fonte — único que expõe availabilityClasses com contagem por booking class
- [Init]: Roundtrip only na v1 — simplifica modelo e lógica; one-way é fase 2

### Pending Todos

None yet.

### Blockers/Concerns

- Amadeus free tier (~2000-3000 calls/mês) limita a ~4 grupos ativos com 2 pollings/dia; arquitetura de polling deve respeitar esse orçamento desde a Phase 2
- Companhias low-cost (Azul, Gol em algumas rotas) têm cobertura parcial no GDS; sinal pode ser ausente para essas rotas

## Session Continuity

Last session: 2026-03-24
Stopped at: Roadmap e STATE inicializados; próximo passo é `/gsd:plan-phase 1`
Resume file: None
