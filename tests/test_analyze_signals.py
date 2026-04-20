"""Script de analise empirica de sinais (Phase 23)."""
import datetime
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.analyze_signals import analyze  # noqa: E402

from app.models import DetectedSignal, FlightSnapshot, RouteGroup  # noqa: E402


def _make_group(db):
    rg = RouteGroup(
        name="Test",
        origins=["GRU"],
        destinations=["LIS"],
        duration_days=7,
        travel_start=date(2026, 7, 1),
        travel_end=date(2026, 7, 31),
        is_active=True,
    )
    db.add(rg)
    db.commit()
    return rg


def test_analyze_returns_zero_when_no_signals(db):
    result = analyze(db)
    assert result["total_signals"] == 0


def test_analyze_classifies_low_price_signal_correctly(db):
    rg = _make_group(db)

    detected_at = datetime.datetime(2026, 4, 1, 10, 0)
    snap = FlightSnapshot(
        route_group_id=rg.id,
        origin="GRU",
        destination="LIS",
        departure_date=date(2026, 7, 10),
        return_date=date(2026, 7, 17),
        price=3000.0,
        currency="BRL",
        airline="LATAM",
        collected_at=detected_at,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)

    signal = DetectedSignal(
        route_group_id=rg.id,
        flight_snapshot_id=snap.id,
        origin="GRU",
        destination="LIS",
        departure_date=date(2026, 7, 10),
        return_date=date(2026, 7, 17),
        signal_type="LOW_PRICE_DETECTED",
        urgency="MEDIA",
        details="low",
        price_at_detection=3000.0,
        detected_at=detected_at,
    )
    db.add(signal)
    db.commit()

    # Snapshots posteriores com preco subindo (sinal teria acertado)
    for days_later, price in [(2, 3300.0), (5, 3500.0), (10, 3600.0)]:
        s = FlightSnapshot(
            route_group_id=rg.id,
            origin="GRU",
            destination="LIS",
            departure_date=date(2026, 7, 10),
            return_date=date(2026, 7, 17),
            price=price,
            currency="BRL",
            airline="LATAM",
            collected_at=detected_at + datetime.timedelta(days=days_later),
        )
        db.add(s)
    db.commit()

    result = analyze(db)
    assert result["total_signals"] == 1
    low_price_stats = result["by_type"].get("LOW_PRICE_DETECTED")
    assert low_price_stats is not None
    assert low_price_stats["hit_rate_7d"] == 1.0
    assert low_price_stats["avg_delta_7d_pct"] > 0
