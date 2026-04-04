from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import os
import logging

from auth import router as auth_router, seed_admin
from seed_data import seed_all
from seed_financial import seed_financial_and_players
from routes.dashboard import router as dashboard_router
from routes.devices import router as devices_router
from routes.events import router as events_router
from routes.commands import router as commands_router
from routes.connectors import router as connectors_router
from routes.audit import router as audit_router
from routes.alerts import router as alerts_router
from routes.emulator import router as emulator_router
from routes.ai_studio import router as ai_studio_router
from routes.messages import router as messages_router
from routes.admin import router as admin_router
from routes.financial import router as financial_router
from routes.players import router as players_router
from routes.marketplace import router as marketplace_router
from routes.jackpots import router as jackpots_router
from routes.export import router as export_router
from routes.swf_analyzer import router as swf_analyzer_router
from routes.content_registry import router as content_registry_router
from routes.route_ops import router as route_ops_router
from routes.route_advanced import router as route_advanced_router
from routes.route_map import router as route_map_router
from routes.certification import router as certification_router
from routes.adapters import router as adapters_router
from routes.gateway import router as gateway_router
from routes.digital_twin import router as digital_twin_router
from routes.emulator_lab_v2 import router as emulator_lab_v2_router
from routes.phase5_tools import router as phase5_tools_router
from routes.ai_analytics import router as ai_analytics_router
from routes.hardware import router as hardware_router
from routes.docs_library import router as docs_library_router
from routes.route_v2 import router as route_v2_router
from routes.security import router as security_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="UGG - Universal Gaming Gateway", version="1.0.0",
              docs_url="/api/docs", openapi_url="/api/openapi.json")

# Rate limiting middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse as StarletteJSONResponse

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        from routes.security import check_rate_limit
        ip = request.client.host if request.client else "unknown"
        if not check_rate_limit(ip):
            return StarletteJSONResponse({"detail": "Rate limit exceeded. Try again later."}, status_code=429)
        response = await call_next(request)
        return response

app.add_middleware(RateLimitMiddleware)

# CORS
cors_origins = os.environ.get('CORS_ORIGINS', '*')
if cors_origins == '*':
    origins_list = ["*"]
else:
    origins_list = [o.strip() for o in cors_origins.split(',') if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(devices_router)
app.include_router(events_router)
app.include_router(commands_router)
app.include_router(connectors_router)
app.include_router(audit_router)
app.include_router(alerts_router)
app.include_router(emulator_router)
app.include_router(ai_studio_router)
app.include_router(messages_router)
app.include_router(admin_router)
app.include_router(financial_router)
app.include_router(players_router)
app.include_router(marketplace_router)
app.include_router(jackpots_router)
app.include_router(export_router)
app.include_router(swf_analyzer_router)
app.include_router(content_registry_router)
app.include_router(route_ops_router)
app.include_router(route_advanced_router)
app.include_router(route_map_router)
app.include_router(certification_router)
app.include_router(adapters_router)
app.include_router(gateway_router)
app.include_router(digital_twin_router)
app.include_router(emulator_lab_v2_router)
app.include_router(phase5_tools_router)
app.include_router(ai_analytics_router)
app.include_router(hardware_router)
app.include_router(docs_library_router)
app.include_router(route_v2_router)
app.include_router(security_router)


@app.get("/api")
async def root():
    return {"message": "UGG - Universal Gaming Gateway API", "version": "1.0.0"}


@app.on_event("startup")
async def startup():
    logger.info("Starting UGG Platform...")
    await seed_admin()
    await seed_all()
    await seed_financial_and_players()
    from seed_marketplace import seed_marketplace_and_jackpots
    await seed_marketplace_and_jackpots()
    from seed_route import seed_route_module
    await seed_route_module()
    # Start real-time event generator
    from routes.events import start_event_generator
    start_event_generator()
    # Start Gateway Core event pipeline
    from gateway_core import gateway_core
    await gateway_core.start()
    from routes.hardware import seed_library
    await seed_library()
    from routes.route_v2 import seed_route_v2
    await seed_route_v2()
    logger.info("UGG Platform ready — real-time event generator + Gateway Core active")


@app.on_event("shutdown")
async def shutdown():
    from database import client
    client.close()
