from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/players", tags=["players"])


@router.get("/sessions")
async def list_sessions(
    request: Request,
    player_id: str = None,
    device_id: str = None,
    status: str = None,
    site_id: str = None,
    limit: int = 50,
    skip: int = 0,
):
    await get_current_user(request)
    query = {}
    if player_id:
        query["player_id"] = player_id
    if device_id:
        query["device_id"] = device_id
    if status:
        query["status"] = status
    if site_id:
        query["site_id"] = site_id
    sessions = await db.player_sessions.find(query, {"_id": 0}).sort("card_in_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await db.player_sessions.count_documents(query)
    return {"sessions": sessions, "total": total}


@router.get("/sessions/{session_id}")
async def get_session(request: Request, session_id: str):
    await get_current_user(request)
    session = await db.player_sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    # Get related financial events
    fin_events = await db.financial_events.find(
        {"player_id": session.get("player_id"), "device_id": session.get("device_id")},
        {"_id": 0}
    ).sort("occurred_at", -1).limit(50).to_list(50)
    session["financial_events"] = fin_events
    return session


@router.get("/summary")
async def player_summary(request: Request):
    await get_current_user(request)
    total_sessions = await db.player_sessions.count_documents({})
    active_sessions = await db.player_sessions.count_documents({"status": "active"})
    completed_sessions = await db.player_sessions.count_documents({"status": "completed"})

    # Unique players
    unique_players = len(await db.player_sessions.distinct("player_id"))

    # Aggregations
    agg_pipe = [{"$group": {
        "_id": None,
        "total_wagered": {"$sum": "$total_wagered"},
        "total_won": {"$sum": "$total_won"},
        "total_games": {"$sum": "$games_played"},
        "avg_duration": {"$avg": "$duration_minutes"},
        "total_loyalty": {"$sum": "$loyalty_points_earned"},
    }}]
    agg = await db.player_sessions.aggregate(agg_pipe).to_list(1)
    stats = agg[0] if agg else {}

    # Tier distribution
    tier_pipe = [{"$group": {"_id": "$player_tier", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    tiers = await db.player_sessions.aggregate(tier_pipe).to_list(10)
    tier_dist = [{"name": t["_id"], "value": t["count"]} for t in tiers]

    return {
        "total_sessions": total_sessions,
        "active_sessions": active_sessions,
        "completed_sessions": completed_sessions,
        "unique_players": unique_players,
        "total_wagered": round(stats.get("total_wagered", 0), 2),
        "total_won": round(stats.get("total_won", 0), 2),
        "total_games": stats.get("total_games", 0),
        "avg_duration_minutes": round(stats.get("avg_duration", 0), 1),
        "total_loyalty_points": stats.get("total_loyalty", 0),
        "tier_distribution": tier_dist,
    }


@router.get("/charts")
async def player_charts(request: Request):
    await get_current_user(request)
    now = datetime.now(timezone.utc)

    # Sessions over time (last 24h, per 2h blocks)
    sessions_timeline = []
    for i in range(12):
        start = (now - timedelta(hours=(i + 1) * 2)).isoformat()
        end = (now - timedelta(hours=i * 2)).isoformat()
        label = (now - timedelta(hours=i * 2)).strftime("%H:00")
        count = await db.player_sessions.count_documents({"card_in_at": {"$gte": start, "$lt": end}})
        sessions_timeline.append({"time": label, "sessions": count})
    sessions_timeline.reverse()

    # Top players by wagered
    top_pipe = [
        {"$group": {"_id": {"id": "$player_id", "name": "$player_name", "tier": "$player_tier"}, "total_wagered": {"$sum": "$total_wagered"}, "total_won": {"$sum": "$total_won"}, "sessions": {"$sum": 1}, "games": {"$sum": "$games_played"}}},
        {"$sort": {"total_wagered": -1}},
        {"$limit": 15},
    ]
    top_players = await db.player_sessions.aggregate(top_pipe).to_list(15)
    leaderboard = [{
        "player_id": p["_id"]["id"],
        "name": p["_id"]["name"],
        "tier": p["_id"]["tier"],
        "total_wagered": round(p["total_wagered"], 2),
        "total_won": round(p["total_won"], 2),
        "net": round(p["total_won"] - p["total_wagered"], 2),
        "sessions": p["sessions"],
        "games": p["games"],
    } for p in top_players]

    # Duration distribution
    dur_buckets = [
        {"label": "< 15 min", "min": 0, "max": 15},
        {"label": "15-30 min", "min": 15, "max": 30},
        {"label": "30-60 min", "min": 30, "max": 60},
        {"label": "1-2 hrs", "min": 60, "max": 120},
        {"label": "2-4 hrs", "min": 120, "max": 240},
        {"label": "4+ hrs", "min": 240, "max": 9999},
    ]
    duration_dist = []
    for b in dur_buckets:
        c = await db.player_sessions.count_documents({"duration_minutes": {"$gte": b["min"], "$lt": b["max"]}})
        duration_dist.append({"name": b["label"], "value": c})

    # Game popularity across sessions
    game_pipe = [{"$unwind": "$game_titles"}, {"$group": {"_id": "$game_titles", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 10}]
    games = await db.player_sessions.aggregate(game_pipe).to_list(10)
    game_popularity = [{"name": g["_id"], "value": g["count"]} for g in games]

    return {
        "sessions_timeline": sessions_timeline,
        "leaderboard": leaderboard,
        "duration_distribution": duration_dist,
        "game_popularity": game_popularity,
    }


@router.get("/active")
async def active_sessions(request: Request):
    await get_current_user(request)
    sessions = await db.player_sessions.find({"status": "active"}, {"_id": 0}).sort("card_in_at", -1).to_list(100)
    return {"sessions": sessions, "count": len(sessions)}
