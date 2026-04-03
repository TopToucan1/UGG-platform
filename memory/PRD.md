# UGG - Universal Gaming Gateway | PRD

## Architecture
- **Backend**: FastAPI + MongoDB — 23 route modules, 120+ API endpoints
- **Frontend**: React 19 + Tailwind + Recharts + Framer Motion — 19 pages
- **AI**: Gemini 3 Flash | **Auth**: JWT RBAC | **Real-time**: WebSocket

## Complete Feature Set

### Core Platform: Dashboard, Command Center, Device Management (85 devices), Connector Builder (DnD + canary), AI Studio (Gemini), Emulator Lab, Audit Explorer, Alert Console, Messages, Settings
### Financial: 1200 transactions, hourly revenue, by-site/game charts, transaction ledger
### Players: 120 sessions, 50 players, tier system, leaderboard, session detail
### Marketplace: 12 connectors, 7 categories, certified/verified, install tracking
### Jackpots: 10 progressives ($1.27M), 115 hit history, charts
### Export: 6 CSV downloads | VIP Alerts: Real-time WebSocket for Platinum/Diamond
### Content Lab: SWF Analyzer, Binary Inspector, EGM Content Registry

### Route Operations Module (NEW - from Programming Spec v1.0):
- **Overview**: 8 KPI cards, 30-day NOR trend chart, Exception Breakdown (10 types), NOR by Distributor table
- **NOR Accounting**: Daily NOR/Coin In/Tax trend, 3 distributors, 85 devices, 2550 NOR periods
- **Monitoring Exceptions**: 10 exception types (DEVICE_OFFLINE, INTEGRITY_VIOLATION, ZERO_PLAY_TODAY, NSF_ALERT, etc.), severity-coded, resolve workflow
- **Software Integrity**: 121 checks, 98.3% pass rate, SCHEDULED/REBOOT/RECONNECT/OPERATOR triggers, audit table
- **Offline Buffer**: Agent connectivity states (ONLINE/DEGRADED/OFFLINE), pending event counts
- **EFT Generation**: NACHA ACH file generation, WEEKLY/MANUAL sweeps, transmission status audit
- **SAS Meter Map**: 13-meter constant table (SAS code → G2S class → UGG canonical)
- **Data**: 3 distributors, 85 retailers, $108M coin in, $7.99M NOR, $558K tax (30-day)

## Testing: Backend 100%, Frontend 95%
## Total: 19 pages, 120+ endpoints, 23 backend modules
