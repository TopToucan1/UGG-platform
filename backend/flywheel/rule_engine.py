"""
FlywheelOS Rule Engine — 12 universal + 3 gaming-specific rule families.
Each rule evaluates an event + actor profile and returns action candidates.
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from database import db
from flywheel import config as cfg
from flywheel.storage import get_rules_for_event, get_scheduled_rules, save_rule

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _make_candidate(rule: dict, profile: dict, event: dict, urgency: float,
                    relevance: float, message: str, poc: float = 0.0,
                    immediate: bool = True) -> dict:
    """Build a standard action candidate."""
    return {
        "id": str(uuid.uuid4()),
        "actor_id": profile.get("actor_id", ""),
        "rule_id": rule.get("id", ""),
        "rule_key": rule.get("key", ""),
        "rule_name": rule.get("name", ""),
        "family": rule.get("family", ""),
        "event_id": event.get("id", ""),
        "object_id": event.get("object_id", ""),
        "target_device_id": profile.get("last_device_id") or event.get("properties", {}).get("device_id", ""),
        "poc_amount": poc,
        "message_template": message,
        "urgency": urgency,
        "relevance": relevance,
        "channel": rule.get("channel_order", ["in_app_surface"])[0],
        "immediate": immediate,
        "created_at": _now(),
        "expires_at": (_now_dt() + timedelta(hours=24)).isoformat(),
    }


def _audience_matches(rule: dict, profile: dict) -> bool:
    """Check if profile matches the rule's audience conditions."""
    # Lifecycle filter
    audience_stages = rule.get("audience_lifecycle", [])
    if audience_stages and profile.get("lifecycle_stage") not in audience_stages:
        return False
    # Churn range
    churn = profile.get("churn_score", 50)
    if churn < rule.get("audience_min_churn", 0):
        return False
    if churn > rule.get("audience_max_churn", 100):
        return False
    return True


# ═══════════════════════════════════════════════════════════════════
# RULE FAMILIES — each returns list of action candidates
# ═══════════════════════════════════════════════════════════════════

async def _loss_recovery(event: dict, profile: dict, rule: dict) -> list[dict]:
    """Fires on competition_loss. Offer POC if net loss exceeds threshold."""
    net_loss = abs(event.get("value", 0))
    if net_loss < cfg.LOSS_RECOVERY_MIN_LOSS:
        return []
    poc = min(net_loss * 0.1, 25.0)  # 10% of loss, cap $25
    poc = max(poc, rule.get("poc_base", 5.0))
    msg = f"We noticed your last session. Here's ${poc:.2f} Play Credits to come back and try again!"
    return [_make_candidate(rule, profile, event, urgency=0.9, relevance=0.7,
                            message=msg, poc=poc, immediate=False)]


async def _milestone_proximity(event: dict, profile: dict, rule: dict) -> list[dict]:
    """Fires on progress_advance. Check if player is near a coin-in milestone."""
    # Get current coin-in from active session or PIRS
    device_id = event.get("properties", {}).get("device_id", "")
    session = await db.credit_sessions.find_one(
        {"device_id": device_id, "is_active": True}, {"_id": 0}
    )
    if not session:
        return []
    session_coin_in = session.get("coin_in", 0) + session.get("total_in", 0)
    candidates = []
    for threshold in cfg.MILESTONE_THRESHOLDS:
        remaining = threshold - session_coin_in
        if remaining > 0 and remaining <= threshold * cfg.MILESTONE_PROXIMITY_PCT:
            poc = round(threshold * 0.02, 2)  # 2% of milestone as POC
            msg = f"You're only ${remaining:.2f} away from the ${threshold} milestone! Keep going for ${poc:.2f} Play Credits!"
            candidates.append(_make_candidate(
                rule, profile, event, urgency=0.7, relevance=0.8,
                message=msg, poc=poc, immediate=True
            ))
            break  # Only closest milestone
    return candidates


async def _re_entry(event: dict, profile: dict, rule: dict) -> list[dict]:
    """Scheduled rule: target dormant/at_risk players with return offer."""
    days = profile.get("days_since_last_visit", 0)
    if days < cfg.RE_ENTRY_DORMANT_DAYS:
        return []
    poc = cfg.RE_ENTRY_POC_BASE
    if days >= 30:
        poc *= 1.5  # Bigger incentive for longer absence
    msg = f"We miss you! Here's ${poc:.2f} Play Credits waiting for you at any machine. Come back and play!"
    return [_make_candidate(rule, profile, event, urgency=0.8, relevance=0.6,
                            message=msg, poc=poc, immediate=False)]


async def _low_friction_earn_path(event: dict, profile: dict, rule: dict) -> list[dict]:
    """Scheduled: suggest simple actions for new/low-activity players to earn quick POC."""
    if profile.get("lifecycle_stage") not in ("new", "active"):
        return []
    if profile.get("session_count", 0) > 10:
        return []
    poc = 3.0
    msg = f"Quick tip: Play 10 more games to earn ${poc:.2f} Play Credits! Easy rewards for new players."
    return [_make_candidate(rule, profile, event, urgency=0.3, relevance=0.5,
                            message=msg, poc=poc, immediate=False)]


async def _social_proof(event: dict, profile: dict, rule: dict) -> list[dict]:
    """Fires on competition_win. Broadcast recent wins at the same site."""
    site_id = event.get("properties", {}).get("site_id", "")
    if not site_id:
        return []
    recent_wins = await db.flywheel_events.count_documents({
        "event_family": "competition_win",
        "properties.site_id": site_id,
        "occurred_at": {"$gte": (_now_dt() - timedelta(hours=1)).isoformat()},
    })
    if recent_wins < cfg.SOCIAL_PROOF_WIN_COUNT:
        return []
    msg = f"{recent_wins} players at this location hit wins in the last hour! The floor is hot!"
    return [_make_candidate(rule, profile, event, urgency=0.4, relevance=0.6,
                            message=msg, poc=0, immediate=True)]


async def _group_momentum(event: dict, profile: dict, rule: dict) -> list[dict]:
    """Event: site play volume up significantly."""
    site_id = event.get("properties", {}).get("site_id", "")
    if not site_id:
        return []
    # Compare last-hour event count to 24h average
    hour_count = await db.flywheel_events.count_documents({
        "properties.site_id": site_id,
        "event_family": "progress_advance",
        "occurred_at": {"$gte": (_now_dt() - timedelta(hours=1)).isoformat()},
    })
    day_count = await db.flywheel_events.count_documents({
        "properties.site_id": site_id,
        "event_family": "progress_advance",
        "occurred_at": {"$gte": (_now_dt() - timedelta(hours=24)).isoformat()},
    })
    hourly_avg = day_count / 24 if day_count > 0 else 1
    if hourly_avg > 0 and (hour_count / hourly_avg) > (1 + cfg.GROUP_MOMENTUM_THRESHOLD):
        msg = "This location is buzzing right now! Extra Play Credits for every milestone hit in the next hour."
        return [_make_candidate(rule, profile, event, urgency=0.5, relevance=0.7,
                                message=msg, poc=5.0, immediate=True)]
    return []


async def _shareable_moment(event: dict, profile: dict, rule: dict) -> list[dict]:
    """Fires on competition_win (jackpot/handpay). Celebrate the win."""
    if event.get("event_name") not in ("device.jackpot.handpay", "device.bonus.triggered"):
        return []
    win_amount = event.get("value", 0)
    msg = f"CONGRATULATIONS! You just won ${win_amount:.2f}! You've been added to the Winners Circle!"
    return [_make_candidate(rule, profile, event, urgency=0.3, relevance=0.9,
                            message=msg, poc=0, immediate=True)]


async def _interest_match(event: dict, profile: dict, rule: dict) -> list[dict]:
    """Fires on progress_start/progress_advance. Suggest content matching affinity."""
    affinity = profile.get("affinity_vectors", {})
    if not affinity:
        return []
    top_type = max(affinity, key=affinity.get) if affinity else None
    if not top_type:
        return []
    msg = f"Based on your play history, you might love our newest {top_type} games. Check them out!"
    return [_make_candidate(rule, profile, event, urgency=0.2, relevance=0.8,
                            message=msg, poc=0, immediate=False)]


async def _resource_deployment(event: dict, profile: dict, rule: dict) -> list[dict]:
    """Fires on progress_start. Remind player of unspent POC."""
    unspent = await db.poc_awards.count_documents({
        "player_id": profile.get("actor_id"),
        "delivery_status": "pending",
    })
    if unspent < 1:
        return []
    msg = f"You have {unspent} unused Play Credit awards! Log in to any machine to redeem them."
    return [_make_candidate(rule, profile, event, urgency=0.4, relevance=0.5,
                            message=msg, poc=0, immediate=True)]


# ── Gaming-specific rules ──
async def _session_extension(event: dict, profile: dict, rule: dict) -> list[dict]:
    """Active session 45min+, power/active tier → offer POC to continue."""
    device_id = event.get("properties", {}).get("device_id", "")
    pin_session = await db.pin_sessions.find_one(
        {"player_id": profile.get("actor_id"), "device_id": device_id, "is_active": True},
        {"_id": 0}
    )
    if not pin_session:
        return []
    started = pin_session.get("started_at", "")
    if not started:
        return []
    from flywheel.actor_profile import _parse_iso
    duration_min = (_now_dt() - _parse_iso(started)).total_seconds() / 60
    if duration_min < cfg.SESSION_EXTENSION_MINUTES:
        return []
    poc = 10.0
    msg = f"You've been playing for {int(duration_min)} minutes — here's ${poc:.2f} Play Credits to keep the fun going!"
    return [_make_candidate(rule, profile, event, urgency=0.5, relevance=0.7,
                            message=msg, poc=poc, immediate=True)]


async def _cold_streak_comfort(event: dict, profile: dict, rule: dict) -> list[dict]:
    """20+ games with no win detected → encouragement + small POC."""
    meters = (event.get("properties", {}) or {})
    games = meters.get("gamesPlayed", meters.get("games_played", 0))
    if not isinstance(games, (int, float)):
        return []
    # Check recent wins for this player
    recent_wins = await db.flywheel_events.count_documents({
        "actor_id": profile.get("actor_id"),
        "event_family": "competition_win",
        "occurred_at": {"$gte": (_now_dt() - timedelta(minutes=30)).isoformat()},
    })
    if recent_wins > 0:
        return []
    # Check games since last win
    device_id = event.get("properties", {}).get("device_id", "")
    session = await db.credit_sessions.find_one(
        {"device_id": device_id, "is_active": True}, {"_id": 0}
    )
    if session and session.get("games_played", 0) >= cfg.COLD_STREAK_GAMES:
        poc = 5.0
        msg = f"Hang in there! Here's ${poc:.2f} Play Credits — your luck could change any spin!"
        return [_make_candidate(rule, profile, event, urgency=0.6, relevance=0.5,
                                message=msg, poc=poc, immediate=True)]
    return []


# ═══════════════════════════════════════════════════════════════════
# Rule family registry
# ═══════════════════════════════════════════════════════════════════
RULE_HANDLERS = {
    "loss_recovery": _loss_recovery,
    "milestone_proximity": _milestone_proximity,
    "re_entry": _re_entry,
    "low_friction_earn_path": _low_friction_earn_path,
    "social_proof": _social_proof,
    "group_momentum": _group_momentum,
    "shareable_moment": _shareable_moment,
    "interest_match": _interest_match,
    "resource_deployment": _resource_deployment,
    "session_extension": _session_extension,
    "cold_streak_comfort": _cold_streak_comfort,
}


# ═══════════════════════════════════════════════════════════════════
# Default rule definitions (loaded on startup)
# ═══════════════════════════════════════════════════════════════════
DEFAULT_RULES = [
    {"key": "loss_recovery", "name": "Loss Recovery", "family": "loss_recovery",
     "trigger_type": "event", "trigger_events": ["competition_loss"],
     "audience_lifecycle": ["active", "power", "at_risk"], "audience_min_churn": 40,
     "scoring": {"base_priority": 0.8, "urgency": 0.9, "relevance_weight": 0.7},
     "poc_base": 5.0, "message_template": "", "priority": 85, "frequency_cap_hours": 48, "max_per_day": 1},

    {"key": "milestone_proximity", "name": "Milestone Proximity", "family": "milestone_proximity",
     "trigger_type": "event", "trigger_events": ["progress_advance"],
     "audience_lifecycle": ["active", "power", "new"], "scoring": {"base_priority": 0.7, "urgency": 0.7},
     "poc_base": 0, "priority": 75, "frequency_cap_hours": 4, "max_per_day": 3},

    {"key": "re_entry", "name": "Re-Entry Welcome Back", "family": "re_entry",
     "trigger_type": "scheduled", "cron_interval_seconds": cfg.WORKER_SCHEDULED_RUNNER,
     "audience_lifecycle": ["dormant", "at_risk"], "scoring": {"base_priority": 0.75, "urgency": 0.8},
     "poc_base": cfg.RE_ENTRY_POC_BASE, "priority": 80, "frequency_cap_hours": 168, "max_per_day": 1},

    {"key": "low_friction_earn_path", "name": "Low Friction Earn Path", "family": "low_friction_earn_path",
     "trigger_type": "scheduled", "cron_interval_seconds": cfg.WORKER_SCHEDULED_RUNNER,
     "audience_lifecycle": ["new", "active"], "scoring": {"base_priority": 0.4, "urgency": 0.3},
     "poc_base": 3.0, "priority": 40, "frequency_cap_hours": 24, "max_per_day": 1},

    {"key": "social_proof", "name": "Social Proof — Hot Floor", "family": "social_proof",
     "trigger_type": "event", "trigger_events": ["competition_win"],
     "audience_lifecycle": ["active", "power"], "scoring": {"base_priority": 0.5, "urgency": 0.4},
     "poc_base": 0, "priority": 50, "frequency_cap_hours": 2, "max_per_day": 3},

    {"key": "group_momentum", "name": "Group Momentum", "family": "group_momentum",
     "trigger_type": "event", "trigger_events": ["progress_advance"],
     "audience_lifecycle": ["active", "power"], "scoring": {"base_priority": 0.5, "urgency": 0.5},
     "poc_base": 5.0, "priority": 55, "frequency_cap_hours": 4, "max_per_day": 2},

    {"key": "shareable_moment", "name": "Shareable Moment — Big Win", "family": "shareable_moment",
     "trigger_type": "event", "trigger_events": ["competition_win"],
     "audience_lifecycle": [], "scoring": {"base_priority": 0.6, "urgency": 0.3},
     "poc_base": 0, "priority": 70, "frequency_cap_hours": 0.5, "max_per_day": 5},

    {"key": "interest_match", "name": "Interest Match", "family": "interest_match",
     "trigger_type": "event", "trigger_events": ["progress_start", "progress_advance"],
     "audience_lifecycle": ["active", "power"], "scoring": {"base_priority": 0.4, "urgency": 0.2},
     "poc_base": 0, "priority": 35, "frequency_cap_hours": 24, "max_per_day": 1},

    {"key": "resource_deployment", "name": "Use Your POC", "family": "resource_deployment",
     "trigger_type": "event", "trigger_events": ["progress_start"],
     "audience_lifecycle": [], "scoring": {"base_priority": 0.5, "urgency": 0.4},
     "poc_base": 0, "priority": 45, "frequency_cap_hours": 12, "max_per_day": 1},

    # Gaming-specific
    {"key": "session_extension", "name": "Session Extension Offer", "family": "session_extension",
     "trigger_type": "event", "trigger_events": ["progress_advance"],
     "audience_lifecycle": ["active", "power"], "audience_min_churn": 50,
     "scoring": {"base_priority": 0.6, "urgency": 0.5},
     "poc_base": 10.0, "priority": 60, "frequency_cap_hours": 2, "max_per_day": 2},

    {"key": "cold_streak_comfort", "name": "Cold Streak Comfort", "family": "cold_streak_comfort",
     "trigger_type": "event", "trigger_events": ["progress_advance"],
     "audience_lifecycle": ["active", "power", "at_risk"],
     "scoring": {"base_priority": 0.55, "urgency": 0.6},
     "poc_base": 5.0, "priority": 58, "frequency_cap_hours": 1, "max_per_day": 3},
]


async def load_default_rules() -> int:
    """Load/upsert all default rules. Returns count loaded."""
    count = 0
    for rule_def in DEFAULT_RULES:
        rule_def.setdefault("app_id", "ugg")
        rule_def.setdefault("enabled", True)
        rule_def.setdefault("channel_order", ["in_app_surface", "in_app_inbox"])
        await save_rule(rule_def)
        count += 1
    logger.info(f"FlywheelOS: loaded {count} default rules")
    return count


async def evaluate_event(event: dict, profile: dict) -> list[dict]:
    """
    Evaluate all enabled event-triggered rules that match this event's family.
    Returns list of action candidates.
    """
    family = event.get("event_family", "")
    rules = await get_rules_for_event(family)
    candidates = []
    for rule in rules:
        if not _audience_matches(rule, profile):
            continue
        handler = RULE_HANDLERS.get(rule.get("family"))
        if not handler:
            continue
        try:
            results = await handler(event, profile, rule)
            candidates.extend(results)
        except Exception as e:
            logger.error(f"Rule {rule.get('key')} error: {e}")
    return candidates


async def evaluate_scheduled(profile: dict) -> list[dict]:
    """
    Evaluate all enabled scheduled rules against a single profile.
    Called by scheduled_rule_runner worker.
    """
    rules = await get_scheduled_rules()
    candidates = []
    dummy_event = {"id": "", "event_family": "scheduled", "properties": {}, "value": 0, "object_id": ""}
    for rule in rules:
        if not _audience_matches(rule, profile):
            continue
        handler = RULE_HANDLERS.get(rule.get("family"))
        if not handler:
            continue
        try:
            results = await handler(dummy_event, profile, rule)
            candidates.extend(results)
        except Exception as e:
            logger.error(f"Scheduled rule {rule.get('key')} error: {e}")
    return candidates
