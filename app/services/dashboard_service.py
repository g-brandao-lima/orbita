import datetime
from datetime import timedelta

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.models import RouteGroup, FlightSnapshot, DetectedSignal


def get_groups_with_summary(db: Session) -> list[dict]:
    """Return all route groups with cheapest snapshot and most urgent recent signal."""
    groups = db.query(RouteGroup).all()
    result = []

    for group in groups:
        # Find most recent collected_at for this group
        latest_collected = (
            db.query(func.max(FlightSnapshot.collected_at))
            .filter(FlightSnapshot.route_group_id == group.id)
            .scalar()
        )

        cheapest_snapshot = None
        if latest_collected is not None:
            cheapest_snapshot = (
                db.query(FlightSnapshot)
                .filter(
                    FlightSnapshot.route_group_id == group.id,
                    FlightSnapshot.collected_at == latest_collected,
                )
                .order_by(FlightSnapshot.price.asc())
                .first()
            )

        # Find most urgent signal in the last 12 hours
        cutoff = datetime.datetime.utcnow() - timedelta(hours=12)
        urgency_order = case(
            (DetectedSignal.urgency == "MAXIMA", 3),
            (DetectedSignal.urgency == "ALTA", 2),
            (DetectedSignal.urgency == "MEDIA", 1),
            else_=0,
        )
        signal = (
            db.query(DetectedSignal)
            .filter(
                DetectedSignal.route_group_id == group.id,
                DetectedSignal.detected_at >= cutoff,
            )
            .order_by(urgency_order.desc())
            .first()
        )

        result.append({
            "group": group,
            "cheapest_snapshot": cheapest_snapshot,
            "signal": signal,
        })

    return result


def get_price_history(db: Session, group_id: int, days: int = 14) -> dict:
    """Return price history labels and prices for the cheapest route of a group."""
    cutoff = datetime.datetime.utcnow() - timedelta(days=days)

    # Find the cheapest route (origin, destination) by average price
    cheapest_route = (
        db.query(FlightSnapshot.origin, FlightSnapshot.destination)
        .filter(
            FlightSnapshot.route_group_id == group_id,
            FlightSnapshot.collected_at >= cutoff,
        )
        .group_by(FlightSnapshot.origin, FlightSnapshot.destination)
        .order_by(func.min(FlightSnapshot.price).asc())
        .first()
    )

    if cheapest_route is None:
        return {"labels": [], "prices": [], "route": ""}

    origin, destination = cheapest_route

    snapshots = (
        db.query(FlightSnapshot)
        .filter(
            FlightSnapshot.route_group_id == group_id,
            FlightSnapshot.origin == origin,
            FlightSnapshot.destination == destination,
            FlightSnapshot.collected_at >= cutoff,
        )
        .order_by(FlightSnapshot.collected_at.asc())
        .all()
    )

    labels = [s.collected_at.strftime("%d/%m %Hh") for s in snapshots]
    prices = [s.price for s in snapshots]

    return {
        "labels": labels,
        "prices": prices,
        "route": f"{origin} -> {destination}",
    }


def get_dashboard_summary(db: Session) -> dict:
    """Return summary metrics for the dashboard: active count, cheapest price, next polling."""
    active_count = (
        db.query(func.count())
        .select_from(RouteGroup)
        .where(RouteGroup.is_active == True)  # noqa: E712
        .scalar()
    )

    # Find cheapest price across all active groups' latest snapshots
    cheapest_price = None
    active_groups = db.query(RouteGroup).filter(RouteGroup.is_active == True).all()  # noqa: E712
    for group in active_groups:
        latest_collected = (
            db.query(func.max(FlightSnapshot.collected_at))
            .filter(FlightSnapshot.route_group_id == group.id)
            .scalar()
        )
        if latest_collected is not None:
            min_price = (
                db.query(func.min(FlightSnapshot.price))
                .filter(
                    FlightSnapshot.route_group_id == group.id,
                    FlightSnapshot.collected_at == latest_collected,
                )
                .scalar()
            )
            if min_price is not None:
                if cheapest_price is None or min_price < cheapest_price:
                    cheapest_price = min_price

    # Next polling from scheduler
    try:
        from app.scheduler import scheduler
        job = scheduler.get_job("polling_cycle")
        if job and job.next_run_time:
            next_polling = job.next_run_time.strftime("%H:%M")
        else:
            next_polling = "Automatico (1x/dia)"
    except Exception:
        next_polling = "Automatico (1x/dia)"

    return {
        "active_count": active_count,
        "cheapest_price": cheapest_price,
        "next_polling": next_polling,
    }


def format_date_br(d: datetime.date | None) -> str:
    """Format a date as dd/mm/aaaa Brazilian format."""
    if d is None:
        return ""
    return d.strftime("%d/%m/%Y")


def format_price_brl(price: float) -> str:
    """Format a float price as Brazilian Real string: R$ X.XXX,XX."""
    formatted = f"R$ {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return formatted
