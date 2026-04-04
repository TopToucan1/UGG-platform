"""
Digital Twin API — real-time device state projections.
Each device has a projection tracking operational state, health score,
live meters, comms state, integrity, and last event timestamps.
"""
from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
from gateway_core import gateway_core, pipeline
import uuid
import random
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/digital-twin", tags=["digital-twin"])


async def _ensure_twin_projections():
    """Ensure every device has a twin projection row. Seed if missing."""
    twin_count = await db.device_state_projection.count_documents({})
    device_count = await db.devices.count_documents({})
    if twin_count >= device_count:
        return
    devices = await db.devices.find({}, {"_id": 0}).to_list(200)
    if not devices:
        return
    now = datetime.now(timezone.utc)
    for d in devices:
        coin_in = random.randint(5000, 200000)
        coin_out = int(coin_in * random.uniform(0.78, 0.95))
        await db.device_state_projection.update_one(
            {"device_id": d["id"]},
            {"$setOnInsert": {
                "device_id": d["id"], "device_ref": d.get("external_ref", ""),
                "manufacturer": d.get("manufacturer", ""), "model": d.get("model", ""),
                "protocol": d.get("protocol_family", "sas"),
                "site_id": d.get("site_id", ""), "tenant_id": d.get("tenant_id", ""),
                "operational_state": d.get("status", "UNKNOWN").upper(),
                "health_score": round(random.uniform(70, 100), 1),
                "last_event_at": (now - timedelta(minutes=random.randint(0, 60))).isoformat(),
                "last_meter_at": (now - timedelta(minutes=random.randint(0, 30))).isoformat(),
                "coin_in_today": coin_in, "coin_out_today": coin_out,
                "current_credits": random.randint(0, 5000),
                "games_played_today": random.randint(50, 2000),
                "comms_state": random.choice(["ONLINE", "ONLINE", "ONLINE", "SYNC", "CLOSED"]),
                "software_integrity": random.choice(["PASS", "PASS", "PASS", "PASS", "UNCHECKED"]),
                "last_integrity_at": (now - timedelta(hours=random.randint(0, 24))).isoformat(),
                "updated_at": now.isoformat(),
            }},
            upsert=True,
        )


@router.get("/fleet")
async def get_fleet_twins(request: Request, status: str = None, protocol: str = None, search: str = None, sort_by: str = "health_score", limit: int = 100):
    """Get digital twin projections for all devices."""
    await get_current_user(request)
    await _ensure_twin_projections()
    query = {}
    if status:
        query["operational_state"] = status.upper()
    if protocol:
        query["protocol"] = protocol
    if search:
        query["$or"] = [{"device_ref": {"$regex": search, "$options": "i"}}, {"manufacturer": {"$regex": search, "$options": "i"}}]
    sort_dir = -1 if sort_by in ("health_score", "coin_in_today") else 1
    twins = await db.device_state_projection.find(query, {"_id": 0}).sort(sort_by, sort_dir).limit(limit).to_list(limit)
    total = await db.device_state_projection.count_documents(query)
    return {"twins": twins, "total": total}


@router.get("/fleet/summary")
async def fleet_twin_summary(request: Request):
    """Aggregated fleet digital twin summary."""
    await get_current_user(request)
    await _ensure_twin_projections()
    total = await db.device_state_projection.count_documents({})
    online = await db.device_state_projection.count_documents({"operational_state": "ONLINE"})
    offline = await db.device_state_projection.count_documents({"operational_state": {"$in": ["OFFLINE", "CLOSED"]}})
    lost = await db.device_state_projection.count_documents({"comms_state": "LOST"})
    integrity_pass = await db.device_state_projection.count_documents({"software_integrity": "PASS"})

    # Aggregations
    agg = await db.device_state_projection.aggregate([{"$group": {
        "_id": None,
        "total_coin_in": {"$sum": {"$ifNull": ["$coin_in_today", 0]}},
        "total_coin_out": {"$sum": {"$ifNull": ["$coin_out_today", 0]}},
        "total_credits": {"$sum": {"$ifNull": ["$current_credits", 0]}},
        "total_games": {"$sum": {"$ifNull": ["$games_played_today", 0]}},
        "avg_health": {"$avg": {"$ifNull": ["$health_score", 0]}},
    }}]).to_list(1)
    stats = agg[0] if agg else {}

    avg_h = stats.get("avg_health")
    avg_health_val = round(avg_h, 1) if avg_h is not None else 0.0

    # Health distribution
    health_ranges = [
        {"label": "Critical (<70)", "min": 0, "max": 70, "color": "#FF3B3B"},
        {"label": "Warning (70-90)", "min": 70, "max": 90, "color": "#FFB800"},
        {"label": "Healthy (90-100)", "min": 90, "max": 101, "color": "#00D97E"},
    ]
    health_dist = []
    for hr in health_ranges:
        c = await db.device_state_projection.count_documents({"health_score": {"$gte": hr["min"], "$lt": hr["max"]}})
        health_dist.append({"label": hr["label"], "count": c, "color": hr["color"]})

    # Comms state distribution
    comms_pipe = [{"$group": {"_id": "$comms_state", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    comms_dist = await db.device_state_projection.aggregate(comms_pipe).to_list(10)

    # Protocol distribution
    proto_pipe = [{"$group": {"_id": "$protocol", "count": {"$sum": 1}, "avg_health": {"$avg": {"$ifNull": ["$health_score", 0]}}}}, {"$sort": {"count": -1}}]
    proto_dist = await db.device_state_projection.aggregate(proto_pipe).to_list(10)

    return {
        "total_devices": total, "online": online, "offline": offline, "comms_lost": lost,
        "integrity_pass": integrity_pass, "integrity_rate": round(integrity_pass / total * 100, 1) if total > 0 else 0,
        "total_coin_in": stats.get("total_coin_in", 0) or 0, "total_coin_out": stats.get("total_coin_out", 0) or 0,
        "total_credits": stats.get("total_credits", 0) or 0, "total_games": stats.get("total_games", 0) or 0,
        "avg_health": avg_health_val,
        "health_distribution": health_dist,
        "comms_distribution": [{"state": c["_id"] or "UNKNOWN", "count": c["count"]} for c in comms_dist],
        "protocol_distribution": [{"protocol": p["_id"] or "unknown", "count": p["count"], "avg_health": round(p["avg_health"] or 0, 1)} for p in proto_dist],
    }


@router.get("/device/{device_id}")
async def get_device_twin(request: Request, device_id: str):
    """Get detailed digital twin for a single device."""
    await get_current_user(request)
    twin = await db.device_state_projection.find_one({"device_id": device_id}, {"_id": 0})
    if not twin:
        raise HTTPException(status_code=404, detail="No digital twin for this device")
    # Get recent events
    events = await db.events.find({"device_id": device_id}, {"_id": 0}).sort("occurred_at", -1).limit(10).to_list(10)
    twin["recent_events"] = events
    # Get recent meters
    meters = await db.meter_snapshots.find({"device_id": device_id}, {"_id": 0}).sort("recorded_at", -1).limit(10).to_list(10)
    twin["recent_meters"] = meters
    return twin


@router.get("/gateway")
async def get_gateway_twin_status(request: Request):
    """Gateway Core status combined with digital twin fleet summary."""
    await get_current_user(request)
    gw = gateway_core.get_status()
    return {
        "gateway": gw,
        "pipeline_stages": [
            {"name": "VALIDATE", "description": "Schema validation + integrity hash"},
            {"name": "ENRICH", "description": "Device/site metadata + statutory fields"},
            {"name": "STORE", "description": "Persist to events collection"},
            {"name": "TWIN", "description": "Update device state projection"},
            {"name": "EXCEPTION", "description": "Evaluate exception rules"},
            {"name": "METER", "description": "Aggregate meter snapshots"},
            {"name": "BROADCAST", "description": "Push to WebSocket clients"},
            {"name": "AUDIT", "description": "Write audit trail"},
        ],
    }
