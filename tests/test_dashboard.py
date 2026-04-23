import datetime
from datetime import timedelta

from app.models import RouteGroup, FlightSnapshot, DetectedSignal


def _make_group(db, name="Test Group", **kwargs):
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


# --- Index page tests ---

def test_index_returns_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_index_shows_group_names(client, db, test_user):
    _make_group(db, name="Europa Verao", user_id=test_user.id)
    _make_group(db, name="Asia Inverno", user_id=test_user.id)

    response = client.get("/")

    assert "Europa Verao" in response.text
    assert "Asia Inverno" in response.text


def test_index_shows_cheapest_price(client, db, test_user):
    group = _make_group(db, user_id=test_user.id)
    _make_snapshot(db, group, price=3500.0)

    response = client.get("/")

    assert "R$ 3.500,00" in response.text


def test_index_shows_signal_badge_alta(client, db, test_user):
    group = _make_group(db, user_id=test_user.id)
    snap = _make_snapshot(db, group)
    _make_signal(db, group, snap, urgency="ALTA")

    response = client.get("/")

    assert "Alta" in response.text
    assert "badge-alta" in response.text


def test_index_shows_no_signal_badge(client, db, test_user):
    _make_group(db, user_id=test_user.id)

    response = client.get("/")

    assert "Sem sinal" in response.text


def test_index_has_viewport_meta(client):
    response = client.get("/")

    assert 'name="viewport"' in response.text


def test_index_has_responsive_css(client):
    response = client.get("/")

    assert "@media" in response.text
    assert "max-width" in response.text


def test_index_has_nav_links(client):
    response = client.get("/")

    assert 'href="/"' in response.text
    assert 'href="/groups/create"' in response.text


# --- Detail page tests ---

def test_detail_returns_html(client, db, test_user):
    group = _make_group(db, user_id=test_user.id)

    response = client.get(f"/groups/{group.id}")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_detail_shows_chart_data(client, db, test_user):
    group = _make_group(db, user_id=test_user.id)
    base = datetime.datetime.utcnow() - timedelta(days=5)
    for i in range(3):
        collected = base + timedelta(days=i)
        _make_snapshot(db, group, price=3000.0 + i * 100, collected_at=collected)

    response = client.get(f"/groups/{group.id}")

    assert "chart.js" in response.text.lower()
    assert "cdn.jsdelivr.net/npm/chart.js@4.5.1" in response.text


def test_detail_empty_group_message(client, db, test_user):
    group = _make_group(db, user_id=test_user.id)

    response = client.get(f"/groups/{group.id}")

    assert "Nenhum dado coletado ainda" in response.text


def test_detail_404_nonexistent(client):
    response = client.get("/groups/999")

    assert response.status_code == 404


# --- Create form tests ---

def test_create_form_page_returns_html(client):
    response = client.get("/groups/create")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "name" in response.text
    assert "origins" in response.text
    assert "destinations" in response.text
    assert 'method="POST"' in response.text.lower() or "method=\"POST\"" in response.text


def test_create_group_via_form(client, db):
    response = client.post("/groups/create", data={
        "name": "Europa Teste",
        "origins": "GRU",
        "destinations": "LIS",
        "duration_days": "10",
        "travel_start": "2026-05-01",
        "travel_end": "2026-05-31",
        "target_price": "",
    }, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].startswith("/")
    group = db.query(RouteGroup).filter_by(name="Europa Teste").first()
    assert group is not None
    assert group.origins == ["GRU"]
    assert group.destinations == ["LIS"]


def test_create_group_uppercase_iata(client, db):
    response = client.post("/groups/create", data={
        "name": "Uppercase Test",
        "origins": "gru,cgh",
        "destinations": "lis,opo",
        "duration_days": "10",
        "travel_start": "2026-05-01",
        "travel_end": "2026-05-31",
        "target_price": "",
    }, follow_redirects=False)

    assert response.status_code == 303
    group = db.query(RouteGroup).filter_by(name="Uppercase Test").first()
    assert group is not None
    assert group.origins == ["GRU", "CGH"]
    assert group.destinations == ["LIS", "OPO"]


def test_create_group_validation_error(client, db):
    response = client.post("/groups/create", data={
        "name": "",
        "origins": "GRU",
        "destinations": "LIS",
        "duration_days": "10",
        "travel_start": "2026-05-01",
        "travel_end": "2026-05-31",
        "target_price": "",
    })

    assert response.status_code == 200
    assert "erro" in response.text.lower() or "obrigat" in response.text.lower()


def test_create_group_invalid_iata(client, db):
    response = client.post("/groups/create", data={
        "name": "IATA Invalido",
        "origins": "XX",
        "destinations": "LIS",
        "duration_days": "10",
        "travel_start": "2026-05-01",
        "travel_end": "2026-05-31",
        "target_price": "",
    })

    assert response.status_code == 200
    assert "IATA" in response.text


# --- Edit form tests ---

def test_edit_form_page_prefilled(client, db, test_user):
    group = _make_group(db, name="Editar Grupo", user_id=test_user.id)

    response = client.get(f"/groups/{group.id}/edit")

    assert response.status_code == 200
    assert "Editar Grupo" in response.text
    assert 'method="POST"' in response.text.lower() or "method=\"POST\"" in response.text


def test_edit_group_via_form(client, db, test_user):
    group = _make_group(db, name="Antes", user_id=test_user.id)

    response = client.post(f"/groups/{group.id}/edit", data={
        "name": "Depois",
        "origins": "GRU",
        "destinations": "CDG",
        "duration_days": "14",
        "travel_start": "2026-06-01",
        "travel_end": "2026-06-30",
        "target_price": "5000.00",
    }, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"].startswith("/")
    db.refresh(group)
    assert group.name == "Depois"
    assert group.destinations == ["CDG"]
    assert group.target_price == 5000.0


# --- Toggle tests ---

def test_toggle_group_active(client, db, test_user):
    group = _make_group(db, is_active=True, user_id=test_user.id)

    response = client.post(f"/groups/{group.id}/toggle", follow_redirects=False)

    assert response.status_code == 303
    db.refresh(group)
    assert group.is_active is False

    response = client.post(f"/groups/{group.id}/toggle", follow_redirects=False)

    assert response.status_code == 303
    db.refresh(group)
    assert group.is_active is True


def test_toggle_respects_limit(client, db, test_user):
    for i in range(10):
        _make_group(db, name=f"Active {i}", is_active=True, user_id=test_user.id)
    inactive = _make_group(db, name="Inactive", is_active=False, user_id=test_user.id)

    response = client.post(f"/groups/{inactive.id}/toggle", follow_redirects=False)

    db.refresh(inactive)
    assert inactive.is_active is False


# HYG-01, HYG-02 — Price Fidelity Hygiene (Phase 31.9)

def test_dashboard_card_exibe_rotulo_preco_referencia(client, db, test_user):
    group = _make_group(db, user_id=test_user.id)
    _make_snapshot(db, group, price=3500.0)

    response = client.get("/")

    assert "Preço de referência Google Flights" in response.text


def test_dashboard_card_exibe_disclaimer_divergencia(client, db, test_user):
    group = _make_group(db, user_id=test_user.id)
    _make_snapshot(db, group, price=3500.0)

    response = client.get("/")

    assert "Pode divergir até 5% do valor final" in response.text
    assert "bagagem e taxas não incluídas" in response.text


def test_detail_page_exibe_rotulo_preco_referencia(client, db, test_user):
    group = _make_group(db, user_id=test_user.id)
    _make_snapshot(db, group, price=3500.0, collected_at=datetime.datetime.utcnow() - timedelta(hours=1))

    response = client.get(f"/groups/{group.id}")

    assert "Preço de referência Google Flights" in response.text


def test_detail_page_exibe_disclaimer_divergencia(client, db, test_user):
    group = _make_group(db, user_id=test_user.id)
    _make_snapshot(db, group, price=3500.0, collected_at=datetime.datetime.utcnow() - timedelta(hours=1))

    response = client.get(f"/groups/{group.id}")

    assert "Pode divergir até 5% do valor final" in response.text


# --- Phase 34: recomendacao COMPRE/AGUARDE/MONITORAR ---

def _seed_history(db, group, base_price: float, count: int, departure: datetime.date):
    now = datetime.datetime.utcnow()
    for i in range(count):
        _make_snapshot(
            db,
            group,
            price=base_price + (i % 5) * 20,
            collected_at=now - timedelta(days=i + 2),
            departure_date=departure,
        )


def test_dashboard_mostra_recommendation_compre(client, db, test_user):
    departure = datetime.date.today() + timedelta(days=60)
    group = _make_group(
        db,
        user_id=test_user.id,
        travel_start=departure,
        travel_end=departure + timedelta(days=10),
    )
    _seed_history(db, group, base_price=3500.0, count=20, departure=departure)
    _make_snapshot(
        db,
        group,
        price=2800.0,
        collected_at=datetime.datetime.utcnow() - timedelta(hours=1),
        departure_date=departure,
    )

    response = client.get("/")

    assert "recommendation-compre" in response.text
    assert "COMPRE" in response.text


def test_dashboard_mostra_recommendation_aguarde(client, db, test_user):
    departure = datetime.date.today() + timedelta(days=140)
    group = _make_group(
        db,
        user_id=test_user.id,
        travel_start=departure,
        travel_end=departure + timedelta(days=10),
    )
    _seed_history(db, group, base_price=3500.0, count=20, departure=departure)
    _make_snapshot(
        db,
        group,
        price=3500.0,
        collected_at=datetime.datetime.utcnow() - timedelta(hours=1),
        departure_date=departure,
    )

    response = client.get("/")

    assert "recommendation-aguarde" in response.text
    assert "AGUARDE" in response.text


def test_dashboard_mostra_recommendation_monitorar(client, db, test_user):
    departure = datetime.date.today() + timedelta(days=60)
    group = _make_group(
        db,
        user_id=test_user.id,
        travel_start=departure,
        travel_end=departure + timedelta(days=10),
    )
    _make_snapshot(
        db,
        group,
        price=3500.0,
        collected_at=datetime.datetime.utcnow() - timedelta(hours=1),
        departure_date=departure,
    )

    response = client.get("/")

    assert "recommendation-monitorar" in response.text
    assert "MONITORAR" in response.text


# --- Phase 36 Plan 04: multi_leg dashboard service ---


def test_multi_leg_service_returns_chain_and_breakdown(
    db, test_user, multi_leg_group_factory, multi_leg_snapshot_factory
):
    """D-16/D-18: get_groups_with_summary exposes chain, total_price, legs_breakdown for multi_leg groups."""
    from app.services.dashboard_service import get_groups_with_summary

    group = multi_leg_group_factory(num_legs=3, name="Eurotrip 3 Legs")
    multi_leg_snapshot_factory(group, total_price=5432.10)

    items = get_groups_with_summary(db, user_id=test_user.id)
    item = next(i for i in items if i["group"].id == group.id)

    assert item["mode"] == "multi_leg"
    assert item["legs_chain"] == ["GRU", "FCO", "MAD", "LIS"]
    assert item["legs_count"] == 3
    assert item["total_price"] == 5432.10
    assert item["legs_breakdown"] is not None
    assert len(item["legs_breakdown"]) == 3
    # cada leg tem 4 URLs one-way
    for leg in item["legs_breakdown"]:
        assert set(leg["compare_urls"].keys()) == {
            "google_flights", "decolar", "skyscanner", "kayak"
        }
        assert "date_br" in leg and "/" in leg["date_br"]


def test_multi_leg_service_empty_snapshot_guard(
    db, test_user, multi_leg_group_factory
):
    """Pitfall 7: grupo multi sem snapshot retorna legs_breakdown=None e total_price=None sem raise."""
    from app.services.dashboard_service import get_groups_with_summary

    group = multi_leg_group_factory(num_legs=2, name="No Snapshot Multi")

    items = get_groups_with_summary(db, user_id=test_user.id)
    item = next(i for i in items if i["group"].id == group.id)

    assert item["mode"] == "multi_leg"
    assert item["total_price"] is None
    assert item["legs_breakdown"] is None
    assert item["legs_chain"] == ["GRU", "FCO", "MAD"]


def test_multi_leg_compare_urls_are_one_way(
    db, test_user, multi_leg_group_factory, multi_leg_snapshot_factory
):
    """D-17: compare_urls por leg sao one-way reais, nao roundtrip do grupo inteiro."""
    from app.services.dashboard_service import get_groups_with_summary

    group = multi_leg_group_factory(num_legs=2, name="Oneway URLs")
    multi_leg_snapshot_factory(group, total_price=3000.0)

    items = get_groups_with_summary(db, user_id=test_user.id)
    item = next(i for i in items if i["group"].id == group.id)

    assert item["legs_breakdown"] is not None
    # One-way: Google Flights com marcador oneway (nao deve ter "*" que separa outbound/inbound)
    for leg in item["legs_breakdown"]:
        g = leg["compare_urls"]["google_flights"]
        # Heuristica: roundtrip usa "*DEST.ORIG.YYYY-MM-DD" separado por * no hash.
        # one-way tem apenas um segmento de voo no #flt=.
        assert g.count("*") == 0, f"Google Flights URL parece roundtrip: {g}"
        k = leg["compare_urls"]["kayak"]
        # Kayak oneway usa /flights/O-D/YYYY-MM-DD (sem segunda data)
        # Contagem de segmentos "YYYY-MM-DD" apos hostname deve ser 1 (nao 2).
        import re
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", k)
        assert len(dates) == 1, f"Kayak URL parece roundtrip: {k}"
