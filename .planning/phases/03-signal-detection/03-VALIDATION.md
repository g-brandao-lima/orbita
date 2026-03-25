---
phase: 3
slug: signal-detection
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 — existing from Phase 1/2 |
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
| 3-01-01 | 01 | 1 | SIGN-01/02 | RED stub | `python -m pytest tests/test_signal_detector.py -x -q` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 1 | SIGN-01/02 | unit GREEN | `python -m pytest tests/test_signal_detector.py -x -q` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | SIGN-03/04 | RED stub | `python -m pytest tests/test_signal_detector.py -x -q` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 1 | SIGN-03/04 | unit GREEN | `python -m pytest tests/test_signal_detector.py -x -q` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 2 | SIGN-05 | RED stub | `python -m pytest tests/test_signal_dedup.py -x -q` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03 | 2 | SIGN-05 | unit GREEN | `python -m pytest tests/test_signal_dedup.py -x -q && python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_signal_detector.py` — stubs: test_detect_balde_fechando, test_detect_balde_reaberto, test_detect_preco_abaixo_historico, test_detect_janela_otima, test_no_signal_first_snapshot
- [ ] `tests/test_signal_dedup.py` — stubs: test_dedup_blocks_within_12h, test_dedup_allows_after_12h, test_dedup_different_routes_not_blocked

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Sinais detectados aparecem corretamente após polling real | SIGN-01 a SIGN-04 | Requer snapshots reais acumulados de ciclos anteriores | Após 2+ ciclos de polling com credenciais Amadeus reais, verificar tabela detected_signals no banco |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
