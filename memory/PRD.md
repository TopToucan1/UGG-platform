# UGG - Universal Gaming Gateway | PRD

## Architecture
- **Backend**: FastAPI + MongoDB — 28 route modules, 155+ API endpoints
- **Gateway Core**: 8-stage event processing pipeline (validate→enrich→store→twin→exception→meter→broadcast→audit)
- **Adapters**: SAS Live (pyserial RS-232 + CRC16), G2S Live (zeep SOAP/HTTP + XML), S2S, VCF (6 types)
- **Frontend**: React 19 + Tailwind + Recharts + Mapbox GL + Framer Motion — 22 pages
- **AI**: Gemini 3 Flash | **Auth**: JWT RBAC (7+4 tier) | **Real-time**: WebSocket

## Phase 2 Gateway Core — Complete
- 8-stage EventPipeline: validate, enrich (statutory), store, digital twin, exception engine, meter aggregate, WebSocket broadcast, audit
- SAS Live: real RS-232 with CRC-16 validation, async serial I/O, frame builder, ROM signature integrity
- G2S Live: real SOAP/HTTP with lxml XML builder/parser, zeep WSDL client, SOAP envelope wrapping
- All 3 adapters (SAS+G2S+S2S) simultaneously connected and flowing through pipeline: 22+ events, 0 errors

## Total: 22 pages, 155+ endpoints, 28 backend modules, 4 adapter packages, Gateway Core pipeline
