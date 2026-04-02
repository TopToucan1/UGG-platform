from fastapi import APIRouter, HTTPException, Request, Query
from database import db
from auth import get_current_user
import uuid

router = APIRouter(prefix="/api/devices", tags=["devices"])


@router.get("")
async def list_devices(
    request: Request,
    site_id: str = None,
    status: str = None,
    protocol: str = None,
    manufacturer: str = None,
    search: str = None,
    limit: int = 50,
    skip: int = 0,
):
    await get_current_user(request)
    query = {}
    if site_id:
        query["site_id"] = site_id
    if status:
        query["status"] = status
    if protocol:
        query["protocol_family"] = protocol
    if manufacturer:
        query["manufacturer"] = manufacturer
    if search:
        query["$or"] = [
            {"external_ref": {"$regex": search, "$options": "i"}},
            {"manufacturer": {"$regex": search, "$options": "i"}},
            {"model": {"$regex": search, "$options": "i"}},
            {"serial_number": {"$regex": search, "$options": "i"}},
        ]
    devices = await db.devices.find(query, {"_id": 0}).sort("external_ref", 1).skip(skip).limit(limit).to_list(limit)
    total = await db.devices.count_documents(query)
    return {"devices": devices, "total": total}


@router.get("/filters")
async def get_device_filters(request: Request):
    await get_current_user(request)
    manufacturers = await db.devices.distinct("manufacturer")
    protocols = await db.devices.distinct("protocol_family")
    statuses = await db.devices.distinct("status")
    sites = await db.sites.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(100)
    return {"manufacturers": manufacturers, "protocols": protocols, "statuses": statuses, "sites": sites}


@router.get("/{device_id}")
async def get_device(request: Request, device_id: str):
    await get_current_user(request)
    device = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    caps = await db.device_capabilities.find_one({"device_id": device_id}, {"_id": 0})
    device["capabilities"] = caps
    return device


@router.get("/{device_id}/events")
async def get_device_events(request: Request, device_id: str, limit: int = 50, event_type: str = None):
    await get_current_user(request)
    query = {"device_id": device_id}
    if event_type:
        query["event_type"] = event_type
    events = await db.events.find(query, {"_id": 0}).sort("occurred_at", -1).limit(limit).to_list(limit)
    return {"events": events}


@router.get("/{device_id}/commands")
async def get_device_commands(request: Request, device_id: str, limit: int = 50):
    await get_current_user(request)
    commands = await db.commands.find({"target_device_id": device_id}, {"_id": 0}).sort("issued_at", -1).limit(limit).to_list(limit)
    return {"commands": commands}


@router.get("/{device_id}/meters")
async def get_device_meters(request: Request, device_id: str, limit: int = 10):
    await get_current_user(request)
    meters = await db.meter_snapshots.find({"device_id": device_id}, {"_id": 0}).sort("recorded_at", -1).limit(limit).to_list(limit)
    return {"meters": meters}


@router.get("/{device_id}/audit")
async def get_device_audit(request: Request, device_id: str, limit: int = 50):
    await get_current_user(request)
    records = await db.audit_records.find({"target_id": device_id}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return {"records": records}


@router.post("/{device_id}/command")
async def send_device_command(request: Request, device_id: str):
    user = await get_current_user(request)
    body = await request.json()
    device = await db.devices.find_one({"id": device_id}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    from datetime import datetime, timezone
    cmd = {
        "id": str(uuid.uuid4()),
        "idempotency_key": str(uuid.uuid4())[:16],
        "tenant_id": device.get("tenant_id"),
        "target_device_id": device_id,
        "device_ref": device["external_ref"],
        "command_type": body.get("command_type", "device.enable"),
        "parameters": body.get("parameters", {}),
        "issued_by": user.get("email", "unknown"),
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "status": "pending",
        "result": None,
        "error_detail": None,
        "retry_count": 0,
        "correlation_id": str(uuid.uuid4()),
        "schema_version": 1,
    }
    await db.commands.insert_one(cmd)

    # Audit
    await db.audit_records.insert_one({
        "id": str(uuid.uuid4()),
        "tenant_id": device.get("tenant_id"),
        "actor": user.get("email"),
        "action": "command.issued",
        "target_type": "device",
        "target_id": device_id,
        "before": None,
        "after": {"command_type": cmd["command_type"]},
        "evidence_ref": cmd["id"],
        "timestamp": cmd["issued_at"],
    })

    cmd.pop("_id", None)
    return cmd
