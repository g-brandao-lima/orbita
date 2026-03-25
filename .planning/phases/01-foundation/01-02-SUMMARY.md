---
phase: 01-foundation
plan: 02
subsystem: route-groups
tags: [tdd, crud, pytest, route-groups, validation]

requires:
  - phase: 01-foundation
    plan: 01
    provides: "App skeleton, RouteGroup model, schemas, CRUD routes, conftest fixtures"
provides:
  - "22 comprehensive API-level tests covering ROUTE-01 through ROUTE-06"
  - "StaticPool fix for in-memory SQLite test reliability"
affects: [01-03]

tech-stack:
  added: []
  patterns: [staticpool-in-memory-sqlite, tdd-red-green-api-tests]

key-files:
  created: [tests/test_route_groups.py]
  modified: [tests/conftest.py]

key-decisions:
  - "Used StaticPool for in-memory SQLite test engine to ensure all connections share the same database"
  - "22 tests instead of 18 minimum to cover edge cases thoroughly"
  - "test_max_active_groups_allows_after_deactivate uses deactivate+create pattern since RouteGroupCreate has no is_active field"

patterns-established:
  - "VALID_GROUP constant as base payload for route group tests"
  - "Create-then-act pattern for stateful tests (create group, then patch/delete)"

requirements-completed: [ROUTE-01, ROUTE-02, ROUTE-03, ROUTE-04, ROUTE-05, ROUTE-06]

duration: 3min
completed: 2026-03-25
---

# Phase 1 Plan 2: Route Groups CRUD Tests Summary

**22 API-level TDD tests covering all Route Group requirements (ROUTE-01 through ROUTE-06) with StaticPool fix for reliable in-memory SQLite test isolation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-25T01:26:41Z
- **Completed:** 2026-03-25T01:30:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- 22 comprehensive tests covering create, validate, activate/deactivate, edit, delete, and max-10-active-groups limit
- TDD process followed: all 22 tests confirmed RED (19 failing due to missing StaticPool), then all GREEN after conftest fix
- Fixed conftest.py with StaticPool to ensure in-memory SQLite connections share the same database
- Full test suite: 28 tests passing (6 infra + 22 route groups)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write 22 tests for Route Groups CRUD (RED)** - `6b12247` (test)
2. **Task 2: Fix conftest StaticPool for GREEN** - `f4a429d` (fix)

## Files Created/Modified
- `tests/test_route_groups.py` - 22 tests: create (4), target_price (2), activate/deactivate (3), edit (4), delete (3), max limit (3), extras (3)
- `tests/conftest.py` - Added StaticPool import and poolclass parameter to test engine

## Test Coverage by Requirement

| Requirement | Tests | Status |
|-------------|-------|--------|
| ROUTE-01 (Create) | test_create_route_group, test_create_route_group_invalid_iata, test_create_route_group_empty_origins, test_create_route_group_invalid_duration | PASSED |
| ROUTE-02 (Target Price) | test_create_with_target_price, test_create_without_target_price | PASSED |
| ROUTE-03 (Activate/Deactivate) | test_deactivate_route_group, test_activate_route_group, test_deactivate_does_not_delete | PASSED |
| ROUTE-04 (Edit) | test_update_route_group_name, test_update_route_group_origins, test_update_nonexistent_group, test_update_partial_fields | PASSED |
| ROUTE-05 (Delete) | test_delete_route_group, test_delete_nonexistent_group, test_get_after_delete | PASSED |
| ROUTE-06 (Max 10 Active) | test_max_active_groups_limit, test_max_active_groups_allows_after_deactivate, test_activate_exceeds_limit | PASSED |
| Extras | test_list_route_groups, test_get_route_group_by_id, test_get_nonexistent_group | PASSED |

## Decisions Made
- Used StaticPool for in-memory SQLite: without it, each connection creates a fresh empty database, causing table-not-found errors
- 22 tests (exceeding 18 minimum) to thoroughly cover validation edge cases and the deactivate+create pattern for the max limit test
- test_max_active_groups_allows_after_deactivate pattern: create 10 active, deactivate 1, create new (since RouteGroupCreate schema has no is_active field)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed StaticPool missing in conftest.py**
- **Found during:** Task 1 (running RED tests)
- **Issue:** In-memory SQLite without StaticPool creates a new database per connection, so tables created by `create_all` were not visible to the test session
- **Fix:** Added `from sqlalchemy.pool import StaticPool` and `poolclass=StaticPool` to test engine configuration
- **Files modified:** tests/conftest.py
- **Commit:** f4a429d

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minimal. The Plan 01 conftest was missing StaticPool, which is a well-known requirement for in-memory SQLite testing. Fixed as part of GREEN phase.

## Issues Encountered
None beyond the StaticPool fix above.

## Known Stubs
None. All tests are fully functional with no placeholder data or hardcoded mock values.

## Next Phase Readiness
- All ROUTE requirements verified via tests
- Plan 03 (Refactor + human verification checkpoint) can proceed
- 28/28 tests passing across the full suite

---
*Phase: 01-foundation*
*Completed: 2026-03-25*

## Self-Check: PASSED

- All 2 created/modified files verified present on disk
- Commit 6b12247 (Task 1 RED) verified in git log
- Commit f4a429d (Task 2 GREEN) verified in git log
- 28/28 tests passing
