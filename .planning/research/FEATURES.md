# Feature Landscape

**Domain:** Flight price prediction / booking class inventory signals
**Researched:** 2026-03-25

---

## Signal Detection: What Each API Can Power

This table maps the four project signals to data sources based on research findings.

| Signal | Data Required | APIs That Support It | Confidence |
|--------|--------------|---------------------|------------|
| BALDE FECHANDO (K/Q drops from >=3 to <=1) | Per-class seat count (RBD level) | Amadeus Flight Availabilities Search (closing July 2026) | HIGH for Amadeus; blocked for all others |
| BALDE REABERTO (class at 0 comes back) | Per-class seat count delta | Same as above | HIGH for Amadeus; blocked for all others |
| PRECO ABAIXO HISTORICO | Price time series for route | SerpAPI, FlightAPI.io, Kiwi Tequila | HIGH |
| JANELA OTIMA | Days-before-flight + price curve | SerpAPI price_history + local historical store | HIGH |

---

## Table Stakes

Features expected for a functional flight monitor. Missing = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Price polling per route on schedule | Core monitoring function | Low | APScheduler already handles this |
| Historical price store (per route/date) | Required for PRECO ABAIXO HISTORICO baseline | Low | SQLite snapshots over time |
| Telegram alert delivery | Core output | Low | Already implemented |
| Per-route configuration | Different routes have different ideal booking windows | Low | Config-driven |
| Deduplication of alerts | Avoid spamming same signal twice | Low | Track last-alerted state |

---

## Differentiators

Features that add value beyond basic price alerts.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Inventory snapshot history | Allows reconstruction of BALDE FECHANDO trend over time even if polling interval is wide | Medium | Store availabilityClasses snapshots per poll; requires Amadeus while available |
| Price history export | User can review trend graphs | Low-Medium | SerpAPI price_history gives timestamps |
| JANELA OTIMA calibration by route type | Short-haul vs long-haul have different optimal booking windows | Medium | Parameterize per route in config |
| BALDE REABERTO urgency ranking | Not all reopened classes are equal (K reopen > Y reopen) | Low | Sort by fare class hierarchy in alert |

---

## Anti-Features

Features to explicitly NOT build given current API landscape.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Scraping airline websites for inventory | Terms of service violation; fragile against HTML changes | Use official APIs only |
| Booking integration | Amadeus Enterprise required for real bookings; completely out of scope | Link to airline/OTA booking pages |
| Aggregating inventory across all airlines | No accessible API provides this; GDS APIs require business contracts | Limit to specific covered airlines (LH Group if using Lufthansa API) |
| Building a GDS relationship just for this | Annual fees $5,000+, agency certification required | Use Amadeus keys while they last; move to price-only signals after July 2026 |
| Real-time sub-minute polling | Rate limits on all APIs prevent this; Lufthansa caps at 6/second 1,000/hour | Poll every 30-60 minutes; that is sufficient for BALDE detection |

---

## Feature Dependencies

```
BALDE FECHANDO --> Per-class seat count from Amadeus (or GDS)
BALDE REABERTO --> Per-class seat count delta from Amadeus (or GDS)
PRECO ABAIXO HISTORICO --> Price time series (any price API)
JANELA OTIMA --> Price time series + route booking window config
Alert delivery --> Any signal being triggered
Deduplication --> Alert delivery + persistent signal state storage
```

---

## MVP Recommendation Given API Reality

Prioritize what works today:

1. PRECO ABAIXO HISTORICO using SerpAPI free tier (250 searches/month covers 3-4 routes polled 2x/day)
2. JANELA OTIMA using local price history built from SerpAPI data
3. BALDE FECHANDO and BALDE REABERTO using Amadeus ONLY IF keys already exist

Defer:
- GDS onboarding: Requires business entity and IATA; months-long process
- Lufthansa fare plan: Apply now; while waiting, feature is blocked for non-LH routes

---

## Sources

- Amadeus availabilityClasses description: https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/flights/
- SerpAPI price_history field: https://serpapi.com/google-flights-price-insights
- Travelport BookingCodeInfo (booking class presence): https://support.travelport.com/webhelp/uapi/Content/Air/Air_Availability/Air%20Availability%20by%20Booking%20Class.htm
- OAG cabin-only seats (not RBD-level): https://www.oag.com/flight-data-seats
- AwardFares confirmation GDS capped at 9: https://blog.awardfares.com/flight-schedules/
