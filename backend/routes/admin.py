from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user, require_role
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/tenants")
async def list_tenants(request: Request):
    await get_current_user(request)
    tenants = await db.tenants.find({}, {"_id": 0}).to_list(100)
    return {"tenants": tenants}


@router.get("/sites")
async def list_sites(request: Request, tenant_id: str = None):
    await get_current_user(request)
    query = {}
    if tenant_id:
        query["tenant_id"] = tenant_id
    sites = await db.sites.find(query, {"_id": 0}).to_list(100)
    return {"sites": sites}


@router.get("/users")
async def list_users(request: Request):
    await require_role(request, ["admin"])
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(100)
    for u in users:
        u["id"] = str(u.pop("_id", "")) if "_id" in u else u.get("id", "")
    return {"users": users}


@router.post("/users/{user_id}/role")
async def update_user_role(request: Request, user_id: str):
    await require_role(request, ["admin"])
    body = await request.json()
    role = body.get("role")
    if role not in ["admin", "operator", "engineer"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    from bson import ObjectId
    result = await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"role": role}})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Role updated"}


@router.get("/agents")
async def list_agents(request: Request):
    await get_current_user(request)
    agents = await db.agent_registrations.find({}, {"_id": 0}).to_list(100)
    return {"agents": agents}


@router.get("/stats")
async def get_platform_stats(request: Request):
    await get_current_user(request)
    return {
        "devices": await db.devices.count_documents({}),
        "events": await db.events.count_documents({}),
        "commands": await db.commands.count_documents({}),
        "connectors": await db.connectors.count_documents({}),
        "alerts": await db.alerts.count_documents({}),
        "users": await db.users.count_documents({}),
        "agents": await db.agent_registrations.count_documents({}),
        "tenants": await db.tenants.count_documents({}),
        "sites": await db.sites.count_documents({}),
    }
