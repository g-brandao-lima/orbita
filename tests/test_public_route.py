"""Rota publica /rotas/{ORIG}-{DEST} + /robots.txt (Phase 33 Plan 01)."""
import datetime
from datetime import timedelta

import pytest

from app.models import FlightSnapshot, RouteCache, RouteGroup


def _seed_route(db, user_id):
    g = RouteGroup(
        user_id=user_id, name="Seed", origins=["GRU"], destinations=["LIS"],
        duration_days=10, travel_start=datetime.date(2026, 9, 1),
        travel_end=datetime.date(2026, 9, 30), is_active=True,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    for i in range(12):
        db.add(FlightSnapshot(
            route_group_id=g.id, origin="GRU", destination="LIS",
            departure_date=datetime.date(2026, 9, 1),
            return_date=datetime.date(2026, 9, 15),
            price=2800.0 + i * 10, currency="BRL", airline="TP",
            collected_at=datetime.datetime.utcnow() - timedelta(days=i * 5),
        ))
    db.add(RouteCache(
        origin="GRU", destination="LIS",
        departure_date=datetime.date(2026, 9, 1),
        return_date=datetime.date(2026, 9, 15),
        min_price=2500.0, currency="BRL",
        cached_at=datetime.datetime.utcnow(), source="travelpayouts",
    ))
    db.commit()
    return g


def test_public_route_returns_200_with_seeded_data(unauthenticated_client, db, test_user):
    _seed_route(db, test_user.id)

    r = unauthenticated_client.get("/rotas/GRU-LIS")

    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


def test_public_route_html_contains_cities_and_price(unauthenticated_client, db, test_user):
    _seed_route(db, test_user.id)

    r = unauthenticated_client.get("/rotas/GRU-LIS")

    assert "GRU" in r.text
    assert "LIS" in r.text
    assert "Sao Paulo" in r.text
    assert "Lisboa" in r.text
    assert "R$" in r.text
    assert "Monitore essa rota" in r.text
    assert "/auth/login" in r.text


def test_public_route_has_canonical_and_og_tags(unauthenticated_client, db, test_user):
    _seed_route(db, test_user.id)

    r = unauthenticated_client.get("/rotas/GRU-LIS")

    assert '<link rel="canonical"' in r.text
    assert "/rotas/GRU-LIS" in r.text
    assert 'property="og:image"' in r.text
    assert 'name="twitter:card"' in r.text


def test_public_route_has_cache_control_header(unauthenticated_client, db, test_user):
    _seed_route(db, test_user.id)

    r = unauthenticated_client.get("/rotas/GRU-LIS")

    assert r.headers.get("Cache-Control") == "public, max-age=21600"


def test_public_route_404_when_no_data(unauthenticated_client, db):
    r = unauthenticated_client.get("/rotas/ZZZ-YYY")
    assert r.status_code == 404


def test_public_route_404_for_invalid_format(unauthenticated_client, db):
    r = unauthenticated_client.get("/rotas/invalid")
    assert r.status_code == 404


def test_public_route_accepts_lowercase(unauthenticated_client, db, test_user):
    _seed_route(db, test_user.id)

    r = unauthenticated_client.get("/rotas/gru-lis")

    assert r.status_code == 200


def test_robots_txt_returns_valid_content(unauthenticated_client):
    r = unauthenticated_client.get("/robots.txt")

    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]
    assert "User-agent: *" in r.text
    assert "Allow: /rotas/" in r.text
    assert "Sitemap:" in r.text
    assert "sitemap.xml" in r.text
