from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
import random
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/route-map", tags=["route-map"])

# Nevada venue coordinates (realistic lat/lng for seeded cities)
CITY_COORDS = {
    "Las Vegas": (36.1699, -115.1398), "Reno": (39.5296, -119.8138),
    "Carson City": (39.1638, -119.7674), "Henderson": (36.0395, -114.9817),
    "Sparks": (39.5349, -119.7527),
}


@router.get("/venues")
async def get_map_venues(request: Request):
    await get_current_user(request)
    retailers = await db.route_retailers.find({}, {"_id": 0}).to_list(500)
    devices = await db.devices.find({}, {"_id": 0, "id": 1, "retailer_id": 1, "status": 1}).to_list(500)

    # Build device counts per retailer
    retailer_devices = {}
    for d in devices:
        rid = d.get("retailer_id")
        if rid:
            if rid not in retailer_devices:
                retailer_devices[rid] = {"total": 0, "online": 0, "offline": 0, "error": 0}
            retailer_devices[rid]["total"] += 1
            retailer_devices[rid][d.get("status", "offline")] = retailer_devices[rid].get(d.get("status", "offline"), 0) + 1

    # Get NOR data per retailer
    nor_pipe = [
        {"$match": {"period_start": {"$gte": (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")}}},
        {"$group": {"_id": "$retailer_id", "nor": {"$sum": "$net_operating_revenue"}, "coin_in": {"$sum": "$coin_in"}}},
    ]
    nor_data = {r["_id"]: r for r in await db.route_nor_periods.aggregate(nor_pipe).to_list(500)}

    # Exception counts per retailer (via device mapping)
    exc_pipe = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$site_id", "count": {"$sum": 1}, "critical": {"$sum": {"$cond": [{"$eq": ["$severity", "CRITICAL"]}, 1, 0]}}}},
    ]
    exc_data = {e["_id"]: e for e in await db.route_exceptions.aggregate(exc_pipe).to_list(500)}

    venues = []
    for r in retailers:
        city = r.get("city", "Las Vegas")
        base_lat, base_lng = CITY_COORDS.get(city, (36.17, -115.14))
        # Add small random offset so venues don't stack
        lat = base_lat + random.uniform(-0.08, 0.08)
        lng = base_lng + random.uniform(-0.08, 0.08)

        dev_stats = retailer_devices.get(r["id"], {"total": 0, "online": 0})
        nor_info = nor_data.get(r["id"], {})
        exc_info = exc_data.get(r["id"], {})
        total = dev_stats["total"]
        online = dev_stats.get("online", 0)
        health = round(online / total * 100, 1) if total > 0 else 0

        venues.append({
            "id": r["id"],
            "name": r["name"],
            "address": r.get("address", ""),
            "city": city,
            "county": r.get("county", ""),
            "state": r.get("state", "NV"),
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "distributor_id": r.get("distributor_id"),
            "device_count": total,
            "online_count": online,
            "health_pct": health,
            "status": "healthy" if health >= 95 else "degraded" if health >= 80 else "critical",
            "today_nor": nor_info.get("nor", 0),
            "today_coin_in": nor_info.get("coin_in", 0),
            "exception_count": exc_info.get("count", 0),
            "critical_exceptions": exc_info.get("critical", 0),
        })

    # Estate summary
    total_devices = sum(v["device_count"] for v in venues)
    total_online = sum(v["online_count"] for v in venues)
    total_nor = sum(v["today_nor"] for v in venues)

    return {
        "venues": venues,
        "estate_summary": {
            "total_venues": len(venues),
            "total_devices": total_devices,
            "total_online": total_online,
            "online_pct": round(total_online / total_devices * 100, 1) if total_devices > 0 else 0,
            "today_nor": total_nor,
        },
    }


@router.get("/venues/{venue_id}")
async def get_venue_detail(request: Request, venue_id: str):
    await get_current_user(request)
    retailer = await db.route_retailers.find_one({"id": venue_id}, {"_id": 0})
    if not retailer:
        raise HTTPException(status_code=404, detail="Venue not found")
    devices = await db.devices.find({"retailer_id": venue_id}, {"_id": 0, "id": 1, "external_ref": 1, "status": 1, "manufacturer": 1, "model": 1}).to_list(50)
    exceptions = await db.route_exceptions.find({"site_id": venue_id, "is_active": True}, {"_id": 0}).to_list(20)
    return {"venue": retailer, "devices": devices, "exceptions": exceptions}
