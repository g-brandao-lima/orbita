"""Internal linking pra SEO (Phase 33 Plan 03)."""
import datetime
from datetime import timedelta

import pytest

from app.models import FlightSnapshot, RouteGroup
from app.services import public_route_service


def _seed_route(db, user_id, origin, destination, count):
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
            price=2800.0, currency="BRL", airline="TP",
            collected_at=datetime.datetime.utcnow() - timedelta(days=i),
        ))
    db.commit()
    return g


def test_get_top_public_routes_filters_by_threshold(db, test_user):
    _seed_route(db, test_user.id, "GRU", "LIS", count=50)
    _seed_route(db, test_user.id, "CGH", "SDU", count=30)
    _seed_route(db, test_user.id, "GRU", "GIG", count=15)
    _seed_route(db, test_user.id, "GRU", "FOR", count=5)

    routes = public_route_service.get_top_public_routes(db, limit=5)

    assert len(routes) == 3
    pairs = [(r["origin"], r["destination"]) for r in routes]
    assert pairs[0] == ("GRU", "LIS")
    assert pairs[1] == ("CGH", "SDU")
    assert pairs[2] == ("GRU", "GIG")


def test_get_top_public_routes_respects_limit(db, test_user):
    _seed_route(db, test_user.id, "GRU", "LIS", count=50)
    _seed_route(db, test_user.id, "CGH", "SDU", count=30)
    _seed_route(db, test_user.id, "GRU", "GIG", count=15)

    routes = public_route_service.get_top_public_routes(db, limit=2)

    assert len(routes) == 2


def test_get_top_public_routes_empty_db(db):
    assert public_route_service.get_top_public_routes(db) == []


def test_landing_shows_popular_routes_links(unauthenticated_client, db, test_user):
    _seed_route(db, test_user.id, "GRU", "LIS", count=50)
    _seed_route(db, test_user.id, "GRU", "FOR", count=5)

    r = unauthenticated_client.get("/")

    assert r.status_code == 200
    assert "/rotas/GRU-LIS" in r.text
    assert "Rotas populares" in r.text
    assert "/rotas/GRU-FOR" not in r.text
