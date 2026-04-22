"""Agregacao somente-banco para pagina publica SEO.

IMPORTANTE: nao chamar SerpAPI nem Travelpayouts. Tudo vem do banco local
(RouteCache + FlightSnapshot). Phase 33 exige zero chamada externa por pageview.
"""
import datetime
import statistics
from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import FlightSnapshot, RouteCache
from app.services.iata_cities import iata_to_city

MIN_SNAPSHOTS_FOR_INDEX = 10
HISTORY_WINDOW_DAYS = 180
MONTH_LABELS_PT = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez",
]


def _month_label(d: datetime.date) -> str:
    return f"{MONTH_LABELS_PT[d.month - 1]}/{d.year}"


def get_top_public_routes(db: Session, limit: int = 5) -> list[dict]:
    """Rotas com >= MIN_SNAPSHOTS_FOR_INDEX, ordenadas por volume desc."""
    rows = (
        db.query(
            FlightSnapshot.origin,
            FlightSnapshot.destination,
            func.count(FlightSnapshot.id).label("cnt"),
        )
        .group_by(FlightSnapshot.origin, FlightSnapshot.destination)
        .having(func.count(FlightSnapshot.id) >= MIN_SNAPSHOTS_FOR_INDEX)
        .order_by(func.count(FlightSnapshot.id).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "origin": origin,
            "destination": destination,
            "origin_city": iata_to_city(origin),
            "destination_city": iata_to_city(destination),
            "snapshot_count": cnt,
        }
        for origin, destination, cnt in rows
    ]


def has_enough_data(db: Session, origin: str, destination: str) -> bool:
    count = (
        db.query(FlightSnapshot)
        .filter(
            FlightSnapshot.origin == origin.upper(),
            FlightSnapshot.destination == destination.upper(),
        )
        .count()
    )
    return count >= MIN_SNAPSHOTS_FOR_INDEX


def get_route_stats(db: Session, origin: str, destination: str) -> dict | None:
    origin = origin.upper()
    destination = destination.upper()
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=HISTORY_WINDOW_DAYS)

    snaps = (
        db.query(FlightSnapshot)
        .filter(
            FlightSnapshot.origin == origin,
            FlightSnapshot.destination == destination,
            FlightSnapshot.collected_at >= cutoff,
        )
        .all()
    )
    cache_row = (
        db.query(RouteCache)
        .filter(
            RouteCache.origin == origin,
            RouteCache.destination == destination,
        )
        .order_by(RouteCache.min_price.asc(), RouteCache.cached_at.desc())
        .first()
    )

    if not snaps and cache_row is None:
        return None

    current_price = None
    currency = "BRL"
    cached_at = None
    current_departure_date = None
    current_return_date = None
    if cache_row is not None:
        current_price = cache_row.min_price
        currency = cache_row.currency
        cached_at = cache_row.cached_at
        current_departure_date = cache_row.departure_date
        current_return_date = cache_row.return_date
    elif snaps:
        latest = max(snaps, key=lambda s: s.collected_at)
        current_price = latest.price
        currency = latest.currency
        current_departure_date = latest.departure_date
        current_return_date = latest.return_date

    by_month: dict[str, list[float]] = defaultdict(list)
    for s in snaps:
        if s.price and s.price > 0:
            by_month[_month_label(s.collected_at.date())].append(s.price)
    monthly_series = [
        {
            "month_label": label,
            "avg_price": round(sum(p) / len(p), 2),
            "snapshot_count": len(p),
        }
        for label, p in sorted(by_month.items(), key=lambda kv: kv[0])
    ]

    all_prices = [s.price for s in snaps if s.price and s.price > 0]
    median_180d = round(statistics.median(all_prices), 2) if all_prices else None
    best_months = sorted(monthly_series, key=lambda m: m["avg_price"])[:3]

    return {
        "origin": origin,
        "destination": destination,
        "origin_city": iata_to_city(origin),
        "destination_city": iata_to_city(destination),
        "current_price": current_price,
        "currency": currency,
        "cached_at": cached_at,
        "current_departure_date": current_departure_date,
        "current_return_date": current_return_date,
        "median_180d": median_180d,
        "snapshot_count": len(snaps),
        "monthly_series": monthly_series,
        "best_months": best_months,
    }
