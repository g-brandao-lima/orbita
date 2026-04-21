"""Integracao route_cache em search_flights_ex (Phase 32 Plan 03)."""
import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models import RouteCache
from app.services import flight_cache
from app.services.flight_search import search_flights_ex


@pytest.fixture(autouse=True)
def _reset_cache():
    flight_cache.clear()
    yield
    flight_cache.clear()


@patch("app.services.flight_search.SessionLocal")
@patch("app.services.flight_search.SerpApiClient")
def test_search_flights_ex_route_cache_hit_returns_synthetic_flight(
    mock_serp_cls, mock_session_local, db
):
    entry = RouteCache(
        origin="GRU",
        destination="LIS",
        departure_date=datetime.date(2026, 9, 1),
        return_date=datetime.date(2026, 9, 15),
        min_price=2500.0,
        currency="BRL",
        cached_at=datetime.datetime.utcnow(),
        source="travelpayouts",
    )
    db.add(entry)
    db.commit()
    mock_session_local.return_value = db

    flights, insights, source, was_cache_hit = search_flights_ex(
        "GRU", "LIS", "2026-09-01", "2026-09-15"
    )

    assert source == "travelpayouts_cached"
    assert was_cache_hit is True
    assert flights[0]["price"] == 2500.0
    mock_serp_cls.assert_not_called()


@patch("app.services.flight_search.SessionLocal")
@patch("app.services.flight_search.SerpApiClient")
def test_search_flights_ex_route_cache_miss_falls_back_to_serpapi(
    mock_serp_cls, mock_session_local, db
):
    mock_session_local.return_value = db
    mock_client = MagicMock()
    mock_client.search_flights_with_insights.return_value = (
        [{"price": 3200.0, "airline": "LA", "flights": [], "type": "Round trip"}],
        {"lowest_price": 3000},
    )
    mock_serp_cls.return_value = mock_client

    flights, insights, source, was_cache_hit = search_flights_ex(
        "GRU", "LIS", "2026-09-01", "2026-09-15"
    )

    assert source == "serpapi"
    assert was_cache_hit is False
    assert flights[0]["price"] == 3200.0
    mock_serp_cls.assert_called_once()
