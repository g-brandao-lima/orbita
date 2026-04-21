"""Mapeamento IATA->cidade (Phase 33 Plan 01)."""
from app.services.iata_cities import IATA_CITIES, iata_to_city


def test_iata_to_city_known_br():
    assert iata_to_city("GRU") == "Sao Paulo"
    assert iata_to_city("GIG") == "Rio de Janeiro"


def test_iata_to_city_known_international():
    assert iata_to_city("LIS") == "Lisboa"


def test_iata_to_city_unknown_returns_code():
    assert iata_to_city("ZZZ") == "ZZZ"


def test_iata_to_city_accepts_lowercase():
    assert iata_to_city("gru") == "Sao Paulo"


def test_iata_cities_covers_top_br_routes():
    from app.services.route_cache_service import TOP_BR_ROUTES
    for origin, destination in TOP_BR_ROUTES:
        assert origin in IATA_CITIES, f"IATA {origin} missing"
        assert destination in IATA_CITIES, f"IATA {destination} missing"
