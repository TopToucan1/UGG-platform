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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="UGG - Universal Gaming Gateway", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://nervous-mclean-4.preview.emergentagent.com", "http://localhost:3000"],
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
    # Start real-time event generator
    from routes.events import start_event_generator
    start_event_generator()
    logger.info("UGG Platform ready — real-time event generator active")


@app.on_event("shutdown")
async def shutdown():
    from database import client
    client.close()
