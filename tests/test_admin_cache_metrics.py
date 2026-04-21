"""Metricas de cache no admin panel (Phase 32 Plan 04)."""
import datetime

import pytest

from app.models import ApiUsage, CacheLookupLog
from app.services import admin_stats_service


def test_cache_lookup_log_insert(db):
    entry = CacheLookupLog(
        origin="GRU",
        destination="LIS",
        hit=True,
        source="travelpayouts_cached",
    )
    db.add(entry)
    db.commit()

    found = db.query(CacheLookupLog).one()
    assert found.hit is True
    assert found.source == "travelpayouts_cached"


def test_get_cache_hit_rate_7d_empty(db):
    result = admin_stats_service.get_cache_hit_rate_7d(db)
    assert result == {"total": 0, "hits": 0, "misses": 0, "hit_rate_pct": 0.0}


def test_get_cache_hit_rate_7d_computes_correctly(db):
    now = datetime.datetime.utcnow()
    for _ in range(3):
        db.add(CacheLookupLog(
            origin="GRU", destination="LIS", hit=True, source="cached",
            looked_up_at=now - datetime.timedelta(days=1),
        ))
    for _ in range(4):
        db.add(CacheLookupLog(
            origin="GRU", destination="LIS", hit=False, source="serpapi",
            looked_up_at=now - datetime.timedelta(days=1),
        ))
    for _ in range(2):
        db.add(CacheLookupLog(
            origin="GRU", destination="LIS", hit=True, source="cached",
            looked_up_at=now - datetime.timedelta(days=10),
        ))
    db.commit()

    result = admin_stats_service.get_cache_hit_rate_7d(db)

    assert result["total"] == 7
    assert result["hits"] == 3
    assert result["misses"] == 4
    assert result["hit_rate_pct"] == 42.9


def test_get_travelpayouts_quota_info_default(db):
    result = admin_stats_service.get_travelpayouts_quota_info(db)
    assert result["used"] == 0
    assert len(result["month"]) == 7


def test_get_travelpayouts_quota_info_after_increment(db):
    admin_stats_service.increment_travelpayouts_usage(db)
    admin_stats_service.increment_travelpayouts_usage(db)
    admin_stats_service.increment_travelpayouts_usage(db)

    result = admin_stats_service.get_travelpayouts_quota_info(db)
    assert result["used"] == 3
