"""
Device Messaging API — Allows UGG to send messages TO games, and games to poll/acknowledge them.
Designed for indie/NoCode developers whose games need to receive and display operator messages.
"""
from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/device-messages", tags=["device-messages"])


# ══════════════════════════════════════════════════
# OPERATOR SIDE — Send messages to devices
# ══════════════════════════════════════════════════

@router.post("/send")
async def send_device_message(request: Request):
    """Operator sends a message to one or more devices."""
    user = await get_current_user(request)
    body = await request.json()

    target_devices = body.get("device_ids", [])
    if isinstance(target_devices, str):
        target_devices = [target_devices]

    message = {
        "message_text": body.get("message", ""),
        "message_type": body.get("type", "INFO"),  # INFO, PROMO, MAINTENANCE, RESPONSIBLE_GAMBLING, URGENT
        "display_duration_seconds": body.get("duration_seconds", 30),
        "display_position": body.get("position", "BOTTOM"),  # TOP, BOTTOM, CENTER, FULLSCREEN
        "background_color": body.get("background_color"),
        "text_color": body.get("text_color"),
        "priority": body.get("priority", "NORMAL"),  # LOW, NORMAL, HIGH, URGENT
        "expires_at": body.get("expires_at") or (datetime.now(timezone.utc) + timedelta(hours=body.get("expires_hours", 24))).isoformat(),
        "sent_by": user.get("email"),
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }

    created = []
    for device_id in target_devices:
        msg = {
            "id": str(uuid.uuid4()),
            "device_id": device_id,
            **message,
            "status": "PENDING",  # PENDING → DELIVERED → DISPLAYED → ACKNOWLEDGED
            "delivered_at": None,
            "displayed_at": None,
            "acknowledged_at": None,
        }
        await db.device_messages.insert_one(msg)
        msg.pop("_id", None)
        created.append(msg)

    return {"messages_sent": len(created), "messages": created}


@router.get("/outbox")
async def get_message_outbox(request: Request, device_id: str = None, status: str = None, limit: int = 50):
    """Operator view — see all sent messages and their delivery status."""
    await get_current_user(request)
    query = {}
    if device_id:
        query["device_id"] = device_id
    if status:
        query["status"] = status
    messages = await db.device_messages.find(query, {"_id": 0}).sort("sent_at", -1).limit(limit).to_list(limit)
    # Stats
    total = await db.device_messages.count_documents(query if query else {})
    pending = await db.device_messages.count_documents({"status": "PENDING"})
    delivered = await db.device_messages.count_documents({"status": "DELIVERED"})
    displayed = await db.device_messages.count_documents({"status": "DISPLAYED"})
    acknowledged = await db.device_messages.count_documents({"status": "ACKNOWLEDGED"})
    return {"messages": messages, "total": total, "stats": {"pending": pending, "delivered": delivered, "displayed": displayed, "acknowledged": acknowledged}}


# ══════════════════════════════════════════════════
# DEVICE/GAME SIDE — Poll for messages, acknowledge display
# These endpoints are called BY the game, not by the operator
# ══════════════════════════════════════════════════

@router.get("/poll/{device_id}")
async def poll_device_messages(device_id: str):
    """
    GAME CALLS THIS — Poll for pending messages.
    No authentication required (device authenticates via its device_id).
    Returns messages that need to be displayed on the game screen.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Get all pending or delivered messages for this device that haven't expired
    messages = await db.device_messages.find({
        "device_id": device_id,
        "status": {"$in": ["PENDING", "DELIVERED"]},
        "expires_at": {"$gte": now},
    }, {"_id": 0}).sort("priority_sort", -1).to_list(10)

    # Mark as DELIVERED on first poll
    for msg in messages:
        if msg["status"] == "PENDING":
            await db.device_messages.update_one(
                {"id": msg["id"], "status": "PENDING"},
                {"$set": {"status": "DELIVERED", "delivered_at": now}}
            )
            msg["status"] = "DELIVERED"
            msg["delivered_at"] = now

    # Simplify response for NoCode developers
    simple_messages = []
    for msg in messages:
        simple_messages.append({
            "id": msg["id"],
            "text": msg["message_text"],
            "type": msg["message_type"],
            "duration_seconds": msg.get("display_duration_seconds", 30),
            "position": msg.get("display_position", "BOTTOM"),
            "background_color": msg.get("background_color"),
            "text_color": msg.get("text_color"),
            "priority": msg.get("priority", "NORMAL"),
        })

    return {
        "device_id": device_id,
        "messages": simple_messages,
        "count": len(simple_messages),
        "poll_again_seconds": 30,
    }


@router.post("/displayed/{message_id}")
async def mark_message_displayed(message_id: str):
    """
    GAME CALLS THIS — Tell UGG the message is now showing on screen.
    No authentication required.
    """
    result = await db.device_messages.update_one(
        {"id": message_id, "status": {"$in": ["PENDING", "DELIVERED"]}},
        {"$set": {"status": "DISPLAYED", "displayed_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        return {"status": "already_displayed_or_not_found"}
    return {"status": "ok", "message_id": message_id}


@router.post("/acknowledged/{message_id}")
async def acknowledge_message(message_id: str):
    """
    GAME CALLS THIS — Tell UGG the player dismissed/acknowledged the message.
    No authentication required.
    """
    result = await db.device_messages.update_one(
        {"id": message_id, "status": {"$in": ["PENDING", "DELIVERED", "DISPLAYED"]}},
        {"$set": {"status": "ACKNOWLEDGED", "acknowledged_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.modified_count == 0:
        return {"status": "already_acknowledged_or_not_found"}
    return {"status": "ok", "message_id": message_id}


# ══════════════════════════════════════════════════
# BROADCAST — Send to all devices or filtered set
# ══════════════════════════════════════════════════

@router.post("/broadcast")
async def broadcast_message(request: Request):
    """Send a message to ALL online devices or a filtered subset."""
    user = await get_current_user(request)
    body = await request.json()

    # Get target devices
    device_filter = body.get("device_filter", {})
    query = {}
    if device_filter.get("status"):
        query["status"] = device_filter["status"]
    if device_filter.get("site_id"):
        query["site_id"] = device_filter["site_id"]
    if device_filter.get("distributor_id"):
        query["distributor_id"] = device_filter["distributor_id"]

    devices = await db.devices.find(query, {"_id": 0, "id": 1}).to_list(500)
    device_ids = [d["id"] for d in devices]

    if not device_ids:
        return {"messages_sent": 0, "message": "No devices matched filter"}

    # Create message for each device
    now = datetime.now(timezone.utc)
    messages = []
    for did in device_ids:
        messages.append({
            "id": str(uuid.uuid4()),
            "device_id": did,
            "message_text": body.get("message", ""),
            "message_type": body.get("type", "INFO"),
            "display_duration_seconds": body.get("duration_seconds", 30),
            "display_position": body.get("position", "BOTTOM"),
            "background_color": body.get("background_color"),
            "text_color": body.get("text_color"),
            "priority": body.get("priority", "NORMAL"),
            "expires_at": (now + timedelta(hours=body.get("expires_hours", 24))).isoformat(),
            "sent_by": user.get("email"),
            "sent_at": now.isoformat(),
            "status": "PENDING",
            "delivered_at": None, "displayed_at": None, "acknowledged_at": None,
        })
    await db.device_messages.insert_many(messages)
    return {"messages_sent": len(messages), "target_devices": len(device_ids), "broadcast_type": body.get("type", "INFO")}
