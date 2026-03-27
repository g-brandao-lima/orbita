# Technology Stack

**Project:** Flight Monitor - Booking Class Inventory
**Researched:** 2026-03-25

---

## Recommended Stack

The current stack (Python, FastAPI, SQLite, APScheduler, Telegram Bot API, Jinja2) is appropriate. The research question is specifically about data sourcing, not the application stack. Recommendations below focus on the API data layer.

### Data API Layer - Price Signals (fully accessible today)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SerpAPI Google Flights | current | Price snapshots, price history arrays | Free tier (250/month), price_history field with timestamps, structured JSON. No booking class data. |
| FlightAPI.io | current | Price polling across 700+ airlines/OTAs | $49/month for 30k credits, simpler than SerpAPI for bulk route monitoring |
| Kiwi Tequila API | current | Price search with `seats` field per itinerary | Free for partners. Exposes a `seats` count (total seats on itinerary, not per fare class). Not RBD-level. |

### Data API Layer - Inventory Signals (booking class counts)

| Technology | Confidence | Purpose | Access Status |
|------------|------------|---------|--------------|
| Amadeus Flight Availabilities Search | HIGH | `availabilityClasses` with RBD codes + seat counts (capped at 9) | CRITICAL: new registration closed March 2026; full shutdown July 17, 2026 |
| Lufthansa Open API - Fare Plan | MEDIUM | Fares and availability for LH Group airlines | Free but requires use-case approval; RBD depth unverified |
| Sabre Bargain Finder Max | MEDIUM | Full GDS inventory data | Sandbox free; production requires travel agency certification |
| Travelport Universal API | MEDIUM | `BookingCodeInfo` in availability response | 30-day sandbox trial; production requires business contract |

### Supporting Libraries (existing, appropriate)

| Library | Purpose | Keep? |
|---------|---------|-------|
| APScheduler | Periodic polling of APIs | Yes |
| SQLite | Storing price snapshots and inventory history | Yes, sufficient for 1-3 routes |
| Telegram Bot API | Alert delivery | Yes |
| FastAPI | Dashboard/health endpoint | Yes |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Price-only API | SerpAPI | AviationStack | AviationStack is flight status/tracking only, no booking prices |
| Price-only API | SerpAPI | Skyscanner API | Skyscanner requires formal partner approval, not self-service |
| Inventory API | Amadeus (while keys last) | Duffel | Duffel does not expose per-class seat counts; it is a booking/selling API |
| Inventory API | Amadeus (while keys last) | OAG | OAG seat data is cabin-level only (Economy/Business), not RBD-level |
| Long-term inventory | Lufthansa Open API | Sabre | Sabre has stronger data but requires IATA affiliation |

---

## Installation for Price Signal Layer

```bash
# SerpAPI Python client
pip install google-search-results

# FlightAPI.io (REST, no dedicated client needed)
pip install httpx  # already likely present

# Kiwi Tequila (REST)
# No dedicated client; use httpx or requests
```

---

## Sources

- Amadeus shutdown: https://www.phocuswire.com/amadeus-shut-down-self-service-apis-portal-developers
- Amadeus shutdown detail: https://tragento.com/en/amadeus-announced-the-shutdown-of-the-self-service-api-portal-for-developers/
- Amadeus Flight Availabilities Search (availabilityClasses): https://developers.amadeus.com/self-service/category/flights/api-doc/flight-availabilities-search
- SerpAPI pricing: https://serpapi.com/pricing
- SerpAPI price history structure: https://serpapi.com/google-flights-price-insights
- Duffel offers schema: https://duffel.com/docs/api/v2/offers
- Duffel pricing: https://duffel.com/pricing
- Lufthansa fares/availability plan: https://developer.lufthansa.com/Fares_Availability
- Travelport Air Availability by Booking Class: https://support.travelport.com/webhelp/uapi/Content/Air/Air_Availability/Air%20Availability%20by%20Booking%20Class.htm
- OAG seat data granularity: https://www.oag.com/flight-data-seats
