"""Open Graph image dinamica (Phase 33 Plan 02)."""
import datetime
from datetime import timedelta
from io import BytesIO

import pytest
from PIL import Image

from app.models import FlightSnapshot, RouteCache, RouteGroup
from app.services.public_share_card_service import build_public_og_card


def _seed(db, user_id):
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
            price=2800.0, currency="BRL", airline="TP",
            collected_at=datetime.datetime.utcnow() - timedelta(days=i),
        ))
    db.add(RouteCache(
        origin="GRU", destination="LIS",
        departure_date=datetime.date(2026, 9, 1),
        return_date=datetime.date(2026, 9, 15),
        min_price=2500.0, currency="BRL",
        cached_at=datetime.datetime.utcnow(), source="travelpayouts",
    ))
    db.commit()


def test_build_public_og_card_returns_png_bytes():
    png = build_public_og_card(
        origin="GRU", dest="LIS",
        current_price=2500.0, median_180d=2800.0,
        origin_city="Sao Paulo", dest_city="Lisboa",
    )
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    img = Image.open(BytesIO(png))
    assert img.size == (1200, 630)


def test_build_public_og_card_no_price():
    png = build_public_og_card(
        origin="XXX", dest="YYY",
        current_price=None, median_180d=None,
        origin_city="XXX", dest_city="YYY",
    )
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_og_image_endpoint_returns_png(unauthenticated_client, db, test_user):
    _seed(db, test_user.id)

    r = unauthenticated_client.get("/rotas/GRU-LIS/og-image.png")

    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_og_image_endpoint_cache_control(unauthenticated_client, db, test_user):
    _seed(db, test_user.id)

    r = unauthenticated_client.get("/rotas/GRU-LIS/og-image.png")

    assert "public" in r.headers["Cache-Control"]


def test_og_image_404_when_no_data(unauthenticated_client, db):
    r = unauthenticated_client.get("/rotas/ZZZ-YYY/og-image.png")
    assert r.status_code == 404
