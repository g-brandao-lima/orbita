"""Construtor de links de afiliado (monetizacao SEO-05).

Aviasales e o motor de busca da Travelpayouts. O marker identifica o afiliado
e atribui a comissao. Formato:
  https://www.aviasales.com/search/{ORIG}{DDMM}{DEST}{DDMM}{PAX}?marker={MARKER}
"""
import datetime

DEFAULT_TRIP_OFFSET_DAYS = 60
DEFAULT_STAY_DAYS = 10


def default_trip_dates(
    today: datetime.date | None = None,
) -> tuple[datetime.date, datetime.date]:
    today = today or datetime.date.today()
    departure = today + datetime.timedelta(days=DEFAULT_TRIP_OFFSET_DAYS)
    return_ = departure + datetime.timedelta(days=DEFAULT_STAY_DAYS)
    return departure, return_


def _ddmm(d: datetime.date) -> str:
    return f"{d.day:02d}{d.month:02d}"


def build_aviasales_url(
    origin: str,
    destination: str,
    departure: datetime.date,
    return_: datetime.date,
    marker: str | None = None,
    passengers: int = 1,
) -> str:
    origin = origin.upper()
    destination = destination.upper()
    path = f"{origin}{_ddmm(departure)}{destination}{_ddmm(return_)}{max(1, passengers)}"
    url = f"https://www.aviasales.com/search/{path}"
    if marker:
        url += f"?marker={marker}"
    return url
