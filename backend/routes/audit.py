from fastapi import APIRouter, Request
from database import db
from auth import get_current_user

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
async def list_audit_records(
    request: Request,
    action: str = None,
    actor: str = None,
    target_type: str = None,
    limit: int = 50,
    skip: int = 0,
):
    await get_current_user(request)
    query = {}
    if action:
        query["action"] = {"$regex": action, "$options": "i"}
    if actor:
        query["actor"] = {"$regex": actor, "$options": "i"}
    if target_type:
        query["target_type"] = target_type
    records = await db.audit_records.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.audit_records.count_documents(query)
    return {"records": records, "total": total}


@router.get("/actions")
async def get_audit_actions(request: Request):
    await get_current_user(request)
    actions = await db.audit_records.distinct("action")
    actors = await db.audit_records.distinct("actor")
    target_types = await db.audit_records.distinct("target_type")
    return {"actions": sorted(actions), "actors": sorted(actors), "target_types": sorted(target_types)}
