"""
UGG Documentation Library — Knowledge base for the entire platform.
Every page, feature, and workflow documented with guides, tutorials, and references.
"""
from fastapi import APIRouter, Request
from auth import get_current_user

router = APIRouter(prefix="/api/docs", tags=["docs"])

DOC_SECTIONS = [
    {"id": "getting-started", "title": "Getting Started", "icon": "Rocket", "docs": [
        {"id": "gs-overview", "title": "Platform Overview", "content": "The Universal Gaming Gateway (UGG) is a protocol-agnostic gaming device interoperability platform. It connects electronic gaming machines (EGMs) from any manufacturer, speaking any protocol (SAS, G2S, proprietary), to a unified central monitoring and management system.\n\n**Core Architecture:**\n- **Gateway Core**: 8-stage event processing pipeline (validate → enrich → store → twin → exception → meter → broadcast → audit)\n- **Protocol Adapters**: SAS RS-232, G2S SOAP/HTTP, S2S System-to-System, Vendor Connector Framework\n- **Digital Twin**: Real-time device state projections for every device in the estate\n- **Route Operations**: NOR accounting, exception monitoring, integrity checks, EFT/NACHA generation\n\n**Key Metrics:**\n- 28 pages across operations, analytics, testing, and administration\n- 240+ API endpoints covering every aspect of gaming operations\n- Real-time WebSocket event streaming with VIP player alerts\n- AI-powered analytics via Gemini 3 Flash"},
        {"id": "gs-login", "title": "Logging In", "content": "Navigate to your UGG instance URL. Enter your email and password.\n\n**Default Admin:** admin@ugg.io\n\n**4-Tier Route Portal Roles:**\n1. **State Regulator** (Tier 1) — Full estate view, all distributors, tax data, integrity reports\n2. **Distributor Admin** (Tier 2) — Own route only, device management, NOR, EFT\n3. **Retailer Viewer** (Tier 3) — Own venue only, read-only device status and NOR\n4. **Manufacturer Viewer** (Tier 4) — Own device models only, integrity and certification data"},
        {"id": "gs-navigation", "title": "Navigation Guide", "content": "The sidebar contains 26 navigation items organized by function:\n\n**Operations:** Mission Control, Command Center, Device Fleet, Route Map\n**Route Management:** Route Operations (9 tabs), Regulatory Dashboard\n**Financial:** Financial Dashboard, Player Sessions, Jackpots\n**Engineering:** Connectors, Marketplace, Content Lab, AI Studio\n**Testing:** Emulator Lab, Analyzer, Proxy Mode, Fleet Simulator, Certification\n**Reference:** Compliance Reference, AI Analytics, Digital Twin\n**Admin:** Audit Explorer, Exceptions, Messages, Export, Settings\n\nThe sidebar is collapsible — click the arrow at the bottom to minimize to icons only."},
    ]},
    {"id": "operations", "title": "Operations", "icon": "ChartBar", "docs": [
        {"id": "ops-dashboard", "title": "Mission Control Dashboard", "content": "The main operational dashboard showing estate health at a glance.\n\n**Summary Cards:** Total Devices, Active Alerts, Command Queue, Event Throughput\n**Device Health Map:** Color-coded grid of all devices — green (online), red (offline/error), amber (maintenance)\n**Live Event Feed:** Real-time WebSocket events streaming as they occur\n**Alert Ticker:** Scrolling marquee of active alerts\n**Charts:** Event Volume (24h), Protocol Mix pie, Severity & Status bar charts\n\n**Auto-refresh:** Data updates every 15 seconds. WebSocket events appear instantly."},
        {"id": "ops-command-center", "title": "Command Center", "content": "Full-screen war room display optimized for large monitors in operations centers.\n\n**Layout:** 6-zone grid with KPI strip, device map, event chart, live feed, jackpots, VIP alerts, active sessions, alert ticker.\n**Access:** Click 'Command Center' in sidebar or use the fullscreen toggle.\n**Exit:** Click the 'Exit' arrow in the top-left to return to the regular dashboard.\n\n**Tip:** The Command Center has its own WebSocket connection — it updates independently of the main dashboard."},
        {"id": "ops-devices", "title": "Device Fleet Management", "content": "Comprehensive device management with filtering, sorting, and detail views.\n\n**Filters:** Status, Protocol, Manufacturer, Search (by device ID, serial, model)\n**Device List:** Sortable columns — Status, Device Ref, Manufacturer, Model, Protocol, Last Seen\n**Detail Drawer:** Click any device to open the 480px detail panel with 5 tabs:\n- **Overview:** Status, serial, firmware, game title, denomination, capabilities, latest meters\n- **Events:** Recent events for this device with severity badges\n- **Commands:** Command history with status (completed/pending/failed)\n- **Connector:** Protocol and connector information\n- **Audit:** Audit trail entries related to this device\n\n**Commands:** Disable, Enable, Send Message buttons directly from the detail drawer."},
        {"id": "ops-route-map", "title": "Route Map", "content": "Geographic visualization of all venues using Mapbox GL JS.\n\n**Map Styles:** Dark (default), Satellite, Streets — toggle in the top-left corner\n**Venue Markers:** Color-coded by health — green (>95%), amber (80-95%), red (<80%). Size proportional to device count.\n**Venue List:** Left sidebar with searchable venue list showing device count, health %, NOR, exception count.\n**Venue Detail:** Click a marker or list item — map flies to venue, detail panel shows devices, exceptions, NOR, and 'View Venue Devices' drill-down.\n\n**Tip:** Hover over markers for popup tooltips with venue name, city, county, and key metrics."},
    ]},
    {"id": "route-ops", "title": "Route Operations", "icon": "MapPin", "docs": [
        {"id": "ro-overview", "title": "Route Operations Overview", "content": "The Route Operations page has 9 tabs covering all aspects of amusement route management:\n\n1. **Overview** — 8 KPI cards, NOR trend chart, exception breakdown, NOR by distributor table\n2. **NOR Accounting** — Daily NOR/Coin In/Tax trend with distributor filtering\n3. **Exceptions** — 10 exception types with severity-coded cards and resolve workflow\n4. **Integrity** — Software integrity checks with pass/fail/no-image results\n5. **Statutory** — 8 mandatory statutory fields, enrichment coverage, county breakdown\n6. **RBAC Portal** — 4-tier permission matrix with user management\n7. **Offline Buffer** — Agent connectivity states and pending event counts\n8. **EFT/NACHA** — NACHA ACH file generation with compliance validation\n9. **Performance** — Database benchmarks, scale projections, index management"},
        {"id": "ro-nor", "title": "NOR Accounting", "content": "Net Operating Revenue tracking per device, per distributor, per day.\n\n**Formula:** NOR = Coin In - Coin Out - Handpays - Voucher Out\n**Tax:** Calculated per distributor at their configured tax_rate_bps (basis points)\n**Trend:** 30-day daily chart showing NOR, Coin In, and Tax lines\n**By Distributor:** Table with Coin In, Coin Out, NOR, Tax, Devices, Hold%\n\n**Filtering:** Use the distributor dropdown to filter all tabs to a single route operator."},
        {"id": "ro-nacha", "title": "EFT & NACHA Compliance", "content": "Generate NACHA-compliant ACH files for electronic funds transfer.\n\n**File Structure:** File Header (1) → Batch Header (5) per distributor → Entry Detail (6) → Batch Control (8) → File Control (9) → Padding to blocking factor 10\n**Validation:** 6 structural checks — File Header, File Control, Record Length (94 chars), Blocking Factor, Batch Pairs, Entry Details\n**Generate:** Click 'Generate NACHA-Compliant' for a validated file, or 'Quick Sweep' for a basic EFT file.\n\n**All records are exactly 94 characters per the NACHA specification.**"},
    ]},
    {"id": "testing", "title": "Testing & Certification", "icon": "Flask", "docs": [
        {"id": "test-emulator", "title": "Emulator Lab", "content": "The most complex screen in UGG — a complete engineering workbench with 7 tabs:\n\n**Script Runner:** Load and execute pre-built or custom test scripts. 19 verbs including player-verb, wait-for-events, balanced-meters-analysis.\n**SmartEGM:** 12 player verbs (INSERT_BILL, PUSH_PLAY, CASH_OUT, etc.) with state machine and win probability distribution.\n**Live G2S:** Connect to real EGM SOAP endpoints. Full startup sequence. Command builder. Session recording & replay.\n**Templates:** Parse Device Template XML files defining EGM capabilities, denominations, classes, win levels.\n**TAR Report:** 7-section Transcript Analysis Report with RED/YELLOW/GREEN flagging.\n**Watchables:** XPath expression engine with 7 pre-built patterns for real-time message matching.\n**Transcripts:** Paginated transcript viewer with XML syntax highlighting, Find/Match Case, channel filtering."},
        {"id": "test-certification", "title": "Certification Suite", "content": "Automated 14-class G2S compliance testing with 4 tiers:\n\n**Bronze:** 6 classes (cabinet, communications, eventHandler, gamePlay, meters, handpay) — minimum for route deployment\n**Silver:** 10 classes (Bronze + bonus, commandHandler, download, GAT) — casino floor deployment\n**Gold:** 12 classes (Silver + noteAcceptor, optionConfig) — full casino with remote config\n**Platinum:** 14 classes (all) — highest tier with progressive and cashless\n\n**Process:** Select device → Select tier → Run All Tests → View accordion results → Download signed PDF certificate\n**Certificate:** Digitally signed with HMAC-SHA256. Public verification URL valid for 1 year."},
        {"id": "test-analyzer", "title": "Advanced Analyzer", "content": "Post-session compliance analysis using a rule engine.\n\n**6 Compliance Rules:**\n- EVT_SUB_001: Event Subscription Accuracy\n- EVT_RPT_001: Event Report Completeness\n- STATE_001: State Transition Consistency\n- COMMS_001: commsOnLine Sequence Integrity\n- METER_001: Meter Monotonicity\n- HANDPAY_001: Handpay Sequence Completeness\n\n**Per-session analysis:** Each Comms Session gets GREEN (no violations), YELLOW (warnings only), or RED (errors found) status."},
        {"id": "test-proxy", "title": "Proxy Mode", "content": "Transparent man-in-the-middle for validating live floor traffic.\n\n**Pipeline:** Raw capture → SOAP parse → G2S parse → Schema validate → Apply filters → Forward\n**Disruptive Filters:** DROP, DELAY, CORRUPT, DUPLICATE — configurable by command class, name, direction, pattern\n**3 Channels:** All messages captured in PROTOCOL_TRACE, SOAP, and G2S transcript channels simultaneously\n\n**Use Case:** 'Ground truth' testing — captures real EGM↔Host traffic, not simulation."},
        {"id": "test-fleet", "title": "Fleet Simulator", "content": "Load testing with up to 200 simultaneous SmartEGM instances.\n\n**9 Engine States:** Engine Stopped → Loading → Starting → Running → Scripts Starting → Scripts Running → Scripts Stopping → Engine Stopping → Status Unknown\n**Per-slot config:** Each of the 200 slots can have its own Device Template and test script\n**Metrics:** Messages sent/received, average response time, error count\n\n**Use Case:** Stress-test CMS before go-live by simulating the full production device count."},
    ]},
    {"id": "ai-tools", "title": "AI & Analytics", "icon": "Sparkle", "docs": [
        {"id": "ai-studio", "title": "AI Studio", "content": "Gemini 3 Flash powered assistant for connector development.\n\n**3 Modes:**\n- **Chat:** Conversational AI for protocol questions, mapping help, debugging\n- **Discovery:** Analyze source system data and auto-suggest canonical event mappings\n- **Generate:** AI-generated connector manifests with code skeletons and test scenarios"},
        {"id": "ai-analytics", "title": "AI Analytics", "content": "AI-powered operational intelligence using live estate data.\n\n**4 Analysis Types:**\n- **Predictive Maintenance:** Failure probability estimates, pattern clusters, maintenance priorities, root causes, revenue impact\n- **NOR Forecast:** 7-day and 30-day revenue predictions with confidence intervals, growth analysis, optimization recommendations\n- **Exception Patterns:** Cluster analysis, correlations, repeat offenders, resolution time patterns, prevention recommendations\n- **Natural Language Query:** Ask any question about your estate in plain English\n\n**All analyses use live data** — device counts, NOR trends, exceptions, and digital twin health scores are gathered in real-time and passed to Gemini."},
    ]},
    {"id": "hardware", "title": "Hardware & Deployment", "icon": "Cpu", "docs": [
        {"id": "hw-agent", "title": "UGG Agent", "content": "The UGG Agent is a Node.js process running on embedded Linux at each venue.\n\n**Hardware:** Raspberry Pi 4 (4GB RAM), 32GB industrial-grade SD card\n**Components:** DeviceManager (10 devices), SyncEngine (5-state machine), IntegrityEngine, NetworkManager, Local API (port 3100)\n**Offline Buffer:** 30-day SQLite buffer — never loses data. Auto-disable after 30 days per regulatory requirement.\n\n**Provisioning:** Generate a provisioning ZIP from the portal → copy to /boot/ugg-provision.zip → boot the agent. It auto-configures, installs certs, registers with central."},
        {"id": "hw-integration", "title": "Integration Testing", "content": "18 hardware integration tests across 5 categories:\n\n**SAS Serial (5 tests):** RS-232 connection, 38-meter poll, exception cycles, multi-address discovery, ROM signature\n**G2S SOAP (5 tests):** SOAP endpoint, startup sequence, keepAlive stability, event subscription, meter reads\n**Network (3 tests):** Cellular connectivity, failover switch, mTLS handshake\n**Offline Buffer (3 tests):** Write performance, sync replay, 30-day auto-disable\n**Integration (2 tests):** End-to-end flow (<5s latency), 24-hour soak test\n\nRun tests from Hardware → Integration Tests. Results include metrics (CRC errors, RTT, packet loss, etc.)"},
        {"id": "hw-library", "title": "Library & Downloads", "content": "Central repository for firmware, configurations, and provisioning packages.\n\n**Package Types:** Agent Image, Firmware, Config, Provisioning, Script\n**Default Packages:** UGG Agent v1.2.0, SAS Adapter Firmware, G2S Certificate Bundle, Route NV Config, Emulator Scripts, Fleet Templates, Integrity Seeds\n\n**Provisioning Generator:** Settings → Hardware → Generate Provisioning — creates a complete ZIP with agent-config.json, mTLS certificates, auth PINs, and README."},
    ]},
    {"id": "admin", "title": "Administration", "icon": "GearSix", "docs": [
        {"id": "admin-export", "title": "Export & Reports", "content": "6 one-click CSV downloads:\n- Financial Transactions (with type filter)\n- Player Sessions (with status filter)\n- Device Inventory\n- Canonical Events (with severity filter)\n- Audit Trail\n- Progressive Jackpots\n\nAll files generated in real-time from live MongoDB data. Maximum 5,000 records per export."},
        {"id": "admin-rbac", "title": "Role-Based Access Control", "content": "7 platform roles + 4-tier route portal:\n\n**Platform:** admin, operator, engineer\n**Route Portal:** state_regulator (Tier 1), distributor_admin (Tier 2), retailer_viewer (Tier 3), manufacturer_viewer (Tier 4)\n\nEach tier has specific permissions — view revenue, view devices, view integrity, view EFT, enable/disable devices, create announcements, view player data.\n\nManage users in Route Operations → RBAC Portal tab."},
    ]},
]


@router.get("")
async def list_doc_sections():
    """Public — list all documentation sections."""
    return {"sections": [{"id": s["id"], "title": s["title"], "icon": s["icon"], "doc_count": len(s["docs"])} for s in DOC_SECTIONS]}


@router.get("/section/{section_id}")
async def get_doc_section(section_id: str):
    """Public — get all docs in a section."""
    section = next((s for s in DOC_SECTIONS if s["id"] == section_id), None)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section


@router.get("/article/{doc_id}")
async def get_doc_article(doc_id: str):
    """Public — get a single documentation article."""
    for s in DOC_SECTIONS:
        for d in s["docs"]:
            if d["id"] == doc_id:
                return {**d, "section_id": s["id"], "section_title": s["title"]}
    raise HTTPException(status_code=404, detail="Article not found")


@router.get("/search")
async def search_docs(q: str = ""):
    """Public — full-text search across all documentation."""
    if not q:
        return {"results": [], "total": 0}
    ql = q.lower()
    results = []
    for s in DOC_SECTIONS:
        for d in s["docs"]:
            if ql in d["title"].lower() or ql in d["content"].lower():
                results.append({"id": d["id"], "title": d["title"], "section": s["title"], "snippet": d["content"][:200]})
    return {"results": results, "total": len(results), "query": q}
