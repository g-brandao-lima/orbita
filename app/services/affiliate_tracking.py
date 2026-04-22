"""Rastreamento proprio de cliques no botao 'Comprar agora' (afiliado).

Grava cada clique na tabela affiliate_click antes de redirecionar pro
Aviasales. Nao depende de API externa pra contabilizar cliques.
Para bookings/comissao, usuario consulta dashboard Travelpayouts.
"""
import datetime
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import AffiliateClick

logger = logging.getLogger(__name__)


def log_click(
    db: Session,
    origin: str,
    destination: str,
    departure_date: datetime.date | None = None,
    return_date: datetime.date | None = None,
    user_id: int | None = None,
    referer: str | None = None,
    source: str = "public_route",
) -> None:
    """Grava um clique. Best-effort: erros nao impedem redirect."""
    try:
        entry = AffiliateClick(
            origin=origin.upper(),
            destination=destination.upper(),
            departure_date=departure_date,
            return_date=return_date,
            user_id=user_id,
            referer=(referer or "")[:500] or None,
            source=source,
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        logger.warning("affiliate_click log failed: %s", e)


def get_click_stats(db: Session, days: int = 7) -> dict:
    """Agregado dos ultimos N dias.

    Retorna:
      total: int
      by_source: {source: count}
      by_route: [{route: "ORIG-DEST", count: N}, ...] top 10
      by_day: [{date: "YYYY-MM-DD", count: N}, ...]
    """
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=days)

    total = (
        db.query(func.count(AffiliateClick.id))
        .filter(AffiliateClick.clicked_at >= cutoff)
        .scalar()
    ) or 0

    by_source_rows = (
        db.query(AffiliateClick.source, func.count(AffiliateClick.id))
        .filter(AffiliateClick.clicked_at >= cutoff)
        .group_by(AffiliateClick.source)
        .all()
    )
    by_source = {src or "unknown": cnt for src, cnt in by_source_rows}

    by_route_rows = (
        db.query(
            AffiliateClick.origin,
            AffiliateClick.destination,
            func.count(AffiliateClick.id).label("cnt"),
        )
        .filter(AffiliateClick.clicked_at >= cutoff)
        .group_by(AffiliateClick.origin, AffiliateClick.destination)
        .order_by(func.count(AffiliateClick.id).desc())
        .limit(10)
        .all()
    )
    by_route = [
        {"route": f"{o}-{d}", "count": c} for o, d, c in by_route_rows
    ]

    return {
        "total": total,
        "days": days,
        "by_source": by_source,
        "by_route": by_route,
    }
