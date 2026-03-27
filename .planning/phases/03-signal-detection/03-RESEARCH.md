# Phase 3: Signal Detection - Research

**Researched:** 2026-03-25
**Domain:** SQLAlchemy temporal queries, signal detection algorithms, deduplication patterns
**Confidence:** HIGH

## Summary

Phase 3 transforma os snapshots brutos coletados pela Phase 2 em sinais acionaveis de compra. O sistema precisa comparar snapshots sequenciais da mesma rota para detectar 4 tipos de sinais (BALDE FECHANDO, BALDE REABERTO, PRECO ABAIXO DO HISTORICO, JANELA OTIMA), cada um com urgencia diferente. Alem disso, precisa de deduplicacao para nao re-alertar o mesmo sinal dentro de 12 horas.

A complexidade central esta em: (1) identificar corretamente o "snapshot anterior" para uma rota especifica (origin+destination+departure_date+return_date), (2) modelar sinais detectados no banco de forma que queries de deduplicacao sejam eficientes, e (3) integrar a deteccao no ciclo de polling existente sem aumentar a complexidade do polling_service. A recomendacao e criar um novo servico `signal_service.py` com funcoes puras que recebem snapshots e retornam sinais, chamado pelo polling_service logo apos salvar cada snapshot. Os sinais sao persistidos em uma nova tabela `detected_signals` com indice composto para deduplicacao.

Nao ha necessidade de novas dependencias externas. Toda a logica e Python puro + SQLAlchemy queries sobre dados ja existentes no banco. O modelo de dados da Phase 2 (flight_snapshots + booking_class_snapshots) ja contem tudo o que e necessario como input.

**Primary recommendation:** Criar tabela `detected_signals` com indice composto (route_group_id, origin, destination, departure_date, return_date, signal_type) + filtro temporal para deduplicacao. Implementar signal_service.py com funcoes puras por tipo de sinal, chamadas pelo polling_service apos cada save_flight_snapshot.

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SIGN-01 | Sistema detecta BALDE FECHANDO quando classe K ou Q passou de >=3 para <=1 comparado ao snapshot anterior - urgencia ALTA | Query SQLAlchemy para buscar snapshot anterior pela mesma rota; comparar booking_classes K/Q entre snapshots |
| SIGN-02 | Sistema detecta BALDE REABERTO quando classe estava em 0 e voltou a ter assentos - urgencia MAXIMA | Mesma query de snapshot anterior; verificar qualquer classe que passou de 0 para >0 |
| SIGN-03 | Sistema detecta PRECO ABAIXO DO HISTORICO quando Amadeus retorna LOW e preco abaixo da media dos ultimos 14 snapshots - urgencia MEDIA | Query de media de preco dos ultimos 14 snapshots + check do campo price_classification == "LOW" |
| SIGN-04 | Sistema detecta JANELA OTIMA quando dias antes do voo entra na faixa ideal por tipo de rota - urgencia MEDIA | Calculo date arithmetic: departure_date - today; heuristica de domestico vs internacional por IATA code |
| SIGN-05 | Sistema nao re-alerta mesmo sinal para mesma rota dentro de 12 horas | Tabela detected_signals com indice composto + query de deduplicacao temporal |

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
| sqlalchemy | 2.0.40 | Queries temporais e persistencia de sinais | Ja em uso; ORM queries para comparacao de snapshots |
| pytest | 8.3.5 | Testes unitarios para cada detector de sinal | Ja em uso; mesmo framework das phases anteriores |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime (stdlib) | N/A | Calculo de dias ate o voo e janelas temporais | SIGN-04 e deduplicacao SIGN-05 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Query por snapshot anterior via SQLAlchemy | Cache em memoria do ultimo snapshot | SQLAlchemy query e mais robusto (sobrevive restart); cache em memoria perde dados se app reinicia |
| Tabela detected_signals no banco | Log file de sinais | Banco permite queries de deduplicacao SQL; log file exigiria parsing |

**Installation:**
Nenhuma nova dependencia necessaria. Tudo ja esta no requirements.txt.

## Architecture Patterns

### Recommended Project Structure
```
app/
  models.py              # MODIFICAR: adicionar DetectedSignal
  services/
    signal_service.py    # NEW: logica de deteccao de sinais
    snapshot_service.py  # MODIFICAR: adicionar query de snapshot anterior e media
    polling_service.py   # MODIFICAR: chamar signal detection apos salvar snapshot
```

### Pattern 1: Tabela DetectedSignal (Modelo de Dados)
**What:** Nova tabela para persistir sinais detectados com todos os campos necessarios para deduplicacao e exibicao futura (Phase 4 alertas, Phase 5 dashboard).
**When to use:** Sempre que um sinal for detectado.
**Example:**
```python
# app/models.py (adicao)
class DetectedSignal(Base):
    __tablename__ = "detected_signals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    route_group_id: Mapped[int] = mapped_column(ForeignKey("route_groups.id"))
    flight_snapshot_id: Mapped[int] = mapped_column(ForeignKey("flight_snapshots.id"))
    origin: Mapped[str] = mapped_column(String(3))
    destination: Mapped[str] = mapped_column(String(3))
    departure_date: Mapped[datetime.date] = mapped_column(Date)
    return_date: Mapped[datetime.date] = mapped_column(Date)
    signal_type: Mapped[str] = mapped_column(String(30))
    # Tipos: BALDE_FECHANDO, BALDE_REABERTO, PRECO_ABAIXO_HISTORICO, JANELA_OTIMA
    urgency: Mapped[str] = mapped_column(String(10))
    # Valores: MEDIA, ALTA, MAXIMA
    details: Mapped[str] = mapped_column(String(500))
    # Texto descritivo do sinal (ex: "Classe K: 5 -> 1 assentos")
    price_at_detection: Mapped[float] = mapped_column(Float)
    detected_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
```

**Indice para deduplicacao:**
```python
from sqlalchemy import Index

# No modelo ou via migration
Index(
    "ix_signal_dedup",
    DetectedSignal.route_group_id,
    DetectedSignal.origin,
    DetectedSignal.destination,
    DetectedSignal.departure_date,
    DetectedSignal.return_date,
    DetectedSignal.signal_type,
)
```

### Pattern 2: Signal Service com funcoes puras por tipo de sinal
**What:** Cada tipo de sinal e uma funcao pura que recebe dados e retorna um sinal ou None. Uma funcao orquestradora chama todas e persiste os sinais validos.
**When to use:** Chamada apos cada save_flight_snapshot no polling_service.
**Example:**
```python
# app/services/signal_service.py
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import (
    FlightSnapshot, BookingClassSnapshot, DetectedSignal
)

def detect_signals(db: Session, snapshot: FlightSnapshot) -> list[DetectedSignal]:
    """Orquestra deteccao de todos os tipos de sinal para um snapshot."""
    signals = []

    previous = _get_previous_snapshot(db, snapshot)

    balde_fechando = _check_balde_fechando(snapshot, previous)
    if balde_fechando:
        signals.append(balde_fechando)

    balde_reaberto = _check_balde_reaberto(snapshot, previous)
    if balde_reaberto:
        signals.append(balde_reaberto)

    preco_baixo = _check_preco_abaixo_historico(db, snapshot)
    if preco_baixo:
        signals.append(preco_baixo)

    janela = _check_janela_otima(snapshot)
    if janela:
        signals.append(janela)

    # Filtrar sinais ja emitidos (deduplicacao)
    new_signals = []
    for signal in signals:
        if not _is_duplicate(db, signal):
            db.add(signal)
            new_signals.append(signal)

    if new_signals:
        db.commit()

    return new_signals
```

### Pattern 3: Query de snapshot anterior
**What:** Buscar o snapshot mais recente anterior ao atual para a mesma rota (mesma combinacao origin+destination+departure_date+return_date).
**When to use:** Para SIGN-01 e SIGN-02 que comparam snapshots sequenciais.
**Example:**
```python
def _get_previous_snapshot(
    db: Session, current: FlightSnapshot
) -> FlightSnapshot | None:
    """Busca o snapshot imediatamente anterior para a mesma rota."""
    return (
        db.query(FlightSnapshot)
        .filter(
            FlightSnapshot.route_group_id == current.route_group_id,
            FlightSnapshot.origin == current.origin,
            FlightSnapshot.destination == current.destination,
            FlightSnapshot.departure_date == current.departure_date,
            FlightSnapshot.return_date == current.return_date,
            FlightSnapshot.id < current.id,  # anterior ao atual
        )
        .order_by(FlightSnapshot.collected_at.desc())
        .first()
    )
```

### Pattern 4: Query de deduplicacao (12 horas)
**What:** Verificar se o mesmo sinal ja foi emitido para a mesma rota nas ultimas 12 horas.
**When to use:** Antes de persistir qualquer sinal novo (SIGN-05).
**Example:**
```python
def _is_duplicate(db: Session, signal: DetectedSignal) -> bool:
    """Verifica se sinal identico foi emitido nas ultimas 12 horas."""
    cutoff = datetime.utcnow() - timedelta(hours=12)
    existing = (
        db.query(DetectedSignal)
        .filter(
            DetectedSignal.route_group_id == signal.route_group_id,
            DetectedSignal.origin == signal.origin,
            DetectedSignal.destination == signal.destination,
            DetectedSignal.departure_date == signal.departure_date,
            DetectedSignal.return_date == signal.return_date,
            DetectedSignal.signal_type == signal.signal_type,
            DetectedSignal.detected_at >= cutoff,
        )
        .first()
    )
    return existing is not None
```

### Pattern 5: Integracao com polling_service
**What:** Chamar detect_signals apos cada snapshot salvo.
**When to use:** Dentro de _process_offer no polling_service.
**Example:**
```python
# Em polling_service.py, dentro de _process_offer, apos save_flight_snapshot:
from app.services.signal_service import detect_signals

snapshot = save_flight_snapshot(db, snapshot_data)
detected = detect_signals(db, snapshot)
if detected:
    for signal in detected:
        logger.info(
            f"Signal detected: {signal.signal_type} ({signal.urgency}) "
            f"for {signal.origin}->{signal.destination} {signal.departure_date}"
        )
```

### Anti-Patterns to Avoid
- **Comparar snapshots de rotas diferentes:** A query de snapshot anterior DEVE filtrar por TODOS os 4 campos da rota (origin, destination, departure_date, return_date) alem do route_group_id. Sem isso, compara peras com macas.
- **Detector de sinal com side effects:** Funcoes de deteccao devem ser puras (recebem dados, retornam resultado). Persistencia e logging ficam no orquestrador.
- **Deduplicacao por ID de snapshot em vez de janela temporal:** O requisito e 12 horas, nao "mesmo ciclo de polling". Se o polling rodar 2x em 12h, a deduplicacao deve funcionar.
- **Tratar seats_available == 9 como exatamente 9:** Conforme Phase 2 research, Amadeus capeia em 9. Para BALDE FECHANDO, 9 deve ser tratado como "abundante" (>=3 e verdadeiro), mas nunca como numero exato.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Query temporal de snapshot anterior | Manter cache em memoria dos ultimos snapshots | SQLAlchemy query ORDER BY collected_at DESC LIMIT 1 | Cache perde dados no restart; query e simples e robusta |
| Deduplicacao de sinais | Comparar com lista em memoria | Query no banco com filtro temporal >= cutoff | Funciona entre restarts, entre ciclos de polling |
| Determinacao domestico vs internacional | Integrar API de geolocalizacao | Lista hardcoded de prefixos IATA brasileiros | Simplicidade; YAGNI; lista de aeroportos BR e estavel e pequena |

**Key insight:** Esta phase e 100% logica Python + queries SQLAlchemy. Nao ha APIs externas novas, nao ha dependencias novas. A complexidade e algoritmnica, nao infraestrutural. Isso significa que os testes podem ser 100% unitarios com banco in-memory, sem mocks de servicos externos.

## Common Pitfalls

### Pitfall 1: Primeiro snapshot de uma rota nao tem "anterior" para comparar
**What goes wrong:** _get_previous_snapshot retorna None; codigo tenta acessar booking_classes de None e crasheia.
**Why it happens:** Na primeira coleta de uma rota, nao existe snapshot anterior.
**How to avoid:** Verificar explicitamente se previous e None antes de checar BALDE FECHANDO e BALDE REABERTO. Retornar None (nenhum sinal detectado) quando nao ha historico.
**Warning signs:** NoneType has no attribute 'booking_classes' em logs.

### Pitfall 2: Booking classes do snapshot anterior podem ter classes diferentes do atual
**What goes wrong:** Snapshot anterior tem classes Y, B, M; snapshot atual tem Y, B, M, Q, K. Comparacao por indice falha.
**Why it happens:** Voos diferentes na mesma rota podem ter conjuntos diferentes de booking classes.
**How to avoid:** Converter booking_classes em dicionario {class_code: seats_available} para cada snapshot. Fazer lookup por class_code, nao por posicao na lista. Tratar classe ausente no anterior como 0 assentos (nunca visto = nao disponivel).
**Warning signs:** IndexError ou KeyError ao comparar listas de booking classes.

### Pitfall 3: Segment direction (OUTBOUND vs INBOUND) precisa ser considerado
**What goes wrong:** Classe K do OUTBOUND comparada com classe K do INBOUND.
**Why it happens:** BookingClassSnapshot tem segment_direction; se nao filtrar, compara segmentos diferentes.
**How to avoid:** Ao comparar booking classes entre snapshots, filtrar por segment_direction. Ou alternativamente, agregar: usar o MINIMO de seats_available entre OUTBOUND e INBOUND para a mesma classe (o "gargalo" determina o sinal).
**Warning signs:** Sinal falso de BALDE FECHANDO quando na verdade era comparacao entre outbound e inbound.

### Pitfall 4: Media de precos com poucos snapshots
**What goes wrong:** SIGN-03 exige media dos ultimos 14 snapshots; se so existem 2, a media nao e representativa.
**Why it happens:** Rota nova com pouco historico.
**How to avoid:** Exigir minimo de 3 snapshots para calcular media. Se menos de 3, nao emitir sinal PRECO ABAIXO DO HISTORICO. Documentar o threshold minimo.
**Warning signs:** Media de preco baseada em 1 snapshot, gerando sinais falsos.

### Pitfall 5: Determinacao domestico vs internacional
**What goes wrong:** Usar heuristica incorreta para determinar se rota e domestica.
**Why it happens:** Nao ha campo "pais" nos dados; depende de inferencia a partir do IATA code.
**How to avoid:** Aeroportos brasileiros comecam com "S" no codigo IATA (ex: GRU=SBGR, GIG=SBRJ, BSB=SBBR). Mas o modelo armazena codigos de 3 letras (GRU, GIG, BSB), nao ICAO. Portanto: usar lista hardcoded dos aeroportos brasileiros mais comuns. Se ambos origin e destination estao na lista, e domestico. Caso contrario, internacional.
**Warning signs:** Rota GRU-GIG classificada como internacional, ou GRU-MIA como domestica.

### Pitfall 6: Timezone em deduplicacao de 12 horas
**What goes wrong:** Sinal emitido as 23:50 UTC nao e detectado como duplicata de sinal emitido as 00:10 UTC (10 minutos antes), porque a logica compara datas sem considerar timezone.
**Why it happens:** SQLite armazena datetime sem timezone; func.now() retorna hora local do servidor.
**How to avoid:** Usar datetime.utcnow() consistentemente para detected_at e para o cutoff de 12 horas. Ou usar datetime.now(timezone.utc). O importante e ser consistente.
**Warning signs:** Sinais duplicados aparecendo em intervalos menores que 12 horas.

## Code Examples

### Detector BALDE FECHANDO (SIGN-01)
```python
# Funcao pura: recebe snapshots, retorna sinal ou None
CLOSING_CLASSES = {"K", "Q"}
CLOSING_THRESHOLD_FROM = 3  # era >= 3
CLOSING_THRESHOLD_TO = 1    # agora <= 1

def _check_balde_fechando(
    current: FlightSnapshot, previous: FlightSnapshot | None
) -> DetectedSignal | None:
    if previous is None:
        return None

    prev_classes = _booking_classes_to_dict(previous.booking_classes)
    curr_classes = _booking_classes_to_dict(current.booking_classes)

    for class_code in CLOSING_CLASSES:
        prev_seats = prev_classes.get(class_code, 0)
        curr_seats = curr_classes.get(class_code, 0)

        if prev_seats >= CLOSING_THRESHOLD_FROM and curr_seats <= CLOSING_THRESHOLD_TO:
            return DetectedSignal(
                route_group_id=current.route_group_id,
                flight_snapshot_id=current.id,
                origin=current.origin,
                destination=current.destination,
                departure_date=current.departure_date,
                return_date=current.return_date,
                signal_type="BALDE_FECHANDO",
                urgency="ALTA",
                details=f"Classe {class_code}: {prev_seats} -> {curr_seats} assentos",
                price_at_detection=current.price,
            )
    return None


def _booking_classes_to_dict(
    booking_classes: list[BookingClassSnapshot],
) -> dict[str, int]:
    """Converte lista de BookingClassSnapshot em dict {class_code: min_seats}.
    Usa minimo entre OUTBOUND e INBOUND como gargalo."""
    result = {}
    for bc in booking_classes:
        code = bc.class_code
        if code not in result:
            result[code] = bc.seats_available
        else:
            result[code] = min(result[code], bc.seats_available)
    return result
```

### Detector BALDE REABERTO (SIGN-02)
```python
def _check_balde_reaberto(
    current: FlightSnapshot, previous: FlightSnapshot | None
) -> DetectedSignal | None:
    if previous is None:
        return None

    prev_classes = _booking_classes_to_dict(previous.booking_classes)
    curr_classes = _booking_classes_to_dict(current.booking_classes)

    reopened = []
    for class_code, curr_seats in curr_classes.items():
        prev_seats = prev_classes.get(class_code, 0)
        if prev_seats == 0 and curr_seats > 0:
            reopened.append(f"{class_code}: 0 -> {curr_seats}")

    if reopened:
        return DetectedSignal(
            route_group_id=current.route_group_id,
            flight_snapshot_id=current.id,
            origin=current.origin,
            destination=current.destination,
            departure_date=current.departure_date,
            return_date=current.return_date,
            signal_type="BALDE_REABERTO",
            urgency="MAXIMA",
            details=f"Classes reabriram: {', '.join(reopened)}",
            price_at_detection=current.price,
        )
    return None
```

### Detector PRECO ABAIXO DO HISTORICO (SIGN-03)
```python
from sqlalchemy import func as sa_func

def _check_preco_abaixo_historico(
    db: Session, snapshot: FlightSnapshot
) -> DetectedSignal | None:
    if snapshot.price_classification != "LOW":
        return None

    # Media dos ultimos 14 snapshots da mesma rota
    avg_result = (
        db.query(sa_func.avg(FlightSnapshot.price), sa_func.count(FlightSnapshot.id))
        .filter(
            FlightSnapshot.route_group_id == snapshot.route_group_id,
            FlightSnapshot.origin == snapshot.origin,
            FlightSnapshot.destination == snapshot.destination,
            FlightSnapshot.departure_date == snapshot.departure_date,
            FlightSnapshot.return_date == snapshot.return_date,
            FlightSnapshot.id < snapshot.id,
        )
        .order_by(FlightSnapshot.collected_at.desc())
        .limit(14)
        .one()
    )

    # Nota: o limit acima nao funciona como esperado em aggregate.
    # Usar subquery para pegar os ultimos 14 e depois calcular media.
    # Ver secao "Query Correta" abaixo.

    return None  # placeholder - ver implementacao correta
```

### Query correta para media dos ultimos 14 snapshots
```python
from sqlalchemy import select

def _get_avg_price_last_n(
    db: Session, snapshot: FlightSnapshot, n: int = 14
) -> tuple[float | None, int]:
    """Retorna (media_de_preco, contagem) dos ultimos N snapshots da mesma rota."""
    subquery = (
        select(FlightSnapshot.price)
        .where(
            FlightSnapshot.route_group_id == snapshot.route_group_id,
            FlightSnapshot.origin == snapshot.origin,
            FlightSnapshot.destination == snapshot.destination,
            FlightSnapshot.departure_date == snapshot.departure_date,
            FlightSnapshot.return_date == snapshot.return_date,
            FlightSnapshot.id < snapshot.id,
        )
        .order_by(FlightSnapshot.collected_at.desc())
        .limit(n)
        .subquery()
    )
    result = db.execute(
        select(sa_func.avg(subquery.c.price), sa_func.count())
    ).one()
    return result[0], result[1]
```

### Detector JANELA OTIMA (SIGN-04)
```python
from datetime import date

# Aeroportos brasileiros mais comuns (3-letter IATA)
BRAZILIAN_AIRPORTS = {
    "GRU", "CGH", "VCP",  # Sao Paulo
    "GIG", "SDU",          # Rio de Janeiro
    "BSB",                 # Brasilia
    "CNF", "PLU",          # Belo Horizonte
    "SSA",                 # Salvador
    "REC",                 # Recife
    "FOR",                 # Fortaleza
    "POA",                 # Porto Alegre
    "CWB",                 # Curitiba
    "FLN",                 # Florianopolis
    "BEL",                 # Belem
    "MAO",                 # Manaus
    "NAT",                 # Natal
    "MCZ",                 # Maceio
    "VIX",                 # Vitoria
    "CGB",                 # Cuiaba
    "GYN",                 # Goiania
    "SLZ",                 # Sao Luis
    "THE",                 # Teresina
    "AJU",                 # Aracaju
    "JPA",                 # Joao Pessoa
    "PMW",                 # Palmas
    "IGU",                 # Foz do Iguacu
}

DOMESTIC_WINDOW = (21, 90)    # dias
INTERNATIONAL_WINDOW = (30, 120)  # dias


def _is_domestic(origin: str, destination: str) -> bool:
    return origin in BRAZILIAN_AIRPORTS and destination in BRAZILIAN_AIRPORTS


def _check_janela_otima(snapshot: FlightSnapshot) -> DetectedSignal | None:
    today = date.today()
    days_until = (snapshot.departure_date - today).days

    if days_until <= 0:
        return None

    domestic = _is_domestic(snapshot.origin, snapshot.destination)
    window = DOMESTIC_WINDOW if domestic else INTERNATIONAL_WINDOW

    if window[0] <= days_until <= window[1]:
        route_type = "domestico" if domestic else "internacional"
        return DetectedSignal(
            route_group_id=snapshot.route_group_id,
            flight_snapshot_id=snapshot.id,
            origin=snapshot.origin,
            destination=snapshot.destination,
            departure_date=snapshot.departure_date,
            return_date=snapshot.return_date,
            signal_type="JANELA_OTIMA",
            urgency="MEDIA",
            details=(
                f"Voo {route_type} em {days_until} dias "
                f"(janela ideal: {window[0]}-{window[1]} dias)"
            ),
            price_at_detection=snapshot.price,
        )
    return None
```

### Estrutura do indice de deduplicacao
```python
# Em models.py, apos a classe DetectedSignal
from sqlalchemy import Index

Index(
    "ix_signal_dedup",
    DetectedSignal.route_group_id,
    DetectedSignal.origin,
    DetectedSignal.destination,
    DetectedSignal.departure_date,
    DetectedSignal.return_date,
    DetectedSignal.signal_type,
)
```

## Decisoes de Design Investigadas

### Como agregar booking classes entre OUTBOUND e INBOUND?

O BookingClassSnapshot tem campo `segment_direction` (OUTBOUND/INBOUND). Para detectar BALDE FECHANDO e BALDE REABERTO, precisamos de um unico numero por classe.

**Opcoes investigadas:**
1. **Analisar cada direcao separadamente:** Gera sinais duplicados (um para outbound, outro para inbound)
2. **Usar minimo entre as direcoes:** O gargalo determina a disponibilidade real. Se K tem 5 no outbound e 1 no inbound, o assento real e 1.
3. **Usar maximo:** Otimista demais; nao reflete a restricao real.

**Recomendacao:** Opcao 2 (minimo). O passageiro precisa de assentos nas DUAS direcoes. O minimo reflete a restricao real. Confidence: HIGH (logica de negocio direta).

### Como determinar domestico vs internacional?

Nao ha campo explicito no modelo. Opcoes:
1. **Lista hardcoded de IATA brasileiros:** Simples, cobre 95%+ dos casos de uso pessoal do autor.
2. **API de lookup de IATA:** Overengineering para uso pessoal com poucos aeroportos.
3. **Campo configuravel no RouteGroup:** Exige mudanca de schema e API; viola YAGNI.

**Recomendacao:** Opcao 1. Lista de ~25 aeroportos brasileiros mais comuns. Se ambos estao na lista, domestico. Confidence: HIGH (YAGNI, caso de uso pessoal, lista estavel).

### SIGN-03: O que conta como "ultimos 14 snapshots"?

O requisito diz "media dos ultimos 14 snapshots". Interpretacao:
- "14 snapshots" = 14 registros anteriores da MESMA rota (nao 14 dias, nao 14 de qualquer rota)
- Filtrar por mesma rota: route_group_id + origin + destination + departure_date + return_date
- Ordenar por collected_at DESC, LIMIT 14

**Recomendacao:** Subquery com LIMIT 14 ORDER BY collected_at DESC, depois AVG sobre o resultado. Exigir minimo de 3 snapshots para media significativa. Confidence: HIGH.

### Prioridade quando multiplos sinais sao detectados no mesmo snapshot

E possivel que um unico snapshot gere multiplos sinais (ex: BALDE FECHANDO + PRECO ABAIXO DO HISTORICO ao mesmo tempo). O requisito nao define limite.

**Recomendacao:** Emitir todos os sinais detectados. Cada um e independente e tem deduplicacao propria. A Phase 4 (alertas) pode consolidar multiplos sinais em um unico email. Confidence: MEDIUM (requisito nao explicito; recomendacao sensata).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| datetime.utcnow() | datetime.now(timezone.utc) | Python 3.12 deprecation warning | Usar timezone-aware datetimes para consistencia |
| SQLAlchemy 1.x Query API | SQLAlchemy 2.0 select() API | 2023 | Ambos funcionam em 2.0.40; manter consistencia com Phase 1/2 patterns |

**Nota:** O projeto usa SQLAlchemy 2.0.40 mas o codigo existente usa o estilo legacy `db.query(Model)`. Manter consistencia com o existente (usar db.query) em vez de migrar para select() nesta phase.

## Open Questions

1. **SIGN-02: "classe estava em 0" significa qualquer classe ou so classes economicas?**
   - What we know: O requisito diz "classe estava em 0 e voltou a ter assentos" sem especificar quais classes
   - What's unclear: Se devemos checar TODAS as classes ou apenas classes economicas relevantes (K, Q, L, M)
   - Recommendation: Checar todas as classes presentes nos snapshots. Se o requisito quiser restringir, pode ser ajustado apos feedback do usuario. Mapear apenas classes que existiam no snapshot anterior (nao gerar sinal para classe nova que nao existia antes).

2. **Minimo de snapshots para SIGN-03: 3 e suficiente?**
   - What we know: 14 snapshots = ~3.5 dias de coleta (com polling a cada 6h). Nos primeiros dias, tera menos de 14.
   - What's unclear: Qual o threshold minimo para media confiavel.
   - Recommendation: Usar 3 como minimo. Se tiver menos de 3 snapshots anteriores, nao emitir SIGN-03. Documentar nos testes.

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
| SIGN-01 | Detecta BALDE FECHANDO (K/Q: >=3 para <=1) | unit | `python -m pytest tests/test_signal_service.py::test_balde_fechando -x` | Wave 0 |
| SIGN-01 | Nao detecta quando K/Q permanece estavel | unit | `python -m pytest tests/test_signal_service.py::test_balde_fechando_no_change -x` | Wave 0 |
| SIGN-02 | Detecta BALDE REABERTO (0 para >0) | unit | `python -m pytest tests/test_signal_service.py::test_balde_reaberto -x` | Wave 0 |
| SIGN-02 | Nao detecta quando classe ja tinha assentos | unit | `python -m pytest tests/test_signal_service.py::test_balde_reaberto_already_open -x` | Wave 0 |
| SIGN-03 | Detecta PRECO ABAIXO HISTORICO (LOW + abaixo da media) | unit | `python -m pytest tests/test_signal_service.py::test_preco_abaixo_historico -x` | Wave 0 |
| SIGN-03 | Nao detecta quando preco e LOW mas acima da media | unit | `python -m pytest tests/test_signal_service.py::test_preco_low_mas_acima_media -x` | Wave 0 |
| SIGN-03 | Nao detecta com menos de 3 snapshots historicos | unit | `python -m pytest tests/test_signal_service.py::test_preco_insufficient_history -x` | Wave 0 |
| SIGN-04 | Detecta JANELA OTIMA domestico (21-90 dias) | unit | `python -m pytest tests/test_signal_service.py::test_janela_otima_domestico -x` | Wave 0 |
| SIGN-04 | Detecta JANELA OTIMA internacional (30-120 dias) | unit | `python -m pytest tests/test_signal_service.py::test_janela_otima_internacional -x` | Wave 0 |
| SIGN-04 | Nao detecta fora da janela | unit | `python -m pytest tests/test_signal_service.py::test_janela_fora_da_faixa -x` | Wave 0 |
| SIGN-05 | Deduplicacao bloqueia sinal identico em <12h | unit | `python -m pytest tests/test_signal_service.py::test_deduplicacao_bloqueia -x` | Wave 0 |
| SIGN-05 | Deduplicacao permite sinal apos >12h | unit | `python -m pytest tests/test_signal_service.py::test_deduplicacao_permite_apos_12h -x` | Wave 0 |
| ALL | Primeiro snapshot (sem anterior) nao gera sinais de balde | unit | `python -m pytest tests/test_signal_service.py::test_primeiro_snapshot_sem_sinal_balde -x` | Wave 0 |
| ALL | DetectedSignal persiste no banco | unit | `python -m pytest tests/test_signal_service.py::test_signal_persisted -x` | Wave 0 |
| ALL | Integracao: polling_service chama detect_signals | unit | `python -m pytest tests/test_polling_service.py::test_signal_detection_called -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green antes de /gsd:verify-work

### Wave 0 Gaps
- [ ] `tests/test_signal_service.py` - covers SIGN-01, SIGN-02, SIGN-03, SIGN-04, SIGN-05
- [ ] `tests/test_signal_model.py` - covers DetectedSignal model persistence and index
- [ ] Nenhuma dependencia nova necessaria; framework e fixtures ja existem

## Sources

### Primary (HIGH confidence)
- Codebase existente: app/models.py, app/services/polling_service.py, app/services/snapshot_service.py, tests/conftest.py
- SQLAlchemy 2.0.40 ORM query patterns (ja em uso no projeto)
- Phase 2 Research (02-RESEARCH.md) para contexto de dados coletados

### Secondary (MEDIUM confidence)
- Lista de aeroportos IATA brasileiros (conhecimento geral, facilmente verificavel)
- Python datetime timezone handling (documentacao stdlib)

### Tertiary (LOW confidence)
- Nenhum item LOW confidence nesta phase; toda a logica e deterministica e testavel

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - nenhuma dependencia nova; tudo ja existe no projeto
- Architecture: HIGH - extensao direta dos patterns da Phase 2 (novo service + novo model)
- Signal detection algorithms: HIGH - logica deterministica com thresholds bem definidos nos requisitos
- Deduplicacao: HIGH - query temporal simples com indice composto
- Domestico vs internacional: MEDIUM - heuristica por lista hardcoded funciona para uso pessoal, mas nao e 100% completa

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (logica interna sem dependencias externas que mudem)
