---
phase: 03-signal-detection
verified: 2026-03-25T04:45:00Z
status: passed
score: 5/5 must-haves verified
gaps: []
human_verification:
  - test: "Executar app em producao e inspecionar logs apos ciclo de polling"
    expected: "Mensagens 'Signal detected: BALDE_FECHANDO (ALTA) for ...' ou similar aparecem no log quando condicoes sao atendidas"
    why_human: "Requer Amadeus API configurada com credenciais reais e dados de voo ao vivo para verificar que o fluxo end-to-end detecta sinais em producao"
---

# Phase 3: Signal Detection Verification Report

**Phase Goal:** Sistema analisa snapshots sequenciais e detecta os momentos de compra mais valiosos
**Verified:** 2026-03-25T04:45:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Sistema detecta BALDE FECHANDO (classe K ou Q caiu de >=3 para <=1) e marca urgencia ALTA | VERIFIED | `_check_balde_fechando` em signal_service.py L202-212; testes `test_balde_fechando_k_drops` e `test_balde_fechando_q_drops` passam |
| 2 | Sistema detecta BALDE REABERTO (classe estava em 0 e voltou a ter assentos) e marca urgencia MAXIMA | VERIFIED | `_check_balde_reaberto` em signal_service.py L216-239; teste `test_balde_reaberto` passa com urgency="MAXIMA" |
| 3 | Sistema detecta PRECO ABAIXO DO HISTORICO (LOW e preco atual abaixo da media dos ultimos 14 snapshots) e marca urgencia MEDIA | VERIFIED | `_check_preco_abaixo_historico` com `_get_avg_price_last_n(n=14)` e `MIN_SNAPSHOTS_FOR_PRICE=3`; testes happy path e edge cases passam |
| 4 | Sistema detecta JANELA OTIMA (dias antes do voo entra na faixa ideal por tipo de rota) e marca urgencia MEDIA | VERIFIED | `_check_janela_otima` com `DOMESTIC_WINDOW=(21,90)` e `INTERNATIONAL_WINDOW=(30,120)`; testes domestico e internacional passam |
| 5 | Mesmo sinal para a mesma rota nao e re-emitido dentro de 12 horas (deduplicacao funciona) | VERIFIED | `_is_duplicate` com `timedelta(hours=12)` aplicado sobre `snapshot.collected_at`; testes `test_deduplicacao_bloqueia`, `test_deduplicacao_permite_apos_12h` e `test_deduplicacao_different_route_not_blocked` passam |

**Score:** 5/5 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/models.py` | DetectedSignal model com 12 campos e ix_signal_dedup | VERIFIED | Classe DetectedSignal com todos os campos especificados, Index("ix_signal_dedup", ...) presente na linha 88-96 |
| `app/services/signal_service.py` | Implementacao completa dos 4 detectores, dedup e orquestrador | VERIFIED | 347 linhas (min 120); exporta `detect_signals`, todos os `_check_*`, `BRAZILIAN_AIRPORTS`, `CLOSING_CLASSES` |
| `app/services/polling_service.py` | Integracao com detect_signals apos save_flight_snapshot | VERIFIED | Import na linha 7; chamada na linha 128 dentro de `_process_offer` |
| `tests/test_signal_service.py` | Testes cobrindo SIGN-01 a SIGN-05 com edge cases | VERIFIED | 617 linhas (min 150); 19 testes em 5 classes: TestBaldeFechando, TestBaldeReaberto, TestPrecoAbaixoHistorico, TestJanelaOtima, TestDeduplicacao, TestEdgeCases |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_signal_service.py` | `app/services/signal_service.py` | `from app.services.signal_service import detect_signals` | WIRED | Linha 11 do arquivo de testes; todos os 19 testes invocam detect_signals |
| `app/models.py` | `app/database.py` | Heranca de Base | WIRED | `class DetectedSignal(Base)` na linha 66 |
| `app/services/signal_service.py` | `app/models.py` | Import de FlightSnapshot, BookingClassSnapshot, DetectedSignal | WIRED | Linhas 8-12 do signal_service |
| `app/services/signal_service.py` | database | db.query(FlightSnapshot) e db.query(DetectedSignal) | WIRED | Linhas 147-159 (`_get_previous_snapshot`) e 305-316 (`_is_duplicate`) |
| `app/services/polling_service.py` | `app/services/signal_service.py` | detect_signals chamado apos save_flight_snapshot | WIRED | Import L7; chamada L128 dentro de bloco try/except com logging |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `signal_service._check_balde_fechando` | `prev_classes`, `curr_classes` | `_booking_classes_to_dict(snapshot.booking_classes)` via SQLAlchemy relationship | Sim — dados lidos diretamente de BookingClassSnapshot persistido | FLOWING |
| `signal_service._check_preco_abaixo_historico` | `avg_price`, `count` | `_get_avg_price_last_n` via `select(sa_func.avg, sa_func.count)` com subquery real | Sim — subquery sobre FlightSnapshot com filtros de rota | FLOWING |
| `signal_service._is_duplicate` | `existing` | `db.query(DetectedSignal).filter(...).first()` | Sim — query real contra detected_signals com cutoff calculado | FLOWING |
| `polling_service._process_offer` | `detected` (sinais retornados) | `detect_signals(db, snapshot)` apos `save_flight_snapshot` | Sim — snapshot real retornado por save_flight_snapshot e passado ao detector | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 74 testes passam (incluindo todos os 19 de signal detection) | `python -m pytest tests/ -v --tb=short` | 74 passed in 1.11s | PASS |
| DetectedSignal importavel com todos os campos | `from app.models import DetectedSignal` — verificacao de colunas | 12 colunas + ix_signal_dedup confirmados | PASS |
| detected_signals table existe no banco | `inspect(engine).get_table_names()` | `['detected_signals']` retornado | PASS |
| detect_signals importavel do modulo correto | `from app.services.signal_service import detect_signals` | Importacao bem sucedida | PASS |
| Todos os exports e constantes presentes | `hasattr(signal_service, ...)` para 8 simbolos | True para todos | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| SIGN-01 | 03-01, 03-02, 03-03 | BALDE FECHANDO: K ou Q cai de >=3 para <=1, urgencia ALTA | SATISFIED | `_check_balde_fechando` implementado; 4 testes passam (k_drops, q_drops, no_change, still_above_threshold) |
| SIGN-02 | 03-01, 03-02, 03-03 | BALDE REABERTO: classe volta de 0 para >0, urgencia MAXIMA | SATISFIED | `_check_balde_reaberto` implementado; 2 testes passam (reaberto, already_open) |
| SIGN-03 | 03-01, 03-02, 03-03 | PRECO ABAIXO HISTORICO: LOW + preco < media de 14 snapshots, urgencia MEDIA | SATISFIED | `_check_preco_abaixo_historico` com `_get_avg_price_last_n`; 4 testes passam (happy, above_avg, insufficient_history, not_low) |
| SIGN-04 | 03-01, 03-02, 03-03 | JANELA OTIMA: faixa ideal (21-90 domestico, 30-120 internacional), urgencia MEDIA | SATISFIED | `_check_janela_otima` com DOMESTIC_WINDOW/INTERNATIONAL_WINDOW; 4 testes passam com mock de date.today() |
| SIGN-05 | 03-01, 03-02, 03-03 | Deduplicacao 12h: mesmo sinal para mesma rota nao re-emitido dentro de 12h | SATISFIED | `_is_duplicate` com timedelta(hours=12); 3 testes passam (bloqueia, permite_apos_12h, different_route) |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `app/services/signal_service.py` | 124 | `datetime.utcnow()` (deprecated desde Python 3.12) | Warning | Fallback apenas ativo quando `snapshot.collected_at is None`; como o campo tem `server_default=func.now()` e e populado pelo SQLAlchemy apos flush, esse caminho nao e atingido em pratica. Nao afeta o comportamento. |

Nenhum blocker encontrado. Sem `print()`, `TODO`, `FIXME`, `raise NotImplementedError` ou retornos estaticos vazios no codigo de producao.

---

### Human Verification Required

#### 1. Deteccao de sinais em ciclo de polling real

**Test:** Configurar credenciais Amadeus reais no `.env`, ativar um RouteGroup com rota ativa, disparar `run_polling_cycle()` manualmente ou aguardar o scheduler (6h) e inspecionar os logs.
**Expected:** Mensagens como `Signal detected: JANELA_OTIMA (MEDIA) for GRU->GIG 2026-08-15` aparecem no log para rotas com datas de embarque dentro da janela ideal.
**Why human:** Requer API Amadeus configurada com credenciais validas e dados de voo ao vivo. Os testes automatizados cobrem toda a logica com dados mockados — a verificacao end-to-end em producao so pode ser feita manualmente.

---

### Gaps Summary

Nenhum gap encontrado. Todos os 5 criterios de sucesso estao implementados, testados e verificados. O item de verificacao humana nao bloqueia o avanco para a Phase 4, pois representa validacao de integracao com API externa, nao uma lacuna de implementacao.

---

## Nota Tecnica: Deduplicacao e `collected_at`

O mecanismo de deduplicacao usa `snapshot.collected_at` como tempo de referencia em vez de `datetime.now(timezone.utc)`. Isso e correto e intencional: garante comportamento deterministico nos testes (onde `collected_at` e definido explicitamente) e evita race conditions em producao. O fallback `datetime.utcnow()` na linha 124 e defensivo e nunca alcancado no fluxo normal.

---

_Verified: 2026-03-25T04:45:00Z_
_Verifier: Claude (gsd-verifier)_
