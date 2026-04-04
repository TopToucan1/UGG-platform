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


# ══════════════════════════════════════════════════
# OPERATOR CONFIGURATION — Full control over rewards
# ══════════════════════════════════════════════════

DEFAULT_CONFIG = {
    "budget_daily_limit": 500,
    "budget_weekly_limit": 2500,
    "budget_monthly_limit": 10000,
    "budget_per_player_daily": 50,
    "budget_per_player_session": 25,
    "min_poc_amount": 5,
    "max_poc_amount": 100,
    "auto_rules_enabled": True,
    "auto_score_recalc_interval_min": 15,
    "auto_scale_rewards": True,
    "happy_hour_enabled": False,
    "happy_hour_start": "16:00",
    "happy_hour_end": "18:00",
    "happy_hour_multiplier": 1.5,
    "weekend_multiplier": 1.0,
    "new_player_welcome_poc": 10,
    "responsible_gambling_session_limit_min": 240,
}


@router.get("/config")
async def get_pirs_config(request: Request):
    await get_current_user(request)
    config = await db.pirs_config.find_one({"type": "global"}, {"_id": 0})
    if not config:
        config = {**DEFAULT_CONFIG, "type": "global", "updated_at": None}
        await db.pirs_config.insert_one(config)
        config.pop("_id", None)
    return config


@router.post("/config")
async def update_pirs_config(request: Request):
    """Operator updates reward configuration — budgets, amounts, schedules."""
    user = await get_current_user(request)
    body = await request.json()
    now = datetime.now(timezone.utc).isoformat()
    # Validate budget values
    if body.get("min_poc_amount", 1) < 1:
        raise HTTPException(status_code=400, detail="Minimum POC amount must be at least $1")
    if body.get("max_poc_amount", 100) > 500:
        raise HTTPException(status_code=400, detail="Maximum POC amount cannot exceed $500")
    if body.get("budget_daily_limit", 100) < 10:
        raise HTTPException(status_code=400, detail="Daily budget must be at least $10")

    update = {k: v for k, v in body.items() if k in DEFAULT_CONFIG}
    update["updated_at"] = now
    update["updated_by"] = user.get("email")
    await db.pirs_config.update_one({"type": "global"}, {"$set": update}, upsert=True)

    # Audit
    await db.audit_records.insert_one({"id": str(uuid.uuid4()), "tenant_id": None, "actor": user.get("email"), "action": "pirs.config_updated", "target_type": "pirs_config", "target_id": "global", "before": None, "after": update, "evidence_ref": None, "timestamp": now})
    return {"message": "PIRS configuration updated", "config": update}


# ══════════════════════════════════════════════════
# EDITABLE RULES — Operators create/edit/delete
# ══════════════════════════════════════════════════

@router.post("/rules/create")
async def create_custom_rule(request: Request):
    """Operator creates a fully custom reward rule."""
    user = await get_current_user(request)
    body = await request.json()
    rule = {
        "id": str(uuid.uuid4()),
        "name": body.get("name", "Custom Rule"),
        "trigger": body.get("trigger", "coin_in_milestone"),
        "condition_churn_min": body.get("condition_churn_min"),
        "condition_churn_max": body.get("condition_churn_max"),
        "condition_coin_in": body.get("condition_coin_in"),
        "condition_mins": body.get("condition_mins"),
        "condition_lapse_min": body.get("condition_lapse_min"),
        "condition_days_absent": body.get("condition_days_absent"),
        "condition_time_window": body.get("condition_time_window"),  # "weekdays", "weekends", "happy_hour", "always"
        "poc_fixed": body.get("poc_fixed", 10),
        "poc_percent_of_loss": body.get("poc_percent_of_loss"),  # e.g., 0.05 = 5% of session loss
        "max_per_day": body.get("max_per_day", 1),
        "max_per_session": body.get("max_per_session"),
        "cooldown_min": body.get("cooldown_min", 60),
        "message_template": body.get("message_template", "You've earned ${amount} in Play Only Credits!"),
        "is_active": True,
        "is_custom": True,
        "created_by": user.get("email"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.pirs_rules.insert_one(rule)
    rule.pop("_id", None)
    return rule


@router.put("/rules/{rule_id}")
async def update_rule(request: Request, rule_id: str):
    """Operator edits any rule — change amounts, conditions, schedules."""
    user = await get_current_user(request)
    body = await request.json()
    allowed_fields = ["name", "trigger", "condition_churn_min", "condition_churn_max", "condition_coin_in", "condition_mins", "condition_lapse_min", "condition_days_absent", "condition_time_window", "poc_fixed", "poc_percent_of_loss", "max_per_day", "max_per_session", "cooldown_min", "message_template", "is_active"]
    update = {k: v for k, v in body.items() if k in allowed_fields}
    update["updated_at"] = datetime.now(timezone.utc).isoformat()
    update["updated_by"] = user.get("email")
    result = await db.pirs_rules.update_one({"id": rule_id}, {"$set": update})
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule updated", "rule_id": rule_id}


@router.delete("/rules/{rule_id}")
async def delete_rule(request: Request, rule_id: str):
    user = await get_current_user(request)
    result = await db.pirs_rules.delete_one({"id": rule_id, "is_custom": True})
    if result.deleted_count == 0:
        raise HTTPException(status_code=400, detail="Cannot delete system rules — toggle them off instead")
    return {"message": "Custom rule deleted"}


# ══════════════════════════════════════════════════
# AUTOMATIC RULE ENGINE — Runs rules against live players
# ══════════════════════════════════════════════════

@router.post("/engine/run")
async def run_pirs_engine(request: Request):
    """Execute all active rules against current player state. Awards POC automatically."""
    user = await get_current_user(request)
    config = await db.pirs_config.find_one({"type": "global"}, {"_id": 0}) or DEFAULT_CONFIG
    rules = await db.pirs_rules.find({"is_active": True}, {"_id": 0}).to_list(100)
    players = await db.pirs_players.find({}, {"_id": 0}).to_list(500)

    if not config.get("auto_rules_enabled", True):
        return {"message": "Auto rules disabled in config", "awards": 0}

    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    current_hour = now.hour
    is_weekend = now.weekday() >= 5
    is_happy_hour = config.get("happy_hour_enabled") and config.get("happy_hour_start", "16:00") <= now.strftime("%H:%M") <= config.get("happy_hour_end", "18:00")

    # Budget tracking
    today_spent_agg = await db.poc_awards.aggregate([{"$match": {"created_at": {"$gte": today}}}, {"$group": {"_id": None, "total": {"$sum": "$poc_amount"}}}]).to_list(1)
    today_spent = today_spent_agg[0]["total"] if today_spent_agg else 0
    budget_remaining = config.get("budget_daily_limit", 500) - today_spent

    awards_given = 0
    awards_skipped_budget = 0
    awards_skipped_cooldown = 0

    for player in players:
        pid = player["player_id"]
        score = player.get("churn_score", 0)
        lapse = player.get("lapse_risk", 0)
        tier = get_tier(score)

        # Per-player daily limit check
        player_today_agg = await db.poc_awards.aggregate([{"$match": {"player_id": pid, "created_at": {"$gte": today}}}, {"$group": {"_id": None, "total": {"$sum": "$poc_amount"}}}]).to_list(1)
        player_today = player_today_agg[0]["total"] if player_today_agg else 0
        player_budget_remaining = config.get("budget_per_player_daily", 50) - player_today

        for rule in rules:
            # Time window check
            tw = rule.get("condition_time_window", "always")
            if tw == "weekdays" and is_weekend:
                continue
            if tw == "weekends" and not is_weekend:
                continue
            if tw == "happy_hour" and not is_happy_hour:
                continue

            # Churn score check
            if rule.get("condition_churn_min") and score < rule["condition_churn_min"]:
                continue
            if rule.get("condition_churn_max") and score > rule["condition_churn_max"]:
                continue

            # Lapse risk check
            if rule.get("condition_lapse_min") and lapse < rule["condition_lapse_min"]:
                continue

            # Cooldown check
            cooldown = rule.get("cooldown_min", 60)
            last_award = await db.poc_awards.find_one({"player_id": pid, "rule_id": rule["id"]}, {"_id": 0, "created_at": 1})
            if last_award:
                try:
                    last_dt = datetime.fromisoformat(last_award["created_at"].replace("Z", "+00:00"))
                    if (now - last_dt).total_seconds() / 60 < cooldown:
                        awards_skipped_cooldown += 1
                        continue
                except (ValueError, TypeError):
                    pass

            # Max per day check
            if rule.get("max_per_day"):
                day_count = await db.poc_awards.count_documents({"player_id": pid, "rule_id": rule["id"], "created_at": {"$gte": today}})
                if day_count >= rule["max_per_day"]:
                    continue

            # Calculate POC amount
            poc = rule.get("poc_fixed", 10)
            if rule.get("poc_percent_of_loss"):
                session_loss = max(0, player.get("coin_in_30d", 0) - player.get("coin_in_30d", 0) * player.get("play_back_rate", 0.5))
                poc = max(poc, round(session_loss * rule["poc_percent_of_loss"], 2))

            # Apply tier multiplier
            poc = round(poc * tier["poc_multiplier"], 2)

            # Apply happy hour / weekend multiplier
            if is_happy_hour:
                poc = round(poc * config.get("happy_hour_multiplier", 1.5), 2)
            if is_weekend and config.get("weekend_multiplier", 1.0) != 1.0:
                poc = round(poc * config["weekend_multiplier"], 2)

            # Enforce limits
            poc = max(config.get("min_poc_amount", 5), min(poc, config.get("max_poc_amount", 100)))

            # Budget checks
            if poc > budget_remaining:
                awards_skipped_budget += 1
                continue
            if poc > player_budget_remaining:
                awards_skipped_budget += 1
                continue

            # Award!
            msg = rule.get("message_template", "You've earned ${amount} in Play Only Credits!").replace("{amount}", f"${poc:.2f}")
            award = {
                "id": str(uuid.uuid4()), "player_id": pid, "player_name": player.get("player_name", ""),
                "egm_id": player.get("last_egm_id"), "trigger_type": rule.get("trigger", "auto_rule"),
                "rule_id": rule["id"], "rule_name": rule.get("name", ""),
                "poc_amount": poc, "poc_type": "play_only_credits",
                "churn_score_at_award": score, "tier_at_award": tier["name"], "tier_multiplier": tier["poc_multiplier"],
                "message_text": msg, "delivery_status": "delivered",
                "delivered_at": now.isoformat(), "awarded_by": "PIRS_ENGINE",
                "created_at": now.isoformat(),
            }
            await db.poc_awards.insert_one(award)
            await db.pirs_players.update_one({"player_id": pid}, {"$inc": {"total_poc_awarded": poc, "poc_awards_count": 1}})
            budget_remaining -= poc
            player_budget_remaining -= poc
            awards_given += 1

            # Push to device messaging if player has active EGM
            if player.get("last_egm_id"):
                await db.device_messages.insert_one({
                    "id": str(uuid.uuid4()), "device_id": player["last_egm_id"],
                    "message_text": msg, "message_type": "PROMO",
                    "display_duration_seconds": 15, "display_position": "CENTER",
                    "background_color": "#FFD700", "text_color": "#070B14",
                    "priority": "HIGH",
                    "expires_at": (now + timedelta(hours=1)).isoformat(),
                    "sent_by": "PIRS_ENGINE", "sent_at": now.isoformat(), "status": "PENDING",
                })

            if budget_remaining <= 0:
                break
        if budget_remaining <= 0:
            break

    # Auto-recalculate scores if configured
    scores_updated = 0
    if config.get("auto_scale_rewards", True):
        for player in players:
            new_score = calculate_churn_score(player)
            new_lapse = calculate_lapse_risk(player)
            new_seg = get_segment(new_score)
            new_tier = get_tier(new_score)
            await db.pirs_players.update_one({"player_id": player["player_id"]}, {"$set": {
                "churn_score_prev": player.get("churn_score", 0),
                "churn_score": new_score, "lapse_risk": round(new_lapse, 1),
                "segment_code": new_seg["segment"], "segment_label": new_seg["label"],
                "tier_id": new_tier["id"], "tier_name": new_tier["name"],
                "churn_score_trend": "rising" if new_score > player.get("churn_score", 0) else "declining" if new_score < player.get("churn_score", 0) else "stable",
            }})
            scores_updated += 1

    return {
        "message": "PIRS engine run complete",
        "awards_given": awards_given,
        "awards_skipped_budget": awards_skipped_budget,
        "awards_skipped_cooldown": awards_skipped_cooldown,
        "budget_spent_today": today_spent + sum(1 for _ in range(awards_given)),
        "budget_remaining": budget_remaining,
        "players_evaluated": len(players),
        "rules_evaluated": len(rules),
        "scores_recalculated": scores_updated,
        "is_happy_hour": is_happy_hour,
        "is_weekend": is_weekend,
    }


@router.get("/engine/status")
async def engine_status(request: Request):
    await get_current_user(request)
    config = await db.pirs_config.find_one({"type": "global"}, {"_id": 0}) or DEFAULT_CONFIG
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    spent_agg = await db.poc_awards.aggregate([{"$match": {"created_at": {"$gte": today}}}, {"$group": {"_id": None, "total": {"$sum": "$poc_amount"}, "count": {"$sum": 1}}}]).to_list(1)
    spent = spent_agg[0] if spent_agg else {}
    active_rules = await db.pirs_rules.count_documents({"is_active": True})
    total_rules = await db.pirs_rules.count_documents({})
    return {
        "auto_enabled": config.get("auto_rules_enabled", True),
        "budget_daily": config.get("budget_daily_limit", 500),
        "budget_spent_today": spent.get("total", 0),
        "budget_remaining": config.get("budget_daily_limit", 500) - spent.get("total", 0),
        "awards_today": spent.get("count", 0),
        "active_rules": active_rules,
        "total_rules": total_rules,
        "config": config,
    }


# ══════════════════════════════════════════════════
# PLAYER RTP TRACKING + COMPENSATION ENGINE
# ══════════════════════════════════════════════════

@router.get("/rtp/below-threshold")
async def get_players_below_rtp(request: Request, threshold: float = 0.70, min_dollars_played: float = 100):
    """Find players whose actual RTP is below the threshold — candidates for compensation."""
    await get_current_user(request)
    # Calculate actual RTP per player from session data
    pipe = [
        {"$match": {"status": "completed"}},
        {"$group": {
            "_id": "$player_id",
            "player_name": {"$first": "$player_name"},
            "total_wagered": {"$sum": "$total_wagered"},
            "total_won": {"$sum": "$total_won"},
            "sessions": {"$sum": 1},
            "last_device": {"$last": "$device_ref"},
            "last_session": {"$last": "$card_in_at"},
        }},
        {"$match": {"total_wagered": {"$gte": min_dollars_played * 100}}},
    ]
    player_stats = await db.player_sessions.aggregate(pipe).to_list(500)

    below_threshold = []
    for ps in player_stats:
        wagered = ps.get("total_wagered", 0)
        won = ps.get("total_won", 0)
        if wagered <= 0:
            continue
        actual_rtp = won / wagered
        if actual_rtp < threshold:
            deficit_dollars = round((threshold * wagered - won) / 100, 2) if wagered > 100 else round(threshold * wagered - won, 2)
            # Get PIRS profile
            pirs = await db.pirs_players.find_one({"player_id": ps["_id"]}, {"_id": 0, "churn_score": 1, "tier_name": 1, "segment_label": 1, "lapse_risk": 1})
            # Check if already has pending compensation
            pending = await db.poc_wallet.find_one({"player_id": ps["_id"], "status": "PENDING", "trigger_type": "rtp_compensation"})

            below_threshold.append({
                "player_id": ps["_id"],
                "player_name": ps.get("player_name", ""),
                "total_wagered": round(wagered, 2),
                "total_won": round(won, 2),
                "actual_rtp": round(actual_rtp, 4),
                "expected_rtp": threshold,
                "rtp_gap": round(threshold - actual_rtp, 4),
                "rtp_pct": round(actual_rtp * 100, 1),
                "deficit_dollars": abs(deficit_dollars),
                "sessions": ps.get("sessions", 0),
                "last_device": ps.get("last_device"),
                "last_session": ps.get("last_session"),
                "churn_score": pirs.get("churn_score") if pirs else None,
                "tier": pirs.get("tier_name") if pirs else None,
                "lapse_risk": pirs.get("lapse_risk") if pirs else None,
                "has_pending_compensation": pending is not None,
                "suggested_poc": round(min(abs(deficit_dollars) * 0.10, 50), 2),
            })

    below_threshold.sort(key=lambda x: x["actual_rtp"])
    return {
        "players_below_rtp": below_threshold,
        "total_found": len(below_threshold),
        "threshold": threshold,
        "min_dollars_played": min_dollars_played,
        "avg_rtp_of_flagged": round(sum(p["actual_rtp"] for p in below_threshold) / len(below_threshold), 4) if below_threshold else 0,
    }


@router.get("/rtp/player/{player_id}")
async def get_player_rtp_detail(request: Request, player_id: str):
    """Detailed RTP analysis for a single player."""
    await get_current_user(request)
    sessions = await db.player_sessions.find({"player_id": player_id, "status": "completed"}, {"_id": 0}).sort("card_in_at", -1).to_list(100)
    if not sessions:
        return {"player_id": player_id, "sessions": 0, "actual_rtp": None, "message": "No completed sessions"}

    total_wagered = sum(s.get("total_wagered", 0) for s in sessions)
    total_won = sum(s.get("total_won", 0) for s in sessions)
    actual_rtp = total_won / total_wagered if total_wagered > 0 else 0

    # Per-session RTP breakdown
    session_rtps = []
    for s in sessions[:20]:
        sw = s.get("total_wagered", 0)
        swin = s.get("total_won", 0)
        session_rtps.append({
            "date": s.get("card_in_at", "")[:10],
            "wagered": round(sw, 2), "won": round(swin, 2),
            "rtp": round(swin / sw, 4) if sw > 0 else 0,
            "net": round(swin - sw, 2),
            "device": s.get("device_ref"),
            "duration_min": s.get("duration_minutes"),
        })

    # Rolling RTP over time
    running_w = 0
    running_won = 0
    rolling = []
    for s in reversed(sessions[:50]):
        running_w += s.get("total_wagered", 0)
        running_won += s.get("total_won", 0)
        if running_w > 0:
            rolling.append({"session": len(rolling) + 1, "rolling_rtp": round(running_won / running_w, 4)})

    # Wallet balance
    wallet = await db.poc_wallet.find({"player_id": player_id, "status": "PENDING"}, {"_id": 0}).to_list(10)
    pending_poc = sum(w.get("amount", 0) for w in wallet)

    return {
        "player_id": player_id,
        "total_sessions": len(sessions),
        "total_wagered": round(total_wagered, 2),
        "total_won": round(total_won, 2),
        "actual_rtp": round(actual_rtp, 4),
        "actual_rtp_pct": round(actual_rtp * 100, 1),
        "net_result": round(total_won - total_wagered, 2),
        "session_breakdown": session_rtps,
        "rolling_rtp": rolling,
        "pending_poc_balance": pending_poc,
        "pending_poc_items": wallet,
    }


# ══════════════════════════════════════════════════
# POC WALLET — Account-level pending credits
# ══════════════════════════════════════════════════

@router.post("/wallet/credit")
async def credit_player_wallet(request: Request):
    """
    Operator sends POC to a player's WALLET — not a specific EGM.
    POC sits waiting until the player's next card-in, then auto-delivers to that EGM.
    """
    user = await get_current_user(request)
    body = await request.json()
    player_id = body.get("player_id")
    amount = body.get("amount", 10)
    reason = body.get("reason", "operator_manual")
    message = body.get("message", f"You have ${amount:.2f} in Play Only Credits waiting! Card in to receive them.")
    expires_days = body.get("expires_days", 30)

    player = await db.pirs_players.find_one({"player_id": player_id}, {"_id": 0})
    if not player:
        raise HTTPException(status_code=400, detail="Player not found in PIRS")

    now = datetime.now(timezone.utc)
    wallet_entry = {
        "id": str(uuid.uuid4()),
        "player_id": player_id,
        "player_name": player.get("player_name", ""),
        "amount": amount,
        "reason": reason,
        "trigger_type": body.get("trigger_type", "operator_manual"),
        "message": message,
        "status": "PENDING",  # PENDING → DELIVERED → PLAYED → EXPIRED
        "expires_at": (now + timedelta(days=expires_days)).isoformat(),
        "credited_by": user.get("email"),
        "credited_at": now.isoformat(),
        "delivered_at": None,
        "delivered_to_egm": None,
    }
    await db.poc_wallet.insert_one(wallet_entry)
    wallet_entry.pop("_id", None)

    # Update player record
    await db.pirs_players.update_one(
        {"player_id": player_id},
        {"$inc": {"wallet_pending_poc": amount}},
    )

    return wallet_entry


@router.post("/wallet/compensate-rtp")
async def compensate_low_rtp(request: Request):
    """Operator sends RTP-compensation POC to flagged players' wallets."""
    user = await get_current_user(request)
    body = await request.json()
    player_id = body.get("player_id")
    amount = body.get("amount")  # operator decides the amount
    auto_amount = body.get("auto_calculate", False)

    player = await db.pirs_players.find_one({"player_id": player_id}, {"_id": 0})
    if not player:
        raise HTTPException(status_code=400, detail="Player not found")

    # If auto-calculate, compute 10% of RTP deficit
    if auto_amount or not amount:
        sessions = await db.player_sessions.find({"player_id": player_id, "status": "completed"}, {"_id": 0}).to_list(200)
        total_w = sum(s.get("total_wagered", 0) for s in sessions)
        total_won = sum(s.get("total_won", 0) for s in sessions)
        actual_rtp = total_won / total_w if total_w > 0 else 0
        deficit = (0.70 * total_w) - total_won
        amount = round(min(max(deficit * 0.10, 5), 100), 2) if deficit > 0 else 10

    now = datetime.now(timezone.utc)
    wallet_entry = {
        "id": str(uuid.uuid4()),
        "player_id": player_id,
        "player_name": player.get("player_name", ""),
        "amount": amount,
        "reason": "rtp_compensation",
        "trigger_type": "rtp_compensation",
        "message": f"We appreciate your loyalty! You have ${amount:.2f} in bonus credits waiting for your next visit.",
        "status": "PENDING",
        "expires_at": (now + timedelta(days=30)).isoformat(),
        "credited_by": user.get("email"),
        "credited_at": now.isoformat(),
        "delivered_at": None,
        "delivered_to_egm": None,
        "rtp_data": {"calculated": auto_amount or not body.get("amount")},
    }
    await db.poc_wallet.insert_one(wallet_entry)
    wallet_entry.pop("_id", None)
    await db.pirs_players.update_one({"player_id": player_id}, {"$inc": {"wallet_pending_poc": amount}})
    return wallet_entry


@router.get("/wallet/{player_id}")
async def get_player_wallet(request: Request, player_id: str):
    """Get a player's pending POC wallet balance."""
    await get_current_user(request)
    entries = await db.poc_wallet.find({"player_id": player_id}, {"_id": 0}).sort("credited_at", -1).to_list(50)
    pending = [e for e in entries if e["status"] == "PENDING"]
    total_pending = sum(e.get("amount", 0) for e in pending)
    return {"player_id": player_id, "pending_balance": total_pending, "pending_items": pending, "all_entries": entries}


@router.post("/wallet/deliver-on-cardin")
async def deliver_wallet_on_cardin(request: Request):
    """
    Called when a player cards in at an EGM.
    Checks for pending wallet POC and delivers to that EGM.
    This would be triggered by the card_in event in the Gateway Core pipeline.
    """
    body = await request.json()
    player_id = body.get("player_id")
    egm_id = body.get("egm_id")

    if not player_id or not egm_id:
        raise HTTPException(status_code=400, detail="player_id and egm_id required")

    now = datetime.now(timezone.utc)
    # Find all pending wallet entries that haven't expired
    pending = await db.poc_wallet.find({
        "player_id": player_id, "status": "PENDING",
        "expires_at": {"$gte": now.isoformat()},
    }, {"_id": 0}).to_list(20)

    if not pending:
        return {"delivered": 0, "message": "No pending POC for this player"}

    total_delivered = 0
    delivered_ids = []
    messages = []

    for entry in pending:
        amt = entry.get("amount", 0)
        await db.poc_wallet.update_one({"id": entry["id"]}, {"$set": {
            "status": "DELIVERED",
            "delivered_at": now.isoformat(),
            "delivered_to_egm": egm_id,
        }})
        total_delivered += amt
        delivered_ids.append(entry["id"])
        messages.append(entry.get("message", f"${amt:.2f} bonus credits loaded!"))

    # Push combined message to EGM
    combined_msg = f"Welcome back! ${total_delivered:.2f} in bonus credits have been loaded to your machine!"
    await db.device_messages.insert_one({
        "id": str(uuid.uuid4()), "device_id": egm_id,
        "message_text": combined_msg, "message_type": "PROMO",
        "display_duration_seconds": 20, "display_position": "CENTER",
        "background_color": "#FFD700", "text_color": "#070B14",
        "priority": "HIGH",
        "expires_at": (now + timedelta(minutes=5)).isoformat(),
        "sent_by": "PIRS_WALLET", "sent_at": now.isoformat(), "status": "PENDING",
    })

    # Create POC award record
    await db.poc_awards.insert_one({
        "id": str(uuid.uuid4()), "player_id": player_id,
        "player_name": "", "egm_id": egm_id,
        "trigger_type": "wallet_delivery_on_cardin",
        "poc_amount": total_delivered, "poc_type": "play_only_credits",
        "delivery_status": "delivered",
        "delivered_at": now.isoformat(), "awarded_by": "PIRS_WALLET",
        "created_at": now.isoformat(),
        "wallet_entry_ids": delivered_ids,
    })

    # Update player pending balance
    await db.pirs_players.update_one({"player_id": player_id}, {"$inc": {"wallet_pending_poc": -total_delivered, "total_poc_awarded": total_delivered}})

    return {
        "delivered": total_delivered,
        "items_delivered": len(delivered_ids),
        "egm_id": egm_id,
        "player_id": player_id,
        "message_sent": combined_msg,
    }


@router.post("/wallet/expire-old")
async def expire_old_wallet_entries(request: Request):
    """Housekeeping — expire wallet entries past their expiry date."""
    await get_current_user(request)
    now = datetime.now(timezone.utc).isoformat()
    result = await db.poc_wallet.update_many(
        {"status": "PENDING", "expires_at": {"$lt": now}},
        {"$set": {"status": "EXPIRED"}},
    )
    return {"expired": result.modified_count}
