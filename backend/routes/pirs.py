"""
UGG PIRS — Players Intelligence Rewards System.
AI-driven churn scoring, POC bonusing, rules engine, player profiles.
Integrated as a module inside UGG.
"""
from fastapi import APIRouter, Request, HTTPException
from database import db
from auth import get_current_user
import uuid
import random
import math
from datetime import datetime, timezone, timedelta

router = APIRouter(prefix="/api/pirs", tags=["pirs"])

# ══════════════════════════════════════════════════
# CHURN SCORING ENGINE
# ══════════════════════════════════════════════════

SCORE_BANDS = [
    {"min": 80, "max": 100, "segment": "elite_churner", "label": "Elite Churner", "max_daily_poc": 50, "poc_mult": 1.5},
    {"min": 65, "max": 79, "segment": "high_churner", "label": "High Value Churner", "max_daily_poc": 35, "poc_mult": 1.2},
    {"min": 50, "max": 64, "segment": "mid_churner", "label": "Mid Value Churner", "max_daily_poc": 20, "poc_mult": 1.0},
    {"min": 35, "max": 49, "segment": "developing", "label": "Developing Player", "max_daily_poc": 10, "poc_mult": 0.8},
    {"min": 20, "max": 34, "segment": "casual", "label": "Casual Player", "max_daily_poc": 5, "poc_mult": 0.5},
    {"min": 0, "max": 19, "segment": "low_value", "label": "Low Value / New", "max_daily_poc": 5, "poc_mult": 0.3},
]

TIERS = [
    {"id": "bronze", "name": "Bronze", "min_score": 0, "poc_multiplier": 1.0, "benefits": ["Basic POC bonuses"]},
    {"id": "silver", "name": "Silver", "min_score": 35, "poc_multiplier": 1.15, "benefits": ["Enhanced POC", "Birthday bonus"]},
    {"id": "gold", "name": "Gold", "min_score": 55, "poc_multiplier": 1.3, "benefits": ["Premium POC", "Birthday + Anniversary", "Priority support"]},
    {"id": "platinum", "name": "Platinum", "min_score": 70, "poc_multiplier": 1.5, "benefits": ["Maximum POC", "All bonuses", "Dedicated host", "Exclusive events"]},
    {"id": "diamond", "name": "Diamond", "min_score": 85, "poc_multiplier": 2.0, "benefits": ["Elite POC", "All benefits", "Custom offers", "VIP everything"]},
]


def calculate_churn_score(profile: dict) -> float:
    play_back = profile.get("play_back_rate", 0.5)
    cash_out = profile.get("cash_out_rate", 0.5)
    coin_ratio = min(profile.get("coin_in_to_loss_ratio", 1), 20) / 20
    session_ext = profile.get("session_extension_rate", 0.3)
    visit_freq = min(profile.get("visits_30d", 0), 30) / 30
    poc_response = profile.get("poc_response_rate", 0.5)
    recency = max(0, 1 - profile.get("days_since_last_visit", 30) / 90)

    raw = (play_back * 0.25 + (1 - cash_out) * 0.20 + coin_ratio * 0.15 +
           session_ext * 0.10 + visit_freq * 0.10 + poc_response * 0.10 + recency * 0.10) * 100

    # Boosters
    if profile.get("coin_in_30d", 0) > 5000:
        raw = min(raw * 1.05, 100)
    if profile.get("days_since_last_visit", 30) <= 3:
        raw = min(raw * 1.03, 100)
    if profile.get("days_since_last_visit", 30) > 30:
        raw *= 0.90
    return round(min(max(raw, 0), 100), 2)


def calculate_lapse_risk(profile: dict) -> float:
    days_since = profile.get("days_since_last_visit", 0)
    avg_gap = profile.get("avg_days_between_visits", 7) or 7
    ratio = days_since / avg_gap
    if ratio < 1.0: return 0
    elif ratio < 1.5: return min((ratio - 1) * 40, 20)
    elif ratio < 2.0: return min(20 + (ratio - 1.5) * 60, 50)
    elif ratio < 3.0: return min(50 + (ratio - 2) * 30, 80)
    else: return min(80 + (ratio - 3) * 10, 100)


def get_segment(score: float) -> dict:
    for band in SCORE_BANDS:
        if band["min"] <= score <= band["max"]:
            return band
    return SCORE_BANDS[-1]


def get_tier(score: float) -> dict:
    tier = TIERS[0]
    for t in TIERS:
        if score >= t["min_score"]:
            tier = t
    return tier


# ══════════════════════════════════════════════════
# PLAYER PROFILES
# ══════════════════════════════════════════════════

@router.get("/players")
async def list_pirs_players(request: Request, segment: str = None, min_score: float = None, limit: int = 50):
    await get_current_user(request)
    query = {}
    if segment:
        query["segment_code"] = segment
    if min_score is not None:
        query["churn_score"] = {"$gte": min_score}
    players = await db.pirs_players.find(query, {"_id": 0}).sort("churn_score", -1).limit(limit).to_list(limit)
    return {"players": players, "total": len(players)}


@router.get("/players/{player_id}")
async def get_pirs_player(request: Request, player_id: str):
    await get_current_user(request)
    player = await db.pirs_players.find_one({"player_id": player_id}, {"_id": 0})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    # Get recent POC awards
    awards = await db.poc_awards.find({"player_id": player_id}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    player["recent_awards"] = awards
    # Get recent sessions
    sessions = await db.player_sessions.find({"player_id": player_id}, {"_id": 0}).sort("card_in_at", -1).limit(10).to_list(10)
    player["recent_sessions"] = sessions
    return player


@router.get("/players/{player_id}/recommendations")
async def get_player_recommendations(request: Request, player_id: str):
    await get_current_user(request)
    player = await db.pirs_players.find_one({"player_id": player_id}, {"_id": 0})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    score = player.get("churn_score", 0)
    lapse = player.get("lapse_risk", 0)
    recs = []
    if score >= 70 and player.get("status") == "active_session":
        recs.append({"type": "IMMEDIATE_POC", "priority": "HIGH", "action": f"Send ${min(score * 0.3, 25):.0f} POC now — Elite player active", "player_id": player_id})
    if lapse >= 50:
        recs.append({"type": "LAPSE_PREVENTION", "priority": "HIGH" if lapse >= 70 else "MEDIUM", "action": f"Send ${15:.0f} reactivation POC — {lapse:.0f}% lapse risk", "player_id": player_id})
    if score >= 60 and player.get("poc_roi_lifetime", 0) > 10:
        recs.append({"type": "INCREASE_INVESTMENT", "priority": "MEDIUM", "action": f"Increase POC tier — current ROI is {player.get('poc_roi_lifetime', 0):.1f}:1", "player_id": player_id})
    if not recs:
        recs.append({"type": "MONITOR", "priority": "LOW", "action": "Continue monitoring — no action needed", "player_id": player_id})
    return {"recommendations": recs, "churn_score": score, "lapse_risk": lapse}


# ══════════════════════════════════════════════════
# RULES ENGINE + POC AWARDS
# ══════════════════════════════════════════════════

DEFAULT_RULES = [
    {"id": "CARD_IN_WELCOME", "name": "Welcome Bonus", "trigger": "card_in", "condition_churn_min": 70, "poc_fixed": 10, "max_per_day": 1, "cooldown_min": 480, "is_active": True},
    {"id": "MILESTONE_CI_100", "name": "$100 Coin-In Milestone", "trigger": "coin_in_milestone", "condition_coin_in": 10000, "poc_fixed": 10, "max_per_session": 1, "is_active": True},
    {"id": "MILESTONE_CI_250", "name": "$250 Coin-In Milestone", "trigger": "coin_in_milestone", "condition_coin_in": 25000, "poc_fixed": 15, "max_per_session": 1, "is_active": True},
    {"id": "MILESTONE_CI_500", "name": "$500 Coin-In Milestone", "trigger": "coin_in_milestone", "condition_coin_in": 50000, "poc_fixed": 20, "max_per_session": 1, "is_active": True},
    {"id": "SESSION_45MIN", "name": "45-Min Session Bonus", "trigger": "session_duration", "condition_mins": 45, "condition_churn_min": 60, "poc_fixed": 10, "max_per_session": 1, "is_active": True},
    {"id": "SESSION_90MIN", "name": "90-Min Session Bonus", "trigger": "session_duration", "condition_mins": 90, "condition_churn_min": 70, "poc_fixed": 20, "max_per_session": 1, "is_active": True},
    {"id": "POST_WIN_RETAIN", "name": "Post-Win Retention", "trigger": "post_win_playback", "condition_churn_min": 65, "poc_fixed": 10, "max_per_session": 2, "is_active": True},
    {"id": "LAPSE_PREVENTION", "name": "Lapse Prevention", "trigger": "lapse_risk", "condition_lapse_min": 70, "poc_fixed": 15, "max_per_day": 1, "is_active": True},
    {"id": "RETURN_VISIT_7D", "name": "7-Day Return Visit", "trigger": "return_visit", "condition_days_absent": 7, "poc_fixed": 10, "max_per_day": 1, "is_active": True},
    {"id": "CHURN_SCORE_80", "name": "Churn Score 80 Reward", "trigger": "churn_threshold", "condition_churn_min": 80, "poc_fixed": 20, "max_per_day": 1, "is_active": True},
]


@router.get("/rules")
async def list_rules(request: Request):
    await get_current_user(request)
    rules = await db.pirs_rules.find({}, {"_id": 0}).to_list(100)
    if not rules:
        # Seed default rules
        for r in DEFAULT_RULES:
            r["created_at"] = datetime.now(timezone.utc).isoformat()
            await db.pirs_rules.insert_one(r)
        rules = DEFAULT_RULES
    return {"rules": rules}


@router.post("/rules")
async def create_rule(request: Request):
    user = await get_current_user(request)
    body = await request.json()
    rule = {**body, "id": body.get("id", str(uuid.uuid4())), "is_active": True, "created_by": user.get("email"), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.pirs_rules.insert_one(rule)
    rule.pop("_id", None)
    return rule


@router.post("/rules/{rule_id}/toggle")
async def toggle_rule(request: Request, rule_id: str):
    await get_current_user(request)
    rule = await db.pirs_rules.find_one({"id": rule_id})
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    new_state = not rule.get("is_active", True)
    await db.pirs_rules.update_one({"id": rule_id}, {"$set": {"is_active": new_state}})
    return {"id": rule_id, "is_active": new_state}


@router.post("/poc/award")
async def award_poc(request: Request):
    """Manually trigger a POC award for a player."""
    user = await get_current_user(request)
    body = await request.json()
    player_id = body.get("player_id")
    amount = body.get("amount", 10)
    trigger = body.get("trigger_type", "campaign_manual")
    message = body.get("message", f"You've earned ${amount:.2f} in Play Only Credits!")

    player = await db.pirs_players.find_one({"player_id": player_id}, {"_id": 0})
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    # Apply tier multiplier
    tier = get_tier(player.get("churn_score", 0))
    final_amount = round(amount * tier["poc_multiplier"], 2)

    award = {
        "id": str(uuid.uuid4()), "player_id": player_id,
        "player_name": player.get("player_name", ""),
        "egm_id": player.get("last_egm_id"),
        "location_id": player.get("last_location_id"),
        "trigger_type": trigger, "rule_id": None,
        "poc_amount": final_amount, "poc_type": "play_only_credits",
        "churn_score_at_award": player.get("churn_score", 0),
        "tier_at_award": tier["name"], "tier_multiplier": tier["poc_multiplier"],
        "message_text": message.replace("{amount}", f"${final_amount:.2f}"),
        "delivery_status": "delivered",
        "delivered_at": datetime.now(timezone.utc).isoformat(),
        "awarded_by": user.get("email"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.poc_awards.insert_one(award)
    award.pop("_id", None)

    # Update player POC totals
    await db.pirs_players.update_one({"player_id": player_id}, {"$inc": {"total_poc_awarded": final_amount, "poc_awards_count": 1}})

    # Send to device messaging
    if player.get("last_egm_id"):
        await db.device_messages.insert_one({
            "id": str(uuid.uuid4()), "device_id": player["last_egm_id"],
            "message_text": award["message_text"], "message_type": "PROMO",
            "display_duration_seconds": 15, "display_position": "CENTER",
            "background_color": "#00D97E", "text_color": "#FFFFFF",
            "priority": "HIGH",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "sent_by": "PIRS", "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "PENDING",
        })

    return award


@router.get("/poc/history")
async def get_poc_history(request: Request, player_id: str = None, limit: int = 50):
    await get_current_user(request)
    query = {}
    if player_id:
        query["player_id"] = player_id
    awards = await db.poc_awards.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    total_poc = sum(a.get("poc_amount", 0) for a in awards)
    return {"awards": awards, "total_poc_awarded": total_poc, "count": len(awards)}


# ══════════════════════════════════════════════════
# FLEET OVERVIEW + ANALYTICS
# ══════════════════════════════════════════════════

@router.get("/dashboard")
async def pirs_dashboard(request: Request):
    await get_current_user(request)
    total_players = await db.pirs_players.count_documents({})
    active_now = await db.pirs_players.count_documents({"status": "active_session"})

    # Score distribution
    dist = []
    for band in SCORE_BANDS:
        c = await db.pirs_players.count_documents({"churn_score": {"$gte": band["min"], "$lte": band["max"]}})
        dist.append({"segment": band["segment"], "label": band["label"], "count": c, "min": band["min"], "max": band["max"]})

    # Totals
    agg = await db.pirs_players.aggregate([{"$group": {"_id": None, "total_coin_in": {"$sum": "$lifetime_coin_in"}, "avg_score": {"$avg": "$churn_score"}, "total_poc": {"$sum": "$total_poc_awarded"}}}]).to_list(1)
    stats = agg[0] if agg else {}

    # Today's POC
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_poc = await db.poc_awards.aggregate([{"$match": {"created_at": {"$gte": today}}}, {"$group": {"_id": None, "total": {"$sum": "$poc_amount"}, "count": {"$sum": 1}}}]).to_list(1)
    today_stats = today_poc[0] if today_poc else {}

    # Lapse risks
    at_risk = await db.pirs_players.count_documents({"lapse_risk": {"$gte": 50}})

    # Top players
    top = await db.pirs_players.find({}, {"_id": 0}).sort("churn_score", -1).limit(10).to_list(10)

    # Recent awards
    recent = await db.poc_awards.find({}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)

    return {
        "total_players": total_players, "active_now": active_now,
        "avg_churn_score": round(stats.get("avg_score") or 0, 1),
        "total_lifetime_coin_in": stats.get("total_coin_in", 0),
        "total_poc_awarded": stats.get("total_poc", 0),
        "poc_today": today_stats.get("total", 0), "poc_today_count": today_stats.get("count", 0),
        "at_risk_players": at_risk,
        "score_distribution": dist,
        "top_players": top,
        "recent_awards": recent,
        "tiers": TIERS,
    }


@router.get("/leaderboard")
async def pirs_leaderboard(request: Request, limit: int = 20):
    await get_current_user(request)
    players = await db.pirs_players.find({}, {"_id": 0}).sort("churn_score", -1).limit(limit).to_list(limit)
    return {"leaderboard": players}


@router.get("/analytics/roi")
async def pirs_roi(request: Request, days: int = 30):
    await get_current_user(request)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    poc_agg = await db.poc_awards.aggregate([{"$match": {"created_at": {"$gte": cutoff}}}, {"$group": {"_id": None, "total_poc": {"$sum": "$poc_amount"}, "count": {"$sum": 1}}}]).to_list(1)
    poc = poc_agg[0] if poc_agg else {}
    total_poc = poc.get("total_poc", 0)
    # Estimate coin-in generated (simulated — production would track actual)
    estimated_coin_in = total_poc * random.uniform(8, 18)
    roi = round(estimated_coin_in / total_poc, 1) if total_poc > 0 else 0
    return {"period_days": days, "total_poc": total_poc, "awards_count": poc.get("count", 0), "estimated_coin_in_from_poc": round(estimated_coin_in, 2), "roi": roi, "target_roi": 10}


@router.get("/segments")
async def get_segments(request: Request):
    await get_current_user(request)
    return {"segments": SCORE_BANDS, "tiers": TIERS}


# ══════════════════════════════════════════════════
# SEED PIRS PLAYER DATA
# ══════════════════════════════════════════════════

PLAYER_NAMES = ["James R.", "Maria S.", "David T.", "Sarah M.", "Michael L.", "Linda W.", "Robert K.", "Jennifer B.", "William J.", "Patricia P.", "Carlos G.", "Yuki F.", "Ahmed D.", "Olga H.", "Wei C.", "Anna V.", "Thomas N.", "Elena Q.", "Marcus A.", "Diana Z."]

async def seed_pirs():
    if await db.pirs_players.count_documents({}) > 0:
        return
    import logging
    logging.getLogger(__name__).info("Seeding PIRS player data...")

    now = datetime.now(timezone.utc)
    players = []
    for i in range(60):
        name = PLAYER_NAMES[i % len(PLAYER_NAMES)]
        coin_in = random.randint(500, 150000)
        play_back = round(random.uniform(0.1, 0.98), 3)
        cash_out = round(1 - play_back + random.uniform(-0.1, 0.1), 3)
        cash_out = max(0.02, min(0.95, cash_out))
        visits = random.randint(3, 200)
        days_since = random.randint(0, 45)
        sessions_30d = random.randint(0, 30)

        profile = {
            "play_back_rate": play_back, "cash_out_rate": cash_out,
            "coin_in_to_loss_ratio": round(coin_in / max(coin_in * (1 - play_back), 1), 2),
            "session_extension_rate": round(random.uniform(0.1, 0.9), 3),
            "visits_30d": sessions_30d, "days_since_last_visit": days_since,
            "poc_response_rate": round(random.uniform(0.3, 0.95), 3),
            "coin_in_30d": random.randint(200, 20000),
            "avg_days_between_visits": round(random.uniform(2, 20), 1),
        }
        score = calculate_churn_score(profile)
        lapse = calculate_lapse_risk(profile)
        segment = get_segment(score)
        tier = get_tier(score)

        player = {
            "player_id": f"PL-{30000 + i}", "account_number": f"ACC-{100000 + i}",
            "player_name": name, "email": f"player{i}@email.com",
            "enrollment_date": (now - timedelta(days=random.randint(30, 1000))).isoformat(),
            "tier_id": tier["id"], "tier_name": tier["name"],
            "status": random.choice(["active_session", "idle", "idle", "idle"]),
            "churn_score": score, "churn_score_prev": round(score + random.uniform(-10, 10), 2),
            "churn_score_trend": random.choice(["rising", "stable", "declining"]),
            "play_back_rate": play_back, "cash_out_rate": cash_out,
            "lapse_risk": round(lapse, 1),
            "segment_code": segment["segment"], "segment_label": segment["label"],
            "lifetime_coin_in": coin_in,
            "coin_in_30d": profile["coin_in_30d"],
            "avg_coin_in_per_session": round(coin_in / max(visits, 1), 2),
            "lifetime_visits": visits, "visits_30d": sessions_30d,
            "days_since_last_visit": days_since,
            "avg_session_length_mins": random.randint(10, 180),
            "avg_bet_size": round(random.uniform(0.25, 25.0), 2),
            "preferred_denomination": random.choice([0.01, 0.05, 0.25, 1.00, 5.00]),
            "total_poc_awarded": round(random.uniform(0, 500), 2),
            "poc_awards_count": random.randint(0, 50),
            "poc_response_rate": profile["poc_response_rate"],
            "poc_roi_lifetime": round(random.uniform(1, 25), 1),
            "last_egm_id": None, "last_location_id": None,
            "percentile_rank": round(random.uniform(1, 100), 1),
            "ltv_projection_90d": round(random.uniform(100, 5000), 2),
            "created_at": now.isoformat(),
        }
        players.append(player)

    await db.pirs_players.insert_many(players)

    # Seed some POC awards
    awards = []
    triggers = ["milestone_coinin", "session_length", "churn_threshold", "card_in_welcome", "return_visit", "post_win_retention", "campaign_manual"]
    for _ in range(100):
        p = random.choice(players)
        awards.append({
            "id": str(uuid.uuid4()), "player_id": p["player_id"], "player_name": p["player_name"],
            "trigger_type": random.choice(triggers),
            "poc_amount": random.choice([5, 10, 15, 20, 25, 30, 50]),
            "poc_type": "play_only_credits",
            "churn_score_at_award": p["churn_score"], "tier_at_award": p["tier_name"],
            "delivery_status": random.choice(["delivered", "delivered", "delivered", "pending"]),
            "message_text": f"You've earned Play Only Credits!", "awarded_by": "system",
            "created_at": (now - timedelta(hours=random.randint(0, 720))).isoformat(),
        })
    await db.poc_awards.insert_many(awards)

    await db.pirs_players.create_index("churn_score")
    await db.pirs_players.create_index("segment_code")
    await db.pirs_players.create_index("player_id", unique=True)
    logging.getLogger(__name__).info(f"Seeded PIRS: {len(players)} players, {len(awards)} POC awards")
