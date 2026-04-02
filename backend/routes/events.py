from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from database import db
from auth import get_current_user
from ws_manager import manager
import asyncio
import uuid
import random
import hashlib
import json
from datetime import datetime, timezone

router = APIRouter(prefix="/api/events", tags=["events"])

EVENT_TYPES = [
    "device.game.start", "device.game.end", "device.door.opened", "device.door.closed",
    "device.tilt", "device.voucher.in", "device.voucher.out", "device.jackpot.handpay",
    "device.meter.changed", "device.player.card.in", "device.player.card.out",
    "device.status.online", "device.health.check", "device.bonus.triggered",
]
SEVERITIES = {
    "device.game.start": "info", "device.game.end": "info",
    "device.door.opened": "warning", "device.door.closed": "info",
    "device.tilt": "critical", "device.voucher.in": "info",
    "device.voucher.out": "info", "device.jackpot.handpay": "warning",
    "device.meter.changed": "info", "device.player.card.in": "info",
    "device.player.card.out": "info", "device.status.online": "info",
    "device.health.check": "info", "device.bonus.triggered": "info",
}

_generator_task = None


async def event_generator():
    """Background task that generates realistic events and broadcasts via WebSocket."""
    while True:
        try:
            await asyncio.sleep(random.uniform(2.0, 6.0))
            devices = await db.devices.find({"status": "online"}, {"_id": 0, "id": 1, "external_ref": 1, "tenant_id": 1, "site_id": 1, "connector_id": 1, "protocol_family": 1}).to_list(100)
            if not devices:
                continue
            device = random.choice(devices)
            event_type = random.choice(EVENT_TYPES)

            payload_data = {}
            if "game" in event_type:
                payload_data = {"game_id": random.randint(1, 50), "bet": round(random.uniform(0.25, 50.0), 2)}
                if event_type == "device.game.end":
                    payload_data["win"] = round(random.uniform(0, 500.0), 2)
            elif "meter" in event_type:
                payload_data = {"coin_in": random.randint(10000, 999999), "coin_out": random.randint(5000, 800000)}
            elif "door" in event_type:
                payload_data = {"door_type": random.choice(["main", "belly", "stacker"])}
            elif "voucher" in event_type:
                payload_data = {"amount": round(random.uniform(1.0, 500.0), 2)}

            now = datetime.now(timezone.utc).isoformat()
            integrity = hashlib.sha256(json.dumps(payload_data).encode()).hexdigest()[:32]

            event = {
                "id": str(uuid.uuid4()),
                "tenant_id": device.get("tenant_id"),
                "site_id": device.get("site_id"),
                "device_id": device["id"],
                "device_ref": device.get("external_ref", ""),
                "connector_id": device.get("connector_id"),
                "event_type": event_type,
                "source_protocol": device.get("protocol_family", "sas"),
                "severity": SEVERITIES.get(event_type, "info"),
                "occurred_at": now,
                "ingested_at": now,
                "payload": payload_data,
                "integrity_hash": integrity,
                "correlation_id": str(uuid.uuid4()),
                "replay_marker": False,
                "schema_version": 1,
            }

            await db.events.insert_one({**event})
            event.pop("_id", None)
            await manager.broadcast(event, "events")

            # Occasionally generate VIP player alerts (Platinum/Diamond card-in)
            if random.random() < 0.08:
                vip_tiers = ["Platinum", "Diamond"]
                vip_names = ["Sarah R.", "James T.", "Maria H.", "David S.", "Wei L.", "Olga K.", "Carlos G.", "Yuki F."]
                tier = random.choice(vip_tiers)
                player_name = random.choice(vip_names)
                player_id = f"PL-{random.randint(20000, 20049)}"
                lifetime_value = round(random.uniform(25000, 500000), 2)
                preferred_games = random.sample(["Buffalo Gold", "Lightning Link", "Dragon Link", "88 Fortunes", "Quick Hit", "Wheel of Fortune"], 3)
                vip_alert = {
                    "id": str(uuid.uuid4()),
                    "type": "vip_player_alert",
                    "player_id": player_id,
                    "player_name": player_name,
                    "player_tier": tier,
                    "device_id": device["id"],
                    "device_ref": device.get("external_ref", ""),
                    "site_id": device.get("site_id"),
                    "lifetime_value": lifetime_value,
                    "preferred_games": preferred_games,
                    "total_visits": random.randint(50, 800),
                    "avg_session_minutes": random.randint(45, 240),
                    "action": "card_in",
                    "occurred_at": now,
                    "message": f"{tier} member {player_name} just carded in at {device.get('external_ref', '')}",
                }
                await db.vip_alerts.insert_one({**vip_alert})
                vip_alert.pop("_id", None)
                await manager.broadcast(vip_alert, "vip_alerts")
                await manager.broadcast(vip_alert, "events")
        except Exception:
            await asyncio.sleep(5)


def start_event_generator():
    global _generator_task
    if _generator_task is None or _generator_task.done():
        _generator_task = asyncio.create_task(event_generator())


@router.get("")
async def list_events(
    request: Request,
    device_id: str = None,
    event_type: str = None,
    severity: str = None,
    limit: int = 50,
    skip: int = 0,
):
    await get_current_user(request)
    query = {}
    if device_id:
        query["device_id"] = device_id
    if event_type:
        query["event_type"] = {"$regex": event_type, "$options": "i"}
    if severity:
        query["severity"] = severity
    events = await db.events.find(query, {"_id": 0}).sort("occurred_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.events.count_documents(query)
    return {"events": events, "total": total}


@router.get("/types")
async def get_event_types(request: Request):
    await get_current_user(request)
    types = await db.events.distinct("event_type")
    return {"types": sorted(types)}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "events")
    start_event_generator()
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "events")


@router.websocket("/ws/vip")
async def vip_websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "vip_alerts")
    start_event_generator()
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "vip_alerts")


@router.get("/vip-alerts")
async def list_vip_alerts(request: Request, limit: int = 30):
    await get_current_user(request)
    alerts = await db.vip_alerts.find({}, {"_id": 0}).sort("occurred_at", -1).limit(limit).to_list(limit)
    return {"alerts": alerts, "total": await db.vip_alerts.count_documents({})}
