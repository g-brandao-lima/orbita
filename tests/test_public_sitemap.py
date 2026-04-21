"""Sitemap.xml dinamico (Phase 33 Plan 02)."""
import datetime
import xml.etree.ElementTree as ET
from datetime import timedelta

import pytest

from app.models import FlightSnapshot, RouteGroup


def _seed_group(db, user_id, origin, destination, count):
    g = RouteGroup(
        user_id=user_id, name=f"{origin}-{destination}",
        origins=[origin], destinations=[destination],
        duration_days=10, travel_start=datetime.date(2026, 9, 1),
        travel_end=datetime.date(2026, 9, 30), is_active=True,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    for i in range(count):
        db.add(FlightSnapshot(
            route_group_id=g.id, origin=origin, destination=destination,
            departure_date=datetime.date(2026, 9, 1),
            return_date=datetime.date(2026, 9, 15),
            price=2800.0 + i, currency="BRL", airline="TP",
            collected_at=datetime.datetime.utcnow() - timedelta(days=i),
        ))
    db.commit()


def test_sitemap_returns_xml(unauthenticated_client, db, test_user):
    _seed_group(db, test_user.id, "GRU", "LIS", count=15)

    r = unauthenticated_client.get("/sitemap.xml")

    assert r.status_code == 200
    assert "xml" in r.headers["content-type"]


def test_sitemap_lists_routes_above_threshold(unauthenticated_client, db, test_user):
    _seed_group(db, test_user.id, "GRU", "LIS", count=15)
    _seed_group(db, test_user.id, "CGH", "SDU", count=12)
    _seed_group(db, test_user.id, "GRU", "GIG", count=5)

    r = unauthenticated_client.get("/sitemap.xml")

    root = ET.fromstring(r.text)
    locs = [elem.text for elem in root.iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert any("/rotas/GRU-LIS" in loc for loc in locs)
    assert any("/rotas/CGH-SDU" in loc for loc in locs)
    assert not any("/rotas/GRU-GIG" in loc for loc in locs)


def test_sitemap_has_cache_control(unauthenticated_client, db, test_user):
    _seed_group(db, test_user.id, "GRU", "LIS", count=15)

    r = unauthenticated_client.get("/sitemap.xml")

    assert r.headers.get("Cache-Control") == "public, max-age=3600"
