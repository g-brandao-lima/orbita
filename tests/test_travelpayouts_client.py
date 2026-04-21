"""Testes do cliente Travelpayouts (Phase 32 Plan 02)."""
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.services.travelpayouts_client import TravelpayoutsClient


def _mock_response(body: dict, status: int = 200):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    if status >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "boom", request=MagicMock(), response=resp
        )
    return resp


def test_is_configured_false_when_no_token():
    assert TravelpayoutsClient(token="").is_configured is False


def test_is_configured_true_when_token():
    assert TravelpayoutsClient(token="abc").is_configured is True


@patch("app.services.travelpayouts_client.httpx.Client")
def test_fetch_calendar_happy_path(mock_client_cls):
    ctx = MagicMock()
    ctx.__enter__.return_value = ctx
    ctx.__exit__.return_value = False
    ctx.get.return_value = _mock_response({
        "success": True,
        "data": {
            "2026-09-01": {"price": 2800, "airline": "TP", "return_at": "2026-09-15T14:00:00"},
            "2026-09-02": {"price": 2900, "airline": "LA", "return_at": "2026-09-16T14:00:00"},
        },
    })
    mock_client_cls.return_value = ctx

    client = TravelpayoutsClient(token="tkn")
    items = client.fetch_calendar(origin="GRU", destination="LIS", depart_month="2026-09")

    assert len(items) == 2
    assert all(i["origin"] == "GRU" for i in items)
    assert all(i["destination"] == "LIS" for i in items)
    prices = sorted(i["min_price"] for i in items)
    assert prices == [2800.0, 2900.0]


@patch("app.services.travelpayouts_client.httpx.Client")
def test_fetch_calendar_preserves_requested_iata(mock_client_cls):
    ctx = MagicMock()
    ctx.__enter__.return_value = ctx
    ctx.__exit__.return_value = False
    ctx.get.return_value = _mock_response({
        "success": True,
        "data": {
            "2026-09-01": {"price": 2800, "airline": "TP", "origin": "SAO", "destination": "LIS"},
        },
    })
    mock_client_cls.return_value = ctx

    client = TravelpayoutsClient(token="tkn")
    items = client.fetch_calendar(origin="GRU", destination="LIS", depart_month="2026-09")

    assert items[0]["origin"] == "GRU"


@patch("app.services.travelpayouts_client.httpx.Client")
def test_fetch_calendar_sends_x_access_token_header(mock_client_cls):
    ctx = MagicMock()
    ctx.__enter__.return_value = ctx
    ctx.__exit__.return_value = False
    ctx.get.return_value = _mock_response({"success": True, "data": {}})
    mock_client_cls.return_value = ctx

    client = TravelpayoutsClient(token="my-secret-token")
    client.fetch_calendar(origin="GRU", destination="LIS", depart_month="2026-09")

    _, kwargs = ctx.get.call_args
    assert kwargs["headers"]["X-Access-Token"] == "my-secret-token"


@patch("app.services.travelpayouts_client.httpx.Client")
def test_fetch_cheap_happy_path(mock_client_cls):
    ctx = MagicMock()
    ctx.__enter__.return_value = ctx
    ctx.__exit__.return_value = False
    ctx.get.return_value = _mock_response({
        "success": True,
        "data": {
            "LIS": {
                "1": {
                    "price": 2800,
                    "airline": "TP",
                    "departure_at": "2026-09-01T10:00:00",
                    "return_at": "2026-09-15T14:00:00",
                }
            }
        },
    })
    mock_client_cls.return_value = ctx

    client = TravelpayoutsClient(token="tkn")
    items = client.fetch_cheap(origin="GRU", destination="LIS")

    assert len(items) == 1
    assert items[0]["origin"] == "GRU"
    assert items[0]["destination"] == "LIS"
    assert items[0]["departure_date"] == "2026-09-01"
    assert items[0]["return_date"] == "2026-09-15"
    assert items[0]["min_price"] == 2800.0


@patch("app.services.travelpayouts_client.httpx.Client")
def test_fetch_month_matrix_happy_path(mock_client_cls):
    ctx = MagicMock()
    ctx.__enter__.return_value = ctx
    ctx.__exit__.return_value = False
    ctx.get.return_value = _mock_response({
        "success": True,
        "data": [
            {"depart_date": "2026-09-01", "return_date": "2026-09-15", "value": 2800, "airline": "TP"},
        ],
    })
    mock_client_cls.return_value = ctx

    client = TravelpayoutsClient(token="tkn")
    items = client.fetch_month_matrix(origin="GRU", destination="LIS")

    assert len(items) == 1
    assert items[0]["origin"] == "GRU"
    assert items[0]["min_price"] == 2800.0
    assert items[0]["departure_date"] == "2026-09-01"


@patch("app.services.travelpayouts_client.httpx.Client")
def test_http_error_returns_empty_list(mock_client_cls):
    ctx = MagicMock()
    ctx.__enter__.return_value = ctx
    ctx.__exit__.return_value = False
    ctx.get.side_effect = httpx.ConnectError("network down")
    mock_client_cls.return_value = ctx

    client = TravelpayoutsClient(token="tkn")
    assert client.fetch_calendar(origin="GRU", destination="LIS", depart_month="2026-09") == []


@patch("app.services.travelpayouts_client.httpx.Client")
def test_api_failure_returns_empty_list(mock_client_cls):
    ctx = MagicMock()
    ctx.__enter__.return_value = ctx
    ctx.__exit__.return_value = False
    ctx.get.return_value = _mock_response({"success": False, "error": "rate limited"})
    mock_client_cls.return_value = ctx

    client = TravelpayoutsClient(token="tkn")
    assert client.fetch_calendar(origin="GRU", destination="LIS", depart_month="2026-09") == []
