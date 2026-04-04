# UGG - Universal Gaming Gateway | PRD

## Architecture
- **Backend**: FastAPI + MongoDB — 30 route modules, 175+ API endpoints
- **Gateway Core**: 8-stage event pipeline | **Adapters**: SAS/G2S/S2S/VCF
- **Frontend**: React 19 + Tailwind + Recharts + Mapbox GL + Framer Motion — 23 pages
- **AI**: Gemini 3 Flash | **Auth**: JWT RBAC (7+4 tier) | **Real-time**: WebSocket

## Phase 4 Emulator Lab — Complete (All 6 Gaps Closed)
1. **SmartEGM Engine**: 12 player verbs (INSERT_BILL, PUSH_PLAY_BUTTON, CASH_OUT, HANDPAY, OPEN_DOOR, FORCE_TILT, etc.), state machine, win probability distribution, meter tracking
2. **Response Manager**: Configurable response profiles with rules (sendOnOccurrence, sendCount, repeatPattern), 4 actions (NO_RESPONSE, CUSTOM_COMMAND, APP_ERROR, CUSTOM_APP_ERROR), custom error format validation (XXX_YYYYYY)
3. **19-Verb Script DSL**: comment, notice, pause, prompt, player-verb, wait-for-events, wait-for-commands, perform-snapshot, balanced-meters-analysis, run-script, etc. 4 system scripts pre-loaded
4. **Balanced Meters Analysis**: 8 Appendix B tests (BM-01 through BM-08), delta computation between snapshots, CSV export
5. **TAR (Transcript Analysis Report)**: 7 sections (Comms Sessions, Summary, Commands, Event Log, ACK Errors, Balanced Meters, Coverage Map), RED/YELLOW/GREEN flagging
6. **Watchables XPath Engine**: 7 pre-built expressions, activate/deactivate toggles, match counting

## Total: 23 pages, 175+ endpoints, 30 backend modules
