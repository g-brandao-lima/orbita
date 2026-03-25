"""Alert service — composicao de email, envio SMTP, token HMAC e silenciamento."""
import hashlib
import hmac
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings
from app.models import DetectedSignal, RouteGroup

_URGENCY_COLORS = {
    "MAXIMA": "#dc2626",
    "ALTA": "#ea580c",
    "MEDIA": "#ca8a04",
}


def compose_alert_email(signal: DetectedSignal, group: RouteGroup) -> MIMEMultipart:
    """Compoe email de alerta a partir de um sinal detectado.

    Retorna MIMEMultipart com partes text/plain e text/html.
    """
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[{signal.urgency}] {signal.signal_type} - {group.name}"
    msg["From"] = settings.gmail_sender
    msg["To"] = settings.gmail_recipient

    token = generate_silence_token(group.id)
    silence_url = (
        f"{settings.app_base_url}/api/v1/alerts/silence/{token}?group_id={group.id}"
    )

    plain = _render_plain(signal, group, silence_url)
    html = _render_html(signal, group, silence_url)

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    return msg


def send_email(msg: MIMEMultipart) -> None:
    """Envia email via Gmail SMTP SSL na porta 465."""
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
        server.login(settings.gmail_sender, settings.gmail_app_password)
        server.send_message(msg)


def generate_silence_token(group_id: int) -> str:
    """Gera token HMAC deterministico para silenciamento de um grupo.

    Usa gmail_app_password como segredo; aceitavel para uso single-user.
    Retorna primeiros 32 caracteres do hexdigest SHA-256.
    """
    secret = settings.gmail_app_password.encode()
    message = f"silence:{group_id}".encode()
    return hmac.new(secret, message, hashlib.sha256).hexdigest()[:32]


def verify_silence_token(token: str, group_id: int) -> bool:
    """Verifica se o token de silenciamento e valido para o grupo.

    Usa hmac.compare_digest para prevenir timing attacks.
    """
    expected = generate_silence_token(group_id)
    return hmac.compare_digest(token, expected)


def should_alert(group: RouteGroup) -> bool:
    """Retorna True se o grupo nao esta silenciado no momento.

    Retorna True quando silenced_until e None ou ja expirou.
    """
    if group.silenced_until is None:
        return True
    return datetime.utcnow() > group.silenced_until


# ---------------------------------------------------------------------------
# Private rendering helpers
# ---------------------------------------------------------------------------


def _render_plain(signal: DetectedSignal, group: RouteGroup, silence_url: str) -> str:
    return (
        f"Sinal detectado: {signal.signal_type}\n"
        f"Urgencia: {signal.urgency}\n"
        f"Grupo: {group.name}\n"
        f"Rota: {signal.origin} -> {signal.destination}\n"
        f"Datas: {signal.departure_date} a {signal.return_date}\n"
        f"Preco: R$ {signal.price_at_detection:,.2f}\n"
        f"Detalhes: {signal.details}\n\n"
        f"Silenciar alertas deste grupo por 24h:\n{silence_url}\n"
    )


def _render_html(signal: DetectedSignal, group: RouteGroup, silence_url: str) -> str:
    color = _URGENCY_COLORS.get(signal.urgency, "#6b7280")
    return (
        "<html><body style=\"font-family:Arial,sans-serif;max-width:600px;margin:0 auto;\">"
        f"<div style=\"background:{color};color:white;padding:12px 20px;border-radius:8px 8px 0 0;\">"
        f"<h2 style=\"margin:0;\">{signal.signal_type.replace('_', ' ')}</h2>"
        f"<p style=\"margin:4px 0 0;\">Urgencia: {signal.urgency}</p>"
        "</div>"
        "<div style=\"border:1px solid #e5e7eb;padding:20px;border-radius:0 0 8px 8px;\">"
        f"<p><strong>Grupo:</strong> {group.name}</p>"
        f"<p><strong>Rota:</strong> {signal.origin} &rarr; {signal.destination}</p>"
        f"<p><strong>Datas:</strong> {signal.departure_date} a {signal.return_date}</p>"
        f"<p><strong>Preco atual:</strong> R$ {signal.price_at_detection:,.2f}</p>"
        f"<p><strong>Detalhes:</strong> {signal.details}</p>"
        "<hr style=\"border:none;border-top:1px solid #e5e7eb;\">"
        "<p style=\"text-align:center;\">"
        f"<a href=\"{silence_url}\" style=\"color:#6b7280;font-size:13px;\">"
        "Silenciar alertas deste grupo por 24h"
        "</a></p>"
        "</div></body></html>"
    )
