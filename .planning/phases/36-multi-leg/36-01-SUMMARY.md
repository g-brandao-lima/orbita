---
phase: 36-multi-leg
plan: 01
subsystem: data-foundation
tags: [model, migration, pydantic, tdd, wave-0]
dependency_graph:
  requires: [i9j0k1l2m3n4]
  provides: [RouteGroupLeg, FlightSnapshot.details, RouteGroupMultiCreate, multi_leg_group_factory, multi_leg_snapshot_factory]
  affects: [app/models.py, app/schemas.py, alembic/versions/, tests/conftest.py]
tech_stack:
  added: []
  patterns: [Pydantic model_validator, SQLAlchemy cascade delete, Alembic sequential revision, pytest factory fixtures]
key_files:
  created:
    - alembic/versions/j0k1l2m3n4o5_add_route_group_leg_and_details.py
    - tests/test_multi_leg_model.py
    - tests/test_multi_leg_service.py
    - tests/test_multi_leg_routes.py
    - tests/test_multi_leg_polling.py
    - tests/test_multi_leg_email.py
  modified:
    - app/models.py
    - app/schemas.py
    - tests/conftest.py
decisions:
  - Snapshot multi reusa FlightSnapshot com details JSON (D-03)
  - Validacao temporal Pydantic com sort-by-order antes de iterar (Pitfall 5)
  - Mensagem unica "entre 2 e 5 trechos" para boundary (conforme interfaces do plano)
metrics:
  duration_minutes: 12
  completed_date: 2026-04-22
  tasks_total: 5
  tasks_completed: 5
  tests_green: 5
  tests_red: 9
  commits: 5
  files_changed: 9
---

# Phase 36 Plan 01: Multi-Leg Foundation Summary

Fundacao de dados e contratos para roteiros multi-trecho. Inclui model `RouteGroupLeg` com cascade delete e unique constraint, coluna `FlightSnapshot.details: JSON`, migration Alembic reversivel, schemas Pydantic `LegCreate`/`LegOut`/`RouteGroupMultiCreate` com validacao temporal pt-BR, factories de teste e 5 arquivos de teste Wave 0 (5 GREEN + 9 RED) cobrindo MULTI-01..04 e D-19.

## Model, Migration e Schemas

### Model (app/models.py)

- **RouteGroupLeg**: id, route_group_id FK ON DELETE CASCADE, order, origin, destination, window_start, window_end, min_stay_days (default 1), max_stay_days nullable, max_stops nullable. Index unique `ix_route_group_legs_group_order(route_group_id, order)`.
- **RouteGroup.legs**: `relationship("RouteGroupLeg", back_populates="route_group", cascade="all, delete-orphan", order_by="RouteGroupLeg.order")`.
- **FlightSnapshot.details**: `Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)`.

### Migration (alembic/versions/j0k1l2m3n4o5_add_route_group_leg_and_details.py)

- revision `j0k1l2m3n4o5`, down_revision `i9j0k1l2m3n4`.
- `upgrade()`: create_table route_group_legs + create_index unique + add_column flight_snapshots.details JSON nullable.
- `downgrade()`: drop_column details + drop_index + drop_table.
- SQL validado via `alembic upgrade i9j0k1l2m3n4:j0k1l2m3n4o5 --sql` (migration gera DDL correto).

### Schemas (app/schemas.py)

- `LegCreate(BaseModel)`: 9 campos com `max_stay_days` e `max_stops` opcionais.
- `LegOut(LegCreate)`: + `id`, `ConfigDict(from_attributes=True)`.
- `RouteGroupMultiCreate(BaseModel)`: name, passengers, target_price, legs. `@model_validator(mode="after")` com sort-by-order (Pitfall 5), rejeita <2 ou >5 legs, min_stay<1, max_stay<min_stay, IATA diferente de 3 letras, e gap temporal invalido entre legs.

## Testes RED Mapeados por Requirement

| Arquivo | Teste | Req | Estado |
|---------|-------|-----|--------|
| test_multi_leg_model.py | test_leg_cascade_delete | MULTI-01 | GREEN |
| test_multi_leg_model.py | test_unique_order_constraint | MULTI-01 | GREEN |
| test_multi_leg_model.py | test_chain_validation_rejects_overlap | MULTI-02 | GREEN |
| test_multi_leg_model.py | test_min_max_legs | MULTI-02 | GREEN |
| test_multi_leg_model.py | test_flight_snapshot_details_json | MULTI-03 | GREEN |
| test_multi_leg_service.py | test_is_valid_chain | MULTI-02 | RED (Plan 02) |
| test_multi_leg_service.py | test_uses_route_cache_before_serpapi | MULTI-03 | RED (Plan 02) |
| test_multi_leg_service.py | test_persists_multi_snapshot_with_details | MULTI-03 | RED (Plan 02) |
| test_multi_leg_service.py | test_picks_cheapest_total | MULTI-03 | RED (Plan 02) |
| test_multi_leg_service.py | test_prediction_uses_total_median | MULTI-04 | RED (Plan 02) |
| test_multi_leg_routes.py | test_create_multi_leg_group_valid | MULTI-01 | RED (Plan 03) |
| test_multi_leg_routes.py | test_create_multi_leg_group_invalid_chain | MULTI-02 | RED (Plan 03) |
| test_multi_leg_polling.py | test_signal_on_total_price | MULTI-04 | RED (Plan 04) |
| test_multi_leg_email.py | test_consolidated_multi_has_chain_and_total | D-19 | RED (Plan 04) |

- 5 testes GREEN, 9 RED (esperado por desenho, dependem de service/route/email a implementar nos Plans 02/03/04).
- Collection limpa: 14/14 coletados, 0 ImportError ou SyntaxError.
- Full suite preexistente: 396 passed (zero regressao).

## Fixtures Adicionadas

- `multi_leg_group_factory(num_legs=2, name="Multi Trip Test")`: cria `RouteGroup(mode="multi_leg")` com N legs sequenciais (GRU->FCO->MAD->LIS->CDG->GRU), janelas de 20 dias separadas, stay 7-14.
- `multi_leg_snapshot_factory(group, total_price=6000.0)`: cria `FlightSnapshot(airline="MULTI", source="multi_leg")` com `details` JSON contendo `total_price` e `legs` breakdown.
- Uso: `def test_xxx(db, multi_leg_group_factory, multi_leg_snapshot_factory):` — reusa fixtures existentes `db` e `test_user`.

## Migration — Status de Aplicacao

- **SQL gerado e valido** (`alembic upgrade --sql` inspecionado).
- **Local SQLite db (orbita.db)**: upgrade head falha na migration antiga `a1b2c3d4e5f6` (`add user_id to route_groups`) por `NotImplementedError: No support for ALTER of constraints in SQLite dialect`. **Bug pre-existente, fora do escopo deste plan** — nao introduzido pela Phase 36. Registrado em `deferred-items.md` da fase.
- **Producao (PostgreSQL Neon)**: DDL padrao sem limitacao SQLite, migration aplicara normalmente.
- **Testes**: usam `Base.metadata.create_all` em SQLite in-memory via conftest, nao passam pelas migrations — todos os 396 pre-existentes + 5 novos GREEN passam.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing field defaults] Fixture multi_leg_group_factory precisa de campos obrigatorios do RouteGroup legado**
- **Found during:** Task 4 (implicito ao escrever), confirmado em Task 5 quando testes de model rodaram
- **Issue:** RouteGroup legacy exige origins, destinations, duration_days, travel_start, travel_end como NOT NULL; fixture crua do plano omitia.
- **Fix:** Preenchi campos com valores placeholder (`origins=["GRU"]`, `destinations=["FCO"]`, `duration_days=7`, `travel_start/end` cobrindo a janela multi). Em modo `multi_leg` esses campos sao ignorados pela logica de polling (D-01), mas precisam existir no schema.
- **Files modified:** tests/conftest.py
- **Commit:** 2841268

## Deferred Issues

**1. Migration legada `a1b2c3d4e5f6` nao roda em SQLite local**
- Nao foi introduzido por este plan; afeta apenas desenvolvimento local que aponte DATABASE_URL para sqlite. Producao (Postgres) nao afetada.
- Sugestao futura: refatorar a1b2c3d4e5f6 para usar `batch_alter_table` do Alembic (SQLite-safe).

## Self-Check: PASSED

Files created:
- FOUND: alembic/versions/j0k1l2m3n4o5_add_route_group_leg_and_details.py
- FOUND: tests/test_multi_leg_model.py
- FOUND: tests/test_multi_leg_service.py
- FOUND: tests/test_multi_leg_routes.py
- FOUND: tests/test_multi_leg_polling.py
- FOUND: tests/test_multi_leg_email.py

Commits:
- FOUND: 44619b8 feat(36-01): add RouteGroupLeg model and FlightSnapshot.details column
- FOUND: 6287e0f feat(36-01): add Alembic migration for route_group_legs and details column
- FOUND: 15fcc7d feat(36-01): add LegCreate, LegOut, RouteGroupMultiCreate schemas
- FOUND: 2841268 test(36-01): add multi_leg_group_factory and multi_leg_snapshot_factory fixtures
- FOUND: c8b2327 test(36-01): add Wave 0 RED test suite for multi-leg (MULTI-01..04, D-19)
