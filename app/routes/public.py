"""Rotas publicas SEO (Phase 33).

Sem autenticacao. Serve 100% do banco local (RouteCache + FlightSnapshot)
sem chamadas externas (SerpAPI, Travelpayouts).
"""
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import FlightSnapshot
from app.services.affiliate_links import build_aviasales_url, default_trip_dates
from app.services.dashboard_service import format_date_br, format_price_brl
from app.services.public_route_service import MIN_SNAPSHOTS_FOR_INDEX, get_route_stats
from app.services.public_share_card_service import build_public_og_card
from app.templates_config import get_templates

router = APIRouter(tags=["public"])
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = get_templates(str(_TEMPLATES_DIR))

IATA_PAIR = re.compile(r"^([A-Za-z]{3})-([A-Za-z]{3})$")
PUBLIC_CACHE_SECONDS = 21600  # 6h, alinhado com TTL do route_cache


@router.get("/rotas/{pair}", response_class=HTMLResponse)
def public_route_page(
    pair: str,
    request: Request,
    db: Session = Depends(get_db),
):
    m = IATA_PAIR.match(pair)
    if not m:
        raise HTTPException(status_code=404, detail="Rota nao encontrada")
    origin, destination = m.group(1).upper(), m.group(2).upper()

    stats = get_route_stats(db, origin, destination)
    if stats is None:
        raise HTTPException(status_code=404, detail="Rota sem dados suficientes")

    base = settings.app_base_url.rstrip("/")
    canonical = f"{base}/rotas/{origin}-{destination}"
    og_image = f"{base}/rotas/{origin}-{destination}/og-image.png"

    # Usar as datas reais do preco mostrado pra alinhar com o checkout Aviasales.
    # Fallback pra default_trip_dates quando nao houver data (rota sem cache/snapshot).
    dep = stats.get("current_departure_date")
    ret = stats.get("current_return_date")
    if dep is None:
        dep, ret = default_trip_dates()
    affiliate_url = build_aviasales_url(
        origin, destination, dep, ret, settings.travelpayouts_marker
    )
    response = templates.TemplateResponse(
        request=request,
        name="public/route.html",
        context={
            "stats": stats,
            "canonical": canonical,
            "og_image": og_image,
            "affiliate_url": affiliate_url,
            "format_price_brl": format_price_brl,
            "format_date_br": format_date_br,
            "user": None,
        },
    )
    response.headers["Cache-Control"] = f"public, max-age={PUBLIC_CACHE_SECONDS}"
    return response


@router.get("/rotas/{pair}/og-image.png")
def public_route_og_image(
    pair: str,
    db: Session = Depends(get_db),
):
    m = IATA_PAIR.match(pair)
    if not m:
        raise HTTPException(status_code=404, detail="Rota invalida")
    origin, destination = m.group(1).upper(), m.group(2).upper()
    stats = get_route_stats(db, origin, destination)
    if stats is None:
        raise HTTPException(status_code=404, detail="Rota sem dados")
    png_bytes = build_public_og_card(
        origin=origin,
        dest=destination,
        current_price=stats["current_price"],
        median_180d=stats["median_180d"],
        origin_city=stats["origin_city"],
        dest_city=stats["destination_city"],
    )
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Cache-Control": f"public, max-age={PUBLIC_CACHE_SECONDS}"},
    )


@router.get("/sitemap.xml")
def sitemap_xml(db: Session = Depends(get_db)):
    rows = (
        db.query(
            FlightSnapshot.origin,
            FlightSnapshot.destination,
            func.count(FlightSnapshot.id).label("cnt"),
            func.max(FlightSnapshot.collected_at).label("last"),
        )
        .group_by(FlightSnapshot.origin, FlightSnapshot.destination)
        .having(func.count(FlightSnapshot.id) >= MIN_SNAPSHOTS_FOR_INDEX)
        .all()
    )
    base = settings.app_base_url.rstrip("/")
    items = []
    for origin, destination, _cnt, last in rows:
        lastmod = last.date().isoformat() if last else ""
        items.append(
            "  <url>\n"
            f"    <loc>{base}/rotas/{origin}-{destination}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            "    <changefreq>daily</changefreq>\n"
            "    <priority>0.7</priority>\n"
            "  </url>"
        )
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ("\n".join(items) + "\n" if items else "")
        + "</urlset>\n"
    )
    return Response(
        content=body,
        media_type="application/xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    base = settings.app_base_url.rstrip("/")
    body = (
        "User-agent: *\n"
        "Allow: /rotas/\n"
        "Disallow: /admin/\n"
        "Disallow: /auth/\n"
        "Disallow: /groups/\n"
        "Disallow: /api/\n"
        f"Sitemap: {base}/sitemap.xml\n"
    )
    return PlainTextResponse(
        body, headers={"Cache-Control": "public, max-age=86400"}
    )
