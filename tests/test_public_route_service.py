"""Testes do public_route_service (Phase 33 Plan 01)."""
import datetime
from datetime import timedelta

import pytest

from app.models import FlightSnapshot, RouteCache, RouteGroup
from app.services import public_route_service


def _make_group(db, user_id):
    g = RouteGroup(
        user_id=user_id, name="Seed", origins=["GRU"], destinations=["LIS"],
        duration_days=10, travel_start=datetime.date(2026, 9, 1),
        travel_end=datetime.date(2026, 9, 30), is_active=True,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


def _seed_snapshot(db, group_id, days_ago, price, origin="GRU", destination="LIS"):
    snap = FlightSnapshot(
        route_group_id=group_id,
        origin=origin, destination=destination,
        departure_date=datetime.date(2026, 9, 1),
        return_date=datetime.date(2026, 9, 15),
        price=price, currency="BRL", airline="TP",
        collected_at=datetime.datetime.utcnow() - timedelta(days=days_ago),
    )
    db.add(snap)
    db.commit()
    return snap


def _seed_cache(db, origin="GRU", destination="LIS", min_price=2500.0):
    entry = RouteCache(
        origin=origin, destination=destination,
        departure_date=datetime.date(2026, 9, 1),
        return_date=datetime.date(2026, 9, 15),
        min_price=min_price, currency="BRL",
        cached_at=datetime.datetime.utcnow(),
        source="travelpayouts",
    )
    db.add(entry)
    db.commit()
    return entry


def test_get_route_stats_returns_none_when_no_data(db):
    assert public_route_service.get_route_stats(db, "ZZZ", "YYY") is None


def test_get_route_stats_returns_data_with_cache_only(db):
    _seed_cache(db, min_price=2500.0)

    result = public_route_service.get_route_stats(db, "GRU", "LIS")

    assert result is not None
    assert result["current_price"] == 2500.0
    assert result["origin_city"] == "Sao Paulo"
    assert result["destination_city"] == "Lisboa"


def test_get_route_stats_with_snapshots_and_cache(db, test_user):
    group = _make_group(db, test_user.id)
    for i, price in enumerate([2800, 2900, 3000, 2700, 2600, 2750, 2850, 2950, 2650, 2800, 3100, 3050]):
        _seed_snapshot(db, group.id, days_ago=i * 15, price=float(price))
    _seed_cache(db, min_price=2500.0)

    result = public_route_service.get_route_stats(db, "GRU", "LIS")

    assert result["current_price"] == 2500.0
    assert result["snapshot_count"] >= 10
    assert result["median_180d"] is not None
    assert len(result["best_months"]) > 0
    assert len(result["monthly_series"]) > 0


def test_has_enough_data_true_when_threshold_met(db, test_user):
    group = _make_group(db, test_user.id)
    for i in range(10):
        _seed_snapshot(db, group.id, days_ago=i, price=2800.0)

    assert public_route_service.has_enough_data(db, "GRU", "LIS") is True


def test_has_enough_data_false_when_below_threshold(db, test_user):
    group = _make_group(db, test_user.id)
    for i in range(5):
        _seed_snapshot(db, group.id, days_ago=i, price=2800.0)

    assert public_route_service.has_enough_data(db, "GRU", "LIS") is False


def test_get_route_stats_does_not_call_external_apis(db, monkeypatch):
    """Critico: pagina publica nao pode disparar SerpAPI/Travelpayouts."""
    def _fail(*a, **kw):
        raise AssertionError("External API should NOT be called in public route")

    monkeypatch.setattr("app.services.flight_search.search_flights_ex", _fail)
    monkeypatch.setattr(
        "app.services.travelpayouts_client.TravelpayoutsClient.fetch_calendar",
        _fail,
    )

    _seed_cache(db)
    result = public_route_service.get_route_stats(db, "GRU", "LIS")
    assert result is not None
