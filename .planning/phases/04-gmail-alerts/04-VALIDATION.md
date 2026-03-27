---
phase: 4
slug: gmail-alerts
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 — existing from Phase 1/2/3 |
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
| 4-01-01 | 01 | 1 | ALRT-01/02 | RED stub | `python -m pytest tests/test_alert_service.py -x -q` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | ALRT-01/02 | GREEN impl | `python -m pytest tests/test_alert_service.py -x -q` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 1 | ALRT-02 | RED stub | `python -m pytest tests/test_alert_routes.py -x -q` | ❌ W0 | ⬜ pending |
| 4-02-02 | 02 | 1 | ALRT-02 | GREEN impl | `python -m pytest tests/test_alert_routes.py -x -q && python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| 4-03-01 | 03 | 2 | ALRT-01/02 | integration | `python -m pytest tests/ -v --tb=short` | W0 | ⬜ pending |
| 4-03-02 | 03 | 2 | ALRT-01/02 | refactor | `python -m pytest tests/ -v --tb=short` | W0 | ⬜ pending |
| 4-03-03 | 03 | 2 | ALL | checkpoint | Human verify email received | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_alert_service.py` — stubs: test_send_alert_called_on_signal, test_silenced_group_skipped, test_email_contains_signal_info, test_hmac_token_generation
- [ ] `tests/test_alert_routes.py` — stubs: test_silence_endpoint_sets_silenced_until, test_invalid_token_rejected, test_silence_endpoint_returns_confirmation

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Email chega no Gmail com conteúdo correto | ALRT-01 | Requer credenciais Gmail reais + envio SMTP real | Configurar .env com gmail_sender/gmail_app_password/gmail_recipient reais, acionar sinal manualmente via polling trigger, verificar inbox |
| Clicar no link silencia o grupo por 24h | ALRT-02 | Requer email recebido e browser | Clicar no link do email, verificar que grupo fica silenciado no banco |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
