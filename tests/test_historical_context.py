"""Contexto historico de preco no alerta (Phase 22)."""
import datetime
from datetime import date

from app.models import FlightSnapshot, RouteGroup
from app.services.alert_service import _format_historical_context
from app.services.snapshot_service import get_historical_price_context


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


def _make_snap(db, rg, price, days_ago=5):
    snap = FlightSnapshot(
        route_group_id=rg.id,
        origin="GRU",
        destination="LIS",
        departure_date=date(2026, 7, 10),
        return_date=date(2026, 7, 17),
        price=price,
        currency="BRL",
        airline="LATAM",
        collected_at=datetime.datetime.utcnow() - datetime.timedelta(days=days_ago),
    )
    db.add(snap)
    db.commit()


def test_historical_context_returns_none_when_few_samples(db):
    rg = _make_group(db)
    for _ in range(5):
        _make_snap(db, rg, 3000.0)

    result = get_historical_price_context(db, "GRU", "LIS", min_samples=10)
    assert result is None


def test_historical_context_returns_stats_when_enough_samples(db):
    rg = _make_group(db)
    for i in range(15):
        _make_snap(db, rg, 3000.0 + i * 100)

    result = get_historical_price_context(db, "GRU", "LIS", min_samples=10)
    assert result is not None
    assert result["count"] == 15
    assert result["min"] == 3000.0
    assert result["max"] == 4400.0
    assert 3500 < result["avg"] < 3900


def test_format_historical_below_average():
    ctx = {"avg": 4000.0, "min": 3000.0, "max": 5000.0, "count": 20, "days": 90}
    phrase = _format_historical_context(ctx, current_price=3000.0)
    assert "abaixo" in phrase
    assert "25%" in phrase


def test_format_historical_above_average():
    ctx = {"avg": 4000.0, "min": 3000.0, "max": 5000.0, "count": 20, "days": 90}
    phrase = _format_historical_context(ctx, current_price=4800.0)
    assert "acima" in phrase
    assert "20%" in phrase


def test_format_historical_in_line_when_close():
    ctx = {"avg": 4000.0, "min": 3500.0, "max": 4500.0, "count": 20, "days": 90}
    phrase = _format_historical_context(ctx, current_price=4050.0)
    assert "linha" in phrase.lower()


def test_format_historical_none_ctx_returns_empty():
    assert _format_historical_context(None, 3000.0) == ""
