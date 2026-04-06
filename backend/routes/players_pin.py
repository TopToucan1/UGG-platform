"""
Player PIN management + PIN-based session queries.

This is the NEW PIN-based tracking model. Separate from legacy routes/players.py
which reads the card-based player_sessions collection.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from database import db
from auth import get_current_user, require_role
from session_engine import hash_pin, verify_pin

router = APIRouter(prefix="/api/players-pin", tags=["players-pin"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class PlayerCreateInput(BaseModel):
    name: str
    pin: str = Field(..., min_length=4, max_length=8)
    account_ref: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tenant_id: Optional[str] = None
    notes: Optional[str] = None


class PlayerUpdateInput(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class PinChangeInput(BaseModel):
    new_pin: str = Field(..., min_length=4, max_length=8)


# ─────────────────────────────────────────────
# Player CRUD — collection endpoints (no path params)
# ─────────────────────────────────────────────
@router.post("")
async def create_player(inp: PlayerCreateInput, request: Request):
    await require_role(request, ["admin", "operator"])
    if not inp.pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN must be numeric")
    if inp.account_ref:
        existing = await db.players_pin.find_one({"account_ref": inp.account_ref})
        if existing:
            raise HTTPException(status_code=400, detail="account_ref already exists")

    player = {
        "id": str(uuid.uuid4()),
        "name": inp.name,
        "pin_hash": hash_pin(inp.pin),
        "account_ref": inp.account_ref,
        "email": inp.email,
        "phone": inp.phone,
        "tenant_id": inp.tenant_id,
        "notes": inp.notes,
        "status": "active",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await db.players_pin.insert_one(dict(player))
    player.pop("pin_hash", None)
    return player


@router.get("")
async def list_players(
    request: Request,
    status: Optional[str] = None,
    tenant_id: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 100,
    skip: int = 0,
):
    await get_current_user(request)
    query = {}
    if status:
        query["status"] = status
    if tenant_id:
        query["tenant_id"] = tenant_id
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"account_ref": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
        ]
    cursor = db.players_pin.find(query, {"_id": 0, "pin_hash": 0}).sort("created_at", -1).skip(skip).limit(limit)
    players = await cursor.to_list(limit)
    total = await db.players_pin.count_documents(query)
    return {"players": players, "total": total}


# ─────────────────────────────────────────────
# Summary (static path — must be before /{player_id})
# ─────────────────────────────────────────────
@router.get("/summary")
async def summary(request: Request):
    await get_current_user(request)
    total_players = await db.players_pin.count_documents({"status": "active"})
    active_credit = await db.credit_sessions.count_documents({"is_active": True})
    active_pin = await db.pin_sessions.count_documents({"is_active": True})
    total_credit = await db.credit_sessions.count_documents({})
    total_pin = await db.pin_sessions.count_documents({})
    open_anomalies = await db.session_anomalies.count_documents({"status": "open"})
    return {
        "active_players": total_players,
        "active_credit_sessions": active_credit,
        "active_pin_sessions": active_pin,
        "total_credit_sessions": total_credit,
        "total_pin_sessions": total_pin,
        "open_anomalies": open_anomalies,
    }


# ─────────────────────────────────────────────
# Session queries (static paths — must be before /{player_id})
# ─────────────────────────────────────────────
@router.get("/sessions/credit")
async def list_credit_sessions(
    request: Request,
    device_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
    skip: int = 0,
):
    await get_current_user(request)
    query = {}
    if device_id:
        query["device_id"] = device_id
    if tenant_id:
        query["tenant_id"] = tenant_id
    if is_active is not None:
        query["is_active"] = is_active
    cursor = db.credit_sessions.find(query, {"_id": 0}).sort("started_at", -1).skip(skip).limit(limit)
    sessions = await cursor.to_list(limit)
    total = await db.credit_sessions.count_documents(query)
    return {"sessions": sessions, "total": total}


@router.get("/sessions/credit/{session_id}")
async def get_credit_session(session_id: str, request: Request):
    await get_current_user(request)
    session = await db.credit_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Credit session not found")
    pin_sessions = await db.pin_sessions.find(
        {"credit_session_id": session_id}, {"_id": 0}
    ).sort("started_at", 1).to_list(100)
    session["pin_sessions"] = pin_sessions
    return session


@router.get("/sessions/pin")
async def list_pin_sessions(
    request: Request,
    player_id: Optional[str] = None,
    device_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 50,
    skip: int = 0,
):
    await get_current_user(request)
    query = {}
    if player_id:
        query["player_id"] = player_id
    if device_id:
        query["device_id"] = device_id
    if is_active is not None:
        query["is_active"] = is_active
    cursor = db.pin_sessions.find(query, {"_id": 0}).sort("started_at", -1).skip(skip).limit(limit)
    sessions = await cursor.to_list(limit)
    total = await db.pin_sessions.count_documents(query)
    return {"sessions": sessions, "total": total}


@router.get("/sessions/active")
async def active_sessions(request: Request):
    """All currently active credit and pin sessions across the fleet."""
    await get_current_user(request)
    credit = await db.credit_sessions.find({"is_active": True}, {"_id": 0}).to_list(500)
    pin = await db.pin_sessions.find({"is_active": True}, {"_id": 0}).to_list(500)
    return {
        "credit_sessions": credit,
        "pin_sessions": pin,
        "credit_count": len(credit),
        "pin_count": len(pin),
    }


# ─────────────────────────────────────────────
# Anomalies (static paths — must be before /{player_id})
# ─────────────────────────────────────────────
@router.get("/anomalies")
async def list_anomalies(
    request: Request,
    player_id: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
):
    await get_current_user(request)
    query = {}
    if player_id:
        query["player_id"] = player_id
    if status:
        query["status"] = status
    if severity:
        query["severity"] = severity
    cursor = db.session_anomalies.find(query, {"_id": 0}).sort("detected_at", -1).skip(skip).limit(limit)
    anomalies = await cursor.to_list(limit)
    total = await db.session_anomalies.count_documents(query)
    return {"anomalies": anomalies, "total": total}


@router.post("/anomalies/{anomaly_id}/ack")
async def acknowledge_anomaly(anomaly_id: str, request: Request):
    user = await require_role(request, ["admin", "operator"])
    result = await db.session_anomalies.update_one(
        {"id": anomaly_id},
        {"$set": {"status": "acknowledged", "acknowledged_by": user.get("email"), "acknowledged_at": _now_iso()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return {"acknowledged": True}


@router.post("/anomalies/{anomaly_id}/dismiss")
async def dismiss_anomaly(anomaly_id: str, request: Request):
    user = await require_role(request, ["admin", "operator"])
    result = await db.session_anomalies.update_one(
        {"id": anomaly_id},
        {"$set": {"status": "dismissed", "dismissed_by": user.get("email"), "dismissed_at": _now_iso()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Anomaly not found")
    return {"dismissed": True}


# ─────────────────────────────────────────────
# Player by ID (dynamic path — MUST be last to avoid catching static routes)
# ─────────────────────────────────────────────
@router.get("/{player_id}")
async def get_player(player_id: str, request: Request):
    await get_current_user(request)
    player = await db.players_pin.find_one({"id": player_id}, {"_id": 0, "pin_hash": 0})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    active_pin = await db.pin_sessions.find_one(
        {"player_id": player_id, "is_active": True}, {"_id": 0}
    )
    player["active_pin_session"] = active_pin
    return player


@router.patch("/{player_id}")
async def update_player(player_id: str, inp: PlayerUpdateInput, request: Request):
    await require_role(request, ["admin", "operator"])
    update = {k: v for k, v in inp.model_dump().items() if v is not None}
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")
    update["updated_at"] = _now_iso()
    result = await db.players_pin.update_one({"id": player_id}, {"$set": update})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"updated": True}


@router.post("/{player_id}/pin")
async def change_pin(player_id: str, inp: PinChangeInput, request: Request):
    await require_role(request, ["admin", "operator"])
    if not inp.new_pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN must be numeric")
    result = await db.players_pin.update_one(
        {"id": player_id},
        {"$set": {"pin_hash": hash_pin(inp.new_pin), "updated_at": _now_iso()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"updated": True}


@router.delete("/{player_id}")
async def deactivate_player(player_id: str, request: Request):
    await require_role(request, ["admin"])
    result = await db.players_pin.update_one(
        {"id": player_id}, {"$set": {"status": "inactive", "updated_at": _now_iso()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Player not found")
    return {"deactivated": True}
