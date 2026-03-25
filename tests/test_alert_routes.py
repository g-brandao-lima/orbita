"""Integration tests for GET /api/v1/alerts/silence/{token} endpoint."""
import datetime
from unittest.mock import patch

import pytest

from app.models import RouteGroup


def make_group(db, name="Test Group") -> RouteGroup:
    """Helper: create a RouteGroup directly in the DB and return it."""
    group = RouteGroup(
        name=name,
        origins=["GRU"],
        destinations=["LIS"],
        duration_days=10,
        travel_start=datetime.date(2026, 6, 1),
        travel_end=datetime.date(2026, 6, 30),
        is_active=True,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


VALID_TOKEN = "valid-hmac-token-abc123"
INVALID_TOKEN = "tokenfake"


class TestSilenceEndpointValidToken:
    """GET /api/v1/alerts/silence/{token}?group_id=X com token valido."""

    def test_silence_endpoint_valid_token_sets_silenced_until(self, client, db):
        """Token valido deve setar silenced_until ~24h no futuro e retornar 200."""
        group = make_group(db)

        with patch(
            "app.routes.alerts.verify_silence_token", return_value=True
        ):
            before = datetime.datetime.utcnow()
            response = client.get(
                f"/api/v1/alerts/silence/{VALID_TOKEN}?group_id={group.id}"
            )
            after = datetime.datetime.utcnow()

        assert response.status_code == 200

        db.refresh(group)
        assert group.silenced_until is not None
        expected_min = before + datetime.timedelta(hours=23, minutes=59)
        expected_max = after + datetime.timedelta(hours=24, minutes=1)
        assert expected_min <= group.silenced_until <= expected_max

    def test_silence_endpoint_response_contains_group_name(self, client, db):
        """Resposta de sucesso deve conter o nome do grupo silenciado."""
        group = make_group(db, name="Minha Rota SP-Lisboa")

        with patch(
            "app.routes.alerts.verify_silence_token", return_value=True
        ):
            response = client.get(
                f"/api/v1/alerts/silence/{VALID_TOKEN}?group_id={group.id}"
            )

        assert response.status_code == 200
        body = response.json()
        assert "Minha Rota SP-Lisboa" in body.get("message", "")

    def test_silence_endpoint_already_silenced_extends(self, client, db):
        """Grupo ja silenciado: clicar novamente reseta silenced_until para +24h."""
        group = make_group(db)
        # Pre-silence with old timestamp
        old_silence = datetime.datetime.utcnow() - datetime.timedelta(hours=5)
        group.silenced_until = old_silence
        db.commit()

        with patch(
            "app.routes.alerts.verify_silence_token", return_value=True
        ):
            before = datetime.datetime.utcnow()
            response = client.get(
                f"/api/v1/alerts/silence/{VALID_TOKEN}?group_id={group.id}"
            )
            after = datetime.datetime.utcnow()

        assert response.status_code == 200

        db.refresh(group)
        expected_min = before + datetime.timedelta(hours=23, minutes=59)
        expected_max = after + datetime.timedelta(hours=24, minutes=1)
        assert expected_min <= group.silenced_until <= expected_max
        assert group.silenced_until > old_silence


class TestSilenceEndpointInvalidToken:
    """GET /api/v1/alerts/silence/{token}?group_id=X com token invalido."""

    def test_silence_endpoint_invalid_token_returns_400(self, client, db):
        """Token invalido deve retornar 400."""
        group = make_group(db)

        with patch(
            "app.routes.alerts.verify_silence_token", return_value=False
        ):
            response = client.get(
                f"/api/v1/alerts/silence/{INVALID_TOKEN}?group_id={group.id}"
            )

        assert response.status_code == 400


class TestSilenceEndpointNonexistentGroup:
    """GET /api/v1/alerts/silence/{token}?group_id=999 com grupo inexistente."""

    def test_silence_endpoint_nonexistent_group_returns_404(self, client, db):
        """group_id inexistente deve retornar 404."""
        with patch(
            "app.routes.alerts.verify_silence_token", return_value=True
        ):
            response = client.get(
                f"/api/v1/alerts/silence/{VALID_TOKEN}?group_id=999"
            )

        assert response.status_code == 404
