# UGG - Universal Gaming Gateway | PRD

## Original Problem Statement
Build the complete Universal Gaming Gateway (UGG) platform from a comprehensive 17-part master design document. UGG is a protocol-agnostic gaming device interoperability platform with six-layer architecture, supporting SAS, G2S, and vendor protocols.

## Architecture
- **Backend**: FastAPI (Python) with MongoDB via Motor
- **Frontend**: React 19 + Tailwind CSS + Radix UI + Phosphor Icons
- **AI Integration**: Gemini 3 Flash via Emergent Integrations library
- **Auth**: JWT cookie-based with RBAC (admin/operator/engineer)
- **Real-time**: WebSocket support for event streaming

## User Personas
1. **Ops Lead** - Estate Dashboard, Alert Console
2. **Operator** - Device Management, Message Composer
3. **Integration Engineer** - Connector Builder, AI Studio
4. **QA Engineer** - Emulator Lab
5. **Security/Audit** - Audit Explorer

## Core Requirements
- Multi-tenant RBAC authentication
- Device registry with 85+ seeded gaming machines
- Canonical event model (500+ events seeded)
- Command lifecycle management
- Connector framework with manifest approval
- AI-assisted discovery and mapping via Gemini
- Emulator lab with scenario execution
- Immutable audit trail
- Alert management with acknowledge/resolve
- Message campaign system

## What's Been Implemented (April 2, 2026)

### Backend (14 route modules)
- Auth system (JWT, RBAC, brute force protection)
- Dashboard aggregation endpoints
- Device CRUD with capabilities, events, commands, meters, audit
- Events listing with filtering
- Commands lifecycle
- Connectors & manifests management with approval workflow
- Audit trail with filtering
- Alert management (acknowledge/resolve)
- Emulator Lab (6 scenarios, virtual devices, trace events, assertions)
- AI Studio (Gemini 3 Flash - chat, discovery, mapping, connector generation)
- Message campaigns (create, send)
- Admin (tenants, sites, users, agents, stats)
- Comprehensive seed data (85 devices, 500 events, 50 commands, 40 alerts, 100 audit records)

### Frontend (10 pages)
1. Login Page - dark themed with UGG branding
2. Estate Dashboard - summary cards, device health map, live event feed, alert ticker
3. Device Management - three-column layout, filters, detail drawer with 5 tabs
4. Connector Builder - three-pane workspace (evidence, mapping canvas, validation)
5. AI Studio - chat, discovery, connector generation modes
6. Emulator Lab - scenario selector, virtual devices, trace stream, assertions
7. Audit Explorer - filterable audit records table
8. Alert Console - severity-coded alerts with acknowledge/resolve
9. Message Composer - campaign creation and sending
10. Settings - platform stats, tenants, sites, users, agents

### Design System
- Dark theme (#0A0C10, #12151C, #1A1E2A)
- Teal accent (#00D4AA)
- Chivo headings, IBM Plex Sans body, JetBrains Mono for data
- 240px collapsible sidebar, 480px detail drawer
- Status colors (online/warning/error/info)

## Prioritized Backlog

### P0 (Next Sprint)
- WebSocket real-time event streaming to dashboard
- Drag-and-drop field mapping in Connector Builder
- Device command execution with real protocol simulation

### P1
- Multi-tenant data isolation
- User management UI with role editing
- Connector version management
- Emulator fault injection controls

### P2
- Financial events dashboard (wager, payout, voucher tracking)
- Player session tracking
- Progressive jackpot monitoring
- Export/reporting functionality
- API key management UI

## Next Tasks
1. Add WebSocket real-time event push to dashboard
2. Implement drag-and-drop mapping in connector builder
3. Add charts/graphs to dashboard (Recharts)
4. Build connector deployment workflow
5. Add bulk device operations
