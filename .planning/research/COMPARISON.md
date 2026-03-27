# Comparison: Flight Data APIs for Booking Class Inventory

**Context:** Which API can power the four signals in flight-monitor (BALDE FECHANDO, BALDE REABERTO, PRECO ABAIXO HISTORICO, JANELA OTIMA)?
**Recommendation:** No single API covers all four signals for an individual developer in March 2026. The minimum viable combination is Amadeus (if keys exist) + SerpAPI. After July 2026, only price signals are achievable without a GDS business relationship.

---

## Quick Comparison

| API | Exposes RBD Seat Counts | Price Data | Free Tier | Individual Dev Access | Signals Supported |
|-----|------------------------|------------|-----------|----------------------|-------------------|
| Amadeus Flight Availabilities Search | YES (capped at 9) | YES | YES (was; registration closed March 2026) | WAS yes; now blocked | BALDE + PRECO + JANELA |
| Duffel API | NO (fare_basis_code only) | YES | Sandbox free; prod $3/order | YES (but booking-focused) | PRECO, JANELA (via price) |
| Sabre Bargain Finder Max | YES (GDS full inventory) | YES | Sandbox free | NO (production needs agency cert) | All (if production access) |
| Travelport Universal API | PARTIAL (depends on supplier) | YES | 30-day sandbox trial | NO (production needs contract) | Partial BALDE + PRECO |
| Lufthansa Open API (fare plan) | UNKNOWN (unverified depth) | YES | YES (free, use-case approval) | YES (pending approval) | Unknown BALDE, LH Group only |
| OAG Flight Seats | NO (cabin-level only) | NO | Contact sales | Enterprise/B2B only | None of the four |
| SerpAPI Google Flights | NO | YES + price history | 250/month free | YES (instant) | PRECO + JANELA |
| Kiwi Tequila | NO (total itinerary seats, not RBD) | YES | Free for partners | YES | PRECO + JANELA |
| FlightAPI.io | NO | YES | 20 calls trial; $49/month | YES | PRECO + JANELA |
| Skyscanner API | NO | YES | No (partner approval) | NO (established business) | PRECO + JANELA (if approved) |
| AviationStack | NO (flight status, not fares) | NO (no booking prices) | 100/month | YES | None of the four |
| Google Flights via SerpAPI | NO | YES + price history | 250/month | YES (instant) | PRECO + JANELA |

---

## Detailed Analysis

### Amadeus Flight Availabilities Search

**Strengths:**
- Uniquely exposed `availabilityClasses` list with `{bookingCode: "K", numberOfBookableSeats: 3}` per class
- Seat counts capped at 9 (same convention as GDS professional tools - confirmed match to the Y7 B4 M3 format)
- Self-service with immediate API key issuance (until March 2026)
- Free tier with per-call pricing model; affordable for personal projects

**Weaknesses:**
- Registration closed March 2026
- Full shutdown July 17, 2026 - existing keys disabled on that date
- Did not cover American Airlines, Delta, British Airways, low-cost carriers in self-service tier
- No path to Enterprise without formal travel industry partnership

**Best for:** Existing users with active keys should use this for all inventory signals until July 2026 and snapshot everything.

---

### Duffel API

**Strengths:**
- Modern REST API, excellent developer experience
- Sandbox free; production $3/confirmed order (not per search)
- Covers 300+ airlines including NDC content
- Returns `fare_basis_code` and `cabin_class`

**Weaknesses:**
- Does NOT return per-class seat counts. This was confirmed by reviewing the official offers schema.
- It is a booking/selling API, not an inventory monitoring API. Fare availability is implicitly binary (returned in search = available).
- $3/order is irrelevant for monitoring (you do not create orders to check inventory)
- Excess searches beyond 1500:1 ratio cost $0.005 each

**Best for:** If you want to verify current price and availability for a specific fare class to confirm a signal before alerting. Not for continuous inventory polling.

---

### Sabre Dev Studio

**Strengths:**
- Full GDS inventory access - the gold standard for booking class seat counts
- REST API (Bargain Finder Max) available
- Sandbox access is free and self-service via developer.sabre.com

**Weaknesses:**
- Production requires formal travel agency onboarding: IATA/ARC number, contract, certification (15+ business days minimum)
- Annual costs estimated $5,000+ for access fees alone
- Not realistically accessible to an individual developer without a registered travel business

**Best for:** Future path if this project grows into a commercial product. Technically the best data quality.

---

### Travelport Universal API

**Strengths:**
- Has `AirAvailabilitySearchRsp` with `BookingCodeInfo` - returns booking class codes present
- 30-day sandbox trial available without business registration
- REST API (JSON) for newer versions

**Weaknesses:**
- Seat counts are supplier-dependent: not all airlines return counts; Travelport derives from passenger count if supplier does not provide
- Production requires minimum booking volume contract; annual fees similar to Sabre
- The "booking class returned" does not necessarily mean "seat count returned" - the `numberOfBookableSeats` equivalent may not be populated

**Best for:** Testing in sandbox to verify whether specific airlines you monitor provide seat counts. Do not assume counts will be available in production without testing.

---

### Lufthansa Open API (Fare/Availability Plan)

**Strengths:**
- Genuinely free (both plans currently free per official site)
- Accessible to individual developers; requires submitting a use-case description
- Rate limits are reasonable: 6/second, 1,000/hour
- Official airline direct data - not aggregated

**Weaknesses:**
- RBD seat count granularity is unconfirmed. The page says "fare/availability data" which may mean availability flag only (available/not available), not the actual count
- Coverage limited to Lufthansa Group: LH, LX, OS, SN, EN (5 airlines)
- Requires application approval - not instant access
- If only returns binary availability, BALDE FECHANDO detection is impossible (you can detect closing but not the magnitude: was it at 3 or at 7 before closing?)

**Best for:** Routes within LH Group airlines. Apply immediately; worth verifying the data granularity.

---

### SerpAPI Google Flights

**Strengths:**
- Immediate self-service access
- `price_history` field returns array of `[timestamp, price]` - directly enables PRECO ABAIXO HISTORICO
- 250 searches/month free; $25/month for 1,000
- Google Flights data is highly reliable for consumer price comparison

**Weaknesses:**
- Zero booking class data. No RBD codes. No seat counts.
- Price_history is pre-computed by Google, not your own historical store - limited to what Google exposes
- Rate limits are strict at free tier

**Best for:** PRECO ABAIXO HISTORICO and JANELA OTIMA signals. The best price-only API for individual developers.

---

### Kiwi Tequila API

**Strengths:**
- Free for Kiwi affiliate partners
- Returns a `seats` field (total available seats on itinerary)
- Good coverage including low-cost carriers

**Weaknesses:**
- `seats` is total itinerary capacity, NOT per booking class. Confirmed to be a single integer, not an array of class inventories.
- Affiliate program focus - may require traffic or booking volume commitments for sustained access

**Best for:** Quick availability checks and price searches. The `seats` field is useful as a loose urgency proxy (very low total seats = any cheap class likely closing) but not precise enough for BALDE detection.

---

### FlightAPI.io

**Strengths:**
- Simple REST API
- $49/month for 30,000 credits is cost-effective for 3-5 routes polled multiple times daily
- No booking/agency requirements

**Weaknesses:**
- Price tracking only. No booking class inventory confirmed.
- "Seat availability information" mentioned in marketing but not confirmed to mean RBD-level counts

**Best for:** Affordable price polling as an alternative or complement to SerpAPI when volume exceeds SerpAPI free tier.

---

## Recommendation

**Choose Amadeus (while keys last) for inventory signals + SerpAPI for price signals.**

This is the only combination that covers all four signals for an individual developer today. After July 17, 2026, BALDE signals have no accessible replacement for individual developers.

**Transition plan:**
1. Now: Verify Amadeus key status. If active, use it and capture all historical data you can.
2. Now: Implement price signals with SerpAPI. This works regardless.
3. Now: Apply for Lufthansa Open API fare plan. Test response granularity.
4. July 2026: If Lufthansa fare plan returns RBD counts, migrate inventory detection to it (LH Group routes only).
5. Post-July 2026 for non-LH routes: Accept that BALDE signals are not detectable without a GDS business relationship.

**Do not invest time in:**
- Duffel for inventory (confirmed: no RBD counts)
- OAG for inventory (confirmed: cabin-level only)
- AviationStack (flight tracking only, no prices)
- Sabre/Travelport for production (blocked without business entity)

---

## Sources

- Amadeus shutdown: https://www.phocuswire.com/amadeus-shut-down-self-service-apis-portal-developers
- Amadeus availabilityClasses description: https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/resources/flights/
- Duffel offers schema (no seat counts): https://duffel.com/docs/api/v2/offers
- Duffel pricing: https://duffel.com/pricing
- Lufthansa fare plan (rate limits confirmed; RBD depth unverified): https://developer.lufthansa.com/Fares_Availability
- Travelport booking class availability: https://support.travelport.com/webhelp/uapi/Content/Air/Air_Availability/Air%20Availability%20by%20Booking%20Class.htm
- Travelport seat count caveat (supplier-dependent): search result snippet from same URL
- OAG cabin-level data confirmed: https://www.oag.com/flight-data-seats
- SerpAPI price_history structure: https://serpapi.com/google-flights-price-insights
- SerpAPI pricing: https://serpapi.com/pricing
- Sabre agency certification requirement: https://www.altexsoft.com/blog/sabre-api-integration/
- Travelport annual cost estimate: https://traveltekpro.com/traveltekpro-com-blog-travelport-gds-api-pricing-guide-complete-cost-for-ota/
- GDS capped at 9 seats confirmed: https://blog.awardfares.com/flight-schedules/
