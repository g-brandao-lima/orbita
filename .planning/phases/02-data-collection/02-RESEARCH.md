# Phase 2: Data Collection - Research

**Researched:** 2026-03-25
**Domain:** Amadeus Self-Service API integration, APScheduler polling, SQLAlchemy snapshot persistence
**Confidence:** HIGH

## Summary

Phase 2 transforma o Flight Monitor de um CRUD de grupos de rota em um sistema autonomo de coleta de dados. O nucleo e um scheduler (APScheduler BackgroundScheduler) que a cada 6 horas, para cada grupo ativo, executa uma sequencia de chamadas a Amadeus API: (1) Flight Offers Search para encontrar as 5 combinacoes mais baratas, (2) Flight Availabilities Search para capturar booking classes com contagem, e (3) Itinerary Price Metrics para classificacao historica de preco. Tudo e persistido como snapshots no SQLite.

O constraint dominante e o budget de API: ~2000 calls/mes no free tier. Com 4 grupos ativos e 4 ciclos/dia, cada ciclo pode consumir no maximo ~12 calls por grupo. A sequencia de 3 endpoints por combinacao (offers + availability + price metrics) deve ser otimizada para respeitar esse budget. A recomendacao e: 1 call de Flight Offers Search (retorna ate 250 ofertas, filtrar as 5 mais baratas no codigo), + 5 calls de Availabilities (1 por combinacao) + 5 calls de Price Metrics = 11 calls por ciclo por grupo, que cabe no budget.

**Primary recommendation:** Usar amadeus-python SDK v12.0.0 com BackgroundScheduler do APScheduler 3.11.2 integrado via FastAPI lifespan. Modelar snapshots em 2 tabelas relacionais (flight_snapshot + booking_class_snapshot) para facilitar queries de comparacao da Phase 3.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

- Polling interval: exatamente 6 horas (COLL-01)
- Por ciclo: as 5 combinacoes mais baratas de (origem x destino x data_ida x data_volta) dentro do periodo do grupo (COLL-02)
- Para cada combinacao: capturar booking classes com contagem via Amadeus Flight Availabilities Search (COLL-03)
- Para cada combinacao: capturar classificacao historica LOW/MEDIUM/HIGH via Amadeus Flight Price Analysis (COLL-04)
- Persistencia: snapshots com timestamp no banco SQLite (COLL-05)
- Tratamento de falhas: gracioso, sem crashar o scheduler; proximo ciclo executa normalmente (COLL-06)
- Scheduler: APScheduler embedded (definido em PROJECT.md, sem Celery)
- Banco: SQLite via SQLAlchemy sync (herdado da Phase 1)
- Budget de API: ~2000 calls/mes no free tier Amadeus; maximo ~4 grupos ativos com 2 pollings/dia
- app/config.py deve ser atualizado: substituir telegram_bot_token e telegram_chat_id por gmail_sender, gmail_app_password, gmail_recipient

### Claude's Discretion

- Endpoints Amadeus a usar e sequencia exata
- Esquema do modelo de dados para snapshots (tabela flat com JSON, tabelas relacionais, ou hibrido)
- Estrategia de retry em caso de timeout ou 429 (skip do ciclo com log, backoff, etc.)
- Comportamento quando credenciais Amadeus ausentes no .env (iniciar sem fazer calls, ou logar aviso)
- Estrutura dos servicos: onde colocar logica de Amadeus client vs logica de scheduler vs logica de persistencia

### Deferred Ideas (OUT OF SCOPE)

Nenhum item discutido para diferir.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| COLL-01 | Sistema faz polling da Amadeus API a cada 6 horas para cada Grupo de Rota ativo | APScheduler BackgroundScheduler com IntervalTrigger(hours=6), integrado via FastAPI lifespan |
| COLL-02 | Por ciclo, encontra as 5 combinacoes mais baratas de (origem x destino x data_ida x data_volta) | Flight Offers Search GET retorna ate 250 ofertas; filtrar top 5 por preco no codigo |
| COLL-03 | Captura inventario de booking classes (Y, B, M, H, Q, K, L com contagem) via Availabilities Search | Flight Availabilities Search POST retorna availabilityClasses com class + numberOfBookableSeats |
| COLL-04 | Captura classificacao historica do preco (LOW/MEDIUM/HIGH) via Flight Price Analysis | Itinerary Price Metrics GET retorna priceMetrics com quartileRanking (MINIMUM/FIRST/MEDIUM/THIRD/MAXIMUM) |
| COLL-05 | Persiste todos os dados como snapshots com timestamp no banco SQLite | 2 tabelas: flight_snapshots + booking_class_snapshots, FK para route_groups |
| COLL-06 | Trata graciosamente falhas de API sem crashar o scheduler | try/except por grupo com logging; ResponseError do SDK captura erros HTTP |

</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Metodologia SDD + TDD obrigatoria: RED (testes falhando) antes de GREEN (implementacao minima) antes de REFACTOR
- Spec deve ser apresentada ao humano antes de codigo
- Cobertura minima: happy path, edge cases, erro esperado, integracao
- YAGNI estrito: nao adicionar nada que nao foi explicitamente pedido
- Complexidade ciclomatica maxima 5 por funcao
- Sem emojis nas respostas
- Sem uso do simbolo " -- "

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| amadeus | 12.0.0 | SDK oficial para Amadeus Self-Service API | Wrapper Python oficial, maneja OAuth2 automaticamente, retry built-in |
| apscheduler | 3.11.2 | Scheduler de polling a cada 6 horas | Unica opcao mencionada em PROJECT.md; BackgroundScheduler roda em thread separada |
| sqlalchemy | 2.0.40 | ORM para persistencia de snapshots | Ja em uso na Phase 1; manter consistencia |
| httpx | 0.28.1 | Ja presente; pode ser usado para testes com TestClient | Ja no requirements.txt da Phase 1 |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.11.1 | Validacao de schemas de resposta Amadeus | Ja presente; usar para schemas de snapshot |
| pydantic-settings | 2.9.1 | Config com .env | Ja presente; adicionar gmail_* e remover telegram_* |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| amadeus SDK | httpx raw | SDK maneja OAuth2 e retry automaticamente; httpx raw exigiria implementar token refresh manual |
| APScheduler BackgroundScheduler | AsyncIOScheduler | BackgroundScheduler e mais simples com SQLAlchemy sync; AsyncIOScheduler exigiria async DB |
| Tabelas relacionais | JSON blob | Relacionais permitem queries SQL diretas para comparacao de snapshots (Phase 3); JSON exigiria parsing em Python |

**Installation:**
```bash
pip install amadeus==12.0.0 apscheduler==3.11.2
```

## Architecture Patterns

### Recommended Project Structure
```
app/
  config.py           # Settings (atualizar: gmail_* substitui telegram_*)
  models.py           # RouteGroup + FlightSnapshot + BookingClassSnapshot
  database.py         # Engine e Session (sem mudancas)
  schemas.py          # Pydantic schemas (adicionar SnapshotResponse se necessario)
  services/
    route_group_service.py    # Existente (sem mudancas)
    amadeus_client.py         # NEW: wrapper do SDK Amadeus (auth, search, availability, metrics)
    polling_service.py        # NEW: orquestra ciclo de polling (busca grupos ativos, chama amadeus_client, persiste)
    snapshot_service.py       # NEW: CRUD de snapshots no banco
  scheduler.py        # NEW: setup do BackgroundScheduler + job registration
main.py               # Lifespan atualizado para start/stop scheduler
```

### Pattern 1: Amadeus Client Service (Wrapper)
**What:** Classe que encapsula todas as chamadas ao SDK Amadeus, expondo metodos de alto nivel.
**When to use:** Sempre que precisar chamar a API Amadeus.
**Example:**
```python
# app/services/amadeus_client.py
from amadeus import Client, ResponseError
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class AmadeusClient:
    def __init__(self):
        if not settings.amadeus_client_id or not settings.amadeus_client_secret:
            logger.warning("Amadeus credentials not configured. API calls disabled.")
            self._client = None
            return
        self._client = Client(
            client_id=settings.amadeus_client_id,
            client_secret=settings.amadeus_client_secret,
        )

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def search_cheapest_offers(
        self, origin: str, destination: str, departure_date: str,
        return_date: str, max_results: int = 5
    ) -> list[dict]:
        """Flight Offers Search GET - retorna ate 250 ofertas, filtradas por preco."""
        response = self._client.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            returnDate=return_date,
            adults=1,
            currencyCode="BRL",
            max=250,
        )
        offers = response.data
        # Ordenar por preco e retornar top N
        offers.sort(key=lambda x: float(x["price"]["grandTotal"]))
        return offers[:max_results]

    def get_availability(
        self, origin: str, destination: str, departure_date: str, return_date: str
    ) -> list[dict]:
        """Flight Availabilities Search POST - retorna booking classes com contagem."""
        body = {
            "originDestinations": [
                {
                    "id": "1",
                    "originLocationCode": origin,
                    "destinationLocationCode": destination,
                    "departureDateTime": {"date": departure_date},
                },
                {
                    "id": "2",
                    "originLocationCode": destination,
                    "destinationLocationCode": origin,
                    "departureDateTime": {"date": return_date},
                },
            ],
            "travelers": [{"id": "1", "travelerType": "ADULT"}],
            "sources": ["GDS"],
        }
        response = self._client.shopping.availability.flight_availabilities.post(body)
        return response.data

    def get_price_metrics(
        self, origin: str, destination: str, departure_date: str
    ) -> dict:
        """Itinerary Price Metrics GET - retorna quartis historicos."""
        response = self._client.analytics.itinerary_price_metrics.get(
            originIataCode=origin,
            destinationIataCode=destination,
            departureDate=departure_date,
            currencyCode="BRL",
        )
        return response.data
```

### Pattern 2: Polling Service (Orquestrador)
**What:** Funcao que executa um ciclo completo de polling para todos os grupos ativos.
**When to use:** Chamada pelo scheduler a cada 6 horas.
**Example:**
```python
# app/services/polling_service.py
from app.database import SessionLocal
from app.models import RouteGroup
from app.services.amadeus_client import AmadeusClient
from app.services.snapshot_service import save_snapshot
import logging

logger = logging.getLogger(__name__)

def run_polling_cycle():
    """Executa um ciclo de polling para todos os grupos ativos."""
    client = AmadeusClient()
    if not client.is_configured:
        logger.warning("Amadeus not configured. Skipping polling cycle.")
        return

    db = SessionLocal()
    try:
        groups = db.query(RouteGroup).filter(RouteGroup.is_active == True).all()
        for group in groups:
            try:
                _poll_group(db, client, group)
            except Exception as e:
                logger.error(f"Polling failed for group {group.id} ({group.name}): {e}")
                continue  # proximo grupo
    finally:
        db.close()

def _poll_group(db, client, group):
    """Polling de um grupo especifico."""
    # Gerar combinacoes origem x destino
    # Para cada par, buscar ofertas no periodo travel_start..travel_end
    # Filtrar top 5 por preco
    # Para cada top 5: buscar availability + price metrics
    # Persistir snapshot
    pass  # implementacao detalhada no plano
```

### Pattern 3: Scheduler Integration via Lifespan
**What:** BackgroundScheduler configurado no lifespan do FastAPI.
**When to use:** Startup e shutdown da aplicacao.
**Example:**
```python
# app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.polling_service import run_polling_cycle

scheduler = BackgroundScheduler()

def init_scheduler():
    scheduler.add_job(
        run_polling_cycle,
        trigger=IntervalTrigger(hours=6),
        id="polling_cycle",
        name="Amadeus polling cycle",
        replace_existing=True,
    )
    scheduler.start()

def shutdown_scheduler():
    scheduler.shutdown(wait=False)
```

```python
# main.py (atualizado)
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.scheduler import init_scheduler, shutdown_scheduler
    init_scheduler()
    yield
    shutdown_scheduler()
```

### Anti-Patterns to Avoid
- **Chamar API dentro de um loop sem tratamento de erro por iteracao:** Se um grupo falha, deve pular para o proximo, nao abortar o ciclo inteiro.
- **Armazenar snapshots como JSON blob monolitico:** Impede queries SQL eficientes para comparacao de snapshots na Phase 3.
- **Usar AsyncIOScheduler com SQLAlchemy sync:** Causa blocking do event loop. BackgroundScheduler roda em thread separada e funciona com SQLAlchemy sync.
- **Fazer Flight Cheapest Date Search + Flight Offers Search em sequencia:** Cheapest Date Search retorna dados de cache diario e pode nao ter precisao para combinacoes especificas. Flight Offers Search com max=250 ja retorna dados suficientes para filtrar top 5.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OAuth2 token management | Token refresh manual com httpx | amadeus SDK (Client) | SDK gerencia token automaticamente, incluindo refresh quando expira |
| Scheduling com thread management | threading.Timer ou time.sleep em loop | APScheduler BackgroundScheduler | APScheduler lida com missed executions, shutdown gracioso, job persistence |
| Retry com backoff | Loop manual com time.sleep | try/except com logging; SDK ja tem retry basico | Complexidade desnecessaria para volume baixo de calls |

**Key insight:** O amadeus SDK faz o trabalho pesado de OAuth2 (client credentials grant, token caching, refresh). Implementar isso manualmente adicionaria ~50 linhas de codigo e riscos de race condition no token refresh.

## Common Pitfalls

### Pitfall 1: Estouro de budget de API
**What goes wrong:** Cada par origem x destino gera uma chamada separada de Flight Offers Search. Com 3 origens x 3 destinos = 9 pares, sao 9 calls so para ofertas.
**Why it happens:** Nao contabilizar que cada combinacao de aeroporto e uma chamada separada.
**How to avoid:** Limitar combinacoes. Se um grupo tem 3 origens e 3 destinos, priorizar ou rodar round-robin entre pares em ciclos diferentes. Budget maximo: 11 calls/ciclo/grupo (1 offers + 5 availability + 5 metrics).
**Warning signs:** Mais de 15 calls por ciclo por grupo.

### Pitfall 2: Flight Offers Search retorna roundtrip como 1 call
**What goes wrong:** Assumir que ida e volta sao 2 calls. Na verdade, Flight Offers Search com returnDate retorna roundtrip completo em 1 chamada GET.
**Why it happens:** Confusao entre endpoints GET (roundtrip simples) e POST (multi-city).
**How to avoid:** Usar GET com departureDate + returnDate. 1 call = 1 roundtrip completo.
**Warning signs:** Usando POST quando GET resolve.

### Pitfall 3: Amadeus capeia contagem em 9
**What goes wrong:** Tratar 9 assentos como "exatamente 9". Na verdade, 9 significa "9 ou mais".
**Why it happens:** Limitacao do GDS.
**How to avoid:** Documentar no modelo que numberOfBookableSeats >= 9 significa "9+". Na Phase 3, tratar 9 como "abundante" e nao como um numero exato.
**Warning signs:** Logica de sinal que diferencia 9 de 10.

### Pitfall 4: Flight Availabilities POST precisa de X-HTTP-Method-Override
**What goes wrong:** Chamada falha com 405 Method Not Allowed.
**Why it happens:** Alguns endpoints Amadeus exigem header especial.
**How to avoid:** O amadeus SDK ja lida com isso automaticamente no metodo .post(). Nao usar httpx raw para este endpoint.
**Warning signs:** Erros 405 ao chamar availability.

### Pitfall 5: Scheduler nao para quando app morre
**What goes wrong:** Threads orfas do BackgroundScheduler continuam rodando.
**Why it happens:** Nao chamar scheduler.shutdown() no lifespan.
**How to avoid:** Sempre usar o pattern lifespan do FastAPI com shutdown no yield.
**Warning signs:** Processos Python pendurados apos Ctrl+C.

### Pitfall 6: Price Metrics indisponivel para algumas rotas
**What goes wrong:** Amadeus retorna 404 ou dados vazios para rotas domesticas pouco populares.
**Why it happens:** Dados historicos insuficientes para aquela rota/data.
**How to avoid:** Tratar 404/vazio como "sem dados de price metrics" e continuar com snapshot parcial. price_classification pode ser NULL no banco.
**Warning signs:** Assumir que toda rota tera dados de price metrics.

## Code Examples

### Amadeus Flight Offers Search (GET, roundtrip)
```python
# Source: amadeus-python SDK README + API docs
response = amadeus.shopping.flight_offers_search.get(
    originLocationCode="GRU",
    destinationLocationCode="GIG",
    departureDate="2026-05-01",
    returnDate="2026-05-08",
    adults=1,
    currencyCode="BRL",
    max=250,
)
# response.data = lista de ate 250 flight-offer objects
# Cada offer tem: price.grandTotal, itineraries[].segments[]
```

### Amadeus Flight Availabilities Search (POST)
```python
# Source: amadeus-python SDK + Amadeus API docs
body = {
    "originDestinations": [
        {
            "id": "1",
            "originLocationCode": "GRU",
            "destinationLocationCode": "GIG",
            "departureDateTime": {"date": "2026-05-01"},
        },
        {
            "id": "2",
            "originLocationCode": "GIG",
            "destinationLocationCode": "GRU",
            "departureDateTime": {"date": "2026-05-08"},
        },
    ],
    "travelers": [{"id": "1", "travelerType": "ADULT"}],
    "sources": ["GDS"],
}
response = amadeus.shopping.availability.flight_availabilities.post(body)
# response.data[].segments[].availabilityClasses = [
#   {"class": "Y", "numberOfBookableSeats": 9},
#   {"class": "B", "numberOfBookableSeats": 4},
#   {"class": "M", "numberOfBookableSeats": 3},
# ]
```

### Amadeus Itinerary Price Metrics (GET)
```python
# Source: amadeus-python SDK + Amadeus blog
response = amadeus.analytics.itinerary_price_metrics.get(
    originIataCode="GRU",
    destinationIataCode="GIG",
    departureDate="2026-05-01",
    currencyCode="BRL",
)
# response.data = [
#   {
#     "type": "itinerary-price-metric",
#     "origin": {"iataCode": "GRU"},
#     "destination": {"iataCode": "GIG"},
#     "departureDate": "2026-05-01",
#     "priceMetrics": [
#       {"amount": "150.00", "quartileRanking": "MINIMUM"},
#       {"amount": "250.00", "quartileRanking": "FIRST"},
#       {"amount": "400.00", "quartileRanking": "MEDIUM"},
#       {"amount": "600.00", "quartileRanking": "THIRD"},
#       {"amount": "900.00", "quartileRanking": "MAXIMUM"},
#     ],
#   }
# ]
```

### Recommended Data Model
```python
# Source: Research recommendation based on Phase 3 query needs
class FlightSnapshot(Base):
    __tablename__ = "flight_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    route_group_id: Mapped[int] = mapped_column(ForeignKey("route_groups.id"))
    origin: Mapped[str] = mapped_column(String(3))         # IATA
    destination: Mapped[str] = mapped_column(String(3))     # IATA
    departure_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[date] = mapped_column(Date)
    price: Mapped[float] = mapped_column(Float)             # grandTotal em BRL
    currency: Mapped[str] = mapped_column(String(3))
    airline: Mapped[str] = mapped_column(String(2))         # carrierCode principal
    # Price metrics (pode ser NULL se indisponivel)
    price_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_first_quartile: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_median: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_third_quartile: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Classificacao derivada: comparar price vs quartis
    price_classification: Mapped[str | None] = mapped_column(String(10), nullable=True)  # LOW/MEDIUM/HIGH
    collected_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    route_group = relationship("RouteGroup", backref="snapshots")
    booking_classes = relationship("BookingClassSnapshot", backref="flight_snapshot",
                                   cascade="all, delete-orphan")


class BookingClassSnapshot(Base):
    __tablename__ = "booking_class_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    flight_snapshot_id: Mapped[int] = mapped_column(ForeignKey("flight_snapshots.id"))
    class_code: Mapped[str] = mapped_column(String(1))      # Y, B, M, H, Q, K, L
    seats_available: Mapped[int] = mapped_column(Integer)    # 0-9 (9 = "9+")
    segment_direction: Mapped[str] = mapped_column(String(10))  # OUTBOUND/INBOUND
```

### Derivando classificacao LOW/MEDIUM/HIGH
```python
def classify_price(price: float, metrics: list[dict]) -> str | None:
    """Compara preco atual com quartis historicos do Amadeus."""
    if not metrics:
        return None
    quartiles = {m["quartileRanking"]: float(m["amount"]) for m in metrics}
    first = quartiles.get("FIRST")
    medium = quartiles.get("MEDIUM")
    if first is None or medium is None:
        return None
    if price <= first:
        return "LOW"
    elif price <= medium:
        return "MEDIUM"
    else:
        return "HIGH"
```

### APScheduler + FastAPI Lifespan
```python
# Source: APScheduler 3.11.2 docs + FastAPI docs
from contextlib import asynccontextmanager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler.add_job(
        run_polling_cycle,
        trigger=IntervalTrigger(hours=6),
        id="polling_cycle",
        replace_existing=True,
    )
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)
```

## API Call Budget Analysis

### Per-Cycle-Per-Group Breakdown

Para um grupo com 1 par origem-destino:

| Step | Endpoint | Calls | Returns |
|------|----------|-------|---------|
| 1. Buscar ofertas | Flight Offers Search GET | 1 | Ate 250 ofertas roundtrip |
| 2. Filtrar top 5 | (no-op, codigo local) | 0 | 5 combinacoes |
| 3. Availability por combinacao | Flight Availabilities POST | 5 | Booking classes por segmento |
| 4. Price metrics por combinacao | Itinerary Price Metrics GET | 5 | Quartis historicos |
| **Total** | | **11** | |

### Budget Mensal

| Cenario | Grupos | Ciclos/dia | Calls/ciclo | Calls/dia | Calls/mes |
|---------|--------|------------|-------------|-----------|-----------|
| Conservador | 2 | 4 | 11 | 88 | 2640 |
| Moderado | 3 | 4 | 11 | 132 | 3960 |
| Tight | 4 | 4 | 11 | 176 | 5280 |
| **Recomendado** | **3** | **4** | **11** | **132** | **~4000** |

**Nota:** O free tier Amadeus oferece ~2000 calls/mes para test environment. O cenario "conservador" com 2 grupos ja excede. Opcoes:
1. Reduzir para 2 ciclos/dia (a cada 12h) em vez de 4 (a cada 6h)
2. Reduzir top combinacoes de 5 para 3
3. Pular Price Metrics e calcular classificacao localmente com historico proprio

**Recomendacao:** Manter 6h de intervalo conforme COLL-01, mas aceitar que com 3+ grupos ativos o budget sera apertado. Implementar um contador de calls e log de warning quando atingir 80% do budget mensal.

### Otimizacao: Multi-origin no Flight Offers Search

O Flight Offers Search GET aceita apenas 1 origem e 1 destino por call. Para um grupo com 3 origens e 3 destinos = 9 pares = 9 calls so na step 1, estourando o budget.

**Solucao:** Limitar a 1 call de offers por ciclo, usando o primeiro par origem-destino do grupo. Ou implementar round-robin: ciclo 1 pesquisa par A-B, ciclo 2 pesquisa par A-C, etc.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| APScheduler 4.x alpha | APScheduler 3.11.2 (stable) | 2024+ | v4 ainda e alpha/dev; usar 3.x que e stable |
| amadeus SDK 8.x | amadeus SDK 12.0.0 | 2024 | v12 e latest stable no PyPI |
| Flight Cheapest Date Search primeiro | Flight Offers Search direto | N/A | Cheapest Date usa cache diario, menos preciso; Offers Search e real-time |

**Deprecated/outdated:**
- APScheduler `@app.on_event("startup")`: substituido por lifespan no FastAPI 0.109+
- amadeus SDK hostname padrao e "test"; para producao usar `hostname='production'`

## Open Questions

1. **Quantos calls exatamente o free tier permite?**
   - What we know: Documentacao menciona ~2000 calls/mes para test
   - What's unclear: Se ha rate limit por minuto/hora alem do mensal
   - Recommendation: Implementar logging de call count; tratar 429 com skip + log

2. **Flight Offers Search com returnDate gera datas fixas ou flexiveis?**
   - What we know: GET com departureDate + returnDate retorna roundtrip com essas datas exatas
   - What's unclear: Como cobrir todo o periodo travel_start..travel_end do grupo (muitas datas possiveis)
   - Recommendation: Gerar combinacoes de datas com step (ex: a cada 3 dias) dentro do periodo, ou usar Flight Cheapest Date Search primeiro para descobrir as datas mais baratas

3. **Amadeus test environment retorna dados reais ou mock?**
   - What we know: Test environment retorna dados simulados (nao precos reais)
   - What's unclear: Qualidade dos dados de availability no test
   - Recommendation: Desenvolver e testar com test env; migrar para production quando pronto

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.8+ | amadeus SDK | Sim | (sistema) | N/A |
| pip | Package install | Sim | (sistema) | N/A |
| amadeus | API calls | Nao (precisa instalar) | 12.0.0 | pip install |
| apscheduler | Scheduling | Nao (precisa instalar) | 3.11.2 | pip install |
| SQLite | Database | Sim (built-in Python) | N/A | N/A |

**Missing dependencies with no fallback:** Nenhum.

**Missing dependencies with fallback:**
- amadeus e apscheduler precisam ser instalados via pip (trivial).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3.5 |
| Config file | Nenhum pytest.ini; usa defaults |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| COLL-01 | Scheduler registra job com intervalo de 6h | unit | `python -m pytest tests/test_scheduler.py -x` | Wave 0 |
| COLL-02 | Polling retorna top 5 combinacoes por preco | unit | `python -m pytest tests/test_polling_service.py::test_top_5_cheapest -x` | Wave 0 |
| COLL-03 | Availability parsing extrai booking classes | unit | `python -m pytest tests/test_amadeus_client.py::test_availability_parsing -x` | Wave 0 |
| COLL-04 | Price metrics parsing extrai classificacao | unit | `python -m pytest tests/test_amadeus_client.py::test_price_classification -x` | Wave 0 |
| COLL-05 | Snapshot persiste no banco com todos os campos | unit | `python -m pytest tests/test_snapshot_service.py -x` | Wave 0 |
| COLL-06 | Falha em um grupo nao impede polling dos demais | unit | `python -m pytest tests/test_polling_service.py::test_graceful_failure -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green antes de /gsd:verify-work

### Wave 0 Gaps
- [ ] `tests/test_amadeus_client.py` - covers COLL-02, COLL-03, COLL-04 (mock do SDK)
- [ ] `tests/test_polling_service.py` - covers COLL-01, COLL-02, COLL-06
- [ ] `tests/test_snapshot_service.py` - covers COLL-05
- [ ] `tests/test_scheduler.py` - covers COLL-01 (job registration)
- [ ] amadeus e apscheduler devem ser instalados: `pip install amadeus==12.0.0 apscheduler==3.11.2`

## Sources

### Primary (HIGH confidence)
- [amadeus-python SDK GitHub](https://github.com/amadeus4dev/amadeus-python) - metodos disponiveis, autenticacao, uso
- [Amadeus Flights API Tutorial mirror](https://alonsomoya.github.io/ama4dev/resources/flights/) - JSON response structures para todos os endpoints
- [PyPI amadeus 12.0.0](https://pypi.org/project/amadeus/) - versao atual verificada
- [PyPI apscheduler 3.11.2](https://pypi.org/project/APScheduler/) - versao atual verificada

### Secondary (MEDIUM confidence)
- [Sentry: Schedule tasks with FastAPI](https://sentry.io/answers/schedule-tasks-with-fastapi/) - pattern APScheduler + lifespan
- [APScheduler 3.x User Guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) - BackgroundScheduler docs
- [Amadeus Flight Price Analysis Django example](https://github.com/amadeus4dev/amadeus-flight-price-analysis-django) - uso pratico de price metrics
- [Amadeus API Swagger spec](https://api.apis.guru/v2/specs/amadeus.com/amadeus-flight-cheapest-date-search/1.0.6/swagger.json) - Flight Cheapest Date Search schema

### Tertiary (LOW confidence)
- Budget exato do free tier (~2000 calls/mes): mencionado em documentacao mas nao verificado com conta real; pode variar

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versoes verificadas no PyPI, SDK oficial Amadeus bem documentado
- Architecture: HIGH - patterns derivados de Phase 1 existente + docs oficiais
- API response structures: HIGH - verificados via mirror docs com JSON examples completos
- Budget analysis: MEDIUM - numeros de calls/mes sao estimativas; free tier exato pode variar
- Pitfalls: HIGH - baseados em documentacao oficial (cap em 9, test env, etc.)

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (Amadeus API e estavel; APScheduler 3.x e mature)
