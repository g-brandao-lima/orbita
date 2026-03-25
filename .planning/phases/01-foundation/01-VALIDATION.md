---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + httpx (TestClient) |
| **Config file** | `tests/conftest.py` — Wave 0 installs |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~5 seconds |

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
| 1-01-01 | 01 | 0 | INFRA-01/02/03 | setup | `python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | INFRA-01 | integration | `python -m pytest tests/test_main.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | INFRA-02/03 | unit | `python -m pytest tests/test_database.py -x -q` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 0 | ROUTE-01/02 | TDD stub | `python -m pytest tests/test_routes.py -x -q` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | ROUTE-01/02 | unit | `python -m pytest tests/test_routes.py::test_create_route_group -x -q` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 1 | ROUTE-03/04 | unit | `python -m pytest tests/test_routes.py::test_update_route_group -x -q` | ❌ W0 | ⬜ pending |
| 1-02-04 | 02 | 1 | ROUTE-05 | unit | `python -m pytest tests/test_routes.py::test_delete_route_group -x -q` | ❌ W0 | ⬜ pending |
| 1-02-05 | 02 | 1 | ROUTE-06 | unit | `python -m pytest tests/test_routes.py::test_max_active_groups -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — pacote de testes
- [ ] `tests/conftest.py` — fixtures: TestClient, in-memory SQLite, limpar tabelas entre testes
- [ ] `tests/test_main.py` — stub: test_app_starts_and_responds (deve falhar RED)
- [ ] `tests/test_database.py` — stubs: test_tables_created_on_startup, test_env_variables_loaded (deve falhar RED)
- [ ] `tests/test_routes.py` — stubs: test_create, test_update, test_activate_deactivate, test_delete, test_max_active_groups (deve falhar RED)
- [ ] `requirements.txt` — fastapi==0.135.2, uvicorn==0.42.0, sqlalchemy==2.0.48, pydantic==2.12.5, pydantic-settings==2.13.1, python-dotenv, httpx, pytest==9.0.2, pytest-anyio

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `python main.py` inicia sem erro no Windows | INFRA-01 | Depende do ambiente Windows local | Rodar `python main.py`, verificar output no terminal |
| `.env` ausente levanta erro claro | INFRA-02 | Erro de inicialização fora do TestClient | Renomear .env, rodar app, verificar mensagem de erro |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
