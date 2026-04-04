# UGG - Universal Gaming Gateway | PRD

## Architecture
- **Backend**: FastAPI + MongoDB — 27 route modules, 150+ API endpoints, 4 protocol adapter packages
- **Frontend**: React 19 + Tailwind + Recharts + Mapbox GL + Framer Motion — 22 pages
- **Adapters**: SAS (pyserial), G2S (zeep/SOAP), S2S, Vendor Connector Framework (6 types)
- **AI**: Gemini 3 Flash | **Auth**: JWT RBAC (7 roles + 4-tier) | **Real-time**: WebSocket

## Phase 1 Protocol Adapters — Complete

### @ugg/sas-adapter (SAS — RS-232 Serial)
- Full 38-meter SAS map with SAS_METER_BY_CODE lookup and ILT_ vendor extension detection
- Poll-response engine with configurable cycle, per-device addressing (0x01-0x1F)
- FaultInjector: MSX001-MSX099, SUPPRESS_RESPONSE, CORRUPT_RESPONSE with count/offset/repeat
- Async poll loop with ConnectionState machine (CLOSED→OPENING→ONLINE→LOST→reconnect)
- Raw hex trace emission for Protocol Trace viewer
- Virtual mode for emulation when no physical serial port

### @ugg/g2s-adapter (G2S — SOAP/XML over HTTP)
- 6 transport states: closed→opening→sync→online→closing→lost
- CommsDisabledHandler: immediate commsDisabledAck + scheduled setCommsState enable=true
- StartupAlgorithmEngine: fixed anchors + verbose mode (getDeviceStatus+setDeviceState per class) + step-through
- CommandGroupExecutor: multiple commands from same class in one SOAP message
- Proxy Certificate: G2S_egmProxy entity type in certificate OU field
- KeepAlive: configurable interval, 3 missed → LOST state
- Schema support: G2S 2.1.0 and 1.1.0

### @ugg/s2s-adapter (S2S — System-to-System)
- Edge/Central topology: UGG Agent as Edge, CMS as Central
- Negotiate handshake with schema versioning (S2S_1.2.6, S2S_1.3.1, S2S_1.5.0)
- Periodic metric push to Central on configurable reportInterval
- Central command translation: S2S→G2S routing to correct adapter

### @ugg/vendor-connector (Vendor Connector Framework)
- 6 connector types: REST, DATABASE, LOG, SDK, FILE, MESSAGE_BUS
- ConnectorManifest with EventMapping[] and configSchema validation
- ConnectorFactory singleton with register/create pattern
- RestConnector with HTTP polling + event mapping
- 4 pre-registered manifests (REST Loyalty, DB Legacy CMS, Log Parser, Kafka Stream)

### Emulator Lab UI Enhancement
- Connector Status Panel: live adapter instances with connection state dots + protocol badges
- 3-Tab Protocol Trace: G2S Messages | SOAP Transport | Protocol Trace (raw hex + ASCII)
- Connect Adapter form: select protocol (SAS/G2S/S2S), device ID, connect/disconnect
- Adapter Detail panel: poll counts, message counts, schema versions, edge IDs

## Total: 22 pages, 150+ endpoints, 27 backend modules, 4 adapter packages
