from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from database import db
from auth import get_current_user
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/api/content-registry", tags=["content-registry"])


@router.post("/register")
async def register_content(request: Request):
    """Register an EGM game content package (SWF, HTML5, etc.)."""
    user = await get_current_user(request)
    body = await request.json()
    record = {
        "id": str(uuid.uuid4()),
        "name": body.get("name", "Unknown Content"),
        "content_type": body.get("content_type", "swf"),
        "version": body.get("version", "1.0.0"),
        "game_title": body.get("game_title", ""),
        "manufacturer": body.get("manufacturer", ""),
        "file_size": body.get("file_size", 0),
        "checksum": body.get("checksum", ""),
        "swf_version": body.get("swf_version"),
        "target_devices": body.get("target_devices", []),
        "deployed_device_count": body.get("deployed_device_count", 0),
        "status": "registered",
        "analysis_id": body.get("analysis_id"),
        "identifiers_count": body.get("identifiers_count", 0),
        "categories": body.get("categories", []),
        "registered_by": user.get("email"),
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "last_deployed_at": None,
    }
    await db.content_registry.insert_one(record)
    record.pop("_id", None)

    await db.audit_records.insert_one({
        "id": str(uuid.uuid4()), "tenant_id": None, "actor": user.get("email"),
        "action": "content.registered", "target_type": "content", "target_id": record["id"],
        "before": None, "after": {"name": record["name"], "version": record["version"]},
        "evidence_ref": record["id"], "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    return record


@router.get("")
async def list_content(request: Request, content_type: str = None, manufacturer: str = None, search: str = None, limit: int = 50):
    await get_current_user(request)
    query = {}
    if content_type:
        query["content_type"] = content_type
    if manufacturer:
        query["manufacturer"] = manufacturer
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"game_title": {"$regex": search, "$options": "i"}},
            {"manufacturer": {"$regex": search, "$options": "i"}},
        ]
    items = await db.content_registry.find(query, {"_id": 0}).sort("registered_at", -1).limit(limit).to_list(limit)
    total = await db.content_registry.count_documents(query)
    return {"content": items, "total": total}


@router.get("/stats")
async def content_stats(request: Request):
    await get_current_user(request)
    total = await db.content_registry.count_documents({})
    by_type = {}
    for t in await db.content_registry.distinct("content_type"):
        by_type[t] = await db.content_registry.count_documents({"content_type": t})
    by_mfr = {}
    for m in await db.content_registry.distinct("manufacturer"):
        if m:
            by_mfr[m] = await db.content_registry.count_documents({"manufacturer": m})
    analyses = await db.swf_analyses.count_documents({})
    return {"total_content": total, "by_type": by_type, "by_manufacturer": by_mfr, "total_analyses": analyses}


@router.get("/{content_id}")
async def get_content(request: Request, content_id: str):
    await get_current_user(request)
    item = await db.content_registry.find_one({"id": content_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Content not found")
    if item.get("analysis_id"):
        analysis = await db.swf_analyses.find_one({"id": item["analysis_id"]}, {"_id": 0})
        item["analysis"] = analysis
    return item


@router.post("/{content_id}/deploy")
async def deploy_content(request: Request, content_id: str):
    user = await get_current_user(request)
    body = await request.json()
    target_devices = body.get("target_devices", [])
    result = await db.content_registry.update_one(
        {"id": content_id},
        {"$set": {
            "status": "deployed",
            "target_devices": target_devices,
            "deployed_device_count": len(target_devices),
            "last_deployed_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    return {"message": f"Deployed to {len(target_devices)} devices"}
