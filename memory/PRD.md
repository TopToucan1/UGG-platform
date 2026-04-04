# UGG - Universal Gaming Gateway | PRD — FINAL

## Architecture
- **Backend**: FastAPI + MongoDB — 35 route modules, 275+ API endpoints
- **Gateway Core**: 8-stage pipeline | **Adapters**: SAS/G2S/S2S/VCF
- **Frontend**: React 19 + Tailwind + Recharts + Mapbox GL + Framer Motion — 30 pages
- **AI**: Gemini 3 Flash | **Auth**: JWT RBAC (7+4 tier) | **Real-time**: WebSocket

## ALL PHASES COMPLETE (0-7) + Route Module Gaps Closed

### Route Module v2 Gaps (Closed):
- NOR Split Engine: 4-way split (Distributor + Operator + Retailer + State) with BigInt-precision math, retailer absorbs rounding, checksum validation
- Operator Entity: 6 operators (2 per distributor) with license numbers, revenue shares, expiry dates
- Revenue Shares: Per-device shares (dist/op/ret must sum to 1.0 ± 0.0001), DB constraint validated
- Statutory Periods: OPEN → CLOSED → SUBMITTED → ACCEPTED lifecycle with NOR totals, close/submit endpoints
- License Expiry: Tracking for distributors and operators with configurable days-to-expiry alerting
- New Exception Types: REVENUE_ANOMALY (NOR < 40% of 90-day avg), MAX_TERMINALS_EXCEEDED, EXCESSIVE_GAMEPLAY (>4hr sessions)
- NSF Handler: Automated processing — create CRITICAL exception, flag EFT entries, hold future payments
- Device Compliance: Per-device integrity history, exception count, NOR summary, twin state, revenue shares
- Route Map: 85 venues verified working with Mapbox GL, health-coded markers, $261K NOR, 85.9% online

## Total: 30 pages, 275+ endpoints, 35 backend modules
