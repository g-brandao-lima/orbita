"""Testes unitarios para app/services/alert_service.py — TDD RED phase."""
import datetime
import unittest.mock

import pytest

from app.models import DetectedSignal, RouteGroup
from app.services.alert_service import (
    compose_alert_email,
    generate_silence_token,
    send_email,
    should_alert,
    verify_silence_token,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures locais
# ---------------------------------------------------------------------------


def _make_group(
    group_id: int = 1,
    name: str = "GRU-JFK Janeiro",
    silenced_until: datetime.datetime | None = None,
) -> unittest.mock.MagicMock:
    group = unittest.mock.MagicMock(spec=RouteGroup)
    group.id = group_id
    group.name = name
    group.silenced_until = silenced_until
    return group


def _make_signal(
    signal_type: str = "BALDE_FECHANDO",
    urgency: str = "ALTA",
    details: str = "Classe K: 3 -> 1 assentos",
    origin: str = "GRU",
    destination: str = "JFK",
    departure_date: datetime.date = datetime.date(2026, 1, 15),
    return_date: datetime.date = datetime.date(2026, 1, 22),
    price_at_detection: float = 3500.00,
    route_group_id: int = 1,
) -> unittest.mock.MagicMock:
    signal = unittest.mock.MagicMock(spec=DetectedSignal)
    signal.signal_type = signal_type
    signal.urgency = urgency
    signal.details = details
    signal.origin = origin
    signal.destination = destination
    signal.departure_date = departure_date
    signal.return_date = return_date
    signal.price_at_detection = price_at_detection
    signal.route_group_id = route_group_id
    return signal


# ---------------------------------------------------------------------------
# Tests — compose_alert_email
# ---------------------------------------------------------------------------


def test_compose_email_subject_contains_urgency_and_signal_type():
    # Arrange
    group = _make_group()
    signal = _make_signal(signal_type="BALDE_FECHANDO", urgency="ALTA")

    # Act
    msg = compose_alert_email(signal, group)

    # Assert
    subject = msg["Subject"]
    assert "[ALTA]" in subject
    assert "BALDE_FECHANDO" in subject


def test_compose_email_body_contains_group_name():
    # Arrange
    group = _make_group(name="GRU-JFK Janeiro")
    signal = _make_signal()

    # Act
    msg = compose_alert_email(signal, group)

    # Assert
    body = msg.as_string()
    assert "GRU-JFK Janeiro" in body


def test_compose_email_body_contains_route_info():
    # Arrange
    group = _make_group()
    signal = _make_signal(
        origin="GRU",
        destination="JFK",
        departure_date=datetime.date(2026, 1, 15),
        return_date=datetime.date(2026, 1, 22),
        price_at_detection=3500.00,
    )

    # Act
    msg = compose_alert_email(signal, group)

    # Assert
    body = msg.as_string()
    assert "GRU" in body
    assert "JFK" in body
    assert "2026-01-15" in body
    assert "2026-01-22" in body
    assert "3500" in body


def test_compose_email_body_contains_silence_link():
    # Arrange
    group = _make_group(group_id=5)
    signal = _make_signal()

    # Act
    msg = compose_alert_email(signal, group)

    # Assert
    body = msg.as_string()
    assert "/api/v1/alerts/silence/" in body


def test_compose_email_plain_text_fallback():
    # Arrange
    group = _make_group()
    signal = _make_signal(signal_type="BALDE_REABERTO", urgency="MAXIMA")

    # Act
    msg = compose_alert_email(signal, group)

    # Assert — deve ter parte text/plain com info do sinal
    plain_part = None
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            plain_part = part.get_payload(decode=True).decode("utf-8")
            break

    assert plain_part is not None
    assert "BALDE_REABERTO" in plain_part or "GRU" in plain_part


# ---------------------------------------------------------------------------
# Tests — send_email
# ---------------------------------------------------------------------------


def test_send_email_calls_smtp_ssl():
    # Arrange
    group = _make_group()
    signal = _make_signal()
    msg = None

    with unittest.mock.patch("smtplib.SMTP_SSL") as mock_ssl:
        mock_server = unittest.mock.MagicMock()
        mock_ssl.return_value.__enter__ = unittest.mock.MagicMock(
            return_value=mock_server
        )
        mock_ssl.return_value.__exit__ = unittest.mock.MagicMock(return_value=False)

        # Act
        send_email(unittest.mock.MagicMock())

        # Assert
        mock_ssl.assert_called_once()
        call_args = mock_ssl.call_args
        assert call_args[0][0] == "smtp.gmail.com"
        assert call_args[0][1] == 465


def test_send_email_uses_timeout():
    # Arrange
    with unittest.mock.patch("smtplib.SMTP_SSL") as mock_ssl:
        mock_server = unittest.mock.MagicMock()
        mock_ssl.return_value.__enter__ = unittest.mock.MagicMock(
            return_value=mock_server
        )
        mock_ssl.return_value.__exit__ = unittest.mock.MagicMock(return_value=False)

        # Act
        send_email(unittest.mock.MagicMock())

        # Assert
        call_kwargs = mock_ssl.call_args[1]
        assert call_kwargs.get("timeout") == 30


# ---------------------------------------------------------------------------
# Tests — generate_silence_token
# ---------------------------------------------------------------------------


def test_generate_silence_token_deterministic():
    # Arrange / Act
    token1 = generate_silence_token(1)
    token2 = generate_silence_token(1)

    # Assert
    assert token1 == token2
    assert isinstance(token1, str)
    assert len(token1) > 0


def test_generate_silence_token_different_groups():
    # Arrange / Act
    token1 = generate_silence_token(1)
    token2 = generate_silence_token(2)

    # Assert
    assert token1 != token2


# ---------------------------------------------------------------------------
# Tests — verify_silence_token
# ---------------------------------------------------------------------------


def test_verify_silence_token_valid():
    # Arrange
    group_id = 42
    token = generate_silence_token(group_id)

    # Act
    result = verify_silence_token(token, group_id)

    # Assert
    assert result is True


def test_verify_silence_token_invalid():
    # Arrange
    group_id = 42

    # Act
    result = verify_silence_token("token_falso_invalido_xpto", group_id)

    # Assert
    assert result is False


# ---------------------------------------------------------------------------
# Tests — should_alert
# ---------------------------------------------------------------------------


def test_should_alert_no_silence():
    # Arrange — grupo sem silenciamento
    group = _make_group(silenced_until=None)

    # Act
    result = should_alert(group)

    # Assert
    assert result is True


def test_should_alert_silenced():
    # Arrange — grupo silenciado ate o futuro
    future = datetime.datetime.utcnow() + datetime.timedelta(hours=12)
    group = _make_group(silenced_until=future)

    # Act
    result = should_alert(group)

    # Assert
    assert result is False


def test_should_alert_expired():
    # Arrange — silenciamento expirado (data no passado)
    past = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    group = _make_group(silenced_until=past)

    # Act
    result = should_alert(group)

    # Assert
    assert result is True
