---
phase: 2
slug: data-collection
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + httpx (TestClient) — existing from Phase 1 |
| **Config file** | `tests/conftest.py` — already exists with StaticPool SQLite fixture |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 0 | COLL-01/05 | setup/RED | `python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | COLL-05 | unit | `python -m pytest tests/test_snapshots.py -x -q` | ❌ W0 | ⬜ pending |
| 2-01-03 | 01 | 1 | COLL-01 | unit | `python -m pytest tests/test_scheduler.py -x -q` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 0 | COLL-02/03 | RED stub | `python -m pytest tests/test_amadeus.py -x -q` | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 1 | COLL-02 | unit | `python -m pytest tests/test_amadeus.py::test_find_cheapest_combinations -x -q` | ❌ W0 | ⬜ pending |
| 2-02-03 | 02 | 1 | COLL-03 | unit | `python -m pytest tests/test_amadeus.py::test_fetch_booking_classes -x -q` | ❌ W0 | ⬜ pending |
| 2-02-04 | 02 | 1 | COLL-04 | unit | `python -m pytest tests/test_amadeus.py::test_fetch_price_analysis -x -q` | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 1 | COLL-06 | unit | `python -m pytest tests/test_amadeus.py::test_api_error_handling -x -q` | ❌ W0 | ⬜ pending |
| 2-03-02 | 03 | 1 | COLL-06 | unit | `python -m pytest tests/test_scheduler.py::test_scheduler_survives_api_failure -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_snapshots.py` — stubs: test_snapshot_persisted, test_snapshot_has_timestamp, test_booking_classes_persisted
- [ ] `tests/test_scheduler.py` — stubs: test_scheduler_starts, test_scheduler_runs_poll, test_scheduler_survives_api_failure
- [ ] `tests/test_amadeus.py` — stubs: test_find_cheapest_combinations, test_fetch_booking_classes, test_fetch_price_analysis, test_api_error_handling
- [ ] `requirements.txt` — adicionar amadeus==12.0.0, apscheduler==3.11.2

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Scheduler executa polling real e salva snapshot da Amadeus | COLL-01/02/03/04 | Requer credenciais reais da Amadeus + conta configurada | Configurar .env com credenciais reais, iniciar app, aguardar 1 ciclo manual (/api/v1/scheduler/trigger), verificar snapshot no banco |
| App inicia sem credenciais sem crashar | COLL-06 | Comportamento de startup fora do TestClient | Deixar AMADEUS_CLIENT_ID vazio no .env, rodar python main.py, confirmar que inicia com log de aviso |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
