---
phase: 12-data-isolation
plan: 03
subsystem: api
tags: [serpapi, quota, counter, dashboard]

requires:
  - phase: 10-postgresql-foundation
    provides: Alembic migration infrastructure
provides:
  - ApiUsage model for global SerpAPI monthly counter
  - quota_service with get/increment/remaining functions
  - Dashboard indicator showing remaining searches
  - Polling auto-stop when quota exhausted
affects: [polling, dashboard, future-billing]

tech-stack:
  added: []
  patterns: [global-counter-by-year-month, quota-guard-before-polling]

key-files:
  created:
    - app/services/quota_service.py
    - alembic/versions/add_api_usage_table.py
    - tests/test_quota_service.py
  modified:
    - app/models.py
    - app/services/polling_service.py
    - app/services/dashboard_service.py
    - app/templates/dashboard/index.html

key-decisions:
  - "Global counter per year_month string (YYYY-MM) with unique constraint, no per-user split"
  - "Quota check at start of polling cycle, increment after each SerpAPI call"

patterns-established:
  - "Quota guard pattern: check remaining before expensive operations, skip gracefully"

requirements-completed: [MULTI-03]

duration: 4min
completed: 2026-03-29
---

# Phase 12 Plan 03: API Quota Counter Summary

**Global SerpAPI usage counter with monthly reset, dashboard indicator, and polling auto-stop at 250 searches/month**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-29T02:33:24Z
- **Completed:** 2026-03-29T02:37:36Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- ApiUsage model with year_month unique key tracks global SerpAPI consumption
- quota_service provides get_monthly_usage, increment_usage, get_remaining_quota
- Dashboard summary bar shows "X/250 buscas restantes" with semantic colors (yellow at <=50, red at <=10)
- Polling cycle skips entirely when monthly quota is exhausted (250 searches)
- 5 unit tests covering zero state, increment, accumulation, month boundary, remaining calculation

## Task Commits

Each task was committed atomically:

1. **Task 1: Modelo ApiUsage + quota_service com contador mensal** - `c0f1941` (feat, TDD)
2. **Task 2: Integrar quota no polling + indicador no dashboard** - `eb53a4f` (feat)

## Files Created/Modified
- `app/models.py` - Added ApiUsage model with year_month, search_count, updated_at
- `app/services/quota_service.py` - MONTHLY_QUOTA=250, get/increment/remaining functions
- `alembic/versions/add_api_usage_table.py` - Migration creating api_usage table
- `tests/test_quota_service.py` - 5 tests covering all quota scenarios
- `app/services/polling_service.py` - Added increment_usage after SerpAPI calls, quota check before cycle
- `app/services/dashboard_service.py` - Added api_usage, api_remaining, api_quota to summary dict
- `app/templates/dashboard/index.html` - Added buscas restantes metric to summary strip

## Decisions Made
- Used global counter (not per-user) since SerpAPI free tier is shared across all users
- year_month as string "YYYY-MM" with unique constraint for simple monthly reset
- Quota check happens once at cycle start (not per-call) to avoid overhead
- increment_usage called after each SerpAPI call (even if no flights returned) since the API call was made

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Alembic autogenerate failed on local SQLite due to FK constraint from parallel 12-01 plan. Created migration manually instead.
- Pre-existing test failures in test_dashboard.py from parallel 12-01 plan (user_id on RouteGroup). Not caused by this plan's changes.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all data flows are wired to real sources.

## Next Phase Readiness
- Quota counter ready for use by any service that calls SerpAPI
- Dashboard indicator live and updating from real data
- Future enhancement: per-user quota tracking if needed

## Self-Check: PASSED

All 7 files exist. Both commits verified (c0f1941, eb53a4f). All acceptance criteria met. 5 quota tests passing.

---
*Phase: 12-data-isolation*
*Completed: 2026-03-29*
