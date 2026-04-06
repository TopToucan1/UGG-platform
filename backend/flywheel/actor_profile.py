"""
FlywheelOS Actor Profile — merges PIRS churn/tier/lapse data with flywheel-specific
engagement state (fatigue, affinity, lifecycle stage).
"""
import logging
from datetime import datetime, timezone, timedelta
from database import db
from flywheel import config as cfg
from flywheel.storage import upsert_profile, get_profile

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(s: str) -> datetime:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return _now()


# ── PIRS tier lookup (mirrors routes/pirs.py) ──
TIERS = [
    {"id": "diamond",  "min_score": 85, "poc_multiplier": 2.0},
    {"id": "platinum", "min_score": 70, "poc_multiplier": 1.5},
    {"id": "gold",     "min_score": 55, "poc_multiplier": 1.3},
    {"id": "silver",   "min_score": 35, "poc_multiplier": 1.15},
    {"id": "bronze",   "min_score": 0,  "poc_multiplier": 1.0},
]


def get_tier(churn_score: float) -> dict:
    for t in TIERS:
        if churn_score >= t["min_score"]:
            return t
    return TIERS[-1]


def classify_lifecycle(profile: dict) -> str:
    """Derive lifecycle stage from PIRS + flywheel data."""
    days_absent = profile.get("days_since_last_visit", 0)
    visits = profile.get("visits_30d", 0)
    churn = profile.get("churn_score", 50)
    lapse = profile.get("lapse_risk", 0)
    events_week = profile.get("events_last_7_days", 0)
    prev_stage = profile.get("lifecycle_stage", "new")
    session_count = profile.get("session_count", 0)

    # Resurrected: was dormant, came back within window
    if prev_stage == "dormant" and days_absent <= cfg.LIFECYCLE_RESURRECTED_WINDOW_DAYS:
        return "resurrected"

    # Dormant: not seen in 30+ days
    if days_absent >= cfg.LIFECYCLE_DORMANT_DAYS:
        return "dormant"

    # At risk: high lapse OR low churn
    if lapse >= cfg.LIFECYCLE_AT_RISK_LAPSE_MIN or churn < cfg.LIFECYCLE_AT_RISK_CHURN_MAX:
        return "at_risk"

    # Power: recent + frequent
    if days_absent <= cfg.LIFECYCLE_POWER_RECENCY_DAYS and events_week >= cfg.LIFECYCLE_POWER_MIN_EVENTS_WEEK:
        return "power"

    # New: few sessions
    if session_count <= cfg.LIFECYCLE_NEW_MAX_VISITS:
        return "new"

    return "active"


async def get_actor_profile(player_id: str) -> dict:
    """
    Build a merged actor profile from PIRS + flywheel_profiles + real-time session data.
    This is the single source of truth for the decision engine.
    """
    # Start with flywheel profile
    fw = await get_profile(player_id) or {"actor_id": player_id}

    # Merge PIRS data
    pirs = await db.pirs_players.find_one({"player_id": player_id}, {"_id": 0})
    if pirs:
        fw["churn_score"] = pirs.get("churn_score", 50)
        fw["lapse_risk"] = pirs.get("lapse_risk", 0)
        fw["lifetime_value"] = pirs.get("coin_in_30d", 0)
        fw["days_since_last_visit"] = pirs.get("days_since_last_visit", 0)
        fw["visits_30d"] = pirs.get("visits_30d", 0)
        fw["player_name"] = pirs.get("player_name", "")
        fw["last_device_id"] = pirs.get("last_egm_id")

    # Merge PIN player data
    pin_player = await db.players_pin.find_one({"id": player_id}, {"_id": 0, "pin_hash": 0})
    if pin_player:
        fw.setdefault("player_name", pin_player.get("name", ""))

    # Compute tier
    churn = fw.get("churn_score", 50)
    tier = get_tier(churn)
    fw["tier"] = tier["id"]
    fw["tier_multiplier"] = tier["poc_multiplier"]
    fw["churn_risk"] = round(1.0 - (churn / 100.0), 3)

    # Count today's actions
    today_start = _now().replace(hour=0, minute=0, second=0).isoformat()
    fw["actions_today"] = await db.flywheel_actions.count_documents(
        {"actor_id": player_id, "status": {"$in": ["approved", "dispatched", "delivered"]},
         "created_at": {"$gte": today_start}}
    )

    # Session count from pin_sessions
    fw["session_count"] = await db.pin_sessions.count_documents({"player_id": player_id})

    # Events last 7 days from flywheel_events
    week_ago = (_now() - timedelta(days=7)).isoformat()
    fw["events_last_7_days"] = await db.flywheel_events.count_documents(
        {"actor_id": player_id, "occurred_at": {"$gte": week_ago}}
    )

    # Check anomaly suppression
    active_anomaly = await db.session_anomalies.find_one(
        {"player_id": player_id, "status": "open", "severity": "HIGH"}
    )
    if active_anomaly:
        fw["suppressed_until"] = (_now() + timedelta(hours=2)).isoformat()

    # Classify lifecycle
    fw["lifecycle_stage"] = classify_lifecycle(fw)

    # Defaults
    fw.setdefault("fatigue_score", 0.0)
    fw.setdefault("affinity_vectors", {})
    fw.setdefault("opted_in_channels", ["in_app_surface", "in_app_inbox"])
    fw.setdefault("updated_at", _now().isoformat())

    return fw


async def recompute_profile(player_id: str) -> dict:
    """Full recompute and persist. Called by profile_updater worker."""
    profile = await get_actor_profile(player_id)

    # Decay fatigue (reduce by 0.05 per recompute cycle, floor 0)
    fatigue = max(0.0, profile.get("fatigue_score", 0.0) - 0.05)
    profile["fatigue_score"] = round(fatigue, 3)

    # Persist flywheel-specific fields
    await upsert_profile(player_id, {
        "actor_id": player_id,
        "lifecycle_stage": profile["lifecycle_stage"],
        "fatigue_score": profile["fatigue_score"],
        "affinity_vectors": profile.get("affinity_vectors", {}),
        "last_action_at": profile.get("last_action_at"),
        "actions_today": profile.get("actions_today", 0),
        "suppressed_until": profile.get("suppressed_until"),
        "session_count": profile.get("session_count", 0),
        "events_last_7_days": profile.get("events_last_7_days", 0),
    })
    return profile


async def increment_fatigue(player_id: str, amount: float = 0.1) -> None:
    """Increase fatigue after an action is delivered. Max 1.0."""
    profile = await get_profile(player_id) or {}
    new_fatigue = min(1.0, profile.get("fatigue_score", 0.0) + amount)
    await upsert_profile(player_id, {"fatigue_score": round(new_fatigue, 3)})
