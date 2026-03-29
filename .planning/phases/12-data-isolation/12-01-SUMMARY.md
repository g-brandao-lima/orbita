---
phase: 12-data-isolation
plan: 01
subsystem: database
tags: [sqlalchemy, alembic, data-isolation, multi-tenant, fk]

# Dependency graph
requires:
  - phase: 11-google-oauth
    provides: User model with google_id, session auth, get_current_user dependency
provides:
  - user_id FK on route_groups table with index
  - Alembic migration for user_id column
  - All dashboard queries filtered by user_id
  - Ownership check on detail, edit, toggle routes
  - Data isolation tests (6 tests)
affects: [12-data-isolation, 13-redesign]

# Tech tracking
tech-stack:
  added: []
  patterns: [user_id filter on all service queries, ownership check on all mutating routes]

key-files:
  created:
    - alembic/versions/add_user_id_to_route_groups.py
    - tests/test_data_isolation.py
  modified:
    - app/models.py
    - app/services/dashboard_service.py
    - app/routes/dashboard.py
    - tests/conftest.py
    - tests/test_dashboard.py
    - tests/test_dashboard_feedback.py

key-decisions:
  - "user_id nullable=True on route_groups for backward compatibility with existing data"
  - "Ownership check returns 404 (not 403) to avoid leaking group existence"
  - "Service functions use optional user_id parameter for backward compatibility"

patterns-established:
  - "All service functions that return user data accept user_id parameter"
  - "All routes that access groups verify group.user_id == user.id"
  - "Test helpers pass user_id when creating RouteGroups for authenticated tests"

requirements-completed: [MULTI-01]

# Metrics
duration: 6min
completed: 2026-03-29
---

# Phase 12 Plan 01: Data Isolation Summary

**user_id FK on route_groups with full query filtering, ownership checks on all routes, and 6 isolation tests**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-29T02:33:08Z
- **Completed:** 2026-03-29T02:39:40Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- RouteGroup model now has user_id FK with index, linked to User via relationship
- All 4 dashboard service functions (get_groups_with_summary, get_dashboard_summary, get_recent_activity, get_price_history) filter by user_id
- All mutating routes (detail, edit, toggle) verify ownership before allowing access
- Group creation automatically assigns the logged-in user's id
- 6 isolation tests verify no cross-user data leakage
- 213 total tests passing with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: user_id FK + migration + isolation tests (RED)** - `6eec708` (test)
2. **Task 2: Filter services and routes by user_id (GREEN)** - `44d55ba` (feat)

## Files Created/Modified
- `app/models.py` - Added user_id FK column and User<->RouteGroup relationship
- `alembic/versions/add_user_id_to_route_groups.py` - Migration adding user_id column with index and FK
- `app/services/dashboard_service.py` - All query functions now accept and filter by user_id
- `app/routes/dashboard.py` - All routes pass user.id to services, ownership checks on detail/edit/toggle
- `tests/test_data_isolation.py` - 6 tests for cross-user isolation
- `tests/conftest.py` - Added second_user fixture
- `tests/test_dashboard.py` - Updated existing tests to pass user_id to RouteGroup creation
- `tests/test_dashboard_feedback.py` - Updated existing tests to pass user_id to RouteGroup creation

## Decisions Made
- user_id is nullable=True on route_groups for backward compatibility with existing production data (migration does not set a default)
- Ownership check returns 404 instead of 403 to prevent information leakage about group existence
- Service functions accept optional user_id parameter (None means no filter) for backward compatibility with polling service

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing tests to pass user_id when creating RouteGroups**
- **Found during:** Task 2 (GREEN phase, full test suite run)
- **Issue:** 15+ existing tests in test_dashboard.py and test_dashboard_feedback.py created RouteGroups without user_id, causing them to be invisible to the authenticated client (filtered out by user_id)
- **Fix:** Added test_user fixture parameter and user_id=test_user.id to all _make_group calls in affected tests
- **Files modified:** tests/test_dashboard.py, tests/test_dashboard_feedback.py
- **Verification:** Full test suite passes (213 tests, 0 failures)
- **Committed in:** 44d55ba (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Expected regression from adding user_id filtering. All tests updated, no scope creep.

## Issues Encountered
None beyond the expected test regressions documented above.

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all data paths are fully wired.

## Next Phase Readiness
- Data isolation is complete for route_groups
- Ready for scheduler fairness (12-02) and quota management (12-03)
- Existing production data will have user_id=NULL; a data migration script may be needed on first deploy to assign existing groups to the admin user

## Self-Check: PASSED

- All 8 key files verified present on disk
- Commit 6eec708 (Task 1 RED) verified in git log
- Commit ac093e4 (Task 2 GREEN) verified in git log
- 213 tests passing (verified via pytest)

---
*Phase: 12-data-isolation*
*Completed: 2026-03-29*
