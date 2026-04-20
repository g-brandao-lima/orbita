"""Inicializacao do Sentry (Phase 21.5 - observability).

Inicializa sentry-sdk com FastAPI + SQLAlchemy + Logging integrations
quando SENTRY_DSN esta configurado. Em dev (sem DSN), no-op silencioso.

LGPD:
- send_default_pii=False: nao envia IP, cookies, headers automaticamente.
- User context e enriquecido manualmente via bind_user_context() com user_id
  apenas (nao envia email/nome).
"""
import logging
import os
import sys

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.config import settings

logger = logging.getLogger(__name__)


def init_sentry() -> bool:
    """Inicializa Sentry quando DSN esta configurado. Retorna True se ativou."""
    if not settings.sentry_dsn:
        logger.info("SENTRY_DSN nao configurado; Sentry desativado")
        return False

    if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
        logger.info("Rodando sob pytest; Sentry desativado")
        return False

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR,
            ),
        ],
        before_send=_scrub_event,
    )
    logger.info(
        "Sentry ativado (env=%s, sample=%s)",
        settings.sentry_environment,
        settings.sentry_traces_sample_rate,
    )
    return True


def _scrub_event(event: dict, hint: dict) -> dict | None:
    """Remove dados sensiveis antes de enviar para o Sentry.

    Remove headers de Authorization, Cookie, e qualquer chave contendo
    'password', 'secret', 'token', 'api_key'.
    """
    request = event.get("request")
    if request is not None:
        headers = request.get("headers")
        if isinstance(headers, dict):
            for key in list(headers.keys()):
                lower = key.lower()
                if lower in ("authorization", "cookie", "x-api-key"):
                    headers[key] = "[scrubbed]"

    for key in list(event.keys()):
        if _is_sensitive_key(key):
            event[key] = "[scrubbed]"

    extra = event.get("extra")
    if isinstance(extra, dict):
        for key in list(extra.keys()):
            if _is_sensitive_key(key):
                extra[key] = "[scrubbed]"

    return event


def _is_sensitive_key(key: str) -> bool:
    lower = key.lower()
    return any(s in lower for s in ("password", "secret", "token", "api_key"))


def bind_user_context(user_id: int | None) -> None:
    """Associa user_id ao evento atual (sem enviar email/nome por LGPD)."""
    if user_id is None:
        return
    sentry_sdk.set_user({"id": str(user_id)})
