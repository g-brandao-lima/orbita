from app.services.airport_service import get_all_airports, is_valid_code, search_airports


class TestGetAllAirports:
    def test_returns_list(self):
        airports = get_all_airports()
        assert isinstance(airports, list)
        assert len(airports) > 100

    def test_each_airport_has_required_fields(self):
        airports = get_all_airports()
        for a in airports[:10]:
            assert "code" in a
            assert "name" in a
            assert "city" in a
            assert "country" in a


class TestIsValidCode:
    def test_valid_brazilian_airport(self):
        assert is_valid_code("GRU") is True

    def test_valid_international_airport(self):
        assert is_valid_code("LIS") is True

    def test_invalid_code(self):
        assert is_valid_code("XYZ") is False

    def test_case_insensitive(self):
        assert is_valid_code("gru") is True

    def test_empty_string(self):
        assert is_valid_code("") is False


class TestSearchAirports:
    def test_search_by_city(self):
        results = search_airports("Lisboa")
        codes = [r["code"] for r in results]
        assert "LIS" in codes

    def test_search_by_code(self):
        results = search_airports("GRU")
        assert len(results) >= 1
        assert results[0]["code"] == "GRU"

    def test_search_by_country(self):
        results = search_airports("Portugal")
        codes = [r["code"] for r in results]
        assert "LIS" in codes
        assert "OPO" in codes

    def test_search_limit(self):
        results = search_airports("a", limit=5)
        assert len(results) <= 5

    def test_search_no_results(self):
        results = search_airports("zzzzzzz")
        assert results == []
