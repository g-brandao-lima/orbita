"""Testes do modelo RouteCache + settings travelpayouts_token (Phase 32 Plan 01)."""
import datetime

import pytest

from app.config import Settings
from app.models import RouteCache


def test_route_cache_insert_and_query(db):
    entry = RouteCache(
        origin="GRU",
        destination="LIS",
        departure_date=datetime.date(2026, 9, 1),
        return_date=datetime.date(2026, 9, 15),
        min_price=2800.50,
        currency="BRL",
        source="travelpayouts",
    )
    db.add(entry)
    db.commit()

    found = (
        db.query(RouteCache)
        .filter(RouteCache.origin == "GRU", RouteCache.destination == "LIS")
        .one()
    )
    assert found.min_price == 2800.50
    assert found.currency == "BRL"
    assert found.source == "travelpayouts"


def test_route_cache_index_lookup(db):
    for dep in (datetime.date(2026, 9, 1), datetime.date(2026, 10, 1), datetime.date(2026, 11, 1)):
        db.add(
            RouteCache(
                origin="GRU",
                destination="LIS",
                departure_date=dep,
                return_date=dep + datetime.timedelta(days=10),
                min_price=3000.0,
            )
        )
    db.commit()

    found = (
        db.query(RouteCache)
        .filter(
            RouteCache.origin == "GRU",
            RouteCache.destination == "LIS",
            RouteCache.departure_date == datetime.date(2026, 10, 1),
        )
        .all()
    )
    assert len(found) == 1


def test_route_cache_nullable_return_date(db):
    entry = RouteCache(
        origin="GRU",
        destination="LIS",
        departure_date=datetime.date(2026, 9, 1),
        return_date=None,
        min_price=1500.0,
    )
    db.add(entry)
    db.commit()

    found = db.query(RouteCache).one()
    assert found.return_date is None


def test_settings_travelpayouts_token():
    s = Settings(travelpayouts_token="abc123")
    assert s.travelpayouts_token == "abc123"


def test_settings_travelpayouts_token_default_empty(monkeypatch):
    monkeypatch.delenv("TRAVELPAYOUTS_TOKEN", raising=False)
    s = Settings(_env_file=None)
    assert s.travelpayouts_token == ""
