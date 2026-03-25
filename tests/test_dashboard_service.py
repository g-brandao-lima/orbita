import datetime
from datetime import timedelta

from app.models import RouteGroup, FlightSnapshot, DetectedSignal
from app.services.dashboard_service import (
    get_groups_with_summary,
    get_price_history,
    format_price_brl,
)


def _make_group(db, name="Test Group", group_id=None, **kwargs):
    defaults = dict(
        name=name,
        origins=["GRU"],
        destinations=["LIS"],
        duration_days=10,
        travel_start=datetime.date(2026, 5, 1),
        travel_end=datetime.date(2026, 5, 31),
        is_active=True,
    )
    defaults.update(kwargs)
    group = RouteGroup(**defaults)
    if group_id is not None:
        group.id = group_id
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def _make_snapshot(db, group, price=3000.0, origin="GRU", destination="LIS",
                   collected_at=None, **kwargs):
    if collected_at is None:
        collected_at = datetime.datetime(2026, 3, 20, 12, 0)
    defaults = dict(
        route_group_id=group.id,
        origin=origin,
        destination=destination,
        departure_date=datetime.date(2026, 5, 10),
        return_date=datetime.date(2026, 5, 20),
        price=price,
        currency="BRL",
        airline="LA",
        collected_at=collected_at,
    )
    defaults.update(kwargs)
    snap = FlightSnapshot(**defaults)
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


def _make_signal(db, group, snapshot, urgency="MEDIA", detected_at=None, **kwargs):
    if detected_at is None:
        detected_at = datetime.datetime.utcnow()
    defaults = dict(
        route_group_id=group.id,
        flight_snapshot_id=snapshot.id,
        origin=snapshot.origin,
        destination=snapshot.destination,
        departure_date=snapshot.departure_date,
        return_date=snapshot.return_date,
        signal_type="BALDE_FECHANDO",
        urgency=urgency,
        details="Test signal",
        price_at_detection=snapshot.price,
        detected_at=detected_at,
    )
    defaults.update(kwargs)
    signal = DetectedSignal(**defaults)
    db.add(signal)
    db.commit()
    db.refresh(signal)
    return signal


# --- get_groups_with_summary tests ---

def test_get_groups_with_summary_returns_all_groups(db):
    _make_group(db, name="Group A")
    _make_group(db, name="Group B")

    result = get_groups_with_summary(db)

    assert len(result) == 2
    for item in result:
        assert "group" in item
        assert "cheapest_snapshot" in item
        assert "signal" in item


def test_get_groups_with_summary_includes_cheapest_price(db):
    group = _make_group(db)
    now = datetime.datetime(2026, 3, 20, 12, 0)
    _make_snapshot(db, group, price=5000.0, collected_at=now)
    _make_snapshot(db, group, price=3000.0, collected_at=now)

    result = get_groups_with_summary(db)

    assert result[0]["cheapest_snapshot"] is not None
    assert result[0]["cheapest_snapshot"].price == 3000.0


def test_get_groups_with_summary_includes_most_urgent_signal(db):
    group = _make_group(db)
    snap = _make_snapshot(db, group)
    now = datetime.datetime.utcnow()
    _make_signal(db, group, snap, urgency="MEDIA", detected_at=now)
    _make_signal(db, group, snap, urgency="ALTA", detected_at=now)

    result = get_groups_with_summary(db)

    assert result[0]["signal"] is not None
    assert result[0]["signal"].urgency == "ALTA"


def test_get_groups_with_summary_no_snapshots(db):
    _make_group(db)

    result = get_groups_with_summary(db)

    assert result[0]["cheapest_snapshot"] is None


def test_get_groups_with_summary_no_signals(db):
    group = _make_group(db)
    _make_snapshot(db, group)

    result = get_groups_with_summary(db)

    assert result[0]["signal"] is None


def test_get_groups_with_summary_old_signal_ignored(db):
    group = _make_group(db)
    snap = _make_snapshot(db, group)
    old_time = datetime.datetime.utcnow() - timedelta(hours=13)
    _make_signal(db, group, snap, urgency="ALTA", detected_at=old_time)

    result = get_groups_with_summary(db)

    assert result[0]["signal"] is None


# --- get_price_history tests ---

def test_get_price_history_returns_labels_and_prices(db):
    group = _make_group(db)
    for i in range(3):
        collected = datetime.datetime(2026, 3, 18 + i, 10, 0)
        _make_snapshot(db, group, price=3000.0 + i * 100, collected_at=collected)

    result = get_price_history(db, group.id)

    assert len(result["labels"]) == 3
    assert len(result["prices"]) == 3
    assert result["labels"][0] == "18/03 10h"
    assert result["prices"][0] == 3000.0


def test_get_price_history_filters_cheapest_route(db):
    group = _make_group(db)
    now = datetime.datetime(2026, 3, 20, 12, 0)
    # Expensive route
    _make_snapshot(db, group, price=8000.0, origin="GRU", destination="CDG",
                   collected_at=now)
    # Cheap route
    _make_snapshot(db, group, price=2500.0, origin="GRU", destination="LIS",
                   collected_at=now)

    result = get_price_history(db, group.id)

    assert "GRU" in result["route"]
    assert "LIS" in result["route"]
    assert result["prices"][0] == 2500.0


def test_get_price_history_empty_group(db):
    group = _make_group(db)

    result = get_price_history(db, group.id)

    assert result == {"labels": [], "prices": [], "route": ""}


def test_get_price_history_respects_14_day_cutoff(db):
    group = _make_group(db)
    old = datetime.datetime.utcnow() - timedelta(days=15)
    recent = datetime.datetime.utcnow() - timedelta(days=13)
    _make_snapshot(db, group, price=3000.0, collected_at=old)
    _make_snapshot(db, group, price=3500.0, collected_at=recent)

    result = get_price_history(db, group.id)

    assert len(result["prices"]) == 1
    assert result["prices"][0] == 3500.0


# --- format_price_brl tests ---

def test_format_price_brl(db):
    assert format_price_brl(3500.0) == "R$ 3.500,00"
    assert format_price_brl(123.5) == "R$ 123,50"
