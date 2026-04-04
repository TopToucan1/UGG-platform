# UGG - Universal Gaming Gateway | PRD

## Architecture
- **Backend**: FastAPI + MongoDB — 31 route modules, 220+ API endpoints
- **Gateway Core**: 8-stage event pipeline | **Adapters**: SAS Live/G2S Live/S2S/VCF
- **Frontend**: React 19 + Tailwind + Recharts + Mapbox GL + Framer Motion — 23 pages
- **AI**: Gemini 3 Flash | **Auth**: JWT RBAC (7+4 tier) | **Real-time**: WebSocket

## Phase 5 Analysis + Testing Tools — Complete

### 1. Advanced Transcript Analyzer (ATA)
- 6 compliance rules (EVT_SUB_001, EVT_RPT_001, STATE_001, COMMS_001, METER_001, HANDPAY_001)
- 3 categories: EVENT_SUBSCRIPTION, EVENT_REPORT, STATE_TRANSITION
- Comms Session grouping, violation tree, GREEN/YELLOW/RED per-session
- Rule evaluation against live transcripts

### 2. Proxy Mode (Transparent MITM)
- SOAP interceptor pipeline: raw→SOAP→G2S→validate→filter→forward
- 3-channel capture (PROTOCOL_TRACE, SOAP, G2S)
- Disruptive filters: DROP/DELAY/CORRUPT/DUPLICATE
- Schema validation, filter matching, message statistics

### 3. Fleet Simulator (200-slot)
- Up to 200 simultaneous SmartEGM instances
- 9 engine status states (Engine Stopped→Loading→Starting→Running→Scripts Starting/Running/Stopping→Engine Stopping)
- Per-slot Device Template + script assignment
- Fleet metrics: messages sent/recv, avg response time, error counts
- Staggered startup, engine/script lifecycle management

### 4. Compliance Reference (Public Knowledge Base)
- 6 rules with full metadata: why_it_matters, protocol_ref, expected_behavior, violation_example, fix_guidance
- Public API (no auth): list, detail, filter by class/category, full-text search
- Links from Analyzer violations to compliance rule detail

### 5. Certificate Digital Signatures
- HMAC-SHA256 signing with UGG private key
- Public verification endpoint (no auth): /api/certificates/{id}/verify
- Expiry enforcement (410 Gone for expired certificates)
- Certificate metadata: tier, device, manufacturer, pass rate, issued/valid dates

## Total: 23 pages, 220+ endpoints, 31 backend modules
