"""Card PNG compartilhavel de preco (Phase 30)."""
import datetime
from datetime import date
from io import BytesIO

from PIL import Image

from app.models import FlightSnapshot, RouteGroup
from app.services.share_card_service import build_price_card


def _make_group(db, user_id, name="Europa Verao"):
    rg = RouteGroup(
        user_id=user_id,
        name=name,
        origins=["GRU"],
        destinations=["LIS"],
        duration_days=7,
        travel_start=date(2026, 7, 1),
        travel_end=date(2026, 7, 31),
        is_active=True,
        passengers=2,
    )
    db.add(rg)
    db.commit()
    return rg


def _make_snap(db, rg, price=3500.0):
    s = FlightSnapshot(
        route_group_id=rg.id,
        origin="GRU",
        destination="LIS",
        departure_date=date(2026, 7, 10),
        return_date=date(2026, 7, 17),
        price=price,
        currency="BRL",
        airline="LATAM",
        price_classification="LOW",
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def test_build_price_card_returns_valid_png(db, test_user):
    rg = _make_group(db, test_user.id)
    snap = _make_snap(db, rg)
    png_bytes = build_price_card(group=rg, snapshot=snap, passengers=2)

    assert png_bytes.startswith(b"\x89PNG")
    img = Image.open(BytesIO(png_bytes))
    assert img.size == (1200, 630)
    assert img.format == "PNG"


def test_build_price_card_accepts_historical_context(db, test_user):
    rg = _make_group(db, test_user.id)
    snap = _make_snap(db, rg, price=3000.0)
    ctx = {"avg": 4000.0, "min": 3000.0, "max": 5000.0, "count": 20, "days": 90}

    png_bytes = build_price_card(group=rg, snapshot=snap, historical_ctx=ctx, passengers=1)
    assert png_bytes.startswith(b"\x89PNG")


def test_share_card_endpoint_returns_png(client, test_user, db):
    rg = _make_group(db, test_user.id)
    _make_snap(db, rg)
    response = client.get(f"/groups/{rg.id}/share-card.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content.startswith(b"\x89PNG")


def test_share_card_returns_404_for_other_user_group(client, db, test_user, second_user):
    rg = _make_group(db, second_user.id, name="Nao minha")
    _make_snap(db, rg)
    response = client.get(f"/groups/{rg.id}/share-card.png")
    assert response.status_code == 404


def test_share_card_returns_404_without_snapshot(client, test_user, db):
    rg = _make_group(db, test_user.id)
    response = client.get(f"/groups/{rg.id}/share-card.png")
    assert response.status_code == 404
