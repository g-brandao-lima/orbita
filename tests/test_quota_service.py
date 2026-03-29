"""Testes do quota_service: contador global de uso SerpAPI."""
import datetime
from unittest.mock import patch

import pytest

from app.models import ApiUsage


class TestQuotaService:
    """Testes para get_monthly_usage, increment_usage e get_remaining_quota."""

    def test_get_monthly_usage_returns_zero_when_no_records(self, db):
        """get_monthly_usage retorna 0 quando nao ha registros no mes atual."""
        from app.services.quota_service import get_monthly_usage

        assert get_monthly_usage(db) == 0

    def test_increment_usage_creates_record_and_returns_one(self, db):
        """increment_usage cria registro e incrementa count para 1."""
        from app.services.quota_service import increment_usage

        result = increment_usage(db)
        assert result == 1

        record = db.query(ApiUsage).first()
        assert record is not None
        assert record.search_count == 1

    def test_multiple_increments_accumulate(self, db):
        """Multiplas chamadas increment_usage acumulam corretamente (3 chamadas = count 3)."""
        from app.services.quota_service import increment_usage

        increment_usage(db)
        increment_usage(db)
        result = increment_usage(db)
        assert result == 3

        record = db.query(ApiUsage).first()
        assert record.search_count == 3

    def test_previous_month_does_not_count(self, db):
        """get_monthly_usage de mes anterior nao conta no mes atual."""
        from app.services.quota_service import get_monthly_usage

        # Inserir registro do mes anterior manualmente
        now = datetime.datetime.utcnow()
        if now.month == 1:
            prev_ym = f"{now.year - 1}-12"
        else:
            prev_ym = f"{now.year}-{now.month - 1:02d}"

        old_record = ApiUsage(year_month=prev_ym, search_count=100)
        db.add(old_record)
        db.commit()

        assert get_monthly_usage(db) == 0

    def test_get_remaining_quota_returns_250_minus_usage(self, db):
        """get_remaining_quota retorna 250 - usage_count."""
        from app.services.quota_service import increment_usage, get_remaining_quota

        increment_usage(db)
        increment_usage(db)

        remaining = get_remaining_quota(db)
        assert remaining == 248  # 250 - 2
