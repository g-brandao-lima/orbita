"""Cliente para Travelpayouts Data API (Aviasales).

Autentica via header X-Access-Token. Normaliza respostas num formato uniforme
preservando o IATA aeroporto pedido (nao IATA cidade retornado pela API).
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.travelpayouts.com"


class TravelpayoutsClient:
    def __init__(self, token: str | None = None, timeout: float = 15.0):
        self._token = token if token is not None else settings.travelpayouts_token
        self._timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self._token)

    def _headers(self) -> dict:
        return {"X-Access-Token": self._token, "Accept": "application/json"}

    def _get(self, path: str, params: dict) -> dict | None:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.get(
                    f"{BASE_URL}{path}", params=params, headers=self._headers()
                )
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as e:
            logger.warning("travelpayouts HTTP error on %s: %s", path, e)
            return None
        if not body.get("success"):
            logger.warning(
                "travelpayouts api failure on %s: %s", path, body.get("error")
            )
            return None
        return body

    def fetch_calendar(
        self,
        origin: str,
        destination: str,
        depart_month: str,
        currency: str = "BRL",
    ) -> list[dict]:
        """GET /v1/prices/calendar — preco dia-a-dia do mes."""
        body = self._get(
            "/v1/prices/calendar",
            {
                "origin": origin,
                "destination": destination,
                "depart_date": depart_month,
                "currency": currency.lower(),
            },
        )
        if not body:
            return []
        results = []
        for depart_date, entry in (body.get("data") or {}).items():
            if not entry or "price" not in entry:
                continue
            return_at = entry.get("return_at")
            return_date = return_at[:10] if return_at else None
            results.append({
                "origin": origin,
                "destination": destination,
                "departure_date": depart_date,
                "return_date": return_date,
                "min_price": float(entry["price"]),
                "currency": currency.upper(),
                "airline": entry.get("airline"),
            })
        return results

    def fetch_cheap(
        self, origin: str, destination: str, currency: str = "BRL"
    ) -> list[dict]:
        """GET /v1/prices/cheap — preco mais barato por destino."""
        body = self._get(
            "/v1/prices/cheap",
            {
                "origin": origin,
                "destination": destination,
                "currency": currency.lower(),
            },
        )
        if not body:
            return []
        results = []
        destinations_block = body.get("data") or {}
        for _dest_code, offers in destinations_block.items():
            for _idx, offer in (offers or {}).items():
                if "price" not in offer:
                    continue
                dep_at = offer.get("departure_at")
                ret_at = offer.get("return_at")
                results.append({
                    "origin": origin,
                    "destination": destination,
                    "departure_date": dep_at[:10] if dep_at else None,
                    "return_date": ret_at[:10] if ret_at else None,
                    "min_price": float(offer["price"]),
                    "currency": currency.upper(),
                    "airline": offer.get("airline"),
                })
        return results

    def fetch_month_matrix(
        self, origin: str, destination: str, currency: str = "BRL"
    ) -> list[dict]:
        """GET /v2/prices/month-matrix — matriz mes inteiro."""
        body = self._get(
            "/v2/prices/month-matrix",
            {
                "origin": origin,
                "destination": destination,
                "currency": currency.lower(),
                "show_to_affiliates": "true",
            },
        )
        if not body:
            return []
        results = []
        for entry in body.get("data") or []:
            if "value" not in entry and "price" not in entry:
                continue
            price = entry.get("value") or entry.get("price")
            results.append({
                "origin": origin,
                "destination": destination,
                "departure_date": entry.get("depart_date"),
                "return_date": entry.get("return_date") or None,
                "min_price": float(price),
                "currency": currency.upper(),
                "airline": entry.get("airline"),
            })
        return results
