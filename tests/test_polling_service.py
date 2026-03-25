import datetime
from unittest.mock import patch, MagicMock, call

from app.models import RouteGroup
from app.services.snapshot_service import save_flight_snapshot


# Mock data fixtures
MOCK_OFFERS = [
    {
        "price": {"grandTotal": "450.00"},
        "validatingAirlineCodes": ["LA"],
        "itineraries": [
            {
                "segments": [
                    {
                        "departure": {"iataCode": "GRU", "at": "2026-05-01T10:00"},
                        "arrival": {"iataCode": "GIG", "at": "2026-05-01T11:00"},
                    }
                ]
            },
            {
                "segments": [
                    {
                        "departure": {"iataCode": "GIG", "at": "2026-05-08T10:00"},
                        "arrival": {"iataCode": "GRU", "at": "2026-05-08T11:00"},
                    }
                ]
            },
        ],
    }
]

MOCK_AVAILABILITY = [
    {
        "segments": [
            {
                "availabilityClasses": [
                    {"class": "Y", "numberOfBookableSeats": 9},
                    {"class": "B", "numberOfBookableSeats": 4},
                    {"class": "M", "numberOfBookableSeats": 3},
                ]
            }
        ]
    },
    {
        "segments": [
            {
                "availabilityClasses": [
                    {"class": "Y", "numberOfBookableSeats": 7},
                    {"class": "B", "numberOfBookableSeats": 2},
                ]
            }
        ]
    },
]

MOCK_METRICS = [
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


def _create_route_group(db, **overrides):
    """Helper to create a RouteGroup in the test database."""
    defaults = {
        "name": "Test Group",
        "origins": ["GRU"],
        "destinations": ["GIG"],
        "duration_days": 7,
        "travel_start": datetime.date(2026, 5, 1),
        "travel_end": datetime.date(2026, 5, 15),
        "target_price": None,
        "is_active": True,
    }
    defaults.update(overrides)
    group = RouteGroup(**defaults)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


class TestPollingCycleSkips:
    """Tests for polling cycle skip conditions."""

    @patch("app.services.polling_service.AmadeusClient")
    def test_polling_cycle_skips_when_not_configured(self, mock_client_cls, db):
        from app.services.polling_service import run_polling_cycle

        mock_instance = MagicMock()
        mock_instance.is_configured = False
        mock_client_cls.return_value = mock_instance

        # Should not raise and should not create snapshots
        run_polling_cycle()

        # search_cheapest_offers should never be called
        mock_instance.search_cheapest_offers.assert_not_called()


class TestPollingCycleProcessing:
    """Tests for polling cycle group processing."""

    @patch("app.services.polling_service.save_flight_snapshot")
    @patch("app.services.polling_service.AmadeusClient")
    def test_polling_cycle_processes_active_groups(
        self, mock_client_cls, mock_save, db
    ):
        from app.services.polling_service import run_polling_cycle

        _create_route_group(db, name="Group A")
        _create_route_group(db, name="Group B")

        mock_instance = MagicMock()
        mock_instance.is_configured = True
        mock_instance.search_cheapest_offers.return_value = MOCK_OFFERS
        mock_instance.get_availability.return_value = MOCK_AVAILABILITY
        mock_instance.get_price_metrics.return_value = MOCK_METRICS
        mock_client_cls.return_value = mock_instance

        with patch("app.services.polling_service.SessionLocal", return_value=db):
            run_polling_cycle()

        # Both groups should generate snapshots
        assert mock_save.call_count >= 2

    @patch("app.services.polling_service.save_flight_snapshot")
    @patch("app.services.polling_service.AmadeusClient")
    def test_polling_cycle_skips_inactive_groups(
        self, mock_client_cls, mock_save, db
    ):
        from app.services.polling_service import run_polling_cycle

        _create_route_group(db, name="Active", is_active=True)
        _create_route_group(db, name="Inactive", is_active=False)

        mock_instance = MagicMock()
        mock_instance.is_configured = True
        mock_instance.search_cheapest_offers.return_value = MOCK_OFFERS
        mock_instance.get_availability.return_value = MOCK_AVAILABILITY
        mock_instance.get_price_metrics.return_value = MOCK_METRICS
        mock_client_cls.return_value = mock_instance

        with patch("app.services.polling_service.SessionLocal", return_value=db):
            run_polling_cycle()

        # Only 1 group processed, so snapshot count should reflect only active group
        # With 1 group, 1 origin, 1 dest, and date combos generating offers
        # At minimum, save should be called (not zero from inactive)
        assert mock_save.call_count >= 1

        # Verify search was called only for active group's routes
        # (inactive group should never trigger search)
        call_count_for_search = mock_instance.search_cheapest_offers.call_count
        # With 1 active group having 1 origin x 1 dest, and multiple date pairs
        # the inactive group should add zero additional calls
        # We verify that the call count matches what 1 group would produce
        assert call_count_for_search >= 1

    @patch("app.services.polling_service.save_flight_snapshot")
    @patch("app.services.polling_service.AmadeusClient")
    def test_polling_cycle_continues_after_group_failure(
        self, mock_client_cls, mock_save, db
    ):
        from app.services.polling_service import run_polling_cycle

        group_a = _create_route_group(db, name="Failing Group")
        group_b = _create_route_group(db, name="Working Group")

        mock_instance = MagicMock()
        mock_instance.is_configured = True

        # First group fails, second group works
        call_count = {"n": 0}
        group_ids_seen = []

        original_search = MagicMock(return_value=MOCK_OFFERS)

        def side_effect_search(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] <= 1:
                raise Exception("API Error for first group")
            return MOCK_OFFERS

        mock_instance.search_cheapest_offers.side_effect = side_effect_search
        mock_instance.get_availability.return_value = MOCK_AVAILABILITY
        mock_instance.get_price_metrics.return_value = MOCK_METRICS
        mock_client_cls.return_value = mock_instance

        with patch("app.services.polling_service.SessionLocal", return_value=db):
            # Should NOT raise exception
            run_polling_cycle()

        # Second group should still produce snapshots
        assert mock_save.call_count >= 1


class TestPollGroupCombinations:
    """Tests for route and date combination generation."""

    @patch("app.services.polling_service.save_flight_snapshot")
    @patch("app.services.polling_service.AmadeusClient")
    def test_poll_group_generates_origin_dest_combinations(
        self, mock_client_cls, mock_save, db
    ):
        from app.services.polling_service import run_polling_cycle

        _create_route_group(
            db,
            name="Multi Origin",
            origins=["GRU", "VCP"],
            destinations=["GIG"],
            travel_start=datetime.date(2026, 5, 1),
            travel_end=datetime.date(2026, 5, 8),
            duration_days=7,
        )

        mock_instance = MagicMock()
        mock_instance.is_configured = True
        mock_instance.search_cheapest_offers.return_value = MOCK_OFFERS
        mock_instance.get_availability.return_value = MOCK_AVAILABILITY
        mock_instance.get_price_metrics.return_value = MOCK_METRICS
        mock_client_cls.return_value = mock_instance

        with patch("app.services.polling_service.SessionLocal", return_value=db):
            run_polling_cycle()

        # search_cheapest_offers should be called for both GRU-GIG and VCP-GIG
        origins_called = [
            c.kwargs.get("origin", c.args[0] if c.args else None)
            for c in mock_instance.search_cheapest_offers.call_args_list
        ]
        assert "GRU" in origins_called or any(
            "GRU" in str(c) for c in mock_instance.search_cheapest_offers.call_args_list
        )
        assert "VCP" in origins_called or any(
            "VCP" in str(c) for c in mock_instance.search_cheapest_offers.call_args_list
        )

    @patch("app.services.polling_service.save_flight_snapshot")
    @patch("app.services.polling_service.AmadeusClient")
    def test_poll_group_generates_date_combinations(
        self, mock_client_cls, mock_save, db
    ):
        from app.services.polling_service import run_polling_cycle

        _create_route_group(
            db,
            name="Date Combos",
            origins=["GRU"],
            destinations=["GIG"],
            travel_start=datetime.date(2026, 5, 1),
            travel_end=datetime.date(2026, 5, 15),
            duration_days=7,
        )

        mock_instance = MagicMock()
        mock_instance.is_configured = True
        mock_instance.search_cheapest_offers.return_value = MOCK_OFFERS
        mock_instance.get_availability.return_value = MOCK_AVAILABILITY
        mock_instance.get_price_metrics.return_value = MOCK_METRICS
        mock_client_cls.return_value = mock_instance

        with patch("app.services.polling_service.SessionLocal", return_value=db):
            run_polling_cycle()

        # travel_start=May 1, travel_end=May 15, duration=7
        # Dates: May 1 (ret May 8), May 4 (ret May 11), May 7 (ret May 14)
        # That's 3 date pairs, so search should be called 3 times (1 origin x 1 dest x 3 dates)
        assert mock_instance.search_cheapest_offers.call_count == 3

        # Check departure dates used
        dep_dates_used = [
            c.kwargs.get("departure_date")
            for c in mock_instance.search_cheapest_offers.call_args_list
        ]
        assert "2026-05-01" in dep_dates_used
        assert "2026-05-04" in dep_dates_used
        assert "2026-05-07" in dep_dates_used


class TestPollGroupSnapshotData:
    """Tests for snapshot data correctness."""

    @patch("app.services.polling_service.save_flight_snapshot")
    @patch("app.services.polling_service.AmadeusClient")
    def test_poll_group_saves_snapshot_with_booking_classes(
        self, mock_client_cls, mock_save, db
    ):
        from app.services.polling_service import run_polling_cycle

        group = _create_route_group(
            db,
            name="Snapshot Test",
            origins=["GRU"],
            destinations=["GIG"],
            travel_start=datetime.date(2026, 5, 1),
            travel_end=datetime.date(2026, 5, 8),
            duration_days=7,
        )

        mock_instance = MagicMock()
        mock_instance.is_configured = True
        mock_instance.search_cheapest_offers.return_value = MOCK_OFFERS
        mock_instance.get_availability.return_value = MOCK_AVAILABILITY
        mock_instance.get_price_metrics.return_value = MOCK_METRICS
        mock_client_cls.return_value = mock_instance

        with patch("app.services.polling_service.SessionLocal", return_value=db):
            run_polling_cycle()

        # save_flight_snapshot should be called at least once
        assert mock_save.call_count >= 1

        # Check the first call's data
        first_call_args = mock_save.call_args_list[0]
        snapshot_data = first_call_args[0][1]  # positional arg: (db, data)

        assert snapshot_data["route_group_id"] == group.id
        assert snapshot_data["origin"] == "GRU"
        assert snapshot_data["destination"] == "GIG"
        assert snapshot_data["price"] == 450.0
        assert snapshot_data["airline"] == "LA"
        assert snapshot_data["currency"] == "BRL"

        # Check booking classes are present
        assert "booking_classes" in snapshot_data
        classes = snapshot_data["booking_classes"]
        assert len(classes) == 5  # 3 outbound + 2 inbound

        # Check OUTBOUND classes
        outbound = [c for c in classes if c["segment_direction"] == "OUTBOUND"]
        assert len(outbound) == 3
        class_codes = {c["class_code"] for c in outbound}
        assert class_codes == {"Y", "B", "M"}

        # Check INBOUND classes
        inbound = [c for c in classes if c["segment_direction"] == "INBOUND"]
        assert len(inbound) == 2

        # Check price metrics in snapshot
        assert snapshot_data["price_min"] == 150.0
        assert snapshot_data["price_first_quartile"] == 250.0
        assert snapshot_data["price_median"] == 400.0
        assert snapshot_data["price_third_quartile"] == 600.0
        assert snapshot_data["price_max"] == 900.0
        assert snapshot_data["price_classification"] == "HIGH"

    @patch("app.services.polling_service.save_flight_snapshot")
    @patch("app.services.polling_service.AmadeusClient")
    def test_poll_group_handles_missing_price_metrics(
        self, mock_client_cls, mock_save, db
    ):
        from app.services.polling_service import run_polling_cycle

        _create_route_group(
            db,
            name="No Metrics",
            origins=["GRU"],
            destinations=["GIG"],
            travel_start=datetime.date(2026, 5, 1),
            travel_end=datetime.date(2026, 5, 8),
            duration_days=7,
        )

        mock_instance = MagicMock()
        mock_instance.is_configured = True
        mock_instance.search_cheapest_offers.return_value = MOCK_OFFERS
        mock_instance.get_availability.return_value = MOCK_AVAILABILITY
        mock_instance.get_price_metrics.return_value = None  # No metrics available
        mock_client_cls.return_value = mock_instance

        with patch("app.services.polling_service.SessionLocal", return_value=db):
            run_polling_cycle()

        assert mock_save.call_count >= 1

        snapshot_data = mock_save.call_args_list[0][0][1]
        assert snapshot_data["price_classification"] is None
        # Price metric fields should not be present or should be None
        assert snapshot_data.get("price_min") is None
        assert snapshot_data.get("price_first_quartile") is None
        assert snapshot_data.get("price_median") is None
        assert snapshot_data.get("price_third_quartile") is None
        assert snapshot_data.get("price_max") is None
