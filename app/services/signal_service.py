import logging
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.models import (
    FlightSnapshot,
    DetectedSignal,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BRAZILIAN_AIRPORTS = {
    "GRU", "CGH", "VCP",
    "GIG", "SDU",
    "BSB",
    "CNF", "PLU",
    "SSA",
    "REC",
    "FOR",
    "POA",
    "CWB",
    "FLN",
    "BEL",
    "MAO",
    "NAT",
    "MCZ",
    "VIX",
    "CGB",
    "GYN",
    "SLZ",
    "THE",
    "AJU",
    "JPA",
    "PMW",
    "IGU",
}

DOMESTIC_WINDOW = (21, 90)
INTERNATIONAL_WINDOW = (30, 120)

MIN_SNAPSHOTS_FOR_PRICE = 3


# ---------------------------------------------------------------------------
# Signal factory (DRY: centraliza criacao de DetectedSignal)
# ---------------------------------------------------------------------------


def _create_signal(
    snapshot: FlightSnapshot,
    signal_type: str,
    urgency: str,
    details: str,
) -> DetectedSignal:
    """Cria DetectedSignal com campos comuns extraidos do snapshot."""
    return DetectedSignal(
        route_group_id=snapshot.route_group_id,
        flight_snapshot_id=snapshot.id,
        origin=snapshot.origin,
        destination=snapshot.destination,
        departure_date=snapshot.departure_date,
        return_date=snapshot.return_date,
        signal_type=signal_type,
        urgency=urgency,
        details=details,
        price_at_detection=snapshot.price,
    )


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def detect_signals(
    db: Session, snapshot: FlightSnapshot
) -> list[DetectedSignal]:
    """Orquestra deteccao de todos os tipos de sinal para um snapshot."""
    candidates = _run_detectors(db, snapshot)
    return _deduplicate_and_persist(db, snapshot, candidates)


def _run_detectors(
    db: Session, snapshot: FlightSnapshot
) -> list[DetectedSignal]:
    """Executa todos os detectores com isolamento de erros por detector."""
    detectors = [
        lambda: _check_preco_abaixo_historico(db, snapshot),
        lambda: _check_janela_otima(snapshot),
    ]

    candidates: list[DetectedSignal] = []
    for detector in detectors:
        try:
            result = detector()
            if result is not None:
                candidates.append(result)
        except Exception as e:
            logger.error(f"Detector failed: {e}")
    return candidates


def _deduplicate_and_persist(
    db: Session,
    snapshot: FlightSnapshot,
    candidates: list[DetectedSignal],
) -> list[DetectedSignal]:
    """Filtra duplicatas e persiste sinais novos."""
    reference_time = snapshot.collected_at or datetime.utcnow()
    new_signals: list[DetectedSignal] = []

    for signal in candidates:
        if not _is_duplicate(db, signal, reference_time):
            db.add(signal)
            new_signals.append(signal)

    if new_signals:
        db.commit()

    return new_signals


def _is_domestic(origin: str, destination: str) -> bool:
    return origin in BRAZILIAN_AIRPORTS and destination in BRAZILIAN_AIRPORTS


# ---------------------------------------------------------------------------
# Detectors (pure functions, no db.add)
# ---------------------------------------------------------------------------


def _check_preco_abaixo_historico(
    db: Session, snapshot: FlightSnapshot
) -> DetectedSignal | None:
    """Detecta preco classificado como LOW e abaixo da media historica."""
    if snapshot.price_classification != "LOW":
        return None

    avg_price, count = _get_avg_price_last_n(db, snapshot, n=14)

    if count < MIN_SNAPSHOTS_FOR_PRICE:
        return None

    if avg_price is not None and snapshot.price < avg_price:
        return _create_signal(
            snapshot,
            signal_type="PRECO_ABAIXO_HISTORICO",
            urgency="MEDIA",
            details=(
                f"Preco {snapshot.price:.2f} abaixo da media "
                f"{avg_price:.2f} dos ultimos {count} snapshots"
            ),
        )
    return None


def _check_janela_otima(
    snapshot: FlightSnapshot,
) -> DetectedSignal | None:
    """Detecta se dias ate o voo estao na faixa ideal para o tipo de rota."""
    today = date.today()
    days_until = (snapshot.departure_date - today).days

    if days_until <= 0:
        return None

    domestic = _is_domestic(snapshot.origin, snapshot.destination)
    window = DOMESTIC_WINDOW if domestic else INTERNATIONAL_WINDOW

    if window[0] <= days_until <= window[1]:
        route_type = "domestico" if domestic else "internacional"
        return _create_signal(
            snapshot,
            signal_type="JANELA_OTIMA",
            urgency="MEDIA",
            details=(
                f"Voo {route_type} em {days_until} dias "
                f"(janela ideal: {window[0]}-{window[1]} dias)"
            ),
        )
    return None


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def _is_duplicate(
    db: Session, signal: DetectedSignal, reference_time: datetime
) -> bool:
    """Verifica se sinal identico foi emitido nas ultimas 12 horas."""
    cutoff = reference_time - timedelta(hours=12)
    existing = (
        db.query(DetectedSignal)
        .filter(
            DetectedSignal.route_group_id == signal.route_group_id,
            DetectedSignal.origin == signal.origin,
            DetectedSignal.destination == signal.destination,
            DetectedSignal.departure_date == signal.departure_date,
            DetectedSignal.return_date == signal.return_date,
            DetectedSignal.signal_type == signal.signal_type,
            DetectedSignal.detected_at >= cutoff,
        )
        .first()
    )
    return existing is not None


# ---------------------------------------------------------------------------
# Price average helper
# ---------------------------------------------------------------------------


def _get_avg_price_last_n(
    db: Session, snapshot: FlightSnapshot, n: int = 14
) -> tuple[float | None, int]:
    """Retorna (media_de_preco, contagem) dos ultimos N snapshots da mesma rota."""
    subquery = (
        select(FlightSnapshot.price)
        .where(
            FlightSnapshot.route_group_id == snapshot.route_group_id,
            FlightSnapshot.origin == snapshot.origin,
            FlightSnapshot.destination == snapshot.destination,
            FlightSnapshot.departure_date == snapshot.departure_date,
            FlightSnapshot.return_date == snapshot.return_date,
            FlightSnapshot.id != snapshot.id,
            FlightSnapshot.collected_at < snapshot.collected_at,
        )
        .order_by(FlightSnapshot.collected_at.desc())
        .limit(n)
        .subquery()
    )
    result = db.execute(
        select(sa_func.avg(subquery.c.price), sa_func.count())
    ).one()
    return result[0], result[1]
