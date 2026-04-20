"""Geracao de card PNG compartilhavel (Phase 30).

Produz imagem 1200x630 (padrao Open Graph) com preco, rota e contexto
historico. Pensado para compartilhamento em WhatsApp, Instagram Stories,
Twitter etc. Gera o PNG on-demand, nao cacheia em disco.
"""
import io
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from app.models import FlightSnapshot, RouteGroup
from app.services.dashboard_service import format_price_brl


# Paleta alinhada com o dashboard dark
BG_TOP = (11, 14, 20)       # #0b0e14
BG_BOTTOM = (17, 24, 39)    # #111827
ACCENT = (14, 165, 233)     # #0ea5e9 (azul)
GREEN = (52, 211, 153)      # #34d399
YELLOW = (251, 191, 36)     # #fbbf24
RED = (248, 113, 113)       # #f87171
TEXT = (241, 245, 249)      # #f1f5f9
MUTED = (148, 163, 184)     # #94a3b8
DIM = (100, 116, 139)       # #64748b

CARD_W, CARD_H = 1200, 630


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Tenta carregar fonte TrueType do sistema, com fallback para default.

    Windows: Arial. Linux: DejaVu. macOS: Helvetica. Se nada funciona,
    cai em ImageFont.load_default() (baixa qualidade mas nunca quebra).
    """
    candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "Helvetica-Bold.ttc" if bold else "Helvetica.ttc",
    ]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _gradient_background(img: Image.Image) -> None:
    """Pinta gradiente vertical do topo escuro para o fundo."""
    top_r, top_g, top_b = BG_TOP
    bot_r, bot_g, bot_b = BG_BOTTOM
    draw = ImageDraw.Draw(img)
    for y in range(CARD_H):
        t = y / CARD_H
        r = int(top_r + (bot_r - top_r) * t)
        g = int(top_g + (bot_g - top_g) * t)
        b = int(top_b + (bot_b - top_b) * t)
        draw.line([(0, y), (CARD_W, y)], fill=(r, g, b))


def _classification_color(classification: Optional[str]) -> tuple:
    if classification == "LOW":
        return GREEN
    if classification == "HIGH":
        return RED
    if classification == "MEDIUM":
        return YELLOW
    return TEXT


def build_price_card(
    group: RouteGroup,
    snapshot: FlightSnapshot,
    historical_ctx: Optional[dict] = None,
    passengers: int = 1,
) -> bytes:
    """Monta o PNG do card e retorna bytes para servir via HTTP.

    group: RouteGroup com nome
    snapshot: FlightSnapshot com preco, rota, datas, classification
    historical_ctx: dict opcional {avg, min, max, count, days} do snapshot_service
    passengers: para mostrar total quando > 1
    """
    img = Image.new("RGB", (CARD_W, CARD_H), BG_TOP)
    _gradient_background(img)
    draw = ImageDraw.Draw(img)

    # Fontes
    f_brand = _load_font(28, bold=True)
    f_tag = _load_font(22, bold=True)
    f_route = _load_font(56, bold=True)
    f_price = _load_font(140, bold=True)
    f_price_sub = _load_font(26)
    f_ctx = _load_font(24, bold=True)
    f_footer = _load_font(22)

    # Header: brand + tag "Preco Justo"
    draw.text((48, 40), "FLIGHT MONITOR", font=f_brand, fill=ACCENT)
    tag_text = "PRECO JUSTO"
    tag_w = draw.textlength(tag_text, font=f_tag)
    tag_pad_x, tag_pad_y = 14, 8
    tag_x = CARD_W - 48 - tag_w - tag_pad_x * 2
    tag_y = 40
    draw.rounded_rectangle(
        [(tag_x, tag_y - tag_pad_y), (tag_x + tag_w + tag_pad_x * 2, tag_y + 28 + tag_pad_y)],
        radius=12,
        fill=ACCENT,
    )
    draw.text((tag_x + tag_pad_x, tag_y), tag_text, font=f_tag, fill=BG_TOP)

    # Rota (centro-esquerda)
    route_y = 140
    route_text = f"{snapshot.origin}  \u2192  {snapshot.destination}"
    draw.text((48, route_y), route_text, font=f_route, fill=TEXT)

    # Nome do grupo (abaixo da rota)
    group_name = group.name if len(group.name) < 56 else group.name[:53] + "..."
    draw.text((48, route_y + 70), group_name, font=f_price_sub, fill=MUTED)

    # Preco grande (centro)
    color_price = _classification_color(snapshot.price_classification)
    price_text = format_price_brl(snapshot.price)
    price_y = 290
    draw.text((48, price_y), price_text, font=f_price, fill=color_price)

    # Sub do preco
    pax = max(1, passengers or 1)
    sub = "por pessoa, ida e volta"
    if pax > 1:
        total = format_price_brl(snapshot.price * pax)
        sub += f"   \u00b7   total {pax} pax: {total}"
    draw.text((52, price_y + 155), sub, font=f_price_sub, fill=MUTED)

    # Contexto historico (acima do footer)
    if historical_ctx and historical_ctx.get("avg", 0) > 0:
        avg = historical_ctx["avg"]
        days = historical_ctx.get("days", 90)
        pct = (snapshot.price - avg) / avg * 100
        if pct <= -5:
            phrase = f"{abs(pct):.0f}% ABAIXO DA MEDIA DOS ULTIMOS {days} DIAS"
            ctx_color = GREEN
        elif pct >= 5:
            phrase = f"{pct:.0f}% ACIMA DA MEDIA DOS ULTIMOS {days} DIAS"
            ctx_color = RED
        else:
            phrase = f"EM LINHA COM A MEDIA DOS ULTIMOS {days} DIAS"
            ctx_color = YELLOW
        draw.text((48, 510), phrase, font=f_ctx, fill=ctx_color)

    # Footer
    footer_text = "Monitorando preco desde sua criacao. Acesse flight-monitor.onrender.com"
    draw.text((48, 570), footer_text, font=f_footer, fill=DIM)

    # Bytes em memoria
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
