from fastapi import APIRouter, Request
from database import db
from auth import get_current_user
from datetime import datetime, timezone, timedelta

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
    points = []
    now = datetime.now(timezone.utc)
    for i in range(12):
        start = (now - timedelta(minutes=(i + 1) * 5)).isoformat()
        end = (now - timedelta(minutes=i * 5)).isoformat()
        count = await db.events.count_documents({"occurred_at": {"$gte": start, "$lt": end}})
        label = (now - timedelta(minutes=i * 5)).strftime("%H:%M")
        points.append({"time": label, "count": count})
    points.reverse()
    return {"throughput": points}


@router.get("/charts")
async def get_chart_data(request: Request):
    """Aggregated chart data for Recharts visualizations."""
    await get_current_user(request)

    # Device distribution by protocol
    protocols = await db.devices.distinct("protocol_family")
    protocol_dist = []
    for p in protocols:
        c = await db.devices.count_documents({"protocol_family": p})
        protocol_dist.append({"name": p.upper(), "value": c})

    # Device distribution by manufacturer
    manufacturers = await db.devices.distinct("manufacturer")
    mfr_dist = []
    for m in manufacturers:
        c = await db.devices.count_documents({"manufacturer": m})
        mfr_dist.append({"name": m, "value": c})
    mfr_dist.sort(key=lambda x: x["value"], reverse=True)

    # Event type breakdown
    event_types = await db.events.distinct("event_type")
    event_dist = []
    for et in event_types:
        c = await db.events.count_documents({"event_type": et})
        short = et.split(".")[-1] if "." in et else et
        event_dist.append({"name": short, "fullName": et, "value": c})
    event_dist.sort(key=lambda x: x["value"], reverse=True)

    # Severity breakdown
    sev_dist = []
    for sev in ["info", "warning", "critical"]:
        c = await db.events.count_documents({"severity": sev})
        sev_dist.append({"name": sev.capitalize(), "value": c})

    # Device status distribution
    status_dist = []
    for st in ["online", "offline", "error", "maintenance"]:
        c = await db.devices.count_documents({"status": st})
        status_dist.append({"name": st.capitalize(), "value": c})

    # Hourly event volume (last 24h)
    now = datetime.now(timezone.utc)
    hourly = []
    for i in range(24):
        start = (now - timedelta(hours=i + 1)).isoformat()
        end = (now - timedelta(hours=i)).isoformat()
        count = await db.events.count_documents({"occurred_at": {"$gte": start, "$lt": end}})
        label = (now - timedelta(hours=i)).strftime("%H:00")
        hourly.append({"hour": label, "events": count})
    hourly.reverse()

    return {
        "protocol_distribution": protocol_dist,
        "manufacturer_distribution": mfr_dist,
        "event_type_distribution": event_dist[:10],
        "severity_distribution": sev_dist,
        "device_status_distribution": status_dist,
        "hourly_event_volume": hourly,
    }
