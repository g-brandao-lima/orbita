"""Analise empirica dos sinais detectados (Phase 23).

Objetivo: medir se os sinais emitidos realmente preveem variacao de preco.
Para cada DetectedSignal no banco:
- Busca snapshots da mesma rota nos 3/7/14 dias apos a deteccao
- Calcula delta percentual do preco medio nesses periodos

Uso:
    DATABASE_URL=postgresql://... python scripts/analyze_signals.py

Saida: tabela console + JSON com metricas.
"""
import datetime
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.database import SessionLocal  # noqa: E402
from app.models import DetectedSignal, FlightSnapshot  # noqa: E402


def analyze(db) -> dict:
    signals = db.query(DetectedSignal).all()
    if not signals:
        return {"total_signals": 0, "note": "Banco sem sinais detectados ainda"}

    by_type: dict[str, list[dict]] = defaultdict(list)
    for signal in signals:
        record = _evaluate(db, signal)
        if record:
            by_type[signal.signal_type].append(record)

    summary: dict = {
        "total_signals": len(signals),
        "signals_evaluated": sum(len(v) for v in by_type.values()),
        "by_type": {},
    }

    for signal_type, records in by_type.items():
        deltas_3 = [r["delta_pct_3d"] for r in records if r["delta_pct_3d"] is not None]
        deltas_7 = [r["delta_pct_7d"] for r in records if r["delta_pct_7d"] is not None]
        deltas_14 = [r["delta_pct_14d"] for r in records if r["delta_pct_14d"] is not None]

        hits_3 = _hit_rate(records, "delta_pct_3d", signal_type)
        hits_7 = _hit_rate(records, "delta_pct_7d", signal_type)

        summary["by_type"][signal_type] = {
            "count": len(records),
            "avg_delta_3d_pct": _safe_mean(deltas_3),
            "avg_delta_7d_pct": _safe_mean(deltas_7),
            "avg_delta_14d_pct": _safe_mean(deltas_14),
            "hit_rate_3d": hits_3,
            "hit_rate_7d": hits_7,
        }

    return summary


def _evaluate(db, signal: DetectedSignal) -> dict | None:
    baseline = signal.price_at_detection
    if baseline is None or baseline <= 0:
        return None

    future_windows = {
        "3d": signal.detected_at + datetime.timedelta(days=3),
        "7d": signal.detected_at + datetime.timedelta(days=7),
        "14d": signal.detected_at + datetime.timedelta(days=14),
    }

    record: dict = {"signal_id": signal.id}
    for label, cutoff in future_windows.items():
        snaps = (
            db.query(FlightSnapshot.price)
            .filter(
                FlightSnapshot.origin == signal.origin,
                FlightSnapshot.destination == signal.destination,
                FlightSnapshot.collected_at > signal.detected_at,
                FlightSnapshot.collected_at <= cutoff,
            )
            .all()
        )
        prices = [s[0] for s in snaps if s[0] is not None and s[0] > 0]
        if not prices:
            record[f"delta_pct_{label}"] = None
            continue
        mean_future = statistics.mean(prices)
        delta_pct = (mean_future - baseline) / baseline * 100
        record[f"delta_pct_{label}"] = delta_pct

    return record


def _hit_rate(records: list[dict], key: str, signal_type: str) -> float | None:
    """% de casos em que o sinal acertou a direcao esperada.

    Para sinais de 'buy now' (LOW_PRICE, BALDE_FECHANDO): acerto = preco SUBIU.
    Para sinais informativos: acerto = preco se manteve ou subiu (nao caiu > 10%).
    """
    buy_signals = {"LOW_PRICE_DETECTED", "BALDE_FECHANDO", "BALDE_REABERTO"}
    considered = [r for r in records if r.get(key) is not None]
    if not considered:
        return None
    if signal_type in buy_signals:
        hits = sum(1 for r in considered if r[key] > 0)
    else:
        hits = sum(1 for r in considered if r[key] > -10)
    return hits / len(considered)


def _safe_mean(values: list[float]) -> float | None:
    return statistics.mean(values) if values else None


def main():
    db = SessionLocal()
    try:
        result = analyze(db)
        print(json.dumps(result, indent=2, default=str))
    finally:
        db.close()


if __name__ == "__main__":
    main()
