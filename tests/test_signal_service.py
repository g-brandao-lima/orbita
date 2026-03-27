import datetime
from datetime import date, timedelta
from unittest.mock import patch

from app.models import (
    RouteGroup,
    FlightSnapshot,
    DetectedSignal,
)
from app.services.signal_service import detect_signals


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_route_group(db, name="Test Group", origins=None, destinations=None):
    """Creates a minimal RouteGroup."""
    group = RouteGroup(
        name=name,
        origins=origins or ["GRU"],
        destinations=destinations or ["GIG"],
        duration_days=7,
        travel_start=date(2026, 6, 1),
        travel_end=date(2026, 7, 31),
        is_active=True,
    )
    db.add(group)
    db.flush()
    return group


def _make_snapshot(
    db,
    route_group,
    origin="GRU",
    destination="GIG",
    dep_date=None,
    ret_date=None,
    price=1500.0,
    classification=None,
    collected_at=None,
):
    """Creates and persists a FlightSnapshot."""
    if dep_date is None:
        dep_date = date(2026, 6, 15)
    if ret_date is None:
        ret_date = date(2026, 6, 22)

    snapshot = FlightSnapshot(
        route_group_id=route_group.id,
        origin=origin,
        destination=destination,
        departure_date=dep_date,
        return_date=ret_date,
        price=price,
        currency="BRL",
        airline="LA",
        price_classification=classification,
    )
    if collected_at is not None:
        snapshot.collected_at = collected_at

    db.add(snapshot)
    db.flush()
    db.refresh(snapshot)
    return snapshot


# ===========================================================================
# PRECO ABAIXO HISTORICO
# ===========================================================================


class TestPrecoAbaixoHistorico:
    """price_classification=LOW e preco abaixo da media dos ultimos snapshots."""

    def test_preco_abaixo_historico(self, db):
        """LOW + preco abaixo da media de 14 snapshots -> sinal PRECO_ABAIXO_HISTORICO."""
        rg = _make_route_group(db)

        for i in range(14):
            _make_snapshot(
                db, rg,
                price=2000.0,
                collected_at=datetime.datetime(2026, 6, 1, 6, 0, 0) + timedelta(hours=6 * i),
            )

        current = _make_snapshot(
            db, rg,
            price=1200.0,
            classification="LOW",
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        preco = [s for s in signals if s.signal_type == "PRECO_ABAIXO_HISTORICO"]
        assert len(preco) == 1
        assert preco[0].urgency == "MEDIA"

    def test_preco_low_but_above_avg(self, db):
        """LOW mas preco acima da media -> nenhum sinal."""
        rg = _make_route_group(db)

        for i in range(14):
            _make_snapshot(
                db, rg,
                price=1000.0,
                collected_at=datetime.datetime(2026, 6, 1, 6, 0, 0) + timedelta(hours=6 * i),
            )

        current = _make_snapshot(
            db, rg,
            price=1500.0,
            classification="LOW",
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        preco = [s for s in signals if s.signal_type == "PRECO_ABAIXO_HISTORICO"]
        assert len(preco) == 0

    def test_preco_insufficient_history(self, db):
        """Apenas 2 snapshots anteriores -> nenhum sinal (minimo 3)."""
        rg = _make_route_group(db)

        for i in range(2):
            _make_snapshot(
                db, rg,
                price=2000.0,
                collected_at=datetime.datetime(2026, 6, 1, 6, 0, 0) + timedelta(hours=6 * i),
            )

        current = _make_snapshot(
            db, rg,
            price=1200.0,
            classification="LOW",
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        preco = [s for s in signals if s.signal_type == "PRECO_ABAIXO_HISTORICO"]
        assert len(preco) == 0

    def test_preco_not_low_classification(self, db):
        """classification=MEDIUM -> nenhum sinal independente do preco."""
        rg = _make_route_group(db)

        for i in range(14):
            _make_snapshot(
                db, rg,
                price=2000.0,
                collected_at=datetime.datetime(2026, 6, 1, 6, 0, 0) + timedelta(hours=6 * i),
            )

        current = _make_snapshot(
            db, rg,
            price=1200.0,
            classification="MEDIUM",
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        preco = [s for s in signals if s.signal_type == "PRECO_ABAIXO_HISTORICO"]
        assert len(preco) == 0


# ===========================================================================
# JANELA OTIMA
# ===========================================================================


class TestJanelaOtima:
    """Dias ate o voo dentro da faixa ideal para o tipo de rota."""

    @patch("app.services.signal_service.date")
    def test_janela_otima_domestico(self, mock_date, db):
        """GRU->GIG, embarque em 45 dias -> sinal JANELA_OTIMA (domestico 21-90)."""
        today = date(2026, 5, 1)
        mock_date.today.return_value = today
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        rg = _make_route_group(db)
        dep = today + timedelta(days=45)

        current = _make_snapshot(
            db, rg,
            origin="GRU",
            destination="GIG",
            dep_date=dep,
            ret_date=dep + timedelta(days=7),
        )

        signals = detect_signals(db, current)

        janela = [s for s in signals if s.signal_type == "JANELA_OTIMA"]
        assert len(janela) == 1
        assert janela[0].urgency == "MEDIA"

    @patch("app.services.signal_service.date")
    def test_janela_otima_internacional(self, mock_date, db):
        """GRU->MIA, embarque em 60 dias -> sinal JANELA_OTIMA (internacional 30-120)."""
        today = date(2026, 5, 1)
        mock_date.today.return_value = today
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        rg = _make_route_group(db, destinations=["MIA"])

        dep = today + timedelta(days=60)
        current = _make_snapshot(
            db, rg,
            origin="GRU",
            destination="MIA",
            dep_date=dep,
            ret_date=dep + timedelta(days=7),
        )

        signals = detect_signals(db, current)

        janela = [s for s in signals if s.signal_type == "JANELA_OTIMA"]
        assert len(janela) == 1
        assert janela[0].urgency == "MEDIA"

    @patch("app.services.signal_service.date")
    def test_janela_fora_da_faixa(self, mock_date, db):
        """GRU->GIG, embarque em 10 dias -> nenhum sinal (muito proximo)."""
        today = date(2026, 5, 1)
        mock_date.today.return_value = today
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        rg = _make_route_group(db)
        dep = today + timedelta(days=10)

        current = _make_snapshot(
            db, rg,
            origin="GRU",
            destination="GIG",
            dep_date=dep,
            ret_date=dep + timedelta(days=7),
        )

        signals = detect_signals(db, current)

        janela = [s for s in signals if s.signal_type == "JANELA_OTIMA"]
        assert len(janela) == 0

    @patch("app.services.signal_service.date")
    def test_janela_fora_da_faixa_longe(self, mock_date, db):
        """GRU->GIG, embarque em 150 dias -> nenhum sinal (muito longe)."""
        today = date(2026, 5, 1)
        mock_date.today.return_value = today
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        rg = _make_route_group(db)
        dep = today + timedelta(days=150)

        current = _make_snapshot(
            db, rg,
            origin="GRU",
            destination="GIG",
            dep_date=dep,
            ret_date=dep + timedelta(days=7),
        )

        signals = detect_signals(db, current)

        janela = [s for s in signals if s.signal_type == "JANELA_OTIMA"]
        assert len(janela) == 0


# ===========================================================================
# DEDUPLICACAO
# ===========================================================================


class TestDeduplicacao:
    """Mesmo sinal para mesma rota nao re-emitido dentro de 12h."""

    def test_deduplicacao_bloqueia(self, db):
        """Mesmo sinal dentro de 12h -> segundo nao e persistido."""
        rg = _make_route_group(db)

        # 14 snapshots para historico
        for i in range(14):
            _make_snapshot(
                db, rg,
                price=2000.0,
                collected_at=datetime.datetime(2026, 6, 1, 6, 0, 0) + timedelta(hours=6 * i),
            )

        current = _make_snapshot(
            db, rg,
            price=1200.0,
            classification="LOW",
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        # Sinal existente emitido ha 6h (dentro da janela de 12h)
        existing = DetectedSignal(
            route_group_id=rg.id,
            flight_snapshot_id=current.id,
            origin="GRU",
            destination="GIG",
            departure_date=date(2026, 6, 15),
            return_date=date(2026, 6, 22),
            signal_type="PRECO_ABAIXO_HISTORICO",
            urgency="MEDIA",
            details="Preco baixo",
            price_at_detection=1200.0,
            detected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )
        db.add(existing)
        db.flush()

        signals = detect_signals(db, current)

        preco = [s for s in signals if s.signal_type == "PRECO_ABAIXO_HISTORICO"]
        assert len(preco) == 0

    def test_deduplicacao_permite_apos_12h(self, db):
        """Mesmo sinal apos 12h -> segundo E persistido."""
        rg = _make_route_group(db)

        for i in range(14):
            _make_snapshot(
                db, rg,
                price=2000.0,
                collected_at=datetime.datetime(2026, 6, 1, 6, 0, 0) + timedelta(hours=6 * i),
            )

        current = _make_snapshot(
            db, rg,
            price=1200.0,
            classification="LOW",
            collected_at=datetime.datetime(2026, 6, 10, 20, 0, 0),
        )

        # Sinal existente emitido ha 13h (fora da janela de 12h)
        existing = DetectedSignal(
            route_group_id=rg.id,
            flight_snapshot_id=current.id,
            origin="GRU",
            destination="GIG",
            departure_date=date(2026, 6, 15),
            return_date=date(2026, 6, 22),
            signal_type="PRECO_ABAIXO_HISTORICO",
            urgency="MEDIA",
            details="Preco baixo",
            price_at_detection=1200.0,
            detected_at=datetime.datetime(2026, 6, 10, 7, 0, 0),
        )
        db.add(existing)
        db.flush()

        signals = detect_signals(db, current)

        preco = [s for s in signals if s.signal_type == "PRECO_ABAIXO_HISTORICO"]
        assert len(preco) >= 1

    def test_deduplicacao_different_route_not_blocked(self, db):
        """Mesmo tipo de sinal mas rota diferente -> nao bloqueado."""
        rg = _make_route_group(db)

        for i in range(14):
            _make_snapshot(
                db, rg,
                price=2000.0,
                collected_at=datetime.datetime(2026, 6, 1, 6, 0, 0) + timedelta(hours=6 * i),
            )

        current = _make_snapshot(
            db, rg,
            origin="GRU",
            destination="GIG",
            price=1200.0,
            classification="LOW",
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        # Sinal existente para rota DIFERENTE (GRU->SSA)
        existing = DetectedSignal(
            route_group_id=rg.id,
            flight_snapshot_id=current.id,
            origin="GRU",
            destination="SSA",
            departure_date=date(2026, 6, 15),
            return_date=date(2026, 6, 22),
            signal_type="PRECO_ABAIXO_HISTORICO",
            urgency="MEDIA",
            details="Preco baixo",
            price_at_detection=1200.0,
            detected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )
        db.add(existing)
        db.flush()

        signals = detect_signals(db, current)

        preco = [s for s in signals if s.signal_type == "PRECO_ABAIXO_HISTORICO"]
        assert len(preco) >= 1


# ===========================================================================
# Edge Cases
# ===========================================================================


class TestEdgeCases:
    """Casos de borda para deteccao de sinais."""

    def test_primeiro_snapshot_sem_sinal_preco(self, db):
        """Primeiro snapshot sem historico -> sem sinal PRECO_ABAIXO_HISTORICO."""
        rg = _make_route_group(db)

        current = _make_snapshot(
            db, rg,
            price=1200.0,
            classification="LOW",
        )

        signals = detect_signals(db, current)

        preco = [s for s in signals if s.signal_type == "PRECO_ABAIXO_HISTORICO"]
        assert len(preco) == 0

    @patch("app.services.signal_service.date")
    def test_multiple_signals_same_snapshot(self, mock_date, db):
        """Snapshot dispara PRECO_ABAIXO_HISTORICO e JANELA_OTIMA ao mesmo tempo."""
        today = date(2026, 5, 1)
        mock_date.today.return_value = today
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        rg = _make_route_group(db)
        dep = today + timedelta(days=45)  # dentro da janela domestica

        for i in range(14):
            _make_snapshot(
                db, rg,
                price=2000.0,
                dep_date=dep,
                ret_date=dep + timedelta(days=7),
                collected_at=datetime.datetime(2026, 4, 1, 6, 0, 0) + timedelta(hours=6 * i),
            )

        current = _make_snapshot(
            db, rg,
            price=1200.0,
            classification="LOW",
            dep_date=dep,
            ret_date=dep + timedelta(days=7),
            collected_at=datetime.datetime(2026, 5, 1, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        types = {s.signal_type for s in signals}
        assert "PRECO_ABAIXO_HISTORICO" in types
        assert "JANELA_OTIMA" in types
