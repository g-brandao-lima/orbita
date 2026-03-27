# Architecture Patterns

**Domain:** Flight price prediction / booking class inventory monitoring
**Researched:** 2026-03-25

---

## Recommended Architecture

Two-lane data pipeline: one lane for price data (accessible, durable), one lane for inventory data (time-limited, high-value).

```
Scheduler (APScheduler)
    |
    +---> Price Lane ---> SerpAPI / FlightAPI.io ---> PriceSnapshot table
    |                                                       |
    |                                                       v
    |                                              Signal Engine
    |                                              (PRECO, JANELA)
    |
    +---> Inventory Lane ---> Amadeus Flight Availabilities Search
                              (while keys exist, until July 17, 2026)
                                        |
                                        v
                               InventorySnapshot table
                                        |
                                        v
                              Signal Engine (BALDE FECHANDO, REABERTO)
                                        |
                                        v
                              Alert Deduplication
                                        |
                                        v
                              Telegram Bot
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| Scheduler | Triggers polling jobs at configured intervals | Price Collector, Inventory Collector |
| Price Collector | Calls external price API, normalizes response | PriceSnapshot store |
| Inventory Collector | Calls Amadeus availabilityClasses, normalizes per-class counts | InventorySnapshot store |
| Signal Engine | Reads snapshots, evaluates signal conditions | Alert Deduplicator |
| Alert Deduplicator | Tracks last-fired state per route per signal | Telegram Notifier |
| Telegram Notifier | Formats and sends alerts | Telegram Bot API |

### Data Flow

```
External API --> Collector --> Raw Snapshot (stored as-is)
                                     |
                            Signal Engine reads last N snapshots
                                     |
                            Evaluate condition (e.g. K class: prev=3, now=1)
                                     |
                            Check dedup state (was this already alerted?)
                                     |
                            Fire Telegram message with urgency level
```

---

## Patterns to Follow

### Pattern: Snapshot-before-signal

**What:** Store the raw API response snapshot to disk before evaluating any signal. Never derive signals from in-memory state only.

**When:** Every poll cycle.

**Why:** If the process restarts, signals can be recomputed from stored snapshots. This is especially important for inventory data since Amadeus access will eventually end and you want to preserve all historical inventory readings you captured.

```python
# Correct order
snapshot = fetch_availability(route)
store_snapshot(snapshot)           # persist first
signals = evaluate_signals(route)  # compute from stored data
```

### Pattern: Pluggable data source per signal type

**What:** Abstract the price and inventory fetchers behind a common interface so the source can be swapped when API access changes.

```python
class InventorySource(Protocol):
    def get_availability(self, origin: str, destination: str, date: str) -> list[ClassAvailability]: ...

class AmadeusInventorySource:
    def get_availability(self, ...) -> list[ClassAvailability]: ...

class StubInventorySource:   # fallback when Amadeus goes down
    def get_availability(self, ...) -> list[ClassAvailability]:
        return []  # no data, no inventory signals fired
```

**When:** Now, before July 2026, so swapping is zero-risk.

### Pattern: Graceful degradation for missing inventory

**What:** When the inventory source returns nothing (API down, keys revoked, plan expired), suppress BALDE signals entirely rather than firing false alerts or crashing.

**When:** After July 17, 2026 when Amadeus keys are disabled.

---

## Anti-Patterns to Avoid

### Anti-Pattern: Polling inventory at the same rate as prices

**Why bad:** Inventory API calls are more expensive in rate limit terms. Amadeus self-service had per-call limits. Lufthansa caps at 1,000/hour. Price APIs (SerpAPI free = 250/month) are even tighter.

**Instead:** Poll prices more frequently (every 2-4 hours), inventory less frequently (every 4-8 hours) for routes monitored. Calculate optimal polling frequency against rate limits and number of routes.

### Anti-Pattern: Depending on a single API without a cutover plan

**Why bad:** Amadeus self-service is shutting down July 2026. Building only around it means all inventory signals die on that date.

**Instead:** Design the inventory source as pluggable from day one, and start evaluating Lufthansa fare plan access now as a partial replacement.

### Anti-Pattern: Using GDS-style booking class data as a booking engine

**Why bad:** APIs like Amadeus self-service prohibited actual ticket creation unless upgraded to enterprise. The inventory data is for monitoring, not for creating orders.

**Instead:** Surface the signal and link to the airline booking page or Google Flights for the actual purchase.

---

## Scalability Considerations

This is a personal project monitoring 3-5 routes. Scalability beyond this is out of scope, but the architecture handles the relevant operational concerns.

| Concern | Current scale (3-5 routes) | What breaks first |
|---------|---------------------------|-------------------|
| API rate limits | SerpAPI free: 250 searches/month = ~8/day; enough for 5 routes polled 1x/day | Rate limits; need to upgrade to $25 plan |
| SQLite concurrency | Single writer (scheduler); no issue | Not an issue at this scale |
| Alert spam | Deduplication logic prevents | Signal state must survive process restart |

---

## Sources

- Amadeus self-service shutdown: https://tragento.com/en/amadeus-announced-the-shutdown-of-the-self-service-api-portal-for-developers/
- Lufthansa rate limits (6/sec, 1000/hour): https://developer.lufthansa.com/Fares_Availability
- SerpAPI rate limits by plan: https://serpapi.com/pricing
- Travelport air availability response (BookingCodeInfo): https://support.travelport.com/webhelp/uapi/Content/Air/Air_Availability/Air%20Availability%20by%20Booking%20Class.htm
