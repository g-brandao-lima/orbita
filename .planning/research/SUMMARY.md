# Research Summary: Flight Monitor - Booking Class Inventory APIs

**Domain:** Flight price prediction / booking class inventory monitoring
**Researched:** 2026-03-25
**Overall confidence:** MEDIUM

---

## Executive Summary

The flight-monitor project depends on detecting booking class inventory signals (BALDE FECHANDO, BALDE REABERTO) that require per-fare-class seat counts such as "Y7 B4 M3 K1 Q0". This level of data granularity lives inside airline reservation systems (CRS) and Global Distribution Systems (GDS). Consumer-facing aggregator APIs (Skyscanner, Google Flights via SerpAPI, Kiwi Tequila, FlightAPI.io, AviationStack) do not expose this layer at all - they return a single price point per itinerary, not per-class seat inventories.

The Amadeus self-service API was the ideal tool for this project because it uniquely exposed `availabilityClasses` with RBD codes and seat counts capped at 9. This portal is now shutting down: registration for new users paused in March 2026, and full decommission is July 17, 2026. Existing keys will be disabled on that date. This is the single most critical finding of this research.

Among the remaining realistic candidates: Duffel exposes `fare_basis_code` and `cabin_class` but NOT per-class seat counts - it is an NDC booking API, not an inventory polling API. Sabre and Travelport have the inventory data technically, but both require formal business onboarding (travel agency affiliation or IATA certification), minimum annual commitments, and go-live certification processes that block individual developer access in practice. Lufthansa Open API offers a free fares/availability plan for developers but the granularity of the availability data (whether RBD seat counts are exposed) is unclear and requires a use-case application for the fare tier.

The PRECO ABAIXO HISTORICO and JANELA OTIMA signals are fully achievable with price-only APIs today. The inventory signals require either a GDS relationship or creative reverse-engineering through existing Amadeus keys (if the project already has one) before the July 2026 cutoff.

---

## Key Findings

**Stack:** Python + SQLite + APScheduler is appropriate for polling; the bottleneck is data access, not code.
**Architecture:** Hybrid approach is the only realistic path - price signals (SerpAPI/Tequila) + inventory signals (Amadeus Enterprise or Lufthansa Open API with fare plan, if attainable).
**Critical pitfall:** Amadeus self-service (the only accessible API with `availabilityClasses`) is shutting down July 17, 2026. New registration closed March 2026.

---

## Implications for Roadmap

Based on research, suggested phase structure:

1. **Phase: Stabilize price-only signals now** - These work today with zero blockers.
   - Addresses: PRECO ABAIXO HISTORICO, JANELA OTIMA
   - Uses: SerpAPI Google Flights (free: 250/month, $25/month for 1,000) or FlightAPI.io ($49/month for 30k credits)
   - Avoids: Dependency on closing API access

2. **Phase: Extend Amadeus usage before cutoff** - If the project already has Amadeus self-service keys, maximize their use before July 17, 2026.
   - Addresses: BALDE FECHANDO, BALDE REABERTO
   - Risk: Access ends regardless of usage. Design data storage to persist historical inventory snapshots.

3. **Phase: Evaluate Lufthansa Open API fare tier** - Free but requires application approval for the fares/availability endpoint.
   - Addresses: Partial inventory data for Lufthansa Group airlines only (LH, LX, OS, SN, EN)
   - Rate limit: 6 calls/second, 1,000 calls/hour
   - Gap: Coverage is airline-specific, not universal

4. **Phase: Evaluate Sabre/Travelport as a long-term path** - Only viable if the project formalizes into a business entity.
   - Sabre Dev Studio: sandbox is free; production requires agency certification
   - Travelport: 30-day sandbox trial; production requires minimum booking volume commitment

**Phase ordering rationale:**
- Price signals first because they require no blocking dependency and deliver immediate user value
- Inventory signals second because they have a hard deadline (July 2026 for Amadeus) and uncertain alternatives
- GDS path last because it requires structural prerequisites (business entity, IATA number) outside developer control

**Research flags for phases:**
- Phase 2 (Amadeus inventory): Verify immediately whether the project already holds active self-service keys. If not, access is permanently blocked as of March 2026.
- Phase 3 (Lufthansa): Apply for the fare/availability plan promptly; approval is not guaranteed and the data coverage is LH Group only.
- Phase 4 (GDS): Needs deeper business/legal research, not just technical research.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Amadeus shutdown | HIGH | Confirmed by PhocusWire, official Amadeus communications, multiple sources |
| Duffel (no RBD counts) | MEDIUM | Docs confirmed fare_basis_code exists, no seat count field found in docs |
| SerpAPI pricing | HIGH | Directly fetched from serpapi.com/pricing |
| Sabre/Travelport access barriers | MEDIUM | Multiple sources confirm business requirements; exact cost is opaque |
| Lufthansa Open API | MEDIUM | Confirmed free plans exist, fare tier requires application; RBD depth unverified |
| Travelport returns booking class codes | MEDIUM | Docs confirm BookingCodeInfo field; seat counts depend on supplier support |
| Kiwi/Skyscanner/AviationStack = price-only | HIGH | Confirmed by multiple independent sources |

---

## Gaps to Address

- Whether the project currently has active Amadeus self-service credentials (this determines everything)
- Exact fields returned by Lufthansa fare/availability endpoint (requires applying for the plan)
- Whether Travelport's `BookingCodeInfo` in `AirAvailabilitySearchRsp` includes actual seat counts or only presence/absence
- OAG pricing for developers (not publicly disclosed; requires contacting sales)
- Whether any NDC aggregator (AirGateway, Verteil) exposes inventory counts to non-agency developers
