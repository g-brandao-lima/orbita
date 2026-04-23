"""Servico de busca de precos multi-trecho (Phase 36).

Reusa route_cache_service, flight_search e price_prediction_service (Phase 34).
Implementa produto cartesiano limitado de datas por leg (cap 7) com filtro
por validade temporal (min_stay/max_stay). Persiste 1 FlightSnapshot com
airline="MULTI" e details JSON contendo breakdown do roteiro.
"""
from __future__ import annotations

import itertools
import logging
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models import FlightSnapshot, RouteGroup, RouteGroupLeg
from app.services import (
    flight_search,
    price_prediction_service,
    route_cache_service,
    snapshot_service,
)

logger = logging.getLogger(__name__)

DATE_CANDIDATES_PER_LEG = 7
HISTORICAL_WINDOW_DAYS = 90


def _candidate_dates(leg: RouteGroupLeg) -> list[date]:
    """Amostra ate DATE_CANDIDATES_PER_LEG datas dentro da janela do leg."""
    total_days = (leg.window_end - leg.window_start).days
    if total_days < 0:
        return []
    if total_days <= DATE_CANDIDATES_PER_LEG - 1:
        return [leg.window_start + timedelta(days=i) for i in range(total_days + 1)]
    # Amostra DATE_CANDIDATES_PER_LEG datas ancoradas em window_start e window_end
    n = DATE_CANDIDATES_PER_LEG - 1
    sampled = [
        leg.window_start + timedelta(days=round(i * total_days / n))
        for i in range(DATE_CANDIDATES_PER_LEG)
    ]
    # Dedup preservando ordem
    seen: set[date] = set()
    dedup: list[date] = []
    for d in sampled:
        if d not in seen:
            seen.add(d)
            dedup.append(d)
    return dedup


def _is_valid_chain(dates: tuple[date, ...], legs: list[RouteGroupLeg]) -> bool:
    """Checa min/max_stay_days entre datas consecutivas."""
    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i - 1]).days
        prev = legs[i - 1]
        if gap < prev.min_stay_days:
            return False
        if prev.max_stay_days is not None and gap > prev.max_stay_days:
            return False
    return True


def _extract_price(cached: dict[str, Any] | None) -> float | None:
    """Extrai preco de dict de cache, aceitando chaves 'price' ou 'min_price'."""
    if cached is None:
        return None
    for key in ("price", "min_price"):
        if key in cached and cached[key] is not None:
            try:
                return float(cached[key])
            except (TypeError, ValueError):
                return None
    return None


def _fetch_leg_price(
    db: Session,
    leg: RouteGroupLeg,
    dep_date: date,
    passengers: int,
) -> dict[str, Any] | None:
    """Cache-first lookup; fallback SerpAPI via search_flights_ex (D-12)."""
    try:
        cached = route_cache_service.get_cached_price(
            db,
            origin=leg.origin,
            destination=leg.destination,
            departure_date=dep_date.isoformat(),
            return_date=None,
        )
    except Exception as exc:
        logger.warning("multi_leg cache lookup failed leg=%s: %s", leg.id, exc)
        cached = None

    price = _extract_price(cached)
    if price is not None:
        airline = cached.get("airline") if isinstance(cached, dict) else None
        return {"price": price, "airline": airline or "CACHE", "source": "cache"}

    # Fallback SerpAPI on-demand (D-12). Workaround one-way: usar mesma data.
    try:
        flights, _insights, source, _was_hit = flight_search.search_flights_ex(
            origin=leg.origin,
            destination=leg.destination,
            departure_date=dep_date.isoformat(),
            return_date=dep_date.isoformat(),
            max_results=1,
            max_stops=leg.max_stops,
            adults=passengers,
        )
    except Exception as exc:
        logger.warning("multi_leg SerpAPI fallback failed leg=%s: %s", leg.id, exc)
        return None

    if not flights:
        return None
    top = flights[0]
    try:
        leg_price = float(top.get("price"))
    except (TypeError, ValueError):
        return None
    if leg_price <= 0:
        return None
    return {
        "price": leg_price,
        "airline": top.get("airline") or "??",
        "source": source or "serpapi",
    }


def _persist_multi_snapshot(
    db: Session,
    group: RouteGroup,
    legs: list[RouteGroupLeg],
    best_combo: tuple[date, ...],
    prices: list[dict[str, Any]],
) -> FlightSnapshot | None:
    """Persiste FlightSnapshot multi com details JSON (Pattern 2)."""
    total = sum(p["price"] for p in prices)
    details = {
        "total_price": total,
        "legs": [
            {
                "order": leg.order,
                "origin": leg.origin,
                "destination": leg.destination,
                "date": best_combo[i].isoformat(),
                "price": prices[i]["price"],
                "airline": prices[i]["airline"],
            }
            for i, leg in enumerate(legs)
        ],
    }
    departure_date = best_combo[0]
    return_date = best_combo[-1]

    # Pitfall 2: dedup especifico airline=MULTI
    if snapshot_service.is_duplicate_snapshot(
        db,
        route_group_id=group.id,
        origin=legs[0].origin,
        destination=legs[-1].destination,
        departure_date=departure_date,
        return_date=return_date,
        price=total,
        airline="MULTI",
    ):
        logger.info("multi_leg: snapshot duplicado ignorado group=%s", group.id)
        return None

    snapshot = FlightSnapshot(
        route_group_id=group.id,
        origin=legs[0].origin,
        destination=legs[-1].destination,
        departure_date=departure_date,
        return_date=return_date,
        price=total,
        currency="BRL",
        airline="MULTI",
        source="multi_leg",
        details=details,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def _totals_stats(db: Session, group: RouteGroup) -> tuple[float | None, float | None, int]:
    """Mediana e stddev de totais dos snapshots multi do grupo nos ultimos 90 dias."""
    cutoff = datetime.utcnow() - timedelta(days=HISTORICAL_WINDOW_DAYS)
    rows = (
        db.query(FlightSnapshot.price)
        .filter(
            FlightSnapshot.route_group_id == group.id,
            FlightSnapshot.airline == "MULTI",
            FlightSnapshot.collected_at >= cutoff,
        )
        .all()
    )
    prices = sorted(r[0] for r in rows if r[0] is not None)
    count = len(prices)
    if count == 0:
        return None, None, 0
    mid = count // 2
    median = prices[mid] if count % 2 == 1 else (prices[mid - 1] + prices[mid]) / 2
    mean = sum(prices) / count
    var = sum((p - mean) ** 2 for p in prices) / count
    stddev = var ** 0.5
    return median, stddev, count


def _maybe_predict(db: Session, snapshot: FlightSnapshot, group: RouteGroup) -> None:
    """Chama price_prediction_service.predict_action com days_to_departure do primeiro leg.

    Pitfall 3: departure_date do snapshot multi ja representa o primeiro leg
    por convencao (Pattern 2). A recomendacao e logada; persistencia e
    responsabilidade do caller/Phase 34 caso aplicavel.
    """
    median, stddev, count = _totals_stats(db, group)
    days_to_departure = (snapshot.departure_date - date.today()).days
    try:
        price_prediction_service.predict_action(
            current_price=snapshot.price,
            median_90d=median,
            stddev_90d=stddev,
            days_to_departure=days_to_departure,
            snapshot_count=count,
            departure_date=snapshot.departure_date,
        )
    except Exception as exc:
        logger.warning("multi_leg prediction failed group=%s: %s", group.id, exc)


def search_multi_leg_prices(
    db: Session, group: RouteGroup
) -> FlightSnapshot | None:
    """Busca precos multi-trecho e persiste 1 FlightSnapshot com details JSON.

    Algoritmo (D-13, Pattern 1):
    1. Para cada leg, amostra ate DATE_CANDIDATES_PER_LEG datas na janela
    2. Produto cartesiano das datas filtrado por _is_valid_chain
    3. Busca preco por leg (cache-first, SerpAPI fallback)
    4. Escolhe combinacao de menor total
    5. Persiste snapshot e dispara predict_action sobre o total
    Retorna None se nao encontrar combinacao com precos completos.
    """
    legs = sorted(group.legs, key=lambda l: l.order)
    if len(legs) < 2:
        logger.warning(
            "multi_leg: group %s tem menos de 2 legs, ignorando", group.id
        )
        return None

    candidate_sets = [_candidate_dates(leg) for leg in legs]
    if any(len(c) == 0 for c in candidate_sets):
        logger.info("multi_leg: group %s tem leg com janela vazia", group.id)
        return None

    passengers = group.passengers or 1

    best_total: float | None = None
    best_combo: tuple[date, ...] | None = None
    best_prices: list[dict[str, Any]] | None = None

    for combo in itertools.product(*candidate_sets):
        if not _is_valid_chain(combo, legs):
            continue
        leg_prices: list[dict[str, Any]] = []
        complete = True
        for leg, dep_date in zip(legs, combo):
            p = _fetch_leg_price(db, leg, dep_date, passengers)
            if p is None:
                complete = False
                break
            leg_prices.append(p)
        if not complete:
            continue
        total = sum(p["price"] for p in leg_prices)
        if best_total is None or total < best_total:
            best_total = total
            best_combo = combo
            best_prices = leg_prices

    if best_combo is None or best_prices is None:
        logger.info(
            "multi_leg: nenhuma combinacao valida para group %s", group.id
        )
        return None

    snapshot = _persist_multi_snapshot(db, group, legs, best_combo, best_prices)
    if snapshot is not None:
        _maybe_predict(db, snapshot, group)
    return snapshot
