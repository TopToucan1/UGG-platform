# UGG - Universal Gaming Gateway | PRD

## Architecture
- **Backend**: FastAPI + MongoDB — 24 route modules, 130+ API endpoints
- **Frontend**: React 19 + Tailwind + Recharts + Framer Motion — 19 pages, 9 Route Ops tabs
- **AI**: Gemini 3 Flash | **Auth**: JWT RBAC (7 roles + 4-tier route portal) | **Real-time**: WebSocket

## Complete Feature Set (All 8 Route Spec Modules Implemented)

### Core: Dashboard, Command Center, Devices (85), Connectors (DnD+canary), AI Studio (Gemini), Emulator Lab, Audit, Alerts, Messages, Settings
### Financial: 1200 txns, charts | Players: 120 sessions, tiers, leaderboard
### Marketplace: 12 connectors, 7 categories | Jackpots: 10 progressives ($1.27M)
### Export: 6 CSVs | VIP Alerts: Real-time WS | Content Lab: SWF Analyzer, Hex, Registry

### Route Operations Module (All 8 Spec Modules):
- **Module 1 — Offline Buffer**: Agent connectivity (ONLINE/DEGRADED/OFFLINE), pending events, 30-day auto-disable
- **Module 2 — SAS Meter Map**: 13-meter SAS→G2S→canonical mapping
- **Module 3 — Integrity**: 121 checks, 98.3% pass rate, SCHEDULED/REBOOT/RECONNECT/OPERATOR triggers
- **Module 4 — Statutory Fields**: 8 mandatory fields, batch enrichment, county breakdown, enrichment coverage tracking
- **Module 5 — NOR/EFT**: $7.99M NOR, 3 distributors, NACHA ACH generation with compliance validation (6 structural checks)
- **Module 6 — Exceptions**: 10 exception types, severity-coded, resolve workflow
- **Module 7 — RBAC Portal**: 4-tier (state_regulator→distributor_admin→retailer_viewer→manufacturer_viewer), permission matrix, 5 seeded users
- **Module 8 — Performance**: Scale projections (9,956 devices/17.44B events/yr), query benchmarks, collection sizes, index management

## Testing: Backend 100%, Frontend 95%+
## Total: 19 pages (9 Route tabs), 130+ endpoints, 24 backend modules
