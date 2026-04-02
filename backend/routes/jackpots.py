from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/jackpots", tags=["jackpots"])


@router.get("")
async def list_jackpots(request: Request, status: str = None, site_id: str = None, jp_type: str = None):
    await get_current_user(request)
    query = {}
    if status:
        query["status"] = status
    if site_id:
        query["site_id"] = site_id
    if jp_type:
        query["type"] = jp_type
    jackpots = await db.progressive_jackpots.find(query, {"_id": 0}).sort("current_amount", -1).to_list(100)
    total = await db.progressive_jackpots.count_documents(query)
    return {"jackpots": jackpots, "total": total}


@router.get("/summary")
async def jackpot_summary(request: Request):
    await get_current_user(request)
    total = await db.progressive_jackpots.count_documents({})
    active = await db.progressive_jackpots.count_documents({"status": "active"})
    hit_pending = await db.progressive_jackpots.count_documents({"status": "hit_pending"})

    pipe = [{"$group": {"_id": None, "total_current": {"$sum": "$current_amount"}, "total_paid": {"$sum": "$total_paid"}, "total_hits": {"$sum": "$total_hits"}, "total_devices": {"$sum": "$linked_device_count"}}}]
    agg = await db.progressive_jackpots.aggregate(pipe).to_list(1)
    stats = agg[0] if agg else {}

    type_pipe = [{"$group": {"_id": "$type", "count": {"$sum": 1}, "total_amount": {"$sum": "$current_amount"}}}, {"$sort": {"total_amount": -1}}]
    type_dist = await db.progressive_jackpots.aggregate(type_pipe).to_list(10)

    return {
        "total_jackpots": total,
        "active": active,
        "hit_pending": hit_pending,
        "total_current_liability": round(stats.get("total_current", 0), 2),
        "total_paid_out": round(stats.get("total_paid", 0), 2),
        "total_hits": stats.get("total_hits", 0),
        "total_linked_devices": stats.get("total_devices", 0),
        "type_distribution": [{"name": t["_id"], "count": t["count"], "amount": round(t["total_amount"], 2)} for t in type_dist],
    }


@router.get("/history")
async def jackpot_history(request: Request, jackpot_id: str = None, limit: int = 50):
    await get_current_user(request)
    query = {}
    if jackpot_id:
        query["jackpot_id"] = jackpot_id
    hits = await db.jackpot_history.find(query, {"_id": 0}).sort("hit_at", -1).limit(limit).to_list(limit)
    total = await db.jackpot_history.count_documents(query)
    return {"hits": hits, "total": total}


@router.get("/charts")
async def jackpot_charts(request: Request):
    await get_current_user(request)
    # By site
    site_pipe = [{"$group": {"_id": "$site_name", "total": {"$sum": "$current_amount"}, "count": {"$sum": 1}}}, {"$sort": {"total": -1}}]
    by_site = await db.progressive_jackpots.aggregate(site_pipe).to_list(10)

    # Hit history timeline (last 30 days, per day)
    now = datetime.now(timezone.utc)
    daily_hits = []
    for i in range(30):
        start = (now - timedelta(days=i + 1)).isoformat()
        end = (now - timedelta(days=i)).isoformat()
        label = (now - timedelta(days=i)).strftime("%m/%d")
        count = await db.jackpot_history.count_documents({"hit_at": {"$gte": start, "$lt": end}})
        amount_pipe = [{"$match": {"hit_at": {"$gte": start, "$lt": end}}}, {"$group": {"_id": None, "t": {"$sum": "$hit_amount"}}}]
        amt = await db.jackpot_history.aggregate(amount_pipe).to_list(1)
        daily_hits.append({"date": label, "hits": count, "amount": round(amt[0]["t"], 2) if amt else 0})
    daily_hits.reverse()

    # Top jackpots by current amount
    top = await db.progressive_jackpots.find({}, {"_id": 0, "name": 1, "current_amount": 1, "base_amount": 1, "type": 1, "status": 1}).sort("current_amount", -1).limit(10).to_list(10)

    return {
        "by_site": [{"name": s["_id"] or "Unknown", "total": round(s["total"], 2), "count": s["count"]} for s in by_site],
        "daily_hits": daily_hits,
        "top_jackpots": top,
    }


@router.get("/{jackpot_id}")
async def get_jackpot(request: Request, jackpot_id: str):
    await get_current_user(request)
    jp = await db.progressive_jackpots.find_one({"id": jackpot_id}, {"_id": 0})
    if not jp:
        raise HTTPException(status_code=404, detail="Jackpot not found")
    hits = await db.jackpot_history.find({"jackpot_id": jackpot_id}, {"_id": 0}).sort("hit_at", -1).limit(20).to_list(20)
    jp["recent_hits"] = hits
    return jp
