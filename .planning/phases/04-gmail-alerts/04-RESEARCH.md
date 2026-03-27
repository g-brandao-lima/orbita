# Phase 4: Gmail Alerts - Research

**Researched:** 2026-03-25
**Domain:** Email alerting via Gmail SMTP + silence/mute mechanism via FastAPI endpoint
**Confidence:** HIGH

## Summary

Phase 4 adds email alerting when the signal detection system (Phase 3) finds actionable signals. The implementation uses Python's stdlib `smtplib` + `email.mime` to send HTML emails via Gmail SMTP with App Password authentication. Gmail config fields already exist in `app/config.py` (`gmail_sender`, `gmail_app_password`, `gmail_recipient`).

The silence link mechanism requires: (1) a new DB column `silenced_until` on `RouteGroup`, (2) a token-based endpoint `GET /api/v1/alerts/silence/{token}` that sets `silenced_until = now + 24h`, and (3) a check in the alert flow to skip sending when the group is silenced. The token can be a simple HMAC-signed value (group_id signed with a secret) since this is single-user with no security attack surface.

**Primary recommendation:** Create `app/services/alert_service.py` with two functions: `send_alert_email(signal, group)` for composing and sending the HTML email, and `should_alert(group)` for checking silence state. Integrate into `polling_service._process_offer` right after `detect_signals` returns new signals. Add `GET /api/v1/alerts/silence/{token}` endpoint. Use `secrets.token_urlsafe` for silence tokens stored in a simple dict or DB field.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ALRT-01 | Sistema envia email via Gmail quando sinal detectado contendo: nome do grupo, rota especifica (origem-destino + datas), preco atual, contexto historico e urgencia | smtplib + email.mime.multipart for HTML email; DetectedSignal has all fields: signal_type, urgency, details, price_at_detection; RouteGroup has name; FlightSnapshot has origin, destination, departure_date, return_date |
| ALRT-02 | Email contem link de silenciar que pausa alertas daquele grupo por 24 horas ao ser clicado | New `silenced_until` column on RouteGroup + HMAC-signed token endpoint; token = hmac(group_id, app_secret); clicking GET endpoint sets silenced_until = now + 24h |
| ALRT-03 | Dashboard web exibe status de todos os grupos ativos e melhor preco atual | NOTE: Dashboard UI deferred to Phase 5 per phase description; Phase 4 scope is email (ALRT-01) + silence link (ALRT-02) only. ALRT-03 data layer (silenced_until field, best_price query) will be available for Phase 5 to consume |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- TDD obrigatorio: testes escritos ANTES do codigo de producao (RED-GREEN-REFACTOR)
- Spec aprovada pelo humano antes de iniciar
- Cobertura minima: happy path, edge cases, erro esperado, integracao
- YAGNI estrito: nao adicionar features nao testadas
- Principios FIRST para testes
- Sem console.log / print de debug esquecido
- Complexidade ciclomatica maxima 5 por funcao

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| smtplib | stdlib (Python 3.13) | SMTP client for sending email | Built into Python, zero dependencies, sufficient for Gmail SMTP |
| email.mime.multipart | stdlib | Compose MIME multipart emails (HTML + plain text) | Standard way to build email messages in Python |
| email.mime.text | stdlib | Create text/html and text/plain parts | Part of email.mime, used with multipart |
| hmac + hashlib | stdlib | Generate signed silence tokens | Prevents token guessing without adding external deps |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI | 0.115.12 (installed) | Expose silence endpoint GET /api/v1/alerts/silence/{token} | Already in project |
| SQLAlchemy | 2.0.40 (installed) | Add silenced_until column to RouteGroup | Already in project |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| smtplib | aiosmtplib | Async, but overkill for single-user; polling runs in sync thread anyway |
| HMAC token | UUID stored in DB | Simpler but requires extra DB table; HMAC is stateless and sufficient |
| HTML email | Plain text | HTML allows urgency styling and clickable silence link; minimal extra effort |

## Architecture Patterns

### Recommended Project Structure
```
app/
  services/
    alert_service.py      # NEW: send_alert_email(), should_alert(), generate_silence_token()
  routes/
    alerts.py             # NEW: GET /api/v1/alerts/silence/{token}
  models.py               # MODIFY: add silenced_until to RouteGroup
  config.py               # EXISTING: gmail_sender, gmail_app_password, gmail_recipient (already present)
tests/
  test_alert_service.py   # NEW: tests for email composition, silence logic, token generation
  test_alert_routes.py    # NEW: tests for silence endpoint
```

### Pattern 1: Alert Service (Pure Logic + SMTP Side Effect)
**What:** Separate email composition (pure, testable) from SMTP sending (side effect, mockable)
**When to use:** Always for email features
**Example:**
```python
# app/services/alert_service.py
import smtplib
import hmac
import hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from app.config import settings
from app.models import DetectedSignal, RouteGroup


def compose_alert_email(signal: DetectedSignal, group: RouteGroup, base_url: str) -> MIMEMultipart:
    """Compoe email HTML com dados do sinal. Funcao pura, testavel sem SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[{signal.urgency}] {signal.signal_type} - {group.name}"
    msg["From"] = settings.gmail_sender
    msg["To"] = settings.gmail_recipient

    silence_token = generate_silence_token(group.id)
    silence_url = f"{base_url}/api/v1/alerts/silence/{silence_token}"

    html = _render_alert_html(signal, group, silence_url)
    plain = _render_alert_plain(signal, group, silence_url)

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def send_email(msg: MIMEMultipart) -> None:
    """Envia email via Gmail SMTP. Side effect isolado."""
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.gmail_sender, settings.gmail_app_password)
        server.send_message(msg)


def generate_silence_token(group_id: int) -> str:
    """Gera token HMAC para silence link. Stateless, deterministic."""
    secret = settings.gmail_app_password.encode()
    message = f"silence:{group_id}".encode()
    return hmac.new(secret, message, hashlib.sha256).hexdigest()[:32]


def verify_silence_token(token: str, group_id: int) -> bool:
    """Verifica se token e valido para o group_id."""
    expected = generate_silence_token(group_id)
    return hmac.compare_digest(token, expected)


def should_alert(group: RouteGroup) -> bool:
    """Verifica se grupo pode receber alertas (nao silenciado)."""
    if group.silenced_until is None:
        return True
    return datetime.utcnow() > group.silenced_until
```

### Pattern 2: Integration Point in Polling Cycle
**What:** After `detect_signals` returns new signals, iterate and send alerts for non-silenced groups
**When to use:** In `polling_service._process_offer` after signal detection
**Example:**
```python
# In polling_service.py, after detect_signals call:
detected = detect_signals(db, snapshot)
for signal in detected:
    logger.info(f"Signal detected: {signal.signal_type} ...")
    try:
        if should_alert(group):
            msg = compose_alert_email(signal, group, base_url="http://localhost:8000")
            send_email(msg)
            logger.info(f"Alert sent for {signal.signal_type}")
    except Exception as e:
        logger.error(f"Alert email failed: {e}")
```

### Pattern 3: Silence Endpoint
**What:** GET endpoint that receives token, extracts group_id, validates, sets silenced_until
**When to use:** Single endpoint in alerts router
**Example:**
```python
# app/routes/alerts.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models import RouteGroup
from app.services.alert_service import verify_silence_token

router = APIRouter()

@router.get("/alerts/silence/{token}")
def silence_group(token: str, group_id: int, db: Session = Depends(get_db)):
    """Silencia alertas de um grupo por 24h. Link clicavel no email."""
    if not verify_silence_token(token, group_id):
        raise HTTPException(status_code=400, detail="Token invalido")

    group = db.query(RouteGroup).get(group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Grupo nao encontrado")

    group.silenced_until = datetime.utcnow() + timedelta(hours=24)
    db.commit()
    return {"message": f"Alertas do grupo '{group.name}' silenciados por 24 horas"}
```

### Anti-Patterns to Avoid
- **Sending email inside detect_signals:** Signal detection is pure logic; mixing in I/O (SMTP) violates SRP and makes testing hard. Alert sending belongs in the polling orchestration layer.
- **Storing silence tokens in DB:** For single-user, HMAC-signed tokens are stateless and sufficient. A tokens table adds complexity without value.
- **Using TLS STARTTLS on port 587 instead of SSL on 465:** Gmail supports both, but `SMTP_SSL` on port 465 is simpler (no two-step handshake). Both work with App Password.
- **Blocking the polling thread on SMTP failures:** Always wrap send_email in try/except to prevent email failures from interrupting the polling cycle.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Email composition | String concatenation of headers | `email.mime.multipart.MIMEMultipart` + `email.mime.text.MIMEText` | Handles encoding, MIME boundaries, headers correctly |
| SMTP auth | Raw socket connection | `smtplib.SMTP_SSL` | Handles TLS negotiation, auth protocol, connection pooling |
| Token signing | Custom hash scheme | `hmac.new()` with `hmac.compare_digest()` | Timing-safe comparison prevents side-channel attacks |
| HTML email template | f-string HTML | Dedicated `_render_alert_html()` function | Isolates template from logic, easier to test and modify |

## Common Pitfalls

### Pitfall 1: Gmail App Password vs Regular Password
**What goes wrong:** Using regular Gmail password instead of App Password results in authentication failure (535 error)
**Why it happens:** Google disabled "less secure app access" permanently. Only App Passwords work for SMTP.
**How to avoid:** Config already has `gmail_app_password` field. Document in .env.example that this must be a 16-character App Password generated at myaccount.google.com/apppasswords. Requires 2FA enabled on the Google account.
**Warning signs:** `smtplib.SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')`

### Pitfall 2: Email Encoding for Portuguese Characters
**What goes wrong:** Accented characters (a, e, o, c) in group names or details appear garbled
**Why it happens:** Default encoding may not handle UTF-8 properly in email headers
**How to avoid:** Use `MIMEText(html, "html", "utf-8")` explicitly. For Subject header with special chars, `email.header.Header` handles encoding automatically when using `MIMEMultipart`.
**Warning signs:** Mojibake in received emails (a showing as A£)

### Pitfall 3: SMTP Connection Timeout in Polling Cycle
**What goes wrong:** Gmail SMTP is unreachable (network issue), causing the entire polling cycle to hang
**Why it happens:** Default smtplib timeout is None (infinite wait)
**How to avoid:** Set explicit timeout: `smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30)`. Wrap in try/except so polling continues even if email fails.
**Warning signs:** Polling cycle takes abnormally long, no snapshots collected

### Pitfall 4: Token in Silence URL Must Include group_id
**What goes wrong:** Silence link only has the token but the endpoint needs to know which group to silence
**Why it happens:** HMAC token encodes group_id but doesn't expose it in the URL
**How to avoid:** URL format: `/api/v1/alerts/silence/{token}?group_id={id}`. Token validates that group_id hasn't been tampered with.
**Warning signs:** 400 errors when clicking silence link

### Pitfall 5: Gmail SMTP Rate Limits
**What goes wrong:** Sending too many emails in a burst triggers Gmail's rate limiting
**Why it happens:** Multiple signals detected in one polling cycle = multiple emails
**How to avoid:** For single-user personal tool with 4 groups max, this is unlikely. But add a small `time.sleep(1)` between emails if sending > 3 in one cycle as a safety measure.
**Warning signs:** `smtplib.SMTPDataError` with code 421

### Pitfall 6: silenced_until Column Migration
**What goes wrong:** Adding new column to existing RouteGroup table requires DB migration or recreation
**Why it happens:** SQLAlchemy `create_all` only creates missing tables, not missing columns
**How to avoid:** Since this is a personal tool with SQLite: either (a) delete the DB file and let it recreate (simplest), or (b) use a raw ALTER TABLE statement in a one-time migration. Document which approach to use.
**Warning signs:** `OperationalError: no such column: route_groups.silenced_until`

## Code Examples

### Gmail SMTP with App Password (verified pattern)
```python
# Source: Python 3.13 stdlib documentation
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

msg = MIMEMultipart("alternative")
msg["Subject"] = "[MAXIMA] BALDE_REABERTO - Europa Junho"
msg["From"] = "sender@gmail.com"
msg["To"] = "recipient@gmail.com"

plain = "Sinal detectado: BALDE REABERTO..."
html = "<html><body><h2>BALDE REABERTO</h2>...</body></html>"

msg.attach(MIMEText(plain, "plain", "utf-8"))
msg.attach(MIMEText(html, "html", "utf-8"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
    server.login("sender@gmail.com", "xxxx-xxxx-xxxx-xxxx")  # App Password
    server.send_message(msg)
```

### HMAC Token Generation (verified pattern)
```python
# Source: Python 3.13 stdlib hmac documentation
import hmac
import hashlib

def generate_silence_token(group_id: int, secret: str) -> str:
    message = f"silence:{group_id}".encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()[:32]

def verify_silence_token(token: str, group_id: int, secret: str) -> bool:
    expected = generate_silence_token(group_id, secret)
    return hmac.compare_digest(token, expected)
```

### HTML Email Template Structure
```python
def _render_alert_html(signal, group, silence_url: str) -> str:
    urgency_colors = {
        "MAXIMA": "#dc2626",
        "ALTA": "#ea580c",
        "MEDIA": "#ca8a04",
    }
    color = urgency_colors.get(signal.urgency, "#6b7280")

    return f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: {color}; color: white; padding: 12px 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">{signal.signal_type.replace('_', ' ')}</h2>
            <p style="margin: 4px 0 0;">Urgencia: {signal.urgency}</p>
        </div>
        <div style="border: 1px solid #e5e7eb; padding: 20px; border-radius: 0 0 8px 8px;">
            <p><strong>Grupo:</strong> {group.name}</p>
            <p><strong>Rota:</strong> {signal.origin} &rarr; {signal.destination}</p>
            <p><strong>Datas:</strong> {signal.departure_date} a {signal.return_date}</p>
            <p><strong>Preco atual:</strong> R$ {signal.price_at_detection:,.2f}</p>
            <p><strong>Detalhes:</strong> {signal.details}</p>
            <hr style="border: none; border-top: 1px solid #e5e7eb;">
            <p style="text-align: center;">
                <a href="{silence_url}" style="color: #6b7280; font-size: 13px;">
                    Silenciar alertas deste grupo por 24h
                </a>
            </p>
        </div>
    </body>
    </html>
    """
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SMTP_STARTTLS on 587 | SMTP_SSL on 465 preferred | Gmail recommendation | Simpler code, one less step (no starttls() call) |
| Regular password auth | App Password required | Google 2022 | Must generate 16-char app password from Google account settings |
| Plain text email | HTML multipart (plain + html) | Standard practice | Better readability, clickable links, urgency styling |

## Open Questions

1. **Base URL for silence links**
   - What we know: Silence URL needs the full base URL (e.g., `http://localhost:8000` or the Fly.io URL)
   - What's unclear: Should this be a config setting or auto-detected from the request?
   - Recommendation: Add `app_base_url` to Settings with default `http://localhost:8000`. Simple, explicit, works for local and Fly.io.

2. **DB migration for silenced_until column**
   - What we know: SQLAlchemy create_all won't add columns to existing tables
   - What's unclear: Does the user have existing data worth preserving?
   - Recommendation: Since this is a personal dev tool in early development, deleting the DB file is acceptable. Add a comment in the migration or a startup check. Alternatively, run `ALTER TABLE route_groups ADD COLUMN silenced_until DATETIME` once.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | none (uses defaults) |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ALRT-01 | compose_alert_email produces correct MIME with all signal fields | unit | `python -m pytest tests/test_alert_service.py::test_compose_email_happy_path -x` | Wave 0 |
| ALRT-01 | send_email calls SMTP_SSL with correct credentials | unit (mock) | `python -m pytest tests/test_alert_service.py::test_send_email_smtp -x` | Wave 0 |
| ALRT-01 | Email subject contains urgency and signal type | unit | `python -m pytest tests/test_alert_service.py::test_email_subject_format -x` | Wave 0 |
| ALRT-01 | Email body contains group name, route, price, details | unit | `python -m pytest tests/test_alert_service.py::test_email_body_content -x` | Wave 0 |
| ALRT-01 | Alert integrates with polling cycle (called after detect_signals) | unit (mock) | `python -m pytest tests/test_alert_service.py::test_polling_triggers_alert -x` | Wave 0 |
| ALRT-01 | SMTP failure does not crash polling cycle | unit (mock) | `python -m pytest tests/test_alert_service.py::test_smtp_failure_isolated -x` | Wave 0 |
| ALRT-02 | generate_silence_token produces deterministic HMAC | unit | `python -m pytest tests/test_alert_service.py::test_silence_token_generation -x` | Wave 0 |
| ALRT-02 | verify_silence_token accepts valid token, rejects invalid | unit | `python -m pytest tests/test_alert_service.py::test_silence_token_verification -x` | Wave 0 |
| ALRT-02 | GET /alerts/silence/{token} sets silenced_until on group | integration | `python -m pytest tests/test_alert_routes.py::test_silence_endpoint_success -x` | Wave 0 |
| ALRT-02 | GET /alerts/silence/{token} with invalid token returns 400 | integration | `python -m pytest tests/test_alert_routes.py::test_silence_endpoint_invalid_token -x` | Wave 0 |
| ALRT-02 | should_alert returns False when group is silenced | unit | `python -m pytest tests/test_alert_service.py::test_should_alert_silenced -x` | Wave 0 |
| ALRT-02 | should_alert returns True when silence expired | unit | `python -m pytest tests/test_alert_service.py::test_should_alert_expired -x` | Wave 0 |
| ALRT-02 | Email contains clickable silence link | unit | `python -m pytest tests/test_alert_service.py::test_email_contains_silence_link -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before /gsd:verify-work

### Wave 0 Gaps
- [ ] `tests/test_alert_service.py` -- covers ALRT-01 and ALRT-02 service logic
- [ ] `tests/test_alert_routes.py` -- covers ALRT-02 silence endpoint

## Sources

### Primary (HIGH confidence)
- Python 3.13 stdlib: smtplib, email.mime.multipart, email.mime.text, hmac, hashlib -- all built-in, verified available on this system
- Existing codebase: `app/config.py` already has gmail_sender, gmail_app_password, gmail_recipient fields
- Existing codebase: `app/services/signal_service.py` detect_signals returns list[DetectedSignal] with all needed fields
- Existing codebase: `app/services/polling_service.py` line 128-135 shows integration point after detect_signals

### Secondary (MEDIUM confidence)
- Gmail SMTP configuration: smtp.gmail.com, port 465 (SSL) or 587 (TLS) -- well-documented, stable for years

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all stdlib, zero new dependencies, verified on this Python 3.13 install
- Architecture: HIGH -- clear integration point exists in polling_service.py, follows existing service pattern
- Pitfalls: HIGH -- Gmail SMTP is well-documented territory; pitfalls are well-known and preventable

**Research date:** 2026-03-25
**Valid until:** 2026-06-25 (stable domain, stdlib-only)
