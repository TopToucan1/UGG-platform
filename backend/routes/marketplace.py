from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/api/marketplace", tags=["marketplace"])


@router.get("")
async def list_marketplace(request: Request, category: str = None, search: str = None, price_model: str = None, certified: bool = None, limit: int = 50):
    await get_current_user(request)
    query = {}
    if category:
        query["category"] = category
    if price_model:
        query["price_model"] = price_model
    if certified is not None:
        query["certified"] = certified
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"vendor_name": {"$regex": search, "$options": "i"}},
        ]
    items = await db.marketplace_connectors.find(query, {"_id": 0}).sort("installs", -1).limit(limit).to_list(limit)
    total = await db.marketplace_connectors.count_documents(query)
    return {"connectors": items, "total": total}


@router.get("/categories")
async def get_categories(request: Request):
    await get_current_user(request)
    cats = await db.marketplace_connectors.distinct("category")
    counts = {}
    for c in cats:
        counts[c] = await db.marketplace_connectors.count_documents({"category": c})
    return {"categories": sorted(cats), "counts": counts}


@router.get("/{connector_id}")
async def get_marketplace_connector(request: Request, connector_id: str):
    await get_current_user(request)
    item = await db.marketplace_connectors.find_one({"id": connector_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Connector not found")
    return item


@router.post("/{connector_id}/install")
async def install_connector(request: Request, connector_id: str):
    user = await get_current_user(request)
    item = await db.marketplace_connectors.find_one({"id": connector_id})
    if not item:
        raise HTTPException(status_code=404, detail="Connector not found")
    await db.marketplace_connectors.update_one({"id": connector_id}, {"$inc": {"installs": 1}})
    install = {
        "id": str(uuid.uuid4()),
        "marketplace_connector_id": connector_id,
        "connector_name": item["name"],
        "installed_by": user.get("email"),
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "status": "installed",
    }
    await db.marketplace_installs.insert_one(install)
    install.pop("_id", None)
    return install


@router.get("/stats/summary")
async def marketplace_stats(request: Request):
    await get_current_user(request)
    total = await db.marketplace_connectors.count_documents({})
    certified = await db.marketplace_connectors.count_documents({"certified": True})
    free = await db.marketplace_connectors.count_documents({"price_model": "free"})
    vendors = len(await db.marketplace_connectors.distinct("vendor_name"))
    return {"total": total, "certified": certified, "free": free, "vendors": vendors}
