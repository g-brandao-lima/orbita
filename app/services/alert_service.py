"""Alert service — composicao de email, envio SMTP, token HMAC e silenciamento."""
from email.mime.multipart import MIMEMultipart

from app.models import DetectedSignal, RouteGroup


def compose_alert_email(signal: DetectedSignal, group: RouteGroup) -> MIMEMultipart:
    """Compoe email de alerta a partir de um sinal detectado."""
    raise NotImplementedError


def send_email(msg: MIMEMultipart) -> None:
    """Envia email via SMTP SSL no Gmail."""
    raise NotImplementedError


def generate_silence_token(group_id: int) -> str:
    """Gera token HMAC deterministico para silenciamento de um grupo."""
    raise NotImplementedError


def verify_silence_token(token: str, group_id: int) -> bool:
    """Verifica se o token de silenciamento e valido para o grupo."""
    raise NotImplementedError


def should_alert(group: RouteGroup) -> bool:
    """Retorna True se o grupo nao esta silenciado no momento."""
    raise NotImplementedError
