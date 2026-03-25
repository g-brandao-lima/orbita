from unittest.mock import patch, MagicMock
import pytest

from app.services.amadeus_client import AmadeusClient, classify_price


# --- Fixtures ---


def _make_offers(prices: list[str]) -> list[dict]:
    """Cria lista de flight-offer dicts com precos dados."""
    return [
        {
            "price": {"grandTotal": p},
            "itineraries": [{"segments": []}],
            "validatingAirlineCodes": ["LA"],
        }
        for p in prices
    ]


def _make_availability_response() -> list[dict]:
    return [
        {
            "segments": [
                {
                    "availabilityClasses": [
                        {"class": "Y", "numberOfBookableSeats": 9},
                        {"class": "B", "numberOfBookableSeats": 4},
                    ]
                }
            ]
        }
    ]


def _make_price_metrics() -> list[dict]:
    return [
        {
            "priceMetrics": [
                {"amount": "150.00", "quartileRanking": "MINIMUM"},
                {"amount": "250.00", "quartileRanking": "FIRST"},
                {"amount": "400.00", "quartileRanking": "MEDIUM"},
                {"amount": "600.00", "quartileRanking": "THIRD"},
                {"amount": "900.00", "quartileRanking": "MAXIMUM"},
            ]
        }
    ]


# --- is_configured tests ---


@patch("app.services.amadeus_client.Client")
@patch("app.services.amadeus_client.settings")
def test_client_not_configured_without_credentials(mock_settings, mock_client_cls):
    mock_settings.amadeus_client_id = ""
    mock_settings.amadeus_client_secret = ""
    client = AmadeusClient()
    assert client.is_configured is False
    mock_client_cls.assert_not_called()


@patch("app.services.amadeus_client.Client")
@patch("app.services.amadeus_client.settings")
def test_client_configured_with_credentials(mock_settings, mock_client_cls):
    mock_settings.amadeus_client_id = "test_id"
    mock_settings.amadeus_client_secret = "test_secret"
    client = AmadeusClient()
    assert client.is_configured is True
    mock_client_cls.assert_called_once_with(
        client_id="test_id", client_secret="test_secret"
    )


# --- search_cheapest_offers tests ---


@patch("app.services.amadeus_client.Client")
@patch("app.services.amadeus_client.settings")
def test_search_cheapest_offers_returns_top_5(mock_settings, mock_client_cls):
    mock_settings.amadeus_client_id = "test_id"
    mock_settings.amadeus_client_secret = "test_secret"

    prices = ["500", "300", "450", "200", "350", "600", "150", "400", "250", "550"]
    mock_response = MagicMock()
    mock_response.data = _make_offers(prices)

    mock_sdk = MagicMock()
    mock_sdk.shopping.flight_offers_search.get.return_value = mock_response
    mock_client_cls.return_value = mock_sdk

    client = AmadeusClient()
    result = client.search_cheapest_offers("GRU", "GIG", "2026-05-01", "2026-05-08")

    assert len(result) == 5
    result_prices = [float(r["price"]["grandTotal"]) for r in result]
    assert result_prices == [150.0, 200.0, 250.0, 300.0, 350.0]


@patch("app.services.amadeus_client.Client")
@patch("app.services.amadeus_client.settings")
def test_search_cheapest_offers_returns_less_if_fewer_available(
    mock_settings, mock_client_cls
):
    mock_settings.amadeus_client_id = "test_id"
    mock_settings.amadeus_client_secret = "test_secret"

    mock_response = MagicMock()
    mock_response.data = _make_offers(["300", "200"])

    mock_sdk = MagicMock()
    mock_sdk.shopping.flight_offers_search.get.return_value = mock_response
    mock_client_cls.return_value = mock_sdk

    client = AmadeusClient()
    result = client.search_cheapest_offers("GRU", "GIG", "2026-05-01", "2026-05-08")

    assert len(result) == 2
    result_prices = [float(r["price"]["grandTotal"]) for r in result]
    assert result_prices == [200.0, 300.0]


# --- get_availability tests ---


@patch("app.services.amadeus_client.Client")
@patch("app.services.amadeus_client.settings")
def test_get_availability_returns_booking_classes(mock_settings, mock_client_cls):
    mock_settings.amadeus_client_id = "test_id"
    mock_settings.amadeus_client_secret = "test_secret"

    mock_response = MagicMock()
    mock_response.data = _make_availability_response()

    mock_sdk = MagicMock()
    mock_sdk.shopping.availability.flight_availabilities.post.return_value = (
        mock_response
    )
    mock_client_cls.return_value = mock_sdk

    client = AmadeusClient()
    result = client.get_availability("GRU", "GIG", "2026-05-01", "2026-05-08")

    assert len(result) == 1
    assert result[0]["segments"][0]["availabilityClasses"][0]["class"] == "Y"
    assert (
        result[0]["segments"][0]["availabilityClasses"][0]["numberOfBookableSeats"] == 9
    )


# --- get_price_metrics tests ---


@patch("app.services.amadeus_client.Client")
@patch("app.services.amadeus_client.settings")
def test_get_price_metrics_returns_data(mock_settings, mock_client_cls):
    mock_settings.amadeus_client_id = "test_id"
    mock_settings.amadeus_client_secret = "test_secret"

    mock_response = MagicMock()
    mock_response.data = _make_price_metrics()

    mock_sdk = MagicMock()
    mock_sdk.analytics.itinerary_price_metrics.get.return_value = mock_response
    mock_client_cls.return_value = mock_sdk

    client = AmadeusClient()
    result = client.get_price_metrics("GRU", "GIG", "2026-05-01")

    assert result is not None
    assert len(result) == 1
    assert len(result[0]["priceMetrics"]) == 5


@patch("app.services.amadeus_client.Client")
@patch("app.services.amadeus_client.settings")
def test_get_price_metrics_returns_none_on_404(mock_settings, mock_client_cls):
    mock_settings.amadeus_client_id = "test_id"
    mock_settings.amadeus_client_secret = "test_secret"

    from amadeus import ResponseError

    mock_sdk = MagicMock()
    mock_http_response = MagicMock()
    mock_http_response.status_code = 404
    mock_http_response.result = {"errors": [{"detail": "not found"}]}
    mock_sdk.analytics.itinerary_price_metrics.get.side_effect = ResponseError(
        mock_http_response
    )
    mock_client_cls.return_value = mock_sdk

    client = AmadeusClient()
    result = client.get_price_metrics("GRU", "GIG", "2026-05-01")

    assert result is None


# --- classify_price tests ---


def test_classify_price_low():
    metrics = _make_price_metrics()[0]["priceMetrics"]
    result = classify_price(200.0, metrics)
    assert result == "LOW"


def test_classify_price_medium():
    metrics = _make_price_metrics()[0]["priceMetrics"]
    result = classify_price(300.0, metrics)
    assert result == "MEDIUM"


def test_classify_price_high():
    metrics = _make_price_metrics()[0]["priceMetrics"]
    result = classify_price(500.0, metrics)
    assert result == "HIGH"


def test_classify_price_no_metrics():
    result = classify_price(300.0, [])
    assert result is None
