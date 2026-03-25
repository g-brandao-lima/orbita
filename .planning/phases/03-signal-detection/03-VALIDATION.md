---
phase: 3
slug: signal-detection
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 3 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 - existing from Phase 1/2 |
| **Config file** | `tests/conftest.py` - already exists with StaticPool SQLite fixture |
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
| 3-01-01 | 01 | 1 | SIGN-01/02/03/04/05 | checkpoint:human-verify | Spec approval (human) | N/A | pending |
| 3-01-02 | 01 | 1 | SIGN-01/02/03/04/05 | model + stubs | `python -c "from app.models import DetectedSignal; print(DetectedSignal.__tablename__)"` | N/A | pending |
| 3-01-03 | 01 | 1 | SIGN-01/02/03/04/05 | RED tests | `python -m pytest tests/test_signal_service.py -x -q` | W0 | pending |
| 3-02-01 | 02 | 2 | SIGN-01/02/03/04/05 | GREEN impl | `python -m pytest tests/test_signal_service.py -v --tb=short` | W0 | pending |
| 3-02-02 | 02 | 2 | SIGN-01/02/03/04/05 | integration | `python -m pytest tests/ -v --tb=short` | W0 | pending |
| 3-03-01 | 03 | 3 | SIGN-01/02/03/04/05 | REFACTOR | `python -m pytest tests/ -v --tb=short` | W0 | pending |
| 3-03-02 | 03 | 3 | SIGN-01/02/03/04/05 | checkpoint:human-verify | Human verification of full system | N/A | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_signal_service.py` - created in Plan 01 Task 3 (RED phase): test_balde_fechando_k_drops, test_balde_reaberto, test_preco_abaixo_historico, test_janela_otima_domestico, test_deduplicacao_bloqueia, test_primeiro_snapshot_sem_sinal_balde, test_multiple_signals_same_snapshot (18+ tests total)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sinais detectados aparecem corretamente apos polling real | SIGN-01 a SIGN-04 | Requer snapshots reais acumulados de ciclos anteriores | Apos 2+ ciclos de polling com credenciais Amadeus reais, verificar tabela detected_signals no banco |
| App funciona de ponta a ponta | All SIGN-* | Integracao real com servidor | Plan 03 Task 2 checkpoint: iniciar servidor, verificar tabelas, revisar RESUMO DA ENTREGA |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
