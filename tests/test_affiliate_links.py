"""Affiliate links Aviasales (Phase 33 Plan 02)."""
import datetime

from app.services.affiliate_links import (
    build_aviasales_url,
    default_trip_dates,
)


def test_build_aviasales_url_format():
    url = build_aviasales_url(
        "GRU", "LIS",
        datetime.date(2026, 6, 15),
        datetime.date(2026, 6, 30),
        marker="714304",
    )
    assert url.startswith("https://www.aviasales.com/search/")
    assert "GRU1506LIS3006" in url
    assert "marker=714304" in url


def test_build_aviasales_url_no_marker_when_empty():
    url = build_aviasales_url(
        "GRU", "LIS",
        datetime.date(2026, 6, 15),
        datetime.date(2026, 6, 30),
        marker="",
    )
    assert "marker=" not in url


def test_build_aviasales_url_normalizes_case():
    url = build_aviasales_url(
        "gru", "lis",
        datetime.date(2026, 6, 15),
        datetime.date(2026, 6, 30),
        marker="X",
    )
    assert "GRU1506LIS3006" in url


def test_default_trip_dates_returns_future_tuple():
    today = datetime.date(2026, 4, 21)
    dep, ret = default_trip_dates(today=today)
    assert dep == datetime.date(2026, 6, 20)
    assert ret == datetime.date(2026, 6, 30)
