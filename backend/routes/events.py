from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from database import db
from auth import get_current_user
from ws_manager import manager

router = APIRouter(prefix="/api/events", tags=["events"])


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
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, "events")
