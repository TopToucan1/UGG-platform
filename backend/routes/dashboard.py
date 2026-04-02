from fastapi import APIRouter, Query, Request
from database import db
from auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
async def get_summary(request: Request):
    await get_current_user(request)

    total = await db.devices.count_documents({})
    online = await db.devices.count_documents({"status": "online"})
    offline = await db.devices.count_documents({"status": "offline"})
    error = await db.devices.count_documents({"status": "error"})
    maintenance = await db.devices.count_documents({"status": "maintenance"})

    active_alerts = await db.alerts.count_documents({"status": "active"})
    critical_alerts = await db.alerts.count_documents({"status": "active", "severity": "critical"})
    warning_alerts = await db.alerts.count_documents({"status": "active", "severity": "warning"})
    info_alerts = await db.alerts.count_documents({"status": "active", "severity": "info"})

    pending_commands = await db.commands.count_documents({"status": {"$in": ["pending", "dispatched"]}})

    from datetime import datetime, timezone, timedelta
    one_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    recent_events = await db.events.count_documents({"ingested_at": {"$gte": one_min_ago}})

    return {
        "devices": {"total": total, "online": online, "offline": offline, "error": error, "maintenance": maintenance},
        "alerts": {"active": active_alerts, "critical": critical_alerts, "warning": warning_alerts, "info": info_alerts},
        "commands": {"pending": pending_commands},
        "events": {"throughput": recent_events, "total": await db.events.count_documents({})},
    }


@router.get("/device-health")
async def get_device_health(request: Request, site_id: str = None, status: str = None, protocol: str = None, search: str = None, limit: int = 100, skip: int = 0):
    await get_current_user(request)
    query = {}
    if site_id:
        query["site_id"] = site_id
    if status:
        query["status"] = status
    if protocol:
        query["protocol_family"] = protocol
    if search:
        query["$or"] = [
            {"external_ref": {"$regex": search, "$options": "i"}},
            {"manufacturer": {"$regex": search, "$options": "i"}},
            {"model": {"$regex": search, "$options": "i"}},
        ]

    devices = await db.devices.find(query, {"_id": 0}).sort("external_ref", 1).skip(skip).limit(limit).to_list(limit)
    total = await db.devices.count_documents(query)
    return {"devices": devices, "total": total}


@router.get("/recent-events")
async def get_recent_events(request: Request, limit: int = 50):
    await get_current_user(request)
    events = await db.events.find({}, {"_id": 0}).sort("occurred_at", -1).limit(limit).to_list(limit)
    return {"events": events}


@router.get("/recent-alerts")
async def get_recent_alerts(request: Request, limit: int = 20):
    await get_current_user(request)
    alerts = await db.alerts.find({"status": "active"}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"alerts": alerts}


@router.get("/event-throughput")
async def get_event_throughput(request: Request):
    await get_current_user(request)
    from datetime import datetime, timezone, timedelta
    points = []
    now = datetime.now(timezone.utc)
    for i in range(12):
        start = (now - timedelta(minutes=(i + 1) * 5)).isoformat()
        end = (now - timedelta(minutes=i * 5)).isoformat()
        count = await db.events.count_documents({"occurred_at": {"$gte": start, "$lt": end}})
        points.append({"time": end, "count": count})
    points.reverse()
    return {"throughput": points}
