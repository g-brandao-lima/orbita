"""Templates de rotas populares para estado vazio do dashboard (Phase 28).

Quando o usuario acabou de se cadastrar e nao tem nenhum grupo, sugerimos
6 rotas de alta demanda no Brasil como ponto de partida. Reduz friccao de
onboarding e aumenta taxa de ativacao (primeiro grupo criado).
"""
import datetime
from dataclasses import dataclass


@dataclass(frozen=True)
class PopularRoute:
    slug: str
    name: str
    origin: str
    destination: str
    description: str
    duration_days: int


POPULAR_ROUTES: list[PopularRoute] = [
    PopularRoute(
        slug="gru-lis",
        name="Sao Paulo para Lisboa",
        origin="GRU",
        destination="LIS",
        description="Destino mais procurado por brasileiros na Europa",
        duration_days=10,
    ),
    PopularRoute(
        slug="gru-mia",
        name="Sao Paulo para Miami",
        origin="GRU",
        destination="MIA",
        description="Portao de entrada dos EUA",
        duration_days=10,
    ),
    PopularRoute(
        slug="gru-eze",
        name="Sao Paulo para Buenos Aires",
        origin="GRU",
        destination="EZE",
        description="Final de semana na capital argentina",
        duration_days=4,
    ),
    PopularRoute(
        slug="gig-cdg",
        name="Rio para Paris",
        origin="GIG",
        destination="CDG",
        description="Ponte aerea Brasil-Franca",
        duration_days=10,
    ),
    PopularRoute(
        slug="rec-lis",
        name="Recife para Lisboa",
        origin="REC",
        destination="LIS",
        description="Voo direto para Europa pelo Nordeste",
        duration_days=10,
    ),
    PopularRoute(
        slug="gru-scl",
        name="Sao Paulo para Santiago",
        origin="GRU",
        destination="SCL",
        description="Neve e montanhas no Chile",
        duration_days=7,
    ),
]


def get_by_slug(slug: str) -> PopularRoute | None:
    for r in POPULAR_ROUTES:
        if r.slug == slug:
            return r
    return None


def default_dates(duration_days: int) -> tuple[datetime.date, datetime.date]:
    """Retorna (travel_start, travel_end) sugeridos: partida daqui a 60 dias,
    janela de 60 dias para o usuario ajustar."""
    today = datetime.date.today()
    start = today + datetime.timedelta(days=60)
    end = start + datetime.timedelta(days=60)
    return start, end
