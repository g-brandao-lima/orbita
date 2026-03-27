# Domain Pitfalls

**Domain:** Flight price prediction / booking class inventory APIs
**Researched:** 2026-03-25

---

## Critical Pitfalls

### Pitfall 1: Amadeus self-service is permanently closing and new registration is already blocked

**What goes wrong:** The project was built around Amadeus `Flight Availabilities Search` because it uniquely exposed `availabilityClasses` with RBD codes (Y, B, M, K, Q) and seat counts. New user registration for the self-service portal was paused in March 2026. Full decommission is July 17, 2026 - all API keys disabled, portal inaccessible.

**Why it happens:** Amadeus did not disclose the reason. They are pushing developers toward their Enterprise API (requires formal travel industry partnership, IATA number, contract).

**Consequences:** If the project does not already hold active self-service keys, the BALDE FECHANDO and BALDE REABERTO signals have no data source. These two signals cannot be detected with any other currently accessible API for individual developers.

**Prevention:**
- Check immediately whether the project has active Amadeus self-service credentials.
- If yes: maximize data collection before July 17, 2026. Store all inventory snapshots you capture.
- If no: registration is closed. The inventory signals require a different strategy.

**Detection:** Try hitting the Amadeus developer portal at developers.amadeus.com. If registration is disabled, you will see confirmation of the pause.

---

### Pitfall 2: Assuming aggregator APIs (Duffel, Kiwi, Skyscanner) expose fare class inventory

**What goes wrong:** These APIs surface price data, not GDS inventory. Duffel returns `fare_basis_code` (a fare rule identifier like "OXZ0RO") and `cabin_class` (economy/business), but zero information about how many seats remain in class K vs class Q. Kiwi Tequila returns a `seats` integer that is the total available seats on the full itinerary - not broken down by RBD.

**Why it happens:** Aggregators act as booking intermediaries. They query airline systems and return the best price for the requested cabin. They do not expose the underlying inventory matrix to consumers.

**Consequences:** Building BALDE detection on top of Duffel or Kiwi will appear to work in development (fields are present) but the data is categorically different from what the signal requires.

**Prevention:** Only accept inventory data if the API explicitly returns a structure analogous to `[{bookingCode: "K", numberOfBookableSeats: 2}, {bookingCode: "Q", numberOfBookableSeats: 0}]`. If a field named `seats` returns a single number, it is not RBD inventory.

**Detection:** Read the exact schema. A single integer for seats = total capacity, not per-class inventory.

---

### Pitfall 3: GDS APIs require travel agency affiliation - not just a credit card

**What goes wrong:** Sabre and Travelport have the inventory data at full granularity. Sabre's Dev Studio sandbox is technically free and accessible. But sandbox access is specifically for testing/certification, and production requires: business entity with IATA or ARC accreditation, contract negotiation, volume commitments ($5,000+/year estimated), and a go-live certification process (Travelport requires 15 business days minimum).

**Why it happens:** GDS systems are designed for travel agencies, not individual developers. Their business model depends on booking commissions and segment fees, not API access fees.

**Consequences:** An individual developer cannot realistically move a Sabre or Travelport integration to production without forming a travel business.

**Prevention:** Do not invest engineering time in Sabre or Travelport integrations unless the project is being commercialized and a business structure is in place.

**Detection:** Sabre Dev Studio sandbox access is possible; the blocker appears only when attempting to go live.

---

## Moderate Pitfalls

### Pitfall 4: OAG Seats data is cabin-level, not RBD-level

**What goes wrong:** OAG markets "flight seats data" prominently. The product delivers seat capacity broken down by cabin (First, Business, Premium Economy, Economy+, Economy). This is capacity planning data for airlines, not real-time fare class inventory for monitoring.

**Prevention:** Do not confuse cabin seat counts with booking class (RBD) seat counts. They are fundamentally different data products. OAG serves the former; GDS systems serve the latter.

---

### Pitfall 5: Lufthansa Open API fare plan data granularity is unverified

**What goes wrong:** Lufthansa offers a free "fares/availability" tier that requires submitting a use case description. The landing page says "we offer fare/availability data together with deep link information" but does not specify whether RBD seat counts are returned or just fare prices and availability flags (available/not available).

**Prevention:**
- Apply for the fare plan immediately.
- In the use case description, explicitly ask whether the API returns per-class seat counts (RBD inventory) or only a binary availability flag.
- Do not assume this solves the inventory problem until you have tested a real response.
- Coverage is limited to LH Group airlines: Lufthansa, Swiss, Austrian, Brussels Airlines, Eurowings.

**Detection:** Apply and test. Rate limits (6/second, 1,000/hour) are known; data granularity is not confirmed.

---

### Pitfall 6: SerpAPI price_history is not real-time inventory

**What goes wrong:** SerpAPI Google Flights Price Insights returns a `price_history` array of `[timestamp, price]` pairs. This is useful for PRECO ABAIXO HISTORICO. It is sometimes confused with availability data because prices drop when inventory opens.

**Prevention:** Use `price_history` only for price trend signals (PRECO ABAIXO HISTORICO, JANELA OTIMA). Never use it to infer inventory state. A price drop does not confirm a specific fare class opened.

---

## Minor Pitfalls

### Pitfall 7: Travelport BookingCodeInfo may not include seat counts from all suppliers

**What goes wrong:** Travelport's Universal API documentation states: "The number of available seats is not supported by all ACH suppliers. If the number of available seats is returned by the supplier, Universal API returns the supplier's number. If not returned by the supplier, Universal API bases the number of available seats on the number of passengers specified in the request."

**Prevention:** Even if Travelport access is obtained, validate that the specific airlines you monitor actually return seat count data, not just a derived estimate.

---

### Pitfall 8: Free tier rate limits make real-time monitoring impossible

**What goes wrong:** SerpAPI free tier is 250 searches/month. That is 8 searches/day. For 5 routes polled every 4 hours (6x/day), you need 30 searches/day - exceeding the free limit immediately.

**Prevention:** Plan the polling frequency against your API budget before building the scheduler. For price signals:
- SerpAPI $25/month: 1,000 searches/month = ~33/day = 5 routes at 1x every 4 hours
- FlightAPI.io $49/month: 30,000 credits = much more headroom

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Implementing inventory signals | Assuming Amadeus keys exist and are still valid | Verify key status first; build price-only path as fallback |
| Replacing Amadeus after July 2026 | No direct equivalent exists for individual developers | Design inventory source as pluggable; degrade gracefully |
| Evaluating Lufthansa API | Assuming it returns RBD counts | Apply for plan and test; confirm granularity before building |
| SerpAPI integration | Exceeding free tier rate limits | Calculate routes x polls x 30 days; upgrade plan proactively |
| Signal logic for BALDE | Single reading is ambiguous | Require 2 consecutive readings confirming the count drop to fire alert |

---

## Sources

- Amadeus shutdown date and registration pause: https://tragento.com/en/amadeus-announced-the-shutdown-of-the-self-service-api-portal-for-developers/
- Duffel fare_basis_code (not inventory): https://duffel.com/docs/api/v2/offers
- Travelport seat count caveats: https://support.travelport.com/webhelp/uapi/Content/Air/Air_Availability/Air%20Availability%20by%20Booking%20Class.htm (search result snippet)
- OAG cabin-level only: https://www.oag.com/flight-data-seats
- Lufthansa fare plan (granularity unverified): https://developer.lufthansa.com/Fares_Availability
- Sabre business requirements: https://www.altexsoft.com/blog/sabre-api-integration/
- Travelport annual fee estimate: https://traveltekpro.com/traveltekpro-com-blog-travelport-gds-api-pricing-guide-complete-cost-for-ota/
- SerpAPI free tier: https://serpapi.com/pricing
