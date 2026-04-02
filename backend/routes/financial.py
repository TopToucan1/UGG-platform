from fastapi import APIRouter, Request
from database import db
from auth import get_current_user
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/financial", tags=["financial"])


@router.get("")
async def list_financial_events(
    request: Request,
    event_type: str = None,
    device_id: str = None,
    player_id: str = None,
    site_id: str = None,
    min_amount: float = None,
    limit: int = 50,
    skip: int = 0,
):
    await get_current_user(request)
    query = {}
    if event_type:
        query["event_type"] = event_type
    if device_id:
        query["device_id"] = device_id
    if player_id:
        query["player_id"] = player_id
    if site_id:
        query["site_id"] = site_id
    if min_amount is not None:
        query["amount"] = {"$gte": min_amount}
    events = await db.financial_events.find(query, {"_id": 0}).sort("occurred_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.financial_events.count_documents(query)
    return {"events": events, "total": total}


@router.get("/summary")
async def financial_summary(request: Request):
    await get_current_user(request)
    now = datetime.now(timezone.utc)
    h24 = (now - timedelta(hours=24)).isoformat()

    # Overall totals
    types = ["wager", "payout", "voucher_in", "voucher_out", "bill_in", "jackpot", "bonus", "handpay"]
    totals = {}
    for t in types:
        pipeline = [
            {"$match": {"event_type": t}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        ]
        result = await db.financial_events.aggregate(pipeline).to_list(1)
        totals[t] = {"total": round(result[0]["total"], 2) if result else 0, "count": result[0]["count"] if result else 0}

    # 24h totals
    totals_24h = {}
    for t in types:
        pipeline = [
            {"$match": {"event_type": t, "occurred_at": {"$gte": h24}}},
            {"$group": {"_id": None, "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        ]
        result = await db.financial_events.aggregate(pipeline).to_list(1)
        totals_24h[t] = {"total": round(result[0]["total"], 2) if result else 0, "count": result[0]["count"] if result else 0}

    # Net win/loss = payouts + jackpots + handpays + bonuses - wagers
    coin_in = totals.get("wager", {}).get("total", 0) + totals.get("bill_in", {}).get("total", 0) + totals.get("voucher_in", {}).get("total", 0)
    coin_out = totals.get("payout", {}).get("total", 0) + totals.get("jackpot", {}).get("total", 0) + totals.get("handpay", {}).get("total", 0) + totals.get("bonus", {}).get("total", 0) + totals.get("voucher_out", {}).get("total", 0)
    house_hold = round(coin_in - coin_out, 2)

    return {
        "totals": totals,
        "totals_24h": totals_24h,
        "coin_in": round(coin_in, 2),
        "coin_out": round(coin_out, 2),
        "house_hold": house_hold,
        "hold_percentage": round((house_hold / coin_in * 100) if coin_in > 0 else 0, 2),
    }


@router.get("/charts")
async def financial_charts(request: Request):
    await get_current_user(request)
    now = datetime.now(timezone.utc)

    # Hourly revenue (last 24h)
    hourly = []
    for i in range(24):
        start = (now - timedelta(hours=i + 1)).isoformat()
        end = (now - timedelta(hours=i)).isoformat()
        label = (now - timedelta(hours=i)).strftime("%H:00")
        wager_pipe = [{"$match": {"event_type": "wager", "occurred_at": {"$gte": start, "$lt": end}}}, {"$group": {"_id": None, "t": {"$sum": "$amount"}}}]
        payout_pipe = [{"$match": {"event_type": {"$in": ["payout", "jackpot", "bonus", "handpay"]}, "occurred_at": {"$gte": start, "$lt": end}}}, {"$group": {"_id": None, "t": {"$sum": "$amount"}}}]
        w = await db.financial_events.aggregate(wager_pipe).to_list(1)
        p = await db.financial_events.aggregate(payout_pipe).to_list(1)
        wager_total = round(w[0]["t"], 2) if w else 0
        payout_total = round(p[0]["t"], 2) if p else 0
        hourly.append({"hour": label, "wagers": wager_total, "payouts": payout_total, "hold": round(wager_total - payout_total, 2)})
    hourly.reverse()

    # By game title (top 10)
    game_pipe = [
        {"$match": {"event_type": "wager"}},
        {"$group": {"_id": "$game_title", "total_wagered": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total_wagered": -1}},
        {"$limit": 10},
    ]
    game_data = await db.financial_events.aggregate(game_pipe).to_list(10)
    by_game = [{"name": g["_id"], "wagered": round(g["total_wagered"], 2), "count": g["count"]} for g in game_data]

    # By site
    site_pipe = [
        {"$match": {"event_type": "wager"}},
        {"$group": {"_id": "$site_name", "total": {"$sum": "$amount"}}},
        {"$sort": {"total": -1}},
    ]
    site_data = await db.financial_events.aggregate(site_pipe).to_list(10)
    by_site = [{"name": s["_id"] or "Unknown", "value": round(s["total"], 2)} for s in site_data]

    # Event type breakdown
    type_pipe = [
        {"$group": {"_id": "$event_type", "total": {"$sum": "$amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}},
    ]
    type_data = await db.financial_events.aggregate(type_pipe).to_list(20)
    by_type = [{"name": t["_id"], "total": round(t["total"], 2), "count": t["count"]} for t in type_data]

    return {
        "hourly_revenue": hourly,
        "by_game": by_game,
        "by_site": by_site,
        "by_type": by_type,
    }


@router.get("/types")
async def get_financial_types(request: Request):
    await get_current_user(request)
    types = await db.financial_events.distinct("event_type")
    return {"types": sorted(types)}
