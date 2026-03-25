import datetime
from datetime import date, timedelta
from unittest.mock import patch

from app.models import (
    RouteGroup,
    FlightSnapshot,
    BookingClassSnapshot,
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
    booking_classes=None,
    collected_at=None,
):
    """Creates and persists a FlightSnapshot with optional BookingClassSnapshots."""
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

    if booking_classes:
        for bc in booking_classes:
            db.add(
                BookingClassSnapshot(
                    flight_snapshot_id=snapshot.id,
                    class_code=bc["class_code"],
                    seats_available=bc["seats"],
                    segment_direction=bc.get("direction", "OUTBOUND"),
                )
            )
    db.flush()
    db.refresh(snapshot)
    return snapshot


# ===========================================================================
# SIGN-01: BALDE FECHANDO
# ===========================================================================


class TestBaldeFechando:
    """Classe K ou Q caiu de >=3 para <=1 entre snapshots consecutivos."""

    def test_balde_fechando_k_drops(self, db):
        """K vai de 5 para 1 -> sinal BALDE_FECHANDO urgencia ALTA."""
        rg = _make_route_group(db)

        # Snapshot anterior: K=5
        _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 5}],
            collected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )

        # Snapshot atual: K=1
        current = _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 1}],
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        assert len(signals) >= 1
        balde = [s for s in signals if s.signal_type == "BALDE_FECHANDO"]
        assert len(balde) == 1
        assert balde[0].urgency == "ALTA"

    def test_balde_fechando_q_drops(self, db):
        """Q vai de 3 para 0 -> sinal BALDE_FECHANDO urgencia ALTA."""
        rg = _make_route_group(db)

        _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "Q", "seats": 3}],
            collected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )

        current = _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "Q", "seats": 0}],
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        balde = [s for s in signals if s.signal_type == "BALDE_FECHANDO"]
        assert len(balde) == 1
        assert balde[0].urgency == "ALTA"

    def test_balde_fechando_no_change(self, db):
        """K permanece em 5 -> nenhum sinal."""
        rg = _make_route_group(db)

        _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 5}],
            collected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )

        current = _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 5}],
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        balde = [s for s in signals if s.signal_type == "BALDE_FECHANDO"]
        assert len(balde) == 0

    def test_balde_fechando_drops_but_still_above_threshold(self, db):
        """K vai de 7 para 2 -> nenhum sinal (ainda > 1)."""
        rg = _make_route_group(db)

        _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 7}],
            collected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )

        current = _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 2}],
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        balde = [s for s in signals if s.signal_type == "BALDE_FECHANDO"]
        assert len(balde) == 0


# ===========================================================================
# SIGN-02: BALDE REABERTO
# ===========================================================================


class TestBaldeReaberto:
    """Classe que estava em 0 voltou a ter assentos."""

    def test_balde_reaberto(self, db):
        """M era 0, agora 3 -> sinal BALDE_REABERTO urgencia MAXIMA."""
        rg = _make_route_group(db)

        _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "M", "seats": 0}],
            collected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )

        current = _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "M", "seats": 3}],
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        reaberto = [s for s in signals if s.signal_type == "BALDE_REABERTO"]
        assert len(reaberto) == 1
        assert reaberto[0].urgency == "MAXIMA"

    def test_balde_reaberto_already_open(self, db):
        """M era 2, agora 3 -> nenhum sinal (nao estava em 0)."""
        rg = _make_route_group(db)

        _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "M", "seats": 2}],
            collected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )

        current = _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "M", "seats": 3}],
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        reaberto = [s for s in signals if s.signal_type == "BALDE_REABERTO"]
        assert len(reaberto) == 0


# ===========================================================================
# SIGN-03: PRECO ABAIXO HISTORICO
# ===========================================================================


class TestPrecoAbaixoHistorico:
    """price_classification=LOW e preco abaixo da media dos ultimos snapshots."""

    def test_preco_abaixo_historico(self, db):
        """LOW + preco abaixo da media de 14 snapshots -> sinal PRECO_ABAIXO_HISTORICO."""
        rg = _make_route_group(db)

        # 14 snapshots anteriores com preco medio de 2000
        for i in range(14):
            _make_snapshot(
                db, rg,
                price=2000.0,
                collected_at=datetime.datetime(2026, 6, 1, 6, 0, 0) + timedelta(hours=6 * i),
            )

        # Snapshot atual: preco 1200, classificacao LOW
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
# SIGN-04: JANELA OTIMA
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
# SIGN-05: DEDUPLICACAO
# ===========================================================================


class TestDeduplicacao:
    """Mesmo sinal para mesma rota nao re-emitido dentro de 12h."""

    def test_deduplicacao_bloqueia(self, db):
        """Mesmo sinal dentro de 12h -> segundo nao e persistido."""
        rg = _make_route_group(db)

        current = _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 1}],
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
            signal_type="BALDE_FECHANDO",
            urgency="ALTA",
            details="K dropped",
            price_at_detection=1500.0,
            detected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )
        db.add(existing)
        db.flush()

        # Snapshot anterior para trigger de BALDE_FECHANDO
        _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 5}],
            collected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )

        signals = detect_signals(db, current)

        balde = [s for s in signals if s.signal_type == "BALDE_FECHANDO"]
        assert len(balde) == 0

    def test_deduplicacao_permite_apos_12h(self, db):
        """Mesmo sinal apos 12h -> segundo E persistido."""
        rg = _make_route_group(db)

        current = _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 1}],
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
            signal_type="BALDE_FECHANDO",
            urgency="ALTA",
            details="K dropped",
            price_at_detection=1500.0,
            detected_at=datetime.datetime(2026, 6, 10, 7, 0, 0),
        )
        db.add(existing)
        db.flush()

        _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 5}],
            collected_at=datetime.datetime(2026, 6, 10, 14, 0, 0),
        )

        signals = detect_signals(db, current)

        balde = [s for s in signals if s.signal_type == "BALDE_FECHANDO"]
        assert len(balde) >= 1

    def test_deduplicacao_different_route_not_blocked(self, db):
        """Mesmo tipo de sinal mas rota diferente -> ambos persistidos."""
        rg = _make_route_group(db)

        current = _make_snapshot(
            db, rg,
            origin="GRU",
            destination="GIG",
            booking_classes=[{"class_code": "K", "seats": 1}],
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
            signal_type="BALDE_FECHANDO",
            urgency="ALTA",
            details="K dropped",
            price_at_detection=1500.0,
            detected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )
        db.add(existing)
        db.flush()

        _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 5}],
            collected_at=datetime.datetime(2026, 6, 10, 6, 0, 0),
        )

        signals = detect_signals(db, current)

        balde = [s for s in signals if s.signal_type == "BALDE_FECHANDO"]
        assert len(balde) >= 1


# ===========================================================================
# Edge Cases
# ===========================================================================


class TestEdgeCases:
    """Casos de borda para deteccao de sinais."""

    def test_primeiro_snapshot_sem_sinal_balde(self, db):
        """Primeiro snapshot (sem anterior) -> sem sinais BALDE, mas JANELA/PRECO podem disparar."""
        rg = _make_route_group(db)

        current = _make_snapshot(
            db, rg,
            booking_classes=[{"class_code": "K", "seats": 1}],
        )

        signals = detect_signals(db, current)

        balde_fechando = [s for s in signals if s.signal_type == "BALDE_FECHANDO"]
        balde_reaberto = [s for s in signals if s.signal_type == "BALDE_REABERTO"]
        assert len(balde_fechando) == 0
        assert len(balde_reaberto) == 0

    def test_multiple_signals_same_snapshot(self, db):
        """Snapshot dispara BALDE_FECHANDO e PRECO_ABAIXO_HISTORICO ao mesmo tempo."""
        rg = _make_route_group(db)

        # 14 snapshots anteriores com preco alto e K=5
        for i in range(14):
            _make_snapshot(
                db, rg,
                price=2000.0,
                booking_classes=[{"class_code": "K", "seats": 5}],
                collected_at=datetime.datetime(2026, 6, 1, 6, 0, 0) + timedelta(hours=6 * i),
            )

        # Snapshot atual: K=1, preco baixo, classificacao LOW
        current = _make_snapshot(
            db, rg,
            price=1200.0,
            classification="LOW",
            booking_classes=[{"class_code": "K", "seats": 1}],
            collected_at=datetime.datetime(2026, 6, 10, 12, 0, 0),
        )

        signals = detect_signals(db, current)

        types = {s.signal_type for s in signals}
        assert "BALDE_FECHANDO" in types
        assert "PRECO_ABAIXO_HISTORICO" in types
