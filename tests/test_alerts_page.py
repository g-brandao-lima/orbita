"""Testes para a pagina Meus Alertas (GET /alerts) — TDD RED phase (12-02)."""
import datetime

import pytest

from app.models import DetectedSignal, FlightSnapshot, RouteGroup


# ---------------------------------------------------------------------------
# Test 3: GET /alerts retorna 200 com template alerts.html
# ---------------------------------------------------------------------------


def test_alerts_page_returns_200(client, test_user, db):
    """GET /alerts retorna 200 para usuario autenticado."""
    # Act
    response = client.get("/alerts")

    # Assert
    assert response.status_code == 200
    assert "Meus Alertas" in response.text


# ---------------------------------------------------------------------------
# Test 4: /alerts mostra apenas sinais dos grupos do usuario logado
# ---------------------------------------------------------------------------


def test_alerts_page_shows_only_user_signals(client, test_user, second_user, db):
    """Pagina /alerts mostra apenas sinais dos grupos do usuario logado."""
    # Arrange — grupo do test_user com sinal
    group_mine = RouteGroup(
        name="Meu Grupo",
        user_id=test_user.id,
        origins=["GRU"],
        destinations=["JFK"],
        duration_days=7,
        travel_start=datetime.date(2026, 6, 1),
        travel_end=datetime.date(2026, 6, 30),
        is_active=True,
    )
    db.add(group_mine)
    db.flush()

    snap_mine = FlightSnapshot(
        route_group_id=group_mine.id,
        origin="GRU",
        destination="JFK",
        departure_date=datetime.date(2026, 6, 10),
        return_date=datetime.date(2026, 6, 17),
        price=3500.00,
        currency="BRL",
        airline="LA",
    )
    db.add(snap_mine)
    db.flush()

    signal_mine = DetectedSignal(
        route_group_id=group_mine.id,
        flight_snapshot_id=snap_mine.id,
        origin="GRU",
        destination="JFK",
        departure_date=datetime.date(2026, 6, 10),
        return_date=datetime.date(2026, 6, 17),
        signal_type="BALDE_FECHANDO",
        urgency="ALTA",
        details="Classe K: 3 -> 1",
        price_at_detection=3500.00,
    )
    db.add(signal_mine)

    # Arrange — grupo do second_user com sinal (NAO deve aparecer)
    group_other = RouteGroup(
        name="Grupo Alheio",
        user_id=second_user.id,
        origins=["GIG"],
        destinations=["MIA"],
        duration_days=5,
        travel_start=datetime.date(2026, 7, 1),
        travel_end=datetime.date(2026, 7, 31),
        is_active=True,
    )
    db.add(group_other)
    db.flush()

    snap_other = FlightSnapshot(
        route_group_id=group_other.id,
        origin="GIG",
        destination="MIA",
        departure_date=datetime.date(2026, 7, 5),
        return_date=datetime.date(2026, 7, 10),
        price=5000.00,
        currency="BRL",
        airline="AA",
    )
    db.add(snap_other)
    db.flush()

    signal_other = DetectedSignal(
        route_group_id=group_other.id,
        flight_snapshot_id=snap_other.id,
        origin="GIG",
        destination="MIA",
        departure_date=datetime.date(2026, 7, 5),
        return_date=datetime.date(2026, 7, 10),
        signal_type="PRECO_BAIXO",
        urgency="MEDIA",
        details="Preco abaixo do historico",
        price_at_detection=5000.00,
    )
    db.add(signal_other)
    db.commit()

    # Act
    response = client.get("/alerts")

    # Assert — sinal do test_user aparece, sinal do second_user NAO
    assert response.status_code == 200
    assert "BALDE_FECHANDO" in response.text
    assert "GIG" not in response.text or "Grupo Alheio" not in response.text


# ---------------------------------------------------------------------------
# Test 5: /alerts com sinais exibe tipo, urgencia, rota, preco e data
# ---------------------------------------------------------------------------


def test_alerts_page_shows_signal_details(client, test_user, db):
    """Pagina /alerts exibe tipo, urgencia, rota, preco e data do sinal."""
    # Arrange
    group = RouteGroup(
        name="Teste Detalhes",
        user_id=test_user.id,
        origins=["GRU"],
        destinations=["LIS"],
        duration_days=10,
        travel_start=datetime.date(2026, 8, 1),
        travel_end=datetime.date(2026, 8, 31),
        is_active=True,
    )
    db.add(group)
    db.flush()

    snap = FlightSnapshot(
        route_group_id=group.id,
        origin="GRU",
        destination="LIS",
        departure_date=datetime.date(2026, 8, 15),
        return_date=datetime.date(2026, 8, 25),
        price=4200.00,
        currency="BRL",
        airline="TP",
    )
    db.add(snap)
    db.flush()

    signal = DetectedSignal(
        route_group_id=group.id,
        flight_snapshot_id=snap.id,
        origin="GRU",
        destination="LIS",
        departure_date=datetime.date(2026, 8, 15),
        return_date=datetime.date(2026, 8, 25),
        signal_type="BALDE_REABERTO",
        urgency="MAXIMA",
        details="Classe M reabriu",
        price_at_detection=4200.00,
    )
    db.add(signal)
    db.commit()

    # Act
    response = client.get("/alerts")

    # Assert — detalhes do sinal presentes
    assert response.status_code == 200
    body = response.text
    assert "BALDE_REABERTO" in body or "BALDE REABERTO" in body
    assert "MAXIMA" in body or "M\u00c1XIMA" in body
    assert "GRU" in body
    assert "LIS" in body
    assert "4.200" in body or "4200" in body
